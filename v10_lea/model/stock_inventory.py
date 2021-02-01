from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re


class StockInventory(models.Model):
    _inherit = 'stock.inventory'
        
    is_putaway = fields.Boolean('Is Putaway')
    putaway_id = fields.Many2one('lea.putaway', 'Putaway No.')
            
    @api.multi
    def create_putaway(self):
        for res in self:                    
            putaway_id = self.env['lea.putaway'].create({
                                                         'type': 'Adjustment',
                                                         'inventory_id': res.id,
                                                         'date': fields.Date.today(),
                                                         })
            
            for line in res.move_ids:                
                available_space = 0
                remaining_qty = 0
                if line.product_id.product_tmpl_id.rack_ids:      
                    for column in line.product_id.product_tmpl_id.rack_ids:                        
                        if column.type == "Stock":                                                                
                            available_space = column.column_id.max_stock - column.column_id.available_stock                            
                            if available_space > 0:
                                if available_space >= line.product_uom_qty: 
                                    self.env['lea.putaway.line'].create({
                                                                       'reference': putaway_id.id,      
                                                                       'column_id': column.column_id.id,                                                               
                                                                       'product_id': line.product_id.id,                                                                                                                                    
                                                                       'qty': line.product_uom_qty,                                                                                                                                                                               
                                                                       })
                                elif available_space < line.product_uom_qty:                                                
                                    self.env['lea.putaway.line'].create({
                                                                       'reference': putaway_id.id,      
                                                                       'column_id': column.column_id.id,                                                               
                                                                       'product_id': line.product_id.id,                                                                                                                                    
                                                                       'qty': available_space,                                                                                                                                                                               
                                                                       })
                                    
                                    remaining_qty = line.product_uom_qty - available_space                
                                                
                    if remaining_qty > 0:                        
                        available_space = 0                               
                        for column in line.product_id.product_tmpl_id.rack_ids:                    
                            if column.type == "Reserved":                                                                                            
                                available_space = column.column_id.max_stock - column.column_id.available_stock                                            
                                if available_space > 0:
                                    if available_space >= remaining_qty: 
                                        self.env['lea.putaway.line'].create({
                                                                           'reference': putaway_id.id,      
                                                                           'column_id': column.column_id.id,                                                               
                                                                           'product_id': line.product_id.id,                                                                                                                                    
                                                                           'qty': remaining_qty,                                                                                                                                                                               
                                                                           })
                                    elif available_space < remaining_qty:                                                
                                        self.env['lea.putaway.line'].create({
                                                                             'reference': putaway_id.id,      
                                                                             'column_id': column.column_id.id,                                                               
                                                                             'product_id': line.product_id.id,                                                                                                                                    
                                                                             'qty': available_space,                                                                                                                                                                               
                                                                             })
                                        
                                        remaining_qty = remaining_qty - available_space
                                        
            if putaway_id:
                res.is_putaway = True
                res.putaway_id = putaway_id.id
                
                      
