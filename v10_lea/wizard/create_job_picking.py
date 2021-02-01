from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardCreateJobPicking(models.TransientModel):
    _name = "wizard.create.job.picking"
    _description = "Create Job Picking"

    gate_id = fields.Many2one('lea.gate', 'Outgoing Gate') 
    picker_id = fields.Many2one('lea.picker', 'Picker Name') 
    
    @api.multi
    def button_create(self):        
        context = dict(self._context or {})
        total_qty = 0        
        pickings = self.env['stock.picking'].browse(context.get('active_ids'))
        for pick in pickings:
            for pack in pick.pack_operation_ids:
                total_qty += pack.product_qty

        for pick in pickings:
	    picking_list = self.env['lea.picking.list'].create({
                                                            'date': fields.Date.today(),
                                                            'gate_id': self.gate_id.id,
                                                            'picker_id': self.picker_id.id,
							    'picking_id': pick.id
                                                            })

            for pack in pick.pack_operation_ids:
                remaining_qty = pack.product_qty   
                rack_stock_ids = self.env['lea.product.column'].search([('reference','=',pack.product_id.id),('type','=','Stock')])                     

		for rack in pack.product_id.rack_ids:
                    if rack.type == "Stock":
                         if remaining_qty > 0:                        
                             if rack.available_stock >= remaining_qty:
                                                                                              
               self.env['lea.picking.list.line'].create({
                                                          'reference': picking_list.id,
                                                          'rack_id': False,
                                                          'product_id': pack.product_id.id,
                                                          'qty': pack.product_qty,
                                                          'qty_scan': pack.product_qty,
                                                          'delivery_id': pick.id,                                                          
                                                          })                            
                #===============================================================
                #             else:
                #                 self.env['lea.picking.list.line'].create({
                #                                                           'reference': picking_list.id,
                #                                                           'rack_id': rack.id,
                #                                                           'product_id': pack.product_id.id,
                #                                                           'qty': rack.available_stock,
                #                                                           'delivery_id': pick.id,                                                          
                #                                                           })                     
                #                 
                #                 remaining_qty = pack.product_qty - rack.available_stock
                # 
                # rack_reserved_ids = self.env['lea.product.column'].search([('reference','=',pack.product_id.id),('type','=','Reserved')])                     
                # for rack in pack.product_id.rack_ids:
                #     if rack.type == "Reserved":
                #         if remaining_qty > 0:                        
                #             if rack.available_stock >= remaining_qty:                                                                                             
                #                 self.env['lea.picking.list.line'].create({
                #                                                           'reference': picking_list.id,
                #                                                           'rack_id': rack.id,
                #                                                           'product_id': pack.product_id.id,
                #                                                           'qty': remaining_qty,
                #                                                           'delivery_id': pick.id,                                                          
                #                                                           })                            
                #             else:
                #                 self.env['lea.picking.list.line'].create({
                #                                                           'reference': picking_list.id,
                #                                                           'rack_id': rack.id,
                #                                                           'product_id': pack.product_id.id,
                #                                                           'qty': rack.available_stock,
                #                                                           'delivery_id': pick.id,                                                          
                #                                                           })                     
                #                 remaining_qty = remaining_qty - rack.available_stock
                #===============================================================
                                                        
                
                current_product = self.env['lea.picking.list.summary'].search([('reference','=',picking_list.id),('product_id','=',pack.product_id.id)])
                qty = 0
                if not current_product:
                    self.env['lea.picking.list.summary'].create({
                                                                 'reference': picking_list.id,                                                          
                                                                 'product_id': pack.product_id.id,
                                                                 'qty': pack.product_qty,                                                                                                            
                                                                 })
                else:
                    qty = current_product[0].qty
                    current_product[0].write({
                                              'qty': qty + pack.product_qty
                                              })
        
        for pick in pickings:
            pick.write({
                        'is_picking_list': True,
                        'picking_list_id': picking_list.id,
                        })
            
        return {'type': 'ir.actions.act_window_close'}
