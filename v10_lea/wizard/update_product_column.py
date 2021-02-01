from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardUpdateProductRack(models.TransientModel):
    _name = "wizard.update.product.rack"
    _description = "Update Product Rack"
        
    @api.multi
    def button_update(self):        
        context = dict(self._context or {})            
        columns = self.env['lea.rack.level.column'].browse(context.get('active_ids'))
        for column in columns:
            column.create_column_product()                    
        return {'type': 'ir.actions.act_window_close'}
