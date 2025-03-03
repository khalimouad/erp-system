# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # User Management Settings
    module_user = fields.Boolean(string='User Management', 
                                help='Enable user management with roles and approval workflows')
    
    # Security Settings
    user_password_expiry_days = fields.Integer(string='Password Expiry Days', 
                                             help='Number of days after which passwords expire (0 for no expiry)')
    user_max_login_attempts = fields.Integer(string='Maximum Login Attempts', 
                                           help='Maximum number of failed login attempts before account is locked (0 for no limit)')
    user_require_password_complexity = fields.Boolean(string='Require Password Complexity', 
                                                    help='Require complex passwords with minimum length, special characters, etc.')
    user_session_timeout_minutes = fields.Integer(string='Session Timeout (Minutes)', 
                                                help='Number of minutes of inactivity before a user session expires (0 for no timeout)')
    
    # Approval Settings
    user_role_approval_required = fields.Boolean(string='Role Approval Required', 
                                               help='Require approval for all role assignments')
    user_role_approval_admin_only = fields.Boolean(string='Admin-Only Role Approval', 
                                                 help='Only administrators can approve role assignments')
    
    # Moroccan-Specific Settings
    user_require_cin = fields.Boolean(string='Require CIN', 
                                     help='Require Moroccan National Identity Card Number (CIN) for all users')
    user_validate_cin = fields.Boolean(string='Validate CIN Format', 
                                      help='Validate the format of Moroccan CIN numbers')
    
    # Audit Settings
    user_activity_logging = fields.Boolean(string='User Activity Logging', 
                                         help='Log all user activities for audit purposes')
    user_login_logging = fields.Boolean(string='Login Attempt Logging', 
                                      help='Log all login attempts, successful or failed')
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        
        # Get values from system parameters
        res.update(
            user_password_expiry_days=int(params.get_param('prism_user.password_expiry_days', '90')),
            user_max_login_attempts=int(params.get_param('prism_user.max_login_attempts', '5')),
            user_require_password_complexity=params.get_param('prism_user.require_password_complexity', 'True') == 'True',
            user_session_timeout_minutes=int(params.get_param('prism_user.session_timeout_minutes', '60')),
            user_role_approval_required=params.get_param('prism_user.role_approval_required', 'True') == 'True',
            user_role_approval_admin_only=params.get_param('prism_user.role_approval_admin_only', 'True') == 'True',
            user_require_cin=params.get_param('prism_user.require_cin', 'True') == 'True',
            user_validate_cin=params.get_param('prism_user.validate_cin', 'True') == 'True',
            user_activity_logging=params.get_param('prism_user.activity_logging', 'True') == 'True',
            user_login_logging=params.get_param('prism_user.login_logging', 'True') == 'True',
        )
        return res
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        
        # Set values in system parameters
        params.set_param('prism_user.password_expiry_days', str(self.user_password_expiry_days))
        params.set_param('prism_user.max_login_attempts', str(self.user_max_login_attempts))
        params.set_param('prism_user.require_password_complexity', str(self.user_require_password_complexity))
        params.set_param('prism_user.session_timeout_minutes', str(self.user_session_timeout_minutes))
        params.set_param('prism_user.role_approval_required', str(self.user_role_approval_required))
        params.set_param('prism_user.role_approval_admin_only', str(self.user_role_approval_admin_only))
        params.set_param('prism_user.require_cin', str(self.user_require_cin))
        params.set_param('prism_user.validate_cin', str(self.user_validate_cin))
        params.set_param('prism_user.activity_logging', str(self.user_activity_logging))
        params.set_param('prism_user.login_logging', str(self.user_login_logging))
