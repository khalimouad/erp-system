from odoo import api, fields, models
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class SimplisGenerateXmlWizard(models.TransientModel):
    _name = 'simplis.generate.xml.wizard'
    _description = 'Generate XML for SIMPL-IS Declaration'
    
    declaration_subtype = fields.Selection([
        ('liasse', 'Liasse Fiscale'),
        ('drvt', 'Déclaration des rémunérations versées à des tiers'),
        ('papsra', 'Déclaration des produits des actions, parts sociales et revenus assimilés'),
        ('pprf', 'Déclaration des produits de placements à revenu fixe'),
        ('ca', 'Déclaration de Chiffre d\'affaires'),
        ('rvt_med', 'Déclaration des rémunérations versées à des tiers (Médecins)'),
        ('ras', 'Déclaration des rémunérations versées à des personnes non résidentes'),
        ('profit', 'Déclaration du résultat fiscal au titre des plus values'),
    ], string='Declaration Type', required=True, default='liasse')
    
    model_id = fields.Selection([
        ('1', 'Comptable Normal'),
        ('2', 'Comptable Simplifié'),
        ('3', 'Etablissements de crédit'),
        ('4', 'Assurance'),
    ], string='Liasse Model', help="Only applicable for Liasse Fiscale")
    
    fiscal_year = fields.Char(string='Fiscal Year', required=True, default=lambda self: str(date.today().year))
    date_from = fields.Date(string='From Date', required=True, default=lambda self: date(date.today().year, 1, 1))
    date_to = fields.Date(string='To Date', required=True, default=lambda self: date(date.today().year, 12, 31))
    
    @api.onchange('fiscal_year')
    def _onchange_fiscal_year(self):
        if self.fiscal_year and self.fiscal_year.isdigit():
            year = int(self.fiscal_year)
            self.date_from = date(year, 1, 1)
            self.date_to = date(year, 12, 31)
    
    def action_generate(self):
        self.ensure_one()
        
        # Create the declaration record
        declaration = self.env['simplis.declaration'].create({
            'name': f"SIMPL-IS {self.declaration_subtype.upper()} {self.fiscal_year}",
            'declaration_type': 'is',
            'declaration_subtype': self.declaration_subtype,
            'model_id': self.model_id if self.declaration_subtype == 'liasse' else False,
            'fiscal_year': self.fiscal_year,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'year': self.fiscal_year,
            'period': '13',  # Annual
        })
        
        # Open the created declaration
        return {
            'name': 'SIMPL-IS Declaration',
            'type': 'ir.actions.act_window',
            'res_model': 'simplis.declaration',
            'res_id': declaration.id,
            'view_mode': 'form',
            'target': 'current',
        }
