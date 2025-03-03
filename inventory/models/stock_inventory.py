from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockInventory(models.Model):
    _inherit = 'stock.inventory'
    
    # Moroccan-specific fields
    inventory_type = fields.Selection([
        ('regular', 'Regular Inventory'),
        ('annual', 'Annual Inventory'),
        ('customs', 'Customs Inventory'),
        ('audit', 'Audit Inventory'),
        ('quality', 'Quality Control')
    ], string="Inventory Type", default='regular', required=True,
       help="Type of inventory according to Moroccan regulations")
    
    # Document references
    reference_number = fields.Char(string="Reference Number", 
                                  help="External reference number for this inventory")
    
    # Approval workflow
    requires_approval = fields.Boolean(string="Requires Approval", compute='_compute_requires_approval',
                                     store=True, help="Whether this inventory requires manager approval")
    
    approval_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Approval Status", default='not_required')
    
    approved_by = fields.Many2one('res.users', string="Approved By")
    
    approval_date = fields.Datetime(string="Approval Date")
    
    # Additional tracking
    inventory_reason = fields.Selection([
        ('periodic', 'Periodic'),
        ('discrepancy', 'Discrepancy'),
        ('damaged', 'Damaged Goods'),
        ('expired', 'Expired Products'),
        ('theft', 'Theft or Loss'),
        ('audit', 'External Audit'),
        ('customs', 'Customs Verification'),
        ('other', 'Other')
    ], string="Inventory Reason", default='periodic')
    
    inventory_notes = fields.Text(string="Inventory Notes")
    
    # Responsible parties
    responsible_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    
    supervisor_id = fields.Many2one('res.users', string="Supervisor")
    
    # Scheduling
    scheduled_date = fields.Datetime(string="Scheduled Date")
    
    completion_date = fields.Datetime(string="Completion Date")
    
    duration = fields.Float(string="Duration (Hours)")
    
    # Computed fields
    total_value_mad = fields.Monetary(string="Total Value (MAD)", compute='_compute_total_value_mad',
                                    store=True, help="Total inventory value in Moroccan Dirhams")
    
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', 
                                        string="Company Currency", readonly=True)
    
    mad_currency_id = fields.Many2one('res.currency', compute='_compute_mad_currency_id',
                                    string="MAD Currency", readonly=True)
    
    @api.depends('company_id')
    def _compute_mad_currency_id(self):
        # Get MAD currency
        mad_currency = self.env['res.currency'].search([('name', '=', 'MAD')], limit=1)
        if not mad_currency:
            # If MAD currency doesn't exist, use company currency
            for inventory in self:
                inventory.mad_currency_id = inventory.company_currency_id
        else:
            for inventory in self:
                inventory.mad_currency_id = mad_currency
    
    @api.depends('line_ids.product_id', 'line_ids.product_qty', 'line_ids.product_uom_id', 'company_id', 'mad_currency_id')
    def _compute_total_value_mad(self):
        for inventory in self:
            total_value_mad = 0.0
            
            for line in inventory.line_ids:
                # Get product cost in company currency
                product_cost = line.product_id.standard_price
                
                # Convert to product UoM if necessary
                if line.product_uom_id and line.product_uom_id != line.product_id.uom_id:
                    product_cost = line.product_uom_id._compute_price(product_cost, line.product_id.uom_id)
                
                # Calculate line value in company currency
                line_value = product_cost * line.product_qty
                
                # Convert to MAD if necessary
                if inventory.company_currency_id != inventory.mad_currency_id:
                    line_value_mad = inventory.company_currency_id._convert(
                        line_value,
                        inventory.mad_currency_id,
                        inventory.company_id,
                        fields.Date.today()
                    )
                else:
                    line_value_mad = line_value
                
                total_value_mad += line_value_mad
            
            inventory.total_value_mad = total_value_mad
    
    @api.depends('inventory_type')
    def _compute_requires_approval(self):
        for inventory in self:
            # Annual and customs inventories require approval
            inventory.requires_approval = inventory.inventory_type in ['annual', 'customs', 'audit']
    
    @api.onchange('inventory_type')
    def _onchange_inventory_type(self):
        if self.inventory_type == 'annual':
            self.inventory_reason = 'periodic'
            self.name = _("Annual Inventory - %s") % fields.Date.today().strftime('%Y')
        elif self.inventory_type == 'customs':
            self.inventory_reason = 'customs'
            self.name = _("Customs Inventory - %s") % fields.Date.today().strftime('%Y-%m-%d')
        elif self.inventory_type == 'audit':
            self.inventory_reason = 'audit'
            self.name = _("Audit Inventory - %s") % fields.Date.today().strftime('%Y-%m-%d')
        elif self.inventory_type == 'quality':
            self.inventory_reason = 'other'
            self.name = _("Quality Control - %s") % fields.Date.today().strftime('%Y-%m-%d')
    
    def action_start(self):
        # Check if approval is required but not yet approved
        for inventory in self:
            if inventory.requires_approval and inventory.approval_state not in ['approved', 'not_required']:
                raise ValidationError(_("This inventory requires approval before starting."))
        
        return super(StockInventory, self).action_start()
    
    def action_validate(self):
        # Record completion date and duration
        for inventory in self:
            inventory.completion_date = fields.Datetime.now()
            if inventory.start_date:
                start_date = fields.Datetime.from_string(inventory.start_date)
                completion_date = fields.Datetime.from_string(inventory.completion_date)
                duration_seconds = (completion_date - start_date).total_seconds()
                inventory.duration = duration_seconds / 3600  # Convert to hours
        
        return super(StockInventory, self).action_validate()
    
    def action_request_approval(self):
        for inventory in self:
            if inventory.requires_approval:
                inventory.approval_state = 'pending'
    
    def action_approve(self):
        self.ensure_one()
        self.approval_state = 'approved'
        self.approved_by = self.env.user
        self.approval_date = fields.Datetime.now()
    
    def action_reject(self):
        self.ensure_one()
        self.approval_state = 'rejected'
