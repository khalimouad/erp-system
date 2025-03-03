from odoo import api, fields, models
import base64
from lxml import etree
import datetime
import re
import zipfile
import io
import logging
from odoo.exceptions import UserError
from odoo import _

_logger = logging.getLogger(__name__)

class SimplisDeclaration(models.Model):
    _name = 'simplis.declaration'
    _description = 'SIMPL-IS Declaration'
    _inherit = 'moroccan.edi.declaration'
    
    declaration_subtype = fields.Selection([
        ('liasse', 'Liasse Fiscale'),
        ('drvt', 'Déclaration des rémunérations versées à des tiers'),
        ('papsra', 'Déclaration des produits des actions, parts sociales et revenus assimilés'),
        ('pprf', 'Déclaration des produits de placements à revenu fixe'),
        ('ca', 'Déclaration de Chiffre d\'affaires'),
        ('rvt_med', 'Déclaration des rémunérations versées à des tiers (Médecins)'),
        ('ras', 'Déclaration des rémunérations versées à des personnes non résidentes'),
        ('profit', 'Déclaration du résultat fiscal au titre des plus values'),
    ], string='IS Declaration Type', required=True)
    
    model_id = fields.Selection([
        ('1', 'Comptable Normal'),
        ('2', 'Comptable Simplifié'),
        ('3', 'Etablissements de crédit'),
        ('4', 'Assurance'),
    ], string='Liasse Model', help="Only applicable for Liasse Fiscale")
    
    fiscal_year = fields.Char(string='Fiscal Year', required=True)
    
    line_ids = fields.One2many('simplis.declaration.line', 'declaration_id', string='Declaration Lines')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['declaration_type'] = 'is'
        return super(SimplisDeclaration, self).create(vals_list)
    
    def action_draft(self):
        self.write({'state': 'draft'})
    
    def action_generate_xml(self):
        self.ensure_one()
        
        # Create XML structure based on the declaration type
        if self.declaration_subtype == 'liasse':
            xml_content = self._generate_liasse_xml()
        else:
            xml_content = self._generate_declaration_xml()
        
        # Save the generated XML
        xml_filename = f"{self.declaration_subtype}_{self.company_id.vat}_{self.fiscal_year}.xml"
        self.xml_file = base64.b64encode(xml_content.encode('utf-8'))
        self.xml_filename = xml_filename
        
        # Create ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr(xml_filename, xml_content)
        
        self.zip_file = base64.b64encode(zip_buffer.getvalue())
        self.zip_filename = f"{self.declaration_subtype}_{self.company_id.vat}_{self.fiscal_year}.zip"
        
        self.state = 'generated'
        return True
    
    def _generate_liasse_xml(self):
        """Generate XML for Liasse Fiscale"""
        root = etree.Element("Liasse")
        
        # Add model information
        model_elem = etree.SubElement(root, "modele")
        id_elem = etree.SubElement(model_elem, "id")
        id_elem.text = self.model_id
        
        # Add fiscal information
        fiscal_elem = etree.SubElement(root, "resultatFiscal")
        
        id_fiscal_elem = etree.SubElement(fiscal_elem, "identifiantFiscal")
        id_fiscal_elem.text = self.company_id.vat
        
        date_from_elem = etree.SubElement(fiscal_elem, "exerciceFiscalDu")
        date_from_elem.text = self.date_from.strftime('%Y-%m-%d')
        
        date_to_elem = etree.SubElement(fiscal_elem, "exerciceFiscalAu")
        date_to_elem.text = self.date_to.strftime('%Y-%m-%d')
        
        # Group tables
        groupe_tableaux_elem = etree.SubElement(root, "groupeValeursTableau")
        
        # Process each mapped table and its data
        for table in self._get_liasse_tables():
            self._add_table_to_xml(groupe_tableaux_elem, table)
        
        # Convert to string with XML declaration and proper encoding
        return etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=True).decode('utf-8')
    
    def _generate_declaration_xml(self):
        """Generate XML for other declaration types"""
        declaration_type_map = {
            'drvt': 'DeclarationDRVT',
            'papsra': 'DeclarationPAPSRA',
            'pprf': 'DeclarationPPRF',
            'ca': 'DeclarationCA',
            'rvt_med': 'DeclarationRVTMed',
            'ras': 'DeclarationRAS',
            'profit': 'DeclarationProfit',
        }
        
        root_tag = declaration_type_map.get(self.declaration_subtype, 'Declaration')
        root = etree.Element(root_tag)
        
        # Add common elements
        id_fiscal_elem = etree.SubElement(root, "identifiantFiscal")
        id_fiscal_elem.text = self.company_id.vat
        
        date_from_elem = etree.SubElement(root, "exerciceFiscalDu")
        date_from_elem.text = self.date_from.strftime('%Y-%m-%d')
        
        date_to_elem = etree.SubElement(root, "exerciceFiscalAu")
        date_to_elem.text = self.date_to.strftime('%Y-%m-%d')
        
        # Add declaration-specific elements
        if self.declaration_subtype == 'drvt':
            self._add_drvt_elements(root)
        elif self.declaration_subtype == 'papsra':
            self._add_papsra_elements(root)
        elif self.declaration_subtype == 'pprf':
            self._add_pprf_elements(root)
        elif self.declaration_subtype == 'ca':
            self._add_ca_elements(root)
        elif self.declaration_subtype == 'rvt_med':
            self._add_rvt_med_elements(root)
        elif self.declaration_subtype == 'ras':
            self._add_ras_elements(root)
        elif self.declaration_subtype == 'profit':
            self._add_profit_elements(root)
        
        # Convert to string with XML declaration and proper encoding
        return etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=True).decode('utf-8')
    
    def _get_liasse_tables(self):
        """Get the tables for Liasse Fiscale"""
        # This would typically come from accounting data based on the model_id
        # For demonstration, returning empty list - in real implementation would fetch actual data
        return []
    
    def _add_table_to_xml(self, parent_elem, table_data):
        """Add a table to the XML structure for Liasse Fiscale"""
        table_elem = etree.SubElement(parent_elem, "ValeursTableau")
        
        # Add table ID
        tableau_elem = etree.SubElement(table_elem, "tableau")
        id_elem = etree.SubElement(tableau_elem, "id")
        id_elem.text = str(table_data.get('id'))
        
        # Add values group
        groupe_valeurs = etree.SubElement(table_elem, "groupeValeurs")
        
        # Add each cell
        for cell in table_data.get('cells', []):
            cell_elem = etree.SubElement(groupe_valeurs, "ValeurCellule")
            
            # Cell ID
            cellule_elem = etree.SubElement(cell_elem, "cellule")
            code_edi_elem = etree.SubElement(cellule_elem, "codeEdi")
            code_edi_elem.text = str(cell.get('code_edi'))
            
            # Cell value
            valeur_elem = etree.SubElement(cell_elem, "valeur")
            valeur_elem.text = str(cell.get('value', ''))
            
            # Line number for tables with multiple lines
            if 'line_number' in cell:
                ligne_elem = etree.SubElement(cell_elem, "numeroLigne")
                ligne_elem.text = str(cell.get('line_number'))
    
    def _add_drvt_elements(self, root):
        """Add DRVT-specific elements to the XML"""
        if not self.line_ids:
            return
        
        # Create parent element for the table
        distributions = etree.SubElement(root, "distributionsRetenues")
        
        # For each record, create an element with the fields
        for line in self.line_ids:
            distribution = etree.SubElement(distributions, "DistributionRetenuePPRF")
            
            # Add beneficiary information
            if line.partner_id.is_company:
                etree.SubElement(distribution, "nom").text = ""
                etree.SubElement(distribution, "prenom").text = ""
                etree.SubElement(distribution, "raisonSociale").text = line.partner_id.name or ""
            else:
                name_parts = (line.partner_id.name or "").split(' ', 1)
                etree.SubElement(distribution, "nom").text = name_parts[0] if name_parts else ""
                etree.SubElement(distribution, "prenom").text = name_parts[1] if len(name_parts) > 1 else ""
                etree.SubElement(distribution, "raisonSociale").text = ""
            
            etree.SubElement(distribution, "adresse").text = line.partner_id.contact_address or ""
            etree.SubElement(distribution, "identifiantFiscal").text = line.partner_id.vat or ""
            etree.SubElement(distribution, "numeroCIN").text = line.cin or ""
            
            # Add payment information
            etree.SubElement(distribution, "montantDistribution").text = f"{line.amount:.2f}"
            etree.SubElement(distribution, "montantRetenue").text = f"{line.tax_amount:.2f}"
            
            # Add category
            etree.SubElement(distribution, "categorie").text = "PM" if line.partner_id.is_company else "PP"
    
    def _add_papsra_elements(self, root):
        """Add PAPSRA-specific elements to the XML"""
        # Similar implementation to _add_drvt_elements but with PAPSRA-specific fields
        pass
    
    def _add_pprf_elements(self, root):
        """Add PPRF-specific elements to the XML"""
        # Similar implementation to _add_drvt_elements but with PPRF-specific fields
        pass
    
    def _add_ca_elements(self, root):
        """Add CA-specific elements to the XML"""
        # Similar implementation to _add_drvt_elements but with CA-specific fields
        pass
    
    def _add_rvt_med_elements(self, root):
        """Add RVT_MED-specific elements to the XML"""
        # Similar implementation to _add_drvt_elements but with RVT_MED-specific fields
        pass
    
    def _add_ras_elements(self, root):
        """Add RAS-specific elements to the XML"""
        # Similar implementation to _add_drvt_elements but with RAS-specific fields
        pass
    
    def _add_profit_elements(self, root):
        """Add PROFIT-specific elements to the XML"""
        # Similar implementation to _add_drvt_elements but with PROFIT-specific fields
        pass
    
    def _prepare_api_data(self):
        """Prepare data for API call"""
        return {
            'identifiantFiscal': self.company_id.vat,
            'annee': self.year,
            'exercice_fiscal_du': self.date_from.strftime('%Y-%m-%d'),
            'exercice_fiscal_au': self.date_to.strftime('%Y-%m-%d'),
            'declaration_type': f'is_{self.declaration_subtype}'
        }


class SimplisDeclarationLine(models.Model):
    _name = 'simplis.declaration.line'
    _description = 'SIMPL-IS Declaration Line'
    
    declaration_id = fields.Many2one('simplis.declaration', string='Declaration', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    partner_id = fields.Many2one('res.partner', string='Partner')
    name = fields.Char(string='Description')
    
    amount = fields.Monetary(string='Amount', currency_field='company_currency_id')
    tax_amount = fields.Monetary(string='Tax Amount', currency_field='company_currency_id')
    
    company_id = fields.Many2one(related='declaration_id.company_id')
    company_currency_id = fields.Many2one(related='company_id.currency_id')
    
    reference = fields.Char(string='Reference')
    date = fields.Date(string='Date')
    
    # Fields specific to different declaration types
    id_fiscal = fields.Char(string='Tax ID')
    cin = fields.Char(string='CIN')
    ice = fields.Char(string='ICE')
    
    nature_id = fields.Many2one('dgi.nature', string='Nature')
    taux_id = fields.Many2one('dgi.taux', string='Rate')
