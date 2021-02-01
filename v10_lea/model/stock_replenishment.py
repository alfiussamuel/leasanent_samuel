from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time, date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re
import calendar
    
STATE = [
    ('draft','Draft'),
    ('approved','Approved'),
    ('cancel','Cancel'),
]

MONTH = [
            (1,'Januari'),
            (2,'Februari'),
            (3,'Maret'),
            (4,'April'),
            (5,'Mei'),
            (6,'Juni'),
            (7,'Juli'),
            (8,'Agustus'),
            (9,'September'),
            (10,'Oktober'),
            (11,'November'),
            (12,'Desember'),
        ]

class LeaStockReplenishment(models.Model):
    _name = 'lea.stock.replenishment'
    _rec_name = 'date'
    _order = 'date desc'

    name                    = fields.Char('Document Number', readonly=True, translate=False)
    date                    = fields.Date('Document Date', default=fields.Datetime.now(), readonly=True)
    start_date              = fields.Date('Start Date', compute='compute_period', store=True)
    end_date                = fields.Date('End Date', compute='compute_period', store=True)
    state                   = fields.Selection(STATE, 'State', default='draft')
    area_id                 = fields.Many2one(comodel_name='lea.area',string='Area')
    warehouse_id            = fields.Many2one(comodel_name='stock.warehouse',string='Warehouse')
    year                    = fields.Char(string='Year', readonly=True, default=lambda self:self._get_default_year())
    month                   = fields.Selection(MONTH, string='Period', readonly=True, default=lambda self:self._get_default_period())
    group_moving_id         = fields.Many2one('lea.product.moving.status','Moving Status')
    product_category_ids    = fields.Many2many('lea.product.category','replenishment_category_rel','replenishment_id','category_id',string='Product Category(s)')
    product_category_line   = fields.One2many('lea.stock.replenishment.category','replenishment_id',string='Product Category(s)')
    product_line            = fields.One2many('lea.stock.replenishment.product','replenishment_id',string='Product(s)')
    stock_onstage           = fields.Integer('Capacity (On Stage)', compute='compute_warehouse', store=True)
    stock_buffer            = fields.Integer('Capacity (Buffer)', compute='compute_warehouse', store=True)
    stock_total             = fields.Integer('Capacity (Total)', compute='compute_warehouse', store=True)
    lead_time               = fields.Integer('Lead Time (Day)', default=30)
    avg_sales               = fields.Integer('Avg. Sales (Month)', default=12)
    replenishment_count     = fields.Integer('#Replenishment', compute='_compute_replenishment_count')    
    total_avg_sales         = fields.Integer('Avg. Sales', compute='compute_avg_sales', store=True)
    trigger_total_average_sales = fields.Boolean("Trigger Total Average Sales")

    start_date_avg_sales    = fields.Date('Start Date', compute='compute_period', store=True)
    end_date_avg_sales      = fields.Date('End Date', compute='compute_period', store=True)


    @api.depends('product_line.avg_sales','trigger_total_average_sales')
    def compute_avg_sales(self):
        for rec in self:
            if rec.product_line:
                rec.total_avg_sales = sum(s.avg_sales for s in rec.product_line)

    @api.multi
    def action_view_replenishment(self):      
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('origin', '=', self.name)]
        action['context'] = {}
        return action
    
    @api.one
    def _compute_replenishment_count(self):
        for res in self:
            replenishment_ids = self.env['stock.picking'].search([('replenishment_id','=',res.id)])
            if replenishment_ids:         
                res.replenishment_count = len(replenishment_ids)     

    def get_sequence(self, name=False, obj=False, pref=False, context=None):
        sequence_id = self.env['ir.sequence'].search([
            ('name', '=', name),
            ('code', '=', obj),
            ('prefix', '=', pref + '%(month)s-%(year)s/')
        ])
        if not sequence_id :
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': name,
                'code': obj,
                'implementation': 'standard',
                'prefix': pref + '%(month)s-%(year)s/',
                'padding': 3
            })
        return sequence_id.next_by_id()

    @api.model
    def create(self, vals):        
        vals['name'] = self.get_sequence('LEA Stock Replenishment','lea.stock.replenishment','RFS/')        
        return super(LeaStockReplenishment, self).create(vals)

    # def action_draft_replenishment(self):
    #     for rec in self :
    #         for x in rec.product_line :
    #             x.write({'draft_replenishment' : x.draft_replenishment2})

    # @api.multi
    # def write(self, vals):
    #     rec = super(LeaStockReplenishment, self).write(vals)
    #     self.action_draft_replenishment()
    #     return rec


    @api.onchange('product_category_line.ratio')
    def onchange_ratio(self):
        for rec in self:
            total_ratio = sum(l.ratio for l in rec.product_category_line)
            if total_ratio > 100:
                raise Warning('Ratio tidak lebih dari 100% !')

    @api.model
    def _get_default_year(self):
        current_year = datetime.now().year
        return current_year

    @api.model
    def _get_default_period(self):
        current_month = datetime.now().month
        return current_month

    @api.depends('month','year')
    def compute_period(self):
        for rec in self:
            if rec.month and rec.year:

                #AVG SALES
                date_convert = date(int(rec.year),int(rec.month),01)+relativedelta(months=-13)
                rec.start_date_avg_sales = str(date_convert.year) + '-' + str(date_convert.month).zfill(2) + '-' + '01'
                date_convert = date(int(rec.year),int(rec.month),01)+relativedelta(months=-1)
                cal2 = calendar.monthrange(int(date_convert.year)-1, int(date_convert.month))
                rec.end_date_avg_sales = str(date_convert.year) + '-' + str(date_convert.month).zfill(2) + '-' + str(cal2[1]).zfill(2)

                #PERIOD
                date_convert = date(int(rec.year),int(rec.month),01)
                rec.start_date = str(date_convert.year) + '-' + str(date_convert.month).zfill(2) + '-' + '01'
                cal2 = calendar.monthrange(int(date_convert.year), int(date_convert.month))
                rec.end_date = str(date_convert.year) + '-' + str(date_convert.month).zfill(2) + '-' + str(cal2[1]).zfill(2)

    @api.depends('warehouse_id')
    def compute_warehouse(self):
        for rec in self:
            if rec.warehouse_id:
                rec.stock_onstage = rec.warehouse_id.wh_onstage
                rec.stock_buffer = rec.warehouse_id.wh_buffer
                rec.stock_total = rec.warehouse_id.wh_capacity
                rec.lead_time = rec.warehouse_id.wh_lead_time
                rec.avg_sales = rec.warehouse_id.wh_avg_sales

    @api.multi
    def button_generate(self):
        if self.product_category_ids:
            for ol in self.product_category_line:
                ol.sudo().unlink()

        if self.warehouse_id:
            if self.product_category_ids:
                for c in self.product_category_ids:
                    
                    ito_ids = self.env['stock.warehouse.ito'].sudo().search([('category_id.id','=',c.id)],limit=1)
                    if not ito_ids:
                        raise Warning('ITO belum di set untuk ' + c.name)

                    self.env['lea.stock.replenishment.category'].sudo().create({
                       'replenishment_id'       : self.id,
                       'category_id'            : c.id,
                       'ito'                    : ito_ids.ito_value if ito_ids else 0,
                       'ratio'                  : 100.00 / float(len(self.product_category_ids))
                       })
        return True

    @api.multi
    def button_generate_2(self):
        ratio = 0

        if self.product_category_ids:
            for rec in self.product_category_line:
                ratio += rec.ratio
                if ratio > 100 :
                    raise Warning('Ratio tidak boleh lebih dari 100')

        # #delete old record
        # if self.product_line:
        #     for ol in self.product_line:
        #         ol.sudo().unlink()

        if self.warehouse_id:
            if self.product_category_ids:
                for c in self.product_category_ids:

                    #CREATE PRODUCT
                    product_ids = self.env['product.product'].sudo().search([
                        ('product_category_id.id','=',c.id),
                        ('product_tmpl_id.product_moving_status_id.id','=',self.group_moving_id.id),
                        ('active','=',True)
                        ])

                    if product_ids:
                        for p in product_ids:
                            
                            # BEGINNING
                            p_beginning = self.env['stock.history'].search([
                                ('product_id.id','=',p.id),
                                ('date','<',self.start_date),
                                ('location_id.id','=',self.warehouse_id.lot_stock_id.id)
                                ], limit=1, order='date desc')

                            #RECEIVED
                            p_receiving = self.env['stock.move'].search([
                                ('product_id.id','=',p.id),
                                ('picking_type_id.warehouse_id.id','=',self.warehouse_id.id),
                                ('date','>=',self.start_date),
                                ('date','<=',self.end_date),
                                ('state','=','done'),
                                ('picking_type_id.code','=','incoming')
                                ])

                            #SALES
                            p_sales = self.env['sale.order.line'].search([
                                ('product_id.id','=',p.id),
                                ('order_id.warehouse_id.id','=',self.warehouse_id.id),
                                ('order_date','>=',self.start_date),
                                ('order_date','<=',self.end_date),
                                ('order_id.state','in',['sale','done'])
                                ])
                            p_pos = self.env['pos.order.line'].search([
                                ('product_id.id','=',p.id),
                                # ('order_id.location_id.id','=',self.warehouse_id.lot_stock_id.id),
                                ('order_id.date_order','>=',self.start_date),
                                ('order_id.date_order','<=',self.end_date),
                                ('order_id.state','not in',['draft','cancel'])
                                ])

                            #INTERNAL TRANSFER
                            p_internal = self.env['stock.move'].search([
                                ('product_id.id','=',p.id),
                                ('picking_type_id.warehouse_id.id','=',self.warehouse_id.id),
                                ('date','>=',self.start_date),
                                ('date','<=',self.end_date),
                                ('state','=','done'),
                                ('picking_type_id.code','=','internal')
                                ])

                            #ADJUSTMENT
                            p_adjustment = self.env['stock.move'].search([
                                ('product_id.id','=',p.id),
                                # ('picking_type_id.warehouse_id.id','=',self.warehouse_id.id), ## kalo dari inventory adj default picking_type_id nya kosong
                                ('date','>=',self.start_date),
                                ('date','<=',self.end_date),
                                ('state','=','done'),
                                ('location_id.usage','=','inventory')
                                ])

                            #IN TRANSIT
                            p_intransit = self.env['stock.move'].search([
                                ('product_id.id','=',p.id),
                                # ('picking_type_id.warehouse_id.id','=',self.warehouse_id.id), ## kalo dari inventory adj default picking_type_id nya kosong
                                ('date','>=',self.start_date),
                                ('date','<=',self.end_date),
                                ('state','in',['draft','waiting','confirmed','assigned']),
                                ('location_id.usage','=','inventory')
                                ])

                            # #AVG SALES
                            # start_sales_sum = 0
                            # end_sales_sum = 0
                            # sales_sum_start = 0
                            # sales_sum_end = 0
                            # total_avg_sales = 0
                            # contribution = 0
                            # start_date_avg_sales = datetime.strptime(self.start_date_avg_sales, '%Y-%m-%d')
                            # end_date_avg_sales = datetime.strptime(self.end_date_avg_sales, '%Y-%m-%d')
                            # year = start_date_avg_sales.year
                            # start_month = start_date_avg_sales.month
                            # end_month = end_date_avg_sales.month
                            # p_avg_sales = self.env['lea.sales.summary'].search([
                            #     ('product_id','=',p.product_tmpl_id.id),
                            #     ('warehouse_id','=',self.warehouse_id.id),
                            #     ('year','>=',year),
                            #     ('year','<=',self.year),
                            #     ])
                            # p_avg_sales_start = self.env['lea.sales.summary'].search([
                            #     ('product_id','=',p.product_tmpl_id.id),
                            #     ('warehouse_id','=',self.warehouse_id.id),
                            #     ('year','=',year),
                            #     ])
                            # p_avg_sales_end = self.env['lea.sales.summary'].search([
                            #     ('product_id','=',p.product_tmpl_id.id),
                            #     ('warehouse_id','=',self.warehouse_id.id),
                            #     ('year','=',self.year),
                            #     ])
                            # for avg_start in p_avg_sales_start :
                            #     if start_month == 1 :
                            #         start_sales_sum = avg_start.total_qty_1 + avg_start.total_qty_2 + avg_start.total_qty_3 + avg_start.total_qty_4 + avg_start.total_qty_5 + avg_start.total_qty_6 + avg_start.total_qty_7 + avg_start.total_qty_8 + avg_start.total_qty_9 + avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 2 :
                            #         start_sales_sum = avg_start.total_qty_2 + avg_start.total_qty_3 + avg_start.total_qty_4 + avg_start.total_qty_5 + avg_start.total_qty_6 + avg_start.total_qty_7 + avg_start.total_qty_8 + avg_start.total_qty_9 + avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 3 :
                            #         start_sales_sum = avg_start.total_qty_3 + avg_start.total_qty_4 + avg_start.total_qty_5 + avg_start.total_qty_6 + avg_start.total_qty_7 + avg_start.total_qty_8 + avg_start.total_qty_9 + avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 4 :
                            #         start_sales_sum = avg_start.total_qty_4 + avg_start.total_qty_5 + avg_start.total_qty_6 + avg_start.total_qty_7 + avg_start.total_qty_8 + avg_start.total_qty_9 + avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 5 :
                            #         start_sales_sum = avg_start.total_qty_5 + avg_start.total_qty_6 + avg_start.total_qty_7 + avg_start.total_qty_8 + avg_start.total_qty_9 + avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 6 :
                            #         start_sales_sum = avg_start.total_qty_6 + avg_start.total_qty_7 + avg_start.total_qty_8 + avg_start.total_qty_9 + avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 7 :
                            #         start_sales_sum = avg_start.total_qty_7 + avg_start.total_qty_8 + avg_start.total_qty_9 + avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 8 :
                            #         start_sales_sum = avg_start.total_qty_8 + avg_start.total_qty_9 + avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 9 :
                            #         start_sales_sum = avg_start.total_qty_9 + avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 10 :
                            #         start_sales_sum = avg_start.total_qty_10 + avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 11 :
                            #         start_sales_sum = avg_start.total_qty_11 + avg_start.total_qty_12
                            #     if start_month == 12 :
                            #         start_sales_sum = avg_start.total_qty_12
                            #     sales_sum_start = start_sales_sum
                            # for avg_end in p_avg_sales_end :
                            #     if end_month == 1 :
                            #         end_sales_sum = avg_end.total_qty_1
                            #     if end_month == 2 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2
                            #     if end_month == 3 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3
                            #     if end_month == 4 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3 + avg_end.total_qty_4
                            #     if end_month == 5 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3 + avg_end.total_qty_4 + avg_end.total_qty_5
                            #     if end_month == 6 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3 + avg_end.total_qty_4 + avg_end.total_qty_5 + avg_end.total_qty_6
                            #     if end_month == 7 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3 + avg_end.total_qty_4 + avg_end.total_qty_5 + avg_end.total_qty_6 + avg_end.total_qty_7
                            #     if end_month == 8 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3 + avg_end.total_qty_4 + avg_end.total_qty_5 + avg_end.total_qty_6 + avg_end.total_qty_7 + avg_end.total_qty_8
                            #     if end_month == 9 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3 + avg_end.total_qty_4 + avg_end.total_qty_5 + avg_end.total_qty_6 + avg_end.total_qty_7 + avg_end.total_qty_8 + avg_end.total_qty_9
                            #     if end_month == 10 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3 + avg_end.total_qty_4 + avg_end.total_qty_5 + avg_end.total_qty_6 + avg_end.total_qty_7 + avg_end.total_qty_8 + avg_end.total_qty_9 + avg_end.total_qty_10
                            #     if end_month == 11 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3 + avg_end.total_qty_4 + avg_end.total_qty_5 + avg_end.total_qty_6 + avg_end.total_qty_7 + avg_end.total_qty_8 + avg_end.total_qty_9 + avg_end.total_qty_10 + avg_end.total_qty_11
                            #     if end_month == 12 :
                            #         end_sales_sum = avg_end.total_qty_1 + avg_end.total_qty_2 + avg_end.total_qty_3 + avg_end.total_qty_4 + avg_end.total_qty_5 + avg_end.total_qty_6 + avg_end.total_qty_7 + avg_end.total_qty_8 + avg_end.total_qty_9 + avg_end.total_qty_10 + avg_end.total_qty_11 + avg_end.total_qty_12
                            #     sales_sum_end = end_sales_sum

                            #ADJUSTMENT
                            if not self.env.user.company_id.headquater_warehouse_id:
                                raise Warning('Gudang Pusat belum di tentukan !')

                            p_stock_hq = self.env['stock.quant'].search([
                                ('product_id.id','=',p.id),
                                ('location_id.id','=',self.env.user.company_id.headquater_warehouse_id.lot_stock_id.id),
                                ('location_id.usage','=','inventory')
                                ])

                            t_stock_hq      = sum(t.qty for t in p_stock_hq)
                            t_beginning     = sum(t.quantity for t in p_beginning)
                            t_receiving     = sum(t.product_uom_qty for t in p_receiving)
                            t_sales         = sum(t.product_uom_qty for t in p_sales) + sum(t.qty for t in p_pos)
                            t_intransit     = sum(t.product_uom_qty for t in p_intransit)
                            t_internal      = sum(t.product_uom_qty for t in p_internal)
                            t_adjustment    = sum(t.product_uom_qty for t in p_adjustment)
                            # t_avg_sales     = sales_sum_start + sales_sum_end
                            t_ending        = t_beginning + t_receiving - t_sales - t_internal + t_intransit + t_adjustment

                            #CREATE RECORD
                            query = """INSERT INTO lea_stock_replenishment_product(
                                        id,
                                        replenishment_id,
                                        product_id,
                                        theory_beginning,
                                        theory_received,
                                        theory_sales,
                                        theory_intransit,
                                        theory_internal,
                                        theory_adjustment,
                                        theory_ending,
                                        -- avg_sales,
                                        draft_headquater)
                                    VALUES(nextval('lea_stock_replenishment_product_seq'),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                            

                            self.env.cr.execute(query,(self.id, p.id, t_beginning, t_receiving, t_sales, t_intransit, t_internal, t_adjustment, t_ending, t_stock_hq))
                            self.trigger_total_average_sales = True

                    product_ids = self.env['lea.stock.replenishment.product'].search([('replenishment_id','=',self.id)])
                    for product in product_ids :
                        product.write({'draft_replenishment' : product.draft_suggest})

        return True

    @api.multi
    def button_create_replenishment(self):
        if self.product_category_line:
            product_list = []

            for p in self.product_line:
                if p.draft_replenishment > 0:
                    product_list.append((0,0,{
                        'name'              : p.product_id.display_name,
                        'product_id'        : p.product_id.id,
                        'product_uom_qty'   : p.draft_replenishment,
                        'product_uom'       : p.product_id.uom_id.id,
                    }))

            # hq_location_id = self.env['stock.warehouse'].search([('name','=','GUDANG_LEA')],limit=1)
            if not self.env.user.company_id.headquater_warehouse_id:
                raise Warning('Gudang Pusat belum di tentukan !')

            hq_location_id = self.env.user.company_id.headquater_warehouse_id

            new_picking = self.env['stock.picking'].create({
               'replenishment_id'       : self.id,
               'min_date'               : fields.Datetime.now(),
               'location_id'            : hq_location_id.id,
               'location_dest_id'       : self.warehouse_id.lot_stock_id.id,
               'picking_type_id'        : hq_location_id.int_type_id.id,
               'partner_id'             : self.warehouse_id.partner_id.id,
               'move_lines'             : product_list,
               'origin'                 : self.name,
               })

            #GO TO FORM VIEW PICKING
            action = self.env['ir.model.data'].xmlid_to_object('stock.action_picking_tree_all')
            if not action:
                action = {
                    'view_type'     : 'form',
                    'view_mode'     : 'tree',
                    'res_model'     : 'stock.picking',
                    'type'          : 'ir.actions.act_window',
                }
            else:
                action = action[0].read()[0]
                    
            action['domain'] = "[('id', 'in', " + str([new_picking.id]) + ")]"
            action['name'] = _('Draft Replenishment')
            return action

        else:
            raise Warning('Harap generate dan sesuaikan terlebih dahulu !')
    

class LeaStockReplenishmentCategory(models.Model):
    _name = 'lea.stock.replenishment.category'

    replenishment_id        = fields.Many2one('lea.stock.replenishment','Replenishment ID')
    category_id             = fields.Many2one('lea.product.category','Category')
    ito                     = fields.Float('ITO')
    ratio                   = fields.Float('Ratio (%)')
    stock_capacity          = fields.Integer('Capacity', compute='compute_stock', store=True)
    stock_min               = fields.Integer('Min', compute='compute_stock', store=True)
    stock_max               = fields.Integer('Max', compute='compute_stock', store=True)

    @api.depends('ratio','ito','replenishment_id.total_avg_sales','replenishment_id.lead_time','replenishment_id.stock_total')
    def compute_stock(self):
        for rec in self:
            if rec.category_id:
                rec.stock_capacity  = (rec.ratio / 100.00) * rec.replenishment_id.stock_total
                rec.stock_min       = rec.replenishment_id.total_avg_sales * rec.replenishment_id.lead_time / 30.00
                rec.stock_max       = rec.ito * rec.stock_min

class LeaStockReplenishmentProduct(models.Model):
    _name = 'lea.stock.replenishment.product'

    replenishment_id        = fields.Many2one('lea.stock.replenishment','Replenishment ID')
    product_id              = fields.Many2one('product.product','Product')
    theory_beginning        = fields.Integer('Beginning')
    theory_received         = fields.Integer('Received')
    theory_sales            = fields.Integer('Sales')
    theory_internal         = fields.Integer('Internal')
    theory_intransit        = fields.Integer('In-Transit')
    theory_adjustment       = fields.Integer('Adjustment')
    theory_ending           = fields.Integer('Ending')
    avg_sales               = fields.Integer('Avg. Sales', compute='compute_sales_summary', store=True)
    contribution            = fields.Integer('Contribution (%)', compute='compute_contribution', store=True)
    over_stock              = fields.Integer('Over Stock', compute='compute_over_stock', store=True)
    draft_suggest           = fields.Integer('Suggest', compute='compute_suggest_stock', store=True)
    draft_headquater        = fields.Integer('Stock HQ')
    draft_replenishment     = fields.Integer('Replenishment')

    @api.depends('contribution','avg_sales','over_stock','theory_ending','replenishment_id.product_category_line.stock_max')
    def compute_suggest_stock(self):
        for rec in self:

            if rec.over_stock > 0:

                #get max stock
                stock_max = 0
                for s in rec.replenishment_id.product_category_line:
                    if rec.product_id.product_category_id.id == s.category_id.id:
                        stock_max = s.stock_max

                rec.draft_suggest = ((rec.contribution / 100.00) * stock_max) - rec.theory_ending


    @api.multi
    @api.depends('product_id','replenishment_id.trigger_total_average_sales')
    def compute_sales_summary(self):
        for rec in self:
            for x in rec.replenishment_id:
                if rec.product_id:
                    total = 0
                    
                    #SAME YEAR
                    if str(x.start_date_avg_sales)[:4] == str(x.end_date_avg_sales)[:4]:

                        sales_summary_ids = self.env['lea.sales.summary'].search([
                            ('year','=',str(x.start_date_avg_sales)[:4]),
                            ('product_id.id','=',rec.product_id.product_tmpl_id.id)
                            ],limit=1)

                        for m in range(int(x.start_date_avg_sales)[5:7],int(x.end_date_avg_sales)[5:7])+1:
                            if m == 1:
                                total += sales_summary_ids.total_qty_1
                            elif m == 2:
                                total += sales_summary_ids.total_qty_2
                            elif m == 3:
                                total += sales_summary_ids.total_qty_3
                            elif m == 4:
                                total += sales_summary_ids.total_qty_4
                            elif m == 5:
                                total += sales_summary_ids.total_qty_5
                            elif m == 6:
                                total += sales_summary_ids.total_qty_6
                            elif m == 7:
                                total += sales_summary_ids.total_qty_7
                            elif m == 8:
                                total += sales_summary_ids.total_qty_8
                            elif m == 9:
                                total += sales_summary_ids.total_qty_9
                            elif m == 10:
                                total += sales_summary_ids.total_qty_10
                            elif m == 11:
                                total += sales_summary_ids.total_qty_11
                            elif m == 12:
                                total += sales_summary_ids.total_qty_12

                    #DIFFERENT YEAR
                    else:
                        #HITUNG 1
                        sales_summary_ids = self.env['lea.sales.summary'].search([
                            ('year','=',str(x.start_date_avg_sales)[:4]),
                            ('product_id.id','=',rec.product_id.product_tmpl_id.id)
                            ],limit=1)

                        start_date_avg_sales = datetime.strptime(x.start_date_avg_sales, '%Y-%m-%d')
                        start_month = start_date_avg_sales.month
                        for m in range(start_month,13):
                            if m == 1:
                                total += sales_summary_ids.total_qty_1
                            elif m == 2:
                                total += sales_summary_ids.total_qty_2
                            elif m == 3:
                                total += sales_summary_ids.total_qty_3
                            elif m == 4:
                                total += sales_summary_ids.total_qty_4
                            elif m == 5:
                                total += sales_summary_ids.total_qty_5
                            elif m == 6:
                                total += sales_summary_ids.total_qty_6
                            elif m == 7:
                                total += sales_summary_ids.total_qty_7
                            elif m == 8:
                                total += sales_summary_ids.total_qty_8
                            elif m == 9:
                                total += sales_summary_ids.total_qty_9
                            elif m == 10:
                                total += sales_summary_ids.total_qty_10
                            elif m == 11:
                                total += sales_summary_ids.total_qty_11
                            elif m == 12:
                                total += sales_summary_ids.total_qty_12

                        #HITUNG 2
                        sales_summary_ids = self.env['lea.sales.summary'].search([
                            ('year','=',str(x.end_date_avg_sales)[:4]),
                            ('product_id.id','=',rec.product_id.product_tmpl_id.id)
                            ],limit=1)

                        end_date_avg_sales = datetime.strptime(x.end_date_avg_sales, '%Y-%m-%d')
                        end_month = end_date_avg_sales.month
                        for m in range(1,end_month):
                            if m == 1:
                                total += sales_summary_ids.total_qty_1
                            elif m == 2:
                                total += sales_summary_ids.total_qty_2
                            elif m == 3:
                                total += sales_summary_ids.total_qty_3
                            elif m == 4:
                                total += sales_summary_ids.total_qty_4
                            elif m == 5:
                                total += sales_summary_ids.total_qty_5
                            elif m == 6:
                                total += sales_summary_ids.total_qty_6
                            elif m == 7:
                                total += sales_summary_ids.total_qty_7
                            elif m == 8:
                                total += sales_summary_ids.total_qty_8
                            elif m == 9:
                                total += sales_summary_ids.total_qty_9
                            elif m == 10:
                                total += sales_summary_ids.total_qty_10
                            elif m == 11:
                                total += sales_summary_ids.total_qty_11
                            elif m == 12:
                                total += sales_summary_ids.total_qty_12

                    rec.avg_sales = total

    @api.depends('theory_ending','replenishment_id.product_category_line.stock_max','contribution')
    def compute_over_stock(self):
        for rec in self:
            if rec.product_id:
                #get max stock
                stock_max = 0
                for s in rec.replenishment_id.product_category_line:
                    if rec.product_id.product_category_id.id == s.category_id.id:
                        stock_max = s.stock_max * rec.contribution

                if rec.theory_ending > stock_max:
                    rec.over_stock = rec.theory_ending - stock_max
                else:
                    rec.over_stock = 0

    @api.depends('replenishment_id.total_avg_sales','avg_sales')
    def compute_contribution(self):
        for rec in self:
            if rec.replenishment_id.total_avg_sales > 0 and rec.avg_sales > 0:
                rec.contribution = (rec.avg_sales / float(rec.replenishment_id.total_avg_sales)) * 100.00
