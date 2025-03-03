from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        
        # Get values from system parameters
        res.update(
            enable_customs_management=params.get_param('prism_inventory.enable_customs_management', 'False') == 'True',
            default_customs_authority=params.get_param('prism_inventory.default_customs_authority', ''),
            enable_vat_exemption=params.get_param('prism_inventory.enable_vat_exemption', 'False') == 'True',
            vat_exemption_document=params.get_param('prism_inventory.vat_exemption_document', ''),
            enable_temperature_control=params.get_param('prism_inventory.enable_temperature_control', 'False') == 'True',
            default_temperature_min=float(params.get_param('prism_inventory.default_temperature_min', '2.0')),
            default_temperature_max=float(params.get_param('prism_inventory.default_temperature_max', '8.0')),
            enable_approval_workflow=params.get_param('prism_inventory.enable_approval_workflow', 'False') == 'True',
            require_manager_approval=params.get_param('prism_inventory.require_manager_approval', 'False') == 'True',
            enable_quality_control=params.get_param('prism_inventory.enable_quality_control', 'False') == 'True',
            default_quality_check_frequency=params.get_param('prism_inventory.default_quality_check_frequency', 'monthly'),
            enable_lot_tracking=params.get_param('prism_inventory.enable_lot_tracking', 'False') == 'True',
            require_lot_origin=params.get_param('prism_inventory.require_lot_origin', 'False') == 'True',
            require_lot_expiry=params.get_param('prism_inventory.require_lot_expiry', 'False') == 'True',
            enable_enhanced_reporting=params.get_param('prism_inventory.enable_enhanced_reporting', 'False') == 'True',
            default_report_currency=params.get_param('prism_inventory.default_report_currency', 'both'),
        )
        return res
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        
        # Set values in system parameters
        params.set_param('prism_inventory.enable_customs_management', str(self.enable_customs_management))
        params.set_param('prism_inventory.default_customs_authority', self.default_customs_authority or '')
        params.set_param('prism_inventory.enable_vat_exemption', str(self.enable_vat_exemption))
        params.set_param('prism_inventory.vat_exemption_document', self.vat_exemption_document or '')
        params.set_param('prism_inventory.enable_temperature_control', str(self.enable_temperature_control))
        params.set_param('prism_inventory.default_temperature_min', str(self.default_temperature_min))
        params.set_param('prism_inventory.default_temperature_max', str(self.default_temperature_max))
        params.set_param('prism_inventory.enable_approval_workflow', str(self.enable_approval_workflow))
        params.set_param('prism_inventory.require_manager_approval', str(self.require_manager_approval))
        params.set_param('prism_inventory.enable_quality_control', str(self.enable_quality_control))
        params.set_param('prism_inventory.default_quality_check_frequency', self.default_quality_check_frequency)
        params.set_param('prism_inventory.enable_lot_tracking', str(self.enable_lot_tracking))
        params.set_param('prism_inventory.require_lot_origin', str(self.require_lot_origin))
        params.set_param('prism_inventory.require_lot_expiry', str(self.require_lot_expiry))
        params.set_param('prism_inventory.enable_enhanced_reporting', str(self.enable_enhanced_reporting))
        params.set_param('prism_inventory.default_report_currency', self.default_report_currency)
    
    # Moroccan-specific inventory settings
    module_prism_inventory = fields.Boolean(string='PRISM Inventory')
    
    # Customs settings
    enable_customs_management = fields.Boolean(string='Enable Customs Management',
                                             help="Enable customs management features for inventory operations")
    default_customs_authority = fields.Char(string='Default Customs Authority',
                                          help="Default customs authority for import/export operations")
    
    # VAT settings
    enable_vat_exemption = fields.Boolean(string='Enable VAT Exemption',
                                        help="Enable VAT exemption for certain warehouse types")
    vat_exemption_document = fields.Char(string='VAT Exemption Document',
                                       help="Default document required for VAT exemption")
    
    # Temperature control settings
    enable_temperature_control = fields.Boolean(string='Enable Temperature Control',
                                              help="Enable temperature control features for inventory operations")
    default_temperature_min = fields.Float(string='Default Minimum Temperature',
                                         help="Default minimum temperature for temperature-controlled locations")
    default_temperature_max = fields.Float(string='Default Maximum Temperature',
                                         help="Default maximum temperature for temperature-controlled locations")
    
    # Approval workflow settings
    enable_approval_workflow = fields.Boolean(string='Enable Approval Workflow',
                                            help="Enable approval workflow for inventory operations")
    require_manager_approval = fields.Boolean(string='Require Manager Approval',
                                            help="Require manager approval for certain inventory operations")
    
    # Quality control settings
    enable_quality_control = fields.Boolean(string='Enable Quality Control',
                                          help="Enable quality control features for inventory operations")
    default_quality_check_frequency = fields.Selection([
        ('none', 'None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], string='Default Quality Check Frequency', default='monthly',
        help="Default frequency for quality checks")
    
    # Lot tracking settings
    enable_lot_tracking = fields.Boolean(string='Enable Lot Tracking',
                                       help="Enable lot tracking features for inventory operations")
    require_lot_origin = fields.Boolean(string='Require Lot Origin',
                                      help="Require origin information for lots")
    require_lot_expiry = fields.Boolean(string='Require Lot Expiry',
                                      help="Require expiry date for lots")
    
    # Reporting settings
    enable_enhanced_reporting = fields.Boolean(string='Enable Enhanced Reporting',
                                             help="Enable enhanced reporting features for inventory operations")
    default_report_currency = fields.Selection([
        ('company', 'Company Currency'),
        ('mad', 'Moroccan Dirham (MAD)'),
        ('both', 'Both'),
    ], string='Default Report Currency', default='both',
        help="Default currency for inventory reports")
