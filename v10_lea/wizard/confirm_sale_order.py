from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError


class WizardConfirmSaleOrder(models.TransientModel):
    _name = "wizard.confirm.sale.order"
    _description = "Confirm Sale"
        
    @api.multi
    def button_confirm(self):        
        context = dict(self._context or {})            
        orders = self.env['sale.order'].browse(context.get('active_ids'))
        for order in orders:
            if order.state not in ['draft','sent']:
                raise Warning('Only quotation can be multiple confirm !')

            order.action_confirm()

        return {'type': 'ir.actions.act_window_close'}


class WizardConfirmSaleOrderLine(models.TransientModel):
    _name = "wizard.confirm.sale.order.line"
    _description = "Confirm Sale Order Line"
    
    @api.multi
    def button_confirm(self):        
        context = dict(self._context or {})   
        orders = self.env['sale.order.line'].browse(context.get('active_ids'))

        confirmed_so_list = []

        for order in orders:
            #search all related sale order line
            all_soi = self.env['sale.order.line'].search([('order_id','=',order.order_id.id)]).ids
            for soi in all_soi:
                if soi not in context.get('active_ids'):
                    raise Warning('Terdapat order line yang belum terpilih untuk ' + order.order_id.name)

            if order.state not in ['draft','sent']:
                raise Warning('Only quotation can be multiple confirm !')

            if order.order_id.id not in confirmed_so_list:
                confirmed_so_list.append(order.order_id.id)

        #START TO CONFIRM SALES
        to_do_confirmed_so = self.env['sale.order'].search([('id','in',confirmed_so_list)])
        for so in to_do_confirmed_so:
            so.action_confirm()

        return {'type': 'ir.actions.act_window_close'}

#UPDATE DISCOUNT
class WizardUpdateDiscountSaleOrderLine(models.TransientModel):
    _name = "wizard.update.discount.sale.order.line"
    _description = "Update Discount"
    
    @api.onchange('discount')
    def onchange_discount(self):
        context = dict(self._context or {})
        orders = self.env['sale.order.line'].browse(context.get('active_ids'))
        if orders:
            self.discount = orders[0].discount
            self.new_discount = orders[0].discount

    discount = fields.Float('Current Discount')
    new_discount = fields.Float('New Discount', required=True)

    @api.multi
    def button_confirm(self):        
        context = dict(self._context or {})   
        orders = self.env['sale.order.line'].browse(context.get('active_ids'))

        for order in orders:
            if order.discount != self.new_discount:
                order.write({'discount':self.new_discount})

        return {'type': 'ir.actions.act_window_close'}
