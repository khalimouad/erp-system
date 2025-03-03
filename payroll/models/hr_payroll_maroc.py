# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class HrPayrollMaroc(models.Model):
    _name = 'hr.payroll.maroc'
    _description = 'Configuration de la Paie Maroc'
    
    name = fields.Char(string='Nom', required=True)
    date_from = fields.Date(string='Date de début', required=True)
    date_to = fields.Date(string='Date de fin', required=True)
    active = fields.Boolean(string='Actif', default=True)
    
    # SMIG/SMAG
    smig_horaire = fields.Float(string='SMIG Horaire', default=17.10)
    smig_mensuel = fields.Float(string='SMIG Mensuel', compute='_compute_smig_mensuel', store=True)
    smag_horaire = fields.Float(string='SMAG Horaire', default=93.01)
    smag_mensuel = fields.Float(string='SMAG Mensuel', compute='_compute_smag_mensuel', store=True)
    
    # CNSS
    cnss_employee_rate = fields.Float(string='Taux CNSS Salarié', default=4.48)
    cnss_employer_rate = fields.Float(string='Taux CNSS Employeur', default=8.98)
    cnss_af_employer_rate = fields.Float(string='Taux Allocations Familiales Employeur', default=6.40)
    cnss_fp_employer_rate = fields.Float(string='Taux Formation Pro Employeur', default=1.60)
    cnss_ceiling = fields.Float(string='Plafond CNSS', default=6000.00)
    
    # AMO
    amo_employee_rate = fields.Float(string='Taux AMO Salarié', default=2.26)
    amo_employer_rate = fields.Float(string='Taux AMO Employeur', default=2.26)
    amo_contribution_employer_rate = fields.Float(string='Taux Participation AMO Employeur', default=1.85)
    
    # Ancienneté
    anciennete_0_2_rate = fields.Float(string='Taux Ancienneté 0-2 ans', default=0.0)
    anciennete_2_5_rate = fields.Float(string='Taux Ancienneté 2-5 ans', default=5.0)
    anciennete_5_12_rate = fields.Float(string='Taux Ancienneté 5-12 ans', default=10.0)
    anciennete_12_20_rate = fields.Float(string='Taux Ancienneté 12-20 ans', default=15.0)
    anciennete_20_25_rate = fields.Float(string='Taux Ancienneté 20-25 ans', default=20.0)
    anciennete_25_plus_rate = fields.Float(string='Taux Ancienneté 25+ ans', default=25.0)
    
    # Frais Professionnels
    fp_rate_below_78000 = fields.Float(string='Taux FP si SBI ≤ 78000', default=35.0)
    fp_max_below_78000 = fields.Float(string='Max FP si SBI ≤ 78000', default=30000.0)
    fp_rate_above_78000 = fields.Float(string='Taux FP si SBI > 78000', default=25.0)
    fp_max_above_78000 = fields.Float(string='Max FP si SBI > 78000', default=35000.0)
    fp_monthly_ceiling = fields.Float(string='Plafond mensuel FP', default=2916.67)
    
    # IR - Barème mensuel
    ir_monthly_threshold_1 = fields.Float(string='Seuil IR mensuel 1', default=3333.00)
    ir_monthly_threshold_2 = fields.Float(string='Seuil IR mensuel 2', default=5000.00)
    ir_monthly_threshold_3 = fields.Float(string='Seuil IR mensuel 3', default=6667.00)
    ir_monthly_threshold_4 = fields.Float(string='Seuil IR mensuel 4', default=8333.00)
    ir_monthly_threshold_5 = fields.Float(string='Seuil IR mensuel 5', default=15000.00)
    
    ir_monthly_rate_1 = fields.Float(string='Taux IR mensuel 1', default=0.0)
    ir_monthly_rate_2 = fields.Float(string='Taux IR mensuel 2', default=10.0)
    ir_monthly_rate_3 = fields.Float(string='Taux IR mensuel 3', default=20.0)
    ir_monthly_rate_4 = fields.Float(string='Taux IR mensuel 4', default=30.0)
    ir_monthly_rate_5 = fields.Float(string='Taux IR mensuel 5', default=34.0)
    ir_monthly_rate_6 = fields.Float(string='Taux IR mensuel 6', default=37.0)
    
    ir_monthly_deduction_1 = fields.Float(string='Déduction IR mensuel 1', default=0.0)
    ir_monthly_deduction_2 = fields.Float(string='Déduction IR mensuel 2', default=333.33)
    ir_monthly_deduction_3 = fields.Float(string='Déduction IR mensuel 3', default=833.33)
    ir_monthly_deduction_4 = fields.Float(string='Déduction IR mensuel 4', default=1500.00)
    ir_monthly_deduction_5 = fields.Float(string='Déduction IR mensuel 5', default=1833.33)
    ir_monthly_deduction_6 = fields.Float(string='Déduction IR mensuel 6', default=2283.33)
    
    # Charges de famille
    family_allowance_deduction = fields.Float(string='Déduction IR par personne', default=41.67)
    
    # Heures supplémentaires
    overtime_rate_day_normal = fields.Float(string='Taux HS Jour (normal)', default=25.0)
    overtime_rate_night_normal = fields.Float(string='Taux HS Nuit (normal)', default=50.0)
    overtime_rate_day_holiday = fields.Float(string='Taux HS Jour (férié)', default=50.0)
    overtime_rate_night_holiday = fields.Float(string='Taux HS Nuit (férié)', default=100.0)
    
    @api.depends('smig_horaire')
    def _compute_smig_mensuel(self):
        for record in self:
            record.smig_mensuel = record.smig_horaire * 191
    
    @api.depends('smag_horaire')
    def _compute_smag_mensuel(self):
        for record in self:
            record.smag_mensuel = record.smag_horaire * 26

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    is_maroc_rule = fields.Boolean(string='Règle Marocaine')
    maroc_rule_type = fields.Selection([
        ('base', 'Salaire de Base'),
        ('prime_anciennete', 'Prime d\'Ancienneté'),
        ('salaire_brut_imposable', 'Salaire Brut Imposable'),
        ('cnss', 'CNSS'),
        ('amo', 'AMO'),
        ('frais_prof', 'Frais Professionnels'),
        ('ir', 'IR'),
        ('net', 'Net à Payer'),
    ], string='Type de Règle Marocaine')

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    matricule = fields.Char(string='Matricule', related='employee_id.matricule', store=True)
    
    def compute_sheet(self):
        for payslip in self:
            # Get employee data
            employee = payslip.employee_id
            date_from = payslip.date_from
            date_to = payslip.date_to
            
            # Calculate worked days
            worked_days = self._compute_worked_days(employee, date_from, date_to)
            payslip.worked_days_line_ids = worked_days
            
            # Calculate salaire de base
            base_salary = employee.contract_id.wage
            
            # Calculate ancienneté
            date_embauche = employee.date_embauche or employee.create_date.date()
            years_worked = relativedelta(date_from, date_embauche).years
            months_worked = relativedelta(date_from, date_embauche).months
            total_months = years_worked * 12 + months_worked
            
            anciennete_rate = 0
            config = self.env['hr.payroll.maroc'].search([], limit=1)
            
            if total_months < 24:  # 0-2 ans
                anciennete_rate = config.anciennete_0_2_rate
            elif total_months < 60:  # 2-5 ans
                anciennete_rate = config.anciennete_2_5_rate
            elif total_months < 144:  # 5-12 ans
                anciennete_rate = config.anciennete_5_12_rate
            elif total_months < 240:  # 12-20 ans
                anciennete_rate = config.anciennete_12_20_rate
            elif total_months < 300:  # 20-25 ans
                anciennete_rate = config.anciennete_20_25_rate
            else:  # 25+ ans
                anciennete_rate = config.anciennete_25_plus_rate
            
            anciennete_amount = base_salary * (anciennete_rate / 100)
            
            # Calculate SBI (Salaire Brut Imposable)
            sbi = base_salary + anciennete_amount
            
            # Calculate CNSS
            cnss_base = min(sbi, config.cnss_ceiling)
            cnss_amount = cnss_base * (config.cnss_employee_rate / 100)
            
            # Calculate AMO
            amo_amount = sbi * (config.amo_employee_rate / 100)
            
            # Calculate Frais Professionnels
            annual_sbi = sbi * 12
            fp_rate = config.fp_rate_below_78000 if annual_sbi <= 78000 else config.fp_rate_above_78000
            fp_max = config.fp_max_below_78000 if annual_sbi <= 78000 else config.fp_max_above_78000
            fp_amount = min(sbi * (fp_rate / 100), config.fp_monthly_ceiling)
            
            # Calculate IR
            net_before_ir = sbi - cnss_amount - amo_amount - fp_amount
            
            ir_amount = self._calculate_ir(net_before_ir, employee.children, employee.ir_family_situation, config)
            
            # Calculate Net à Payer
            net_a_payer = sbi - cnss_amount - amo_amount - ir_amount
            
            # Create lines
            lines = []
            lines.append({
                'code': 'BASE',
                'name': 'Salaire de Base',
                'amount': base_salary,
                'category_id': self.env.ref('hr_payroll.BASIC').id,
            })
            
            lines.append({
                'code': 'ANCIENNETE',
                'name': 'Prime d\'Ancienneté',
                'amount': anciennete_amount,
                'category_id': self.env.ref('hr_payroll.ALW').id,
            })
            
            lines.append({
                'code': 'SBI',
                'name': 'Salaire Brut Imposable',
                'amount': sbi,
                'category_id': self.env.ref('hr_payroll.GROSS').id,
            })
            
            lines.append({
                'code': 'CNSS',
                'name': 'CNSS',
                'amount': -cnss_amount,
                'category_id': self.env.ref('hr_payroll.DED').id,
            })
            
            lines.append({
                'code': 'AMO',
                'name': 'AMO',
                'amount': -amo_amount,
                'category_id': self.env.ref('hr_payroll.DED').id,
            })
            
            lines.append({
                'code': 'FRAIS_PROF',
                'name': 'Frais Professionnels',
                'amount': -fp_amount,
                'category_id': self.env.ref('hr_payroll.DED').id,
            })
            
            lines.append({
                'code': 'IR',
                'name': 'IR',
                'amount': -ir_amount,
                'category_id': self.env.ref('hr_payroll.DED').id,
            })
            
            lines.append({
                'code': 'NET',
                'name': 'Net à Payer',
                'amount': net_a_payer,
                'category_id': self.env.ref('hr_payroll.NET').id,
            })
            
            payslip.line_ids = lines
            
        return super(HrPayslip, self).compute_sheet()
    
    def _compute_worked_days(self, employee, date_from, date_to):
        # This method should be implemented to calculate worked days
        # For simplicity, we'll assume 26 working days per month
        return [(0, 0, {
            'name': 'Jours Travaillés',
            'code': 'WORK100',
            'number_of_days': 26,
            'contract_id': employee.contract_id.id,
        })]
    
    def _calculate_ir(self, net_before_ir, children, family_situation, config):
        # Apply family charges deduction
        children_deduction = min(children, 6) * config.family_allowance_deduction
        net_after_children = net_before_ir - children_deduction
        
        # Apply IR barème
        ir_amount = 0
        
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
        
        return max(ir_amount, 0)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    matricule = fields.Char(string='Matricule')
    cin = fields.Char(string='CIN')
    cnss_num = fields.Char(string='N° CNSS')
    date_embauche = fields.Date(string='Date d\'embauche')
    ir_family_situation = fields.Selection([
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié(e)'),
        ('divorce', 'Divorcé(e)'),
    ], string='Situation Familiale IR', default='celibataire')
    children = fields.Integer(string='Nombre d\'enfants', default=0)

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    frais_representation = fields.Float(string='Indemnité de représentation', default=0.0)
    prime_transport = fields.Float(string='Prime de transport', default=0.0)
    prime_panier = fields.Float(string='Prime de panier', default=0.0)
