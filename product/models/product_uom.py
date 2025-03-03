from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class UoM(models.Model):
    _inherit = 'uom.uom'
    
    # Additional fields
    local_name = fields.Char(string="Local Name (Arabic)",
                           help="Unit of measure name in Arabic")
    
    abbreviation = fields.Char(string="Abbreviation",
                              help="Short form of the unit of measure")
    
    description = fields.Text(string="Description")
    
    is_active = fields.Boolean(string="Active", default=True)
    
    # Statistics fields
    product_count = fields.Integer(string="Product Count", compute='_compute_product_count')
    
    # Additional fields for better UoM management
    decimal_precision = fields.Integer(string="Decimal Precision", default=2,
                                     help="Number of decimal places to use in calculations")
    
    display_format = fields.Char(string="Display Format", 
                               help="Format string for displaying quantities (e.g., '%.2f %s')")
    
    # Conversion tracking fields
    last_conversion_date = fields.Datetime(string="Last Conversion Date", readonly=True,
                                         help="Date of last conversion using this unit")
    
    conversion_count = fields.Integer(string="Conversion Count", default=0, readonly=True,
                                    help="Number of times this unit has been used in conversions")
    
    @api.depends()
    def _compute_product_count(self):
        for uom in self:
            uom.product_count = self.env['product.template'].search_count([
                ('uom_id', '=', uom.id)
            ])
    
    @api.constrains('factor', 'factor_inv')
    def _check_factor(self):
        for uom in self:
            if uom.factor <= 0 or uom.factor_inv <= 0:
                raise ValidationError(_("Conversion factors must be greater than zero"))
    
    @api.onchange('name')
    def _onchange_name(self):
        if self.name and not self.abbreviation:
            # Generate abbreviation from name if not set
            words = self.name.split()
            if len(words) > 1:
                self.abbreviation = ''.join(word[0].upper() for word in words)
            else:
                self.abbreviation = self.name[:3].upper()
    
    def convert_to_reference(self, qty):
        """Convert quantity from this UoM to the reference UoM of the category"""
        self.ensure_one()
        self._update_conversion_stats()
        if self.uom_type == 'reference':
            return qty
        return qty * self.factor
    
    def convert_from_reference(self, qty):
        """Convert quantity from reference UoM to this UoM"""
        self.ensure_one()
        self._update_conversion_stats()
        if self.uom_type == 'reference':
            return qty
        return qty / self.factor
    
    def _update_conversion_stats(self):
        """Update conversion statistics"""
        self.ensure_one()
        self.write({
            'last_conversion_date': fields.Datetime.now(),
            'conversion_count': self.conversion_count + 1
        })
    
    def format_quantity(self, quantity):
        """Format a quantity according to this UoM's display format"""
        self.ensure_one()
        format_string = self.display_format or f"%.{self.decimal_precision}f %s"
        return format_string % (quantity, self.abbreviation or self.name)
    
    def name_get(self):
        """Override name_get to include abbreviation if available"""
        result = []
        for uom in self:
            name = uom.name
            if uom.abbreviation:
                name = f"{name} ({uom.abbreviation})"
            result.append((uom.id, name))
        return result
    
    @api.model
    def create(self, vals):
        """Override create to set default display format if not provided"""
        if 'display_format' not in vals and 'decimal_precision' in vals:
            vals['display_format'] = f"%.{vals['decimal_precision']}f %s"
        return super(UoM, self).create(vals)
    
    def write(self, vals):
        """Override write to update display format when decimal_precision changes"""
        res = super(UoM, self).write(vals)
        if 'decimal_precision' in vals and 'display_format' not in vals:
            for uom in self:
                uom.display_format = f"%.{uom.decimal_precision}f %s"
        return res
    
    def action_view_products(self):
        """Open a view showing all products that use this unit of measure"""
        self.ensure_one()
        action = self.env.ref('product.action_product_template').read()[0]
        action['domain'] = [('uom_id', '=', self.id)]
        action['context'] = {
            'default_uom_id': self.id,
            'search_default_filter_to_sell': 0  # Remove default filter
        }
        action['name'] = _("Products with UoM: %s") % self.name
        return action
    
    def action_open_conversion_wizard(self):
        """Open the UoM conversion wizard with this UoM as the source"""
        self.ensure_one()
        action = self.env.ref('product.action_uom_conversion_wizard').read()[0]
        action['context'] = {
            'default_source_uom_id': self.id,
        }
        return action
