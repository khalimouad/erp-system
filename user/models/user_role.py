# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class UserRole(models.Model):
    _name = 'user.role'
    _description = 'User Role'
    _order = 'sequence, name'

    name = fields.Char(string='Role Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(string='Active', default=True)
    
    # Permissions
    group_ids = fields.Many2many('res.groups', string='Associated Groups')
    
    # Moroccan-specific fields
    is_moroccan_specific = fields.Boolean(string='Moroccan-Specific Role')
    requires_approval = fields.Boolean(string='Requires Approval', 
                                      help='If checked, users assigned to this role will require approval')
    approval_user_ids = fields.Many2many('res.users', 'user_role_approver_rel', 
                                        string='Approvers',
                                        help='Users who can approve this role assignment')
    
    # Constraints
    max_users = fields.Integer(string='Maximum Users', 
                              help='Maximum number of users that can have this role (0 for unlimited)')
    
    # Relationships
    user_ids = fields.Many2many('res.users', 'user_role_users_rel', string='Users')
    user_count = fields.Integer(compute='_compute_user_count', string='User Count')
    
    @api.depends('user_ids')
    def _compute_user_count(self):
        for role in self:
            role.user_count = len(role.user_ids)
    
    @api.constrains('user_ids', 'max_users')
    def _check_max_users(self):
        for role in self:
            if role.max_users > 0 and len(role.user_ids) > role.max_users:
                raise ValidationError(_(
                    'Maximum number of users allowed for role "%s" is %s.') % 
                    (role.name, role.max_users))
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Role code must be unique!'),
    ]
