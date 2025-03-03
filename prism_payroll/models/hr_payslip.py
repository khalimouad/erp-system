# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    # Moroccan-specific fields
    matricule = fields.Char(string='Employee ID', related='employee_id.matricule', store=True)
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash')
    ], string='Payment Method', default='bank_transfer')
    
    # Computed fields for Moroccan payroll
    seniority_years = fields.Integer(string='Seniority (Years)', compute='_compute_seniority', store=True)
    seniority_rate = fields.Float(string='Seniority Rate (%)', compute='_compute_seniority_rate', store=True)
    seniority_amount = fields.Float(string='Seniority Amount', compute='_compute_seniority_amount', store=True)
    
    # CNSS and AMO
    cnss_base = fields.Float(string='CNSS Base', compute='_compute_cnss', store=True)
    cnss_employee = fields.Float(string='CNSS Employee', compute='_compute_cnss', store=True)
    cnss_employer = fields.Float(string='CNSS Employer', compute='_compute_cnss', store=True)
    amo_employee = fields.Float(string='AMO Employee', compute='_compute_amo', store=True)
    amo_employer = fields.Float(string='AMO Employer', compute='_compute_amo', store=True)
    
    # IR (Income Tax)
    ir_base = fields.Float(string='IR Base', compute='_compute_ir', store=True)
    ir_amount = fields.Float(string='IR Amount', compute='_compute_ir', store=True)
    
    # Professional expenses
    prof_exp_amount = fields.Float(string='Professional Expenses', compute='_compute_prof_exp', store=True)
    
    # Net salary
    net_salary = fields.Float(string='Net Salary', compute='_compute_net_salary', store=True)
    
    @api.depends('employee_id', 'date_from')
    def _compute_seniority(self):
        for payslip in self:
            if payslip.employee_id and payslip.employee_id.date_embauche and payslip.date_from:
                delta = relativedelta(payslip.date_from, payslip.employee_id.date_embauche)
                payslip.seniority_years = delta.years
            else:
                payslip.seniority_years = 0
    
    @api.depends('seniority_years')
    def _compute_seniority_rate(self):
        for payslip in self:
            config = self.env['hr.payroll.config'].get_current_config()
            
            if payslip.seniority_years < 2:
                payslip.seniority_rate = config.seniority_0_2_rate
            elif payslip.seniority_years < 5:
                payslip.seniority_rate = config.seniority_2_5_rate
            elif payslip.seniority_years < 12:
                payslip.seniority_rate = config.seniority_5_12_rate
            elif payslip.seniority_years < 20:
                payslip.seniority_rate = config.seniority_12_20_rate
            elif payslip.seniority_years < 25:
                payslip.seniority_rate = config.seniority_20_25_rate
            else:
                payslip.seniority_rate = config.seniority_25_plus_rate
    
    @api.depends('contract_id.wage', 'seniority_rate')
    def _compute_seniority_amount(self):
        for payslip in self:
            if payslip.contract_id and payslip.contract_id.wage:
                payslip.seniority_amount = payslip.contract_id.wage * (payslip.seniority_rate / 100.0)
            else:
                payslip.seniority_amount = 0.0
    
    @api.depends('contract_id.gross_salary')
    def _compute_cnss(self):
        for payslip in self:
            config = self.env['hr.payroll.config'].get_current_config()
            
            if payslip.contract_id and payslip.contract_id.gross_salary:
                # CNSS is capped
                payslip.cnss_base = min(payslip.contract_id.gross_salary, config.cnss_ceiling)
                payslip.cnss_employee = payslip.cnss_base * (config.cnss_employee_rate / 100.0)
                payslip.cnss_employer = payslip.cnss_base * (config.cnss_employer_rate / 100.0)
            else:
                payslip.cnss_base = 0.0
                payslip.cnss_employee = 0.0
                payslip.cnss_employer = 0.0
    
    @api.depends('contract_id.gross_salary')
    def _compute_amo(self):
        for payslip in self:
            config = self.env['hr.payroll.config'].get_current_config()
            
            if payslip.contract_id and payslip.contract_id.gross_salary:
                # AMO is not capped
                payslip.amo_employee = payslip.contract_id.gross_salary * (config.amo_employee_rate / 100.0)
                payslip.amo_employer = payslip.contract_id.gross_salary * (config.amo_employer_rate / 100.0)
            else:
                payslip.amo_employee = 0.0
                payslip.amo_employer = 0.0
    
    @api.depends('contract_id.gross_salary')
    def _compute_prof_exp(self):
        for payslip in self:
            config = self.env['hr.payroll.config'].get_current_config()
            
            if payslip.contract_id and payslip.contract_id.gross_salary:
                annual_salary = payslip.contract_id.gross_salary * 12
                
                if annual_salary <= 78000:
                    rate = config.fp_rate_below_78000
                    max_amount = config.fp_max_below_78000
                else:
                    rate = config.fp_rate_above_78000
                    max_amount = config.fp_max_above_78000
                
                # Calculate monthly amount
                monthly_amount = min(
                    payslip.contract_id.gross_salary * (rate / 100.0),
                    max_amount / 12
                )
                
                # Apply monthly ceiling
                payslip.prof_exp_amount = min(monthly_amount, config.fp_monthly_ceiling)
            else:
                payslip.prof_exp_amount = 0.0
    
    @api.depends('contract_id.gross_salary', 'cnss_employee', 'amo_employee', 'prof_exp_amount')
    def _compute_ir(self):
        for payslip in self:
            config = self.env['hr.payroll.config'].get_current_config()
            
            if payslip.contract_id and payslip.contract_id.gross_salary:
                # Calculate IR base
                payslip.ir_base = (
                    payslip.contract_id.gross_salary - 
                    payslip.cnss_employee - 
                    payslip.amo_employee - 
                    payslip.prof_exp_amount
                )
                
                # Apply family charges deduction
                children_deduction = min(payslip.employee_id.children or 0, 6) * config.family_allowance_deduction
                net_after_children = payslip.ir_base - children_deduction
                
                # Apply IR brackets
                if net_after_children <= config.ir_monthly_threshold_1:
                    ir_amount = (net_after_children * config.ir_monthly_rate_1 / 100) - config.ir_monthly_deduction_1
                elif net_after_children <= config.ir_monthly_threshold_2:
                    ir_amount = (net_after_children * config.ir_monthly_rate_2 / 100) - config.ir_monthly_deduction_2
                elif net_after_children <= config.ir_monthly_threshold_3:
                    ir_amount = (net_after_children * config.ir_monthly_rate_3 / 100) - config.ir_monthly_deduction_3
                elif net_after_children <= config.ir_monthly_threshold_4:
                    ir_amount = (net_after_children * config.ir_monthly_rate_4 / 100) - config.ir_monthly_deduction_4
                elif net_after_children <= config.ir_monthly_threshold_5:
                    ir_amount = (net_after_children * config.ir_monthly_rate_5 / 100) - config.ir_monthly_deduction_5
                else:
                    ir_amount = (net_after_children * config.ir_monthly_rate_6 / 100) - config.ir_monthly_deduction_6
                
                payslip.ir_amount = max(ir_amount, 0)
            else:
                payslip.ir_base = 0.0
                payslip.ir_amount = 0.0
    
    @api.depends('contract_id.gross_salary', 'cnss_employee', 'amo_employee', 'ir_amount')
    def _compute_net_salary(self):
        for payslip in self:
            if payslip.contract_id and payslip.contract_id.gross_salary:
                payslip.net_salary = (
                    payslip.contract_id.gross_salary - 
                    payslip.cnss_employee - 
                    payslip.amo_employee - 
                    payslip.ir_amount
                )
            else:
                payslip.net_salary = 0.0
    
    def compute_sheet(self):
        for payslip in self:
            # Get employee data
            employee = payslip.employee_id
            date_from = payslip.date_from
            date_to = payslip.date_to
            
            # Calculate worked days
            worked_days = self._compute_worked_days(employee, date_from, date_to)
            payslip.worked_days_line_ids = worked_days
            
            # Calculate base salary
            base_salary = payslip.contract_id.wage
            
            # Create lines
            lines = []
            
            # Base salary
            lines.append({
                'name': 'Salaire de Base',
                'code': 'BASE',
                'amount': base_salary,
                'category_id': self.env.ref('hr_payroll.BASIC').id,
            })
            
            # Seniority
            if payslip.seniority_amount > 0:
                lines.append({
                    'name': "Prime d'Ancienneté",
                    'code': 'SENIORITY',
                    'amount': payslip.seniority_amount,
                    'category_id': self.env.ref('hr_payroll.ALW').id,
                })
            
            # Allowances from contract
            if payslip.contract_id.representation_allowance > 0:
                lines.append({
                    'name': 'Indemnité de Représentation',
                    'code': 'REP_ALW',
                    'amount': payslip.contract_id.representation_allowance,
                    'category_id': self.env.ref('hr_payroll.ALW').id,
                })
            
            if payslip.contract_id.transport_allowance > 0:
                lines.append({
                    'name': 'Indemnité de Transport',
                    'code': 'TRANS_ALW',
                    'amount': payslip.contract_id.transport_allowance,
                    'category_id': self.env.ref('hr_payroll.ALW').id,
                })
            
            if payslip.contract_id.meal_allowance > 0:
                lines.append({
                    'name': 'Indemnité de Repas',
                    'code': 'MEAL_ALW',
                    'amount': payslip.contract_id.meal_allowance,
                    'category_id': self.env.ref('hr_payroll.ALW').id,
                })
            
            # Gross salary
            lines.append({
                'name': 'Salaire Brut Imposable',
                'code': 'SBI',
                'amount': payslip.contract_id.gross_salary,
                'category_id': self.env.ref('hr_payroll.GROSS').id,
            })
            
            # CNSS
            lines.append({
                'name': 'CNSS',
                'code': 'CNSS',
                'amount': -payslip.cnss_employee,
                'category_id': self.env.ref('hr_payroll.DED').id,
            })
            
            # AMO
            lines.append({
                'name': 'AMO',
                'code': 'AMO',
                'amount': -payslip.amo_employee,
                'category_id': self.env.ref('hr_payroll.DED').id,
            })
            
            # Professional expenses
            lines.append({
                'name': 'Frais Professionnels',
                'code': 'PROF_EXP',
                'amount': -payslip.prof_exp_amount,
                'category_id': self.env.ref('hr_payroll.DED').id,
            })
            
            # IR
            lines.append({
                'name': 'IR',
                'code': 'IR',
                'amount': -payslip.ir_amount,
                'category_id': self.env.ref('hr_payroll.DED').id,
            })
            
            # Net salary
            lines.append({
                'name': 'Net à Payer',
                'code': 'NET',
                'amount': payslip.net_salary,
                'category_id': self.env.ref('hr_payroll.NET').id,
            })
            
            payslip.line_ids = [(5, 0, 0)] + [(0, 0, line) for line in lines]
        
        return super(HrPayslip, self).compute_sheet()
    
    def _compute_worked_days(self, employee, date_from, date_to):
        """Compute worked days for the payslip"""
        # For simplicity, we'll assume 26 working days per month
        return [(0, 0, {
            'name': 'Jours Travaillés',
            'code': 'WORK100',
            'number_of_days': 26,
            'contract_id': employee.contract_id.id,
        })]
