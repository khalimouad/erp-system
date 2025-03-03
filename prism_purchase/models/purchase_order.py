from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    # Moroccan-specific fields
    order_type = fields.Selection([
        ('standard', 'Standard Order'),
        ('import', 'Import Order'),
        ('free_zone', 'Free Zone Order'),
        ('government', 'Government Order')
    ], string="Order Type", default='standard', required=True,
       help="Type of purchase order according to Moroccan regulations")
    
    is_import = fields.Boolean(string="Is Import", compute='_compute_is_import', store=True)
    
    origin_country_id = fields.Many2one('res.country', string="Origin Country",
                                       help="For import orders, the country of origin")
    
    # Document references
    reference_number = fields.Char(string="Reference Number", 
                                  help="Vendor reference number for this order")
    
    quotation_validity = fields.Integer(string="Quotation Validity (Days)", default=30,
                                      help="Number of days the quotation is valid")
    
    quotation_expiry_date = fields.Date(string="Quotation Expiry Date", compute='_compute_quotation_expiry_date',
                                      store=True, help="Date when the quotation expires")
    
    # Payment and delivery terms
    payment_term_notes = fields.Text(string="Payment Term Notes")
    
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
    ], string="Delivery Terms", default='ex_works')
    
    shipping_method = fields.Selection([
        ('road', 'Road'),
        ('sea', 'Sea'),
        ('air', 'Air'),
        ('rail', 'Rail'),
        ('multi', 'Multimodal')
    ], string="Shipping Method", default='road')
    
    # Additional fields
    expected_delivery_date = fields.Date(string="Expected Delivery Date")
    
    notes = fields.Text(string="Notes")
    
    # VAT related fields
    is_vat_reverse_charge = fields.Boolean(string="VAT Reverse Charge", default=False,
                                         help="Apply reverse charge mechanism for VAT")
    
    reverse_charge_reason = fields.Selection([
        ('import', 'Import Purchase'),
        ('free_zone', 'Free Zone Purchase'),
        ('non_resident', 'Non-resident Vendor'),
        ('other', 'Other')
    ], string="Reverse Charge Reason")
    
    # Import-specific fields
    customs_declaration_number = fields.Char(string="Customs Declaration Number")
    
    customs_declaration_date = fields.Date(string="Customs Declaration Date")
    
    customs_value = fields.Monetary(string="Customs Value", currency_field='currency_id')
    
    customs_duty = fields.Monetary(string="Customs Duty", currency_field='currency_id')
    
    import_vat = fields.Monetary(string="Import VAT", currency_field='currency_id')
    
    # Computed fields
    amount_untaxed_mad = fields.Monetary(string="Untaxed Amount (MAD)", compute='_compute_amounts_in_mad',
                                       store=True, help="Total untaxed amount in Moroccan Dirhams")
    
    amount_tax_mad = fields.Monetary(string="Tax Amount (MAD)", compute='_compute_amounts_in_mad',
                                   store=True, help="Total tax amount in Moroccan Dirhams")
    
    amount_total_mad = fields.Monetary(string="Total Amount (MAD)", compute='_compute_amounts_in_mad',
                                     store=True, help="Total amount in Moroccan Dirhams")
    
    exchange_rate = fields.Float(string="Exchange Rate", digits=(16, 6), default=1.0,
                               help="Exchange rate from company currency to MAD")
    
    # Approval workflow
    requires_approval = fields.Boolean(string="Requires Approval", compute='_compute_requires_approval',
                                     store=True, help="Whether this order requires manager approval")
    
    approval_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Approval Status", default='not_required')
    
    approved_by = fields.Many2one('res.users', string="Approved By")
    
    approval_date = fields.Datetime(string="Approval Date")
    
    @api.depends('order_type')
    def _compute_is_import(self):
        for order in self:
            order.is_import = order.order_type in ['import', 'free_zone']
    
    @api.depends('date_order', 'quotation_validity')
    def _compute_quotation_expiry_date(self):
        for order in self:
            if order.date_order and order.quotation_validity:
                order.quotation_expiry_date = order.date_order.date() + timedelta(days=order.quotation_validity)
            else:
                order.quotation_expiry_date = False
    
    @api.depends('amount_untaxed', 'amount_tax', 'exchange_rate')
    def _compute_amounts_in_mad(self):
        for order in self:
            order.amount_untaxed_mad = order.amount_untaxed * order.exchange_rate
            order.amount_tax_mad = order.amount_tax * order.exchange_rate
            order.amount_total_mad = order.amount_total * order.exchange_rate
    
    @api.depends('amount_total', 'order_type')
    def _compute_requires_approval(self):
        for order in self:
            # Orders above 100,000 MAD or import orders require approval
            order.requires_approval = (order.amount_total_mad > 100000) or (order.order_type in ['import', 'free_zone'])
    
    @api.onchange('order_type')
    def _onchange_order_type(self):
        if self.order_type == 'import':
            self.is_vat_reverse_charge = True
            self.reverse_charge_reason = 'import'
        elif self.order_type == 'free_zone':
            self.is_vat_reverse_charge = True
            self.reverse_charge_reason = 'free_zone'
        elif self.order_type == 'standard' and self.partner_id and not self.partner_id.country_id.code == 'MA':
            self.is_vat_reverse_charge = True
            self.reverse_charge_reason = 'non_resident'
        else:
            self.is_vat_reverse_charge = False
            self.reverse_charge_reason = False
    
    @api.onchange('is_vat_reverse_charge')
    def _onchange_is_vat_reverse_charge(self):
        if not self.is_vat_reverse_charge:
            self.reverse_charge_reason = False
    
    def button_confirm(self):
        # Check if approval is required but not yet approved
        for order in self:
            if order.requires_approval and order.approval_state not in ['approved', 'not_required']:
                raise ValidationError(_("This order requires approval before confirmation."))
        
        return super(PurchaseOrder, self).button_confirm()
    
    def action_request_approval(self):
        for order in self:
            if order.requires_approval:
                order.approval_state = 'pending'
    
    def action_approve(self):
        self.ensure_one()
        self.approval_state = 'approved'
        self.approved_by = self.env.user
        self.approval_date = fields.Datetime.now()
    
    def action_reject(self):
        self.ensure_one()
        self.approval_state = 'rejected'
