from odoo import api, fields, models, tools

class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    
    # Moroccan-specific fields
    order_type = fields.Selection([
        ('standard', 'Standard Order'),
        ('import', 'Import Order'),
        ('free_zone', 'Free Zone Order'),
        ('government', 'Government Order')
    ], string="Order Type", readonly=True)
    
    is_import = fields.Boolean(string="Is Import", readonly=True)
    
    origin_country_id = fields.Many2one('res.country', string="Origin Country", readonly=True)
    
    is_vat_reverse_charge = fields.Boolean(string="VAT Reverse Charge", readonly=True)
    
    reverse_charge_reason = fields.Selection([
        ('import', 'Import Purchase'),
        ('free_zone', 'Free Zone Purchase'),
        ('non_resident', 'Non-resident Vendor'),
        ('other', 'Other')
    ], string="Reverse Charge Reason", readonly=True)
    
    vat_rate = fields.Selection([
        ('0', 'Exempt (0%)'),
        ('7', 'Reduced Rate (7%)'),
        ('10', 'Reduced Rate (10%)'),
        ('14', 'Reduced Rate (14%)'),
        ('20', 'Standard Rate (20%)')
    ], string="VAT Rate", readonly=True)
    
    # Additional fields
    delivery_term = fields.Selection([
        ('ex_works', 'EXW - Ex Works'),
        ('fca', 'FCA - Free Carrier'),
        ('fas', 'FAS - Free Alongside Ship'),
        ('fob', 'FOB - Free on Board'),
        ('cfr', 'CFR - Cost and Freight'),
        ('cif', 'CIF - Cost, Insurance and Freight'),
        ('cpt', 'CPT - Carriage Paid To'),
        ('cip', 'CIP - Carriage and Insurance Paid To'),
        ('dap', 'DAP - Delivered at Place'),
        ('dpu', 'DPU - Delivered at Place Unloaded'),
        ('ddp', 'DDP - Delivered Duty Paid')
    ], string="Delivery Terms", readonly=True)
    
    shipping_method = fields.Selection([
        ('road', 'Road'),
        ('sea', 'Sea'),
        ('air', 'Air'),
        ('rail', 'Rail'),
        ('multi', 'Multimodal')
    ], string="Shipping Method", readonly=True)
    
    # Import-specific fields
    customs_code = fields.Char(string="Customs Code", readonly=True)
    
    country_of_origin = fields.Many2one('res.country', string="Country of Origin", readonly=True)
    
    # Monetary fields in MAD
    price_subtotal_mad = fields.Float(string="Subtotal (MAD)", readonly=True)
    price_tax_mad = fields.Float(string="Tax (MAD)", readonly=True)
    price_total_mad = fields.Float(string="Total (MAD)", readonly=True)
    
    # Discount information
    discount = fields.Float(string='Discount (%)', readonly=True)
    
    discount_reason = fields.Selection([
        ('volume', 'Volume Discount'),
        ('loyalty', 'Loyalty Discount'),
        ('promotion', 'Promotional Discount'),
        ('clearance', 'Clearance Discount'),
        ('damaged', 'Damaged Product Discount'),
        ('other', 'Other')
    ], string="Discount Reason", readonly=True)
    
    def _select_additional_fields(self):
        return """
            , po.order_type as order_type
            , po.is_import as is_import
            , po.origin_country_id as origin_country_id
            , po.is_vat_reverse_charge as is_vat_reverse_charge
            , po.reverse_charge_reason as reverse_charge_reason
            , po.delivery_term as delivery_term
            , po.shipping_method as shipping_method
            , l.price_subtotal_mad as price_subtotal_mad
            , l.price_tax_mad as price_tax_mad
            , l.price_total_mad as price_total_mad
            , l.discount as discount
            , l.discount_reason as discount_reason
            , l.customs_code as customs_code
            , l.country_of_origin as country_of_origin
            , pt.vat_rate as vat_rate
        """
    
    def _from_additional_fields(self):
        return """
        """
    
    def _group_by_additional_fields(self):
        return """
            , po.order_type
            , po.is_import
            , po.origin_country_id
            , po.is_vat_reverse_charge
            , po.reverse_charge_reason
            , po.delivery_term
            , po.shipping_method
            , l.price_subtotal_mad
            , l.price_tax_mad
            , l.price_total_mad
            , l.discount
            , l.discount_reason
            , l.customs_code
            , l.country_of_origin
            , pt.vat_rate
        """
    
    def _select(self):
        return super(PurchaseReport, self)._select() + self._select_additional_fields()
    
    def _from(self):
        return super(PurchaseReport, self)._from() + self._from_additional_fields()
    
    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + self._group_by_additional_fields()
