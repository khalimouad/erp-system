from odoo import api, fields, models, _

class StockLocationType(models.Model):
    _name = 'stock.location.type'
    _description = 'Location Type'
    _order = 'sequence, id'
    
    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    
    requires_approval = fields.Boolean(string='Requires Approval', default=False,
                                     help="Whether operations in locations of this type require approval")
    
    restricted_access = fields.Boolean(string='Restricted Access', default=False,
                                     help="Whether locations of this type have restricted access")
    
    has_temperature_control = fields.Boolean(string='Temperature Control', default=False,
                                           help="Whether locations of this type have temperature control")
    
    customs_controlled = fields.Boolean(string='Customs Controlled', default=False,
                                      help="Whether locations of this type are under customs control")
    
    customs_document_required = fields.Boolean(string='Customs Document Required', default=False,
                                             help="Whether customs documents are required for operations in locations of this type")
    
    note = fields.Text(string='Notes')
