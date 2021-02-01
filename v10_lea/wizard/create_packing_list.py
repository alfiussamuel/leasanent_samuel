from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardCreateJobPacking(models.TransientModel):
    _name = "wizard.create.job.packing"
    _description = "Create Job Packing"
    
    @api.multi
    def button_create(self):        
        context = dict(self._context or {})            
        pickings = self.env['stock.picking'].browse(context.get('active_ids'))
        sale_id = ''
        for pick in pickings:                                    
            sale_id = self.env['sale.order'].search([('name','=',pick.origin)])
            packing_list = self.env['lea.packing.list'].create({
                                                                'date': fields.Date.today(),
                                                                'picking_id': pick.id,
                                                                'picking_date': pick.min_date,
                                                                'sale_id': sale_id.id,
                                                                'sale_date': sale_id.date_order,
                                                                'partner_id': pick.partner_id.id,                                                            
                                                                })
            
            for pack in pick.pack_operation_ids:                          
                self.env['lea.packing.list.line'].create({
                                                          'reference': packing_list.id,                                                          
                                                          'product_id': pack.product_id.id,
                                                          'qty_picked': pack.product_qty,     
                                                          'qty_remaining': pack.product_qty,                                                                                                                
                                                          })
            
            pick.write({
                        'is_packing_list': True,
                        'packing_list_id': packing_list.id,
                        })
                        
        return {'type': 'ir.actions.act_window_close'}
