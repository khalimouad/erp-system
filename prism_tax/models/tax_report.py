# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TaxReport(models.Model):
    _name = 'tax.report'
    _description = 'Tax Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    tax_type_id = fields.Many2one('tax.type', string='Tax Type', required=True, ondelete='restrict')
    
    date = fields.Date(string='Report Date', required=True, default=fields.Date.context_today)
    period_from = fields.Date(string='Period From', required=True)
    period_to = fields.Date(string='Period To', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('sent', 'Sent'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True)
    
    # Financial information
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)
    amount_taxable = fields.Monetary(string='Taxable Amount', compute='_compute_amounts', store=True)
    amount_tax = fields.Monetary(string='Tax Amount', compute='_compute_amounts', store=True)
    amount_total = fields.Monetary(string='Total Amount', compute='_compute_amounts', store=True)
    
    # Report configuration
    report_type = fields.Selection([
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('analysis', 'Analysis Report'),
    ], string='Report Type', required=True, default='summary')
    
    include_declarations = fields.Boolean(string='Include Declarations', default=True)
    include_exemptions = fields.Boolean(string='Include Exemptions', default=True)
    include_rates = fields.Boolean(string='Include Rates', default=True)
    
    # Report data
    declaration_ids = fields.Many2many('tax.declaration', string='Declarations')
    declaration_count = fields.Integer(string='Declaration Count', compute='_compute_declaration_count')
    
    # Report content
    report_content = fields.Html(string='Report Content')
    
    # Attachments
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    # Notes
    notes = fields.Text(string='Notes')
    
    # Moroccan specific fields
    is_moroccan_report = fields.Boolean(string='Is Moroccan Report', related='tax_type_id.is_moroccan_tax', store=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('tax.report') or 'New'
        return super(TaxReport, self).create(vals_list)
    
    @api.depends('declaration_ids.amount_taxable', 'declaration_ids.amount_tax')
    def _compute_amounts(self):
        for report in self:
            report.amount_taxable = sum(report.declaration_ids.mapped('amount_taxable'))
            report.amount_tax = sum(report.declaration_ids.mapped('amount_tax'))
            report.amount_total = report.amount_taxable + report.amount_tax
    
    @api.depends('declaration_ids')
    def _compute_declaration_count(self):
        for report in self:
            report.declaration_count = len(report.declaration_ids)
    
    @api.constrains('period_from', 'period_to')
    def _check_period(self):
        for report in self:
            if report.period_from > report.period_to:
                raise ValidationError(_('The start date must be earlier than the end date.'))
    
    def action_generate_report(self):
        self.ensure_one()
        
        # Find declarations for the period
        declarations = self.env['tax.declaration'].search([
            ('tax_type_id', '=', self.tax_type_id.id),
            ('company_id', '=', self.company_id.id),
            ('period_from', '>=', self.period_from),
            ('period_to', '<=', self.period_to),
            ('state', 'in', ['confirmed', 'submitted', 'paid']),
        ])
        
        self.declaration_ids = declarations
        
        # Generate report content based on report_type
        if self.report_type == 'summary':
            self._generate_summary_report()
        elif self.report_type == 'detailed':
            self._generate_detailed_report()
        elif self.report_type == 'analysis':
            self._generate_analysis_report()
        
        self.state = 'generated'
        return True
    
    def _generate_summary_report(self):
        """Generate a summary report"""
        content = f"""
        <h1>Tax Summary Report</h1>
        <p>Period: {self.period_from} to {self.period_to}</p>
        <p>Tax Type: {self.tax_type_id.name}</p>
        <p>Company: {self.company_id.name}</p>
        
        <h2>Summary</h2>
        <table class="table table-bordered">
            <tr>
                <th>Taxable Amount</th>
                <td>{self.amount_taxable}</td>
            </tr>
            <tr>
                <th>Tax Amount</th>
                <td>{self.amount_tax}</td>
            </tr>
            <tr>
                <th>Total Amount</th>
                <td>{self.amount_total}</td>
            </tr>
            <tr>
                <th>Number of Declarations</th>
                <td>{self.declaration_count}</td>
            </tr>
        </table>
        """
        
        self.report_content = content
    
    def _generate_detailed_report(self):
        """Generate a detailed report"""
        content = f"""
        <h1>Tax Detailed Report</h1>
        <p>Period: {self.period_from} to {self.period_to}</p>
        <p>Tax Type: {self.tax_type_id.name}</p>
        <p>Company: {self.company_id.name}</p>
        
        <h2>Summary</h2>
        <table class="table table-bordered">
            <tr>
                <th>Taxable Amount</th>
                <td>{self.amount_taxable}</td>
            </tr>
            <tr>
                <th>Tax Amount</th>
                <td>{self.amount_tax}</td>
            </tr>
            <tr>
                <th>Total Amount</th>
                <td>{self.amount_total}</td>
            </tr>
            <tr>
                <th>Number of Declarations</th>
                <td>{self.declaration_count}</td>
            </tr>
        </table>
        
        <h2>Declarations</h2>
        <table class="table table-bordered">
            <tr>
                <th>Reference</th>
                <th>Date</th>
                <th>Period</th>
                <th>Taxable Amount</th>
                <th>Tax Amount</th>
                <th>Total Amount</th>
                <th>Status</th>
            </tr>
        """
        
        for declaration in self.declaration_ids:
            content += f"""
            <tr>
                <td>{declaration.name}</td>
                <td>{declaration.date}</td>
                <td>{declaration.period_from} - {declaration.period_to}</td>
                <td>{declaration.amount_taxable}</td>
                <td>{declaration.amount_tax}</td>
                <td>{declaration.amount_total}</td>
                <td>{dict(self.env['tax.declaration']._fields['state'].selection).get(declaration.state)}</td>
            </tr>
            """
        
        content += """
        </table>
        """
        
        self.report_content = content
    
    def _generate_analysis_report(self):
        """Generate an analysis report"""
        content = f"""
        <h1>Tax Analysis Report</h1>
        <p>Period: {self.period_from} to {self.period_to}</p>
        <p>Tax Type: {self.tax_type_id.name}</p>
        <p>Company: {self.company_id.name}</p>
        
        <h2>Summary</h2>
        <table class="table table-bordered">
            <tr>
                <th>Taxable Amount</th>
                <td>{self.amount_taxable}</td>
            </tr>
            <tr>
                <th>Tax Amount</th>
                <td>{self.amount_tax}</td>
            </tr>
            <tr>
                <th>Total Amount</th>
                <td>{self.amount_total}</td>
            </tr>
            <tr>
                <th>Number of Declarations</th>
                <td>{self.declaration_count}</td>
            </tr>
        </table>
        
        <h2>Analysis by Tax Rate</h2>
        <table class="table table-bordered">
            <tr>
                <th>Tax Rate</th>
                <th>Taxable Amount</th>
                <th>Tax Amount</th>
                <th>Total Amount</th>
            </tr>
        """
        
        # Group by tax rate
        rate_data = {}
        for declaration in self.declaration_ids:
            for line in declaration.line_ids:
                rate = line.tax_rate_id
                if rate not in rate_data:
                    rate_data[rate] = {
                        'taxable': 0.0,
                        'tax': 0.0,
                        'total': 0.0,
                    }
                rate_data[rate]['taxable'] += line.amount_taxable
                rate_data[rate]['tax'] += line.amount_tax
                rate_data[rate]['total'] += line.amount_taxable + line.amount_tax
        
        for rate, data in rate_data.items():
            content += f"""
            <tr>
                <td>{rate.name}</td>
                <td>{data['taxable']}</td>
                <td>{data['tax']}</td>
                <td>{data['total']}</td>
            </tr>
            """
        
        content += """
        </table>
        """
        
        self.report_content = content
    
    def action_send_report(self):
        self.write({'state': 'sent'})
    
    def action_archive_report(self):
        self.write({'state': 'archived'})
    
    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
    
    def action_view_declarations(self):
        self.ensure_one()
        return {
            'name': _('Declarations'),
            'type': 'ir.actions.act_window',
            'res_model': 'tax.declaration',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.declaration_ids.ids)],
        }
