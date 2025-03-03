from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class UoMConversionWizard(models.TransientModel):
    _name = 'uom.conversion.wizard'
    _description = 'Unit of Measure Conversion Wizard'
    
    # Source UoM and quantity
    source_uom_id = fields.Many2one('uom.uom', string="Source Unit of Measure", 
                                   required=True, ondelete='cascade')
    source_quantity = fields.Float(string="Source Quantity", default=1.0, required=True)
    
    # Target UoM and quantity
    target_uom_id = fields.Many2one('uom.uom', string="Target Unit of Measure", 
                                   required=True, ondelete='cascade')
    target_quantity = fields.Float(string="Target Quantity", compute='_compute_target_quantity', 
                                  readonly=True, store=True)
    
    # Formatted display fields
    source_display = fields.Char(string="Source Display", compute='_compute_displays')
    target_display = fields.Char(string="Target Display", compute='_compute_displays')
    
    # Category constraint
    @api.constrains('source_uom_id', 'target_uom_id')
    def _check_category(self):
        for wizard in self:
            if wizard.source_uom_id.category_id != wizard.target_uom_id.category_id:
                raise ValidationError(_("Source and target units of measure must be in the same category."))
    
    # Auto-fill target UoM based on source UoM's category
    @api.onchange('source_uom_id')
    def _onchange_source_uom(self):
        if self.source_uom_id and not self.target_uom_id:
            # Try to set the reference UoM of the category as the target
            reference_uom = self.env['uom.uom'].search([
                ('category_id', '=', self.source_uom_id.category_id.id),
                ('uom_type', '=', 'reference')
            ], limit=1)
            
            if reference_uom and reference_uom != self.source_uom_id:
                self.target_uom_id = reference_uom.id
    
    # Compute target quantity based on source quantity and UoMs
    @api.depends('source_uom_id', 'target_uom_id', 'source_quantity')
    def _compute_target_quantity(self):
        for wizard in self:
            if not (wizard.source_uom_id and wizard.target_uom_id and wizard.source_quantity):
                wizard.target_quantity = 0.0
                continue
                
            # Update conversion stats for both UoMs
            wizard.source_uom_id._update_conversion_stats()
            wizard.target_uom_id._update_conversion_stats()
            
            # Convert to reference UoM first, then to target UoM
            if wizard.source_uom_id == wizard.target_uom_id:
                wizard.target_quantity = wizard.source_quantity
            else:
                # Convert to reference
                reference_qty = wizard.source_uom_id.convert_to_reference(wizard.source_quantity)
                # Convert from reference to target
                wizard.target_quantity = wizard.target_uom_id.convert_from_reference(reference_qty)
    
    # Compute formatted displays
    @api.depends('source_uom_id', 'target_uom_id', 'source_quantity', 'target_quantity')
    def _compute_displays(self):
        for wizard in self:
            if wizard.source_uom_id and wizard.source_quantity:
                wizard.source_display = wizard.source_uom_id.format_quantity(wizard.source_quantity)
            else:
                wizard.source_display = ''
                
            if wizard.target_uom_id and wizard.target_quantity:
                wizard.target_display = wizard.target_uom_id.format_quantity(wizard.target_quantity)
            else:
                wizard.target_display = ''
    
    # Swap source and target UoMs
    def action_swap_uoms(self):
        self.ensure_one()
        # Swap UoMs
        self.source_uom_id, self.target_uom_id = self.target_uom_id, self.source_uom_id
        # Set source quantity to previous target quantity
        self.source_quantity = self.target_quantity
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'uom.conversion.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
