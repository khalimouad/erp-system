# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    # Roles
    role_ids = fields.Many2many('user.role', 'user_role_users_rel', string='Roles')
    
    # Moroccan-specific fields
    cin = fields.Char(string='CIN', help='Moroccan National Identity Card Number')
    moroccan_address = fields.Text(string='Moroccan Address')
    
    # Approval status
    approval_ids = fields.One2many('user.approval', 'user_id', string='Approval Requests')
    pending_approval_count = fields.Integer(compute='_compute_approval_counts', string='Pending Approvals')
    approved_count = fields.Integer(compute='_compute_approval_counts', string='Approved Roles')
    rejected_count = fields.Integer(compute='_compute_approval_counts', string='Rejected Requests')
    
    # Security fields
    last_password_reset = fields.Datetime(string='Last Password Reset')
    password_expiry_date = fields.Datetime(string='Password Expiry Date')
    require_password_change = fields.Boolean(string='Require Password Change', default=False)
    login_attempts = fields.Integer(string='Failed Login Attempts', default=0)
    account_locked = fields.Boolean(string='Account Locked', default=False)
    
    # Activity tracking
    last_activity = fields.Datetime(string='Last Activity')
    
    @api.depends('approval_ids', 'approval_ids.state')
    def _compute_approval_counts(self):
        for user in self:
            user.pending_approval_count = self.env['user.approval'].search_count([
                ('user_id', '=', user.id),
                ('state', 'in', ['draft', 'submitted'])
            ])
            user.approved_count = self.env['user.approval'].search_count([
                ('user_id', '=', user.id),
                ('state', '=', 'approved')
            ])
            user.rejected_count = self.env['user.approval'].search_count([
                ('user_id', '=', user.id),
                ('state', '=', 'rejected')
            ])
    
    def action_view_approvals(self):
        self.ensure_one()
        action = self.env.ref('user.action_user_approval').read()[0]
        action['domain'] = [('user_id', '=', self.id)]
        action['context'] = {'default_user_id': self.id}
        return action
    
    def action_request_role(self):
        self.ensure_one()
        return {
            'name': _('Request Role'),
            'type': 'ir.actions.act_window',
            'res_model': 'user.approval',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_user_id': self.id},
        }
    
    @api.constrains('cin')
    def _check_cin_format(self):
        for user in self:
            if user.cin and not self._is_valid_cin(user.cin):
                raise ValidationError(_('Invalid CIN format. CIN must be in the format: XX123456'))
    
    def _is_valid_cin(self, cin):
        """Validate Moroccan CIN format"""
        if not cin:
            return True
        
        # Basic validation - can be enhanced with more specific rules
        if len(cin) != 8:
            return False
        
        # First two characters should be letters, rest should be digits
        if not (cin[:2].isalpha() and cin[2:].isdigit()):
            return False
            
        return True
    
    def reset_password(self):
        self.ensure_one()
        # Logic to reset password
        self.write({
            'last_password_reset': fields.Datetime.now(),
            'require_password_change': True,
            'login_attempts': 0,
            'account_locked': False,
        })
        return True
    
    def lock_account(self):
        self.ensure_one()
        self.write({'account_locked': True})
        return True
    
    def unlock_account(self):
        self.ensure_one()
        self.write({
            'account_locked': False,
            'login_attempts': 0,
        })
        return True
