# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
from datetime import datetime


class TaxDeclaration(models.Model):
    _name = 'tax.declaration'
    _description = 'Tax Declaration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    tax_type_id = fields.Many2one('tax.type', string='Tax Type', required=True, ondelete='restrict')
    
    date = fields.Date(string='Declaration Date', required=True, default=fields.Date.context_today)
    period_from = fields.Date(string='Period From', required=True)
    period_to = fields.Date(string='Period To', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('submitted', 'Submitted'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Financial information
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)
    amount_taxable = fields.Monetary(string='Taxable Amount', compute='_compute_amounts', store=True)
    amount_tax = fields.Monetary(string='Tax Amount', compute='_compute_amounts', store=True)
    amount_total = fields.Monetary(string='Total Amount', compute='_compute_amounts', store=True)
    
    # Declaration lines
    line_ids = fields.One2many('tax.declaration.line', 'declaration_id', string='Declaration Lines')
    line_count = fields.Integer(string='Line Count', compute='_compute_line_count')
    
    # XML and EDI fields
    xml_file = fields.Binary(string='XML File', attachment=True)
    xml_filename = fields.Char(string='XML Filename')
    zip_file = fields.Binary(string='ZIP File', attachment=True)
    zip_filename = fields.Char(string='ZIP Filename')
    
    # Submission information
    submission_date = fields.Datetime(string='Submission Date')
    submission_user_id = fields.Many2one('res.users', string='Submitted By')
    submission_reference = fields.Char(string='Submission Reference')
    
    # Payment information
    payment_date = fields.Date(string='Payment Date')
    payment_reference = fields.Char(string='Payment Reference')
    payment_method = fields.Char(string='Payment Method')
    
    # Notes
    notes = fields.Text(string='Notes')
    
    # Moroccan specific fields
    is_moroccan_declaration = fields.Boolean(string='Is Moroccan Declaration', related='tax_type_id.is_moroccan_tax', store=True)
    moroccan_declaration_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ], string='Declaration Frequency', default='monthly')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('tax.declaration') or 'New'
        return super(TaxDeclaration, self).create(vals_list)
    
    @api.depends('line_ids.amount_taxable', 'line_ids.amount_tax')
    def _compute_amounts(self):
        for declaration in self:
            declaration.amount_taxable = sum(declaration.line_ids.mapped('amount_taxable'))
            declaration.amount_tax = sum(declaration.line_ids.mapped('amount_tax'))
            declaration.amount_total = declaration.amount_taxable + declaration.amount_tax
    
    @api.depends('line_ids')
    def _compute_line_count(self):
        for declaration in self:
            declaration.line_count = len(declaration.line_ids)
    
    @api.constrains('period_from', 'period_to')
    def _check_period(self):
        for declaration in self:
            if declaration.period_from > declaration.period_to:
                raise ValidationError(_('The start date must be earlier than the end date.'))
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_submit(self):
        for declaration in self:
            if not declaration.xml_file:
                declaration.generate_xml()
            
            declaration.write({
                'state': 'submitted',
                'submission_date': fields.Datetime.now(),
                'submission_user_id': self.env.user.id,
            })
    
    def action_mark_as_paid(self):
        self.write({
            'state': 'paid',
            'payment_date': fields.Date.context_today(self),
        })
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    
    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
    
    def generate_xml(self):
        self.ensure_one()
        
        if self.is_moroccan_declaration:
            if self.tax_type_id.moroccan_tax_category == 'tva':
                return self._generate_tva_xml()
            elif self.tax_type_id.moroccan_tax_category == 'is':
                return self._generate_is_xml()
            elif self.tax_type_id.moroccan_tax_category == 'ir':
                return self._generate_ir_xml()
        
        # Generic XML generation
        return self._generate_generic_xml()
    
    def _generate_tva_xml(self):
        """Generate XML for TVA declaration"""
        root = ET.Element("DeclarationTVA")
        
        # Add header information
        ET.SubElement(root, "identifiantFiscal").text = self.company_id.vat
        ET.SubElement(root, "annee").text = str(self.period_from.year)
        ET.SubElement(root, "periode").text = str(self.period_from.month)
        ET.SubElement(root, "regime").text = "1"  # Monthly
        
        # Add lines
        lines = ET.SubElement(root, "lignes")
        
        for line in self.line_ids:
            line_elem = ET.SubElement(lines, "ligne")
            ET.SubElement(line_elem, "code").text = line.tax_rate_id.code
            ET.SubElement(line_elem, "montantHT").text = str(line.amount_taxable)
            ET.SubElement(line_elem, "montantTVA").text = str(line.amount_tax)
        
        # Convert to string
        xml_string = ET.tostring(root, encoding='utf-8', method='xml')
        xml_string = b'<?xml version="1.0" encoding="UTF-8"?>' + xml_string
        
        # Save XML file
        filename = f"TVA_{self.period_from.year}_{self.period_from.month}.xml"
        self.xml_file = base64.b64encode(xml_string)
        self.xml_filename = filename
        
        # Create ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(filename, xml_string)
        
        self.zip_file = base64.b64encode(zip_buffer.getvalue())
        self.zip_filename = f"TVA_{self.period_from.year}_{self.period_from.month}.zip"
        
        return True
    
    def _generate_is_xml(self):
        """Generate XML for IS declaration"""
        root = ET.Element("DeclarationIS")
        
        # Add header information
        ET.SubElement(root, "identifiantFiscal").text = self.company_id.vat
        ET.SubElement(root, "annee").text = str(self.period_from.year)
        ET.SubElement(root, "exerciceFiscalDu").text = self.period_from.strftime('%Y-%m-%d')
        ET.SubElement(root, "exerciceFiscalAu").text = self.period_to.strftime('%Y-%m-%d')
        
        # Add lines
        lines = ET.SubElement(root, "lignes")
        
        for line in self.line_ids:
            line_elem = ET.SubElement(lines, "ligne")
            ET.SubElement(line_elem, "code").text = line.tax_rate_id.code
            ET.SubElement(line_elem, "montantBase").text = str(line.amount_taxable)
            ET.SubElement(line_elem, "montantIS").text = str(line.amount_tax)
        
        # Convert to string
        xml_string = ET.tostring(root, encoding='utf-8', method='xml')
        xml_string = b'<?xml version="1.0" encoding="UTF-8"?>' + xml_string
        
        # Save XML file
        filename = f"IS_{self.period_from.year}.xml"
        self.xml_file = base64.b64encode(xml_string)
        self.xml_filename = filename
        
        # Create ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(filename, xml_string)
        
        self.zip_file = base64.b64encode(zip_buffer.getvalue())
        self.zip_filename = f"IS_{self.period_from.year}.zip"
        
        return True
    
    def _generate_ir_xml(self):
        """Generate XML for IR declaration"""
        root = ET.Element("DeclarationIR")
        
        # Add header information
        ET.SubElement(root, "identifiantFiscal").text = self.company_id.vat
        ET.SubElement(root, "annee").text = str(self.period_from.year)
        ET.SubElement(root, "periode").text = str(self.period_from.month)
        
        # Add lines
        lines = ET.SubElement(root, "lignes")
        
        for line in self.line_ids:
            line_elem = ET.SubElement(lines, "ligne")
            ET.SubElement(line_elem, "code").text = line.tax_rate_id.code
            ET.SubElement(line_elem, "montantBase").text = str(line.amount_taxable)
            ET.SubElement(line_elem, "montantIR").text = str(line.amount_tax)
        
        # Convert to string
        xml_string = ET.tostring(root, encoding='utf-8', method='xml')
        xml_string = b'<?xml version="1.0" encoding="UTF-8"?>' + xml_string
        
        # Save XML file
        filename = f"IR_{self.period_from.year}_{self.period_from.month}.xml"
        self.xml_file = base64.b64encode(xml_string)
        self.xml_filename = filename
        
        # Create ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(filename, xml_string)
        
        self.zip_file = base64.b64encode(zip_buffer.getvalue())
        self.zip_filename = f"IR_{self.period_from.year}_{self.period_from.month}.zip"
        
        return True
    
    def _generate_generic_xml(self):
        """Generate generic XML for non-Moroccan declarations"""
        root = ET.Element("TaxDeclaration")
        
        # Add header information
        ET.SubElement(root, "taxType").text = self.tax_type_id.name
        ET.SubElement(root, "company").text = self.company_id.name
        ET.SubElement(root, "vatNumber").text = self.company_id.vat or ''
        ET.SubElement(root, "periodFrom").text = self.period_from.strftime('%Y-%m-%d')
        ET.SubElement(root, "periodTo").text = self.period_to.strftime('%Y-%m-%d')
        ET.SubElement(root, "declarationDate").text = self.date.strftime('%Y-%m-%d')
        
        # Add totals
        totals = ET.SubElement(root, "totals")
        ET.SubElement(totals, "taxableAmount").text = str(self.amount_taxable)
        ET.SubElement(totals, "taxAmount").text = str(self.amount_tax)
        ET.SubElement(totals, "totalAmount").text = str(self.amount_total)
        
        # Add lines
        lines = ET.SubElement(root, "lines")
        
        for line in self.line_ids:
            line_elem = ET.SubElement(lines, "line")
            ET.SubElement(line_elem, "description").text = line.name
            ET.SubElement(line_elem, "taxRate").text = line.tax_rate_id.name
            ET.SubElement(line_elem, "taxableAmount").text = str(line.amount_taxable)
            ET.SubElement(line_elem, "taxAmount").text = str(line.amount_tax)
            ET.SubElement(line_elem, "totalAmount").text = str(line.amount_taxable + line.amount_tax)
        
        # Convert to string
        xml_string = ET.tostring(root, encoding='utf-8', method='xml')
        xml_string = b'<?xml version="1.0" encoding="UTF-8"?>' + xml_string
        
        # Save XML file
        filename = f"Tax_Declaration_{self.period_from.year}_{self.period_from.month}.xml"
        self.xml_file = base64.b64encode(xml_string)
        self.xml_filename = filename
        
        # Create ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(filename, xml_string)
        
        self.zip_file = base64.b64encode(zip_buffer.getvalue())
        self.zip_filename = f"Tax_Declaration_{self.period_from.year}_{self.period_from.month}.zip"
        
        return True
    
    def action_view_lines(self):
        self.ensure_one()
        return {
            'name': _('Declaration Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'tax.declaration.line',
            'view_mode': 'tree,form',
            'domain': [('declaration_id', '=', self.id)],
            'context': {'default_declaration_id': self.id},
        }


class TaxDeclarationLine(models.Model):
    _name = 'tax.declaration.line'
    _description = 'Tax Declaration Line'
    _order = 'sequence, id'

    declaration_id = fields.Many2one('tax.declaration', string='Declaration', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    name = fields.Char(string='Description')
    
    tax_type_id = fields.Many2one('tax.type', string='Tax Type', related='declaration_id.tax_type_id', store=True)
    tax_rate_id = fields.Many2one('tax.rate', string='Tax Rate', required=True, domain="[('tax_type_id', '=', tax_type_id)]")
    tax_exemption_id = fields.Many2one('tax.exemption', string='Tax Exemption', domain="[('tax_type_id', '=', tax_type_id)]")
    
    # Financial information
    currency_id = fields.Many2one('res.currency', string='Currency', related='declaration_id.currency_id', readonly=True)
    amount_taxable = fields.Monetary(string='Taxable Amount', required=True)
    amount_tax = fields.Monetary(string='Tax Amount', compute='_compute_amount_tax', store=True)
    
    # Source document
    source_document_model = fields.Char(string='Source Document Model')
    source_document_id = fields.Integer(string='Source Document ID')
    
    @api.depends('amount_taxable', 'tax_rate_id', 'tax_exemption_id')
    def _compute_amount_tax(self):
        for line in self:
            if line.tax_exemption_id:
                line.amount_tax = 0.0
            elif line.tax_rate_id:
                line.amount_tax = line.amount_taxable * (line.tax_rate_id.rate / 100.0)
            else:
                line.amount_tax = 0.0
    
    @api.onchange('tax_rate_id')
    def _onchange_tax_rate_id(self):
        if self.tax_rate_id and not self.name:
            self.name = self.tax_rate_id.name
