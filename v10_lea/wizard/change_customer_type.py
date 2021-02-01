from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardChangeCustomerType(models.TransientModel):
    _name = "wizard.change.customer.type"
    _description = "Change Customer Type"
        
    @api.multi
    def button_change(self):        
        context = dict(self._context or {})            
        orders = self.env['sale.order'].browse(context.get('active_ids'))
        for order in orders:
            order.write({
                         'customer_type': order.partner_id.customer_type
                         })
                    
        return {'type': 'ir.actions.act_window_close'}
