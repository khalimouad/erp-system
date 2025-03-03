from odoo import api, fields, models

class DgiCommune(models.Model):
    """DGI Commune Reference for Declarations"""
    _name = 'dgi.commune'
    _description = 'DGI Commune Reference'
    
    name = fields.Char(string='Commune Name', required=True)
    code = fields.Char(string='Commune Code', required=True)
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The commune code must be unique!')
    ]


class DgiNature(models.Model):
    """DGI Nature Reference for Declarations"""
    _name = 'dgi.nature'
    _description = 'DGI Nature Reference'
    
    name = fields.Char(string='Nature Name', required=True)
    code = fields.Char(string='Nature Code', required=True)
    declaration_type = fields.Selection([
        ('papsra', 'PAPSRA'),
        ('pprf', 'PPRF'),
        ('ca', 'CA'),
        ('ras', 'RAS'),
        ('profit', 'PROFIT'),
    ], string='Declaration Type', required=True)
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('code_type_unique', 'unique(code, declaration_type)', 'The nature code must be unique per declaration type!')
    ]


class DgiTaux(models.Model):
    """DGI Tax Rate Reference for Declarations"""
    _name = 'dgi.taux'
    _description = 'DGI Tax Rate Reference'
    
    name = fields.Char(string='Rate Name', required=True)
    code = fields.Char(string='Rate Code', required=True)
    rate = fields.Float(string='Rate (%)', required=True)
    declaration_type = fields.Selection([
        ('drvt', 'DRVT'),
        ('papsra', 'PAPSRA'),
        ('pprf', 'PPRF'),
        ('rvt_med', 'RVT_MED'),
        ('ras', 'RAS'),
        ('profit', 'PROFIT'),
    ], string='Declaration Type', required=True)
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('code_type_unique', 'unique(code, declaration_type)', 'The rate code must be unique per declaration type!')
    ]
