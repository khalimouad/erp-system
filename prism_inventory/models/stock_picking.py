from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    # Moroccan-specific fields
    picking_type_category = fields.Selection([
        ('standard', 'Standard'),
        ('customs', 'Customs'),
        ('quarantine', 'Quarantine'),
        ('return', 'Return'),
        ('destruction', 'Destruction')
    ], string="Picking Category", compute='_compute_picking_type_category',
       store=True, help="Category of picking according to Moroccan regulations")
    
    # Document references
    reference_number = fields.Char(string="Reference Number", 
                                  help="External reference number for this transfer")
    
    # Customs fields
    customs_document = fields.Char(string="Customs Document", 
                                  help="Customs document reference for international transfers")
    
    customs_date = fields.Date(string="Customs Date",
                             help="Date of customs clearance for international transfers")
    
    customs_officer_id = fields.Many2one('res.partner', string="Customs Officer",
                                       domain=[('is_company', '=', False)],
                                       help="Customs officer responsible for this transfer")
    
    # VAT related fields
    is_vat_exempt = fields.Boolean(string="VAT Exempt", default=False,
                                 help="Whether this transfer is exempt from VAT")
    
    vat_exemption_reason = fields.Selection([
        ('export', 'Export'),
        ('free_zone', 'Free Zone'),
        ('diplomatic', 'Diplomatic'),
        ('government', 'Government'),
        ('other', 'Other')
    ], string="VAT Exemption Reason")
    
    # Quality control
    quality_check_required = fields.Boolean(string="Quality Check Required", default=False)
    
    quality_state = fields.Selection([
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed')
    ], string="Quality State", default='pending')
    
    quality_check_date = fields.Date(string="Quality Check Date")
    
    quality_checked_by = fields.Many2one('res.users', string="Checked By")
    
    quality_notes = fields.Text(string="Quality Notes")
    
    # Approval workflow
    requires_approval = fields.Boolean(string="Requires Approval", compute='_compute_requires_approval',
                                     store=True, help="Whether this transfer requires manager approval")
    
    approval_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Approval Status", default='not_required')
    
    approved_by = fields.Many2one('res.users', string="Approved By")
    
    approval_date = fields.Datetime(string="Approval Date")
    
    # Transportation and delivery
    transport_mode = fields.Selection([
        ('road', 'Road'),
        ('sea', 'Sea'),
        ('air', 'Air'),
        ('rail', 'Rail'),
        ('multi', 'Multimodal')
    ], string="Transport Mode")
    
    carrier_id = fields.Many2one('res.partner', string="Carrier",
                               domain=[('is_company', '=', True)])
    
    vehicle_number = fields.Char(string="Vehicle Number")
    
    driver_id = fields.Many2one('res.partner', string="Driver",
                              domain=[('is_company', '=', False)])
    
    driver_phone = fields.Char(string="Driver Phone")
    
    # Additional tracking
    temperature_required = fields.Boolean(string="Temperature Control Required", default=False)
    
    temperature_min = fields.Float(string="Minimum Temperature (°C)")
    
    temperature_max = fields.Float(string="Maximum Temperature (°C)")
    
    actual_temperature = fields.Float(string="Actual Temperature (°C)")
    
    @api.depends('picking_type_id', 'location_id', 'location_dest_id')
    def _compute_picking_type_category(self):
        for picking in self:
            # Determine category based on locations and picking type
            if picking.picking_type_id.code == 'incoming' and picking.location_id.usage == 'supplier':
                # Check if destination is a customs or quarantine location
                if hasattr(picking.location_dest_id, 'location_type'):
                    if picking.location_dest_id.location_type == 'customs':
                        picking.picking_type_category = 'customs'
                    elif picking.location_dest_id.location_type == 'quarantine':
                        picking.picking_type_category = 'quarantine'
                    else:
                        picking.picking_type_category = 'standard'
                else:
                    picking.picking_type_category = 'standard'
            elif picking.picking_type_id.code == 'outgoing' and picking.location_dest_id.usage == 'customer':
                picking.picking_type_category = 'standard'
            elif picking.picking_type_id.code == 'internal':
                # Check if source or destination is a special location
                if hasattr(picking.location_id, 'location_type') and picking.location_id.location_type == 'quarantine':
                    picking.picking_type_category = 'quarantine'
                elif hasattr(picking.location_dest_id, 'location_type') and picking.location_dest_id.location_type == 'quarantine':
                    picking.picking_type_category = 'quarantine'
                else:
                    picking.picking_type_category = 'standard'
            else:
                picking.picking_type_category = 'standard'
    
    @api.depends('picking_type_category', 'move_lines.product_id')
    def _compute_requires_approval(self):
        for picking in self:
            # Determine if approval is required
            if picking.picking_type_category in ['customs', 'quarantine']:
                picking.requires_approval = True
            elif picking.picking_type_id.code == 'outgoing' and any(move.product_id.categ_id.requires_approval for move in picking.move_lines if hasattr(move.product_id.categ_id, 'requires_approval')):
                picking.requires_approval = True
            else:
                picking.requires_approval = False
    
    @api.onchange('picking_type_category')
    def _onchange_picking_type_category(self):
        if self.picking_type_category == 'customs':
            self.quality_check_required = True
        elif self.picking_type_category == 'quarantine':
            self.quality_check_required = True
    
    @api.constrains('temperature_required', 'temperature_min', 'temperature_max')
    def _check_temperature_range(self):
        for picking in self:
            if picking.temperature_required:
                if not picking.temperature_min or not picking.temperature_max:
                    raise ValidationError(_("Temperature range must be specified when temperature control is required."))
                if picking.temperature_min >= picking.temperature_max:
                    raise ValidationError(_("Minimum temperature must be less than maximum temperature."))
    
    def action_confirm(self):
        # Check if approval is required but not yet approved
        for picking in self:
            if picking.requires_approval and picking.approval_state not in ['approved', 'not_required']:
                raise ValidationError(_("This transfer requires approval before confirmation."))
        
        return super(StockPicking, self).action_confirm()
    
    def action_request_approval(self):
        for picking in self:
            if picking.requires_approval:
                picking.approval_state = 'pending'
    
    def action_approve(self):
        self.ensure_one()
        self.approval_state = 'approved'
        self.approved_by = self.env.user
        self.approval_date = fields.Datetime.now()
    
    def action_reject(self):
        self.ensure_one()
        self.approval_state = 'rejected'
    
    def action_quality_pass(self):
        self.ensure_one()
        self.quality_state = 'passed'
        self.quality_check_date = fields.Date.today()
        self.quality_checked_by = self.env.user
    
    def action_quality_fail(self):
        self.ensure_one()
        self.quality_state = 'failed'
        self.quality_check_date = fields.Date.today()
        self.quality_checked_by = self.env.user
