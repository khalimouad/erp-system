# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TaxType(models.Model):
    _name = 'tax.type'
    _description = 'Tax Type'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    description = fields.Text(string='Description')
    
    # Rates
    rate_ids = fields.One2many('tax.rate', 'tax_type_id', string='Rates')
    rate_count = fields.Integer(string='Rate Count', compute='_compute_rate_count')
    
    # Exemptions
    exemption_ids = fields.One2many('tax.exemption', 'tax_type_id', string='Exemptions')
    exemption_count = fields.Integer(string='Exemption Count', compute='_compute_exemption_count')
    
    # Declarations
    declaration_ids = fields.One2many('tax.declaration', 'tax_type_id', string='Declarations')
    declaration_count = fields.Integer(string='Declaration Count', compute='_compute_declaration_count')
    
    # Reports
    report_ids = fields.One2many('tax.report', 'tax_type_id', string='Reports')
    report_count = fields.Integer(string='Report Count', compute='_compute_report_count')
    
    # Moroccan specific fields
    is_moroccan_tax = fields.Boolean(string='Is Moroccan Tax', default=False)
    moroccan_tax_category = fields.Selection([
        ('tva', 'TVA'),
        ('is', 'IS'),
        ('ir', 'IR'),
        ('droits', 'Droits d\'Enregistrement'),
        ('timbre', 'Droits de Timbre'),
        ('taxe_professionnelle', 'Taxe Professionnelle'),
    ], string='Moroccan Tax Category')
    
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'The code must be unique per company!'),
    ]
    
    @api.depends('rate_ids')
    def _compute_rate_count(self):
        for tax_type in self:
            tax_type.rate_count = len(tax_type.rate_ids)
    
    @api.depends('exemption_ids')
    def _compute_exemption_count(self):
        for tax_type in self:
            tax_type.exemption_count = len(tax_type.exemption_ids)
    
    @api.depends('declaration_ids')
    def _compute_declaration_count(self):
        for tax_type in self:
            tax_type.declaration_count = len(tax_type.declaration_ids)
    
    @api.depends('report_ids')
    def _compute_report_count(self):
        for tax_type in self:
            tax_type.report_count = len(tax_type.report_ids)
    
    def name_get(self):
        result = []
        for tax_type in self:
            name = tax_type.name
            if tax_type.code:
                name = '[%s] %s' % (tax_type.code, name)
            result.append((tax_type.id, name))
        return result
    
    def action_view_rates(self):
        self.ensure_one()
        return {
            'name': _('Rates'),
            'type': 'ir.actions.act_window',
            'res_model': 'tax.rate',
            'view_mode': 'tree,form',
            'domain': [('tax_type_id', '=', self.id)],
            'context': {'default_tax_type_id': self.id},
        }
    
    def action_view_exemptions(self):
        self.ensure_one()
        return {
            'name': _('Exemptions'),
            'type': 'ir.actions.act_window',
            'res_model': 'tax.exemption',
            'view_mode': 'tree,form',
            'domain': [('tax_type_id', '=', self.id)],
            'context': {'default_tax_type_id': self.id},
        }
    
    def action_view_declarations(self):
        self.ensure_one()
        return {
            'name': _('Declarations'),
            'type': 'ir.actions.act_window',
            'res_model': 'tax.declaration',
            'view_mode': 'tree,form',
            'domain': [('tax_type_id', '=', self.id)],
            'context': {'default_tax_type_id': self.id},
        }
    
    def action_view_reports(self):
        self.ensure_one()
        return {
            'name': _('Reports'),
            'type': 'ir.actions.act_window',
            'res_model': 'tax.report',
            'view_mode': 'tree,form',
            'domain': [('tax_type_id', '=', self.id)],
            'context': {'default_tax_type_id': self.id},
        }
