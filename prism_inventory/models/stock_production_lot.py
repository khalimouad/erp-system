from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    
    # Moroccan-specific fields
    origin_type = fields.Selection([
        ('domestic', 'Domestic'),
        ('imported', 'Imported'),
        ('free_zone', 'Free Zone')
    ], string="Origin Type", default='domestic', required=True,
       help="Origin of the lot according to Moroccan regulations")
    
    customs_document = fields.Char(string="Customs Document", 
                                  help="Customs document reference for imported products")
    
    customs_date = fields.Date(string="Customs Date",
                             help="Date of customs clearance for imported products")
    
    # Traceability fields
    manufacturer_id = fields.Many2one('res.partner', string="Manufacturer",
                                    domain=[('is_company', '=', True)],
                                    help="Manufacturer of this lot")
    
    manufacturer_date = fields.Date(string="Manufacturing Date")
    
    best_before_date = fields.Date(string="Best Before Date")
    
    expiry_date = fields.Date(string="Expiry Date")
    
    use_days = fields.Integer(string="Days to Use",
                            help="Number of days the product can be used after opening")
    
    # Quality control
    quality_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Inspection'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Quality State", default='draft')
    
    quality_check_date = fields.Date(string="Quality Check Date")
    
    quality_checked_by = fields.Many2one('res.users', string="Checked By")
    
    quality_notes = fields.Text(string="Quality Notes")
    
    # Additional tracking
    is_sample = fields.Boolean(string="Is Sample", default=False,
                             help="Whether this lot is a sample")
    
    is_quarantine = fields.Boolean(string="In Quarantine", default=False,
                                 help="Whether this lot is in quarantine")
    
    quarantine_reason = fields.Text(string="Quarantine Reason")
    
    quarantine_until = fields.Date(string="Quarantine Until")
    
    # Computed fields
    days_until_expiry = fields.Integer(string="Days Until Expiry", compute='_compute_days_until_expiry',
                                     store=True, help="Number of days until expiry")
    
    expiry_alert = fields.Boolean(string="Expiry Alert", compute='_compute_expiry_alert',
                                store=True, help="Whether this lot is nearing expiry")
    
    @api.depends('expiry_date')
    def _compute_days_until_expiry(self):
        today = fields.Date.today()
        for lot in self:
            if lot.expiry_date:
                delta = lot.expiry_date - today
                lot.days_until_expiry = delta.days
            else:
                lot.days_until_expiry = False
    
    @api.depends('days_until_expiry')
    def _compute_expiry_alert(self):
        for lot in self:
            if lot.days_until_expiry is not False:
                # Alert if less than 30 days until expiry
                lot.expiry_alert = lot.days_until_expiry <= 30
            else:
                lot.expiry_alert = False
    
    @api.constrains('origin_type', 'customs_document', 'customs_date')
    def _check_customs_info(self):
        for lot in self:
            if lot.origin_type in ['imported', 'free_zone']:
                if not lot.customs_document:
                    raise ValidationError(_("Customs document is required for %s products.") % lot.origin_type)
                if not lot.customs_date:
                    raise ValidationError(_("Customs date is required for %s products.") % lot.origin_type)
    
    @api.constrains('manufacturer_date', 'expiry_date')
    def _check_dates(self):
        for lot in self:
            if lot.manufacturer_date and lot.expiry_date:
                if lot.manufacturer_date > lot.expiry_date:
                    raise ValidationError(_("Manufacturing date cannot be after expiry date."))
    
    @api.onchange('manufacturer_date', 'product_id')
    def _onchange_manufacturer_date(self):
        if self.manufacturer_date and self.product_id and self.product_id.use_expiration_date:
            # If product has shelf life, calculate expiry date
            if hasattr(self.product_id, 'shelf_life_days') and self.product_id.shelf_life_days:
                self.expiry_date = fields.Date.add(self.manufacturer_date, days=self.product_id.shelf_life_days)
    
    def action_quality_approve(self):
        self.ensure_one()
        self.quality_state = 'approved'
        self.quality_check_date = fields.Date.today()
        self.quality_checked_by = self.env.user
    
    def action_quality_reject(self):
        self.ensure_one()
        self.quality_state = 'rejected'
        self.quality_check_date = fields.Date.today()
        self.quality_checked_by = self.env.user
        # Put in quarantine
        self.is_quarantine = True
        self.quarantine_until = fields.Date.add(fields.Date.today(), days=30)
    
    def action_set_quarantine(self):
        self.ensure_one()
        self.is_quarantine = True
        self.quarantine_until = fields.Date.add(fields.Date.today(), days=30)
    
    def action_release_quarantine(self):
        self.ensure_one()
        self.is_quarantine = False
        self.quarantine_until = False
