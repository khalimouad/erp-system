from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountAccount(models.Model):
    _name = 'account.account'
    _description = 'Account'
    _order = 'code'
    
    name = fields.Char(string='Account Name', required=True, index=True)
    code = fields.Char(string='Account Code', required=True, index=True)
    account_type = fields.Selection([
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('other', 'Other'),
    ], string='Account Type', required=True)
    
    internal_type = fields.Selection([
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('liquidity', 'Liquidity'),
        ('other', 'Regular'),
    ], string='Internal Type', required=True, default='other')
    
    internal_group = fields.Selection([
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('off_balance', 'Off Balance'),
    ], string='Internal Group', required=True)
    
    reconcile = fields.Boolean(string='Allow Reconciliation', default=False)
    deprecated = fields.Boolean(string='Deprecated', default=False)
    
    user_type_id = fields.Many2one('account.account.type', string='Account Type', required=True)
    
    # Moroccan-specific fields
    is_moroccan_account = fields.Boolean(string='Is Moroccan Account', default=True)
    moroccan_account_class = fields.Selection([
        ('class1', 'Class 1: Financing Accounts'),
        ('class2', 'Class 2: Fixed Asset Accounts'),
        ('class3', 'Class 3: Inventory Accounts'),
        ('class4', 'Class 4: Third Party Accounts'),
        ('class5', 'Class 5: Financial Accounts'),
        ('class6', 'Class 6: Expense Accounts'),
        ('class7', 'Class 7: Revenue Accounts'),
        ('class8', 'Class 8: Special Accounts'),
        ('class9', 'Class 9: Analytical Accounts'),
        ('class0', 'Class 0: Special Accounts'),
    ], string='Moroccan Account Class')
    
    tax_ids = fields.Many2many('account.tax', string='Default Taxes')
    tag_ids = fields.Many2many('account.account.tag', string='Tags')
    
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                               default=lambda self: self.env.company)
    
    currency_id = fields.Many2one('res.currency', string='Account Currency',
                                help="Forces all moves for this account to have this account currency.")
    
    # Balances
    balance = fields.Monetary(string='Balance', compute='_compute_balance')
    debit = fields.Monetary(string='Debit', compute='_compute_balance')
    credit = fields.Monetary(string='Credit', compute='_compute_balance')
    
    # For Moroccan accounting
    is_vat_account = fields.Boolean(string='Is VAT Account', default=False)
    vat_type = fields.Selection([
        ('input', 'Input VAT'),
        ('output', 'Output VAT'),
    ], string='VAT Type')
    
    is_tax_account = fields.Boolean(string='Is Tax Account', default=False)
    tax_type = fields.Selection([
        ('is', 'IS (Corporate Tax)'),
        ('ir', 'IR (Income Tax)'),
        ('tva', 'TVA (VAT)'),
        ('other', 'Other Tax'),
    ], string='Tax Type')
    
    # For weighted average cost calculation
    is_inventory_account = fields.Boolean(string='Is Inventory Account', default=False)
    inventory_valuation_method = fields.Selection([
        ('fifo', 'First In First Out (FIFO)'),
        ('lifo', 'Last In First Out (LIFO)'),
        ('average', 'Weighted Average Cost (CUMP)'),
        ('standard', 'Standard Cost'),
    ], string='Inventory Valuation Method')
    
    @api.depends('company_id')
    def _compute_balance(self):
        for account in self:
            account.balance = 0
            account.debit = 0
            account.credit = 0
            
            # In a real implementation, this would compute the balance from account moves
            # For now, we'll just set them to 0
    
    @api.constrains('code')
    def _check_code(self):
        for account in self:
            if account.is_moroccan_account:
                if not account.code or len(account.code) < 4:
                    raise ValidationError(_("Moroccan account codes must have at least 4 digits."))
                
                # Check if the first digit matches the account class
                first_digit = account.code[0]
                class_digit = account.moroccan_account_class[5] if account.moroccan_account_class else None
                
                if class_digit and first_digit != class_digit:
                    raise ValidationError(_("The first digit of the account code (%s) must match the account class (%s).") % 
                                         (first_digit, class_digit))
    
    @api.onchange('moroccan_account_class')
    def _onchange_moroccan_account_class(self):
        if self.moroccan_account_class and not self.code:
            class_digit = self.moroccan_account_class[5]
            self.code = class_digit + '000'
            
        if self.moroccan_account_class == 'class4':
            self.reconcile = True
        
        if self.moroccan_account_class == 'class5':
            self.internal_type = 'liquidity'
            
        if self.moroccan_account_class == 'class6':
            self.account_type = 'expense'
            self.internal_group = 'expense'
            
        if self.moroccan_account_class == 'class7':
            self.account_type = 'income'
            self.internal_group = 'income'
    
    @api.onchange('account_type')
    def _onchange_account_type(self):
        if self.account_type == 'asset':
            self.internal_group = 'asset'
        elif self.account_type == 'liability':
            self.internal_group = 'liability'
        elif self.account_type == 'equity':
            self.internal_group = 'equity'
        elif self.account_type == 'income':
            self.internal_group = 'income'
        elif self.account_type == 'expense':
            self.internal_group = 'expense'
    
    @api.onchange('internal_type')
    def _onchange_internal_type(self):
        if self.internal_type == 'receivable' or self.internal_type == 'payable':
            self.reconcile = True
        else:
            self.reconcile = False
            
    def action_open_moves(self):
        """Open all moves for this account"""
        self.ensure_one()
        action = self.env.ref('accounting.action_account_moves').read()[0]
        action['domain'] = [('account_id', '=', self.id)]
        action['context'] = {'default_account_id': self.id}
        return action
    
    def action_open_reconciliation(self):
        """Open reconciliation view for this account"""
        self.ensure_one()
        if not self.reconcile:
            raise ValidationError(_("You can only reconcile reconcilable accounts."))
        
        action = self.env.ref('accounting.action_account_reconciliation').read()[0]
        action['context'] = {'default_account_id': self.id}
        return action
    
    def action_mark_as_deprecated(self):
        """Mark account as deprecated"""
        self.ensure_one()
        self.deprecated = True
    
    def action_unmark_as_deprecated(self):
        """Unmark account as deprecated"""
        self.ensure_one()
        self.deprecated = False


