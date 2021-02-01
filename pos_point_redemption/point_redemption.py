from odoo import fields,models,api
from odoo.exceptions import UserError,Warning

class point_scheme(models.Model):   
    _name='point.scheme'
    _description = 'Point Scheme'
    _track = {
            'state': {
                'sale.order_draft': lambda self, cr, uid, obj, ctx=None: obj['state'] in ['draft'],
                'sale.order_confirmed': lambda self, cr, uid, obj, ctx=None: obj['state'] in ['done']
            },
        }
    
    state = fields.Selection([
       ('draft','Request'),
       ('approve','Approved'),
       ('cancel','Cancelled'),
       ('done', 'Done'),
        ], 'Status', readonly=True,select=True,default='draft')
    name = fields.Char('Point Scheme Name',required=True,size=64)
    start_date = fields.Date('Start Date', select=1,default=fields.Date.context_today)
    end_date = fields.Date('End Date', select=1,default=fields.Date.context_today)
    points_basis = fields.Selection([('sale_invoice', 'Sale Invoice'), ('on_product_quantity', 'On/Product/Quantity')], "Points Basis", required=True,default='sale_invoice')
    product_ids = fields.One2many('point.scheme.product.quantity','product_no','Product quantity')
    invoice_ids = fields.Float('Percentage(%)')
    shop_company_ids = fields.Many2many('stock.location','new_location_rel','point_scheme_id','location_id','Location',required=True)
    
#     _defaults={
#              'state': 'draft',
#              'points_basis':'sale_invoice',
#              'start_date': fields.Date.context_today,
#              'end_date': fields.Date.context_today,
#               }
    @api.multi
    def cancel(self):
        return self.write({'state': 'cancel'})
    
    @api.multi
    def approve(self):
        loyalty_record_id = [];
        shop_list = []
        loyalty_obj = self.env['point.scheme']
        loyalty_srch = loyalty_obj.search([])
        for y in self:
            loyalty_record_id.append(y.id)
            start_date = y.start_date
            end_date = y.end_date 
            s_state=y.points_basis
        
        loyalty_shop = self
        for shop in loyalty_shop.shop_company_ids:
            shop_list.append(shop.id)
        if len(self)== 1:
            return self.write({'state': 'approve'})
            return True
        else: 
            for sh in shop_list:
                for loyalty_brw in self:
                    if loyalty_brw.id != self._ids[0]:
                        for x in loyalty_brw.shop_company_ids:
                            if loyalty_brw.points_basis == "sale_invoice":
                                if ((x.id == sh) & (loyalty_brw.state == "approve")):
                                    s_date=loyalty_brw.start_date
                                    e_date=loyalty_brw.end_date
                                    if (((start_date >= s_date) & (start_date <= e_date)) | ((end_date >= s_date) & (end_date <= e_date))):
                                        shop_obj=self.env['stock.location'].browse(sh)
                                        if s_state == "sale_invoice":
                                            raise UserError(_('Error!'), _(' "%s" already has scheme defined for this period . Please remove this Location from the list:') % \
                                                            (shop_obj.name,))
                                            
#                                             raise osv.except_osv(('Error!'),
#                                                             (' "%s" already has scheme defined for this period . Please remove this Location from the list:') % \
#                                                                 (shop_obj.name,))
                            else :
                                if loyalty_brw.points_basis == "on_product_quantity":
                                    if ((x.id == sh) & (loyalty_brw.state == "approve")):
                                        s_date=loyalty_brw.start_date
                                        e_date=loyalty_brw.end_date
                                        
                                        if (((start_date >= s_date) & (start_date <= e_date)) | ((end_date >= s_date) & (end_date <= e_date))):
                                            shop_obj=self.pool.get('stock.location').browse(sh)
                                            if s_state == "on_product_quantity":
                                                raise UserError(('Error!'),
                                                                (' "%s" already has scheme defined for this period . Please remove this Location from the list:') % \
                                                                    (shop_obj.name,))
                    
        
        self.write({'state': 'approve'})
        return True
    
    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.start_date < fields.Date.context_today(self):
            raise Warning("Start Date should be greater than todays date")

    @api.onchange('start_date','end_date')
    def onchange_end_date(self):
        if self.end_date < self.start_date:
            raise Warning('End Date should be greater than start date')
     


class reedem_points(models.Model):   
    _name='reedem.points'
    _description = 'Point Redemption'
    
    state = fields.Selection([
       ('draft','Request'),
       ('approve','Approved'),
       ('cancel','Cancelled'),
       ('done', 'Done'),
       
        ], 'Status', readonly=True,select=True,default='draft')
    name = fields.Char('Point Redemption Rule',required=True,size=64)
    start_date = fields.Date('From Date', select=1,default=fields.Date.context_today)
    end_date = fields.Date('To Date', select=1,default=fields.Date.context_today)
    unit_of_currency = fields.Float('Points/unit Of Currency', select=1)
    shop_company_ids_1 = fields.Many2many('stock.location','location_rel_1','reedem_point_id','location_id','Location',required=True)
    
