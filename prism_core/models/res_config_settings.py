from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        # No need to add custom logic here since all fields are related fields
        return res
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        # No need to add custom logic here since all fields are related fields
    
    # Company Information
    company_name = fields.Char(related='company_id.name', readonly=False)
    company_tax_id = fields.Char(related='company_id.vat', string="ICE Number", readonly=False)
    company_rc_number = fields.Char(related='company_id.company_registry', string="Trade Register", readonly=False)
    company_cnss_number = fields.Char(related='company_id.social_security', string="Social Security", readonly=False)
    
    # System Configuration
    module_prism_company = fields.Boolean(string="Company Management")
    module_prism_user = fields.Boolean(string="User Management")
    module_prism_partner = fields.Boolean(string="Partner Management")
    module_prism_product = fields.Boolean(string="Product Management")
    module_prism_sales = fields.Boolean(string="Sales Management")
    module_prism_purchase = fields.Boolean(string="Purchase Management")
    module_prism_inventory = fields.Boolean(string="Inventory Management")
    module_prism_accounting = fields.Boolean(string="Accounting Management")
    module_prism_tax = fields.Boolean(string="Tax Management")
    module_prism_payroll = fields.Boolean(string="Payroll Management")
