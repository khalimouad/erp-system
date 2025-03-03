# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class UserApproval(models.Model):
    _name = 'user.approval'
    _description = 'User Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, 
                      default=lambda self: _('New'))
    user_id = fields.Many2one('res.users', string='User', required=True, 
                             tracking=True, readonly=True, 
                             states={'draft': [('readonly', False)]})
    role_id = fields.Many2one('user.role', string='Role', required=True, 
                             tracking=True, readonly=True,
                             states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled')
    ], string='Status', default='draft', tracking=True)
    
    # Approval information
    approver_ids = fields.Many2many('res.users', string='Approvers', 
                                   compute='_compute_approvers', store=True)
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True)
    rejected_by_id = fields.Many2one('res.users', string='Rejected By', readonly=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)
    rejection_date = fields.Datetime(string='Rejection Date', readonly=True)
    
    # Additional information
    notes = fields.Text(string='Notes', tracking=True)
    reason = fields.Text(string='Reason for Request', tracking=True, 
                        readonly=True, states={'draft': [('readonly', False)]})
    
    @api.depends('role_id')
    def _compute_approvers(self):
        for approval in self:
            if approval.role_id:
                approval.approver_ids = approval.role_id.approval_user_ids
            else:
                approval.approver_ids = False
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('user.approval') or _('New')
        return super(UserApproval, self).create(vals)
    
    def action_submit(self):
        self.ensure_one()
        if not self.approver_ids:
            raise UserError(_('No approvers defined for this role. Please contact your administrator.'))
        self.write({'state': 'submitted'})
        # Send notification to approvers
        self.message_subscribe(partner_ids=self.approver_ids.mapped('partner_id').ids)
        message = _('Approval request %s has been submitted by %s.') % (self.name, self.env.user.name)
        self.message_post(body=message, subtype_xmlid='mail.mt_comment')
        return True
    
    def action_approve(self):
        self.ensure_one()
        if self.env.user not in self.approver_ids:
            raise UserError(_('You are not authorized to approve this request.'))
        
        # Assign role to user
        if self.role_id and self.user_id:
            self.role_id.write({'user_ids': [(4, self.user_id.id)]})
            
            # Add user to associated groups
            if self.role_id.group_ids:
                for group in self.role_id.group_ids:
                    group.write({'users': [(4, self.user_id.id)]})
        
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        
        message = _('Approval request has been approved by %s.') % self.env.user.name
        self.message_post(body=message, subtype_xmlid='mail.mt_comment')
        return True
    
    def action_reject(self):
        self.ensure_one()
        if self.env.user not in self.approver_ids:
            raise UserError(_('You are not authorized to reject this request.'))
        
        self.write({
            'state': 'rejected',
            'rejected_by_id': self.env.user.id,
            'rejection_date': fields.Datetime.now(),
        })
        
        message = _('Approval request has been rejected by %s.') % self.env.user.name
        self.message_post(body=message, subtype_xmlid='mail.mt_comment')
        return True
    
    def action_cancel(self):
        self.ensure_one()
        if self.state in ['approved', 'rejected']:
            raise UserError(_('Cannot cancel an already processed approval.'))
        
        self.write({'state': 'canceled'})
        message = _('Approval request has been canceled.')
        self.message_post(body=message, subtype_xmlid='mail.mt_comment')
        return True
    
    def action_reset_to_draft(self):
        self.ensure_one()
        if self.state in ['approved']:
            raise UserError(_('Cannot reset an approved request. Create a new request instead.'))
        
        self.write({'state': 'draft'})
        message = _('Approval request has been reset to draft.')
        self.message_post(body=message, subtype_xmlid='mail.mt_comment')
        return True
