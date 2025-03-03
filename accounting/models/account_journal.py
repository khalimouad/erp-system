from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountJournal(models.Model):
    _name = 'account.journal'
    _description = 'Journal'
    _order = 'sequence, type, code'
    
    name = fields.Char(string='Journal Name', required=True)
    code = fields.Char(string='Short Code', size=5, required=True, help="The journal's short code, which will appear on journal items.")
    active = fields.Boolean(string='Active', default=True, help="If unchecked, the journal will be deactivated and not appear in selections.")
    type = fields.Selection([
        ('sale', 'Sales'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'Miscellaneous'),
    ], string='Type', required=True)
    
    sequence = fields.Integer(string='Sequence', help="Used to order journals in the dashboard view", default=10)
    
    default_account_id = fields.Many2one('account.account', string='Default Account',
                                       help="The account used by default when creating journal items for this journal.")
    
    suspense_account_id = fields.Many2one('account.account', string='Suspense Account',
                                        help="The account used to record unreconciled transactions.")
    
    profit_account_id = fields.Many2one('account.account', string='Profit Account',
                                      help="The account used to record profit when reconciling journal items.")
    
    loss_account_id = fields.Many2one('account.account', string='Loss Account',
                                    help="The account used to record loss when reconciling journal items.")
    
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                               default=lambda self: self.env.company)
    
    currency_id = fields.Many2one('res.currency', string='Currency',
                                help="The currency used by the journal. If not set, the company's currency will be used.")
    
    # Bank accounts
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account',
                                    help="The bank account used by this journal.")
    
    bank_statements_source = fields.Selection([
        ('manual', 'Manual'),
        ('file_import', 'File Import'),
        ('online', 'Online Synchronization'),
    ], string='Bank Statements Source', default='manual')
    
    # Sequences
    sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence',
                                help="The sequence used to generate journal entry numbers.")
    
    refund_sequence_id = fields.Many2one('ir.sequence', string='Credit Note Entry Sequence',
                                       help="The sequence used to generate credit note numbers.")
    
    sequence_number_next = fields.Integer(string='Next Number',
                                        help="The next sequence number that will be used for new entries.")
    
    refund_sequence_number_next = fields.Integer(string='Next Credit Note Number',
                                              help="The next sequence number that will be used for new credit notes.")
    
    # Options
    refund_sequence = fields.Boolean(string='Dedicated Credit Note Sequence',
                                   help="If checked, a dedicated sequence will be used for credit notes.")
    
    post_at = fields.Selection([
        ('pay_val', 'Payment Validation'),
        ('bank_rec', 'Bank Reconciliation'),
    ], string='Post At', default='pay_val')
    
    invoice_reference_type = fields.Selection([
        ('none', 'Free Reference'),
        ('invoice', 'Based on Invoice'),
        ('partner', 'Based on Partner'),
    ], string='Communication Type', default='invoice')
    
    invoice_reference_model = fields.Selection([
        ('odoo', 'Odoo'),
        ('moroccan', 'Moroccan'),
    ], string='Communication Standard', default='odoo')
    
    # For Moroccan accounting
    is_moroccan_journal = fields.Boolean(string='Is Moroccan Journal', default=True)
    
    moroccan_journal_type = fields.Selection([
        ('sales', 'Sales Journal'),
        ('purchases', 'Purchases Journal'),
        ('cash', 'Cash Journal'),
        ('bank', 'Bank Journal'),
        ('operations', 'Operations Journal'),
        ('closing', 'Closing Journal'),
        ('opening', 'Opening Journal'),
        ('situation', 'Situation Journal'),
    ], string='Moroccan Journal Type')
    
    # For VAT reporting
    vat_required = fields.Boolean(string='VAT Required on Entries',
                                help="If checked, a VAT number will be required when creating entries in this journal.")
    
    # For bank reconciliation
    bank_reconciliation_start_date = fields.Date(string='Bank Reconciliation Start Date')
    
    # For cash journals
    cash_control = fields.Boolean(string='Cash Control',
                                help="If checked, cash control will be required for this journal.")
    
    # For purchase journals
    purchase_reverse_charge = fields.Boolean(string='Purchase Reverse Charge',
                                          help="If checked, the journal will be used for purchase reverse charge.")
    
    # For sales journals
    sale_activity_type_id = fields.Many2one('mail.activity.type', string='Schedule Activity on Invoice Validation')
    sale_activity_user_id = fields.Many2one('res.users', string='Activity User')
    sale_activity_note = fields.Text(string='Activity Note')
    
    # For bank and cash journals
    profit_account_id = fields.Many2one('account.account', string='Profit Account',
                                      help="The account used to record profit when reconciling journal items.")
    
    loss_account_id = fields.Many2one('account.account', string='Loss Account',
                                    help="The account used to record loss when reconciling journal items.")
    
    # For all journals
    group_invoice_lines = fields.Boolean(string='Group Invoice Lines',
                                       help="If checked, invoice lines will be grouped by product, account, taxes, etc.")
    
    @api.constrains('code')
    def _check_code(self):
        for journal in self:
            if not journal.code or len(journal.code) < 1 or len(journal.code) > 5:
                raise ValidationError(_("Journal code must be between 1 and 5 characters."))
            
            # Check for duplicate codes in the same company
            domain = [
                ('code', '=', journal.code),
                ('company_id', '=', journal.company_id.id),
                ('id', '!=', journal.id),
            ]
            
            if self.search_count(domain) > 0:
                raise ValidationError(_("Journal code must be unique per company."))
    
    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'sale':
            self.moroccan_journal_type = 'sales'
            self.default_account_id = self.env['account.account'].search([
                ('internal_type', '=', 'receivable'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        elif self.type == 'purchase':
            self.moroccan_journal_type = 'purchases'
            self.default_account_id = self.env['account.account'].search([
                ('internal_type', '=', 'payable'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        elif self.type == 'cash':
            self.moroccan_journal_type = 'cash'
            self.default_account_id = self.env['account.account'].search([
                ('internal_type', '=', 'liquidity'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        elif self.type == 'bank':
            self.moroccan_journal_type = 'bank'
            self.default_account_id = self.env['account.account'].search([
                ('internal_type', '=', 'liquidity'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
        elif self.type == 'general':
            self.moroccan_journal_type = 'operations'
    
    @api.onchange('moroccan_journal_type')
    def _onchange_moroccan_journal_type(self):
        if self.moroccan_journal_type == 'sales':
            self.type = 'sale'
        elif self.moroccan_journal_type == 'purchases':
            self.type = 'purchase'
        elif self.moroccan_journal_type == 'cash':
            self.type = 'cash'
        elif self.moroccan_journal_type == 'bank':
            self.type = 'bank'
        elif self.moroccan_journal_type in ['operations', 'closing', 'opening', 'situation']:
            self.type = 'general'
    
    def action_create_new(self):
        """Create a new entry in this journal"""
        self.ensure_one()
        action = self.env.ref('accounting.action_move_journal_line').read()[0]
        action['context'] = {
            'default_journal_id': self.id,
        }
        return action
    
    def action_open_reconcile(self):
        """Open reconciliation view for this journal"""
        self.ensure_one()
        action = self.env.ref('accounting.action_account_reconciliation').read()[0]
        action['context'] = {
            'default_journal_id': self.id,
        }
        return action
    
    def action_open_to_check(self):
        """Open entries to check for this journal"""
        self.ensure_one()
        action = self.env.ref('accounting.action_move_journal_line').read()[0]
        action['domain'] = [
            ('journal_id', '=', self.id),
            ('to_check', '=', True),
        ]
        action['context'] = {
            'default_journal_id': self.id,
        }
        return action
    
    def action_open_bank_statements(self):
        """Open bank statements for this journal"""
        self.ensure_one()
        action = self.env.ref('accounting.action_bank_statement_tree').read()[0]
        action['domain'] = [
            ('journal_id', '=', self.id),
        ]
        action['context'] = {
            'default_journal_id': self.id,
        }
        return action
    
    def action_open_transfers(self):
        """Open transfers for this journal"""
        self.ensure_one()
        action = self.env.ref('accounting.action_account_transfers').read()[0]
        action['domain'] = [
            '|',
            ('journal_id', '=', self.id),
            ('destination_journal_id', '=', self.id),
        ]
        action['context'] = {
            'default_journal_id': self.id,
        }
        return action
    
    def action_configure_bank_journal(self):
        """Configure bank journal"""
        self.ensure_one()
        if self.type not in ['bank', 'cash']:
            raise ValidationError(_("Only bank and cash journals can be configured."))
        
        action = self.env.ref('accounting.action_account_bank_journal_form').read()[0]
        action['res_id'] = self.id
        return action
