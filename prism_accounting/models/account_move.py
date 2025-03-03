from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero
from datetime import datetime, timedelta

class AccountMove(models.Model):
    _name = 'account.move'
    _description = 'Journal Entry'
    _order = 'date desc, name desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Number', required=True, readonly=True, copy=False, default='/')
    date = fields.Date(string='Date', required=True, index=True, readonly=True,
                     states={'draft': [('readonly', False)]}, default=fields.Date.context_today)
    ref = fields.Char(string='Reference', copy=False)
    narration = fields.Text(string='Narration')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True, default='draft')
    
    move_type = fields.Selection([
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'),
    ], string='Type', required=True, readonly=True, tracking=True, change_default=True, default='entry')
    
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                               states={'draft': [('readonly', False)]}, tracking=True)
    
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                               states={'draft': [('readonly', False)]},
                               default=lambda self: self.env.company)
    
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True,
                               states={'draft': [('readonly', False)]}, tracking=True)
    
    commercial_partner_id = fields.Many2one('res.partner', string='Commercial Entity',
                                          compute='_compute_commercial_partner', store=True)
    
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                states={'draft': [('readonly', False)]},
                                default=lambda self: self.env.company.currency_id)
    
    line_ids = fields.One2many('account.move.line', 'move_id', string='Journal Items', copy=True, readonly=True,
                             states={'draft': [('readonly', False)]})
    
    invoice_line_ids = fields.One2many('account.move.line', 'move_id', string='Invoice Lines',
                                     domain=[('exclude_from_invoice_tab', '=', False)], copy=True, readonly=True,
                                     states={'draft': [('readonly', False)]})
    
    tax_line_ids = fields.One2many('account.move.line', 'move_id', string='Tax Lines',
                                  domain=[('tax_line_id', '!=', False)], copy=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    
    # Amounts
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_compute_amount')
    amount_tax = fields.Monetary(string='Tax', store=True, readonly=True, compute='_compute_amount')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount')
    amount_residual = fields.Monetary(string='Amount Due', compute='_compute_amount')
    amount_untaxed_signed = fields.Monetary(string='Untaxed Amount Signed', compute='_compute_amount')
    amount_tax_signed = fields.Monetary(string='Tax Signed', compute='_compute_amount')
    amount_total_signed = fields.Monetary(string='Total Signed', compute='_compute_amount')
    amount_residual_signed = fields.Monetary(string='Amount Due Signed', compute='_compute_amount')
    
    # Dates
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, states={'draft': [('readonly', False)]},
                             index=True, copy=False)
    invoice_date_due = fields.Date(string='Due Date', readonly=True, states={'draft': [('readonly', False)]},
                                 index=True, copy=False)
    
    # Payment (deprecated field kept for compatibility)
    invoice_payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
    ], string='Payment Status (Deprecated)', compute='_compute_invoice_payment_state', store=True, readonly=True, copy=False, default='not_paid')
    
    payment_id = fields.Many2one('account.payment', string='Payment', copy=False)
    statement_line_id = fields.Many2one('account.bank.statement.line', string='Statement Line', copy=False)
    
    # Misc
    invoice_user_id = fields.Many2one('res.users', string='Salesperson', tracking=True,
                                    readonly=True, states={'draft': [('readonly', False)]},
                                    default=lambda self: self.env.user)
    
    invoice_origin = fields.Char(string='Origin', readonly=True, tracking=True,
                               help="Reference of the document that generated this invoice.")
    
    invoice_payment_ref = fields.Char(string='Payment Reference', copy=False,
                                    help="The payment reference to set on journal items.")
    
    invoice_sent = fields.Boolean(string='Invoice Sent', default=False,
                                help="It indicates that the invoice has been sent.")
    
    # For Moroccan accounting
    is_moroccan_move = fields.Boolean(string='Is Moroccan Move', default=True)
    
    moroccan_move_type = fields.Selection([
        ('standard', 'Standard Entry'),
        ('opening', 'Opening Entry'),
        ('closing', 'Closing Entry'),
        ('adjustment', 'Adjustment Entry'),
        ('reversal', 'Reversal Entry'),
        ('reclassification', 'Reclassification Entry'),
    ], string='Moroccan Move Type', default='standard')
    
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',
                                       readonly=True, states={'draft': [('readonly', False)]})
    
    # For VAT reporting
    vat_reporting_date = fields.Date(string='VAT Reporting Date',
                                   help="Date used for VAT reporting if different from the move date.")
    
    # For IS (Corporate Tax) reporting
    is_reporting_date = fields.Date(string='IS Reporting Date',
                                  help="Date used for IS reporting if different from the move date.")
    
    # For IR (Income Tax) reporting
    ir_reporting_date = fields.Date(string='IR Reporting Date',
                                  help="Date used for IR reporting if different from the move date.")
    
    # For weighted average cost calculation
    affects_inventory_valuation = fields.Boolean(string='Affects Inventory Valuation', compute='_compute_affects_inventory_valuation',
                                              help="Whether this move affects inventory valuation.")
    
    inventory_valuation_method = fields.Selection([
        ('fifo', 'First In First Out (FIFO)'),
        ('lifo', 'Last In First Out (LIFO)'),
        ('average', 'Weighted Average Cost (CUMP)'),
        ('standard', 'Standard Cost'),
    ], string='Inventory Valuation Method', compute='_compute_inventory_valuation_method')
    
    # For audit trail
    posted_by = fields.Many2one('res.users', string='Posted By', readonly=True, copy=False)
    posted_date = fields.Datetime(string='Posted Date', readonly=True, copy=False)
    
    cancelled_by = fields.Many2one('res.users', string='Cancelled By', readonly=True, copy=False)
    cancelled_date = fields.Datetime(string='Cancelled Date', readonly=True, copy=False)
    
    # For approval workflow
    requires_approval = fields.Boolean(string='Requires Approval', default=False)
    approval_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval Status', default='not_required', tracking=True)
    
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    approved_date = fields.Datetime(string='Approved Date', readonly=True, copy=False)
    
    rejected_by = fields.Many2one('res.users', string='Rejected By', readonly=True, copy=False)
    rejected_date = fields.Datetime(string='Rejected Date', readonly=True, copy=False)
    
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True, copy=False)
    
    # For document management
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    # For reconciliation
    to_check = fields.Boolean(string='To Check', default=False, tracking=True,
                            help="If checked, the entry will be displayed in red in the journal entries list.")
    
    # For bank reconciliation
    statement_ids = fields.One2many('account.bank.statement.line', 'move_id', string='Bank Statement Lines')
    
    # For cash control
    cash_register_id = fields.Many2one('account.bank.statement', string='Cash Register')
    
    # For invoice validation
    invoice_validate_date = fields.Date(string='Invoice Validation Date', readonly=True, copy=False)
    invoice_validated_by = fields.Many2one('res.users', string='Invoice Validated By', readonly=True, copy=False)
    
    # For invoice cancellation
    invoice_cancel_date = fields.Date(string='Invoice Cancellation Date', readonly=True, copy=False)
    invoice_cancelled_by = fields.Many2one('res.users', string='Invoice Cancelled By', readonly=True, copy=False)
    
    # For invoice refund
    refund_invoice_id = fields.Many2one('account.move', string='Refunded Invoice', readonly=True, copy=False)
    refund_reason = fields.Text(string='Refund Reason', readonly=True, copy=False)
    
    # For invoice payment
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
    ], string='Payment Status', compute='_compute_payment_state', store=True, readonly=True, copy=False, default='not_paid')
    
    # For invoice due date
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
                                           readonly=True, states={'draft': [('readonly', False)]})
    
    # For invoice discount
    invoice_discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Discount Type', readonly=True, states={'draft': [('readonly', False)]})
    
    invoice_discount_amount = fields.Float(string='Discount Amount', readonly=True, states={'draft': [('readonly', False)]})
    
    # For invoice rounding
    invoice_rounding = fields.Boolean(string='Round Total', readonly=True, states={'draft': [('readonly', False)]})
    invoice_rounding_method = fields.Selection([
        ('up', 'Round Up'),
        ('down', 'Round Down'),
        ('half_up', 'Round Half Up'),
        ('half_down', 'Round Half Down'),
    ], string='Rounding Method', readonly=True, states={'draft': [('readonly', False)]})
    
    # For invoice notes
    invoice_note = fields.Text(string='Invoice Note', readonly=True, states={'draft': [('readonly', False)]})
    
    # For invoice terms and conditions
    invoice_terms = fields.Text(string='Terms and Conditions', readonly=True, states={'draft': [('readonly', False)]})
    
    @api.depends('partner_id')
    def _compute_commercial_partner(self):
        for move in self:
            move.commercial_partner_id = move.partner_id.commercial_partner_id or move.partner_id
    
    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id')
    def _compute_amount(self):
        for move in self:
            move.amount_untaxed = sum(line.price_subtotal for line in move.invoice_line_ids)
            move.amount_tax = sum(line.price_total for line in move.tax_line_ids)
            move.amount_total = move.amount_untaxed + move.amount_tax
            move.amount_residual = move.amount_total
            
            # Signed amounts
            sign = -1 if move.move_type in ['out_refund', 'in_refund'] else 1
            move.amount_untaxed_signed = sign * move.amount_untaxed
            move.amount_tax_signed = sign * move.amount_tax
            move.amount_total_signed = sign * move.amount_total
            move.amount_residual_signed = sign * move.amount_residual
    
    @api.depends('payment_state')
    def _compute_invoice_payment_state(self):
        for move in self:
            # Map payment_state to invoice_payment_state for backward compatibility
            if move.payment_state == 'paid':
                move.invoice_payment_state = 'paid'
            elif move.payment_state in ['partial', 'in_payment']:
                move.invoice_payment_state = 'in_payment'
            else:
                move.invoice_payment_state = 'not_paid'
    
    @api.depends('line_ids.account_id', 'line_ids.account_id.is_inventory_account')
    def _compute_affects_inventory_valuation(self):
        for move in self:
            move.affects_inventory_valuation = any(line.account_id.is_inventory_account for line in move.line_ids)
    
    @api.depends('line_ids.account_id', 'line_ids.account_id.inventory_valuation_method')
    def _compute_inventory_valuation_method(self):
        for move in self:
            inventory_accounts = move.line_ids.filtered(lambda l: l.account_id.is_inventory_account).mapped('account_id')
            methods = inventory_accounts.mapped('inventory_valuation_method')
            
            if not methods:
                move.inventory_valuation_method = False
            elif len(set(methods)) == 1:
                move.inventory_valuation_method = methods[0]
            else:
                # If there are multiple methods, use the company's default method
                move.inventory_valuation_method = move.company_id.inventory_valuation_method
    
    @api.depends('line_ids.matched_debit_ids', 'line_ids.matched_credit_ids', 'line_ids.account_id')
    def _compute_payment_state(self):
        for move in self:
            if move.move_type == 'entry' or move.is_outbound():
                move.payment_state = 'not_paid'
                continue
            
            if move.state != 'posted':
                move.payment_state = 'not_paid'
                continue
            
            # Check if the move is fully paid
            reconciled_lines = move.line_ids.filtered(lambda line: line.account_id.internal_type in ('receivable', 'payable'))
            if not reconciled_lines:
                move.payment_state = 'paid'
                continue
            
            # Check if the move is partially paid
            if all(line.reconciled for line in reconciled_lines):
                move.payment_state = 'paid'
            elif any(line.reconciled for line in reconciled_lines):
                move.payment_state = 'partial'
            else:
                move.payment_state = 'not_paid'
    
    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id or self.company_id.currency_id
            
            # Set default accounts based on journal type
            if self.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                self.fiscal_position_id = self.partner_id.property_account_position_id
            elif self.move_type in ['in_invoice', 'in_refund', 'in_receipt']:
                self.fiscal_position_id = self.partner_id.property_account_position_id
    
    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id:
            self.fiscal_position_id = self.partner_id.property_account_position_id
            
            # Set payment terms based on partner
            if self.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                self.invoice_payment_term_id = self.partner_id.property_payment_term_id
            elif self.move_type in ['in_invoice', 'in_refund', 'in_receipt']:
                self.invoice_payment_term_id = self.partner_id.property_supplier_payment_term_id
    
    @api.onchange('invoice_payment_term_id', 'invoice_date')
    def _onchange_payment_term(self):
        if self.invoice_payment_term_id and self.invoice_date:
            self.invoice_date_due = self.invoice_payment_term_id.compute(self.amount_total, self.invoice_date)[-1][0]
        elif self.invoice_date:
            self.invoice_date_due = self.invoice_date
    
    def action_post(self):
        """Post the journal entry"""
        for move in self:
            if move.state != 'draft':
                raise UserError(_("Only draft moves can be posted."))
            
            if move.requires_approval and move.approval_state not in ['approved', 'not_required']:
                raise UserError(_("This move requires approval before posting."))
            
            if not move.line_ids:
                raise UserError(_("You cannot post an empty journal entry."))
            
            if not move.name or move.name == '/':
                # Get sequence
                sequence = move.journal_id.sequence_id
                if move.move_type in ['out_refund', 'in_refund'] and move.journal_id.refund_sequence:
                    sequence = move.journal_id.refund_sequence_id
                
                if not sequence:
                    raise UserError(_("Please define a sequence on your journal."))
                
                move.name = sequence.next_by_id()
            
            # Check if the move is balanced
            if not move._check_balanced():
                raise UserError(_("The move is not balanced."))
            
            # Post the move
            move.state = 'posted'
            move.posted_by = self.env.user.id
            move.posted_date = fields.Datetime.now()
            
            # Update invoice validation date
            if move.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt']:
                move.invoice_validate_date = fields.Date.today()
                move.invoice_validated_by = self.env.user.id
            
            # Create activity for sales team if configured
            if move.move_type in ['out_invoice', 'out_refund'] and move.journal_id.sale_activity_type_id:
                activity_type = move.journal_id.sale_activity_type_id
                user = move.journal_id.sale_activity_user_id or self.env.user
                
                self.env['mail.activity'].create({
                    'activity_type_id': activity_type.id,
                    'note': move.journal_id.sale_activity_note or '',
                    'res_id': move.id,
                    'res_model_id': self.env['ir.model']._get('account.move').id,
                    'user_id': user.id,
                })
        
        return True
    
    def action_cancel(self):
        """Cancel the journal entry"""
        for move in self:
            if move.state != 'posted':
                raise UserError(_("Only posted moves can be cancelled."))
            
            # Cancel the move
            move.state = 'cancel'
            move.cancelled_by = self.env.user.id
            move.cancelled_date = fields.Datetime.now()
            
            # Update invoice cancellation date
            if move.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt']:
                move.invoice_cancel_date = fields.Date.today()
                move.invoice_cancelled_by = self.env.user.id
        
        return True
    
    def action_draft(self):
        """Reset the journal entry to draft"""
        for move in self:
            if move.state != 'cancel':
                raise UserError(_("Only cancelled moves can be reset to draft."))
            
            # Reset the move to draft
            move.state = 'draft'
            
            # Reset approval state if required
            if move.requires_approval:
                move.approval_state = 'pending'
        
        return True
    
    def action_request_approval(self):
        """Request approval for the journal entry"""
        for move in self:
            if move.state != 'draft':
                raise UserError(_("Only draft moves can be submitted for approval."))
            
            # Set approval state to pending
            move.requires_approval = True
            move.approval_state = 'pending'
            
            # Create activity for approvers
            approvers = self.env.ref('accounting.group_account_manager').users
            
            for approver in approvers:
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'note': _("Please review and approve this journal entry."),
                    'res_id': move.id,
                    'res_model_id': self.env['ir.model']._get('account.move').id,
                    'user_id': approver.id,
                })
        
        return True
    
    def action_approve(self):
        """Approve the journal entry"""
        for move in self:
            if move.approval_state != 'pending':
                raise UserError(_("Only pending moves can be approved."))
            
            # Set approval state to approved
            move.approval_state = 'approved'
            move.approved_by = self.env.user.id
            move.approved_date = fields.Datetime.now()
        
        return True
    
    def action_reject(self):
        """Reject the journal entry"""
        for move in self:
            if move.approval_state != 'pending':
                raise UserError(_("Only pending moves can be rejected."))
            
            # Set approval state to rejected
            move.approval_state = 'rejected'
            move.rejected_by = self.env.user.id
            move.rejected_date = fields.Datetime.now()
            
            # Ask for rejection reason
            return {
                'name': _('Rejection Reason'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move.reject.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_move_id': move.id},
            }
        
        return True
    
    def _check_balanced(self):
        """Check if the move is balanced"""
        for move in self:
            # Check if the move is balanced
            debit = sum(line.debit for line in move.line_ids)
            credit = sum(line.credit for line in move.line_ids)
            
            if not float_is_zero(debit - credit, precision_digits=2):
                return False
        
        return True
    
    def is_outbound(self):
        """Check if the move is an outbound payment"""
        self.ensure_one()
        return self.move_type in ['out_invoice', 'out_refund', 'out_receipt']
    
    def is_inbound(self):
        """Check if the move is an inbound payment"""
        self.ensure_one()
        return self.move_type in ['in_invoice', 'in_refund', 'in_receipt']
    
    def is_invoice(self):
        """Check if the move is an invoice"""
        self.ensure_one()
        return self.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']
    
    def is_sale(self):
        """Check if the move is a sale"""
        self.ensure_one()
        return self.move_type in ['out_invoice', 'out_refund', 'out_receipt']
    
    def is_purchase(self):
        """Check if the move is a purchase"""
        self.ensure_one()
        return self.move_type in ['in_invoice', 'in_refund', 'in_receipt']
    
    def action_register_payment(self):
        """Register payment for the journal entry"""
        self.ensure_one()
        
        if self.state != 'posted':
            raise UserError(_("You can only register payment for posted moves."))
        
        if self.payment_state == 'paid':
            raise UserError(_("This move is already paid."))
        
        return {
            'name': _('Register Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_ids': self.ids, 'active_model': 'account.move'},
        }
    
    def action_view_payments(self):
        """View payments for the journal entry"""
        self.ensure_one()
        
        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('move_id', '=', self.id)],
        }
    
    def action_view_invoices(self):
        """View invoices for the journal entry"""
        self.ensure_one()
        
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.id)],
        }
    
    def action_send_invoice(self):
        """Send invoice by email"""
        self.ensure_one()
        
        if self.move_type not in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']:
            raise UserError(_("You can only send invoices by email."))
        
        template = self.env.ref('accounting.email_template_invoice', False)
        
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
        )
        
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
    
    def action_print_invoice(self):
        """Print invoice"""
        self.ensure_one()
        
        if self.move_type not in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']:
            raise UserError(_("You can only print invoices."))
        
        return self.env.ref('accounting.action_report_invoice').report_action(self)
    
    def action_duplicate(self):
        """Duplicate the journal entry"""
        self.ensure_one()
        
        # Copy the move
        new_move = self.copy()
        
        # Open the new move
        return {
            'name': _('Journal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': new_move.id,
        }
    
    def action_reverse(self):
        """Reverse the journal entry"""
        self.ensure_one()
        
        if self.state != 'posted':
            raise UserError(_("You can only reverse posted moves."))
        
        return {
            'name': _('Reverse Move'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.reversal',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_ids': self.ids, 'active_model': 'account.move'},
        }
    
    def action_open_reconcile(self):
        """Open reconciliation view for the journal entry"""
        self.ensure_one()
        
        return {
            'name': _('Reconcile'),
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
            'context': {'active_ids': self.ids, 'active_model': 'account.move'},
        }
    
    def action_mark_as_checked(self):
        """Mark the journal entry as checked"""
        self.ensure_one()
        
        self.to_check = True
    
    def action_unmark_as_checked(self):
        """Unmark the journal entry as checked"""
        self.ensure_one()
        
        self.to_check = False


class AccountMoveRejectWizard(models.TransientModel):
    _name = 'account.move.reject.wizard'
    _description = 'Journal Entry Rejection Wizard'
    
    move_id = fields.Many2one('account.move', string='Journal Entry', required=True)
    reason = fields.Text(string='Rejection Reason', required=True)
    
    def action_confirm(self):
        """Confirm rejection"""
        self.ensure_one()
        
        # Set rejection reason
        self.move_id.rejection_reason = self.reason
        
        return {'type': 'ir.actions.act_window_close'}
