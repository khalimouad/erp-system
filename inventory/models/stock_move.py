from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    # Moroccan-specific fields
    customs_status = fields.Selection([
        ('pending', 'Pending Customs'),
        ('cleared', 'Customs Cleared'),
        ('rejected', 'Customs Rejected'),
        ('not_applicable', 'Not Applicable')
    ], string="Customs Status", default='not_applicable',
       help="Status of customs clearance for this move")
    
    customs_document = fields.Char(string="Customs Document", 
                                  help="Customs document reference for this move")
    
    customs_date = fields.Date(string="Customs Date",
                             help="Date of customs clearance for this move")
    
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
    
    # Lot tracking
    requires_lot = fields.Boolean(string="Requires Lot", compute='_compute_requires_lot',
                                store=True, help="Whether this move requires lot tracking")
    
    # Additional tracking
    temperature_required = fields.Boolean(string="Temperature Control Required", default=False)
    
    temperature_min = fields.Float(string="Minimum Temperature (°C)")
    
    temperature_max = fields.Float(string="Maximum Temperature (°C)")
    
    actual_temperature = fields.Float(string="Actual Temperature (°C)")
    
    # Cost tracking
    customs_value = fields.Monetary(string="Customs Value", currency_field='company_currency_id')
    
    customs_duty = fields.Monetary(string="Customs Duty", currency_field='company_currency_id')
    
    import_vat = fields.Monetary(string="Import VAT", currency_field='company_currency_id')
    
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', 
                                        string="Company Currency", readonly=True)
    
    # Computed fields
    total_landed_cost = fields.Monetary(string="Total Landed Cost", currency_field='company_currency_id',
                                      compute='_compute_total_landed_cost', store=True)
    
    @api.depends('product_id', 'picking_id.picking_type_id')
    def _compute_requires_lot(self):
        for move in self:
            # Check if product requires lot tracking
            if move.product_id and move.product_id.tracking != 'none':
                move.requires_lot = True
            # Check if picking type requires lot tracking
            elif move.picking_id and move.picking_id.picking_type_id.use_create_lots:
                move.requires_lot = True
            # Check if destination location requires lot tracking
            elif move.location_dest_id and hasattr(move.location_dest_id, 'location_type') and move.location_dest_id.location_type in ['quarantine', 'temperature']:
                move.requires_lot = True
            else:
                move.requires_lot = False
    
    @api.depends('value', 'customs_value', 'customs_duty', 'import_vat')
    def _compute_total_landed_cost(self):
        for move in self:
            move.total_landed_cost = (move.value or 0.0) + (move.customs_value or 0.0) + (move.customs_duty or 0.0) + (move.import_vat or 0.0)
    
    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            # Inherit customs fields from picking
            self.customs_document = self.picking_id.customs_document
            self.customs_date = self.picking_id.customs_date
            
            # Inherit quality check requirement from picking
            self.quality_check_required = self.picking_id.quality_check_required
            
            # Inherit temperature control from picking
            self.temperature_required = self.picking_id.temperature_required
            self.temperature_min = self.picking_id.temperature_min
            self.temperature_max = self.picking_id.temperature_max
    
    @api.onchange('product_id')
    def _onchange_product_id_quality(self):
        if self.product_id:
            # Check if product requires quality check
            if hasattr(self.product_id, 'quality_check_required') and self.product_id.quality_check_required:
                self.quality_check_required = True
            
            # Check if product requires temperature control
            if hasattr(self.product_id, 'temperature_control_required') and self.product_id.temperature_control_required:
                self.temperature_required = True
                self.temperature_min = self.product_id.temperature_min if hasattr(self.product_id, 'temperature_min') else 0.0
                self.temperature_max = self.product_id.temperature_max if hasattr(self.product_id, 'temperature_max') else 0.0
    
    @api.constrains('temperature_required', 'temperature_min', 'temperature_max')
    def _check_temperature_range(self):
        for move in self:
            if move.temperature_required:
                if not move.temperature_min or not move.temperature_max:
                    raise ValidationError(_("Temperature range must be specified when temperature control is required."))
                if move.temperature_min >= move.temperature_max:
                    raise ValidationError(_("Minimum temperature must be less than maximum temperature."))
    
    def _action_done(self, cancel_backorder=False):
        # Check if quality check is required but not passed
        for move in self:
            if move.quality_check_required and move.quality_state != 'passed':
                raise ValidationError(_("Quality check must be passed before completing this move."))
        
        return super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
    
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
