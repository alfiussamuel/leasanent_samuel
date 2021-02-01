# -*- coding: utf-8 -*-
from openerp.exceptions import ValidationError
from openerp import api, fields, models, _



class PromotionalSchemes(models.Model):
    _name = 'loyalty.promotional.schemes'
    _description = 'Promotional Scheme'
    
    name = fields.Char('Scheme Name',size=64,required=True)
    state = fields.Selection([
                                ('draft','Request'),
                                ('approve','Approved'),
                                ('cancel','Cancelled'),
                                ('done', 'Done'),
                                ], 'Status', readonly=True, index=True)
    scheme_type = fields.Selection([
        ('buy_x_get_y','Buy X Get Y Free'),
        ('unit_price_disc_amt','Unit Price Disc. (Amt.)'),
        ('unit_price_disc_percent','Unit Price Disc. (%)'),
        ('volume_discount','Volume Discount'),
         ],'Scheme Type', copy=True)
    scheme_basis = fields.Selection([
        ('on_same_prod','On Same Product'),
        ('on_diff_prod','On Different Product'),
         ],'Scheme Basis', copy=True)
    scheme_id = fields.Many2one('stock.warehouse','Scheme ID', copy=True)
    from_date= fields.Date('From Date',required=True, copy=True)
    to_date= fields.Date('To Date',required=True, copy=True)
    template_ids = fields.One2many('loyalty.template','reference','Template Promotion', copy=True)
    available_on = fields.One2many('loyalty.available_on','scheme_id','Available On', copy=True)
    scheme_product = fields.One2many('loyalty.available_on','scheme_id2','Scheme Product', copy=True)
    locations = fields.Many2many('stock.location', 'location_shop_relation', 'scheme_id','id','Locations',required=True, copy=True) 
    buy_a_qty = fields.Integer('Buy A Qty in Full Price',required=True, copy=True)
    get_a_qty = fields.Integer('Get A Qty in Discount',required=True, copy=True)
    discount = fields.Integer('Discount in %',required=True, copy=True)
    qty_disc = fields.One2many('loyalty.qty.disc','buyx_gety_id','Select Qty and Disc.', copy=True)
    buy_a_qty_in_volume = fields.Integer('Buy A Qty',required=True, copy=True)
    offer_price = fields.Float('Offer Price',required=True, copy=True)
    
    _defaults = {
                 'scheme_type':'buy_x_get_y',
                 'scheme_basis':'on_same_prod',
                 'state': 'draft',
            }
    
    @api.multi    
    def approve(self):
        self.write({'state': 'approve'})
        return True
        
    @api.one
    def cancel(self):
        return self.write({'state': 'cancel'})
    
class QtyDisc(models.Model):
    _name = 'loyalty.qty.disc'
    _description = 'Select Quantity and Discount'
    
    buyx_gety_id = fields.Many2one('loyalty.promotional.schemes','loyalty_promotional_scheme_ref')
    qty = fields.Float('Quantity')
    discount = fields.Float('Discount')

class LoyaltyTemplate(models.Model):
    _name = 'loyalty.template'    
    
    name = fields.Char('Name',size=64)
    reference = fields.Many2one('loyalty.promotional.schemes', 'Reference')    
    available_ids = fields.One2many('loyalty.available_on', 'reference', 'Available On')
        
class LoyaltyAvailableOn(models.Model):
    _name = 'loyalty.available_on'
    _description = "Loyalty available on product template"
    
    name = fields.Char('Name',size=64)
    reference = fields.Many2one('loyalty.template', 'Reference')
    scheme_id = fields.Many2one('loyalty.promotional.schemes','Scheme Ref.')
    scheme_id2 = fields.Many2one('loyalty.promotional.schemes','Scheme Ref1.')
    template_id = fields.Many2one('product.template','Template')
    category_id = fields.Many2one('product.category','Article Code')    
    product_list = fields.Many2many('product.product','product_list_rel','template_id','id','Select Products')
    
    @api.onchange('template_id')
    def onchange_template_id(self):
        template_name = self.env['product.template'].browse(self.template_id.id).name        
        products_ids = self.env['product.product'].search([('product_tmpl_id','=',template_name)])         
        return {'value' : {'product_list':products_ids}}
    
    @api.onchange('category_id')
    def onchange_category_id(self):                
        products_ids = self.env['product.product'].search([('categ_id','=',self.category_id.id)])                
        return {'value' : {'product_list':products_ids}}
