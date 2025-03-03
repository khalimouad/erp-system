from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    # Moroccan-specific fields
    location_type_id = fields.Many2one('stock.location.type', string="Location Type",
                                     default=lambda self: self.env.ref('inventory.location_type_standard', False),
                                     help="Type of location for special handling requirements")
    
    location_type_code = fields.Char(related='location_type_id.code', string="Type Code", readonly=True, store=True)
    
    # Additional fields
    max_capacity = fields.Float(string="Maximum Capacity (m³)",
                              help="Maximum storage capacity in cubic meters")
    
    current_occupancy = fields.Float(string="Current Occupancy (%)", compute='_compute_current_occupancy',
                                   help="Current occupancy percentage")
    
    # Temperature and humidity control
    has_temperature_control = fields.Boolean(string="Has Temperature Control", default=False)
    
    temperature_min = fields.Float(string="Minimum Temperature (°C)")
    
    temperature_max = fields.Float(string="Maximum Temperature (°C)")
    
    humidity_min = fields.Float(string="Minimum Humidity (%)")
    
    humidity_max = fields.Float(string="Maximum Humidity (%)")
    
    # Security and access control
    requires_approval = fields.Boolean(string="Requires Approval", default=False,
                                     help="Whether moving items to/from this location requires approval")
    
    restricted_access = fields.Boolean(string="Restricted Access", default=False,
                                     help="Whether this location has restricted access")
    
    allowed_user_ids = fields.Many2many('res.users', string="Allowed Users",
                                      help="Users allowed to access this location")
    
    # Tracking and monitoring
    last_inventory_date = fields.Date(string="Last Inventory Date")
    
    next_inventory_date = fields.Date(string="Next Inventory Date")
    
    inventory_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string="Inventory Frequency", default='monthly')
    
    # Customs and compliance
    customs_controlled = fields.Boolean(string="Customs Controlled", default=False,
                                      help="Whether this location is under customs control")
    
    customs_document_required = fields.Boolean(string="Customs Document Required", default=False,
                                             help="Whether customs documents are required for moving items")
    
    @api.depends('max_capacity')
    def _compute_current_occupancy(self):
        for location in self:
            # Calculate current occupancy based on quants
            if location.max_capacity:
                # Get all quants in this location
                quants = self.env['stock.quant'].search([
                    ('location_id', '=', location.id)
                ])
                
                # Calculate total volume
                total_volume = sum(quant.product_id.volume * quant.quantity for quant in quants if quant.product_id.volume)
                
                # Calculate occupancy percentage
                location.current_occupancy = (total_volume / location.max_capacity) * 100
            else:
                location.current_occupancy = 0
    
    @api.constrains('temperature_min', 'temperature_max')
    def _check_temperature_range(self):
        for location in self:
            if location.has_temperature_control:
                if location.temperature_min >= location.temperature_max:
                    raise ValidationError(_("Minimum temperature must be less than maximum temperature."))
    
    @api.constrains('humidity_min', 'humidity_max')
    def _check_humidity_range(self):
        for location in self:
            if location.humidity_min and location.humidity_max:
                if location.humidity_min >= location.humidity_max:
                    raise ValidationError(_("Minimum humidity must be less than maximum humidity."))
                if location.humidity_min < 0 or location.humidity_max > 100:
                    raise ValidationError(_("Humidity values must be between 0 and 100 percent."))
    
    @api.onchange('location_type_id')
    def _onchange_location_type_id(self):
        if self.location_type_id:
            self.customs_controlled = self.location_type_id.customs_controlled
            self.customs_document_required = self.location_type_id.customs_document_required
            self.requires_approval = self.location_type_id.requires_approval
            self.restricted_access = self.location_type_id.restricted_access
            self.has_temperature_control = self.location_type_id.has_temperature_control
    
    def action_schedule_inventory(self):
        """Schedule next inventory based on frequency"""
        for location in self:
            if location.last_inventory_date:
                if location.inventory_frequency == 'daily':
                    location.next_inventory_date = fields.Date.add(location.last_inventory_date, days=1)
                elif location.inventory_frequency == 'weekly':
                    location.next_inventory_date = fields.Date.add(location.last_inventory_date, weeks=1)
                elif location.inventory_frequency == 'monthly':
                    location.next_inventory_date = fields.Date.add(location.last_inventory_date, months=1)
                elif location.inventory_frequency == 'quarterly':
                    location.next_inventory_date = fields.Date.add(location.last_inventory_date, months=3)
                elif location.inventory_frequency == 'yearly':
                    location.next_inventory_date = fields.Date.add(location.last_inventory_date, years=1)
