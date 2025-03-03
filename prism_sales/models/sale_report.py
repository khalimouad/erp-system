from odoo import api, fields, models, tools

class SaleReport(models.Model):
    _inherit = 'sale.report'
    
    # Moroccan-specific fields
    order_type = fields.Selection([
        ('standard', 'Standard Order'),
        ('export', 'Export Order'),
        ('free_zone', 'Free Zone Order'),
        ('government', 'Government Order')
    ], string="Order Type", readonly=True)
    
    # Bon de Livraison fields
    is_bl = fields.Boolean(string="Is Bon de Livraison", readonly=True)
    bl_number = fields.Char(string="BL Number", readonly=True)
    bl_date = fields.Date(string="BL Date", readonly=True)
    to_invoice_end_of_month = fields.Boolean(string="Invoice End of Month", readonly=True)
    month_to_invoice = fields.Char(string="Month to Invoice", readonly=True)
    
    is_export = fields.Boolean(string="Is Export", readonly=True)
    
    destination_country_id = fields.Many2one('res.country', string="Destination Country", readonly=True)
    
    is_vat_exempt = fields.Boolean(string="VAT Exempt", readonly=True)
    
    vat_exemption_reason = fields.Selection([
        ('export', 'Export Sale'),
        ('free_zone', 'Free Zone Sale'),
        ('diplomatic', 'Diplomatic Sale'),
        ('government', 'Government Sale'),
        ('other', 'Other')
    ], string="VAT Exemption Reason", readonly=True)
    
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
    
    # Monetary fields in MAD
    price_subtotal_mad = fields.Float(string="Subtotal (MAD)", readonly=True)
    price_tax_mad = fields.Float(string="Tax (MAD)", readonly=True)
    price_total_mad = fields.Float(string="Total (MAD)", readonly=True)
    
    # Discount information
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
            , s.order_type as order_type
            , s.is_export as is_export
            , s.destination_country_id as destination_country_id
            , s.is_vat_exempt as is_vat_exempt
            , s.vat_exemption_reason as vat_exemption_reason
            , s.delivery_term as delivery_term
            , s.shipping_method as shipping_method
            , l.price_subtotal_mad as price_subtotal_mad
            , l.price_tax_mad as price_tax_mad
            , l.price_total_mad as price_total_mad
            , l.discount_reason as discount_reason
            , pt.vat_rate as vat_rate
            , (s.state = 'bl') as is_bl
            , s.bl_number as bl_number
            , s.bl_date as bl_date
            , s.to_invoice_end_of_month as to_invoice_end_of_month
            , s.month_to_invoice as month_to_invoice
        """
    
    def _from_additional_fields(self):
        return """
        """
    
    def _group_by_additional_fields(self):
        return """
            , s.order_type
            , s.is_export
            , s.destination_country_id
            , s.is_vat_exempt
            , s.vat_exemption_reason
            , s.delivery_term
            , s.shipping_method
            , l.price_subtotal_mad
            , l.price_tax_mad
            , l.price_total_mad
            , l.discount_reason
            , pt.vat_rate
            , s.state
            , s.bl_number
            , s.bl_date
            , s.to_invoice_end_of_month
            , s.month_to_invoice
        """
    
    def _select(self):
        return super(SaleReport, self)._select() + self._select_additional_fields()
    
    def _from(self):
        return super(SaleReport, self)._from() + self._from_additional_fields()
    
    def _group_by(self):
        return super(SaleReport, self)._group_by() + self._group_by_additional_fields()
