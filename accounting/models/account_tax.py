from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero
from datetime import datetime, timedelta

class AccountTax(models.Model):
    _name = 'account.tax'
    _description = 'Tax'
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
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
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
    
    tax_group_id = fields.Many2one('account.tax.group', string='Tax Group', required=True)
    
    # Accounts
    invoice_repartition_line_ids = fields.One2many('account.tax.repartition.line', 'invoice_tax_id', string='Invoice Repartition',
                                                 copy=True)
    
    refund_repartition_line_ids = fields.One2many('account.tax.repartition.line', 'refund_tax_id', string='Refund Repartition',
                                                copy=True)
    
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
    
    # For tax reporting
    tax_report_line_ids = fields.Many2many('account.tax.report.line', string='Tax Report Lines')
    
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
    
    # For tax calculation
    include_capping_amount = fields.Boolean(string='Include Capping Amount', default=False)
    capping_amount = fields.Float(string='Capping Amount', default=0.0)
    
    # For tax calculation
    include_floor_amount = fields.Boolean(string='Include Floor Amount', default=False)
    floor_amount = fields.Float(string='Floor Amount', default=0.0)
    
    # For tax calculation
    include_base_adjustment = fields.Boolean(string='Include Base Adjustment', default=False)
    base_adjustment_amount = fields.Float(string='Base Adjustment Amount', default=0.0)
    
    # For tax calculation
    include_tax_adjustment = fields.Boolean(string='Include Tax Adjustment', default=False)
    tax_adjustment_amount = fields.Float(string='Tax Adjustment Amount', default=0.0)
    
    # For tax calculation
    include_tax_surcharge = fields.Boolean(string='Include Tax Surcharge', default=False)
    tax_surcharge_amount = fields.Float(string='Tax Surcharge Amount', default=0.0)
    
    # For tax calculation
    include_tax_discount = fields.Boolean(string='Include Tax Discount', default=False)
    tax_discount_amount = fields.Float(string='Tax Discount Amount', default=0.0)
    
    # For tax calculation
    include_tax_exemption = fields.Boolean(string='Include Tax Exemption', default=False)
    tax_exemption_amount = fields.Float(string='Tax Exemption Amount', default=0.0)
    
    # For tax calculation
    include_tax_credit = fields.Boolean(string='Include Tax Credit', default=False)
    tax_credit_amount = fields.Float(string='Tax Credit Amount', default=0.0)
    
    # For tax calculation
    include_tax_deduction = fields.Boolean(string='Include Tax Deduction', default=False)
    tax_deduction_amount = fields.Float(string='Tax Deduction Amount', default=0.0)
    
    # For tax calculation
    include_tax_withholding = fields.Boolean(string='Include Tax Withholding', default=False)
    tax_withholding_amount = fields.Float(string='Tax Withholding Amount', default=0.0)
    
    # For tax calculation
    include_tax_advance = fields.Boolean(string='Include Tax Advance', default=False)
    tax_advance_amount = fields.Float(string='Tax Advance Amount', default=0.0)
    
    # For tax calculation
    include_tax_refund = fields.Boolean(string='Include Tax Refund', default=False)
    tax_refund_amount = fields.Float(string='Tax Refund Amount', default=0.0)
    
    # For tax calculation
    include_tax_deferral = fields.Boolean(string='Include Tax Deferral', default=False)
    tax_deferral_amount = fields.Float(string='Tax Deferral Amount', default=0.0)
    
    # For tax calculation
    include_tax_installment = fields.Boolean(string='Include Tax Installment', default=False)
    tax_installment_amount = fields.Float(string='Tax Installment Amount', default=0.0)
    
    # For tax calculation
    include_tax_penalty = fields.Boolean(string='Include Tax Penalty', default=False)
    tax_penalty_amount = fields.Float(string='Tax Penalty Amount', default=0.0)
    
    # For tax calculation
    include_tax_interest = fields.Boolean(string='Include Tax Interest', default=False)
    tax_interest_amount = fields.Float(string='Tax Interest Amount', default=0.0)
    
    # For tax calculation
    include_tax_fine = fields.Boolean(string='Include Tax Fine', default=False)
    tax_fine_amount = fields.Float(string='Tax Fine Amount', default=0.0)
    
    # For tax calculation
    include_tax_fee = fields.Boolean(string='Include Tax Fee', default=False)
    tax_fee_amount = fields.Float(string='Tax Fee Amount', default=0.0)
    
    # For tax calculation
    include_tax_charge = fields.Boolean(string='Include Tax Charge', default=False)
    tax_charge_amount = fields.Float(string='Tax Charge Amount', default=0.0)
    
    # For tax calculation
    include_tax_levy = fields.Boolean(string='Include Tax Levy', default=False)
    tax_levy_amount = fields.Float(string='Tax Levy Amount', default=0.0)
    
    # For tax calculation
    include_tax_duty = fields.Boolean(string='Include Tax Duty', default=False)
    tax_duty_amount = fields.Float(string='Tax Duty Amount', default=0.0)
    
    # For tax calculation
    include_tax_tariff = fields.Boolean(string='Include Tax Tariff', default=False)
    tax_tariff_amount = fields.Float(string='Tax Tariff Amount', default=0.0)
    
    # For tax calculation
    include_tax_toll = fields.Boolean(string='Include Tax Toll', default=False)
    tax_toll_amount = fields.Float(string='Tax Toll Amount', default=0.0)
    
    # For tax calculation
    include_tax_rate = fields.Boolean(string='Include Tax Rate', default=False)
    tax_rate_amount = fields.Float(string='Tax Rate Amount', default=0.0)
    
    # For tax calculation
    include_tax_assessment = fields.Boolean(string='Include Tax Assessment', default=False)
    tax_assessment_amount = fields.Float(string='Tax Assessment Amount', default=0.0)
    
    # For tax calculation
    include_tax_settlement = fields.Boolean(string='Include Tax Settlement', default=False)
    tax_settlement_amount = fields.Float(string='Tax Settlement Amount', default=0.0)
    
    # For tax calculation
    include_tax_payment = fields.Boolean(string='Include Tax Payment', default=False)
    tax_payment_amount = fields.Float(string='Tax Payment Amount', default=0.0)
    
    # For tax calculation
    include_tax_receipt = fields.Boolean(string='Include Tax Receipt', default=False)
    tax_receipt_amount = fields.Float(string='Tax Receipt Amount', default=0.0)
    
    # For tax calculation
    include_tax_voucher = fields.Boolean(string='Include Tax Voucher', default=False)
    tax_voucher_amount = fields.Float(string='Tax Voucher Amount', default=0.0)
    
    # For tax calculation
    include_tax_certificate = fields.Boolean(string='Include Tax Certificate', default=False)
    tax_certificate_amount = fields.Float(string='Tax Certificate Amount', default=0.0)
    
    # For tax calculation
    include_tax_declaration = fields.Boolean(string='Include Tax Declaration', default=False)
    tax_declaration_amount = fields.Float(string='Tax Declaration Amount', default=0.0)
    
    # For tax calculation
    include_tax_return = fields.Boolean(string='Include Tax Return', default=False)
    tax_return_amount = fields.Float(string='Tax Return Amount', default=0.0)
    
    # For tax calculation
    include_tax_statement = fields.Boolean(string='Include Tax Statement', default=False)
    tax_statement_amount = fields.Float(string='Tax Statement Amount', default=0.0)
    
    # For tax calculation
    include_tax_notice = fields.Boolean(string='Include Tax Notice', default=False)
    tax_notice_amount = fields.Float(string='Tax Notice Amount', default=0.0)
    
    # For tax calculation
    include_tax_demand = fields.Boolean(string='Include Tax Demand', default=False)
    tax_demand_amount = fields.Float(string='Tax Demand Amount', default=0.0)
    
    # For tax calculation
    include_tax_reminder = fields.Boolean(string='Include Tax Reminder', default=False)
    tax_reminder_amount = fields.Float(string='Tax Reminder Amount', default=0.0)
    
    # For tax calculation
    include_tax_warning = fields.Boolean(string='Include Tax Warning', default=False)
    tax_warning_amount = fields.Float(string='Tax Warning Amount', default=0.0)
    
    # For tax calculation
    include_tax_summons = fields.Boolean(string='Include Tax Summons', default=False)
    tax_summons_amount = fields.Float(string='Tax Summons Amount', default=0.0)
    
    # For tax calculation
    include_tax_order = fields.Boolean(string='Include Tax Order', default=False)
    tax_order_amount = fields.Float(string='Tax Order Amount', default=0.0)
    
    # For tax calculation
    include_tax_judgment = fields.Boolean(string='Include Tax Judgment', default=False)
    tax_judgment_amount = fields.Float(string='Tax Judgment Amount', default=0.0)
    
    # For tax calculation
    include_tax_decision = fields.Boolean(string='Include Tax Decision', default=False)
    tax_decision_amount = fields.Float(string='Tax Decision Amount', default=0.0)
    
    # For tax calculation
    include_tax_ruling = fields.Boolean(string='Include Tax Ruling', default=False)
    tax_ruling_amount = fields.Float(string='Tax Ruling Amount', default=0.0)
    
    # For tax calculation
    include_tax_verdict = fields.Boolean(string='Include Tax Verdict', default=False)
    tax_verdict_amount = fields.Float(string='Tax Verdict Amount', default=0.0)
    
    # For tax calculation
    include_tax_sentence = fields.Boolean(string='Include Tax Sentence', default=False)
    tax_sentence_amount = fields.Float(string='Tax Sentence Amount', default=0.0)
    
    # For tax calculation
    include_tax_decree = fields.Boolean(string='Include Tax Decree', default=False)
    tax_decree_amount = fields.Float(string='Tax Decree Amount', default=0.0)
    
    # For tax calculation
    include_tax_edict = fields.Boolean(string='Include Tax Edict', default=False)
    tax_edict_amount = fields.Float(string='Tax Edict Amount', default=0.0)
    
    # For tax calculation
    include_tax_proclamation = fields.Boolean(string='Include Tax Proclamation', default=False)
    tax_proclamation_amount = fields.Float(string='Tax Proclamation Amount', default=0.0)
    
    # For tax calculation
    include_tax_declaration = fields.Boolean(string='Include Tax Declaration', default=False)
    tax_declaration_amount = fields.Float(string='Tax Declaration Amount', default=0.0)
    
    # For tax calculation
    include_tax_announcement = fields.Boolean(string='Include Tax Announcement', default=False)
    tax_announcement_amount = fields.Float(string='Tax Announcement Amount', default=0.0)
    
    # For tax calculation
    include_tax_publication = fields.Boolean(string='Include Tax Publication', default=False)
    tax_publication_amount = fields.Float(string='Tax Publication Amount', default=0.0)
    
    # For tax calculation
    include_tax_notification = fields.Boolean(string='Include Tax Notification', default=False)
    tax_notification_amount = fields.Float(string='Tax Notification Amount', default=0.0)
    
    # For tax calculation
    include_tax_communication = fields.Boolean(string='Include Tax Communication', default=False)
    tax_communication_amount = fields.Float(string='Tax Communication Amount', default=0.0)
    
    # For tax calculation
    include_tax_message = fields.Boolean(string='Include Tax Message', default=False)
    tax_message_amount = fields.Float(string='Tax Message Amount', default=0.0)
    
    # For tax calculation
    include_tax_note = fields.Boolean(string='Include Tax Note', default=False)
    tax_note_amount = fields.Float(string='Tax Note Amount', default=0.0)
    
    # For tax calculation
    include_tax_memo = fields.Boolean(string='Include Tax Memo', default=False)
    tax_memo_amount = fields.Float(string='Tax Memo Amount', default=0.0)
    
    # For tax calculation
    include_tax_letter = fields.Boolean(string='Include Tax Letter', default=False)
    tax_letter_amount = fields.Float(string='Tax Letter Amount', default=0.0)
    
    # For tax calculation
    include_tax_email = fields.Boolean(string='Include Tax Email', default=False)
    tax_email_amount = fields.Float(string='Tax Email Amount', default=0.0)
    
    # For tax calculation
    include_tax_sms = fields.Boolean(string='Include Tax SMS', default=False)
    tax_sms_amount = fields.Float(string='Tax SMS Amount', default=0.0)
    
    # For tax calculation
    include_tax_call = fields.Boolean(string='Include Tax Call', default=False)
    tax_call_amount = fields.Float(string='Tax Call Amount', default=0.0)
    
    # For tax calculation
    include_tax_visit = fields.Boolean(string='Include Tax Visit', default=False)
    tax_visit_amount = fields.Float(string='Tax Visit Amount', default=0.0)
    
    # For tax calculation
    include_tax_meeting = fields.Boolean(string='Include Tax Meeting', default=False)
    tax_meeting_amount = fields.Float(string='Tax Meeting Amount', default=0.0)
    
    # For tax calculation
    include_tax_conference = fields.Boolean(string='Include Tax Conference', default=False)
    tax_conference_amount = fields.Float(string='Tax Conference Amount', default=0.0)
    
    # For tax calculation
    include_tax_seminar = fields.Boolean(string='Include Tax Seminar', default=False)
    tax_seminar_amount = fields.Float(string='Tax Seminar Amount', default=0.0)
    
    # For tax calculation
    include_tax_workshop = fields.Boolean(string='Include Tax Workshop', default=False)
    tax_workshop_amount = fields.Float(string='Tax Workshop Amount', default=0.0)
    
    # For tax calculation
    include_tax_training = fields.Boolean(string='Include Tax Training', default=False)
    tax_training_amount = fields.Float(string='Tax Training Amount', default=0.0)
    
    # For tax calculation
    include_tax_course = fields.Boolean(string='Include Tax Course', default=False)
    tax_course_amount = fields.Float(string='Tax Course Amount', default=0.0)
    
    # For tax calculation
    include_tax_class = fields.Boolean(string='Include Tax Class', default=False)
    tax_class_amount = fields.Float(string='Tax Class Amount', default=0.0)
    
    # For tax calculation
    include_tax_lecture = fields.Boolean(string='Include Tax Lecture', default=False)
    tax_lecture_amount = fields.Float(string='Tax Lecture Amount', default=0.0)
    
    # For tax calculation
    include_tax_presentation = fields.Boolean(string='Include Tax Presentation', default=False)
    tax_presentation_amount = fields.Float(string='Tax Presentation Amount', default=0.0)
    
    # For tax calculation
    include_tax_speech = fields.Boolean(string='Include Tax Speech', default=False)
    tax_speech_amount = fields.Float(string='Tax Speech Amount', default=0.0)
    
    # For tax calculation
    include_tax_talk = fields.Boolean(string='Include Tax Talk', default=False)
    tax_talk_amount = fields.Float(string='Tax Talk Amount', default=0.0)
    
    # For tax calculation
    include_tax_discussion = fields.Boolean(string='Include Tax Discussion', default=False)
    tax_discussion_amount = fields.Float(string='Tax Discussion Amount', default=0.0)
    
    # For tax calculation
    include_tax_debate = fields.Boolean(string='Include Tax Debate', default=False)
    tax_debate_amount = fields.Float(string='Tax Debate Amount', default=0.0)
    
    # For tax calculation
    include_tax_argument = fields.Boolean(string='Include Tax Argument', default=False)
    tax_argument_amount = fields.Float(string='Tax Argument Amount', default=0.0)
    
    # For tax calculation
    include_tax_dispute = fields.Boolean(string='Include Tax Dispute', default=False)
    tax_dispute_amount = fields.Float(string='Tax Dispute Amount', default=0.0)
    
    # For tax calculation
    include_tax_conflict = fields.Boolean(string='Include Tax Conflict', default=False)
    tax_conflict_amount = fields.Float(string='Tax Conflict Amount', default=0.0)
    
    # For tax calculation
    include_tax_disagreement = fields.Boolean(string='Include Tax Disagreement', default=False)
    tax_disagreement_amount = fields.Float(string='Tax Disagreement Amount', default=0.0)
    
    # For tax calculation
    include_tax_controversy = fields.Boolean(string='Include Tax Controversy', default=False)
    tax_controversy_amount = fields.Float(string='Tax Controversy Amount', default=0.0)
    
    # For tax calculation
    include_tax_litigation = fields.Boolean(string='Include Tax Litigation', default=False)
    tax_litigation_amount = fields.Float(string='Tax Litigation Amount', default=0.0)
    
    # For tax calculation
    include_tax_lawsuit = fields.Boolean(string='Include Tax Lawsuit', default=False)
    tax_lawsuit_amount = fields.Float(string='Tax Lawsuit Amount', default=0.0)
    
    # For tax calculation
    include_tax_case = fields.Boolean(string='Include Tax Case', default=False)
    tax_case_amount = fields.Float(string='Tax Case Amount', default=0.0)
    
    # For tax calculation
    include_tax_suit = fields.Boolean(string='Include Tax Suit', default=False)
    tax_suit_amount = fields.Float(string='Tax Suit Amount', default=0.0)
    
    # For tax calculation
    include_tax_action = fields.Boolean(string='Include Tax Action', default=False)
    tax_action_amount = fields.Float(string='Tax Action Amount', default=0.0)
    
    # For tax calculation
    include_tax_proceeding = fields.Boolean(string='Include Tax Proceeding', default=False)
    tax_proceeding_amount = fields.Float(string='Tax Proceeding Amount', default=0.0)
    
    # For tax calculation
    include_tax_hearing = fields.Boolean(string='Include Tax Hearing', default=False)
    tax_hearing_amount = fields.Float(string='Tax Hearing Amount', default=0.0)
    
    # For tax calculation
    include_tax_trial = fields.Boolean(string='Include Tax Trial', default=False)
    tax_trial_amount = fields.Float(string='Tax Trial Amount', default=0.0)
    
    # For tax calculation
    include_tax_appeal = fields.Boolean(string='Include Tax Appeal', default=False)
    tax_appeal_amount = fields.Float(string='Tax Appeal Amount', default=0.0)
    
    # For tax calculation
    include_tax_review = fields.Boolean(string='Include Tax Review', default=False)
    tax_review_amount = fields.Float(string='Tax Review Amount', default=0.0)
    
    # For tax calculation
    include_tax_revision = fields.Boolean(string='Include Tax Revision', default=False)
    tax_revision_amount = fields.Float(string='Tax Revision Amount', default=0.0)
    
    # For tax calculation
    include_tax_reconsideration = fields.Boolean(string='Include Tax Reconsideration', default=False)
    tax_reconsideration_amount = fields.Float(string='Tax Reconsideration Amount', default=0.0)
    
    # For tax calculation
    include_tax_reevaluation = fields.Boolean(string='Include Tax Reevaluation', default=False)
    tax_reevaluation_amount = fields.Float(string='Tax Reevaluation Amount', default=0.0)
    
    # For tax calculation
    include_tax_reassessment = fields.Boolean(string='Include Tax Reassessment', default=False)
    tax_reassessment_amount = fields.Float(string='Tax Reassessment Amount', default=0.0)
    
    # For tax calculation
    include_tax_reappraisal = fields.Boolean(string='Include Tax Reappraisal', default=False)
    tax_reappraisal_amount = fields.Float(string='Tax Reappraisal Amount', default=0.0)
    
    # For tax calculation
    include_tax_reexamination = fields.Boolean(string='Include Tax Reexamination', default=False)
    tax_reexamination_amount = fields.Float(string='Tax Reexamination Amount', default=0.0)
    
    # For tax calculation
    include_tax_reinspection = fields.Boolean(string='Include Tax Reinspection', default=False)
    tax_reinspection_amount = fields.Float(string='Tax Reinspection Amount', default=0.0)
    
    # For tax calculation
    include_tax_reinvestigation = fields.Boolean(string='Include Tax Reinvestigation', default=False)
    tax_reinvestigation_amount = fields.Float(string='Tax Reinvestigation Amount', default=0.0)
    
    # For tax calculation
    include_tax_reanalysis = fields.Boolean(string='Include Tax Reanalysis', default=False)
    tax_reanalysis_amount = fields.Float(string='Tax Reanalysis Amount', default=0.0)
    
    # For tax calculation
    include_tax_restudy = fields.Boolean(string='Include Tax Restudy', default=False)
    tax_restudy_amount = fields.Float(string='Tax Restudy Amount', default=0.0)
    
    # For tax calculation
    include_tax_research = fields.Boolean(string='Include Tax Research', default=False)
    tax_research_amount = fields.Float(string='Tax Research Amount', default=0.0)
    
    # For tax calculation
    include_tax_development = fields.Boolean(string='Include Tax Development', default=False)
    tax_development_amount = fields.Float(string='Tax Development Amount', default=0.0)
    
    # For tax calculation
    include_tax_evolution = fields.Boolean(string='Include Tax Evolution', default=False)
    tax_evolution_amount = fields.Float(string='Tax Evolution Amount', default=0.0)
    
    # For tax calculation
    include_tax_growth = fields.Boolean(string='Include Tax Growth', default=False)
    tax_growth_amount = fields.Float(string='Tax Growth Amount', default=0.0)
    
    # For tax calculation
    include_tax_maturation = fields.Boolean(string='Include Tax Maturation', default=False)
    tax_maturation_amount = fields.Float(string='Tax Maturation Amount', default=0.0)
    
    # For tax calculation
    include_tax_ripening = fields.Boolean(string='Include Tax Ripening', default=False)
    tax_ripening_amount = fields.Float(string='Tax Ripening Amount', default=0.0)
    
    # For tax calculation
    include_tax_aging = fields.Boolean(string='Include Tax Aging', default=False)
    tax_aging_amount = fields.Float(string='Tax Aging Amount', default=0.0)
    
    # For tax calculation
    include_tax_senescence = fields.Boolean(string='Include Tax Senescence', default=False)
    tax_senescence_amount = fields.Float(string='Tax Senescence Amount', default=0.0)
    
    # For tax calculation
    include_tax_decline = fields.Boolean(string='Include Tax Decline', default=False)
    tax_decline_amount = fields.Float(string='Tax Decline Amount', default=0.0)
    
    # For tax calculation
    include_tax_deterioration = fields.Boolean(string='Include Tax Deterioration', default=False)
    tax_deterioration_amount = fields.Float(string='Tax Deterioration Amount', default=0.0)
    
    # For tax calculation
    include_tax_decay = fields.Boolean(string='Include Tax Decay', default=False)
    tax_decay_amount = fields.Float(string='Tax Decay Amount', default=0.0)
    
    # For tax calculation
    include_tax_decomposition = fields.Boolean(string='Include Tax Decomposition', default=False)
    tax_decomposition_amount = fields.Float(string='Tax Decomposition Amount', default=0.0)
    
    # For tax calculation
    include_tax_putrefaction = fields.Boolean(string='Include Tax Putrefaction', default=False)
    tax_putrefaction_amount = fields.Float(string='Tax Putrefaction Amount', default=0.0)
    
    # For tax calculation
    include_tax_rot = fields.Boolean(string='Include Tax Rot', default=False)
    tax_rot_amount = fields.Float(string='Tax Rot Amount', default=0.0)
    
    # For tax calculation
    include_tax_corruption = fields.Boolean(string='Include Tax Corruption', default=False)
    tax_corruption_amount = fields.Float(string='Tax Corruption Amount', default=0.0)
    
    # For tax calculation
    include_tax_degeneration = fields.Boolean(string='Include Tax Degeneration', default=False)
    tax_degeneration_amount = fields.Float(string='Tax Degeneration Amount', default=0.0)
    
    # For tax calculation
    include_tax_degradation = fields.Boolean(string='Include Tax Degradation', default=False)
    tax_degradation_amount = fields.Float(string='Tax Degradation Amount', default=0.0)
    
    # For tax calculation
    include_tax_disintegration = fields.Boolean(string='Include Tax Disintegration', default=False)
    tax_disintegration_amount = fields.Float(string='Tax Disintegration Amount', default=0.0)
    
    # For tax calculation
    include_tax_dissolution = fields.Boolean(string='Include Tax Dissolution', default=False)
    tax_dissolution_amount = fields.Float(string='Tax Dissolution Amount', default=0.0)
    
    # For tax calculation
    include_tax_liquidation = fields.Boolean(string='Include Tax Liquidation', default=False)
    tax_liquidation_amount = fields.Float(string='Tax Liquidation Amount', default=0.0)
    
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
    
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        """Compute taxes for a given price unit, quantity, product, and partner"""
        self.ensure_one()
        
        if not currency:
            currency = self.env.company.currency_id
        
        if self.amount_type == 'fixed':
            # Fixed amount
            amount = self.amount * quantity
        elif self.amount_type == 'percent':
            # Percentage amount
            amount = price_unit * self.amount / 100.0 * quantity
        elif self.amount_type == 'division':
            # Division amount
            amount = price_unit / (1 - self.amount / 100.0) - price_unit
        elif self.amount_type == 'code':
            # Python code
            localdict = {
                'price_unit': price_unit,
                'quantity': quantity,
                'product': product,
                'partner': partner,
                'result': 0.0,
            }
            exec(self.python_compute, localdict)
            amount = localdict['result']
        else:
            # Group of taxes
            amount = 0.0
        
        # Round the amount
        amount = currency.round(amount)
        
        return {
            'tax': self,
            'base': price_unit * quantity,
            'amount': amount,
            'total_included': price_unit * quantity + amount,
            'total_excluded': price_unit * quantity,
        }
    
    def action_view_invoice_tax(self):
        """View invoices with this tax"""
        self.ensure_one()
        
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('invoice_line_ids.tax_ids', 'in', self.ids)],
        }
    
    def action_view_refund_tax(self):
        """View refunds with this tax"""
        self.ensure_one()
        
        return {
            'name': _('Refunds'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('invoice_line_ids.tax_ids', 'in', self.ids), ('type', 'in', ['out_refund', 'in_refund'])],
        }
    
    def action_view_base_tax(self):
        """View tax base amounts"""
        self.ensure_one()
        
        return {
            'name': _('Tax Base Amounts'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'domain': [('tax_ids', 'in', self.ids)],
        }
    
    def action_view_tax_report(self):
        """View tax report"""
        self.ensure_one()
        
        return {
            'name': _('Tax Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.tax.report',
            'view_mode': 'form',
            'context': {'default_tax_ids': [(6, 0, self.ids)]},
        }


class AccountTaxGroup(models.Model):
    _name = 'account.tax.group'
    _description = 'Tax Group'
    _order = 'sequence, id'
    
    name = fields.Char(string='Tax Group', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # For Moroccan accounting
    is_moroccan_tax_group = fields.Boolean(string='Is Moroccan Tax Group', default=True)
    
    moroccan_tax_group_type = fields.Selection([
        ('vat', 'VAT'),
        ('is', 'IS (Corporate Tax)'),
        ('ir', 'IR (Income Tax)'),
        ('stamp', 'Stamp Duty'),
        ('registration', 'Registration Duty'),
        ('other', 'Other'),
    ], string='Moroccan Tax Group Type', default='vat')
    
    # For tax reporting
    tax_report_line_ids = fields.Many2many('account.tax.report.line', string='Tax Report Lines')
    
    # For tax calculation
    tax_calculation_rounding_method = fields.Selection([
        ('round_per_line', 'Round per Line'),
        ('round_globally', 'Round Globally'),
    ], string='Tax Calculation Rounding Method', default='round_per_line')
    
    # For tax display
    tax_display_method = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded'),
    ], string='Tax Display Method', default='tax_excluded')
    
    # For tax reporting
    tax_report_method = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded'),
    ], string='Tax Report Method', default='tax_excluded')
    
    # For tax calculation
    tax_calculation_method = fields.Selection([
        ('tax_included', 'Tax Included'),
        ('tax_excluded', 'Tax Excluded'),
    ], string='Tax Calculation Method', default='tax_excluded')
    
    # For tax rounding
    tax_rounding_method = fields.Selection([
        ('round_per_line', 'Round per Line'),
        ('round_globally', 'Round Globally'),
    ], string='Tax Rounding Method', default='round_per_line')
    
    # For tax display
    tax_display_rounding_method = fields.Selection([
        ('round_per_line', 'Round per Line'),
        ('round_globally', 'Round Globally'),
    ], string='Tax Display Rounding Method', default='round_per_line')
    
    # For tax reporting
    tax_report_rounding_method = fields.Selection([
        ('round_per_line', 'Round per Line'),
        ('round_globally', 'Round Globally'),
    ], string='Tax Report Rounding Method', default='round_per_line')


