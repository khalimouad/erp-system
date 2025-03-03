from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # Moroccan-specific company fields
    cnss_number = fields.Char(string="CNSS Number", help="Social Security Number")
    rc_number = fields.Char(string="RC Number", help="Trade Register Number")
    ice_number = fields.Char(string="ICE Number", help="Tax ID")
    legal_form = fields.Selection([
        ('sarl', 'SARL - Limited Liability Company'),
        ('sa', 'SA - Public Limited Company'),
        ('sas', 'SAS - Simplified Joint-Stock Company'),
        ('snc', 'SNC - General Partnership'),
        ('scs', 'SCS - Limited Partnership'),
        ('sarlau', 'SARL AU - Single Member Limited Liability Company'),
        ('other', 'Other')
    ], string="Legal Form", default='sarl')
    
    region = fields.Selection([
        ('casablanca_settat', 'Casablanca-Settat'),
        ('rabat_sale_kenitra', 'Rabat-Salé-Kénitra'),
        ('marrakech_safi', 'Marrakech-Safi'),
        ('fes_meknes', 'Fès-Meknès'),
        ('tanger_tetouan_alhoceima', 'Tanger-Tétouan-Al Hoceïma'),
        ('souss_massa', 'Souss-Massa'),
        ('oriental', 'Oriental'),
        ('beni_mellal_khenifra', 'Béni Mellal-Khénifra'),
        ('draa_tafilalet', 'Drâa-Tafilalet'),
        ('guelmim_oued_noun', 'Guelmim-Oued Noun'),
        ('laayoune_sakia_elhamra', 'Laâyoune-Sakia El Hamra'),
        ('dakhla_oued_eddahab', 'Dakhla-Oued Ed-Dahab')
    ], string="Region")
    
    is_sme = fields.Boolean(string="Is SME", help="Small and Medium Enterprise")
    is_exporter = fields.Boolean(string="Is Exporter")
    is_in_free_zone = fields.Boolean(string="Is in Free Zone")
    free_zone_name = fields.Char(string="Free Zone Name")
    
    has_tax_exemption = fields.Boolean(string="Has Tax Exemption")
    tax_exemption_type = fields.Selection([
        ('export', 'Export Company'),
        ('free_zone', 'Free Zone'),
        ('investment', 'Investment Agreement'),
        ('other', 'Other')
    ], string="Tax Exemption Type")
    tax_exemption_expiry = fields.Date(string="Tax Exemption Expiry Date")
    
    # Accounting-related fields
    accounting_method = fields.Selection([
        ('accrual', 'Accrual Accounting'),
        ('cash', 'Cash Accounting')
    ], string="Accounting Method", default='accrual')
    fiscal_year_start_month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ], string="Fiscal Year Start Month", default='1')
    fiscal_year_start_day = fields.Selection([
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
        ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
        ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
        ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
        ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24'), ('25', '25'),
        ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'), ('30', '30'),
        ('31', '31')
    ], string="Fiscal Year Start Day", default='1')
    
    # VAT-related fields
    vat_filing_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly')
    ], string="VAT Filing Frequency", default='monthly')
    
    # Additional contact information
    website = fields.Char(string="Website")
    social_facebook = fields.Char(string="Facebook")
    social_twitter = fields.Char(string="Twitter")
    social_linkedin = fields.Char(string="LinkedIn")
    
    @api.onchange('is_in_free_zone')
    def _onchange_is_in_free_zone(self):
        if not self.is_in_free_zone:
            self.free_zone_name = False
            
    @api.onchange('has_tax_exemption')
    def _onchange_has_tax_exemption(self):
        if not self.has_tax_exemption:
            self.tax_exemption_type = False
            self.tax_exemption_expiry = False
