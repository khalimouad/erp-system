from odoo import api, fields, models, _

class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    # Moroccan-specific fields
    default_vat_rate = fields.Selection([
        ('0', 'Exempt (0%)'),
        ('7', 'Reduced Rate (7%)'),
        ('10', 'Reduced Rate (10%)'),
        ('14', 'Reduced Rate (14%)'),
        ('20', 'Standard Rate (20%)')
    ], string="Default VAT Rate", default='20',
       help="Default VAT rate for products in this category")
    
    # Accounting fields
    purchase_account_id = fields.Many2one('account.account', string="Purchase Account",
                                        help="Default purchase account for products in this category")
    
    sale_account_id = fields.Many2one('account.account', string="Sale Account",
                                     help="Default sale account for products in this category")
    
    stock_account_id = fields.Many2one('account.account', string="Stock Account",
                                      help="Default stock account for products in this category")
    
    stock_input_account_id = fields.Many2one('account.account', string="Stock Input Account",
                                           help="Default stock input account for products in this category")
    
    stock_output_account_id = fields.Many2one('account.account', string="Stock Output Account",
                                            help="Default stock output account for products in this category")
    
    # Additional fields
    description = fields.Text(string="Description")
    
    is_active = fields.Boolean(string="Active", default=True)
    
    # Statistics fields
    product_count = fields.Integer(string="Product Count", compute='_compute_product_count')
    
    @api.depends()
    def _compute_product_count(self):
        for category in self:
            category.product_count = self.env['product.template'].search_count([
                ('categ_id', 'child_of', category.id)
            ])
    
    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            self.default_vat_rate = self.parent_id.default_vat_rate
            self.purchase_account_id = self.parent_id.purchase_account_id
            self.sale_account_id = self.parent_id.sale_account_id
            self.stock_account_id = self.parent_id.stock_account_id
            self.stock_input_account_id = self.parent_id.stock_input_account_id
            self.stock_output_account_id = self.parent_id.stock_output_account_id
    
    def action_view_products(self):
        """Open a view showing all products in this category"""
        self.ensure_one()
        action = self.env.ref('product.action_product_template').read()[0]
        action['domain'] = [('categ_id', 'child_of', self.id)]
        action['context'] = {
            'default_categ_id': self.id,
            'search_default_filter_to_sell': 0  # Remove default filter
        }
        action['name'] = _("Products in category: %s") % self.name
        return action
    
    def action_open_conversion_wizard(self):
        """Open the UoM conversion wizard"""
        self.ensure_one()
        action = self.env.ref('product.action_uom_conversion_wizard').read()[0]
        return action
