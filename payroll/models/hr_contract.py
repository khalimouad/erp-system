# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    # Moroccan-specific fields
    representation_allowance = fields.Float(string='Representation Allowance', default=0.0,
                                           help="Monthly allowance for representation expenses")
    transport_allowance = fields.Float(string='Transport Allowance', default=0.0,
                                      help="Monthly allowance for transportation")
    meal_allowance = fields.Float(string='Meal Allowance', default=0.0,
                                 help="Monthly allowance for meals")
    
    # Housing benefits
    housing_allowance = fields.Float(string='Housing Allowance', default=0.0)
    housing_advantage = fields.Float(string='Housing Advantage', default=0.0,
                                    help="Value of company-provided housing")
    
    # Family benefits
    family_allowance = fields.Float(string='Family Allowance', default=0.0)
    
    # Professional expenses
    professional_expenses = fields.Float(string='Professional Expenses', default=0.0)
    
    # Overtime
    overtime_allowance = fields.Float(string='Overtime Allowance', default=0.0)
    
    # Bonuses
    annual_bonus = fields.Float(string='Annual Bonus', default=0.0,
                               help="Annual bonus amount (13th month, etc.)")
    performance_bonus = fields.Float(string='Performance Bonus', default=0.0)
    
    # Deductions
    mutual_insurance = fields.Float(string='Mutual Insurance', default=0.0,
                                   help="Employee contribution to mutual insurance")
    complementary_retirement = fields.Float(string='Complementary Retirement', default=0.0,
                                          help="Employee contribution to complementary retirement plan")
    
    # Contract type details
    is_fixed_term = fields.Boolean(string='Fixed Term Contract', default=False)
    trial_period_duration = fields.Integer(string='Trial Period (days)', default=90)
    notice_period = fields.Integer(string='Notice Period (days)', default=30)
    
    # Working time
    weekly_hours = fields.Float(string='Weekly Working Hours', default=44.0)
    monthly_hours = fields.Float(string='Monthly Working Hours', compute='_compute_monthly_hours', store=True)
    
    # Salary structure
    moroccan_salary_structure_id = fields.Many2one('hr.payroll.structure', string='Moroccan Salary Structure',
                                                 domain=[('country_id.code', '=', 'MA')])
    
    # Computed fields
    gross_salary = fields.Float(string='Gross Salary', compute='_compute_gross_salary', store=True)
    
    @api.depends('weekly_hours')
    def _compute_monthly_hours(self):
        for contract in self:
            contract.monthly_hours = contract.weekly_hours * 52 / 12
    
    @api.depends('wage', 'representation_allowance', 'transport_allowance', 'meal_allowance', 
                'housing_allowance', 'family_allowance', 'professional_expenses', 'overtime_allowance')
    def _compute_gross_salary(self):
        for contract in self:
            contract.gross_salary = (
                contract.wage +
                contract.representation_allowance +
                contract.transport_allowance +
                contract.meal_allowance +
                contract.housing_allowance +
                contract.family_allowance +
                contract.professional_expenses +
                contract.overtime_allowance
            )
