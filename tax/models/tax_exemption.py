# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TaxExemption(models.Model):
    _name = 'tax.exemption'
    _description = 'Tax Exemption'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    tax_type_id = fields.Many2one('tax.type', string='Tax Type', required=True, ondelete='restrict')
    
    description = fields.Text(string='Description')
    legal_reference = fields.Text(string='Legal Reference')
    
    date_from = fields.Date(string='Valid From')
    date_to = fields.Date(string='Valid To')
    
    # Moroccan specific fields
    is_moroccan_exemption = fields.Boolean(string='Is Moroccan Exemption', related='tax_type_id.is_moroccan_tax', store=True)
    moroccan_exemption_category = fields.Selection([
        ('export', 'Export'),
        ('agriculture', 'Agriculture'),
        ('investment', 'Investment'),
        ('social', 'Social'),
        ('other', 'Other'),
    ], string='Moroccan Exemption Category')
    
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'The code must be unique per company!'),
    ]
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for exemption in self:
            if exemption.date_from and exemption.date_to and exemption.date_from > exemption.date_to:
                raise ValidationError(_('The start date must be earlier than the end date.'))
    
    def name_get(self):
        result = []
        for exemption in self:
            name = exemption.name
            if exemption.code:
                name = '[%s] %s' % (exemption.code, name)
            result.append((exemption.id, name))
        return result
