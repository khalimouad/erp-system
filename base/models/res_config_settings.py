from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # Company Information
    company_name = fields.Char(related='company_id.name', readonly=False)
    company_tax_id = fields.Char(related='company_id.vat', string="ICE Number", readonly=False)
    company_rc_number = fields.Char(related='company_id.company_registry', string="Trade Register", readonly=False)
    company_cnss_number = fields.Char(string="Social Security", readonly=False)
    
    # System Configuration
    module_company = fields.Boolean(string="Company Management")
    module_user = fields.Boolean(string="User Management")
    module_partner = fields.Boolean(string="Partner Management")
    module_product = fields.Boolean(string="Product Management")
    module_sales = fields.Boolean(string="Sales Management")
    module_purchase = fields.Boolean(string="Purchase Management")
    module_inventory = fields.Boolean(string="Inventory Management")
    module_accounting = fields.Boolean(string="Accounting Management")
    module_tax = fields.Boolean(string="Tax Management")
    module_payroll = fields.Boolean(string="Payroll Management")
    
    @api.model
    def _get_values(self):
        res = super(ResConfigSettings, self)._get_values()
        res.update(
            company_cnss_number=self.env['ir.config_parameter'].sudo().get_param('base.company_cnss_number'),
        )
        return res
    
    def _set_values(self):
        super(ResConfigSettings, self)._set_values()
        self.env['ir.config_parameter'].sudo().set_param('base.company_cnss_number', self.company_cnss_number or '')
