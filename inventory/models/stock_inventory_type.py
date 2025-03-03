from odoo import api, fields, models, _

class StockInventoryType(models.Model):
    _name = 'stock.inventory.type'
    _description = 'Inventory Type'
    _order = 'sequence, id'
    
    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    
    requires_approval = fields.Boolean(string='Requires Approval', default=False,
                                     help="Whether inventories of this type require approval")
    
    requires_supervisor = fields.Boolean(string='Requires Supervisor', default=False,
                                       help="Whether inventories of this type require a supervisor")
    
    requires_documentation = fields.Boolean(string='Requires Documentation', default=False,
                                          help="Whether inventories of this type require additional documentation")
    
    note = fields.Text(string='Notes')
