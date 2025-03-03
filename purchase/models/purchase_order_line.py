from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    # Moroccan-specific fields
    vat_rate = fields.Selection(related='product_id.vat_rate', string="VAT Rate", readonly=True, store=True)
    
    is_vat_reverse_charge = fields.Boolean(related='order_id.is_vat_reverse_charge', string="VAT Reverse Charge", readonly=True)
    
    # Additional fields
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    
    discount_reason = fields.Selection([
        ('volume', 'Volume Discount'),
        ('loyalty', 'Loyalty Discount'),
        ('promotion', 'Promotional Discount'),
        ('clearance', 'Clearance Discount'),
        ('damaged', 'Damaged Product Discount'),
        ('other', 'Other')
    ], string="Discount Reason")
    
    discount_notes = fields.Text(string="Discount Notes")
    
    # Import-specific fields
    customs_code = fields.Char(string="Customs Code", help="Harmonized System code for customs")
    
    country_of_origin = fields.Many2one('res.country', string="Country of Origin")
    
    # Computed fields
    price_subtotal_mad = fields.Monetary(string="Subtotal (MAD)", compute='_compute_amounts_in_mad',
                                       store=True, help="Subtotal in Moroccan Dirhams")
    
    price_tax_mad = fields.Monetary(string="Tax (MAD)", compute='_compute_amounts_in_mad',
                                  store=True, help="Tax amount in Moroccan Dirhams")
    
    price_total_mad = fields.Monetary(string="Total (MAD)", compute='_compute_amounts_in_mad',
                                    store=True, help="Total in Moroccan Dirhams")
    
    @api.depends('price_subtotal', 'price_tax', 'price_total', 'order_id.exchange_rate')
    def _compute_amounts_in_mad(self):
        for line in self:
            exchange_rate = line.order_id.exchange_rate or 1.0
            line.price_subtotal_mad = line.price_subtotal * exchange_rate
            line.price_tax_mad = line.price_tax * exchange_rate
            line.price_total_mad = line.price_total * exchange_rate
    
    @api.onchange('discount')
    def _onchange_discount(self):
        if self.discount > 0 and not self.discount_reason:
            return {
                'warning': {
                    'title': _("Discount Reason Required"),
                    'message': _("Please specify a reason for the discount.")
                }
            }
    
    @api.onchange('product_id')
    def _onchange_product_id_vat(self):
        if self.product_id and self.order_id.is_vat_reverse_charge:
            # If the order is VAT reverse charge, set the tax to 0%
            taxes = self.env['account.tax'].search([
                ('type_tax_use', '=', 'purchase'),
                ('amount', '=', 0),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if taxes:
                self.taxes_id = [(6, 0, taxes.ids)]
        elif self.product_id and self.product_id.vat_rate:
            # Otherwise, set the tax according to the product's VAT rate
            vat_rate = float(self.product_id.vat_rate)
            taxes = self.env['account.tax'].search([
                ('type_tax_use', '=', 'purchase'),
                ('amount', '=', vat_rate),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if taxes:
                self.taxes_id = [(6, 0, taxes.ids)]
    
    @api.onchange('product_id')
    def _onchange_product_id_customs(self):
        if self.product_id and self.order_id.is_import:
            # Set customs code and country of origin from product
            self.customs_code = self.product_id.customs_code if hasattr(self.product_id, 'customs_code') else False
            self.country_of_origin = self.product_id.country_of_origin if hasattr(self.product_id, 'country_of_origin') else False
    
    @api.constrains('discount')
    def _check_discount(self):
        for line in self:
            if line.discount > 0 and not line.discount_reason:
                raise ValidationError(_("A reason must be provided for discounts."))
            
            # Maximum discount allowed is 50% unless user has special rights
            max_discount = 50.0
            if line.discount > max_discount and not self.env.user.has_group('purchase.group_purchase_manager'):
                raise ValidationError(_("Discount cannot exceed %s%% without approval.") % max_discount)
    
    # Override the _prepare_compute_all_values method to include discount
    def _prepare_compute_all_values(self):
        vals = super(PurchaseOrderLine, self)._prepare_compute_all_values()
        
        # Apply discount to price_unit if discount exists
        if self.discount:
            vals['price_unit'] = vals['price_unit'] * (1 - (self.discount / 100.0))
            
        return vals
