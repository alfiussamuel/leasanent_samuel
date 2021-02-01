# coding: utf-8
from datetime import datetime
from odoo import models, fields, api


class CreateReplenishmentWizard(models.TransientModel):
    _name = "create.replenishment.wizard"
    _description = "Create Replenishment Wizard"

    rack_id = fields.Many2one('lea.rack')
    level_id = fields.Many2one('lea.rack.level')
    product_category_id = fields.Many2one('product.category', 'Article Code')
    product_id = fields.Many2one('product.product', 'Barcode') 
        
    @api.multi
    def create_replenishment(self):
        for res in self:
            replenishment_id = self.env['lea.replenishment'].create({
                                                                     'date': fields.Date.today()
                                                                     })
                        
            if res.product_id:
                reserved_column_ids = self.env['lea.rack.level.column'].search([
                                                                                ('level_id.type','=','Stock'),                                                                                    
                                                                                ('product_id','=',res.product_id.id),
                                                                                ])
            
            elif res.product_category_id:
                reserved_column_ids = self.env['lea.rack.level.column'].search([
                                                                                ('level_id.type','=','Stock'),                                                                                    
                                                                                ('product_id.categ_id','=',res.product_category_id.id),
                                                                                ])                                                            
            elif res.rack_id:
                if res.level_id:
                    reserved_column_ids = self.env['lea.rack.level.column'].search([
                                                                                    ('level_id.type','=','Stock'),
                                                                                    ('level_id.rack_id','=',res.rack_id.id),
                                                                                    ('level_id','=',res.level_id.id)
                                                                                    ])                                
                else:
                    reserved_column_ids = self.env['lea.rack.level.column'].search([('level_id.type','=','Stock'),('level_id.rack_id','=',res.rack_id.id)])
            else:
                reserved_column_ids = self.env['lea.rack.level.column'].search([('level_id.type','=','Stock')])            
                    
            for column in reserved_column_ids:
                if column.product_id:
                    replenishment_qty = 0
                    print "Column ", column.name
                    print "Available Stock ", column.available_stock
                    print "Min Stock ", column.min_stock                    
                    if column.available_stock <= column.min_stock:
                        replenishment_qty = column.max_stock - column.available_stock
                        print "Replenishment Qty ", replenishment_qty
                        reserved_column_id = self.env['lea.rack.level.column'].search([('level_id.type','=','Reserved'),('product_id','=',column.product_id.id)])                        
                        if reserved_column_id and reserved_column_id[0].available_stock > 0:                        
                            print "Reserved Column ", reserved_column_id[0].name
                            if reserved_column_id[0].available_stock >= replenishment_qty:                             
                                self.env['lea.replenishment.line'].create({
                                                                           'reference': replenishment_id.id,
                                                                           'product_id': column.product_id.id,
                                                                           'column_from': reserved_column_id[0].id,
                                                                           'column_to': column.id,
                                                                           'qty': replenishment_qty,                                                  
                                                                           })
                            elif reserved_column_id[0].available_stock < replenishment_qty:                             
                                self.env['lea.replenishment.line'].create({
                                                                           'reference': replenishment_id.id,
                                                                           'product_id': column.product_id.id,
                                                                           'column_from': reserved_column_id[0].id,
                                                                           'column_to': column.id,
                                                                           'qty': reserved_column_id[0].available_stock,                                                  
                                                                           })
                            
        return {'type': 'ir.actions.act_window_close'}

