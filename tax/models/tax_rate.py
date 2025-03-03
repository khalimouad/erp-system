# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TaxRate(models.Model):
    _name = 'tax.rate'
    _description = 'Tax Rate'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    tax_type_id = fields.Many2one('tax.type', string='Tax Type', required=True, ondelete='restrict')
    
    rate = fields.Float(string='Rate (%)', required=True)
    amount_type = fields.Selection([
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Amount Type', required=True, default='percent')
    
    description = fields.Text(string='Description')
    
    date_from = fields.Date(string='Valid From')
    date_to = fields.Date(string='Valid To')
    
    # Moroccan specific fields
    is_moroccan_rate = fields.Boolean(string='Is Moroccan Rate', related='tax_type_id.is_moroccan_tax', store=True)
    moroccan_rate_category = fields.Selection([
        ('standard', 'Standard'),
        ('reduced', 'Reduced'),
        ('super_reduced', 'Super Reduced'),
        ('zero', 'Zero'),
        ('exempt', 'Exempt'),
    ], string='Moroccan Rate Category')
    
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'The code must be unique per company!'),
    ]
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rate in self:
            if rate.date_from and rate.date_to and rate.date_from > rate.date_to:
                raise ValidationError(_('The start date must be earlier than the end date.'))
    
    @api.constrains('rate', 'amount_type')
    def _check_rate(self):
        for rate in self:
            if rate.amount_type == 'percent' and (rate.rate < 0 or rate.rate > 100):
                raise ValidationError(_('The rate for a percentage amount type must be between 0 and 100.'))
            elif rate.amount_type == 'fixed' and rate.rate < 0:
                raise ValidationError(_('The rate for a fixed amount type must be positive.'))
    
    def name_get(self):
        result = []
        for rate in self:
            name = rate.name
            if rate.code:
                name = '[%s] %s' % (rate.code, name)
            if rate.amount_type == 'percent':
                name = '%s (%.2f%%)' % (name, rate.rate)
            else:
                name = '%s (%.2f)' % (name, rate.rate)
            result.append((rate.id, name))
        return result
    
    @api.model
    def get_rate_at_date(self, tax_type_code, rate_code, date=None):
        """Get the rate valid at a specific date"""
        if not date:
            date = fields.Date.context_today(self)
        
        domain = [
            ('tax_type_id.code', '=', tax_type_code),
            ('code', '=', rate_code),
            '|', ('date_from', '=', False), ('date_from', '<=', date),
            '|', ('date_to', '=', False), ('date_to', '>=', date),
        ]
        
        rate = self.search(domain, limit=1)
        return rate
