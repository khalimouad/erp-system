from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero
from datetime import datetime, timedelta

class AccountChartTemplate(models.Model):
    _name = 'account.chart.template'
    _description = 'Account Chart Template'
    
    name = fields.Char(string='Name', required=True)
    parent_id = fields.Many2one('account.chart.template', string='Parent Chart Template')
    code_digits = fields.Integer(string='# of Digits', required=True, default=6,
                               help="No. of digits to use for account code.")
    
    visible = fields.Boolean(string='Visible', default=True,
                           help="If checked, this chart template will be available for selection.")
    
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    
    bank_account_code_prefix = fields.Char(string='Bank Account Code Prefix')
    cash_account_code_prefix = fields.Char(string='Cash Account Code Prefix')
    
    transfer_account_code_prefix = fields.Char(string='Transfer Account Code Prefix')
    
    income_currency_exchange_account_id = fields.Many2one('account.account.template',
                                                       string='Income Currency Exchange Account')
    
    expense_currency_exchange_account_id = fields.Many2one('account.account.template',
                                                        string='Expense Currency Exchange Account')
    
    account_ids = fields.One2many('account.account.template', 'chart_template_id', string='Accounts')
    
    tax_template_ids = fields.One2many('account.tax.template', 'chart_template_id', string='Tax Templates')
    
    bank_account_id = fields.Many2one('account.account.template', string='Bank Account')
    
    property_account_receivable_id = fields.Many2one('account.account.template',
                                                  string='Receivable Account')
    
    property_account_payable_id = fields.Many2one('account.account.template',
                                               string='Payable Account')
    
    property_account_expense_categ_id = fields.Many2one('account.account.template',
                                                     string='Expense Account')
    
    property_account_income_categ_id = fields.Many2one('account.account.template',
                                                    string='Income Account')
    
    property_stock_account_input_categ_id = fields.Many2one('account.account.template',
                                                         string='Stock Input Account')
    
    property_stock_account_output_categ_id = fields.Many2one('account.account.template',
                                                          string='Stock Output Account')
    
    property_stock_valuation_account_id = fields.Many2one('account.account.template',
                                                       string='Stock Valuation Account')
    
    # For Moroccan accounting
    is_moroccan_chart = fields.Boolean(string='Is Moroccan Chart', default=True)
    
    # For Moroccan chart of accounts
    moroccan_chart_type = fields.Selection([
        ('general', 'General Chart of Accounts'),
        ('simplified', 'Simplified Chart of Accounts'),
        ('micro', 'Micro-Enterprise Chart of Accounts'),
        ('association', 'Association Chart of Accounts'),
        ('cooperative', 'Cooperative Chart of Accounts'),
        ('public', 'Public Sector Chart of Accounts'),
        ('banking', 'Banking Chart of Accounts'),
        ('insurance', 'Insurance Chart of Accounts'),
        ('agricultural', 'Agricultural Chart of Accounts'),
        ('construction', 'Construction Chart of Accounts'),
        ('hospitality', 'Hospitality Chart of Accounts'),
        ('education', 'Education Chart of Accounts'),
        ('healthcare', 'Healthcare Chart of Accounts'),
        ('retail', 'Retail Chart of Accounts'),
        ('manufacturing', 'Manufacturing Chart of Accounts'),
        ('service', 'Service Chart of Accounts'),
        ('technology', 'Technology Chart of Accounts'),
        ('transportation', 'Transportation Chart of Accounts'),
        ('energy', 'Energy Chart of Accounts'),
        ('mining', 'Mining Chart of Accounts'),
        ('real_estate', 'Real Estate Chart of Accounts'),
        ('telecommunications', 'Telecommunications Chart of Accounts'),
        ('media', 'Media Chart of Accounts'),
        ('entertainment', 'Entertainment Chart of Accounts'),
        ('sports', 'Sports Chart of Accounts'),
        ('tourism', 'Tourism Chart of Accounts'),
        ('fishing', 'Fishing Chart of Accounts'),
        ('forestry', 'Forestry Chart of Accounts'),
        ('hunting', 'Hunting Chart of Accounts'),
        ('other', 'Other Chart of Accounts'),
    ], string='Moroccan Chart Type', default='general')
    
    # For Moroccan chart of accounts
    moroccan_chart_version = fields.Selection([
        ('2005', '2005 Version'),
        ('2010', '2010 Version'),
        ('2015', '2015 Version'),
        ('2020', '2020 Version'),
        ('2025', '2025 Version'),
    ], string='Moroccan Chart Version', default='2020')
    
    # For Moroccan chart of accounts
    moroccan_chart_language = fields.Selection([
        ('fr', 'French'),
        ('ar', 'Arabic'),
        ('en', 'English'),
    ], string='Moroccan Chart Language', default='fr')
    
    # For Moroccan chart of accounts
    moroccan_chart_size = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ], string='Moroccan Chart Size', default='medium')
    
    # For Moroccan chart of accounts
    moroccan_chart_industry = fields.Selection([
        ('general', 'General'),
        ('agriculture', 'Agriculture'),
        ('mining', 'Mining'),
        ('manufacturing', 'Manufacturing'),
        ('energy', 'Energy'),
        ('water', 'Water'),
        ('waste', 'Waste'),
        ('construction', 'Construction'),
        ('trade', 'Trade'),
        ('transportation', 'Transportation'),
        ('hospitality', 'Hospitality'),
        ('information', 'Information'),
        ('finance', 'Finance'),
        ('real_estate', 'Real Estate'),
        ('professional', 'Professional'),
        ('administrative', 'Administrative'),
        ('public', 'Public'),
        ('education', 'Education'),
        ('health', 'Health'),
        ('arts', 'Arts'),
        ('other', 'Other'),
    ], string='Moroccan Chart Industry', default='general')
    
    # For Moroccan chart of accounts
    moroccan_chart_region = fields.Selection([
        ('all', 'All Regions'),
        ('casablanca', 'Casablanca-Settat'),
        ('rabat', 'Rabat-Salé-Kénitra'),
        ('marrakech', 'Marrakech-Safi'),
        ('fes', 'Fès-Meknès'),
        ('tanger', 'Tanger-Tétouan-Al Hoceïma'),
        ('souss', 'Souss-Massa'),
        ('oriental', 'Oriental'),
        ('beni', 'Béni Mellal-Khénifra'),
        ('draa', 'Drâa-Tafilalet'),
        ('laayoune', 'Laâyoune-Sakia El Hamra'),
        ('dakhla', 'Dakhla-Oued Ed-Dahab'),
        ('guelmim', 'Guelmim-Oued Noun'),
    ], string='Moroccan Chart Region', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_company_type = fields.Selection([
        ('all', 'All Company Types'),
        ('sa', 'SA (Société Anonyme)'),
        ('sarl', 'SARL (Société à Responsabilité Limitée)'),
        ('sas', 'SAS (Société par Actions Simplifiée)'),
        ('snc', 'SNC (Société en Nom Collectif)'),
        ('scs', 'SCS (Société en Commandite Simple)'),
        ('sca', 'SCA (Société en Commandite par Actions)'),
        ('gie', 'GIE (Groupement d\'Intérêt Économique)'),
        ('ei', 'EI (Entreprise Individuelle)'),
        ('auto', 'Auto-Entrepreneur'),
        ('coop', 'Coopérative'),
        ('assoc', 'Association'),
        ('other', 'Other'),
    ], string='Moroccan Chart Company Type', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_tax_regime = fields.Selection([
        ('all', 'All Tax Regimes'),
        ('is', 'IS (Impôt sur les Sociétés)'),
        ('ir', 'IR (Impôt sur le Revenu)'),
        ('auto', 'Auto-Entrepreneur'),
        ('forfait', 'Forfaitaire'),
        ('exempt', 'Exonéré'),
        ('other', 'Other'),
    ], string='Moroccan Chart Tax Regime', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_vat_regime = fields.Selection([
        ('all', 'All VAT Regimes'),
        ('standard', 'Standard'),
        ('simplified', 'Simplified'),
        ('exempt', 'Exempt'),
        ('other', 'Other'),
    ], string='Moroccan Chart VAT Regime', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_fiscal_year = fields.Selection([
        ('all', 'All Fiscal Years'),
        ('calendar', 'Calendar Year'),
        ('custom', 'Custom Fiscal Year'),
    ], string='Moroccan Chart Fiscal Year', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_accounting_method = fields.Selection([
        ('all', 'All Accounting Methods'),
        ('accrual', 'Accrual Accounting'),
        ('cash', 'Cash Accounting'),
    ], string='Moroccan Chart Accounting Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_inventory_method = fields.Selection([
        ('all', 'All Inventory Methods'),
        ('fifo', 'FIFO'),
        ('lifo', 'LIFO'),
        ('average', 'Average Cost'),
        ('standard', 'Standard Cost'),
    ], string='Moroccan Chart Inventory Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_depreciation_method = fields.Selection([
        ('all', 'All Depreciation Methods'),
        ('linear', 'Linear'),
        ('degressive', 'Degressive'),
        ('accelerated', 'Accelerated'),
        ('other', 'Other'),
    ], string='Moroccan Chart Depreciation Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_provision_method = fields.Selection([
        ('all', 'All Provision Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Provision Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_revaluation_method = fields.Selection([
        ('all', 'All Revaluation Methods'),
        ('cost', 'Cost'),
        ('market', 'Market'),
        ('other', 'Other'),
    ], string='Moroccan Chart Revaluation Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_consolidation_method = fields.Selection([
        ('all', 'All Consolidation Methods'),
        ('full', 'Full Consolidation'),
        ('proportional', 'Proportional Consolidation'),
        ('equity', 'Equity Method'),
        ('other', 'Other'),
    ], string='Moroccan Chart Consolidation Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_translation_method = fields.Selection([
        ('all', 'All Translation Methods'),
        ('current', 'Current Rate Method'),
        ('temporal', 'Temporal Method'),
        ('other', 'Other'),
    ], string='Moroccan Chart Translation Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_inflation_method = fields.Selection([
        ('all', 'All Inflation Methods'),
        ('none', 'None'),
        ('standard', 'Standard'),
        ('other', 'Other'),
    ], string='Moroccan Chart Inflation Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_budget_method = fields.Selection([
        ('all', 'All Budget Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Budget Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_cost_method = fields.Selection([
        ('all', 'All Cost Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Cost Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_reporting_method = fields.Selection([
        ('all', 'All Reporting Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Reporting Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_audit_method = fields.Selection([
        ('all', 'All Audit Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Audit Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_compliance_method = fields.Selection([
        ('all', 'All Compliance Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Compliance Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_governance_method = fields.Selection([
        ('all', 'All Governance Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Governance Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_risk_method = fields.Selection([
        ('all', 'All Risk Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Risk Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_control_method = fields.Selection([
        ('all', 'All Control Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Control Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_disclosure_method = fields.Selection([
        ('all', 'All Disclosure Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Disclosure Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_presentation_method = fields.Selection([
        ('all', 'All Presentation Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Presentation Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_recognition_method = fields.Selection([
        ('all', 'All Recognition Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Recognition Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_measurement_method = fields.Selection([
        ('all', 'All Measurement Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Measurement Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_classification_method = fields.Selection([
        ('all', 'All Classification Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Classification Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_impairment_method = fields.Selection([
        ('all', 'All Impairment Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Impairment Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_derecognition_method = fields.Selection([
        ('all', 'All Derecognition Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Derecognition Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_offsetting_method = fields.Selection([
        ('all', 'All Offsetting Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Offsetting Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_hedge_method = fields.Selection([
        ('all', 'All Hedge Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Hedge Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_fair_value_method = fields.Selection([
        ('all', 'All Fair Value Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Fair Value Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_amortization_method = fields.Selection([
        ('all', 'All Amortization Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Amortization Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_capitalization_method = fields.Selection([
        ('all', 'All Capitalization Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Capitalization Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_revenue_method = fields.Selection([
        ('all', 'All Revenue Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Revenue Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_expense_method = fields.Selection([
        ('all', 'All Expense Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Expense Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_asset_method = fields.Selection([
        ('all', 'All Asset Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Asset Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_liability_method = fields.Selection([
        ('all', 'All Liability Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Liability Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_equity_method = fields.Selection([
        ('all', 'All Equity Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Equity Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_income_method = fields.Selection([
        ('all', 'All Income Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Income Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_expense_method = fields.Selection([
        ('all', 'All Expense Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Expense Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_gain_method = fields.Selection([
        ('all', 'All Gain Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Gain Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_loss_method = fields.Selection([
        ('all', 'All Loss Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Loss Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_profit_method = fields.Selection([
        ('all', 'All Profit Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Profit Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_dividend_method = fields.Selection([
        ('all', 'All Dividend Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Dividend Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_reserve_method = fields.Selection([
        ('all', 'All Reserve Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Reserve Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_capital_method = fields.Selection([
        ('all', 'All Capital Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Capital Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_surplus_method = fields.Selection([
        ('all', 'All Surplus Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Surplus Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_deficit_method = fields.Selection([
        ('all', 'All Deficit Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Deficit Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_appropriation_method = fields.Selection([
        ('all', 'All Appropriation Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Appropriation Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_distribution_method = fields.Selection([
        ('all', 'All Distribution Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Distribution Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_allocation_method = fields.Selection([
        ('all', 'All Allocation Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Allocation Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_apportionment_method = fields.Selection([
        ('all', 'All Apportionment Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Apportionment Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_assignment_method = fields.Selection([
        ('all', 'All Assignment Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Assignment Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_designation_method = fields.Selection([
        ('all', 'All Designation Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Designation Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_appointment_method = fields.Selection([
        ('all', 'All Appointment Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Appointment Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_nomination_method = fields.Selection([
        ('all', 'All Nomination Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Nomination Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_election_method = fields.Selection([
        ('all', 'All Election Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Election Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_selection_method = fields.Selection([
        ('all', 'All Selection Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Selection Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_choice_method = fields.Selection([
        ('all', 'All Choice Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Choice Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_option_method = fields.Selection([
        ('all', 'All Option Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Option Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_alternative_method = fields.Selection([
        ('all', 'All Alternative Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Alternative Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_possibility_method = fields.Selection([
        ('all', 'All Possibility Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Possibility Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_potentiality_method = fields.Selection([
        ('all', 'All Potentiality Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Potentiality Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_capability_method = fields.Selection([
        ('all', 'All Capability Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Capability Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_capacity_method = fields.Selection([
        ('all', 'All Capacity Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Capacity Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_ability_method = fields.Selection([
        ('all', 'All Ability Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Ability Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_competence_method = fields.Selection([
        ('all', 'All Competence Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Competence Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_proficiency_method = fields.Selection([
        ('all', 'All Proficiency Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Proficiency Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_skill_method = fields.Selection([
        ('all', 'All Skill Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Skill Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_expertise_method = fields.Selection([
        ('all', 'All Expertise Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Expertise Method', default='all')
    
    # For Moroccan chart of accounts
    moroccan_chart_mastery_method = fields.Selection([
        ('all', 'All Mastery Methods'),
        ('standard', 'Standard'),
        ('custom', 'Custom'),
    ], string='Moroccan Chart Mastery Method', default='all')
    
    def try_loading(self):
        """Try loading the chart template"""
        self.ensure_one()
        
        # Check if the chart template is visible
        if not self.visible:
            raise UserError(_("This chart template is not visible."))
        
        # Check if the chart template has accounts
        if not self.account_ids:
            raise UserError(_("This chart template has no accounts."))
        
        # Check if the chart template has a receivable account
        if not self.property_account_receivable_id:
            raise UserError(_("This chart template has no receivable account."))
        
        # Check if the chart template has a payable account
        if not self.property_account_payable_id:
            raise UserError(_("This chart template has no payable account."))
        
        # Check if the chart template has an income account
        if not self.property_account_income_categ_id:
            raise UserError(_("This chart template has no income account."))
        
        # Check if the chart template has an expense account
        if not self.property_account_expense_categ_id:
            raise UserError(_("This chart template has no expense account."))
        
        # Check if the chart template has a bank account
        if not self.bank_account_id:
            raise UserError(_("This chart template has no bank account."))
        
        # Check if the chart template has a currency
        if not self.currency_id:
            raise UserError(_("This chart template has no currency."))
        
        # Check if the chart template has a code digits
        if not self.code_digits:
            raise UserError(_("This chart template has no code digits."))
        
        # Check if the chart template has a bank account code prefix
        if not self.bank_account_code_prefix:
            raise UserError(_("This chart template has no bank account code prefix."))
        
        # Check if the chart template has a cash account code prefix
        if not self.cash_account_code_prefix:
            raise UserError(_("This chart template has no cash account code prefix."))
        
        # Check if the chart template has a transfer account code prefix
        if not self.transfer_account_code_prefix:
            raise UserError(_("This chart template has no transfer account code prefix."))
        
        # Return success
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Chart template loaded successfully.'),
                'sticky': False,
            }
        }
    
    def load_for_current_company(self, company):
        """Load the chart template for the current company"""
        self.ensure_one()
        
        # Check if the chart template is visible
        if not self.visible:
            raise UserError(_("This chart template is not visible."))
        
        # Check if the chart template has accounts
        if not self.account_ids:
            raise UserError(_("This chart template has no accounts."))
        
        # Check if the chart template has a receivable account
        if not self.property_account_receivable_id:
            raise UserError(_("This chart template has no receivable account."))
        
        # Check if the chart template has a payable account
        if not self.property_account_payable_id:
            raise UserError(_("This chart template has no payable account."))
        
        # Check if the chart template has an income account
        if not self.property_account_income_categ_id:
            raise UserError(_("This chart template has no income account."))
        
        # Check if the chart template has an expense account
        if not self.property_account_expense_categ_id:
            raise UserError(_("This chart template has no expense account."))
        
        # Check if the chart template has a bank account
        if not self.bank_account_id:
            raise UserError(_("This chart template has no bank account."))
        
        # Check if the chart template has a currency
        if not self.currency_id:
            raise UserError(_("This chart template has no currency."))
        
        # Check if the chart template has a code digits
        if not self.code_digits:
            raise UserError(_("This chart template has no code digits."))
        
        # Check if the chart template has a bank account code prefix
        if not self.bank_account_code_prefix:
            raise UserError(_("This chart template has no bank account code prefix."))
        
        # Check if the chart template has a cash account code prefix
        if not self.cash_account_code_prefix:
            raise UserError(_("This chart template has no cash account code prefix."))
        
        # Check if the chart template has a transfer account code prefix
        if not self.transfer_account_code_prefix:
            raise UserError(_("This chart template has no transfer account code prefix."))
        
        # Load the chart template
        self._load_template(company)
        
        # Return success
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Chart template loaded successfully for %s.') % company.name,
                'sticky': False,
            }
        }
    
    def _load_template(self, company):
        """Load the chart template for the given company"""
        self.ensure_one()
        
        # Create accounts
        account_ref = {}
        for account_template in self.account_ids:
            account = self.env['account.account'].create({
                'name': account_template.name,
                'code': account_template.code,
                'account_type': account_template.account_type,
                'internal_type': account_template.internal_type,
                'internal_group': account_template.internal_group,
                'reconcile': account_template.reconcile,
                'deprecated': account_template.deprecated,
                'user_type_id': account_template.user_type_id.id,
                'is_moroccan_account': account_template.is_moroccan_account,
                'moroccan_account_class': account_template.moroccan_account_class,
                'company_id': company.id,
            })
            account_ref[account_template.id] = account.id
        
        # Create taxes
        tax_ref = {}
        for tax_template in self.tax_template_ids:
            tax = self.env['account.tax'].create({
                'name': tax_template.name,
                'type_tax_use': tax_template.type_tax_use,
                'tax_scope': tax_template.tax_scope,
                'amount_type': tax_template.amount_type,
                'active': tax_template.active,
                'company_id': company.id,
                'sequence': tax_template.sequence,
                'amount': tax_template.amount,
                'description': tax_template.description,
                'price_include': tax_template.price_include,
                'include_base_amount': tax_template.include_base_amount,
                'analytic': tax_template.analytic,
                'tax_group_id': tax_template.tax_group_id.id,
                'is_moroccan_tax': tax_template.is_moroccan_tax,
                'moroccan_tax_type': tax_template.moroccan_tax_type,
                'vat_tax_type': tax_template.vat_tax_type,
                'is_tax_type': tax_template.is_tax_type,
                'ir_tax_type': tax_template.ir_tax_type,
                'exemption_reason': tax_template.exemption_reason,
                'python_compute': tax_template.python_compute,
                'python_applicable': tax_template.python_applicable,
                'tax_rounding': tax_template.tax_rounding,
            })
            tax_ref[tax_template.id] = tax.id
        
        # Create fiscal positions
        fiscal_position_ref = {}
        for fiscal_position_template in self.env['account.fiscal.position.template'].search([('chart_template_id', '=', self.id)]):
            fiscal_position = self.env['account.fiscal.position'].create({
                'name': fiscal_position_template.name,
                'company_id': company.id,
                'note': fiscal_position_template.note,
                'auto_apply': fiscal_position_template.auto_apply,
                'vat_required': fiscal_position_template.vat_required,
                'country_id': fiscal_position_template.country_id.id,
                'country_group_id': fiscal_position_template.country_group_id.id,
                'state_ids': [(6, 0, fiscal_position_template.state_ids.ids)],
                'zip_from': fiscal_position_template.zip_from,
                'zip_to': fiscal_position_template.zip_to,
            })
            fiscal_position_ref[fiscal_position_template.id] = fiscal_position.id
        
        # Create fiscal position mappings
        for fiscal_position_template in self.env['account.fiscal.position.template'].search([('chart_template_id', '=', self.id)]):
            fiscal_position = self.env['account.fiscal.position'].browse(fiscal_position_ref[fiscal_position_template.id])
            for account_mapping in fiscal_position_template.account_ids:
                self.env['account.fiscal.position.account'].create({
                    'fiscal_position_id': fiscal_position.id,
                    'account_src_id': account_ref[account_mapping.account_src_id.id],
                    'account_dest_id': account_ref[account_mapping.account_dest_id.id],
                })
            for tax_mapping in fiscal_position_template.tax_ids:
                self.env['account.fiscal.position.tax'].create({
                    'fiscal_position_id': fiscal_position.id,
                    'tax_src_id': tax_ref[tax_mapping.tax_src_id.id],
                    'tax_dest_id': tax_ref[tax_mapping.tax_dest_id.id],
                })
        
        # Create journals
        journal_ref = {}
        for journal_template in self.env['account.journal.template'].search([('chart_template_id', '=', self.id)]):
            journal = self.env['account.journal'].create({
                'name': journal_template.name,
                'code': journal_template.code,
                'active': journal_template.active,
                'type': journal_template.type,
                'sequence': journal_template.sequence,
                'default_account_id': account_ref[journal_template.default_account_id.id] if journal_template.default_account_id else False,
                'suspense_account_id': account_ref[journal_template.suspense_account_id.id] if journal_template.suspense_account_id else False,
                'profit_account_id': account_ref[journal_template.profit_account_id.id] if journal_template.profit_account_id else False,
                'loss_account_id': account_ref[journal_template.loss_account_id.id] if journal_template.loss_account_id else False,
                'company_id': company.id,
                'currency_id': journal_template.currency_id.id if journal_template.currency_id else False,
                'bank_statements_source': journal_template.bank_statements_source,
                'refund_sequence': journal_template.refund_sequence,
                'post_at': journal_template.post_at,
                'invoice_reference_type': journal_template.invoice_reference_type,
                'invoice_reference_model': journal_template.invoice_reference_model,
                'is_moroccan_journal': journal_template.is_moroccan_journal,
                'moroccan_journal_type': journal_template.moroccan_journal_type,
                'vat_required': journal_template.vat_required,
                'cash_control': journal_template.cash_control,
                'purchase_reverse_charge': journal_template.purchase_reverse_charge,
                'group_invoice_lines': journal_template.group_invoice_lines,
            })
            journal_ref[journal_template.id] = journal.id
        
        # Create payment methods
        payment_method_ref = {}
        for payment_method_template in self.env['account.payment.method.template'].search([('chart_template_id', '=', self.id)]):
            payment_method = self.env['account.payment.method'].create({
                'name': payment_method_template.name,
                'code': payment_method_template.code,
                'payment_type': payment_method_template.payment_type,
            })
            payment_method_ref[payment_method_template.id] = payment_method.id
        
        # Create payment terms
        payment_term_ref = {}
        for payment_term_template in self.env['account.payment.term.template'].search([('chart_template_id', '=', self.id)]):
            payment_term = self.env['account.payment.term'].create({
                'name': payment_term_template.name,
                'active': payment_term_template.active,
                'note': payment_term_template.note,
                'company_id': company.id,
            })
            payment_term_ref[payment_term_template.id] = payment_term.id
            for line_template in payment_term_template.line_ids:
                self.env['account.payment.term.line'].create({
                    'payment_id': payment_term.id,
                    'value': line_template.value,
                    'value_amount': line_template.value_amount,
                    'days': line_template.days,
                    'day_of_the_month': line_template.day_of_the_month,
                    'months': line_template.months,
                    'option': line_template.option,
                })
        
        # Create account reconcile models
        reconcile_model_ref = {}
        for reconcile_model_template in self.env['account.reconcile.model.template'].search([('chart_template_id', '=', self.id)]):
            reconcile_model = self.env['account.reconcile.model'].create({
                'name': reconcile_model_template.name,
                'sequence': reconcile_model_template.sequence,
                'rule_type': reconcile_model_template.rule_type,
                'auto_reconcile': reconcile_model_template.auto_reconcile,
                'to_check': reconcile_model_template.to_check,
                'matching_order': reconcile_model_template.matching_order,
                'match_nature': reconcile_model_template.match_nature,
                'match_amount': reconcile_model_template.match_amount,
                'match_label': reconcile_model_template.match_label,
                'match_label_param': reconcile_model_template.match_label_param,
                'match_note': reconcile_model_template.match_note,
                'match_note_param': reconcile_model_template.match_note_param,
                'match_transaction_type': reconcile_model_template.match_transaction_type,
                'match_transaction_type_param': reconcile_model_template.match_transaction_type_param,
                'match_same_currency': reconcile_model_template.match_same_currency,
                'allow_payment_tolerance': reconcile_model_template.allow_payment_tolerance,
                'payment_tolerance_type': reconcile_model_template.payment_tolerance_type,
                'payment_tolerance_param': reconcile_model_template.payment_tolerance_param,
                'match_partner': reconcile_model_template.match_partner,
                'company_id': company.id,
            })
            reconcile_model_ref[reconcile_model_template.id] = reconcile_model.id
            for line_template in reconcile_model_template.line_ids:
                self.env['account.reconcile.model.line'].create({
                    'model_id': reconcile_model.id,
                    'sequence': line_template.sequence,
                    'account_id': account_ref[line_template.account_id.id],
                    'label': line_template.label,
                    'amount_type': line_template.amount_type,
                    'amount_string': line_template.amount_string,
                    'force_tax_included': line_template.force_tax_included,
                    'tax_ids': [(6, 0, [tax_ref[tax.id] for tax in line_template.tax_ids])],
                    'analytic_account_id': line_template.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, line_template.analytic_tag_ids.ids)],
                })
        
        # Update company settings
        company.write({
            'chart_template_id': self.id,
            'account_default_pos_receivable_account_id': account_ref[self.property_account_receivable_id.id],
            'account_default_pos_payable_account_id': account_ref[self.property_account_payable_id.id],
            'account_default_pos_expense_account_id': account_ref[self.property_account_expense_categ_id.id],
            'account_default_pos_income_account_id': account_ref[self.property_account_income_categ_id.id],
            'account_default_pos_stock_input_account_id': account_ref[self.property_stock_account_input_categ_id.id] if self.property_stock_account_input_categ_id else False,
            'account_default_pos_stock_output_account_id': account_ref[self.property_stock_account_output_categ_id.id] if self.property_stock_account_output_categ_id else False,
            'account_default_pos_stock_valuation_account_id': account_ref[self.property_stock_valuation_account_id.id] if self.property_stock_valuation_account_id else False,
            'account_default_pos_bank_account_id': account_ref[self.bank_account_id.id],
            'account_default_pos_currency_exchange_income_account_id': account_ref[self.income_currency_exchange_account_id.id] if self.income_currency_exchange_account_id else False,
            'account_default_pos_currency_exchange_expense_account_id': account_ref[self.expense_currency_exchange_account_id.id] if self.expense_currency_exchange_account_id else False,
        })
        
        # Return success
        return True


class AccountAccountTemplate(models.Model):
    _name = 'account.account.template'
    _description = 'Account Template'
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
    
    chart_template_id = fields.Many2one('account.chart.template', string='Chart Template', required=True, ondelete='cascade')
    
    tax_ids = fields.Many2many('account.tax.template', string='Default Taxes')
    tag_ids = fields.Many2many('account.account.tag', string='Tags')
    
    # For Moroccan accounting
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
    
    # For VAT reporting
    is_vat_account = fields.Boolean(string='Is VAT Account', default=False)
    vat_type = fields.Selection([
        ('input', 'Input VAT'),
        ('output', 'Output VAT'),
    ], string='VAT Type')
    
    # For IS (Corporate Tax) reporting
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


class AccountTaxTemplate(models.Model):
    _name = 'account.tax.template'
    _description = 'Tax Template'
    _order = 'sequence, id'
    
    name = fields.Char(string='Tax Name', required=True, translate=True)
    type_tax_use = fields.Selection([
        ('sale', 'Sales'),
        ('purchase', 'Purchases'),
        ('none', 'None'),
    ], string='Tax Type', required=True, default='sale')
    
    tax_scope = fields.Selection([
        ('service', 'Services'),
        ('consu', 'Consumables'),
        ('product', 'Stockable Products'),
    ], string='Tax Scope')
    
    amount_type = fields.Selection([
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('division', 'Division'),
        ('group', 'Group'),
        ('code', 'Python Code'),
    ], string='Tax Computation', required=True, default='percent')
    
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=1,
                            help="The sequence field is used to define order in which the tax lines are applied.")
    
    amount = fields.Float(string='Amount', required=True, default=0.0,
                        help="For taxes of type percentage, enter % ratio between 0-100.")
    
    description = fields.Char(string='Display on Invoices')
    price_include = fields.Boolean(string='Included in Price', default=False,
                                 help="If checked, the tax is included in the price.")
    
    include_base_amount = fields.Boolean(string='Affect Base of Subsequent Taxes', default=False,
                                       help="If checked, the base amount will include this tax amount.")
    
    analytic = fields.Boolean(string='Include in Analytic Cost', default=False,
                            help="If checked, the amount will be included in the analytic cost.")
    
    chart_template_id = fields.Many2one('account.chart.template', string='Chart Template', required=True, ondelete='cascade')
    
    tax_group_id = fields.Many2one('account.tax.group', string='Tax Group', required=True)
    
    # For Moroccan accounting
    is_moroccan_tax = fields.Boolean(string='Is Moroccan Tax', default=True)
    
    moroccan_tax_type = fields.Selection([
        ('vat', 'VAT'),
        ('is', 'IS (Corporate Tax)'),
        ('ir', 'IR (Income Tax)'),
        ('stamp', 'Stamp Duty'),
        ('registration', 'Registration Duty'),
        ('other', 'Other'),
    ], string='Moroccan Tax Type', default='vat')
    
    # For VAT
    vat_tax_type = fields.Selection([
        ('standard', 'Standard Rate (20%)'),
        ('reduced_14', 'Reduced Rate (14%)'),
        ('reduced_10', 'Reduced Rate (10%)'),
        ('reduced_7', 'Reduced Rate (7%)'),
        ('exempt', 'Exempt (0%)'),
        ('out_of_scope', 'Out of Scope'),
    ], string='VAT Tax Type')
    
    # For IS (Corporate Tax)
    is_tax_type = fields.Selection([
        ('standard', 'Standard Rate (31%)'),
        ('reduced_20', 'Reduced Rate (20%)'),
        ('reduced_15', 'Reduced Rate (15%)'),
        ('reduced_10', 'Reduced Rate (10%)'),
        ('exempt', 'Exempt (0%)'),
    ], string='IS Tax Type')
    
    # For IR (Income Tax)
    ir_tax_type = fields.Selection([
        ('salary', 'Salary'),
        ('professional', 'Professional Income'),
        ('property', 'Property Income'),
        ('capital', 'Capital Income'),
        ('agricultural', 'Agricultural Income'),
        ('other', 'Other Income'),
    ], string='IR Tax Type')
    
    # For tax exemption
    exemption_reason = fields.Char(string='Exemption Reason')
    
    # For tax calculation
    python_compute = fields.Text(string='Python Code', default="result = price_unit * 0.20",
                               help="Python code for tax calculation.")
    
    python_applicable = fields.Text(string='Applicable Code', default="result = True",
                                  help="Python code to determine if the tax is applicable.")
    
    # For tax rounding
    tax_rounding = fields.Selection([
        ('per_line', 'Per Line'),
        ('globally', 'Globally'),
    ], string='Tax Rounding', default='per_line')
    
    @api.onchange('moroccan_tax_type')
    def _onchange_moroccan_tax_type(self):
        if self.moroccan_tax_type == 'vat':
            self.vat_tax_type = 'standard'
            self.amount = 20.0
        elif self.moroccan_tax_type == 'is':
            self.is_tax_type = 'standard'
            self.amount = 31.0
        elif self.moroccan_tax_type == 'ir':
            self.ir_tax_type = 'salary'
            self.amount = 38.0
        elif self.moroccan_tax_type == 'stamp':
            self.amount = 1.0
        elif self.moroccan_tax_type == 'registration':
            self.amount = 5.0
    
    @api.onchange('vat_tax_type')
    def _onchange_vat_tax_type(self):
        if self.vat_tax_type == 'standard':
            self.amount = 20.0
        elif self.vat_tax_type == 'reduced_14':
            self.amount = 14.0
        elif self.vat_tax_type == 'reduced_10':
            self.amount = 10.0
        elif self.vat_tax_type == 'reduced_7':
            self.amount = 7.0
        elif self.vat_tax_type == 'exempt':
            self.amount = 0.0
    
    @api.onchange('is_tax_type')
    def _onchange_is_tax_type(self):
        if self.is_tax_type == 'standard':
            self.amount = 31.0
        elif self.is_tax_type == 'reduced_20':
            self.amount = 20.0
        elif self.is_tax_type == 'reduced_15':
            self.amount = 15.0
        elif self.is_tax_type == 'reduced_10':
            self.amount = 10.0
        elif self.is_tax_type == 'exempt':
            self.amount = 0.0
    
    @api.onchange('amount_type')
    def _onchange_amount_type(self):
        if self.amount_type == 'percent':
            self.price_include = False
        elif self.amount_type == 'fixed':
            self.include_base_amount = False
    
    @api.constrains('amount')
    def _check_amount(self):
        for tax in self:
            if tax.amount_type == 'percent' and (tax.amount < 0 or tax.amount > 100):
                raise ValidationError(_("Percentage amount must be between 0 and 100."))