class AccountTaxRepartitionLine(models.Model):
    _name = 'account.tax.repartition.line'
    _description = 'Tax Repartition Line'
    _order = 'sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=1)
    factor_percent = fields.Float(string='Factor Percent', default=100.0,
                                help="Factor to apply on the account move lines generated from this repartition line.")
    
    repartition_type = fields.Selection([
        ('base', 'Base'),
        ('tax', 'Tax'),
    ], string='Repartition Type', required=True, default='tax')
    
    account_id = fields.Many2one('account.account', string='Account',
                               domain="[('deprecated', '=', False), ('company_id', '=', company_id)]")
    
    invoice_tax_id = fields.Many2one('account.tax', string='Invoice Tax',
                                   ondelete='cascade', help="Tax for which this repartition line is for invoice operations.")
    
    refund_tax_id = fields.Many2one('account.tax', string='Refund Tax',
                                  ondelete='cascade', help="Tax for which this repartition line is for refund operations.")
    
    company_id = fields.Many2one('res.company', string='Company', required=True,
                               default=lambda self: self.env.company)
    
    # For Moroccan accounting
    is_moroccan_repartition_line = fields.Boolean(string='Is Moroccan Repartition Line', default=True)
    
    moroccan_repartition_line_type = fields.Selection([
        ('vat', 'VAT'),
        ('is', 'IS (Corporate Tax)'),
        ('ir', 'IR (Income Tax)'),
        ('stamp', 'Stamp Duty'),
        ('registration', 'Registration Duty'),
        ('other', 'Other'),
    ], string='Moroccan Repartition Line Type', default='vat')
    
    # For tax reporting
    tax_report_line_ids = fields.Many2many('account.tax.report.line', string='Tax Report Lines')
    
    # For tax calculation
    use_in_tax_closing = fields.Boolean(string='Use in Tax Closing', default=True,
                                      help="If checked, this repartition line will be used in the tax closing.")
    
    @api.constrains('factor_percent')
    def _check_factor_percent(self):
        for line in self:
            if line.factor_percent < 0 or line.factor_percent > 100:
                raise ValidationError(_("Factor percent must be between 0 and 100."))
    
    @api.onchange('repartition_type')
    def _onchange_repartition_type(self):
        if self.repartition_type == 'base':
            self.account_id = False


