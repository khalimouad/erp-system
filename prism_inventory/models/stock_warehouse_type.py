from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockWarehouseType(models.Model):
    _name = 'stock.warehouse.type'
    _description = 'Warehouse Type'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', required=True, translate=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    # Customs and regulatory fields
    requires_customs = fields.Boolean(string='Requires Customs', default=False, tracking=True,
                                    help="Whether warehouses of this type require customs documentation")
    
    is_vat_exempt = fields.Boolean(string='VAT Exempt', default=False, tracking=True,
                                 help="Whether warehouses of this type are exempt from VAT")
    
    customs_authority_id = fields.Many2one('res.partner', string='Customs Authority', 
                                         domain=[('is_company', '=', True)],
                                         tracking=True,
                                         help="The customs authority responsible for this warehouse type")
    
    # Categorization fields
    category = fields.Selection([
        ('standard', 'Standard'),
        ('bonded', 'Bonded'),
        ('free_zone', 'Free Zone'),
        ('transit', 'Transit'),
        ('export', 'Export'),
        ('special', 'Special Economic Zone')
    ], string='Category', required=True, default='standard', tracking=True,
       help="The category of the warehouse type according to Moroccan regulations")
    
    # Regulatory requirements
    requires_special_license = fields.Boolean(string='Requires Special License', 
                                            default=False, tracking=True,
                                            help="Whether warehouses of this type require a special license")
    
    license_authority_id = fields.Many2one('res.partner', string='License Authority',
                                         domain=[('is_company', '=', True)],
                                         tracking=True,
                                         help="The authority that issues licenses for this warehouse type")
    
    inspection_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannual', 'Bi-annual'),
        ('annual', 'Annual')
    ], string='Inspection Frequency', default='quarterly', tracking=True,
       help="How often warehouses of this type must be inspected")
    
    # Documentation requirements
    required_documents = fields.Text(string='Required Documents', tracking=True,
                                   help="Documents required for warehouses of this type")
    
    # Notes and additional information
    note = fields.Text(string='Notes', tracking=True)
    
    # Statistics
    warehouse_count = fields.Integer(string='Warehouse Count', 
                                   compute='_compute_warehouse_count',
                                   help="Number of warehouses of this type")
    
    @api.depends()
    def _compute_warehouse_count(self):
        """Compute the number of warehouses for each warehouse type"""
        for warehouse_type in self:
            warehouse_type.warehouse_count = self.env['stock.warehouse'].search_count([
                ('warehouse_type_id', '=', warehouse_type.id)
            ])
    
    @api.constrains('code')
    def _check_code_unique(self):
        """Ensure warehouse type code is unique"""
        for warehouse_type in self:
            if self.search_count([('code', '=', warehouse_type.code), ('id', '!=', warehouse_type.id)]) > 0:
                raise ValidationError(_("Warehouse type code must be unique. Code '%s' already exists.") % warehouse_type.code)
    
    @api.constrains('category', 'requires_customs')
    def _check_category_customs(self):
        """Ensure customs requirements are consistent with category"""
        for warehouse_type in self:
            if warehouse_type.category in ['bonded', 'transit', 'free_zone'] and not warehouse_type.requires_customs:
                raise ValidationError(_("Warehouse types in the '%s' category must require customs documentation.") % warehouse_type.category)
    
    @api.onchange('category')
    def _onchange_category(self):
        """Set default values based on category"""
        if self.category in ['bonded', 'transit', 'free_zone']:
            self.requires_customs = True
            
        if self.category in ['free_zone', 'export']:
            self.is_vat_exempt = True
        else:
            self.is_vat_exempt = False
            
        if self.category in ['bonded', 'free_zone', 'special']:
            self.requires_special_license = True
        else:
            self.requires_special_license = False
    
    def action_view_warehouses(self):
        """Open warehouses of this type"""
        self.ensure_one()
        return {
            'name': _('Warehouses'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.warehouse',
            'view_mode': 'tree,form',
            'domain': [('warehouse_type_id', '=', self.id)],
            'context': {'default_warehouse_type_id': self.id},
        }
    
    def name_get(self):
        """Custom name_get to include code"""
        result = []
        for warehouse_type in self:
            name = '%s [%s]' % (warehouse_type.name, warehouse_type.code)
            result.append((warehouse_type.id, name))
        return result
