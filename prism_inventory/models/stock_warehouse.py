from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    # Moroccan-specific fields
    warehouse_type_id = fields.Many2one('stock.warehouse.type', string="Warehouse Type", 
                                      required=True, 
                                      help="Type of warehouse according to Moroccan regulations")
    warehouse_type_code = fields.Char(related='warehouse_type_id.code', string="Warehouse Type Code", 
                                    readonly=True, store=True)
    
    customs_code = fields.Char(string="Customs Code", 
                              help="Customs code for bonded or free zone warehouses")
    
    customs_authorization = fields.Char(string="Customs Authorization", 
                                      help="Authorization number from customs for special warehouses")
    
    customs_authorization_date = fields.Date(string="Authorization Date")
    
    customs_officer_id = fields.Many2one('res.partner', string="Customs Officer",
                                       domain=[('is_company', '=', False)],
                                       help="Customs officer responsible for this warehouse")
    
    # Additional fields
    is_vat_exempt = fields.Boolean(string="VAT Exempt", 
                                 related='warehouse_type_id.is_vat_exempt', 
                                 readonly=True, store=True,
                                 help="Whether goods in this warehouse are exempt from VAT")
    
    requires_customs_clearance = fields.Boolean(string="Requires Customs Clearance", 
                                              related='warehouse_type_id.requires_customs',
                                              readonly=True, store=True)
    
    # Location constraints
    max_storage_capacity = fields.Float(string="Maximum Storage Capacity (m³)",
                                      help="Maximum storage capacity in cubic meters")
    
    current_occupancy = fields.Float(string="Current Occupancy (%)", compute='_compute_current_occupancy',
                                   help="Current occupancy percentage")
    
    # Security and compliance
    has_security_cameras = fields.Boolean(string="Has Security Cameras", default=False)
    
    has_fire_system = fields.Boolean(string="Has Fire System", default=False)
    
    has_temperature_control = fields.Boolean(string="Has Temperature Control", default=False)
    
    temperature_min = fields.Float(string="Minimum Temperature (°C)")
    
    temperature_max = fields.Float(string="Maximum Temperature (°C)")
    
    humidity_min = fields.Float(string="Minimum Humidity (%)")
    
    humidity_max = fields.Float(string="Maximum Humidity (%)")
    
    last_inspection_date = fields.Date(string="Last Inspection Date")
    
    next_inspection_date = fields.Date(string="Next Inspection Date")
    
    inspection_notes = fields.Text(string="Inspection Notes")
    
    # This method is no longer needed as we're using a related field
    # @api.depends('warehouse_type_id')
    # def _compute_requires_customs_clearance(self):
    #     for warehouse in self:
    #         warehouse.requires_customs_clearance = warehouse.warehouse_type_id.requires_customs
    
    @api.depends('max_storage_capacity')
    def _compute_current_occupancy(self):
        for warehouse in self:
            # Calculate current occupancy based on quants
            if warehouse.max_storage_capacity:
                # Get all quants in this warehouse
                quants = self.env['stock.quant'].search([
                    ('location_id.warehouse_id', '=', warehouse.id),
                    ('location_id.usage', '=', 'internal')
                ])
                
                # Calculate total volume
                total_volume = sum(quant.product_id.volume * quant.quantity for quant in quants if quant.product_id.volume)
                
                # Calculate occupancy percentage
                warehouse.current_occupancy = (total_volume / warehouse.max_storage_capacity) * 100
            else:
                warehouse.current_occupancy = 0
    
    @api.constrains('warehouse_type_id', 'customs_code', 'customs_authorization')
    def _check_customs_info(self):
        for warehouse in self:
            if warehouse.requires_customs_clearance:
                if not warehouse.customs_code:
                    raise ValidationError(_("Customs code is required for %s warehouses.") % warehouse.warehouse_type_id.name)
                if not warehouse.customs_authorization:
                    raise ValidationError(_("Customs authorization is required for %s warehouses.") % warehouse.warehouse_type_id.name)
    
    @api.constrains('temperature_min', 'temperature_max')
    def _check_temperature_range(self):
        for warehouse in self:
            if warehouse.has_temperature_control:
                if warehouse.temperature_min >= warehouse.temperature_max:
                    raise ValidationError(_("Minimum temperature must be less than maximum temperature."))
    
    @api.constrains('humidity_min', 'humidity_max')
    def _check_humidity_range(self):
        for warehouse in self:
            if warehouse.humidity_min and warehouse.humidity_max:
                if warehouse.humidity_min >= warehouse.humidity_max:
                    raise ValidationError(_("Minimum humidity must be less than maximum humidity."))
                if warehouse.humidity_min < 0 or warehouse.humidity_max > 100:
                    raise ValidationError(_("Humidity values must be between 0 and 100 percent."))
    
    def action_schedule_inspection(self):
        """Schedule next inspection based on warehouse type"""
        for warehouse in self:
            if warehouse.last_inspection_date:
                if warehouse.requires_customs_clearance:
                    # Schedule next inspection in 3 months for customs-controlled warehouses
                    warehouse.next_inspection_date = fields.Date.add(warehouse.last_inspection_date, months=3)
                else:
                    # Schedule next inspection in 6 months for standard warehouses
                    warehouse.next_inspection_date = fields.Date.add(warehouse.last_inspection_date, months=6)
                
                # Log the inspection scheduling
                self.env['mail.message'].create({
                    'body': _("Next inspection scheduled for %s") % warehouse.next_inspection_date,
                    'model': self._name,
                    'res_id': warehouse.id,
                    'message_type': 'notification',
                    'subtype_id': self.env.ref('mail.mt_note').id,
                })
