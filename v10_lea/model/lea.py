from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re

class LeaTransferLine(models.Model):
    _name = 'lea.transfer.line'
            
    reference = fields.Many2one('lea.transfer', 'Reference')    
    product_id = fields.Many2one('product.product', 'Barcode')
    column_from = fields.Many2one('lea.rack.level.column', 'From')
    column_to = fields.Many2one('lea.rack.level.column', 'To')
    qty = fields.Float('Qty', digits=dp.get_precision('Product Unit of Measure'))
    
class LeaTransfer(models.Model):
    _name = 'lea.transfer'
            
    name = fields.Char('Transfer No.')    
    date = fields.Date('Transfer Date')    
    line_ids = fields.One2many('lea.transfer.line', 'reference', 'Lines')
    state = fields.Selection([
        ('Draft','Draft'),
        ('Done','Done')],
        string='Status', default='Draft')

    @api.multi
    def button_draft(self):
        for res in self:
            if res.line_ids:
                for line in res.line_ids:
                    if line.product_id == line.column_to.product_id and line.column_to.available_stock >= line.qty:
                        self.env['lea.rack.level.column.detail'].create({
                           'reference': line.column_from.id,
                           'qty': line.qty,
                           'type': "Incoming",
                           'date': fields.Date.today(),
                        })

                        # Create Incoming for Destination Column
                        self.env['lea.rack.level.column.detail'].create({
                           'reference': line.column_to.id,
                           'qty': line.qty,
                           'type': "Outgoing",
                           'date': fields.Date.today(),
                        })

                        res.state = "Draft"
        
    @api.multi
    def button_done(self):
        for res in self:
            if res.line_ids:
                for line in res.line_ids:
                    if line.product_id == line.column_from.product_id and line.column_from.available_stock >= line.qty:
                        if line.column_to.product_id:
                            raise Warning('Destionation Location already assigned to another Products')   

                        # Create Outgoing for Source Column
                        self.env['lea.rack.level.column.detail'].create({
                           'reference': line.column_from.id,
                           'qty': line.qty,
                           'type': "Outgoing",
                           'date': fields.Date.today(),
                        })

                        # Create Incoming for Destination Column
                        self.env['lea.rack.level.column.detail'].create({
                           'reference': line.column_to.id,
                           'qty': line.qty,
                           'type': "Incoming",
                           'date': fields.Date.today(),
                        })

                        line.column_to.product_id = line.product_id.id
                        res.state = "Done"

                    else:
                        raise Warning('Product are note available in Source Location')            
                
    @api.model
    def create(self, vals):        
        vals['name'] = self.env['ir.sequence'].next_by_code('lea.transfer') or '/'
        return super(LeaTransfer, self).create(vals)
    
class LeaProductColumn(models.Model):
    _name = 'lea.product.column'
        
    reference = fields.Many2one('product.template', 'Reference')        
    column_id = fields.Many2one('lea.rack.level.column', 'Rack')
    type = fields.Char('Type')    
    available_stock = fields.Integer(related='column_id.available_stock', string='Available Stock', digits=dp.get_precision('Product Unit of Measure'))

class LeaProductRack(models.Model):
    _name = 'lea.product.rack'
        
    reference = fields.Many2one('product.template', 'Reference')
    column_id = fields.Many2one('lea.rack.level.column', 'Rack')
    type = fields.Char('Type')    
    available_stock = fields.Integer(related='column_id.available_stock', string='Available Stock', digits=dp.get_precision('Product Unit of Measure'))
    
class LeaPutawayDetail(models.Model):
    _name = 'lea.putaway.detail'
    _order = "product_id asc"
        
    reference = fields.Many2one('lea.putaway', 'Reference')    
    product_id = fields.Many2one('product.product', 'Barcode')
    column_id = fields.Many2one('lea.rack.level.column', 'Rack')
    qty = fields.Float('Qty', digits=dp.get_precision('Product Unit of Measure'))        
    
        
class LeaPutaway(models.Model):
    _name = 'lea.putaway'
    
    name = fields.Char('Putaway No.')  
    date = fields.Date('Created Date')  
    type = fields.Selection([('Receipt','Receipt'),('Adjustment','Adjustment')])
    picking_id = fields.Many2one('stock.picking', 'Receipt No.')
    location_id = fields.Many2one(compute="_get_detail", comodel_name='stock.location', string='Source Location')
    partner_id = fields.Many2one(compute="_get_detail", comodel_name='res.partner', string='Supplier')
    inventory_id = fields.Many2one('stock.inventory', 'Adjustment No.')    
    line_ids = fields.One2many('lea.putaway.detail', 'reference', 'Lines')
    state = fields.Selection([
        ('Draft','Draft'),
        ('Progress','Progress'),
        ('Done','Done')],
        string='Status', default='Draft')

    total_qty = fields.Integer(compute='_get_total_qty', string='Total Qty', digits=dp.get_precision('Product Unit of Measure'))
    
    @api.depends('line_ids.qty')
    def _get_total_qty(self):
        for res in self:
            total_qty = 0
            for line in res.line_ids:
                total_qty += line.qty 
            res.total_qty = total_qty

    @api.depends('picking_id')
    def _get_detail(self):
        for res in self:
            if res.picking_id:
                res.location_id = res.picking_id.location_id.id
                res.partner_id = res.picking_id.partner_id.id

    @api.multi
    def button_cancel(self):
        for res in self:                            
            created_lines = self.env['lea.rack.level.column.detail'].search([('putaway_id','=',res.id)])
            if created_lines:
                for line in created_lines:
                    line.unlink()
            res.state = "Draft"
                
    @api.multi
    def button_confirm(self):
        self.state = "Progress"
        
    @api.multi
    def button_done(self):
        for res in self:
            for line in res.line_ids:
                self.env['lea.rack.level.column.detail'].create({
                   'reference': line.column_id.id,
                   'qty': line.qty,
                   'type': "Putaway",
                   'date': fields.Date.today(),
                   'putaway_id': res.id,
                   'putaway_line_id': line.id,
                })

            res.state = "Done"
                
    @api.model
    def create(self, vals):        
        vals['name'] = self.env['ir.sequence'].next_by_code('lea.putaway') or '/'
        return super(LeaPutaway, self).create(vals)
    
        
class LeaPackingListLine(models.Model):
    _name = 'lea.packing.list.line'
        
    reference = fields.Many2one('lea.packing.list', 'Reference')    
    product_id = fields.Many2one('product.product', 'Barcode')
    qty_picked = fields.Integer('Qty Picked', digits=dp.get_precision('Product Unit of Measure'))
    qty_remaining = fields.Integer('Remaining Qty', digits=dp.get_precision('Product Unit of Measure'))
    qty_packed = fields.Integer('Qty Packed Scan', digits=dp.get_precision('Product Unit of Measure'))
    coli = fields.Char('Coli No.')
    

class LeaPackingListBoxProduct(models.Model):
    _name = 'lea.packing.list.box.product'
        
    reference = fields.Many2one('lea.packing.list.box', 'Reference')
    product_id = fields.Many2one('product.product', 'Barcode')
    categ_id = fields.Many2one('product.category', 'Article')            
    qty = fields.Integer('Quantity')
    total_qty = fields.Integer(compute="_get_total_qty", string='Total Qty')    
    qty_al = fields.Char('AL')
    qty_xs = fields.Char('XS')
    qty_s = fields.Char('S')
    qty_m = fields.Char('M')
    qty_l = fields.Char('L')
    qty_xl = fields.Char('XL')
    qty_x = fields.Char('X')
    qty_y = fields.Char('Y')
    qty_z = fields.Char('Z')
    qty_25 = fields.Char('25')
    qty_26 = fields.Char('26')
    qty_27 = fields.Char('27')
    qty_28 = fields.Char('28')
    qty_29 = fields.Char('29')
    qty_30 = fields.Char('30')
    qty_31 = fields.Char('31')
    qty_32 = fields.Char('32')
    qty_33 = fields.Char('33')
    qty_34 = fields.Char('34')
    qty_35 = fields.Char('35')
    qty_36 = fields.Char('36')
    qty_38 = fields.Char('38')
    qty_40 = fields.Char('40')
    qty_42 = fields.Char('42')
    
    @api.depends('qty_al','qty_xs','qty_s','qty_m','qty_l','qty_xl','qty_x','qty_y','qty_z','qty_25','qty_26','qty_27','qty_28','qty_29','qty_30','qty_31','qty_32','qty_33','qty_34','qty_35','qty_36','qty_38','qty_40','qty_42',)
    def _get_total_qty(self):
        for res in self:
            total_product = 0
            if res.qty_al != '':
                total_product += int(res.qty_al)
            if res.qty_xs != '':
                total_product += int(res.qty_xs)
            if res.qty_s != '':
                total_product += int(res.qty_s)
            if res.qty_m != '':
                total_product += int(res.qty_m)
            if res.qty_l != '':
                total_product += int(res.qty_l)
            if res.qty_xl != '':
                total_product += int(res.qty_xl)
            if res.qty_x != '':
                total_product += int(res.qty_x)
            if res.qty_y != '':
                total_product += int(res.qty_y)
            if res.qty_z != '':
                total_product += int(res.qty_z)
            if res.qty_25 != '':
                total_product += int(res.qty_25)
            if res.qty_26 != '':
                total_product += int(res.qty_26)
            if res.qty_27 != '':
                total_product += int(res.qty_27)
            if res.qty_28 != '':
                total_product += int(res.qty_28)
            if res.qty_29 != '':
                total_product += int(res.qty_29)
            if res.qty_30 != '':
                total_product += int(res.qty_30)
            if res.qty_31 != '':
                total_product += int(res.qty_31)
            if res.qty_32 != '':
                total_product += int(res.qty_32)
            if res.qty_33 != '':
                total_product += int(res.qty_33)
            if res.qty_34 != '':
                total_product += int(res.qty_34)
            if res.qty_35 != '':
                total_product += int(res.qty_35)
            if res.qty_36 != '':
                total_product += int(res.qty_36)
            if res.qty_38 != '':
                total_product += int(res.qty_38)
            if res.qty_40 != '':
                total_product += int(res.qty_40)
            if res.qty_42 != '':
                total_product += int(res.qty_42)

            res.total_qty = total_product   
        
class LeaPackingListBox(models.Model):
    _name = 'lea.packing.list.box'
    _order = 'coli asc'
        
    reference = fields.Many2one('lea.packing.list', 'Reference')            
    coli = fields.Char('Coli No.')
    total_qty = fields.Integer(compute="_get_total_qty", string='Total Qty', digits=dp.get_precision('Product Unit of Measure'))
    weight = fields.Float('Weight (Kg)')    
    product_ids = fields.One2many('lea.packing.list.box.product', 'reference', 'Products')
    
    @api.depends('product_ids')
    def _get_total_qty(self):
        for res in self:
            total_qty = 0
            if res.product_ids:
                total_qty = 0
                for line in res.product_ids:
                    total_qty += line.total_qty
    
            res.total_qty = total_qty
            
    @api.multi
    def unlink(self):
        for res in self:
            for product in res.product_ids:
                line = self.env['lea.packing.list.line'].search([
                    ('reference','=',res.reference.id),
                    ('product_id','=',product.product_id.id)
                ])

                if line:
                    line.qty_remaining += product.qty                                        
                                    
        return super(LeaPackingListBox, self).unlink()
                
