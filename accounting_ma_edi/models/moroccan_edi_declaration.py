import base64
import logging
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class MoroccanEdiDeclaration(models.AbstractModel):
    """Base model for all Moroccan EDI declarations"""
    _name = 'moroccan.edi.declaration'
    _description = 'Moroccan EDI Declaration Base'
    
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
    year = fields.Char('Year', required=True, default=lambda self: str(datetime.now().year))
    period = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ('13', 'Annual')
    ], string='Period', required=True)
    
    xml_file = fields.Binary('XML File')
    xml_filename = fields.Char('XML Filename')
    zip_file = fields.Binary('ZIP File')
    zip_filename = fields.Char('ZIP Filename')
    
    response_message = fields.Text('Response from DGI')
    
    declaration_type = fields.Selection([
        ('tva', 'TVA Retenue à la Source'),
        ('ir', 'Traitements et Salaires'),
        ('is', 'SIMPL-IS')
    ], string='Declaration Type', required=True)
    
    @api.model
    def create(self, vals):
        """Create a name based on the declaration type, year and period"""
        if not vals.get('name'):
            declaration_type = vals.get('declaration_type', 'unknown')
            year = vals.get('year', datetime.now().year)
            period = vals.get('period', '1')
            
            if declaration_type == 'tva':
                vals['name'] = f"TVA Retenue {year}-{period}"
            elif declaration_type == 'ir':
                vals['name'] = f"Traitements et Salaires {year}-{period}"
            elif declaration_type == 'is':
                subtype = vals.get('declaration_subtype', 'unknown')
                vals['name'] = f"SIMPL-IS {subtype.upper()} {year}-{period}"
        
        return super(MoroccanEdiDeclaration, self).create(vals)
    
    def action_generate_xml(self):
        """Generate XML file according to DGI specifications"""
        self.ensure_one()
        
        # Abstract method to be implemented by specific declaration types
        raise NotImplementedError(_("This method should be implemented by specific declaration types"))
    
    def action_send_to_dgi(self):
        """Send the generated ZIP file to DGI"""
        self.ensure_one()
        
        if not self.zip_file:
            raise UserError(_("Please generate the XML file first"))
        
        # This would be replaced with actual API call to DGI
        try:
            # Simulate API call
            _logger.info(f"Sending {self.declaration_type} file to DGI...")
            
            # Call the specific implementation
            result = self._call_dgi_api()
            
            if result:
                self.state = 'sent'
                self.response_message = f"File successfully sent to DGI. Awaiting processing."
                
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
        """Base implementation of DGI API call"""
        import requests
        
        try:
            # Get the API endpoint and credentials from system parameters
            dgi_url = self.env['ir.config_parameter'].sudo().get_param('dgi.api.url')
            username = self.env['ir.config_parameter'].sudo().get_param('dgi.api.username')
            password = self.env['ir.config_parameter'].sudo().get_param('dgi.api.password')
            
            if not all([dgi_url, username, password]):
                raise UserError(_("DGI API configuration is incomplete. Please configure it in System Parameters."))
            
            # Prepare the files for upload
            files = {
                'file': (self.zip_filename, base64.b64decode(self.zip_file), 'application/zip')
            }
            
            # Prepare the data - different for each declaration type
            data = self._prepare_api_data()
            
            # Make the API call
            response = requests.post(
                dgi_url,
                files=files,
                data=data,
                auth=(username, password),
                timeout=30
            )
            
            # Process the response
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('status') == 'success':
                    self.state = 'sent'
                    self.response_message = response_data.get('message', 'File successfully sent to DGI')
                    return True
                else:
                    self.response_message = response_data.get('message', 'Unknown error')
                    raise UserError(self.response_message)
            else:
                self.response_message = f"HTTP Error: {response.status_code} - {response.text}"
                raise UserError(self.response_message)
        
        except requests.exceptions.RequestException as e:
            self.response_message = f"Connection error: {str(e)}"
            raise UserError(self.response_message)
        except Exception as e:
            self.response_message = f"Unexpected error: {str(e)}"
            raise UserError(self.response_message)
    
    def _prepare_api_data(self):
        """Prepare data for API call - to be implemented by specific declaration types"""
        raise NotImplementedError(_("This method should be implemented by specific declaration types"))
    
    def validate_xml_against_xsd(self, xml_string, xsd_path):
        """Validate XML against XSD schema"""
        try:
            from lxml import etree
            
            # Parse the XSD schema
            xmlschema_doc = etree.parse(xsd_path)
            xmlschema = etree.XMLSchema(xmlschema_doc)
            
            # Parse the XML
            xml_doc = etree.fromstring(xml_string)
            
            # Validate
            result = xmlschema.validate(xml_doc)
            
            # Get validation errors if any
            log = xmlschema.error_log
            error_messages = []
            for error in log:
                error_messages.append(f"Line {error.line}: {error.message}")
            
            return result, error_messages
        except Exception as e:
            return False, [str(e)]
