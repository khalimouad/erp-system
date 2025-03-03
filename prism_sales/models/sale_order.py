from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Moroccan-specific fields
    order_type = fields.Selection([
        ('standard', 'Standard Order'),
        ('export', 'Export Order'),
        ('free_zone', 'Free Zone Order'),
        ('government', 'Government Order')
    ], string="Order Type", default='standard', required=True,
       help="Type of sale order according to Moroccan regulations")
    
    # Bon de Livraison (BL) fields
    is_bl = fields.Boolean(string="Is Bon de Livraison", compute='_compute_is_bl', store=True)
    bl_number = fields.Char(string="BL Number", readonly=True, copy=False)
    bl_date = fields.Date(string="BL Date")
    bl_printed = fields.Boolean(string="BL Printed", default=False)
    bl_notes = fields.Text(string="BL Notes")
    
    # End of month invoicing
    to_invoice_end_of_month = fields.Boolean(string="Invoice End of Month", default=False,
                                           help="If checked, this BL will be invoiced at the end of the month")
    month_to_invoice = fields.Char(string="Month to Invoice", compute='_compute_month_to_invoice', store=True)
    
    is_export = fields.Boolean(string="Is Export", compute='_compute_is_export', store=True)
    
    destination_country_id = fields.Many2one('res.country', string="Destination Country",
                                           help="For export orders, the destination country")
    
    # Document references
    reference_number = fields.Char(string="Reference Number", 
                                  help="Customer reference number for this order")
    
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
    is_vat_exempt = fields.Boolean(string="VAT Exempt", default=False)
    
    vat_exemption_reason = fields.Selection([
        ('export', 'Export Sale'),
        ('free_zone', 'Free Zone Sale'),
        ('diplomatic', 'Diplomatic Sale'),
        ('government', 'Government Sale'),
        ('other', 'Other')
    ], string="VAT Exemption Reason")
    
    vat_exemption_certificate = fields.Char(string="VAT Exemption Certificate")
    
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
    
    # Extended state field to include BL states
    state = fields.Selection(selection_add=[
        ('bl', 'Bon de Livraison'),
        ('to_invoice', 'To Invoice'),
        ('returned', 'Returned')
    ])
    
    @api.depends('order_type')
    def _compute_is_export(self):
        for order in self:
            order.is_export = order.order_type in ['export', 'free_zone']
    
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
    
    @api.depends('state')
    def _compute_is_bl(self):
        for order in self:
            order.is_bl = order.state == 'bl'
    
    @api.depends('bl_date', 'to_invoice_end_of_month')
    def _compute_month_to_invoice(self):
        for order in self:
            if order.to_invoice_end_of_month and order.bl_date:
                order.month_to_invoice = order.bl_date.strftime('%Y-%m')
            else:
                order.month_to_invoice = False
    
    @api.depends('amount_total', 'order_type')
    def _compute_requires_approval(self):
        for order in self:
            # Orders above 50,000 MAD or export orders require approval
            order.requires_approval = (order.amount_total_mad > 50000) or (order.order_type in ['export', 'free_zone'])
    
    @api.onchange('order_type')
    def _onchange_order_type(self):
        if self.order_type == 'export':
            self.is_vat_exempt = True
            self.vat_exemption_reason = 'export'
        elif self.order_type == 'free_zone':
            self.is_vat_exempt = True
            self.vat_exemption_reason = 'free_zone'
        elif self.order_type == 'government':
            self.is_vat_exempt = True
            self.vat_exemption_reason = 'government'
        else:
            self.is_vat_exempt = False
            self.vat_exemption_reason = False
    
    @api.onchange('is_vat_exempt')
    def _onchange_is_vat_exempt(self):
        if not self.is_vat_exempt:
            self.vat_exemption_reason = False
            self.vat_exemption_certificate = False
    
    def action_confirm(self):
        """Override to add BL-specific logic when confirming a sale order"""
        # Check if approval is required but not yet approved
        for order in self:
            if order.requires_approval and order.approval_state not in ['approved', 'not_required']:
                raise ValidationError(_("This order requires approval before confirmation."))
        
        res = super(SaleOrder, self).action_confirm()
        
        # Generate BL number and move to BL state
        for order in self:
            if not order.bl_number:
                order.bl_number = self.env['ir.sequence'].next_by_code('sale.order.bl') or _('New BL')
            order.write({
                'state': 'bl',
                'bl_date': fields.Date.today()
            })
        
        return res
    
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
    
    def action_print_bl(self):
        """Print the Bon de Livraison"""
        self.ensure_one()
        if self.state != 'bl':
            raise UserError(_("You can only print a Bon de Livraison in BL state."))
        
        self.bl_printed = True
        return self.env.ref('sales.action_report_bon_de_livraison').report_action(self)
    
    def action_create_invoice(self):
        """Create invoice from BL"""
        self.ensure_one()
        if self.state != 'bl':
            raise UserError(_("You can only create an invoice for a Bon de Livraison."))
        
        # Create invoice
        invoice = self._create_invoices()
        self.write({'state': 'to_invoice'})
        return invoice
    
    def action_return_bl(self):
        """Process a return for this BL"""
        self.ensure_one()
        if self.state != 'bl':
            raise UserError(_("You can only return a Bon de Livraison."))
        
        # Create return picking
        return_wizard = self.env['stock.return.picking'].with_context(
            active_id=self.picking_ids[0].id,
            active_model='stock.picking'
        ).create({})
        return_wizard.product_return_moves.write({'quantity': 1.0})
        new_picking_id, pick_type_id = return_wizard._create_returns()
        
        # Update state
        self.write({'state': 'returned'})
        
        # Show the return picking
        return {
            'name': _('Return Picking'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': new_picking_id,
            'type': 'ir.actions.act_window',
        }
    
    @api.model
    def create_end_of_month_invoices(self):
        """Create invoices for all BLs marked for end-of-month invoicing"""
        # Get current month
        current_month = fields.Date.today().strftime('%Y-%m')
        
        # Find all BLs to invoice for this month
        orders_to_invoice = self.search([
            ('state', '=', 'bl'),
            ('to_invoice_end_of_month', '=', True),
            ('month_to_invoice', '=', current_month)
        ])
        
        # Group by partner
        partner_orders = {}
        for order in orders_to_invoice:
            if order.partner_id not in partner_orders:
                partner_orders[order.partner_id] = []
            partner_orders[order.partner_id].append(order)
        
        # Create one invoice per partner
        invoices = []
        for partner, orders in partner_orders.items():
            # Create invoice
            invoice = orders[0]._create_invoices(final=True)
            invoices.append(invoice.id)
            
            # Update orders
            for order in orders:
                order.write({'state': 'to_invoice'})
        
        return invoices
