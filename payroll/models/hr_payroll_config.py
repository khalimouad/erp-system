# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class HrPayrollConfig(models.Model):
    _name = 'hr.payroll.config'
    _description = 'Payroll Configuration'
    _order = 'date_from desc, id desc'
    
    name = fields.Char(string='Name', required=True)
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    active = fields.Boolean(string='Active', default=True)
    
    # SMIG/SMAG
    smig_horaire = fields.Float(string='SMIG Hourly', default=17.10)
    smig_mensuel = fields.Float(string='SMIG Monthly', compute='_compute_smig_mensuel', store=True)
    smag_horaire = fields.Float(string='SMAG Hourly', default=93.01)
    smag_mensuel = fields.Float(string='SMAG Monthly', compute='_compute_smag_mensuel', store=True)
    
    # CNSS
    cnss_employee_rate = fields.Float(string='CNSS Employee Rate (%)', default=4.48)
    cnss_employer_rate = fields.Float(string='CNSS Employer Rate (%)', default=8.98)
    cnss_af_employer_rate = fields.Float(string='Family Allowance Employer Rate (%)', default=6.40)
    cnss_fp_employer_rate = fields.Float(string='Professional Training Employer Rate (%)', default=1.60)
    cnss_ceiling = fields.Float(string='CNSS Ceiling', default=6000.00)
    
    # AMO
    amo_employee_rate = fields.Float(string='AMO Employee Rate (%)', default=2.26)
    amo_employer_rate = fields.Float(string='AMO Employer Rate (%)', default=2.26)
    amo_contribution_employer_rate = fields.Float(string='AMO Contribution Employer Rate (%)', default=1.85)
    
    # Seniority
    seniority_0_2_rate = fields.Float(string='Seniority Rate 0-2 years (%)', default=0.0)
    seniority_2_5_rate = fields.Float(string='Seniority Rate 2-5 years (%)', default=5.0)
    seniority_5_12_rate = fields.Float(string='Seniority Rate 5-12 years (%)', default=10.0)
    seniority_12_20_rate = fields.Float(string='Seniority Rate 12-20 years (%)', default=15.0)
    seniority_20_25_rate = fields.Float(string='Seniority Rate 20-25 years (%)', default=20.0)
    seniority_25_plus_rate = fields.Float(string='Seniority Rate 25+ years (%)', default=25.0)
    
    # Professional Expenses
    fp_rate_below_78000 = fields.Float(string='Professional Expenses Rate if Annual SBI ≤ 78000 (%)', default=35.0)
    fp_max_below_78000 = fields.Float(string='Max Professional Expenses if Annual SBI ≤ 78000', default=30000.0)
    fp_rate_above_78000 = fields.Float(string='Professional Expenses Rate if Annual SBI > 78000 (%)', default=25.0)
    fp_max_above_78000 = fields.Float(string='Max Professional Expenses if Annual SBI > 78000', default=35000.0)
    fp_monthly_ceiling = fields.Float(string='Monthly Professional Expenses Ceiling', default=2916.67)
    
    # IR - Monthly tax brackets
    ir_monthly_threshold_1 = fields.Float(string='IR Monthly Threshold 1', default=3333.00)
    ir_monthly_threshold_2 = fields.Float(string='IR Monthly Threshold 2', default=5000.00)
    ir_monthly_threshold_3 = fields.Float(string='IR Monthly Threshold 3', default=6667.00)
    ir_monthly_threshold_4 = fields.Float(string='IR Monthly Threshold 4', default=8333.00)
    ir_monthly_threshold_5 = fields.Float(string='IR Monthly Threshold 5', default=15000.00)
    
    ir_monthly_rate_1 = fields.Float(string='IR Monthly Rate 1 (%)', default=0.0)
    ir_monthly_rate_2 = fields.Float(string='IR Monthly Rate 2 (%)', default=10.0)
    ir_monthly_rate_3 = fields.Float(string='IR Monthly Rate 3 (%)', default=20.0)
    ir_monthly_rate_4 = fields.Float(string='IR Monthly Rate 4 (%)', default=30.0)
    ir_monthly_rate_5 = fields.Float(string='IR Monthly Rate 5 (%)', default=34.0)
    ir_monthly_rate_6 = fields.Float(string='IR Monthly Rate 6 (%)', default=37.0)
    
    ir_monthly_deduction_1 = fields.Float(string='IR Monthly Deduction 1', default=0.0)
    ir_monthly_deduction_2 = fields.Float(string='IR Monthly Deduction 2', default=333.33)
    ir_monthly_deduction_3 = fields.Float(string='IR Monthly Deduction 3', default=833.33)
    ir_monthly_deduction_4 = fields.Float(string='IR Monthly Deduction 4', default=1500.00)
    ir_monthly_deduction_5 = fields.Float(string='IR Monthly Deduction 5', default=1833.33)
    ir_monthly_deduction_6 = fields.Float(string='IR Monthly Deduction 6', default=2283.33)
    
    # Family Charges
    family_allowance_deduction = fields.Float(string='Family Allowance Deduction per Person', default=41.67)
    
    # Overtime
    overtime_rate_day_normal = fields.Float(string='Overtime Rate Day (normal) (%)', default=25.0)
    overtime_rate_night_normal = fields.Float(string='Overtime Rate Night (normal) (%)', default=50.0)
    overtime_rate_day_holiday = fields.Float(string='Overtime Rate Day (holiday) (%)', default=50.0)
    overtime_rate_night_holiday = fields.Float(string='Overtime Rate Night (holiday) (%)', default=100.0)
    
    @api.depends('smig_horaire')
    def _compute_smig_mensuel(self):
        for record in self:
            record.smig_mensuel = record.smig_horaire * 191
    
    @api.depends('smag_horaire')
    def _compute_smag_mensuel(self):
        for record in self:
            record.smag_mensuel = record.smag_horaire * 26
    
    @api.model
    def get_current_config(self):
        """Get the current active configuration based on date"""
        today = fields.Date.today()
        config = self.search([
            ('date_from', '<=', today),
            ('date_to', '>=', today),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            # If no config found for current date, get the latest one
            config = self.search([('active', '=', True)], order='date_to desc', limit=1)
        
        if not config:
            # If still no config, create a default one
            config = self.create({
                'name': 'Default Configuration',
                'date_from': fields.Date.today().replace(month=1, day=1),
                'date_to': fields.Date.today().replace(month=12, day=31),
            })
        
        return config
