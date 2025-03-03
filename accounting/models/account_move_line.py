from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero
from datetime import datetime, timedelta

class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _description = 'Journal Item'
    _order = 'date desc, move_id desc, id'
    
    # Basic fields
    name = fields.Char(string='Label', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price', default=0.0)
    discount = fields.Float(string='Discount (%)', default=0.0)
    debit = fields.Monetary(string='Debit', default=0.0)
    credit = fields.Monetary(string='Credit', default=0.0)
    balance = fields.Monetary(string='Balance', compute='_compute_balance', store=True)
    amount_currency = fields.Monetary(string='Amount in Currency', default=0.0,
                                    help="The amount expressed in the secondary currency, if there is one.")
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_price', store=True)
    price_total = fields.Monetary(string='Total', compute='_compute_price', store=True)
    
    # Related fields
    move_id = fields.Many2one('account.move', string='Journal Entry', required=True, index=True, ondelete='cascade')
    journal_id = fields.Many2one(related='move_id.journal_id', string='Journal', store=True, index=True)
    company_id = fields.Many2one(related='move_id.company_id', string='Company', store=True, index=True)
    date = fields.Date(related='move_id.date', string='Date', store=True, index=True)
    ref = fields.Char(related='move_id.ref', string='Reference', store=True)
    parent_state = fields.Selection(related='move_id.state', string='State', store=True)
    move_type = fields.Selection(related='move_id.type', string='Move Type', store=True)
    
    # Account fields
    account_id = fields.Many2one('account.account', string='Account', required=True, index=True,
                               domain="[('deprecated', '=', False), ('company_id', '=', company_id)]")
    account_internal_type = fields.Selection(related='account_id.internal_type', string='Internal Type', store=True)
    account_root_id = fields.Many2one(related='account_id.root_id', string='Account Root', store=True)
    
    # Partner fields
    partner_id = fields.Many2one('res.partner', string='Partner', index=True)
    
    # Currency fields
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                help="The currency used for this line.")
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency', store=True)
    
    # Tax fields
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes applied on this line.")
    tax_line_id = fields.Many2one('account.tax', string='Originator Tax', ondelete='restrict',
                                help="The tax that created this tax line.")
    tax_group_id = fields.Many2one(related='tax_line_id.tax_group_id', string='Tax Group', store=True)
    tax_base_amount = fields.Monetary(string='Base Amount', store=True)
    
    # Reconciliation fields
    reconciled = fields.Boolean(string='Reconciled', compute='_compute_reconciled', store=True)
    full_reconcile_id = fields.Many2one('account.full.reconcile', string='Matching Number', copy=False, index=True)
    matched_debit_ids = fields.One2many('account.partial.reconcile', 'credit_move_id', string='Matched Debits')
    matched_credit_ids = fields.One2many('account.partial.reconcile', 'debit_move_id', string='Matched Credits')
    
    # Analytic fields
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    
    # Invoice fields
    exclude_from_invoice_tab = fields.Boolean(string='Exclude from Invoice Tab', default=False,
                                           help="If checked, this line will not be displayed in the invoice tab.")
    
    # Product fields
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    
    # Sequence
    sequence = fields.Integer(string='Sequence', default=10)
    
    # For Moroccan accounting
    is_moroccan_line = fields.Boolean(string='Is Moroccan Line', default=True)
    
    # For VAT reporting
    vat_line_type = fields.Selection([
        ('base', 'Base'),
        ('tax', 'Tax'),
    ], string='VAT Line Type')
    
    vat_tax_type = fields.Selection([
        ('input', 'Input VAT'),
        ('output', 'Output VAT'),
    ], string='VAT Tax Type')
    
    # For IS (Corporate Tax) reporting
    is_line_type = fields.Selection([
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('tax', 'Tax'),
    ], string='IS Line Type')
    
    # For IR (Income Tax) reporting
    ir_line_type = fields.Selection([
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('tax', 'Tax'),
    ], string='IR Line Type')
    
    # For weighted average cost calculation
    affects_inventory_valuation = fields.Boolean(string='Affects Inventory Valuation',
                                              related='account_id.is_inventory_account')
    
    inventory_valuation_method = fields.Selection([
        ('fifo', 'First In First Out (FIFO)'),
        ('lifo', 'Last In First Out (LIFO)'),
        ('average', 'Weighted Average Cost (CUMP)'),
        ('standard', 'Standard Cost'),
    ], string='Inventory Valuation Method', related='account_id.inventory_valuation_method')
    
    # For audit trail
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now, readonly=True)
    
    # For reconciliation
    to_check = fields.Boolean(string='To Check', default=False,
                            help="If checked, this line will be displayed in red in the journal entries list.")
    
    # For bank reconciliation
    statement_id = fields.Many2one('account.bank.statement', string='Statement')
    statement_line_id = fields.Many2one('account.bank.statement.line', string='Statement Line')
    
    # For cash control
    cash_register_id = fields.Many2one('account.bank.statement', string='Cash Register')
    
    # For invoice validation
    invoice_validated = fields.Boolean(string='Invoice Validated', default=False)
    
    # For invoice cancellation
    invoice_cancelled = fields.Boolean(string='Invoice Cancelled', default=False)
    
    # For invoice refund
    refund_line_id = fields.Many2one('account.move.line', string='Refunded Line')
    
    # For invoice payment
    payment_id = fields.Many2one('account.payment', string='Payment')
    
    # For invoice due date
    date_maturity = fields.Date(string='Due Date')
    
    # For invoice discount
    discount_amount = fields.Monetary(string='Discount Amount', compute='_compute_discount_amount', store=True)
    
    # For invoice rounding
    rounding_amount = fields.Monetary(string='Rounding Amount', default=0.0)
    
    # For invoice notes
    note = fields.Text(string='Note')
    
    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for line in self:
            line.balance = line.debit - line.credit
    
    @api.depends('quantity', 'price_unit', 'discount', 'tax_ids')
    def _compute_price(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids.compute_all(price, line.currency_id, line.quantity, product=line.product_id, partner=line.partner_id)
            line.price_subtotal = taxes['total_excluded']
            line.price_total = taxes['total_included']
    
    @api.depends('discount', 'price_unit', 'quantity')
    def _compute_discount_amount(self):
        for line in self:
            line.discount_amount = line.price_unit * line.quantity * line.discount / 100.0
    
    @api.depends('matched_debit_ids', 'matched_credit_ids')
    def _compute_reconciled(self):
        for line in self:
            line.reconciled = line.account_id.reconcile and (
                (line.matched_debit_ids and line.credit > 0) or
                (line.matched_credit_ids and line.debit > 0)
            )
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.lst_price
            self.product_uom_id = self.product_id.uom_id
            
            # Set taxes based on product
            self.tax_ids = self.product_id.taxes_id
            
            # Set account based on product
            if self.move_id.type in ['out_invoice', 'out_refund', 'out_receipt']:
                self.account_id = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
            elif self.move_id.type in ['in_invoice', 'in_refund', 'in_receipt']:
                self.account_id = self.product_id.property_account_expense_id or self.product_id.categ_id.property_account_expense_categ_id
    
    @api.onchange('account_id')
    def _onchange_account_id(self):
        if self.account_id:
            # Set partner based on account type
            if self.account_id.internal_type in ['receivable', 'payable'] and not self.partner_id:
                self.partner_id = self.move_id.partner_id
            
            # Set date_maturity based on account type
            if self.account_id.internal_type in ['receivable', 'payable']:
                self.date_maturity = self.move_id.invoice_date_due or self.move_id.date
    
    @api.onchange('quantity', 'price_unit', 'discount')
    def _onchange_price(self):
        if self.move_id.type in ['out_invoice', 'out_refund', 'out_receipt', 'in_invoice', 'in_refund', 'in_receipt']:
            # For invoices, set debit/credit based on price
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0) * self.quantity
            
            if self.move_id.type in ['out_invoice', 'in_refund', 'out_receipt']:
                self.debit = 0.0
                self.credit = price
            elif self.move_id.type in ['in_invoice', 'out_refund', 'in_receipt']:
                self.debit = price
                self.credit = 0.0
    
    @api.onchange('debit')
    def _onchange_debit(self):
        if self.debit:
            self.credit = 0.0
    
    @api.onchange('credit')
    def _onchange_credit(self):
        if self.credit:
            self.debit = 0.0
    
    @api.constrains('debit', 'credit')
    def _check_debit_credit(self):
        for line in self:
            if line.debit and line.credit:
                raise ValidationError(_("You cannot have a line with both debit and credit."))
    
    @api.constrains('account_id', 'journal_id')
    def _check_account_journal(self):
        for line in self:
            if line.account_id.company_id != line.journal_id.company_id:
                raise ValidationError(_("The account and journal must belong to the same company."))
    
    def reconcile(self):
        """Reconcile the current line with other lines"""
        self.ensure_one()
        
        if not self.account_id.reconcile:
            raise UserError(_("You cannot reconcile this line because the account does not allow reconciliation."))
        
        if self.reconciled:
            raise UserError(_("This line is already reconciled."))
        
        # Find lines to reconcile with
        domain = [
            ('account_id', '=', self.account_id.id),
            ('partner_id', '=', self.partner_id.id),
            ('reconciled', '=', False),
            ('id', '!=', self.id),
        ]
        
        if self.debit > 0:
            domain.append(('credit', '>', 0))
        else:
            domain.append(('debit', '>', 0))
        
        lines_to_reconcile = self.env['account.move.line'].search(domain)
        
        if not lines_to_reconcile:
            raise UserError(_("No lines found to reconcile with."))
        
        # Reconcile lines
        lines_to_reconcile |= self
        lines_to_reconcile.reconcile()
        
        return True
    
    def remove_move_reconcile(self):
        """Unreconcile the current line"""
        self.ensure_one()
        
        if not self.reconciled:
            raise UserError(_("This line is not reconciled."))
        
        # Remove reconciliation
        self.matched_debit_ids.unlink()
        self.matched_credit_ids.unlink()
        
        return True
    
    def action_open_reconcile(self):
        """Open reconciliation view for the current line"""
        self.ensure_one()
        
        if not self.account_id.reconcile:
            raise UserError(_("You cannot reconcile this line because the account does not allow reconciliation."))
        
        return {
            'name': _('Reconcile'),
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
            'context': {'active_ids': self.ids, 'active_model': 'account.move.line'},
        }
    
    def action_mark_as_checked(self):
        """Mark the line as checked"""
        self.ensure_one()
        
        self.to_check = True
    
    def action_unmark_as_checked(self):
        """Unmark the line as checked"""
        self.ensure_one()
        
        self.to_check = False
    
    def action_open_product(self):
        """Open product form"""
        self.ensure_one()
        
        if not self.product_id:
            raise UserError(_("This line has no product."))
        
        return {
            'name': _('Product'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'form',
            'res_id': self.product_id.id,
        }
    
    def action_open_account(self):
        """Open account form"""
        self.ensure_one()
        
        return {
            'name': _('Account'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.account',
            'view_mode': 'form',
            'res_id': self.account_id.id,
        }
    
    def action_open_partner(self):
        """Open partner form"""
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_("This line has no partner."))
        
        return {
            'name': _('Partner'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.partner_id.id,
        }
    
    def action_open_move(self):
        """Open move form"""
        self.ensure_one()
        
        return {
            'name': _('Journal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
        }
    
    def action_open_full_reconcile(self):
        """Open full reconcile form"""
        self.ensure_one()
        
        if not self.full_reconcile_id:
            raise UserError(_("This line is not fully reconciled."))
        
        return {
            'name': _('Full Reconcile'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.full.reconcile',
            'view_mode': 'form',
            'res_id': self.full_reconcile_id.id,
        }
    
    def action_open_tax(self):
        """Open tax form"""
        self.ensure_one()
        
        if not self.tax_line_id:
            raise UserError(_("This line has no originator tax."))
        
        return {
            'name': _('Tax'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.tax',
            'view_mode': 'form',
            'res_id': self.tax_line_id.id,
        }
