import base64
import logging
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class TvaTeleDeclaration(models.Model):
    _name = 'account.tva.teledeclaration'
    _description = 'TVA Retenue Source Teledeclaration'
    _order = 'date_start desc, id desc'
    
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'XML Generated'),
        ('sent', 'Sent to DGI'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft')
    
    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)
    period = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Period', required=True)
    
    year = fields.Char('Year', required=True, default=lambda self: str(datetime.now().year))
    regime = fields.Selection([('1', 'Monthly')], string='Regime', default='1', required=True)
    
    supplier_line_ids = fields.One2many('account.tva.teledeclaration.line', 'declaration_id', string='Supplier Lines')
    
    xml_file = fields.Binary('XML File')
    xml_filename = fields.Char('XML Filename')
    zip_file = fields.Binary('ZIP File')
    zip_filename = fields.Char('ZIP Filename')
    
    response_message = fields.Text('Response from DGI')
    
    @api.model
    def create(self, vals):
        vals['name'] = f"TVA Retenue {vals.get('year')}-{vals.get('period')}"
        return super(TvaTeleDeclaration, self).create(vals)
    
    def action_generate_xml(self):
        """Generate XML file according to DGI specifications"""
        self.ensure_one()
        
        if not self.supplier_line_ids:
            raise UserError(_("No supplier lines found to include in the declaration"))
        
        # Create root element
        root = ET.Element("VersementRetenueSources")
        
        # Add header information
        ET.SubElement(root, "identifiantFiscal").text = self.company_id.vat
        ET.SubElement(root, "annee").text = self.year
        ET.SubElement(root, "periode").text = self.period
        ET.SubElement(root, "regime").text = self.regime
        
        # Add suppliers section
        suppliers = ET.SubElement(root, "fournisseurs")
        
        for line in self.supplier_line_ids:
            supplier = ET.SubElement(suppliers, "fournisseur")
            ET.SubElement(supplier, "ifuFournisseur").text = line.partner_id.vat
            ET.SubElement(supplier, "numFacture").text = line.invoice_ref
            ET.SubElement(supplier, "datePaiement").text = line.payment_date.strftime('%Y-%m-%d')
            ET.SubElement(supplier, "dateOperation").text = line.operation_date.strftime('%Y-%m-%d')
            ET.SubElement(supplier, "refNatOpt").text = line.operation_type
            ET.SubElement(supplier, "montantHT").text = str(line.amount_untaxed)
            ET.SubElement(supplier, "tauxTva").text = str(line.vat_rate)
            ET.SubElement(supplier, "tauxRetenuSource").text = str(line.withholding_rate)
        
        # Convert XML to string
        xml_string = ET.tostring(root, encoding='utf-8', method='xml')
        
        # Add XML declaration
        xml_string = b'<?xml version="1.0" encoding="UTF-8"?>' + xml_string
        
        # Store XML file
        self.xml_file = base64.b64encode(xml_string)
        self.xml_filename = f"TVA_Retenue_{self.year}_{self.period}.xml"
        
        # Create ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(self.xml_filename, xml_string)
        
        # Store ZIP file
        self.zip_file = base64.b64encode(zip_buffer.getvalue())
        self.zip_filename = f"TVA_Retenue_{self.year}_{self.period}.zip"
        
        self.state = 'generated'
        return True
    
    def action_send_to_dgi(self):
        """Send the generated ZIP file to DGI"""
        self.ensure_one()
        
        if not self.zip_file:
            raise UserError(_("Please generate the XML file first"))
        
        # This would be replaced with actual API call to DGI
        # For now, this is a placeholder
        try:
            # Simulate API call
            _logger.info("Sending file to DGI...")
            # response = self._call_dgi_api()
            
            # For demonstration, we'll simulate a successful response
            self.state = 'sent'
            self.response_message = "File successfully sent to DGI. Awaiting processing."
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Declaration successfully sent to DGI'),
                    'sticky': False,
                }
            }
        except Exception as e:
            self.response_message = f"Error sending file: {str(e)}"
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }
    
    def _call_dgi_api(self):
        """Actual implementation of the DGI API call"""
        # This method would contain the actual API call to DGI
        # It would depend on the specific API documentation provided by DGI
        # For now, it's a placeholder
        pass