#     _defaults={
#              'state': 'draft',
#              'start_date': fields.Date.context_today,
#              'end_date': fields.Date.context_today,
#         }
    
    @api.multi
    def approve(self):
        loyalty_record_id = [];
        shop_list = []
        loyalty_obj = self.env['reedem.points']
        loyalty_srch = loyalty_obj.search([])
        for y in loyalty_srch:
            loyalty_record_id.append(y.id)
            start_date = y.start_date
            end_date = y.end_date 
            
        loyalty_shop = loyalty_srch
        for shop in loyalty_shop.shop_company_ids_1:
            shop_list.append(shop.id)
        if len(loyalty_srch) == 1:
            return self.write({'state': 'approve'})
            return True
        
        else: 
            for sh in shop_list:
                for loyalty_brw in loyalty_srch:
                    if loyalty_brw.id != self._ids[0]:
                        for x in loyalty_brw.shop_company_ids_1:
                            if x.id==sh:
                                s_date=loyalty_brw.start_date
                                e_date=loyalty_brw.end_date
                                if (((start_date >= s_date) & (start_date <= e_date)) | ((end_date >= s_date) & (end_date <= e_date))):
                                    shop_obj=self.env['stock.location'].browse(sh)
                                    raise UserError(('Error!'),
                                                (' "%s" already has scheme defined for this period . Please remove this shop from the list:') % \
                                                    (shop_obj.name,))
            self.write({'state': 'approve'})
            return True
    
    @api.multi
    def cancel(self):
        return self.write({'state': 'cancel'})
    
    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.start_date < fields.Date.context_today(self):
            raise Warning('Start Date should be greater than todays date')
    
    @api.onchange('start_date','end_date')
    def onchange_end_date(self):
        if self.end_date < self.start_date:
            raise Warning('End Date should be greater than start date')
         


class point_scheme_product_quantity(models.Model):   
    _name='point.scheme.product.quantity'
    _description = 'Point Scheme Product Quantity'
     
    product = fields.Many2one('product.product','Product',size=64)
    product_category = fields.Many2one('product.category','Product Category',size=64)
    points = fields.Float('Points',required=True)
    product_no = fields.Many2one('point.scheme','Product No')
     
point_scheme_product_quantity()



class res_partner(models.Model):   
    _inherit="res.partner"
    
    reedemable_points_available = fields.Float('Redeemable Points Available',readonly=True)
    pos_order_ids = fields.Many2many('pos.order','partner_pos_order_rel','partner_id','order_id','Order Ref.',readonly=True)

    _sql_constraints = [
        ('mobile_uniq', 'unique (mobile)', 'The mobile no. must be unique !')
    ]
    
res_partner()




class pos_order(models.Model):
    _inherit="pos.order"
    
    @api.model    
    def _order_fields(self, ui_order):
        oldObj = super(pos_order,self)._order_fields(ui_order)
        bal_point=((int(ui_order.get('points_avail',0))-int(ui_order.get('redeems_point',0)))+int(ui_order.get('gained_points',0)))
        oldObj.update({
                       'balance_points':bal_point,
                       'points_reedemed':ui_order.get('redeems_point',0),
                       'points_earned':ui_order.get('gained_points',0)
                    });
        return oldObj
    
    @api.model
    def method_for_partner(self,vals):
        if 'p_id' in vals and vals.get('p_id',0):
            p_obj=self.env['res.partner'].browse([vals.get('p_id')])[0]
            poi_ids = [vals.get('o_id')]
            
            print poi_ids
            if p_obj.pos_order_ids:
                print "x1"
                for idd in p_obj.pos_order_ids:
                    print "x2"
                    poi_ids.append(idd.id)
                print "x3"
            reedemable_points=((int(vals.get('avail_point',0))-int(vals.get('r_point',0)))+int(vals.get('earn_point',0)))
            print "x4"
            p_obj.write({'reedemable_points_available':reedemable_points,'pos_order_ids':[(6,0,poi_ids)]})
            print "x5"
        
    @api.model    
    def create_from_ui(self, orders):
        order_ids=super(pos_order,self).create_from_ui(orders)
        if order_ids:
            da=orders[0]['data']
            if da.get('partner_id'):
                partner={
                    'p_id':da.get('partner_id',0),
                    'avail_point':da.get('points_avail',0),
                    'earn_point':da.get('gained_points',0),
                    'r_point':da.get('redeems_point',0),
                    'o_id':order_ids[0],
                    };
                self.method_for_partner(partner);
        return order_ids
            
        
    points_earned = fields.Float('Points Earned')
    points_reedemed = fields.Float('Points Redeemed')
    balance_points = fields.Float('Balance Points')
    state = fields.Selection([('draft', 'New'),
                           ('cancel', 'Cancelled'),
                           ('paid', 'Paid'),
                           ('credited','Credited'),
                           ('done', 'Posted'),
                           ('invoiced', 'Invoiced')],
                          'Status', readonly=True)

        

class account_journal(models.Model):
    _inherit = 'account.journal'
    
    for_points = fields.Boolean('For Points')
   
account_journal()