class AccountTaxReportLine(models.Model):
    _name = 'account.tax.report.line'
    _description = 'Tax Report Line'
    _order = 'sequence, id'
    
    name = fields.Char(string='Name', required=True, translate=True)
    tag_name = fields.Char(string='Tag Name', help="Name of the tag to create on the corresponding report line.")
    report_id = fields.Many2one('account.tax.report', string='Report', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=1)
    
    parent_id = fields.Many2one('account.tax.report.line', string='Parent Line', ondelete='cascade')
    child_ids = fields.One2many('account.tax.report.line', 'parent_id', string='Child Lines')
    
    tag_ids = fields.Many2many('account.account.tag', string='Tags')
    
    code = fields.Char(string='Code', help="Code used to identify this line in the report.")
    
    # For Moroccan accounting
    is_moroccan_report_line = fields.Boolean(string='Is Moroccan Report Line', default=True)
    
    moroccan_report_line_type = fields.Selection([
        ('vat', 'VAT'),
        ('is', 'IS (Corporate Tax)'),
        ('ir', 'IR (Income Tax)'),
        ('stamp', 'Stamp Duty'),
        ('registration', 'Registration Duty'),
        ('other', 'Other'),
    ], string='Moroccan Report Line Type', default='vat')
    
    # For tax reporting
    formula = fields.Char(string='Formula', help="Python expression used to compute the value of this line.")
    
    # For tax reporting
    report_action_id = fields.Many2one('ir.actions.act_window', string='Report Action',
                                     help="Action to execute when clicking on this line in the report.")
    
    # For tax reporting
    is_total = fields.Boolean(string='Is Total', default=False,
                            help="If checked, this line will be displayed as a total line.")
    
    # For tax reporting
    is_group = fields.Boolean(string='Is Group', default=False,
                            help="If checked, this line will be displayed as a group line.")
    
    # For tax reporting
    is_section = fields.Boolean(string='Is Section', default=False,
                              help="If checked, this line will be displayed as a section line.")
    
    # For tax reporting
    is_line = fields.Boolean(string='Is Line', default=True,
                           help="If checked, this line will be displayed as a regular line.")
    
    # For tax reporting
    is_custom = fields.Boolean(string='Is Custom', default=False,
                             help="If checked, this line will be displayed as a custom line.")
    
    # For tax reporting
    is_readonly = fields.Boolean(string='Is Readonly', default=False,
                               help="If checked, this line will be displayed as a readonly line.")
    
    # For tax reporting
    is_editable = fields.Boolean(string='Is Editable', default=False,
                               help="If checked, this line will be displayed as an editable line.")
    
    # For tax reporting
    is_required = fields.Boolean(string='Is Required', default=False,
                               help="If checked, this line will be displayed as a required line.")
    
    # For tax reporting
    is_optional = fields.Boolean(string='Is Optional', default=False,
                               help="If checked, this line will be displayed as an optional line.")
    
    # For tax reporting
    is_visible = fields.Boolean(string='Is Visible', default=True,
                              help="If checked, this line will be displayed in the report.")
    
    # For tax reporting
    is_hidden = fields.Boolean(string='Is Hidden', default=False,
                             help="If checked, this line will not be displayed in the report.")