class TvaTeleDeclarationLine(models.Model):
    _name = 'account.tva.teledeclaration.line'
    _description = 'TVA Retenue Source Line'
    
    declaration_id = fields.Many2one('account.tva.teledeclaration', string='Declaration', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Supplier', required=True)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_ref = fields.Char('Invoice Reference', required=True)
    
    payment_date = fields.Date('Payment Date', required=True)
    operation_date = fields.Date('Operation Date', required=True)
    
    operation_type = fields.Selection([
        ('1', 'Equipment Purchase'),
        ('2', 'Work Purchase'),
        ('3', 'Service Purchase')
    ], string='Operation Type', required=True)
    
    amount_untaxed = fields.Float('Amount Untaxed', required=True)
    vat_rate = fields.Float('VAT Rate', required=True)
    withholding_rate = fields.Selection([
        ('75', '75%'),
        ('100', '100%')
    ], string='Withholding Rate', default='75', required=True)
    
    amount_tax = fields.Float('VAT Amount', compute='_compute_amount_tax', store=True)
    amount_withholding = fields.Float('Withholding Amount', compute='_compute_amount_withholding', store=True)
    
    @api.depends('amount_untaxed', 'vat_rate')
    def _compute_amount_tax(self):
        for line in self:
            line.amount_tax = line.amount_untaxed * (line.vat_rate / 100.0)
    
    @api.depends('amount_tax', 'withholding_rate')
    def _compute_amount_withholding(self):
        for line in self:
            line.amount_withholding = line.amount_tax * (float(line.withholding_rate) / 100.0)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    is_tva_withholding = fields.Boolean('TVA Withholding', default=False)
    withholding_rate = fields.Selection([
        ('75', '75%'),
        ('100', '100%')
    ], string='Withholding Rate', default='75')
    
    def action_create_tva_withholding_lines(self):
        """Create TVA withholding declaration lines from invoices"""
        active_ids = self.env.context.get('active_ids', [])
        invoices = self.browse(active_ids)
        
        # Check if there's an active declaration
        declaration = self.env['account.tva.teledeclaration'].search([
            ('state', '=', 'draft'),
            ('year', '=', str(datetime.now().year)),
            ('period', '=', str(datetime.now().month))
        ], limit=1)
        
        if not declaration:
            # Create a new declaration if none exists
            declaration = self.env['account.tva.teledeclaration'].create({
                'year': str(datetime.now().year),
                'period': str(datetime.now().month),
                'date_start': datetime.now().replace(day=1),
                'date_end': datetime.now(),
            })
        
        for invoice in invoices:
            if invoice.move_type not in ('in_invoice', 'in_refund'):
                continue
                
            for line in invoice.invoice_line_ids:
                if not line.tax_ids:
                    continue
                    
                # Create a withholding line for each tax line
                vat_rate = 0
                for tax in line.tax_ids:
                    if tax.tax_group_id.name == 'TVA':
                        vat_rate = tax.amount
                        
                self.env['account.tva.teledeclaration.line'].create({
                    'declaration_id': declaration.id,
                    'partner_id': invoice.partner_id.id,
                    'invoice_id': invoice.id,
                    'invoice_ref': invoice.name or invoice.ref,
                    'payment_date': invoice.invoice_date_due,
                    'operation_date': invoice.invoice_date,
                    'operation_type': '3',  # Default to service, can be changed later
                    'amount_untaxed': line.price_subtotal,
                    'vat_rate': vat_rate,
                    'withholding_rate': invoice.withholding_rate or '75',
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'TVA Withholding Declaration',
            'res_model': 'account.tva.teledeclaration',
            'view_mode': 'form',
            'res_id': declaration.id,
            'target': 'current',
        }