class LeaPackingList(models.Model):
    _name = 'lea.packing.list'
    
    name = fields.Char('Packing No.')
    date = fields.Date('Packing Date')
    coli = fields.Char('Coli')
    barcode = fields.Char('Scan Barcode')    
    picking_id = fields.Many2one('stock.picking', 'DO No.')
    picking_date = fields.Date('DO Date')
    sale_id = fields.Many2one('sale.order', 'SO No.')
    sale_date = fields.Date('SO Date')
    partner_id = fields.Many2one('res.partner', 'Customer')    
    line_ids = fields.One2many('lea.packing.list.line', 'reference', 'Lines')
    coli_ids = fields.One2many('lea.packing.list.box', 'reference', 'Summary per Coli')
    coli_qty = fields.Integer(compute="_get_coli_qty", string="Qty Coli")
    total_scanned = fields.Integer("Total Scanned")
    total_qty_coli = fields.Integer("Total Qty Coli")
    total_weight = fields.Float(compute="_get_total_weight", string="Total Weight", digits=dp.get_precision('OneDecimal'))   
    total_picked = fields.Integer(compute='_get_total_picked', string='Total Picked Qty', digits=dp.get_precision('Product Unit of Measure'))
    total_packed = fields.Integer(compute='_get_total_packed', string='Total Packed Qty', digits=dp.get_precision('Product Unit of Measure'))
    total_coli = fields.Integer(compute='_get_total_coli', string='Total Coli', digits=dp.get_precision('Product Unit of Measure'))
    total_article = fields.Integer(compute='_get_total_article', string='Total Article', digits=dp.get_precision('Product Unit of Measure'))
    state = fields.Selection([('Draft','Draft'),('Done','Done')], string='Status', default='Draft')

    @api.onchange('coli')
    def onchange_coli(self):
        for res in self:
            if res.coli:
                res.total_qty_coli = res.coli_qty
            else:
                res.total_qty_coli = 0
    
    @api.depends('coli')
    def _get_coli_qty(self):
        for res in self:
            total = 0
            for coli in res.coli_ids:
                if coli.coli == res.coli:
                    total = coli.total_qty                    
            res.coli_qty = total
            
    @api.depends('coli_ids')
    def _get_total_weight(self):
        for res in self:
            total_weight = 0
            for line in res.coli_ids:
                total_weight += line.weight
            res.total_weight = total_weight
            
    @api.depends('line_ids.qty_picked')
    def _get_total_picked(self):
        for res in self:
            total_picked = 0
            for line in res.line_ids:
                total_picked += line.qty_picked
            res.total_picked = total_picked
            
    @api.depends('line_ids')
    def _get_total_article(self):
        for res in self:            
            article_ids = []
            for line in res.line_ids:
                if line.qty_remaining != line.qty_picked:
                    if line.product_id.categ_id.id not in article_ids:                    
                        article_ids.append(line.product_id.categ_id.id)            
            res.total_article = len(article_ids)            
            
    @api.depends('line_ids.qty_picked', 'line_ids.qty_remaining')
    def _get_total_packed(self):
        for res in self:
            total_packed = 0
            for line in res.line_ids:
                total_packed += (line.qty_picked - line.qty_remaining)
            res.total_packed = total_packed

    @api.depends('coli_ids')
    def _get_total_coli(self):
        for res in self:
            total_coli = 0
            if res.coli_ids:
                total_coli = len(res.coli_ids)            
            res.total_coli = total_coli
            
    @api.onchange('barcode')
    def barcode_scanning(self):
        match = False
        product_obj = self.env['product.product']
        product_id = product_obj.search([('barcode', '=', self.barcode)])        
        coli_ids = []
        value = {}
                
        if not self.coli and self.barcode:
            self.barcode = False
            return {'warning': {
                    'title': "Warning",
                    'message': "Please Input Coli Number",
                    }
                }    
            
        if self.barcode and not product_id:
            self.barcode = False
            return {'warning': {
                    'title': "Warning",
                    'message': "No product is available for this barcode",
                    }
                }    
                    
        if self.barcode and self.line_ids:            
            for line in self.line_ids:
                if line.product_id.barcode == self.barcode:
                    if line.qty_remaining == 0:
                        self.barcode = False
                        return {'warning': {
                            'title': "Warning",
                            'message': "Cannot Scan more than Qty",
                            }
                        }                        
                    else: 
                        line.qty_packed += 1      
                        line.qty_remaining -= 1
                        self.total_scanned += 1  
                        self.total_qty_coli += 1                                                                                                                                                    
                        self.barcode = False                        
                        match = True
                        
        if self.barcode and not match:
            self.barcode = False
            if product_id:
                return {'warning': {
                    'title': "Warning",
                    'message': "This product is not available in the order.",
                    }
                }            
                                                
        return {'value':value}    
                                
    @api.multi
    def create_coli(self):
        for res in self:
            coli_id = False
            qty_al = 0
            qty_xs = 0
            qty_s = 0
            qty_m = 0
            qty_l = 0
            qty_xl = 0
            qty_x = 0
            qty_y = 0
            qty_z = 0
            qty_25 = 0
            qty_26 = 0
            qty_27 = 0
            qty_28 = 0
            qty_29 = 0
            qty_30 = 0
            qty_31 = 0
            qty_32 = 0
            qty_33 = 0
            qty_34 = 0
            qty_35 = 0
            qty_36 = 0
            qty_38 = 0
            qty_40 = 0
            qty_42 = 0
            
            str_qty_al = ''
            str_qty_xs = ''
            str_qty_s = ''
            str_qty_m = ''
            str_qty_l = ''
            str_qty_xl = ''
            str_qty_x = ''
            str_qty_y = ''
            str_qty_z = ''
            str_qty_25 = ''
            str_qty_26 = ''
            str_qty_27 = ''
            str_qty_28 = ''
            str_qty_29 = ''
            str_qty_30 = ''
            str_qty_31 = ''
            str_qty_32 = ''
            str_qty_33 = ''
            str_qty_34 = ''
            str_qty_35 = ''
            str_qty_36 = ''
            str_qty_38 = ''
            str_qty_40 = ''
            str_qty_42 = ''  
                                                                              
            if not res.coli:
                raise Warning('Please Input Coli Number')
            elif res.coli:
                current_coli = self.env['lea.packing.list.box'].search([
                    ('coli','=',res.coli),
                    ('reference','=',res.id)
                ])

                if current_coli:
                    coli_id = current_coli[0]                    
                else:
                    coli_id = self.env['lea.packing.list.box'].create({
                        'reference': res.id,
                        'coli': res.coli,                                                                                                          
                    })
                
                for line in res.line_ids:
                    if line.qty_packed > 0:
                        qty = 0
                        current_product = self.env['lea.packing.list.box.product'].search([
                            ('categ_id','=',line.product_id.categ_id.id),
                            ('reference.reference','=',res.id),
                            ('reference','=',coli_id.id)
                        ])

                        if current_product:
                            if line.product_id.product_size_id.name == "AL":
                                qty = current_product[0].qty_al           
                                current_product[0].write({'qty_al' : (qty or 0) + line.qty_packed})                           
                            elif line.product_id.product_size_id.name == "XS":
                                qty = current_product[0].qty_xs
                                current_product[0].write({'qty_xs' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "S":
                                qty = current_product[0].qty_s
                                current_product[0].write({'qty_s' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "M":
                                qty = current_product[0].qty_m                                
                                current_product[0].write({'qty_m' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "L":
                                qty = current_product[0].qty_l
                                current_product[0].write({'qty_l' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "XL":
                                qty = current_product[0].qty_xl
                                current_product[0].write({'qty_xl' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "X":
                                qty = current_product[0].qty_x
                                current_product[0].write({'qty_x' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "Y":
                                qty = current_product[0].qty_y
                                current_product[0].write({'qty_y' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "Z":
                                qty = current_product[0].qty_z
                                current_product[0].write({'qty_z' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "25":
                                qty = current_product[0].qty_25
                                current_product[0].write({'qty_25' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "26":
                                qty = current_product[0].qty_26
                                current_product[0].write({'qty_26' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "27":
                                qty = current_product[0].qty_27
                                current_product[0].write({'qty_27' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "28":
                                qty = current_product[0].qty_28
                                current_product[0].write({'qty_28' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "29":
                                qty = current_product[0].qty_29
                                current_product[0].write({'qty_29' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "30":
                                qty = current_product[0].qty_30
                                current_product[0].write({'qty_30' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "31":
                                qty = current_product[0].qty_31
                                current_product[0].write({'qty_31' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "32":
                                qty = current_product[0].qty_32
                                current_product[0].write({'qty_32' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "33":
                                qty = current_product[0].qty_33
                                current_product[0].write({'qty_33' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "34":
                                qty = current_product[0].qty_34
                                current_product[0].write({'qty_34' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "35":
                                qty = current_product[0].qty_35
                                current_product[0].write({'qty_35' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "36":
                                qty = current_product[0].qty_36
                                current_product[0].write({'qty_36' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "38":
                                qty = current_product[0].qty_38
                                current_product[0].write({'qty_38' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "40":
                                qty = current_product[0].qty_40
                                current_product[0].write({'qty_40' : (qty or 0) + line.qty_packed})
                            elif line.product_id.product_size_id.name == "42":
                                qty = current_product[0].qty_42                             
                                current_product[0].write({'qty_42' : (qty or 0) + line.qty_packed})                                                                                                                                     
                        else:
                            if line.product_id.product_size_id.name == "AL":
                                qty_al += line.qty_packed
                            elif line.product_id.product_size_id.name == "XS":
                                qty_xs += line.qty_packed
                            elif line.product_id.product_size_id.name == "S":
                                qty_s += line.qty_packed
                            elif line.product_id.product_size_id.name == "M":
                                qty_m += line.qty_packed
                            elif line.product_id.product_size_id.name == "L":
                                qty_l += line.qty_packed
                            elif line.product_id.product_size_id.name == "XL":
                                qty_xl += line.qty_packed
                            elif line.product_id.product_size_id.name == "X":
                                qty_x += line.qty_packed
                            elif line.product_id.product_size_id.name == "Y":
                                qty_y += line.qty_packed
                            elif line.product_id.product_size_id.name == "Z":
                                qty_z += line.qty_packed
                            elif line.product_id.product_size_id.name == "25":
                                qty_25 += line.qty_packed
                            elif line.product_id.product_size_id.name == "26":
                                qty_26 += line.qty_packed
                            elif line.product_id.product_size_id.name == "27":
                                qty_27 += line.qty_packed
                            elif line.product_id.product_size_id.name == "28":
                                qty_28 += line.qty_packed
                            elif line.product_id.product_size_id.name == "29":
                                qty_29 += line.qty_packed
                            elif line.product_id.product_size_id.name == "30":
                                qty_30 += line.qty_packed
                            elif line.product_id.product_size_id.name == "31":
                                qty_31 += line.qty_packed
                            elif line.product_id.product_size_id.name == "32":
                                qty_32 += line.qty_packed
                            elif line.product_id.product_size_id.name == "33":
                                qty_33 += line.qty_packed
                            elif line.product_id.product_size_id.name == "34":
                                qty_34 += line.qty_packed
                            elif line.product_id.product_size_id.name == "35":
                                qty_35 += line.qty_packed
                            elif line.product_id.product_size_id.name == "36":
                                qty_36 += line.qty_packed
                            elif line.product_id.product_size_id.name == "38":
                                qty_38 += line.qty_packed
                            elif line.product_id.product_size_id.name == "40":
                                qty_40 += line.qty_packed
                            elif line.product_id.product_size_id.name == "42":
                                qty_42 += line.qty_packed
                            
                            if qty_al > 0:
                                str_qty_al = str(qty_al)
                            elif qty_xs > 0:
                                str_qty_xs = str(qty_xs)
                            elif qty_s > 0:
                                str_qty_s = str(qty_s)
                            elif qty_m > 0:
                                str_qty_m = str(qty_m)
                            elif qty_l > 0:
                                str_qty_l = str(qty_l)
                            elif qty_xl > 0:
                                str_qty_xl = str(qty_xl)
                            elif qty_x > 0:
                                str_qty_x = str(qty_x)
                            elif qty_y > 0:
                                str_qty_y = str(qty_y)
                            elif qty_z > 0:
                                str_qty_z = str(qty_z)
                            elif qty_25 > 0:
                                str_qty_25 = str(qty_25)
                            elif qty_26 > 0:
                                str_qty_26 = str(qty_26)
                            elif qty_27 > 0:
                                str_qty_27 = str(qty_27)
                            elif qty_28 > 0:
                                str_qty_28 = str(qty_28)
                            elif qty_29 > 0:
                                str_qty_29 = str(qty_29)
                            elif qty_30 > 0:
                                str_qty_30 = str(qty_30)
                            elif qty_31 > 0:
                                str_qty_31 = str(qty_31)
                            elif qty_32 > 0:
                                str_qty_32 = str(qty_32)
                            elif qty_33 > 0:
                                str_qty_33 = str(qty_33)
                            elif qty_34 > 0:
                                str_qty_34 = str(qty_34)
                            elif qty_35 > 0:
                                str_qty_35 = str(qty_35)
                            elif qty_36 > 0:
                                str_qty_36 = str(qty_36)
                            elif qty_38 > 0:
                                str_qty_38 = str(qty_38)
                            elif qty_40 > 0:
                                str_qty_40 = str(qty_40)
                            elif qty_42 > 0:
                                str_qty_42 = str(qty_42)
                                
                            self.env['lea.packing.list.box.product'].create({
                                  'reference': coli_id.id,
                                  'categ_id': line.product_id.categ_id.id,
                                  'qty': line.qty_packed,
                                  'qty_al': str_qty_al,
                                  'qty_xs': str_qty_xs,
                                  'qty_s': str_qty_s,
                                  'qty_m': str_qty_m,
                                  'qty_l': str_qty_l,
                                  'qty_xl': str_qty_xl,
                                  'qty_x': str_qty_x,
                                  'qty_y': str_qty_y,
                                  'qty_z': str_qty_z,
                                  'qty_25': str_qty_25,
                                  'qty_26': str_qty_26,
                                  'qty_27': str_qty_27,
                                  'qty_28': str_qty_28,
                                  'qty_29': str_qty_29,
                                  'qty_30': str_qty_30,
                                  'qty_31': str_qty_31,
                                  'qty_32': str_qty_32,
                                  'qty_33': str_qty_33,
                                  'qty_34': str_qty_34,
                                  'qty_35': str_qty_35,
                                  'qty_36': str_qty_36,
                                  'qty_38': str_qty_38,
                                  'qty_40': str_qty_40,
                                  'qty_42': str_qty_42,
                            })
                    
                    line.qty_packed = 0
                    
                res.coli = False       
                res.total_scanned = 0
                res.total_qty_coli = 0                
        
    @api.multi
    def button_done(self):
        for res in self:
            if res.total_packed != res.total_picked:
                raise Warning('Total Picked Qty and Packed Qty need to be same')
            res.state = 'Done'
            
    @api.multi
    def button_draft(self):
        for res in self:
            res.state = 'Draft'
            
    @api.multi
    def unlink(self):
        for res in self:
            if res.state == "Done":
                raise Warning('Cannot delete Packing List which already in Done State')
            else:                                        
                res.picking_id.write({
                    'is_packing_list': False,
                    'packing_list_id': False,
                })
                                    
        return super(LeaPackingList, self).unlink()
            
    @api.model
    def create(self, vals):        
        vals['name'] = self.env['ir.sequence'].next_by_code('lea.packing.list') or '/'
        return super(LeaPackingList, self).create(vals)
                
            
class LeaPickingList(models.Model):
    _name = 'lea.picking.list'
    
    name = fields.Char('Picking List No.')
    barcode = fields.Char('Scan Barcode')
    barcode_summary = fields.Char('Scan Barcode')
    message = fields.Text('Error Message')
    date = fields.Date('Date')
    warehouse_id = fields.Many2one('stock.warehouse', compute="_get_warehouse_id", string='Warehouse')
    location_id = fields.Many2one('stock.location', compute="_get_location_id", string='Location')
    gate_id = fields.Many2one('lea.gate', 'Gate')
    picker_id = fields.Many2one('lea.picker', 'Picker')
    picking_id = fields.Many2one('stock.picking', 'DO Document')
    partner_id = fields.Many2one(related='picking_id.partner_id', comodel_name='res.partner', string='Customer/Toko')
    total_do = fields.Integer(compute='_get_total_do', string='Total DO', digits=dp.get_precision('Product Unit of Measure'))
    total_picked = fields.Integer(compute='_get_total_picked', string='Total Picked', digits=dp.get_precision('Product Unit of Measure'))
    line_ids = fields.One2many('lea.picking.list.line', 'reference', 'Lines')
    summary_ids = fields.One2many('lea.picking.list.summary', 'reference', 'Summary')
    state = fields.Selection([('Draft','Draft'),('Done','Done')], string='Status', default='Draft')

    total_qty = fields.Integer(compute='_get_total_qty', string='Total Qty', digits=dp.get_precision('Product Unit of Measure'))

    @api.depends('line_ids.qty')
    def _get_total_qty(self):
        for res in self:
            total_qty = 0
            for line in res.line_ids:
                total_qty += line.qty 
            res.total_qty = total_qty


    @api.onchange('barcode','barcode_summary')
    def barcode_scanning(self):
        match = False
        product_obj = self.env['product.product']
        product_id = product_obj.search([('barcode', '=', self.barcode)])
        if self.barcode and not product_id:
            self.barcode = False
            return {'warning': {
                    'title': "Warning",
                    'message': "No product is available for this barcode",
                    }
                }            
        if self.barcode and self.line_ids:
            for line in self.line_ids:
                if line.product_id.barcode == self.barcode:
                    if line.qty_scan == line.qty:
                        self.barcode = False
                        return {'warning': {
                            'title': "Warning",
                            'message': "Cannot Scan more than Qty",
                            }
                        }                        
                    else: 
                        line.qty_scan += 1
                        self.barcode = False
                        self.message = False
                        match = True
        if self.barcode and not match:
            self.barcode = False
            if product_id:
                return {'warning': {
                    'title': "Warning",
                    'message': "This product is not available in the order.",
                    }
                }            
                
    @api.depends('gate_id')
    def _get_warehouse_id(self):
        for res in self:
            if res.gate_id:                        
                res.warehouse_id = res.gate_id.warehouse_id.id
                
    @api.depends('gate_id')
    def _get_location_id(self):
        for res in self:
            if res.gate_id:                        
                res.location_id = res.gate_id.location_id.id
                        
    @api.depends('line_ids.qty_scan')
    def _get_total_picked(self):
        for res in self:
            total_picked = 0
            for line in res.line_ids:
                total_picked += line.qty_scan
            res.total_picked = total_picked            
            
    @api.depends('line_ids')
    def _get_total_do(self):
        for res in self:
            do_ids = []
            total_do = 0
            for line in res.line_ids:
                if line.delivery_id.id not in do_ids:
                    do_ids.append(line.delivery_id.id)
                    total_do += 1 
            res.total_do = total_do

    @api.multi
    def button_done(self):
        for res in self:     
            if res.total_picked > res.total_qty:
                raise Warning('Qty Picked cannot more than Qty Order')
            
            for line in res.line_ids:
                self.env['lea.rack.level.column.detail'].create({
                   'reference': line.rack_id.id,
                   'qty': line.qty_scan,
                   'type': "Outgoing",
                   'date': fields.Date.today(),
                   # 'putaway_id': res.id,
                   # 'putaway_line_id': line.id,
                })

            res.state = 'Done'
            
    @api.multi
    def button_draft(self):
        for res in self:
            res.state = 'Draft'
    
    @api.multi
    def unlink(self):
        for res in self:
            if res.state == "Done":
                raise Warning('Cannot delete Picking List which already in Done State')
            else:                        
                for line in res.line_ids:
                    line.delivery_id.write({
                        'is_picking_list': False,
                        'picking_list_id': False,
                    })               
                    
                res.line_ids.unlink()            
        return super(LeaPickingList, self).unlink()
    
    @api.model
    def create(self, vals):        
        vals['name'] = self.env['ir.sequence'].next_by_code('lea.picking.list') or '/'
        return super(LeaPickingList, self).create(vals)            


class LeaPickingListLine(models.Model):
    _name = 'lea.picking.list.line'
    _order = 'product_id asc, delivery_id asc'
        
    reference = fields.Many2one('lea.picking.list', 'Reference')
    rack_id = fields.Many2one('lea.rack.level.column', 'Rack')
    product_id = fields.Many2one('product.product', 'Barcode')
    qty = fields.Float('Qty Pick', digits=dp.get_precision('Product Unit of Measure'))
    qty_scan = fields.Float('Qty Scan', digits=dp.get_precision('Product Unit of Measure'))
    delivery_id = fields.Many2one('stock.picking', 'DO No.')
    

class LeaPickingListSummary(models.Model):
    _name = 'lea.picking.list.summary'
    _order = 'product_id asc'
        
    reference = fields.Many2one('lea.picking.list', 'Reference')    
    product_id = fields.Many2one('product.product', 'Barcode')
    qty = fields.Float('Qty Pick', digits=dp.get_precision('Product Unit of Measure'))
    qty_scan = fields.Float('Qty Scan', digits=dp.get_precision('Product Unit of Measure'))    
    
                        
class LeaGate(models.Model):
    _name = 'lea.gate'
    
    name = fields.Char('Gate')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    location_id = fields.Many2one('stock.location', 'Location')
    
    
class LeaPicker(models.Model):
    _name = 'lea.picker'
    
    name = fields.Char('Picker Name')
    
    
class LeaRack(models.Model):
    _name = 'lea.rack'
    
    name = fields.Char('Rack')        

        
class LeaRackLevel(models.Model):
    _name = 'lea.rack.level'
    
    rack_id = fields.Many2one('lea.rack', 'Rack')
    name = fields.Char('Level')
    type = fields.Selection([('Stock','Stock'),('Reserved','Reserved')], string='Type', default='Stock')



    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = []
        if name:
            res = self.search([('name', operator, name)] + args, limit=limit)
        if not res:
            res = self.search([('name', operator, name)] + args, limit=limit)
        return res.name_get()

    @api.multi
    @api.depends('rack_id','name')
    def name_get(self):
        result = []
        for level in self:
            name =  level.rack_id.name + '-' + level.name 
            result.append((level.id, name))
        return result
    

class LeaRackLevelColumn(models.Model):
    _name = 'lea.rack.level.column'
    
    rack_id = fields.Many2one('lea.rack', 'Rack')
    level_id = fields.Many2one('lea.rack.level', 'Level')
    name = fields.Char('Column')
    product_id = fields.Many2one('product.product', 'Product')
    min_stock = fields.Float('Minimum', digits=dp.get_precision('Product Unit of Measure'), defaut=0)
    max_stock = fields.Float('Maximum', digits=dp.get_precision('Product Unit of Measure'), defaut=0)
    type = fields.Char(compute='_get_type', string='Type')
    available_stock = fields.Integer(compute='_get_available_stock', string='Available Stock')
    line_ids = fields.One2many('lea.rack.level.column.detail', 'reference', 'Lines')    

    @api.multi
    def create_column_product(self):
        for res in self:            
            current_id = self.env['lea.product.rack'].search([
                ('reference','=',res.product_id.product_tmpl_id.id),
                ('column_id','=',res.id)
            ])

            if not current_id:
                self.env['lea.product.rack'].create({
                   'reference': res.product_id.product_tmpl_id.id,
                   'column_id': res.id,
                   'type': res.type,
                })
    
    @api.multi
    @api.depends('name','type')
    def name_get(self):
        result = []
        for column in self:
            name =  column.name + ' (' + column.type + ')'
            result.append((column.id, name))
        return result
    
    @api.depends('line_ids.qty')
    def _get_available_stock(self):
        for res in self:
            available_stock = 0
            for line in res.line_ids:                            
                if line.type == "Incoming" or line.type == "Putaway":
                    available_stock += line.qty
                elif line.type == "Outgoing":
                    available_stock -= line.qty
            res.available_stock = available_stock
                
    @api.depends('level_id')
    def _get_type(self):
        for res in self:
            if res.level_id:
                res.type = res.level_id.type                    
    
    @api.onchange('level_id')
    def onchange_level_id(self):
        for res in self:
            if res.level_id:
                name =  res.level_id.rack_id.name + '-' + res.level_id.name + '-'
                res.name = name


    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     result = {}
    #     result['domain'] = {'product_id': [('id', '=', self.product_id.id), ('is_rack', '=', False)]}
    #     return result


class LeaRackLevelColumnDetail(models.Model):
    _name = 'lea.rack.level.column.detail'
    
    reference = fields.Many2one('lea.rack.level.column', 'Reference')
    type = fields.Selection([('Incoming','Incoming'),('Outgoing','Outgoing'),('Putaway','Putaway')], string='Movement Type')
    qty = fields.Integer('Qty')
    date = fields.Date('Date')
    putaway_id = fields.Many2one('lea.putaway', 'Putaway ID')
    putaway_line_id = fields.Many2one('lea.putaway.detail', 'Putaway Line ID')
    mutation_id = fields.Many2one('lea.rack.mutation', 'Mutation No.')
    
            
class LeaRackMutation(models.Model):
    _name = 'lea.rack.mutation'
    
    name = fields.Char('No.')
    picking_id = fields.Many2one('stock.picking', 'Origin')    
    created_by = fields.Many2one('res.users', 'Created by', default=lambda self:self.env.user)
    created_date = fields.Date('Created Date', default=fields.Date.today())
    line_ids = fields.One2many('lea.rack.mutation.line', 'reference', 'Lines')
    state = fields.Selection([('Draft','Draft'),('Confirmed','Confirmed'),('Approved','Approved')], string='Status', default='Draft')
    
    @api.model
    def create(self, vals):        
        vals['name'] = self.env['ir.sequence'].next_by_code('lea.rack.mutation') or '/'
        return super(LeaRackMutation, self).create(vals)

    @api.multi
    def button_confirm(self):
        for res in self:
            for line in res.line_ids:
                if line.column_from.product_id.id == line.product_id.id and line.column_from.available_stock < line.qty:
                    raise Warning('Stock not Available')                    
                if line.column_from.type == "Stock" and line.column_to.type == "Reserved":
                    if line.column_from.product_id.id <> line.product_id.id:
                        raise Warning('Selected Product are not Configured in Selected Source Location')
                elif line.column_from.type == "Reserved" and line.column_to.type == "Stock":
                    if line.column_to.product_id.id <> line.product_id.id:
                        raise Warning('Selected Product are not Configured in Selected Destination Location')
                elif line.column_from.type == "Stock" and line.column_to.type == "Stock":
                    if line.column_from.product_id.id <> line.product_id.id and line.column_to.product_id.id <> line.product_id.id:
                        raise Warning('Selected Product are not Configured in Selected Source/Destination Location')
                               
            res.state = 'Confirmed'
            
    @api.multi
    def button_set_to_draft(self):
        for res in self:                    
            res.state = 'Draft'            
            
    @api.multi
    def button_approve(self):
        for res in self:
            for line in res.line_ids:
                if line.column_from.product_id.id == line.product_id.id and line.column_from.available_stock < line.qty:
                    raise Warning('Stock not Available')         
                
                if line.column_from.available_stock < line.qty:
                    raise Warning('Stock not Available')                    
                if line.column_from.type == "Stock" and line.column_to.type == "Reserved":
                    if line.column_from.product_id.id <> line.product_id.id:
                        raise Warning('Selected Product are not Configured in Selected Source Location')
                elif line.column_from.type == "Reserved" and line.column_to.type == "Stock":
                    if line.column_to.product_id.id <> line.product_id.id:
                        raise Warning('Selected Product are not Configured in Selected Destination Location')
                elif line.column_from.type == "Stock" and line.column_to.type == "Stock":
                    if line.column_from.product_id.id <> line.product_id.id and line.column_to.product_id.id <> line.product_id.id:
                        raise Warning('Selected Product are not Configured in Selected Source/Destination Location')
                           
                self.env['lea.rack.level.column.detail'].create({
                    'reference': line.column_from.id,
                    'type': 'Outgoing',
                    'qty': line.qty,
                    'mutation_id': res.id
                })
                
                self.env['lea.rack.level.column.detail'].create({
                    'reference': line.column_to.id,
                    'type': 'Incoming',
                    'qty': line.qty,
                    'mutation_id': res.id
                })
                
            res.state = 'Approved'     
            
    @api.multi
    def button_cancel(self):
        for res in self:            
            mutation_ids = self.env['lea.rack.level.column.detail'].search([('mutation_id','=',res.id)])
            if mutation_ids:
                for mutation in mutation_ids:
                    mutation.unlink()                                                     
            res.state = 'Cancelled'                        
            

class LeaRackMutationLine(models.Model):
    _name = 'lea.rack.mutation.line'
    
    reference = fields.Many2one('lea.rack.mutation', 'Reference')
    product_id = fields.Many2one('product.product', 'Product')
    column_from = fields.Many2one('lea.rack.level.column', 'From Column')
    column_to = fields.Many2one('lea.rack.level.column', 'To Column')
    qty = fields.Integer('Qty')
    type = fields.Char(compute="_get_type", string="Mutation Type")
    
    @api.depends('column_from','column_to')    
    def _get_type(self):
        for res in self:            
            if res.column_from.type == "Stock" and res.column_to.type == "Reserved":
                res.type = "Stock to Reserved"
            elif res.column_from.type == "Stock" and res.column_to.type == "Stock":
                res.type = "Stock to Stock"
            elif res.column_from.type == "Reserved" and res.column_to.type == "Stock":
                res.type = "Reserved to Stock"
            elif res.column_from.type == "Reserved" and res.column_to.type == "Reserved":
                res.type = "Reserved to Reserved"                                    
            
class LeaDepartment(models.Model):
    _name = 'lea.department'
    
    name = fields.Char('Department')
    
    
class LeaPurchaseRequestLine(models.Model):
    _name = 'lea.purchase.request.line'
    
    reference = fields.Many2one('lea.purchase.request', 'Reference')            
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float('Qty')
    product_uom_id = fields.Many2one('product.uom', 'UoM')
    product_desc = fields.Char('Description')
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        for res in self:
            if res.product_id:
                res.product_uom_id = res.product_id.uom_id.id or False
                res.product_desc = res.product_id.product_desc or ''
    
    
class LeaPurchaseRequest(models.Model):
    _name = 'lea.purchase.request'
    
    name = fields.Char('Request No.')
    expired_date = fields.Date('Expired Date')
    notes = fields.Text('Notes')    
    created_by = fields.Many2one('res.users', 'Created by', default=lambda self:self.env.user)
    created_date = fields.Date('Created Date', default=fields.Date.today())
    approved_date = fields.Date('Approved Date', copy=False)
    approved_by = fields.Many2one('res.users', 'Approved by', copy=False)
    state = fields.Selection([('Draft','Draft'),('Confirmed','Confirmed'),('Approved','Approved')], string='Status', default='Draft')
    line_ids = fields.One2many('lea.purchase.request.line', 'reference', string='Lines', copy=True)
    
    @api.multi
    def button_confirm(self):
        for res in self:
            res.state = 'Confirmed'
            
    @api.multi
    def button_approve(self):
        for res in self:            
            res.state = 'Approved'
            res.approved_date = fields.Date.today()
            res.approved_by = self.env.user.id
            
    @api.multi
    def button_set_to_draft(self):
        for res in self:
            res.state = 'Draft'
    
    @api.model
    def create(self, vals):        
        vals['name'] = self.env['ir.sequence'].next_by_code('lea.purchase.request') or '/'
        return super(LeaPurchaseRequest, self).create(vals)
    
class LeaBankStatementLine(models.Model):
    _name = 'lea.bank.statement.line'
    
    reference = fields.Many2one('lea.bank.statement', 'Reference')
    move_id = fields.Many2one('account.move', 'Voucher No.')
    point_of_sale_id = fields.Many2one('pos.config', 'LEA Store')    
    type = fields.Selection([('Penerimaan','Penerimaan'),('Pengeluaran','Pengeluaran')], string="Jenis Transaksi", default="Pengeluaran")
    name = fields.Char('Keterangan')
    pos_amount = fields.Float(compute="_get_pos_amount", string='Keterangan')        
    date = fields.Date('Tanggal Transaksi')
    date_to = fields.Date('Tanggal Transaksi')            
    amount_debit = fields.Float('Debit')
    amount_credit = fields.Float('Credit')
    account_id = fields.Many2one('account.account', 'Account')
    is_biaya = fields.Boolean('Biaya Lain', default=False)
    is_credit_card = fields.Boolean('Debit / Credit Card', default=False)    
    account_biaya_id = fields.Many2one('account.account', 'Account Biaya')
    amount_biaya = fields.Float('Nilai Biaya')
    
    @api.depends('point_of_sale_id')
    def _get_pos_amount(self):
        for res in self:            
            total_amount = 0
            if res.point_of_sale_id:
                order_ids = self.env['pos.order'].search([('config_id','=',res.point_of_sale_id.id)])
                if order_ids:
                    for order in order_ids:                        
                        statement_ids = self.env['account.bank.statement.line'].search([('pos_statement_id','=',order.id)])
                        if statement_ids:
                            for statement in statement_ids:
                                total_amount =+ statement.amount
            res.pos_amount = total_amount                                                    
    
    
class LeaBankStatement(models.Model):
    _name = 'lea.bank.statement'
    
    name = fields.Char('Nomor Dokumen')
    tanggal_input = fields.Date('Tanggal Input', default=fields.Date.today())
    date = fields.Date('Tanggal Transaksi', default=fields.Date.today())    
    journal_id = fields.Many2one('account.journal', 'Bank', domain=[('type','=','bank')])
    amount_total_debit = fields.Float(compute="_get_amount_total_debit", string='Total Debit')
    amount_total_credit = fields.Float(compute="_get_amount_total_credit", string='Total Credit')
    state = fields.Selection([('Draft','Draft'),('Posted','Posted')], string='Status', default='Draft')
    line_ids = fields.One2many('lea.bank.statement.line', 'reference', string='Lines')
    journal_count = fields.Integer('# Journal Entries', compute='_compute_journal_count')
    
    @api.multi
    def button_post(self):
        for res in self:                                                                                                    
            for line in res.line_ids:                                                               
                move_id = ''           
                                                    
                vals_credit = {}
                vals_debit = {}
                vals_biaya = {}
                
                if line.amount_debit == 0 and line.amount_credit > 0:
                    vals_debit['name'] = res.name                
                    vals_debit['journal_id'] = res.journal_id.id or ''
                    vals_debit['date'] = res.date                
                    vals_debit['account_id'] = line.account_id.id                
                    vals_debit['debit'] = line.amount_credit
                    vals_debit['credit'] = 0
                    
                    vals_credit['name'] = res.name                
                    vals_credit['journal_id'] = res.journal_id.id or ''
                    vals_credit['date'] = res.date                
                    vals_credit['account_id'] = res.journal_id.default_debit_account_id.id
                    vals_credit['credit'] = line.amount_credit
                    vals_credit['debit'] = 0            
                    
                    move_id = self.env['account.move'].create({
                        'ref': res.name,                                        
                        'journal_id': res.journal_id.id,
                        'date': res.date,
                        'narration': res.name,
                        'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)]
                    })

                    move_id.post()
                    
                elif line.amount_credit == 0 and line.amount_debit > 0:
                    if not line.is_biaya:
                        vals_debit['name'] = res.name                
                        vals_debit['journal_id'] = res.journal_id.id or ''
                        vals_debit['date'] = res.date                
                        vals_debit['account_id'] = res.journal_id.default_debit_account_id.id                
                        vals_debit['debit'] = line.amount_debit
                        vals_debit['credit'] = 0
                        
                        vals_credit['name'] = res.name                
                        vals_credit['journal_id'] = res.journal_id.id or ''
                        vals_credit['date'] = res.date                
                        vals_credit['account_id'] = line.account_id.id
                        vals_credit['credit'] = line.amount_debit
                        vals_credit['debit'] = 0            
                        
                        move_id = self.env['account.move'].create({
                            'ref': res.name,                                        
                            'journal_id': res.journal_id.id,
                            'date': res.date,
                            'narration': res.name,
                            'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)]
                        })

                        move_id.post()
                        
                    if line.is_biaya:
                        vals_debit['name'] = res.name                
                        vals_debit['journal_id'] = res.journal_id.id or ''
                        vals_debit['date'] = res.date                
                        vals_debit['account_id'] = res.journal_id.default_debit_account_id.id                
                        vals_debit['debit'] = line.amount_debit - line.amount_biaya
                        vals_debit['credit'] = 0
                        
                        vals_biaya['name'] = res.name                
                        vals_biaya['journal_id'] = res.journal_id.id or ''
                        vals_biaya['date'] = res.date                
                        vals_biaya['account_id'] = line.account_biaya_id.id                
                        vals_biaya['debit'] = line.amount_biaya
                        vals_biaya['credit'] = 0
                        
                        vals_credit['name'] = res.name                
                        vals_credit['journal_id'] = res.journal_id.id or ''
                        vals_credit['date'] = res.date                
                        vals_credit['account_id'] = line.account_id.id
                        vals_credit['credit'] = line.amount_debit
                        vals_credit['debit'] = 0            
                        
                        move_id = self.env['account.move'].create({
                            'ref': res.name,                                        
                            'journal_id': res.journal_id.id,
                            'date': res.date,
                            'narration': res.name,
                            'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit), (0, 0, vals_biaya)]
                        })

                        move_id.post()
                                                
                line.move_id = move_id                                                
            res.state = "Posted"                        
            
    @api.multi
    def button_cancel(self):
        for res in self:            
            move_ids = self.env['account.move'].search([('ref','=',res.name)])
            if move_ids:
                for move_id in move_ids:
                    if move_id.state == "posted":
                        move_id.button_cancel()
                        move_id.unlink()
                    else:
                        move_id.unlink()
                                                                        
            self.state = "Draft"
    
    @api.multi
    def action_view_journal(self):      
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('ref', '=', self.name)]
        action['context'] = {}
        return action
    
    @api.multi
    def _compute_journal_count(self):
        for res in self:
            journal_ids = self.env['account.move'].search([('ref','=',res.name)])
            if journal_ids:         
                res.journal_count = len(journal_ids)
                
    @api.model
    def create(self, vals):        
        vals['name'] = self.env['ir.sequence'].next_by_code('lea.bank.statement') or '/'
        return super(LeaBankStatement, self).create(vals)
    
    @api.depends('line_ids.amount_debit')
    def _get_amount_total_debit(self):
        for res in self:
            amount_total_debit = 0
            for line in res.line_ids:
                amount_total_debit += line.amount_debit            
            res.amount_total_debit = amount_total_debit

    @api.depends('line_ids.amount_credit')
    def _get_amount_total_credit(self):
        for res in self:
            amount_total_credit = 0
            for line in res.line_ids:
                amount_total_credit += line.amount_credit            
            res.amount_total_credit = amount_total_credit
            
class LeaUangMukaLine(models.Model):
    _name = 'lea.uang.muka.line'
    
    reference = fields.Many2one('lea.uang.muka', 'Reference')
    name = fields.Char('Keterangan')            
    amount = fields.Float('Jumlah')
    account_id = fields.Many2one('account.account', 'Account')
    
        
class LeaUangMuka(models.Model):
    _name = 'lea.uang.muka'
    
    name = fields.Char('Nomor Uang Muka')    
    partner_id = fields.Many2one('res.partner', 'User', domain=[('customer','=',False),('supplier','=',False)])
    tanggal_input = fields.Date('Tanggal Input', default=fields.Date.today())    
    journal_id = fields.Many2one('account.journal', 'Petty Cash', domain=[('type','=','cash')])
    journal_uang_muka_id = fields.Many2one('account.journal', 'Jenis', domain=[('is_uang_muka','=',True)])
    amount = fields.Float(string='Jumlah Uang Muka')
    state = fields.Selection([('Draft','Draft'),('Approved','Approved'),('Posted','Posted')], string='Status', default='Draft')    
    journal_count = fields.Integer('# Journal Entries', compute='_compute_journal_count')
    amount_total = fields.Float(compute="_get_amount_total", string='Jumlah Biaya')
    line_ids = fields.One2many('lea.uang.muka.line', 'reference', string='Lines')
    
    @api.depends('line_ids.amount')
    def _get_amount_total(self):
        for res in self:
            amount_total = 0
            for line in res.line_ids:
                amount_total += line.amount            
            res.amount_total = amount_total
            
    @api.multi
    def button_approve(self):
        for res in self:                                                                                                        
            vals_credit = {}
            vals_debit = {}                                                
            move_id = ''           
            
            current_partner = self.env['lea.uang.muka'].search([
                ('partner_id','=',res.partner_id.id),
                ('id','<>',res.id),
                ('state','in',('Draft','Approved'))
            ])

            if current_partner:
                raise Warning('Partner yang dipilih masih memiliki Uang Muka yang belum dipertanggungjawabkan')
                
            if not res.journal_uang_muka_id.default_debit_account_id.id or '':
                raise Warning('Belum tersedia Pengaturan Account untuk Uang Muka')
            if not res.journal_id.default_debit_account_id:
                raise Warning('Belum tersedia Pengaturan Account untuk Petty Cash')
                                                
            vals_debit['name'] = res.name
            vals_debit['partner_id'] = res.partner_id.id or ''
            vals_debit['journal_id'] = res.journal_id.id or ''
            vals_debit['date'] = fields.Date.today()                
            vals_debit['account_id'] = res.journal_uang_muka_id.default_debit_account_id.id or ''                
            vals_debit['debit'] = res.amount
            vals_debit['credit'] = 0
            
            vals_credit['name'] = res.name
            vals_credit['partner_id'] = res.partner_id.id or ''
            vals_credit['journal_id'] = res.journal_id.id or ''
            vals_credit['date'] = fields.Date.today()                
            vals_credit['account_id'] = res.journal_id.default_debit_account_id.id or ''
            vals_credit['credit'] = res.amount
            vals_credit['debit'] = 0            
            
            move_id = self.env['account.move'].create({
                'ref': res.name,                                        
                'journal_id': res.journal_id.id,
                'date': fields.date.today(),
                'narration': res.name,
                'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)]
            })

            move_id.post()                                                        
            res.state = "Approved"                  
            
    @api.multi
    def button_post(self):
        for res in self:                                                                                                                                                                
            move_id = ''           
            
            if not res.line_ids:
                raise Warning('Detail Pengeluaran Biaya tidak boleh kosong')            
            if not res.journal_uang_muka_id.default_debit_account_id:
                raise Warning('Belum tersedia Pengaturan Account untuk Uang Muka')
            if not res.journal_id.default_debit_account_id:
                raise Warning('Belum tersedia Pengaturan Account untuk Jurnal Petty Cash')
                                                
            for line in res.line_ids:
                vals_credit = {}
                vals_debit = {}
                
                vals_debit['name'] = line.name
                vals_debit['partner_id'] = line.reference.partner_id.id or ''
                vals_debit['journal_id'] = line.reference.journal_uang_muka_id.id or ''
                vals_debit['date'] = fields.Date.today()                
                vals_debit['account_id'] = line.account_id.id                
                vals_debit['debit'] = line.amount
                vals_debit['credit'] = 0
                
                vals_credit['name'] = line.name
                vals_credit['partner_id'] = line.reference.partner_id.id or ''
                vals_credit['journal_id'] = line.reference.journal_uang_muka_id.id or ''
                vals_credit['date'] = fields.Date.today()
                vals_credit['account_id'] = line.reference.journal_uang_muka_id.default_debit_account_id.id or ''
                vals_credit['credit'] = line.amount
                vals_credit['debit'] = 0            
                
                move_id = self.env['account.move'].create({
                    'ref': res.name,                                        
                    'journal_id': res.journal_uang_muka_id.id,
                    'date': fields.Date.today(),
                    'narration': res.name,
                    'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)]
                })

                move_id.post()
                                                                        
            if res.amount > res.amount_total:
                vals_credit = {}
                vals_debit = {}
                
                vals_debit['name'] = line.name
                vals_debit['partner_id'] = line.reference.partner_id.id or ''
                vals_debit['journal_id'] = line.reference.journal_id.id or ''
                vals_debit['date'] = fields.Date.today()                
                vals_debit['account_id'] = line.reference.journal_id.default_debit_account_id.id or ''                
                vals_debit['debit'] = res.amount - res.amount_total
                vals_debit['credit'] = 0
                
                vals_credit['name'] = line.name
                vals_credit['partner_id'] = line.reference.partner_id.id or ''
                vals_credit['journal_id'] = line.reference.journal_id.id or ''
                vals_credit['date'] = fields.Date.today()
                vals_credit['account_id'] = line.reference.journal_uang_muka_id.default_debit_account_id.id or ''
                vals_credit['credit'] = res.amount - res.amount_total
                vals_credit['debit'] = 0            
                
                move_id = self.env['account.move'].create({
                    'ref': res.name,                                        
                    'journal_id': res.journal_id.id,
                    'date': fields.date.today(),
                    'narration': res.name,
                    'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)]
                })

                move_id.post()
                
            elif res.amount < res.amount_total:
                vals_credit = {}
                vals_debit = {}
                
                vals_debit['name'] = line.name
                vals_debit['partner_id'] = line.reference.partner_id.id or ''
                vals_debit['journal_id'] = line.reference.journal_id.id or ''
                vals_debit['date'] = fields.Date.today()                
                vals_debit['account_id'] = line.reference.journal_uang_muka_id.default_debit_account_id.id or ''                
                vals_debit['debit'] = res.amount_total - res.amount
                vals_debit['credit'] = 0
                
                vals_credit['name'] = line.name
                vals_credit['partner_id'] = line.reference.partner_id.id or ''
                vals_credit['journal_id'] = line.reference.journal_id.id or ''
                vals_credit['date'] = fields.Date.today()
                vals_credit['account_id'] = line.reference.journal_id.default_debit_account_id.id or ''
                vals_credit['credit'] = res.amount_total - res.amount
                vals_credit['debit'] = 0            
                
                move_id = self.env['account.move'].create({
                    'ref': res.name,                                        
                    'journal_id': res.journal_id.id,
                    'date': fields.date.today(),
                    'narration': res.name,
                    'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)]
                })

                move_id.post()
                
            res.state = "Posted"      
                              
            
    @api.multi
    def button_cancel(self):
        for res in self:            
            move_ids = self.env['account.move'].search([('ref','=',res.name)])
            if move_ids:
                for move_id in move_ids:
                    if move_id.state == "posted":
                        move_id.button_cancel()
                        move_id.unlink()
                    else:
                        move_id.unlink()
                                                                        
            self.state = "Draft"
    
    @api.multi
    def action_view_journal(self):      
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('ref', '=', self.name)]
        action['context'] = {}
        return action
    
    @api.multi
    def _compute_journal_count(self):
        for res in self:
            journal_ids = self.env['account.move'].search([('ref','=',res.name)])
            if journal_ids:         
                res.journal_count = len(journal_ids)
                
    @api.model
    def create(self, vals):        
        vals['name'] = self.env['ir.sequence'].next_by_code('lea.uang.muka') or '/'
        return super(LeaUangMuka, self).create(vals)
            
            
class LeaPettyCashLine(models.Model):
    _name = 'lea.petty.cash.line'
    
    reference = fields.Many2one('lea.petty.cash', 'Reference')    
    name = fields.Char('Keterangan')    
    partner_id = fields.Many2one('res.partner', 'User', domain=[('customer','=',False),('supplier','=',False)])
    date = fields.Date('Tanggal Transaksi')
    amount = fields.Float('Jumlah')
    account_id = fields.Many2one('account.account', 'Account')
    
    
class LeaPettyCash(models.Model):
    _name = 'lea.petty.cash'
    
    name = fields.Char('Nomor Pengeluaran Kas')
    partner_id = fields.Many2one('res.partner', 'User', domain=[('customer','=',False),('supplier','=',False)])
    tanggal_input = fields.Date('Tanggal Input', default=fields.Date.today())
    journal_id = fields.Many2one('account.journal', 'Petty Cash', domain=[('type','=','cash')])
    amount_total = fields.Float(compute="_get_amount_total", string='Jumlah Total')
    state = fields.Selection([('Draft','Draft'),('Posted','Posted')], string='Status', default='Draft')
    line_ids = fields.One2many('lea.petty.cash.line', 'reference', string='Lines')
    journal_count = fields.Integer('# Journal Entries', compute='_compute_journal_count')
    
    @api.multi
    def button_post(self):
        for res in self:                                                                                                    
            for line in res.line_ids:                                                               
                move_id = ''           
                                                    
                vals_credit = {}
                vals_debit = {}
                
                vals_debit['name'] = res.name
                vals_debit['partner_id'] = line.partner_id.id or ''
                vals_debit['journal_id'] = res.journal_id.id or ''
                vals_debit['date'] = res.date                
                vals_debit['account_id'] = line.account_id.id                
                vals_debit['debit'] = line.amount
                vals_debit['credit'] = 0
                
                vals_credit['name'] = res.name
                vals_credit['partner_id'] = line.partner_id.id or ''
                vals_credit['journal_id'] = res.journal_id.id or ''
                vals_credit['date'] = res.date                
                vals_credit['account_id'] = res.journal_id.default_debit_account_id.id
                vals_credit['credit'] = line.amount
                vals_credit['debit'] = 0            
                
                move_id = self.env['account.move'].create({
                    'ref': res.name,                                        
                    'journal_id': res.journal_id.id,
                    'date': res.date,
                    'narration': res.name,
                    'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)]
                })

                move_id.post()
        
                                                    
            res.state = "Posted"                        
            
    @api.multi
    def button_cancel(self):
        for res in self:            
            move_ids = self.env['account.move'].search([('ref','=',res.name)])
            if move_ids:
                for move_id in move_ids:
                    if move_id.state == "posted":
                        move_id.button_cancel()
                        move_id.unlink()
                    else:
                        move_id.unlink()
                                                                        
            self.state = "Draft"
    
    @api.multi
    def action_view_journal(self):      
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('ref', '=', self.name)]
        action['context'] = {}
        return action
    
    @api.multi
    def _compute_journal_count(self):
        for res in self:
            journal_ids = self.env['account.move'].search([('ref','=',res.name)])
            if journal_ids:         
                res.journal_count = len(journal_ids)
                
    @api.model
    def create(self, vals):        
        vals['name'] = self.env['ir.sequence'].next_by_code('lea.petty.cash') or '/'
        return super(LeaPettyCash, self).create(vals)
    
    @api.depends('line_ids.amount')
    def _get_amount_total(self):
        for res in self:
            amount_total = 0
            for line in res.line_ids:
                amount_total += line.amount            
            res.amount_total = amount_total
            
    
class LeaEkspedisi(models.Model):
    _name = 'lea.ekspedisi'
        
    name = fields.Char('Request #')    
    
    
class LeaStockRequest(models.Model):
    _name = 'lea.stock.request'
        
    name = fields.Char('Request #')
    sale_id = fields.Many2one('sale.order', 'SO Number')    

class LeaDiscount(models.Model):
    _name = 'lea.discount'
        
    name = fields.Char(compute="_get_discount_name", string='Discount Name')    
    disc1 = fields.Float('Discount 1 (%)')
    disc2 = fields.Float('Discount 2 (%)')
    disc3 = fields.Float('Discount 3 (%)')
    
    @api.depends('disc1', 'disc2', 'disc3')
    def _get_discount_name(self):
        for res in self:
            name = ''
            if res.disc1:
                name += name + "+" + str(res.disc1)
            if res.disc2:
                name += name + "+" + str(res.disc2)
            if res.disc3:
                name += name + "+" + str(res.disc3)
    
class LeaArea(models.Model):
    _name = 'lea.area'
        
    name = fields.Char('Area')
    
class LeaSubArea(models.Model):
    _name = 'lea.sub.area'
            
    name = fields.Char('Sub Area')
    area_id = fields.Many2one('lea.area', 'Area')        

class LeaIdentityType(models.Model):
    _name = 'lea.identity.type'
            
    name = fields.Char('Identity Type')

#unuse
class LeaIdentity(models.Model):
    _name = 'lea.identity'
            
    reference = fields.Many2one('res.partner', 'Reference')
    identity_type = fields.Many2one('lea.identity.type', 'Identity Type')
    identity_number = fields.Char('Identity No.')
    identity_file = fields.Binary('Identity File')
    
    
###### PRODUCT ATTRIBUTES ######
class LeaProductPocket(models.Model):
    _name = 'lea.product.pocket'
    
    name = fields.Char('Pocket')
    
class LeaProductSleeve(models.Model):
    _name = 'lea.product.sleeve'
    
    name = fields.Char('Sleeve')

class LeaProductColor(models.Model):
    _name = 'lea.product.color'
    
    name = fields.Char('Color')
    
class LeaProductEmbeded(models.Model):
    _name = 'lea.product.embeded'
    
    name = fields.Char('Embeded')
    
class LeaProductRawMaterial(models.Model):
    _name = 'lea.product.raw.material'
    
    name = fields.Char('Raw Material')

class LeaProductFittingCategory(models.Model):
    _name = 'lea.product.fitting.category'
    
    name = fields.Char('Fitting Category')
    
class LeaProductSexCategory(models.Model):
    _name = 'lea.product.sex.category'
    
    name = fields.Char('Sex Category')
    
class LeaProductStyle(models.Model):
    _name = 'lea.product.style'
    
    name = fields.Char('Style')
    
class LeaProductMovingStatus(models.Model):
    _name = 'lea.product.moving.status'
    
    name = fields.Char('Moving Status')
    default_contribution = fields.Float('Default Target')
    
class LeaProductSellingGroup(models.Model):
    _name = 'lea.product.selling.group'
    
    name = fields.Char('Selling Group')
    
class LeaProductQcGroup(models.Model):
    _name = 'lea.product.qc.group'
    
    name = fields.Char('QC Group')
    
class LeaProductClassCategory(models.Model):
    _name = 'lea.product.class.category'
    
    name = fields.Char('Class Product Category')
    
class LeaProductCategory(models.Model):
    _name = 'lea.product.category'
    
    name = fields.Char('Category')

class LeaProductLabel(models.Model):
    _name = 'lea.product.label'
    
    name = fields.Char('Label')
##############################################################


class LeaProductClass(models.Model):
    _name = 'lea.product.class'
    
    name = fields.Char('Class')
    
class LeaProductCategory1(models.Model):
    _name = 'lea.product.category1'
    
    name = fields.Char('Category Name')
    
class LeaProductCategory2(models.Model):
    _name = 'lea.product.category2'
    
    name = fields.Char('Category Name')
    
class LeaProductCategory3(models.Model):
    _name = 'lea.product.category3'
    
    name = fields.Char('Category Name')
    
class LeaProductCategory4(models.Model):
    _name = 'lea.product.category4'
    
    name = fields.Char('Category Name')
    
class LeaProductCategory5(models.Model):
    _name = 'lea.product.category5'
    
    name = fields.Char('Category Name')
    
class LeaProductCategory6(models.Model):
    _name = 'lea.product.category6'
    
    name = fields.Char('Category Name')
    
class LeaProductFitting(models.Model):
    _name = 'lea.product.fitting'
    
    name = fields.Char('Fitting')
    
class LeaProductSize(models.Model):
    _name = 'lea.product.size'
    
    name = fields.Char('Size')
    
class LeaProductBrand(models.Model):
    _name = 'lea.product.brand'
    
    name = fields.Char('Brand')
    
class LeaProductSourcing(models.Model):
    _name = 'lea.product.sourcing'
    
    name = fields.Char('Sourcing')
    
class LeaProductMaterialGroup(models.Model):
    _name = 'lea.product.material.group'
    
    name = fields.Char('Material Group')
    desc = fields.Char('Description')
    
class LeaProductMaterialType(models.Model):
    _name = 'lea.product.material.type'
    
    name = fields.Char('Material Type')
    desc = fields.Char('Description')

class LeaProductMaterialCategory(models.Model):
    _name = 'lea.product.material.category'
    
    name = fields.Char('Material Category')
    desc = fields.Char('Description')

class LeaProductStockType(models.Model):
    _name = 'lea.product.stock.type'
    
    name = fields.Char('Stock Type')
    desc = fields.Char('Description')
    
class PurchaseOrderRequest(models.Model):
    _name = 'purchase.order.request'
    
    reference = fields.Many2one('purchase.order', 'Reference')
    product_id = fields.Char('Description')
    
    
################################################# INHERITANCE #########################################################
class ProductCategory(models.Model):
    _inherit = "product.category"
    
    property_account_income_categ_id = fields.Many2one('account.account', company_dependent=True,
        string="Income Account", oldname="property_account_income_categ",
        domain=[('deprecated', '=', False)],
        help="This account will be used for invoices to value sales.", copy=True)
    property_account_expense_categ_id = fields.Many2one('account.account', company_dependent=True,
        string="Expense Account", oldname="property_account_expense_categ",
        domain=[('deprecated', '=', False)],
        help="This account will be used for invoices to value expenses.", copy=True)    
    property_stock_journal = fields.Many2one(
        'account.journal', 'Stock Journal', company_dependent=True, copy=True,
        help="When doing real-time inventory valuation, this is the Accounting Journal in which entries will be automatically posted when stock moves are processed.")
    property_stock_account_input_categ_id = fields.Many2one(
        'account.account', 'Stock Input Account', company_dependent=True, copy=True,
        domain=[('deprecated', '=', False)], oldname="property_stock_account_input_categ",
        help="When doing real-time inventory valuation, counterpart journal items for all incoming stock moves will be posted in this account, unless "
             "there is a specific valuation account set on the source location. This is the default value for all products in this category. It "
             "can also directly be set on each product")
    property_stock_account_output_categ_id = fields.Many2one(
        'account.account', 'Stock Output Account', company_dependent=True, copy=True,
        domain=[('deprecated', '=', False)], oldname="property_stock_account_output_categ",
        help="When doing real-time inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account, unless "
             "there is a specific valuation account set on the destination location. This is the default value for all products in this category. It "
             "can also directly be set on each product")
    property_stock_valuation_account_id = fields.Many2one(
        'account.account', 'Stock Valuation Account', company_dependent=True, copy=True,
        domain=[('deprecated', '=', False)],
        help="When real-time inventory valuation is enabled on a product, this account will hold the current value of the products.",)
    
    
class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))        
        if self.advance_payment_method == 'delivered':
            discount0_ids = []
            discount10_ids = []
            discount20_ids = []
            discount30_ids = []
            discount40_ids = []
            discount50_ids = []            
            for sale in sale_orders:
                for order_line in sale.order_line:
                    if order_line.discount == 0:
                        discount0_ids.append(sale.id)
                    elif order_line.discount == 10:
                        discount10_ids.append(sale.id)
                    elif order_line.discount == 20:
                        discount20_ids.append(sale.id)
                    elif order_line.discount == 30:
                        discount30_ids.append(sale.id)
                    elif order_line.discount == 40:
                        discount40_ids.append(sale.id)
                    elif order_line.discount == 50:
                        discount50_ids.append(sale.id)
                    
            if discount0_ids:                                
                self.env['sale.order'].browse(discount0_ids).action_invoice_create()
            if discount10_ids:                                
                self.env['sale.order'].browse(discount10_ids).action_invoice_create()
            if discount20_ids:                                
                self.env['sale.order'].browse(discount20_ids).action_invoice_create()
            if discount30_ids:                                
                self.env['sale.order'].browse(discount30_ids).action_invoice_create()
            if discount40_ids:                                
                self.env['sale.order'].browse(discount40_ids).action_invoice_create()
            if discount50_ids:                                
                self.env['sale.order'].browse(discount50_ids).action_invoice_create()
                    
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.values'].sudo().set_default('sale.config.settings', 'deposit_product_id_setting', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                if order.fiscal_position_id and self.product_id.taxes_id:
                    tax_ids = order.fiscal_position_id.map_tax(self.product_id.taxes_id).ids
                else:
                    tax_ids = self.product_id.taxes_id.ids
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, tax_ids)],
                })
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
    
    
class SaleReport(models.Model):
    _inherit = 'sale.report'
    
    categ_id = fields.Many2one('lea.product.category', 'Product Category', readonly=True)
    #product_category_id = fields.Many2one('lea.product.category', 'Product Category', readonly=True)
    amount_total = fields.Float('Total', readonly=True)    
    customer_type = fields.Selection([
        ('JEANS STORE','JEANS STORE'),
        ('WHOLESALE','WHOLESALE'),
        ('CORPORATE','CORPORATE'),
        ('CONSIGNMENT','CONSIGNMENT'),
        ('RETAIL_ONLINE', 'RETAIL ONLINE'),
        ],
        string='Customer Type', default='WHOLESALE')    
    
    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
                    sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
                    sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    sum(l.price_subtotal / COALESCE(cr.rate, 1.0)) as price_subtotal,
                    count(*) as nbr,
                    s.name as name,
                    s.amount_total as amount_total,
                    s.date_order as date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,                    
                    s.pricelist_id as pricelist_id,
                    s.project_id as analytic_account_id,
                    s.team_id as team_id,
                    p.product_tmpl_id,
                    partner.country_id as country_id,
                    partner.customer_type as customer_type,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,                    
                    s.name,
                    s.date_order,
                    s.partner_id,
                    s.user_id,
                    s.state,
                    s.company_id,
                    s.pricelist_id,
                    s.project_id,
                    s.team_id,
                    s.amount_total,
                    p.product_tmpl_id,
                    partner.country_id,
                    partner.customer_type,
                    partner.commercial_partner_id
        """
        return group_by_str
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    request_line_id = fields.Many2one('lea.purchase.request.line', 'Request Line')
    request_id = fields.Many2one('lea.purchase.request', related='request_line_id.reference', string='Purchase Request', store=False, readonly=True)
    
        
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    request_id = fields.Many2one('lea.purchase.request', 'Request #')
    delivery_type = fields.Selection([('Pusat','Pusat'),('Pabrik','Pabrik')], default="Pabrik", string="Delivery Type") 
    request_line_ids = fields.One2many('purchase.order.request', 'reference', string='Request Lines')

    @api.onchange('order_line')
    def _onchange_allowed_request_ids(self):
        result = {}        
        request_line_ids = self.order_line.mapped('request_line_id')
        request_ids = self.order_line.mapped('request_id').filtered(lambda r: r.line_ids <= request_line_ids)

        result['domain'] = {'request_id': [                        
            ('id', 'not in', request_ids.ids),
            ]}
        return result
    
    def _prepare_purchase_line_from_request_line(self, line):                        
        data = {
            'request_line_id': line.id,            
            'product_id': line.product_id.id,                        
            'product_qty': line.product_qty,                                                
        }        
        return data
    
    @api.onchange('request_id')
    def request_order_change(self):
        if not self.request_id:
            return {}           
        new_lines = self.env['purchase.order.line']
        for line in self.request_id.line_ids:
            # Load a PO line only once
            if line in self.order_line.mapped('request_line_id'):
                continue
            data = self._prepare_purchase_line_from_request_line(line)
            new_line = new_lines.new(data)            
            new_lines += new_line

        self.order_line += new_lines     
        self.request_id = False
        return {}
    
#===============================================================================
#     @api.onchange('requisition_id')
#     def _onchange_requisition_id(self):
#         if not self.requisition_id:
#             return
# 
#         requisition = self.requisition_id
#         if self.partner_id:
#             partner = self.partner_id
#         else:
#             partner = requisition.vendor_id
#         payment_term = partner.property_supplier_payment_term_id
#         currency = partner.property_purchase_currency_id or requisition.company_id.currency_id
# 
#         FiscalPosition = self.env['account.fiscal.position']
#         fpos = FiscalPosition.get_fiscal_position(partner.id)
#         fpos = FiscalPosition.browse(fpos)
# 
#         #self.partner_id = partner.id            
#         print self.env.user.name
#         print self.env.user.id
#         partner_id = self.env['res.partner'].search([])
#         print partner_id
#         partner_id = self.env['res.partner'].search([('related_user_id','=',self.env.user.id)])
#         print partner_id
#         print "Related Partner ", partner_id            
#         self.partner_id = partner_id.id or False
#         self.fiscal_position_id = fpos.id
#         self.payment_term_id = payment_term.id,
#         self.company_id = requisition.company_id.id
#         self.currency_id = currency.id
#         self.origin = requisition.name
#         self.partner_ref = requisition.name # to control vendor bill based on agreement reference
#         self.notes = requisition.description
#         self.date_order = requisition.date_end or fields.Datetime.now()
#         self.picking_type_id = requisition.picking_type_id.id
# 
#         if requisition.type_id.line_copy != 'copy':
#             return
# 
#         # Create PO lines if necessary
#         order_lines = []
#         for line in requisition.line_ids:
#             # Compute name
#             product_lang = line.product_id.with_context({
#                 'lang': partner.lang,
#                 'partner_id': partner.id,
#             })
#             name = product_lang.display_name
#             if product_lang.description_purchase:
#                 name += '\n' + product_lang.description_purchase
# 
#             # Compute taxes
#             if fpos:
#                 taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id))
#             else:
#                 taxes_ids = line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id).ids
# 
#             # Compute quantity and price_unit
#             if line.product_uom_id != line.product_id.uom_po_id:
#                 product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
#                 price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
#             else:
#                 product_qty = line.product_qty
#                 price_unit = line.price_unit
# 
#             if requisition.type_id.quantity_copy != 'copy':
#                 product_qty = 0
# 
#             # Compute price_unit in appropriate currency
#             if requisition.company_id.currency_id != currency:
#                 price_unit = requisition.company_id.currency_id.compute(price_unit, currency)
# 
#             # Create PO line
#             order_lines.append((0, 0, {
#                 'name': name,
#                 'product_id': line.product_id.id,
#                 'product_uom': line.product_id.uom_po_id.id,
#                 'product_qty': product_qty,
#                 'price_unit': price_unit,
#                 'taxes_id': [(6, 0, taxes_ids)],
#                 'date_planned': requisition.schedule_date or fields.Date.today(),
#                 'procurement_ids': [(6, 0, [requisition.procurement_id.id])] if requisition.procurement_id else False,
#                 'account_analytic_id': line.account_analytic_id.id,
#             }))
#         self.order_line = order_lines
#===============================================================================
        

class AccountJournal(models.Model):
    _inherit = 'account.journal'
    
    is_credit_card = fields.Boolean('Credit Card')
    is_uang_muka = fields.Boolean('Uang Muka')
    
    
class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    responsible_id  = fields.Many2many('res.users', string='PDS')
    code            = fields.Char('Short Name', size=50, help="Short name used to identify your warehouse")
    wh_code         = fields.Char('Warehouse Code', help="Short name used to identify your warehouse", required=True)
    wh_area_id      = fields.Many2one('lea.area','Area', required=True)
    wh_subarea_id   = fields.Many2one('lea.sub.area','Sub-Area', required=True)
    wh_grade        = fields.Char('Grade', required=True)
    wh_type         = fields.Selection([('LS','Store'),('LC','Consignment'),('TP','Toko Putus'),('CP','Corporate'),('MW','Main WH')], string='Warehouse Type')
    wh_onstage      = fields.Integer('On Stage')
    wh_buffer       = fields.Integer('Buffer')
    wh_capacity     = fields.Integer(string='Capacity', compute='compute_capacity', store=True)
    wh_lead_time    = fields.Integer('Lead Time (Day)', default=30)
    wh_avg_sales    = fields.Integer('Avg. Sales (Month)', default=12)
    ito_list        = fields.One2many(comodel_name='stock.warehouse.ito', inverse_name='warehouse_id', string='ITO List')

    @api.depends('wh_onstage','wh_buffer')
    def compute_capacity(self):
        for rec in self:
            rec.wh_capacity = rec.wh_onstage + rec.wh_buffer
    

class StockWarehouseITO(models.Model):
    _name = 'stock.warehouse.ito'
    
    warehouse_id    = fields.Many2one('stock.warehouse', string='Warehouse')
    category_id     = fields.Many2one('lea.product.category', 'Product Category')
    ito_value       = fields.Integer('ITO')


class StockPickingArticle(models.Model):
    _name = 'stock.picking.article'
    
    reference = fields.Many2one('stock.picking', 'Reference')    
    article_code = fields.Char('Article Code')
    size24 = fields.Integer('24')
    size25 = fields.Integer('25')
    size26 = fields.Integer('26')
    size27 = fields.Integer('27')
    size28 = fields.Integer('28')
    size29 = fields.Integer('29')
    size30 = fields.Integer('30')
    size31 = fields.Integer('31')
    size32 = fields.Integer('32')
    size33 = fields.Integer('33')
    size34 = fields.Integer('34')
    size35 = fields.Integer('35')
    size36 = fields.Integer('36')
    size37 = fields.Integer('37')
    size38 = fields.Integer('38')
    size39 = fields.Integer('39')
    size40 = fields.Integer('40')
    size41 = fields.Integer('41')
    size42 = fields.Integer('42')
    sizexs = fields.Integer('XS')
    sizes = fields.Integer('S')
    sizem = fields.Integer('M')
    sizel = fields.Integer('L')
    sizexl = fields.Integer('XL')
    sizexxl = fields.Integer('XXL')    
    sizeal = fields.Integer('AL')
    sizex = fields.Integer('X')
    sizey = fields.Integer('Y')
    sizez = fields.Integer('Z')
    total_qty = fields.Integer(compute="_get_total_qty", string='Total')
    
    @api.depends('size24', 'size25', 'size26', 'size27', 'size28', 'size29', 'size30', 'size31', 'size32', 'size33', 'size34', 'size35', 'size36', 'size37', 'size38', 'size39', 'size40', 'size41', 'size42', 'sizexs', 'sizes', 'sizem', 'sizel', 'sizexl', 'sizexxl', 'sizeal', 'sizex', 'sizey', 'sizez' )
    def _get_total_qty(self):
        for res in self:                            
            res.total_qty = res.size24 + res.size25 + res.size26 + res.size27 + res.size28 + res.size29 + res.size30 + res.size31 + res.size32 + res.size33 + res.size34 + res.size35 + res.size36 + res.size37 + res.size38 + res.size39 + res.size40 + res.size41 + res.size42 + res.sizexs + res.sizes + res.sizem + res.sizel + res.sizexl + res.sizexxl + res.sizeal + res.sizex + res.sizey + res.sizez     
            

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    is_picking_list = fields.Boolean('Picking List', default=False)
    picking_penerima = fields.Many2one(compute="_get_penerima", comodel_name='stock.location', string="Penerima", store=True)

    @api.depends('picking_id')
    def _get_penerima(self):
        for res in self:
            if res.picking_id:
                res.picking_penerima = res.picking_id.location_final_id.id
    
    
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'min_date desc'
    
    note = fields.Text('Notes')
    area_id = fields.Char('Area')
    sub_area_id = fields.Char(compute="_get_sub_area_id", string='Sub Area')
    is_picking_list = fields.Boolean('Picking List', default=False)
    is_packing_list = fields.Boolean('Packing List', default=False)
    picking_list_id = fields.Many2one('lea.picking.list', string='Picking List No.')
    packing_list_id = fields.Many2one('lea.packing.list', string='Packing List No.')    
    amount_total_qty = fields.Integer(compute="_get_amount_total_qty", string='Shipped Qty')
    amount_total_qty_demmand = fields.Integer(compute="_get_amount_total_qty_demmand", string='Ordered Qty')    
    is_transit = fields.Boolean('Transit', default=False)    
    location_final_id = fields.Many2one('stock.location', string='Penerima')
    picking_final_id = fields.Many2one('stock.picking', string='Dokumen Referensi')
    incoterm_id = fields.Many2one('stock.incoterms', string='Ekspedisi')
    resi = fields.Char('No. Resi')
    dokumen_referensi = fields.Char('Dokumen Referensi')
    reference_document_id = fields.Many2one('stock.pickin', 'Dokumen Referensi')
    received_date = fields.Datetime('Tanggal Terima')
    so_created_date = fields.Datetime(compute="_get_so_created_date", string='SO Created')
    so_approved_date = fields.Datetime(compute="_get_so_approved_date", string='SO Approved')
    jumlah_collie = fields.Float('Jumlah Collie')
    total_berat = fields.Float('Total Berat (Kg)')
    article_code_ids = fields.One2many('stock.picking.article', 'reference', 'Article Code')
    replenishment_id = fields.Many2one(comodel_name='lea.stock.replenishment',string='Replenishment ID')
    putaway_id = fields.Many2one('lea.putaway', 'Putaway Doc')

    @api.multi
    def create_putaway(self):
        for res in self:                    
            putaway_id = self.env['lea.putaway'].create({
                'type': 'Receipt',
                'picking_id': res.id,
                'date': fields.Date.today(),
            })

            res.write({'putaway_id': putaway_id.id})
            
            for line in res.pack_operation_product_ids:                
                available_space = 0
                remaining_qty = line.qty_done

                if line.product_id.product_tmpl_id.racknew_ids:
                    for column in line.product_id.product_tmpl_id.racknew_ids:
                        if remaining_qty > 0:
                            if column.type == "Stock":                                                                
                                available_space = column.column_id.max_stock - column.column_id.available_stock
                                if available_space > 0:
                                    if available_space >= line.qty_done: 
                                        self.env['lea.putaway.detail'].create({
                                            'reference': putaway_id.id,      
                                            'column_id': column.column_id.id,                                                               
                                            'product_id': line.product_id.id,                                                                                                                                    
                                            'qty': line.qty_done,
                                        })

                                        remaining_qty -= line.qty_done

                                    elif available_space < line.qty_done: 
                                        self.env['lea.putaway.detail'].create({
                                            'reference': putaway_id.id,
                                            'column_id': column.column_id.id,
                                            'product_id': line.product_id.id,
                                            'qty': available_space,
                                        })

                                        remaining_qty -= available_space
                                    
                        # remaining_qty = line.qty_done - available_space
                    if remaining_qty > 0:
                        available_space = 0
                        for column in line.product_id.product_tmpl_id.racknew_ids:
                            if column.type == "Reserved":
                                available_space = column.column_id.max_stock - column.column_id.available_stock
                                if available_space > 0:
                                    if available_space >= remaining_qty: 
                                        self.env['lea.putaway.detail'].create({
                                            'reference': putaway_id.id,
                                            'column_id': column.column_id.id,
                                            'product_id': line.product_id.id,
                                            'qty': remaining_qty,
                                        })

                                    elif available_space < remaining_qty:
                                        self.env['lea.putaway.detail'].create({
                                            'reference': putaway_id.id,
                                            'column_id': column.column_id.id,
                                            'product_id': line.product_id.id,
                                            'qty': available_space,
                                        })
                                        
                                        remaining_qty -= available_space

                else:
                    self.env['lea.putaway.detail'].create({
                        'reference': putaway_id.id,
                        'product_id': line.product_id.id,
                        'qty': line.qty_done,
                    })

    
    @api.depends('sub_area_id')
    def _get_sub_area_id(self):
        for res in self:
            sub_area_id = "-"
            if res.origin:
                sale_id = self.env['sale.order'].search([('name','=',res.origin)])
                if sale_id:
                    if sale_id[0].partner_id.city:
                        sub_area_id = sale_id[0].partner_id.city
            res.sub_area_id = sub_area_id

    @api.multi
    def action_create_job_picking(self):
        action = {
            'name': ('Create Job Picking'),
            'type': "ir.actions.act_window",
            'res_model': "stock.picking",
            'view_type': "tree",
            'view_mode': "tree",
            'view_id': "view_lea_create_job_picking_tree",
            'domain': "[('picking_type_id.code','=','outgoing'),('state','in',('assigned','partially_available')),('is_picking_list','=',False)]"
        }                    
        return action
    
    @api.multi
    def action_create_job_packing(self):
        action = {
            'name': ('Create Job Packing'),
            'type': "ir.actions.act_window",
            'res_model': "stock.picking",
            'view_type': "tree",
            'view_mode': "tree",
            'view_id': "view_lea_create_job_packing_tree",            
            'domain': "[('picking_type_id.code','=','outgoing'),('state','in',('assigned','partially_available')),('is_packing_list','=',False),('is_picking_list','=',True),('picking_list_id.state','=','Done')]"            
        }                    
        return action
    
    @api.depends('pack_operation_product_ids')
    def _get_amount_total_qty(self):
        for res in self:
            amount_total_qty = 0
            for line in res.pack_operation_product_ids:
                amount_total_qty += line.product_qty
            res.amount_total_qty = amount_total_qty
            
            
    @api.depends('move_lines')
    def _get_amount_total_qty_demmand(self):
        for res in self:
            amount_total_qty_demmand = 0
            for line in res.move_lines:
                amount_total_qty_demmand += line.product_uom_qty
            res.amount_total_qty_demmand = amount_total_qty_demmand
            
    @api.multi
    def do_transfer(self):        
        """ If no pack operation, we do simple action_done of the picking.
        Otherwise, do the pack operations. """
        # TDE CLEAN ME: reclean me, please
        self._create_lots_for_picking()

        no_pack_op_pickings = self.filtered(lambda picking: not picking.pack_operation_ids)
        no_pack_op_pickings.action_done()
        other_pickings = self - no_pack_op_pickings
        for picking in other_pickings:
            need_rereserve, all_op_processed = picking.picking_recompute_remaining_quantities()
            todo_moves = self.env['stock.move']
            toassign_moves = self.env['stock.move']

            # create extra moves in the picking (unexpected product moves coming from pack operations)
            if not all_op_processed:
                todo_moves |= picking._create_extra_moves()

            if need_rereserve or not all_op_processed:
                moves_reassign = any(x.origin_returned_move_id or x.move_orig_ids for x in picking.move_lines if x.state not in ['done', 'cancel'])
                if moves_reassign and picking.location_id.usage not in ("supplier", "production", "inventory"):
                    # unnecessary to assign other quants than those involved with pack operations as they will be unreserved anyways.
                    picking.with_context(reserve_only_ops=True, no_state_change=True).rereserve_quants(move_ids=picking.move_lines.ids)
                picking.do_recompute_remaining_quantities()

            # split move lines if needed
            for move in picking.move_lines:
                rounding = move.product_id.uom_id.rounding
                remaining_qty = move.remaining_qty
                if move.state in ('done', 'cancel'):
                    # ignore stock moves cancelled or already done
                    continue
                elif move.state == 'draft':
                    toassign_moves |= move
                if float_compare(remaining_qty, 0,  precision_rounding=rounding) == 0:
                    if move.state in ('draft', 'assigned', 'confirmed'):
                        todo_moves |= move
                elif float_compare(remaining_qty, 0, precision_rounding=rounding) > 0 and float_compare(remaining_qty, move.product_qty, precision_rounding=rounding) < 0:
                    # TDE FIXME: shoudl probably return a move - check for no track key, by the way
                    new_move_id = move.split(remaining_qty)
                    new_move = self.env['stock.move'].with_context(mail_notrack=True).browse(new_move_id)
                    todo_moves |= move
                    # Assign move as it was assigned before
                    toassign_moves |= new_move

            # TDE FIXME: do_only_split does not seem used anymore
            if todo_moves and not self.env.context.get('do_only_split'):
                todo_moves.action_done()
            elif self.env.context.get('do_only_split'):
                picking = picking.with_context(split=todo_moves.ids)

            picking._create_backorder()
            
            if picking.is_transit:                
                new_picking_type_id = self.env['stock.picking.type'].search([
                    ('default_location_src_id','=',picking.location_final_id.id),
                    ('code','=','internal')
                ])

                new_picking_id = picking.copy({
                    'picking_type_id': new_picking_type_id.id,
                    'name': '/',                                            
                    'location_id': picking.location_dest_id.id,
                    'location_dest_id': picking.location_final_id.id,
                    'is_transit': False,                                            
                    'dokumen_referensi': picking.name or '',
                    'reference_document_id': picking.id,
                })
                                
                new_picking_id.action_assign()

                if new_picking_id:
                    picking.write({
                        'reference_document_id':new_picking_id.id,
                        'dokumen_referensi': new_picking_id.name,
                    })
                
        return True
    
    @api.depends('origin')
    def _get_so_created_date(self):
        for res in self:
            order = self.env['sale.order'].search([('name','=',res.origin)])
            if order:
                res.so_created_date = order[0].create_date
                
    @api.depends('origin')
    def _get_so_approved_date(self):
        for res in self:
            order = self.env['sale.order'].search([('name','=',res.origin)])
            if order:
                res.so_approved_date = order[0].confirmation_date                                    
    
    @api.multi
    def force_assign(self):        
        """ Changes state of picking to available if moves are confirmed or waiting.
        @return: True
        """        
        self.mapped('move_lines').filtered(lambda move: move.state in ['confirmed', 'waiting']).force_assign()
        
        for res in self:            
            delete_article_ids = self.env['stock.picking.article'].search([('reference','=',res.id)])
            if delete_article_ids:
                for delete in delete_article_ids:
                    delete.unlink()
            
            size24 = size25 = size26 = size27 =  size28 =  size29 =  size30 =  size31 =  size32 =  size33 =  size34 =  size35 =  size36 =  size37 =  size38 =  size39 =  size40 =  size41 =  size42 = 0
            sizexs =  sizes =  sizem =  sizel =  sizexl = sizexxl =  sizeal =  sizex =  sizey =  sizez = 0
            for line in res.pack_operation_product_ids:                
                current_article_ids = self.env['stock.picking.article'].search([
                    ('reference','=',res.id),
                    ('article_code','=',line.product_id.product_article_code)
                ])

                if current_article_ids:
                    if line.product_id.product_size_id.name == "24":
                        current_article_ids[0].size24 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "25":
                        current_article_ids[0].size25 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "26":
                        current_article_ids[0].size26 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "27":
                        current_article_ids[0].size27 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "28":
                        current_article_ids[0].size28 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "29":
                        current_article_ids[0].size29 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "30":
                        current_article_ids[0].size30 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "31":
                        current_article_ids[0].size31 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "32":
                        current_article_ids[0].size32 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "33":
                        current_article_ids[0].size33 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "34":
                        current_article_ids[0].size34 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "35":
                        current_article_ids[0].size35 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "36":
                        current_article_ids[0].size36 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "37":
                        current_article_ids[0].size37 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "38":
                        current_article_ids[0].size38 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "39":
                        current_article_ids[0].size39 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "40":
                        current_article_ids[0].size40 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "41":
                        current_article_ids[0].size41 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "42":
                        current_article_ids[0].size42 = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "XS":
                        current_article_ids[0].sizexs = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "S":
                        current_article_ids[0].sizes = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "M":
                        current_article_ids[0].sizem = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "L":
                        current_article_ids[0].sizel = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "XL":
                        current_article_ids[0].sizexl = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "XXL":
                        current_article_ids[0].sizexxl = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "AL":
                        current_article_ids[0].sizeal = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "X":
                        current_article_ids[0].sizex = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "Y":
                        current_article_ids[0].sizey = int(int(current_article_ids[0].size24) + line.product_qty)
                    elif line.product_id.product_size_id.name == "Z":
                        current_article_ids[0].sizez = int(int(current_article_ids[0].size24) + line.product_qty)
                else:
                    if line.product_id.product_size_id.name == "24":
                        size24 += line.product_qty
                    elif line.product_id.product_size_id.name == "25":
                        size25 += line.product_qty
                    elif line.product_id.product_size_id.name == "26":
                        size26 += line.product_qty
                    elif line.product_id.product_size_id.name == "27":
                        size27 += line.product_qty
                    elif line.product_id.product_size_id.name == "28":
                        size28 += line.product_qty
                    elif line.product_id.product_size_id.name == "29":
                        size29 += line.product_qty
                    elif line.product_id.product_size_id.name == "30":
                        size30 += line.product_qty
                    elif line.product_id.product_size_id.name == "31":
                        size31 += line.product_qty
                    elif line.product_id.product_size_id.name == "32":
                        size32 += line.product_qty
                    elif line.product_id.product_size_id.name == "33":
                        size33 += line.product_qty
                    elif line.product_id.product_size_id.name == "34":
                        size34 += line.product_qty
                    elif line.product_id.product_size_id.name == "35":
                        size35 += line.product_qty
                    elif line.product_id.product_size_id.name == "36":
                        size36 += line.product_qty
                    elif line.product_id.product_size_id.name == "37":
                        size37 += line.product_qty
                    elif line.product_id.product_size_id.name == "38":
                        size38 += line.product_qty
                    elif line.product_id.product_size_id.name == "39":
                        size39 += line.product_qty
                    elif line.product_id.product_size_id.name == "40":
                        size40 += line.product_qty
                    elif line.product_id.product_size_id.name == "41":
                        size41 += line.product_qty
                    elif line.product_id.product_size_id.name == "42":
                        size42 += line.product_qty
                    elif line.product_id.product_size_id.name == "XS":
                        sizexs += line.product_qty
                    elif line.product_id.product_size_id.name == "S":
                        sizes += line.product_qty
                    elif line.product_id.product_size_id.name == "M":
                        sizem += line.product_qty
                    elif line.product_id.product_size_id.name == "L":
                        sizel += line.product_qty
                    elif line.product_id.product_size_id.name == "XL":
                        sizexl += line.product_qty
                    elif line.product_id.product_size_id.name == "XXL":
                        sizexxl += line.product_qty
                    elif line.product_id.product_size_id.name == "AL":
                        sizeal += line.product_qty
                    elif line.product_id.product_size_id.name == "X":
                        sizex += line.product_qty
                    elif line.product_id.product_size_id.name == "Y":
                        sizey += line.product_qty
                    elif line.product_id.product_size_id.name == "Z":
                        sizez += line.product_qty
                    
                    
                    self.env['stock.picking.article'].create({
                        'reference' : res.id,
                        'article_code' : line.product_id.product_article_code,
                        'product_id' : line.product_id.id,
                        'product_name' : line.product_id.name,
                        'size24' : size24,
                        'size25' : size25,
                        'size26' : size26,
                        'size27' : size27,
                        'size28' : size28,
                        'size29' : size29,
                        'size30' : size30,
                        'size31' : size31,
                        'size32' : size32,
                        'size33' : size33,
                        'size34' : size34,
                        'size35' : size35,
                        'size36' : size36,
                        'size37' : size37,
                        'size38' : size38,
                        'size39' : size39,
                        'size40' : size40,
                        'size41' : size41,
                        'size42' : size42,
                        'sizexs' : sizexs,
                        'sizes' : sizes,
                        'sizem' : sizem,
                        'sizel' : sizel,
                        'sizexl' : sizexl,
                        'sizexxl' : sizexxl,
                        'sizeal' : sizeal,
                        'sizex' : sizex,
                        'sizey' : sizey,
                        'sizez' : sizez,                                                    
                    })
                    
        return True
    
    @api.multi
    def action_assign(self):
        """ Check availability of picking moves.
        This has the effect of changing the state and reserve quants on available moves, and may
        also impact the state of the picking as it is computed based on move's states.
        @return: True            
        """                                                            
        self.filtered(lambda picking: picking.state == 'draft').action_confirm()
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        if not moves:
            raise UserError(_('Nothing to check the availability for.'))
        moves.action_assign()              
        
        for res in self:            
            delete_article_ids = self.env['stock.picking.article'].search([('reference','=',res.id)])
            if delete_article_ids:
                for delete in delete_article_ids:
                    delete.unlink()
            
            size24 = size25 = size26 = size27 =  size28 =  size29 =  size30 =  size31 =  size32 =  size33 =  size34 =  size35 =  size36 =  size37 =  size38 =  size39 =  size40 =  size41 =  size42 = 0
            sizexs =  sizes =  sizem =  sizel =  sizexl = sizexxl =  sizeal =  sizex =  sizey =  sizez = 0
            for line in res.pack_operation_product_ids:                
                current_article_ids = self.env['stock.picking.article'].search([
                    ('reference','=',res.id),
                    ('article_code','=',line.product_id.product_article_code)
                ])

                if current_article_ids:
                    if line.product_id.product_size_id.name == "24":
                        current_article_ids[0].size24 = current_article_ids[0].size24 + line.product_qty
                    elif line.product_id.product_size_id.name == "25":
                        current_article_ids[0].size25 = current_article_ids[0].size25 + line.product_qty
                    elif line.product_id.product_size_id.name == "26":
                        current_article_ids[0].size26 = current_article_ids[0].size26 + line.product_qty
                    elif line.product_id.product_size_id.name == "27":
                        current_article_ids[0].size27 = current_article_ids[0].size27 + line.product_qty
                    elif line.product_id.product_size_id.name == "28":
                        current_article_ids[0].size28 = current_article_ids[0].size28 + line.product_qty
                    elif line.product_id.product_size_id.name == "29":
                        current_article_ids[0].size29 = current_article_ids[0].size29 + line.product_qty
                    elif line.product_id.product_size_id.name == "30":
                        current_article_ids[0].size30 = current_article_ids[0].size30 + line.product_qty
                    elif line.product_id.product_size_id.name == "31":
                        current_article_ids[0].size31 = current_article_ids[0].size31 + line.product_qty
                    elif line.product_id.product_size_id.name == "32":
                        current_article_ids[0].size32 = current_article_ids[0].size32 + line.product_qty
                    elif line.product_id.product_size_id.name == "33":
                        current_article_ids[0].size33 = current_article_ids[0].size33 + line.product_qty
                    elif line.product_id.product_size_id.name == "34":
                        current_article_ids[0].size34 = current_article_ids[0].size34 + line.product_qty
                    elif line.product_id.product_size_id.name == "35":
                        current_article_ids[0].size35 = current_article_ids[0].size35 + line.product_qty
                    elif line.product_id.product_size_id.name == "36":
                        current_article_ids[0].size36 = current_article_ids[0].size36 + line.product_qty
                    elif line.product_id.product_size_id.name == "37":
                        current_article_ids[0].size37 = current_article_ids[0].size37 + line.product_qty
                    elif line.product_id.product_size_id.name == "38":
                        current_article_ids[0].size38 = current_article_ids[0].size38 + line.product_qty
                    elif line.product_id.product_size_id.name == "39":
                        current_article_ids[0].size39 = current_article_ids[0].size39 + line.product_qty
                    elif line.product_id.product_size_id.name == "40":
                        current_article_ids[0].size40 = current_article_ids[0].size40 + line.product_qty
                    elif line.product_id.product_size_id.name == "41":
                        current_article_ids[0].size41 = current_article_ids[0].size41 + line.product_qty
                    elif line.product_id.product_size_id.name == "42":
                        current_article_ids[0].size42 = current_article_ids[0].size42 + line.product_qty
                    elif line.product_id.product_size_id.name == "XS":
                        current_article_ids[0].sizexs = current_article_ids[0].sizexs + line.product_qty
                    elif line.product_id.product_size_id.name == "S":
                        current_article_ids[0].sizes = current_article_ids[0].sizes + line.product_qty
                    elif line.product_id.product_size_id.name == "M":
                        current_article_ids[0].sizem = current_article_ids[0].sizem + line.product_qty
                    elif line.product_id.product_size_id.name == "L":
                        current_article_ids[0].sizel = current_article_ids[0].sizel + line.product_qty
                    elif line.product_id.product_size_id.name == "XL":
                        current_article_ids[0].sizexl = current_article_ids[0].sizexl + line.product_qty
                    elif line.product_id.product_size_id.name == "XXL":
                        current_article_ids[0].sizexxl = current_article_ids[0].sizexxl + line.product_qty
                    elif line.product_id.product_size_id.name == "AL":
                        current_article_ids[0].sizeal = current_article_ids[0].sizeal + line.product_qty
                    elif line.product_id.product_size_id.name == "X":
                        current_article_ids[0].sizex = current_article_ids[0].sizex + line.product_qty
                    elif line.product_id.product_size_id.name == "Y":
                        current_article_ids[0].sizey = current_article_ids[0].sizey + line.product_qty
                    elif line.product_id.product_size_id.name == "Z":
                        current_article_ids[0].sizez = current_article_ids[0].sizez + line.product_qty
                else:
                    if line.product_id.product_size_id.name == "24":
                        size24 += line.product_qty
                    elif line.product_id.product_size_id.name == "25":
                        size25 += line.product_qty
                    elif line.product_id.product_size_id.name == "26":
                        size26 += line.product_qty
                    elif line.product_id.product_size_id.name == "27":
                        size27 += line.product_qty
                    elif line.product_id.product_size_id.name == "28":
                        size28 += line.product_qty
                    elif line.product_id.product_size_id.name == "29":
                        size29 += line.product_qty
                    elif line.product_id.product_size_id.name == "30":
                        size30 += line.product_qty
                    elif line.product_id.product_size_id.name == "31":
                        size31 += line.product_qty
                    elif line.product_id.product_size_id.name == "32":
                        size32 += line.product_qty
                    elif line.product_id.product_size_id.name == "33":
                        size33 += line.product_qty
                    elif line.product_id.product_size_id.name == "34":
                        size34 += line.product_qty
                    elif line.product_id.product_size_id.name == "35":
                        size35 += line.product_qty
                    elif line.product_id.product_size_id.name == "36":
                        size36 += line.product_qty
                    elif line.product_id.product_size_id.name == "37":
                        size37 += line.product_qty
                    elif line.product_id.product_size_id.name == "38":
                        size38 += line.product_qty
                    elif line.product_id.product_size_id.name == "39":
                        size39 += line.product_qty
                    elif line.product_id.product_size_id.name == "40":
                        size40 += line.product_qty
                    elif line.product_id.product_size_id.name == "41":
                        size41 += line.product_qty
                    elif line.product_id.product_size_id.name == "42":
                        size42 += line.product_qty
                    elif line.product_id.product_size_id.name == "XS":
                        sizexs += line.product_qty
                    elif line.product_id.product_size_id.name == "S":
                        sizes += line.product_qty
                    elif line.product_id.product_size_id.name == "M":
                        sizem += line.product_qty
                    elif line.product_id.product_size_id.name == "L":
                        sizel += line.product_qty
                    elif line.product_id.product_size_id.name == "XL":
                        sizexl += line.product_qty
                    elif line.product_id.product_size_id.name == "XXL":
                        sizexxl += line.product_qty
                    elif line.product_id.product_size_id.name == "AL":
                        sizeal += line.product_qty
                    elif line.product_id.product_size_id.name == "X":
                        sizex += line.product_qty
                    elif line.product_id.product_size_id.name == "Y":
                        sizey += line.product_qty
                    elif line.product_id.product_size_id.name == "Z":
                        sizez += line.product_qty                                        
                    
                    self.env['stock.picking.article'].create({
                        'reference' : res.id,
                        'article_code' : line.product_id.product_article_code,
                        'product_id' : line.product_id.id,
                        'product_name' : line.product_id.name,
                        'size24' : size24,
                        'size25' : size25,
                        'size26' : size26,
                        'size27' : size27,
                        'size28' : size28,
                        'size29' : size29,
                        'size30' : size30,
                        'size31' : size31,
                        'size32' : size32,
                        'size33' : size33,
                        'size34' : size34,
                        'size35' : size35,
                        'size36' : size36,
                        'size37' : size37,
                        'size38' : size38,
                        'size39' : size39,
                        'size40' : size40,
                        'size41' : size41,
                        'size42' : size42,
                        'sizexs' : sizexs,
                        'sizes' : sizes,
                        'sizem' : sizem,
                        'sizel' : sizel,
                        'sizexl' : sizexl,
                        'sizexxl' : sizexxl,
                        'sizeal' : sizeal,
                        'sizex' : sizex,
                        'sizey' : sizey,
                        'sizez' : sizez,                                                    
                    })
                                                                  
        return True

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    customer_type = fields.Selection([('JEANS STORE','JEANS STORE'),('WHOLESALE','WHOLESALE'),('CORPORATE','CORPORATE'),('CONSIGNMENT','CONSIGNMENT'),('RETAIL_ONLINE', 'RETAIL ONLINE')], string='Customer Type')
    partner_margin = fields.Float(compute="_get_partner_margin", string='Margin')    
    total_margin = fields.Float(compute="_get_total_margin", string='Total Margin', digits=dp.get_precision('Product Unit of Measure'))
    total_available_stock = fields.Float(compute="_get_total_available_stock", string='Available Stock', digits=dp.get_precision('Product Unit of Measure'))
    total_available_value = fields.Float(compute="_get_total_available_value", string='Total Available', digits=dp.get_precision('Product Unit of Measure'))
    total_before_discount = fields.Float(compute="_get_total_before_discount", string='Total Before Disc', digits=dp.get_precision('Product Unit of Measure'))
    total_after_discount = fields.Float(compute="_get_total_after_discount", string='Total After Disc', digits=dp.get_precision('Product Unit of Measure'))        
    amount_total_qty = fields.Float(compute="_get_amount_total_qty", string='Total Qty', digits=dp.get_precision('Product Unit of Measure'))
    date_delivery = fields.Date('Delivery Date')
    reference_invoice = fields.Char('Invoice Reference')    

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'date_order' in vals:
            soi_ids = self.env['sale.order.line'].search([('order_id', '=', self.id)])
            for soi in soi_ids:
                soi.write({'order_date':self.date_order})
        return res

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        if self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.user_id:
            values['user_id'] = self.partner_id.user_id.id
        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
            
        if self.partner_id:
            self.customer_type = self.partner_id.customer_type
            self.type_id = self.partner_id.sale_type

        self.update(values)
        
    @api.depends('picking_ids')
    def _get_total_available_stock(self):
        for order in self:
            total_available_stock = 0.0                    
            for picking in order.picking_ids:
                total_available_stock += picking.amount_total_qty                            
            order.total_available_stock = total_available_stock
            
    @api.depends('amount_total','amount_total_qty','total_available_stock')
    def _get_total_available_value(self):
        for order in self:
            total_available_value = 0.0                    
            total_available_value = order.total_available_stock * order.amount_total / (order.amount_total_qty or 1)                                                                    
            order.total_available_value = total_available_value              
            
    @api.depends('order_line')
    def _get_total_before_discount(self):
        for order in self:
            total_before_discount = 0.0                    
            for line in order.order_line:
                total_before_discount += line.price_subtotal
            order.total_before_discount = total_before_discount

    @api.depends('order_line')
    def _get_total_after_discount(self):
        for order in self:
            total_after_discount = 0.0                    
            for line in order.order_line:
                total_after_discount += line.price_subtotal                            
            order.total_after_discount = total_after_discount
            
    @api.depends('order_line', 'partner_id', 'partner_margin')
    def _get_total_margin(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0                    
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax                
            order.total_margin = (amount_untaxed + amount_tax) * order.partner_margin / 100
                
    @api.depends('order_line', 'partner_id', 'partner_margin')
    def _amount_all(self):        
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            total_margin = (amount_untaxed + amount_tax) * order.partner_margin / 100
            amount_total = amount_untaxed + amount_tax - total_margin            
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_total,
            })
            
    @api.depends('partner_id')
    def _get_partner_margin(self):
        for res in self:                        
            if res.partner_id:
                res.partner_margin = res.partner_id.margin                                    
            
    @api.depends('order_line')
    def _get_amount_total_qty(self):
        for res in self:
            amount_total_qty = 0
            for line in res.order_line:
                amount_total_qty += line.product_uom_qty
            res.amount_total_qty = amount_total_qty                                                             
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = 'name asc, product_id asc'
    
    manual_discount = fields.Float('Extra Discount')
    order_date = fields.Date(compute="_get_order_date", string='Order Date', store=True) 
    #total_with_tax = fields.Float(string='Total',compute="_compute_amount", store=True)
    is_special_price = fields.Boolean('Is SP', default=False, readonly=True)
    
    @api.depends('order_id')
    def _get_order_date(self):
        for res in self:
            if res.order_id:
                res.order_date = res.order_id.date_order
        
    @api.depends('product_uom_qty', 'discount', 'manual_discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            #price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            price = (line.price_unit * (1 - (line.discount or 0.0) / 100.0) * (1 - (line.manual_discount or 0.0) / 100.0))
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                #'total_with_tax': line.price_unit * line.product_uom_qty,
            })
            
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        #name = product.name_get()[0][1]
        name = product.name
        if product.product_category3_id.name:
            name = product.product_category3_id.name
        elif product.product_category5_id.name:
            name = product.product_category5_id.name 
        #=======================================================================
        # el product.description_sale:
        #     name += '\n' + product.description_sale
        #=======================================================================
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product), product.taxes_id, self.tax_id)
        self.update(vals)

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product.sale_line_warn == 'block':
                self.product_id = False
            return {'warning': warning}
        return {'domain': domain}

    
class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_rack = fields.Boolean('is rack', default="False")
        
    @api.multi
    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            #===================================================================
            # code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            # if code:
            #     name = '[%s] %s' % (code,name)
            #===================================================================
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []
        for product in self.sudo():
            # display only the attributes with multiple possible values on the template
            variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id')
            variant = product.attribute_value_ids._variant_name(variable_attributes)

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = []
            if partner_ids:
                sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and (x.product_id == product)]
                if not sellers:
                    sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and not x.product_id]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': seller_variant or name,
                              'default_code': s.product_code or product.default_code,
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': product.default_code,                          
                          }
                result.append(_name_get(mydict))
        return result
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            products = self.env['product.product']
            if operator in positive_operators:
                products = self.search([('default_code', '=', name)] + args, limit=limit)
                if not products:
                    products = self.search([('barcode', '=', name)] + args, limit=limit)
            if not products and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                products = self.search(args + [('default_code', operator, name)], limit=limit)
                if not limit or len(products) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(products)) if limit else False
                    products += self.search(args + [('name', operator, name), ('id', 'not in', products.ids)], limit=limit2)
            elif not products and operator in expression.NEGATIVE_TERM_OPERATORS:
                products = self.search(args + ['&', ('default_code', operator, name), ('name', operator, name)], limit=limit)
            if not products and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    products = self.search([('default_code', '=', res.group(2))] + args, limit=limit)
            # still no results, partner in context: search on supplier info as last hope to find something
            if not products and self._context.get('partner_id'):
                suppliers = self.env['product.supplierinfo'].search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)])
                if suppliers:
                    products = self.search([('product_tmpl_id.seller_ids', 'in', suppliers.ids)], limit=limit)
        else:
            products = self.search(args, limit=limit)
        return products.name_get()
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    product_pocket_id = fields.Many2one('lea.product.pocket', 'Pocket', copy=True)
    product_sleeve_id = fields.Many2one('lea.product.sleeve', 'Sleeve', copy=True)
    product_color_id = fields.Many2one('lea.product.color', 'Color', copy=True)
    product_embeded_id = fields.Many2one('lea.product.embeded', 'Embeded', copy=True)
    product_raw_material_id = fields.Many2one('lea.product.raw.material', 'Raw Material', copy=True)
    product_fitting_category_id = fields.Many2one('lea.product.fitting.category', 'Fitting Category', copy=True)
    product_sex_category_id = fields.Many2one('lea.product.sex.category', 'Sex Category', copy=True)
    product_style_id = fields.Many2one('lea.product.style', 'Style', copy=True)
    product_moving_status_id = fields.Many2one('lea.product.moving.status', 'Moving Status', copy=True)
    product_selling_group_id = fields.Many2one('lea.product.selling.group', 'Selling Group', copy=True)
    product_qc_group_id = fields.Many2one('lea.product.qc.group', 'QC Group', copy=True)
    product_class_category_id = fields.Many2one('lea.product.class.category', 'Class Category', copy=True)
    product_category_id = fields.Many2one('lea.product.category', 'Category', copy=True)
    product_label_id = fields.Many2one('lea.product.label', 'Label', copy=True)

    
    product_size_id = fields.Many2one('lea.product.size', 'Size', copy=True)
    product_class_id = fields.Many2one('lea.product.class', 'Class', copy=True)
    product_category1_id = fields.Many2one('lea.product.category1', 'Category 1', copy=True)
    product_category2_id = fields.Many2one('lea.product.category2', 'Category 2', copy=True)
    product_category3_id = fields.Many2one('lea.product.category3', 'Category 3', copy=True)
    product_category4_id = fields.Many2one('lea.product.category4', 'Category 4', copy=True)
    product_category5_id = fields.Many2one('lea.product.category5', 'Category 5', copy=True)
    product_category6_id = fields.Many2one('lea.product.category6', 'Category 6', copy=True)
    product_sourcing_id = fields.Many2one('lea.product.sourcing', 'Sourcing', copy=True)
    product_material_group_id = fields.Many2one('lea.product.material.group', 'Material Group', copy=True)
    product_material_type_id = fields.Many2one('lea.product.material.type', 'Material Type', copy=True)
    product_material_category_id = fields.Many2one('lea.product.material.category', 'Material Category', copy=True)
    product_stock_type_id = fields.Many2one('lea.product.stock.type', 'Stock Type', copy=True)
    product_fitting_id = fields.Many2one('lea.product.fitting', 'Fitting', copy=True)
    product_brand_id = fields.Many2one('lea.product.brand', 'Brand', copy=True)
    product_warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse ID', copy=True)
    product_article_code = fields.Char('Article Code', copy=True)
    product_desc = fields.Text('Product Description', copy=True)
    product_specification = fields.Char('Product Specification', copy=True)
    product_sub_location = fields.Char('Product Sub Location', copy=True)
    product_short_name = fields.Char('Product Name', copy=True)
    rack_ids = fields.One2many('lea.product.column', 'reference', 'Racks')    
    racknew_ids = fields.One2many('lea.product.rack', 'reference', 'Racks')    
    
    @api.onchange('product_article_code', 'product_short_name', 'barcode', 'product_size_id')
    def onchange_product_article_code(self):
        for res in self:
            res.barcode = False
            res.name = False            
            if res.product_size_id:
                res.barcode = (res.product_article_code or '') + '..' + (res.product_size_id.name or '')
                res.name = (res.barcode or '') + ' ' + (res.product_short_name or '')
                res.default_code = res.barcode
            elif not res.product_size_id:                
                res.name = res.product_short_name or ''
                res.default_code = res.product_article_code
        
class Partner(models.Model):
    _inherit = 'res.partner'
        
    related_user_id = fields.Many2one('res.users', 'Related User')
    customer_type = fields.Selection([('JEANS STORE','JEANS STORE'),('WHOLESALE','WHOLESALE'),('CORPORATE','CORPORATE'),('CONSIGNMENT','CONSIGNMENT'),('RETAIL_ONLINE', 'RETAIL ONLINE')], string='Customer Type', default='WHOLESALE')
    customer_code = fields.Char('Customer/Supplier Code')    
    store_owner = fields.Char('Store Owner')
    credit_limit = fields.Float('Credit Limit')
    margin = fields.Float('Margin')
    facebook_id = fields.Char('Facebook')
    twitter_id = fields.Char('Twitter')
    instagram_id = fields.Char('Instagram')
    npwp_id = fields.Char('NPWP ID')
    gender = fields.Selection([('Male', 'Male'), ('Female', 'Female')], string='Gender', default='Male')
    npwp_name = fields.Char('NPWP Name')
    pkp_id = fields.Char('PKP ID')    
    tanggal_pengukuhan = fields.Char('Tanggal Pengukuhan')
    area_id = fields.Many2one('lea.area', string='Area')
    sub_area_id = fields.Many2one('lea.sub.area', string='Sub Area')
    dob = fields.Date('Date of Birth')
    age = fields.Integer(compute="_compute_age", string='Age')    
    pkp_status = fields.Selection([('PKP', 'PKP'), ('NPKP', 'NPKP')], string='PKP/NPKP', default='PKP')
    identity_ids = fields.One2many('lea.identity', 'reference', 'Identity') #unuse
    status_margin = fields.Selection([('To Approve','To Approve'),('Sales Approved','Sales Approved'),('Accounting Approved','Accounting Approved')], string="Status Margin", default="To Approve")
    status_limit = fields.Selection([('To Approve','To Approve'),('Sales Approved','Sales Approved')], string="Status Limit", default="To Approve")
    

    #new by mario ardi
    identity_type       = fields.Many2one('lea.identity.type', 'Identity Type')
    identity_number     = fields.Char('Identity No.')
    identity_file       = fields.Binary('Identity File')
    identity_filename   = fields.Char('Identity Filename')
    whatsapp            = fields.Char('Whatsapp')
    phone_secondary     = fields.Char('Secondary Phone')
    
    taxation_street = fields.Char('Street')
    taxation_street2 = fields.Char('Street 2')
    taxation_blok = fields.Char('Blok', size=8)
    taxation_nomor = fields.Char('Nomor', size=8)
    taxation_rt = fields.Char('RT', size=3)
    taxation_rw = fields.Char('RW', size=3)
    taxation_kelurahan_id = fields.Many2one('res.kelurahan', string="Kelurahan")
    taxation_kecamatan_id = fields.Many2one('res.kecamatan', string="Kecamatan")
    taxation_kabupaten_id = fields.Many2one('res.kabupaten', string="Kabupaten")
    taxation_state_id = fields.Many2one('res.country.state', string="State")
    taxation_postal_code = fields.Char('Kode POS')
    taxation_country_id = fields.Many2one('res.country', string="Country")
    
    #BILLING ADDRESS
    billing_name = fields.Char('Billing Name')
    billing_from_main = fields.Boolean('Copy from main address', default=False)
    billing_street = fields.Char('Street')
    billing_street2 = fields.Char('Street 2')
    billing_blok = fields.Char('Blok', size=8)
    billing_nomor = fields.Char('Nomor', size=8)
    billing_rt = fields.Char('RT', size=3)
    billing_rw = fields.Char('RW', size=3)
    billing_kelurahan_id = fields.Many2one('res.kelurahan', string="Kelurahan")
    billing_kecamatan_id = fields.Many2one('res.kecamatan', string="Kecamatan")
    billing_kabupaten_id = fields.Many2one('res.kabupaten', string="Kabupaten")
    billing_state_id = fields.Many2one('res.country.state', string="State")
    billing_postal_code = fields.Char('Kode POS')
    billing_country_id = fields.Many2one('res.country', string="Country")

    #SHIPPING ADDRESS
    shipping_name = fields.Char('Shipping Name')
    shipping_from_main = fields.Boolean('Copy from main address', default=False)
    shipping_street = fields.Char('Street')
    shipping_street2 = fields.Char('Street 2')
    shipping_blok = fields.Char('Blok', size=8)
    shipping_nomor = fields.Char('Nomor', size=8)
    shipping_rt = fields.Char('RT', size=3)
    shipping_rw = fields.Char('RW', size=3)
    shipping_kelurahan_id = fields.Many2one('res.kelurahan', string="Kelurahan")
    shipping_kecamatan_id = fields.Many2one('res.kecamatan', string="Kecamatan")
    shipping_kabupaten_id = fields.Many2one('res.kabupaten', string="Kabupaten")
    shipping_state_id = fields.Many2one('res.country.state', string="State")
    shipping_postal_code = fields.Char('Kode POS')
    shipping_country_id = fields.Many2one('res.country', string="Country")

    #CONTRACT
    contract_no = fields.Char('Contract No.')
    contract_date = fields.Date('Contract Date')
    contract_start_date = fields.Date('Start Date Contract')
    contract_end_date = fields.Date('End Date Contract')
    warehouse_code = fields.Char('Warehouse Code', size=6)

    #LOYALTY
    loyalty_lpc_no = fields.Char('LPC No.')
    loyalty_lpc_date = fields.Date('LPC Date')
    loyalty_lpc_valid_date = fields.Date('LPC Valid Date')
    loyalty_shopping_amount = fields.Float('Shopping Amount', compute="_compute_shopping_amount")
    loyalty_lpc_class = fields.Selection([
        ('regular','Regular'),
        ('premium_silver','Premium Silver'),
        ('premium_gold','Premium Gold'),
        ('premium_platinum','Premium Platinum'),
    ], compute="_compute_shopping_amount", string='LPC Class')
    loyalty_dob = fields.Date('Date of Birth')
    loyalty_age = fields.Integer(compute="_compute_loyalty_age", string='Age', store=True)
    loyalty_gender = fields.Selection([('Male', 'Male'), ('Female', 'Female')], string='Gender')
    loyalty_title = fields.Many2one('res.partner.title','Title')
    loyalty_points_has_been_redeem = fields.Integer('Points has been redeem', compute='_compute_points')
    loyalty_points_expired = fields.Integer('Points Expired', compute='_compute_points')
    
    counting_margin_ids = fields.One2many(comodel_name='res.partner.counting.margin', inverse_name='partner_id', string='Counting Margin')
    type_counting_margin    = fields.Selection([('ds1p','DS1P'),('ds2p','DS2P'),('tpp','TPP'),('ds1n','DS1N'),('ds2n','DS2N'),('tpn','TPN')], string='Type Counting Margin')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('customer_code', operator, name)]
        partner_ids = self.search(domain + args, limit=limit)
        return partner_ids.name_get()

    @api.multi
    def _compute_points(self):    
        for record in self:
            record.loyalty_points_has_been_redeem = 0
            record.loyalty_points_expired = 0

    @api.multi
    def _compute_shopping_amount(self):                
        for record in self:                    
            total = 0
            lpc_class = ''
            
            #search on sale order
            order_ids = self.env['sale.order'].search([
                ('partner_id.id','=',record.id),
                ('state','in',['sale','done']),
            ])

            total += sum(line.amount_total for line in order_ids)

            #search on pos order
            order_ids = self.env['pos.order'].search([
                ('partner_id.id','=',record.id),
                ('state','in',['paid','done','invoiced','credited']),
            ])

            total += sum(line.amount_total for line in order_ids)

            if total >= 100000 and total < 2500000:
                lpc_class = 'regular'
            elif total >= 2500000 and total < 5000000:
                lpc_class = 'premium_silver'
            elif total >= 5000000 and total < 10000000:
                lpc_class = 'premium_gold'
            elif total >= 10000000:
                lpc_class = 'premium_platinum'

            record.loyalty_shopping_amount = total
            record.loyalty_lpc_class = lpc_class

    @api.depends('loyalty_age')
    def _compute_loyalty_age(self):                
        delta_year = 0        
        for record in self:                    
            if record.loyalty_dob:
                born = datetime.strptime(record.loyalty_dob,"%Y-%m-%d")
                today = datetime.today()                                                     
                born_month = born.strftime('%m')
                today_month = today.strftime('%m')
                born_year = born.strftime('%Y')
                today_year = int(today.strftime('%Y'))                    
                if today_month > born_month:
                    delta_year = int(today_year) - int(born_year) + 1
                elif today_month < born_month:
                    delta_year = int(today_year) - int(born_year)                        
                elif today_month == born_month:
                    delta_year = int(today_year) - int(born_year)                                                                                                                                                                                                                                        
                         
            record.loyalty_age = delta_year

    @api.onchange('name')
    def onchange_main_partner_name(self):
        self.billing_name = self.name
        self.shipping_name = self.name

    @api.onchange('billing_from_main')
    def onchange_billing_from_main(self):
        if self.billing_from_main == True:
            self.billing_street         = self.street
            self.billing_street2        = self.street2
            self.billing_blok           = self.blok
            self.billing_nomor          = self.nomor
            self.billing_rt             = self.rt
            self.billing_rw             = self.rw
            self.billing_kelurahan_id   = self.kelurahan_id.id
            self.billing_kecamatan_id   = self.kecamatan_id.id
            self.billing_kabupaten_id   = self.kabupaten_id.id
            self.billing_state_id       = self.state_id.id
            self.billing_postal_code    = self.zip
            self.billing_country_id     = self.country_id.id

    @api.onchange('shipping_from_main')
    def onchange_shipping_from_main(self):
        if self.shipping_from_main == True:
            self.shipping_street         = self.street
            self.shipping_street2        = self.street2
            self.shipping_blok           = self.blok
            self.shipping_nomor          = self.nomor
            self.shipping_rt             = self.rt
            self.shipping_rw             = self.rw
            self.shipping_kelurahan_id   = self.kelurahan_id.id
            self.shipping_kecamatan_id   = self.kecamatan_id.id
            self.shipping_kabupaten_id   = self.kabupaten_id.id
            self.shipping_state_id       = self.state_id.id
            self.shipping_postal_code    = self.zip
            self.shipping_country_id     = self.country_id.id

    @api.multi
    def button_approve_margin_sales(self):
        for res in self:
            res.status_margin = "Sales Approved"
            
    @api.multi
    def button_approve_margin_accounting(self):
        for res in self:
            res.status_margin = "Accounting Approved"
    
    @api.multi
    def button_approve_limit_sales(self):
        for res in self:
            res.status_limit = "Sales Approved"
            
    @api.depends('dob')
    def _compute_age(self):                
        delta_year = 0        
        for record in self:                    
            if record.dob:
                born = datetime.strptime(record.dob,"%Y-%m-%d")
                today = datetime.today()                                                     
                born_month = born.strftime('%m')
                today_month = today.strftime('%m')
                born_year = born.strftime('%Y')
                today_year = int(today.strftime('%Y'))                    
                if today_month > born_month:
                    delta_year = int(today_year) - int(born_year) + 1
                elif today_month < born_month:
                    delta_year = int(today_year) - int(born_year)                        
                elif today_month == born_month:
                    delta_year = int(today_year) - int(born_year)                                                                                                                                                                                                                                        
                         
            record.age = delta_year

class ResPartnerCountingMargin(models.Model):
    _name = 'res.partner.counting.margin'
    _rec_name = 'partner_id'
    
    partner_id = fields.Many2one(comodel_name='res.partner',string='Partner')        
    discount_to_customer = fields.Float(string='Discount to Customer (%)')
    share_discount = fields.Float(string='Share Discount (%)')
    count_nett_margin = fields.Boolean(string='Count Net Margin')
    margin = fields.Float(string='Margin (%)')
    nett_margin = fields.Float(string='Net Margin (%)')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

class Users(models.Model):
    _inherit = 'res.users'
            
    vendor_id = fields.Many2one('res.partner', string='Related Vendor')
    area_id = fields.Many2one('lea.area', string='Area')
    sub_area_id = fields.Many2one('lea.sub.area', string='Sub Area')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    pos_id = fields.Many2one('pos.config', string='Store')
    target_sales = fields.Float(string='Target Penjualan (Rp.)')
    
class AccountInvoiceArticle(models.Model):
    _name = 'account.invoice.article'
    
    reference = fields.Many2one('account.invoice', 'Reference')
    article_code = fields.Char('Article Code')
    product_id = fields.Many2one('product.product', 'Product')
    product_name = fields.Char('Product Name')
    qty = fields.Integer('Qty')
    price_unit = fields.Float('Price Unit')
    price_subtotal = fields.Float(compute="_get_price_subtotal", string='Subtotal')
    
    @api.depends('price_unit', 'qty')
    def _get_price_subtotal(self):
        for res in self:
            res.price_subtotal = res.price_unit * res.qty
        
    
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
            
    article_code_ids = fields.One2many('account.invoice.article', 'reference', 'Article Code') 
    partner_margin_invoice = fields.Float(compute="_get_partner_margin_invoice", string='Margin')      
    total_before_discount = fields.Float(compute="_get_total_before_discount_invoice", string='Total Amount', digits=dp.get_precision('Product Unit of Measure'))
    total_discount = fields.Float(compute="_get_total_discount", string='Total Discount', digits=dp.get_precision('Product Unit of Measure'))
    total_margin_invoice = fields.Float(compute="_get_total_margin_invoice", string='Total Margin', digits=dp.get_precision('Product Unit of Measure'))  
    amount_total_qty = fields.Float(compute="_get_amount_total_qty_invoice", string='Total Qty', digits=dp.get_precision('Product Unit of Measure'))
    amount_discount_acara = fields.Float(compute="_get_amount_discount_acara", string='Discount Acara', store=False)
    amount_discount_non_pkp = fields.Float(compute="_get_amount_discount_non_pkp", string='Discount Non PKP', store=False)
    number_of_print = fields.Integer(string='Number of Print', readonly=True)
    number_internal_retur = fields.Char(string='Internal Retur No.')
    update_val = fields.Boolean(string='Update Val')
    picking_id = fields.Many2one("stock.picking", string="No. DO")
    first_invoice_id = fields.Many2one("account.invoice", string="No. Invoice Asal", compute="_get_invoice")

    @api.multi
    def button_update_val(self):
        for res in self:
            res.write({'update_val': True})

    @api.depends('origin')
    def _get_invoice(self):
        for invoice in self:
            invoice_id = False
            invoice_ids = self.env['account.invoice'].search([('number', '=', invoice.origin)])
            if invoice_ids:
                invoice_id = invoice_ids[0].id
            invoice.first_invoice_id = invoice_id


    def group_lines(self, iml, line):
        """Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
        if self.journal_id.group_invoice_lines:
            line2 = {}
            for x, y, l in line:
                tmp = self.inv_line_characteristic_hashcode(l)
                if tmp in line2:
                    am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                    line2[tmp]['debit'] = (am > 0) and am or 0.0
                    line2[tmp]['credit'] = (am < 0) and -am or 0.0
                    line2[tmp]['amount_currency'] += l['amount_currency']
                    line2[tmp]['analytic_line_ids'] += l['analytic_line_ids']
                    qty = l.get('quantity')
                    if qty:
                        line2[tmp]['quantity'] = line2[tmp].get('quantity', 0.0) + qty
                else:
                    line2[tmp] = l
            line = []
            for key, val in line2.items():
                line.append((0, 0, val))
                
        return line
    
    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        for res in self:            
            delete_article_ids = self.env['account.invoice.article'].search([('reference','=',res.id)])
            if delete_article_ids:
                for delete in delete_article_ids:
                    delete.unlink()
                    
            for line in res.invoice_line_ids:
                current_article_ids = self.env['account.invoice.article'].search([('reference','=',res.id),('article_code','=',line.product_id.product_article_code)])
                if current_article_ids:
                    current_article_ids[0].qty += int(line.quantity)
                else:
                    self.env['account.invoice.article'].create({
                        'reference' : res.id,
                        'article_code' : line.product_id.product_article_code,
                        'product_id' : line.product_id.id,
                        'product_name' : line.product_id.name,
                        'qty' : int(line.quantity),
                        'price_unit' : line.price_unit,
                    })
            
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'account.report_invoice')


    @api.depends('invoice_line_ids')
    def _get_total_before_discount_invoice(self):
        for invoice in self:
            total_before_discount = 0.0                    
            for line in invoice.invoice_line_ids:
                # total_before_discount += line.price_subtotal
                # total_before_discount += line.lea_line_amount
                total_before_discount += line.subtotal_invoice
            invoice.total_before_discount = total_before_discount

    @api.depends('invoice_line_ids')
    def _get_total_discount(self):
        for invoice in self:
            total_discount_invoice = 0.0                    
            for line in invoice.invoice_line_ids:
                # total_discount_invoice += line.price_discount + line.lea_share_discount                          
                if invoice.partner_id.type_counting_margin in ['tpp','tpn']:
                    total_discount_invoice += line.price_discount                          
                else:
                    total_discount_invoice += line.lea_share_discount                          
            invoice.total_discount = total_discount_invoice


    @api.depends('partner_id')
    def _get_partner_margin_invoice(self):
        for res in self:                        
            if res.partner_id:
                res.partner_margin_invoice = res.partner_id.margin 


    @api.depends('invoice_line_ids', 'partner_id', 'partner_margin_invoice')
    def _get_total_margin_invoice(self):
        for invoice in self:
            total = 0.0                    
            for line in invoice.invoice_line_ids:
                total += line.lea_margin            
            invoice.total_margin_invoice = total


    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice', 'partner_margin_invoice','update_val')
    def _compute_amount(self):
        if self.type == 'out_invoice' or 'out_refund':
            total_dpp = 0
            for line in self.invoice_line_ids:
                total_dpp += line.lea_dpp

            total_margin = 0
            for line in self.invoice_line_ids:
                total_margin += line.lea_margin

            # self.amount_untaxed = self.total_before_discount - (self.total_discount + self.total_margin_invoice)
            self.amount_untaxed = total_dpp
            # self.amount_untaxed = total_dpp
            # self.amount_tax = self.amount_untaxed * 0.1
            # self.amount_tax = sum(line.amount for line in self.tax_line_ids)
            self.amount_tax = int(0.10 * self.amount_untaxed)
            # self.amount_total = self.amount_untaxed + self.amount_tax
            # self.amount_total = self.amount_untaxed + self.amount_tax
            self.amount_total = self.total_before_discount - self.total_discount - self.total_margin_invoice + self.amount_tax
            amount_total_company_signed = self.amount_total
            amount_untaxed_signed = self.amount_untaxed
            if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
                currency_id = self.currency_id.with_context(date=self.date_invoice)
                amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
                amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
            sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
            self.amount_total_company_signed = amount_total_company_signed * sign
            self.amount_total_signed = self.amount_total * sign
            self.amount_untaxed_signed = amount_untaxed_signed * sign
        else :
            self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
            self.amount_tax = sum(line.amount for line in self.tax_line_ids)
            self.amount_total = self.amount_untaxed + self.amount_tax
            amount_total_company_signed = self.amount_total
            amount_untaxed_signed = self.amount_untaxed
            if self.currency_id and self.currency_id != self.company_id.currency_id:
                currency_id = self.currency_id.with_context(date=self.date_invoice)
                amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
                amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
            sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
            self.amount_total_company_signed = amount_total_company_signed * sign
            self.amount_total_signed = self.amount_total * sign
            self.amount_untaxed_signed = amount_untaxed_signed * sign


    @api.depends('invoice_line_ids')
    def _get_amount_total_qty_invoice(self):
        for res in self:
            amount_total_qty = 0
            for line in res.invoice_line_ids:
                amount_total_qty += line.quantity
            res.amount_total_qty = amount_total_qty

    def _get_amount_discount_acara(self):
        for res in self:
            # total_discount = 0
            # for line in self.invoice_line_ids:
            #     total_discount += line.price_discount
            res.amount_discount_acara = round((float(res.total_discount) / float(res.amount_untaxed+res.total_discount)) * 100.00,2)

    def _get_amount_discount_non_pkp(self):
        for res in self:
            res.amount_discount_non_pkp = round((float(res.total_before_discount) - float(res.amount_total)) / float(res.total_before_discount) * 100.00,2)

class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    subtotal_invoice = fields.Monetary(string='Amount Subtotal',
        store=True, readonly=True, compute='_compute_subtotal')

    price_discount = fields.Monetary(string='Price Discount',
        store=True, readonly=True, compute='_compute_subtotal')

    price_unit_base = fields.Monetary(string='Price Unit (Exclude PPN)',
        store=True, readonly=True, compute='_compute_subtotal')

    lea_line_amount = fields.Monetary(string='Line Amount',
        store=True, readonly=True, compute='_compute_subtotal')

    lea_share_discount = fields.Monetary(string='Share Discount',
        store=True, readonly=True, compute='_compute_subtotal')

    lea_margin = fields.Monetary(string='Margin',
        store=True, readonly=True, compute='_compute_subtotal')

    lea_dpp = fields.Monetary(string='DPP',
        store=True, readonly=True, compute='_compute_subtotal')

    lea_value_invoice = fields.Monetary(string='Subtotal',
        store=True, readonly=True, compute='_compute_subtotal')

    lea_net_amount = fields.Monetary(string='Net',
        store=True, readonly=True, compute='_compute_subtotal')

    lea_sell_price = fields.Monetary(string='Sell Price',
        store=True, readonly=True, compute='_compute_subtotal')

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_subtotal(self):

        if self.partner_id.code_transaction in ['01','02','03']:
            self.lea_line_amount = self.subtotal_invoice / float(1.1)
            self.lea_sell_price = self.price_unit / float(1.1)
        else:
            self.lea_line_amount = self.subtotal_invoice
            self.lea_sell_price = self.price_unit

        self.subtotal_invoice = self.quantity * self.lea_sell_price

        #SEARCH DC DISCOUNT
        rule_ids = self.env['res.partner.counting.margin'].search([
            ('partner_id.id','=',self.invoice_id.partner_id.id),
            ('discount_to_customer','=',self.discount),
            ('start_date','<=',self.invoice_id.date_invoice),
            ('end_date','>=',self.invoice_id.date_invoice),
            ],limit=1)

        if rule_ids:
            # self.price_discount = self.lea_line_amount * (rule_ids.discount_to_customer / 100.0)
            self.price_discount = self.subtotal_invoice * (rule_ids.discount_to_customer / 100.0)
        
        #SEARCH SD DISCOUNT
        if self.partner_id.type_counting_margin not in ['tpp','tpn']:
            if rule_ids:
                self.lea_share_discount = self.price_discount * (rule_ids.share_discount / 100.0)

                #SEARCH MARGIN
                nett_margin = 0
                if rule_ids.count_nett_margin:
                    if self.price_unit != self.product_id.lst_price:
                        nett_margin = float(rule_ids.nett_margin) / 100.00
                    else:
                        nett_margin = float(rule_ids.margin) / 100.00
                else:
                    nett_margin = float(rule_ids.margin) / 100.00

                if self.partner_id.type_counting_margin in ['ds1p','ds1n']:
                    # self.lea_margin = nett_margin * (self.lea_line_amount - self.lea_share_discount)
                    self.lea_margin = nett_margin * (self.subtotal_invoice - self.lea_share_discount)
                if self.partner_id.type_counting_margin in ['ds2p','ds2n']:
                    self.lea_margin = nett_margin * self.subtotal_invoice
                    # self.lea_margin = nett_margin * self.lea_line_amount

        if self.partner_id.code_transaction in ['01','02','03']:
            # self.lea_dpp = self.lea_line_amount - self.price_discount - self.lea_share_discount
            
            if self.partner_id.type_counting_margin not in ['tpp','tpn']:
                # self.lea_dpp = self.lea_line_amount - self.lea_share_discount - self.lea_margin
                self.lea_dpp = self.subtotal_invoice - self.lea_share_discount - self.lea_margin
            else:
                # self.lea_dpp = self.lea_line_amount - self.price_discount - self.lea_margin
                self.lea_dpp = self.subtotal_invoice - self.price_discount - self.lea_margin

            self.lea_value_invoice = self.lea_dpp * 0.1

        else:
            self.lea_dpp = 0
            if self.partner_id.type_counting_margin not in ['tpp','tpn']:
                # self.lea_value_invoice = self.lea_line_amount - (self.price_discount + self.lea_share_discount) - self.lea_margin
                self.lea_value_invoice = self.lea_line_amount - (self.lea_share_discount) - self.lea_margin
            else:
                # self.lea_value_invoice = self.lea_line_amount - (self.price_discount + self.lea_share_discount)
                self.lea_value_invoice = self.lea_line_amount - (self.lea_share_discount)

        self.lea_net_amount = self.subtotal_invoice - self.lea_share_discount - self.lea_margin
        #self.price_discount = self.quantity * self.price_unit * self.discount / 100
        taxes = self.invoice_line_tax_ids.compute_all(self.price_unit, self.invoice_id.currency_id, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_unit_base = taxes['total_excluded']
        
    
class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    default_cashbox_lines_ids = fields.One2many('account.cashbox.line', 'default_pos_id', string='Default Balance', copy=True)
    
class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    user_ids = fields.Many2many('res.users', string="Allowed Users")
    
    
class ResCompany(models.Model):
    _inherit = 'res.company'
    
    headquater_warehouse_id  = fields.Many2one('stock.warehouse', string='Gudang Pusat')
    
