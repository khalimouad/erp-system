from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Moroccan-specific fields
    vat_rate = fields.Selection([
        ('0', 'Exempt (0%)'),
        ('7', 'Reduced Rate (7%)'),
        ('10', 'Reduced Rate (10%)'),
        ('14', 'Reduced Rate (14%)'),
        ('20', 'Standard Rate (20%)')
    ], string="VAT Rate", default='20', required=True,
       help="VAT rate applicable to the product according to Moroccan tax law")
    
    is_service = fields.Boolean(string="Is a Service", 
                               help="Check if this is a service rather than a physical product")
    
    local_code = fields.Char(string="Local Code", 
                            help="Product code used locally in Morocco")
    
    # Additional fields for better product management
    min_stock = fields.Float(string="Minimum Stock", default=0.0,
                           help="Minimum stock level for reordering")
    
    max_stock = fields.Float(string="Maximum Stock", default=0.0,
                           help="Maximum stock level for inventory management")
    
    reorder_qty = fields.Float(string="Reorder Quantity", default=0.0,
                             help="Default quantity to reorder when stock is low")
    
    lead_time = fields.Integer(string="Lead Time (Days)", default=1,
                              help="Average time in days between ordering and receiving this product")
    
    shelf_life = fields.Integer(string="Shelf Life (Days)", default=0,
                               help="Number of days the product can be stored before expiry (0 = no expiry)")
    
    country_of_origin = fields.Many2one('res.country', string="Country of Origin")
    
    # Classification fields
    product_classification = fields.Selection([
        ('raw', 'Raw Material'),
        ('semi', 'Semi-Finished'),
        ('finished', 'Finished Product'),
        ('consumable', 'Consumable'),
        ('service', 'Service')
    ], string="Product Classification", default='finished')
    
    # Accounting fields
    purchase_account_id = fields.Many2one('account.account', string="Purchase Account",
                                        help="Account used for product purchases")
    
    sale_account_id = fields.Many2one('account.account', string="Sale Account",
                                     help="Account used for product sales")
    
    # Computed fields
    stock_value = fields.Monetary(string="Stock Value", compute='_compute_stock_value', store=False,
                                currency_field='currency_id')
    
    @api.depends('qty_available', 'standard_price')
    def _compute_stock_value(self):
        for product in self:
            product.stock_value = product.qty_available * product.standard_price
    
    @api.onchange('is_service')
    def _onchange_is_service(self):
        if self.is_service:
            self.product_classification = 'service'
            self.type = 'service'
        elif self.product_classification == 'service':
            self.product_classification = 'finished'
    
    @api.onchange('product_classification')
    def _onchange_product_classification(self):
        if self.product_classification == 'service':
            self.is_service = True
            self.type = 'service'
    
    @api.constrains('vat_rate', 'is_service')
    def _check_vat_rate_service(self):
        for product in self:
            # Services typically use 10% VAT rate in Morocco
            if product.is_service and product.vat_rate not in ['0', '10']:
                raise ValidationError(_("Services typically use 10% VAT rate in Morocco. "
                                      "Please verify the VAT rate for this service."))