class AccountAccountType(models.Model):
    _name = 'account.account.type'
    _description = 'Account Type'
    
    name = fields.Char(string='Account Type', required=True, translate=True)
    type = fields.Selection([
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('other', 'Other'),
    ], string='Type', required=True)
    
    internal_group = fields.Selection([
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('off_balance', 'Off Balance'),
    ], string='Internal Group', required=True)
    
    note = fields.Text(string='Description')
    
    include_initial_balance = fields.Boolean(string='Include Initial Balance', default=True,
                                          help="If set, this account type will include the initial balance when generating financial reports.")
    
    # For Moroccan accounting
    is_moroccan_type = fields.Boolean(string='Is Moroccan Type', default=True)
    moroccan_account_class = fields.Selection([
        ('class1', 'Class 1: Financing Accounts'),
        ('class2', 'Class 2: Fixed Asset Accounts'),
        ('class3', 'Class 3: Inventory Accounts'),
        ('class4', 'Class 4: Third Party Accounts'),
        ('class5', 'Class 5: Financial Accounts'),
        ('class6', 'Class 6: Expense Accounts'),
        ('class7', 'Class 7: Revenue Accounts'),
        ('class8', 'Class 8: Special Accounts'),
        ('class9', 'Class 9: Analytical Accounts'),
        ('class0', 'Class 0: Special Accounts'),
    ], string='Moroccan Account Class')


class AccountAccountTag(models.Model):
    _name = 'account.account.tag'
    _description = 'Account Tag'
    
    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(string='Active', default=True)
    
    applicability = fields.Selection([
        ('accounts', 'Accounts'),
        ('taxes', 'Taxes'),
    ], string='Applicability', required=True, default='accounts')
    
    # For Moroccan accounting
    is_moroccan_tag = fields.Boolean(string='Is Moroccan Tag', default=False)
    moroccan_tag_type = fields.Selection([
        ('vat', 'VAT Related'),
        ('is', 'IS (Corporate Tax) Related'),
        ('ir', 'IR (Income Tax) Related'),
        ('other', 'Other'),
    ], string='Moroccan Tag Type')
