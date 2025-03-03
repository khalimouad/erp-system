from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
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
