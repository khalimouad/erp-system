from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Partner Type Selection
    is_customer = fields.Boolean(string="Is a Customer", default=False)
    is_vendor = fields.Boolean(string="Is a Vendor", default=False)
    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('both', 'Customer and Vendor')
    ], string="Partner Type", compute='_compute_partner_type', store=True, readonly=False)
    
    # Moroccan-specific fields
    ice_number = fields.Char(string="ICE Number", help="Tax ID")
    rc_number = fields.Char(string="RC Number", help="Trade Register Number")
    cnss_number = fields.Char(string="CNSS Number", help="Social Security Number")
    
    # Additional contact information
    contact_person = fields.Char(string="Contact Person")
    job_title = fields.Char(string="Job Title")
    department = fields.Char(string="Department")
    
    # Payment and credit information
    payment_terms = fields.Selection([
        ('immediate', 'Immediate Payment'),
        ('15days', '15 Days'),
        ('30days', '30 Days'),
        ('45days', '45 Days'),
        ('60days', '60 Days'),
        ('90days', '90 Days'),
        ('end_month', 'End of Month'),
        ('end_month_15days', 'End of Month + 15 Days'),
        ('end_month_30days', 'End of Month + 30 Days'),
        ('custom', 'Custom')
    ], string="Payment Terms", default='30days')
    custom_payment_terms = fields.Char(string="Custom Payment Terms")
    credit_limit = fields.Float(string="Credit Limit")
    
    # Classification fields
    partner_category = fields.Selection([
        ('a', 'A - Premium'),
        ('b', 'B - Standard'),
        ('c', 'C - Basic')
    ], string="Partner Category", default='b')
    
    # Due invoices information
    due_invoice_count = fields.Integer(string="Due Invoices", compute='_compute_due_invoice_count')
    due_invoice_amount = fields.Monetary(string="Due Amount", compute='_compute_due_invoice_amount', currency_field='currency_id')
    overdue_invoice_count = fields.Integer(string="Overdue Invoices", compute='_compute_overdue_invoice_count')
    overdue_invoice_amount = fields.Monetary(string="Overdue Amount", compute='_compute_overdue_invoice_amount', currency_field='currency_id')
    
    # Bank information
    bank_name = fields.Char(string="Bank Name")
    bank_account_number = fields.Char(string="Bank Account Number")
    bank_swift = fields.Char(string="SWIFT Code")
    
    # Additional fields
    is_active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Notes")
    
    @api.depends('is_customer', 'is_vendor')
    def _compute_partner_type(self):
        for partner in self:
            if partner.is_customer and partner.is_vendor:
                partner.partner_type = 'both'
            elif partner.is_customer:
                partner.partner_type = 'customer'
            elif partner.is_vendor:
                partner.partner_type = 'vendor'
            else:
                partner.partner_type = False
    
    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        for partner in self:
            if partner.partner_type == 'customer':
                partner.is_customer = True
                partner.is_vendor = False
            elif partner.partner_type == 'vendor':
                partner.is_customer = False
                partner.is_vendor = True
            elif partner.partner_type == 'both':
                partner.is_customer = True
                partner.is_vendor = True
            else:
                partner.is_customer = False
                partner.is_vendor = False
    
    def _compute_due_invoice_count(self):
        for partner in self:
            partner.due_invoice_count = self.env['account.move'].search_count([
                ('partner_id', '=', partner.id),
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('payment_state', 'not in', ['paid', 'reversed']),
                ('state', '=', 'posted')
            ])
    
    def _compute_due_invoice_amount(self):
        for partner in self:
            invoices = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('payment_state', 'not in', ['paid', 'reversed']),
                ('state', '=', 'posted')
            ])
            partner.due_invoice_amount = sum(invoices.mapped('amount_residual'))
    
    def _compute_overdue_invoice_count(self):
        today = fields.Date.today()
        for partner in self:
            partner.overdue_invoice_count = self.env['account.move'].search_count([
                ('partner_id', '=', partner.id),
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('payment_state', 'not in', ['paid', 'reversed']),
                ('state', '=', 'posted'),
                ('invoice_date_due', '<', today)
            ])
    
    def _compute_overdue_invoice_amount(self):
        today = fields.Date.today()
        for partner in self:
            invoices = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('payment_state', 'not in', ['paid', 'reversed']),
                ('state', '=', 'posted'),
                ('invoice_date_due', '<', today)
            ])
            partner.overdue_invoice_amount = sum(invoices.mapped('amount_residual'))
    
    @api.constrains('ice_number')
    def _check_ice_number(self):
        for partner in self:
            if partner.ice_number:
                # ICE number should be 15 digits
                if not partner.ice_number.isdigit() or len(partner.ice_number) != 15:
                    raise ValidationError(_("ICE Number must be exactly 15 digits."))
                
                # Check if ICE number is unique
                same_ice = self.search([
                    ('ice_number', '=', partner.ice_number),
                    ('id', '!=', partner.id)
                ])
                if same_ice:
                    raise ValidationError(_("ICE Number must be unique. It is already used by %s.") % same_ice[0].name)
    
    def action_view_due_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [
            ('partner_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'in_invoice']),
            ('payment_state', 'not in', ['paid', 'reversed']),
            ('state', '=', 'posted')
        ]
        action['context'] = {'default_partner_id': self.id}
        return action
    
    def action_view_overdue_invoices(self):
        self.ensure_one()
        today = fields.Date.today()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [
            ('partner_id', '=', self.id),
            ('move_type', 'in', ['out_invoice', 'in_invoice']),
            ('payment_state', 'not in', ['paid', 'reversed']),
            ('state', '=', 'posted'),
            ('invoice_date_due', '<', today)
        ]
        action['context'] = {'default_partner_id': self.id}
        return action
