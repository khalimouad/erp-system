# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    # Moroccan-specific fields
    matricule = fields.Char(string='Employee ID', help="Internal identification number for the employee")
    cin = fields.Char(string='CIN', help="National Identity Card number")
    cnss_num = fields.Char(string='CNSS Number', help="Social Security number")
    date_embauche = fields.Date(string='Hiring Date')
    
    # Family situation for IR calculation
    ir_family_situation = fields.Selection([
        ('celibataire', 'Single'),
        ('marie', 'Married'),
        ('divorce', 'Divorced'),
        ('veuf', 'Widowed')
    ], string='Family Situation', default='celibataire')
    children = fields.Integer(string='Number of Children', default=0)
    
    # Banking information
    bank_account_number = fields.Char(string='Bank Account Number')
    bank_name = fields.Char(string='Bank Name')
    
    # Social security information
    cnss_affiliation_date = fields.Date(string='CNSS Affiliation Date')
    amo_affiliation_date = fields.Date(string='AMO Affiliation Date')
    
    # Tax information
    tax_id = fields.Char(string='Tax ID')
    tax_office = fields.Char(string='Tax Office')
    
    # Work permit (for foreigners)
    work_permit_number = fields.Char(string='Work Permit Number')
    work_permit_expiry_date = fields.Date(string='Work Permit Expiry Date')
    
    # Education and classification
    education_level = fields.Selection([
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('doctorate', 'Doctorate'),
        ('other', 'Other')
    ], string='Education Level')
    
    job_classification = fields.Selection([
        ('worker', 'Worker'),
        ('employee', 'Employee'),
        ('technician', 'Technician'),
        ('supervisor', 'Supervisor'),
        ('manager', 'Manager'),
        ('executive', 'Executive')
    ], string='Job Classification')
    
    # Compute methods
    @api.depends('contract_ids.date_start')
    def _compute_seniority(self):
        """Compute employee seniority in years"""
        for employee in self:
            if not employee.date_embauche:
                # Try to get date from first contract
                contracts = employee.contract_ids.sorted('date_start')
                if contracts:
                    employee.date_embauche = contracts[0].date_start
    
    # Override create to set matricule if not provided
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('matricule'):
                vals['matricule'] = self.env['ir.sequence'].next_by_code('hr.employee.matricule')
        return super(HrEmployee, self).create(vals_list)