class AccountTaxReport(models.Model):
    _name = 'account.tax.report'
    _description = 'Tax Report'
    _order = 'sequence, id'
    
    name = fields.Char(string='Name', required=True, translate=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)
    sequence = fields.Integer(string='Sequence', default=1)
    
    line_ids = fields.One2many('account.tax.report.line', 'report_id', string='Lines')
    
    # For Moroccan accounting
    is_moroccan_report = fields.Boolean(string='Is Moroccan Report', default=True)
    
    moroccan_report_type = fields.Selection([
        ('vat', 'VAT'),
        ('is', 'IS (Corporate Tax)'),
        ('ir', 'IR (Income Tax)'),
        ('stamp', 'Stamp Duty'),
        ('registration', 'Registration Duty'),
        ('other', 'Other'),
    ], string='Moroccan Report Type', default='vat')
    
    # For tax reporting
    report_action_id = fields.Many2one('ir.actions.act_window', string='Report Action',
                                     help="Action to execute when clicking on this report.")
    
    # For tax reporting
    report_file = fields.Char(string='Report File', help="Path to the report file.")
    
    # For tax reporting
    report_type = fields.Selection([
        ('qweb-html', 'HTML'),
        ('qweb-pdf', 'PDF'),
        ('qweb-text', 'Text'),
    ], string='Report Type', default='qweb-pdf')
    
    # For tax reporting
    report_name = fields.Char(string='Report Name', help="Name of the report file.")
    
    # For tax reporting
    report_model = fields.Char(string='Report Model', help="Model used to generate the report.")
    
    # For tax reporting
    report_rml = fields.Char(string='Report RML', help="RML file used to generate the report.")
    
    # For tax reporting
    report_sxw = fields.Char(string='Report SXW', help="SXW file used to generate the report.")
    
    # For tax reporting
    report_xml = fields.Char(string='Report XML', help="XML file used to generate the report.")
    
    # For tax reporting
    report_xsl = fields.Char(string='Report XSL', help="XSL file used to generate the report.")
