from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    # Moroccan-specific fields
    customs_status = fields.Selection([
        ('pending', 'Pending Customs'),
        ('cleared', 'Customs Cleared'),
        ('not_applicable', 'Not Applicable')
    ], string="Customs Status", default='not_applicable',
       help="Status of customs clearance for this inventory")
    
    # Quality control
    quality_state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Quality State", default='pending')
    
    # Lot tracking
    lot_origin_type = fields.Selection(related='lot_id.origin_type', string="Lot Origin", readonly=True)
    
    lot_expiry_date = fields.Date(related='lot_id.expiry_date', string="Expiry Date", readonly=True)
    
    lot_expiry_alert = fields.Boolean(related='lot_id.expiry_alert', string="Expiry Alert", readonly=True)
    
    lot_days_until_expiry = fields.Integer(related='lot_id.days_until_expiry', string="Days Until Expiry", readonly=True)
    
    lot_is_quarantine = fields.Boolean(related='lot_id.is_quarantine', string="In Quarantine", readonly=True)
    
    # Additional tracking
    last_inventory_date = fields.Date(string="Last Inventory Date")
    
    last_counted_by = fields.Many2one('res.users', string="Last Counted By")
    
    # Computed fields
    value_mad = fields.Monetary(string="Value (MAD)", compute='_compute_value_mad',
                              store=True, help="Value in Moroccan Dirhams")
    
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', 
                                        string="Company Currency", readonly=True)
    
    mad_currency_id = fields.Many2one('res.currency', compute='_compute_mad_currency_id',
                                    string="MAD Currency", readonly=True)
    
    # Location type
    location_type = fields.Selection(related='location_id.location_type', string="Location Type", readonly=True)
    
    # Temperature control
    has_temperature_control = fields.Boolean(related='location_id.has_temperature_control', 
                                           string="Has Temperature Control", readonly=True)
    
    temperature_min = fields.Float(related='location_id.temperature_min', 
                                 string="Minimum Temperature (°C)", readonly=True)
    
    temperature_max = fields.Float(related='location_id.temperature_max', 
                                 string="Maximum Temperature (°C)", readonly=True)
    
    @api.depends('company_id')
    def _compute_mad_currency_id(self):
        # Get MAD currency
        mad_currency = self.env['res.currency'].search([('name', '=', 'MAD')], limit=1)
        if not mad_currency:
            # If MAD currency doesn't exist, use company currency
            for quant in self:
                quant.mad_currency_id = quant.company_currency_id
        else:
            for quant in self:
                quant.mad_currency_id = mad_currency
    
    @api.depends('value', 'company_id', 'mad_currency_id')
    def _compute_value_mad(self):
        for quant in self:
            if quant.company_currency_id == quant.mad_currency_id:
                # If company currency is MAD, use the same value
                quant.value_mad = quant.value
            else:
                # Convert value to MAD
                company_currency = quant.company_currency_id
                mad_currency = quant.mad_currency_id
                
                if company_currency and mad_currency:
                    quant.value_mad = company_currency._convert(
                        quant.value,
                        mad_currency,
                        quant.company_id,
                        fields.Date.today()
                    )
                else:
                    quant.value_mad = quant.value
    
    @api.constrains('location_id', 'lot_id')
    def _check_lot_location_compatibility(self):
        for quant in self:
            # Check if quarantine lot is in quarantine location
            if quant.lot_id and quant.lot_id.is_quarantine and quant.location_id.location_type != 'quarantine':
                raise ValidationError(_("Quarantined lot %s must be stored in a quarantine location.") % quant.lot_id.name)
            
            # Check if temperature-controlled product is in temperature-controlled location
            if quant.lot_id and quant.product_id.temperature_control_required and not quant.location_id.has_temperature_control:
                raise ValidationError(_("Temperature-controlled product %s must be stored in a temperature-controlled location.") % quant.product_id.name)
    
    def action_apply_inventory(self):
        # Record inventory date and counter
        for quant in self:
            quant.last_inventory_date = fields.Date.today()
            quant.last_counted_by = self.env.user
        
        return super(StockQuant, self).action_apply_inventory()
    
    def action_set_inventory_quantity(self):
        # Record inventory date and counter
        for quant in self:
            quant.last_inventory_date = fields.Date.today()
            quant.last_counted_by = self.env.user
        
        return super(StockQuant, self).action_set_inventory_quantity()
    
    def action_set_inventory_quantity_to_zero(self):
        # Record inventory date and counter
        for quant in self:
            quant.last_inventory_date = fields.Date.today()
            quant.last_counted_by = self.env.user
        
        return super(StockQuant, self).action_set_inventory_quantity_to_zero()
