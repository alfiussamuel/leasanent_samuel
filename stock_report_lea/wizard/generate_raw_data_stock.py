import base64
from cStringIO import StringIO
from odoo import api, fields, models
import xlsxwriter
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class generate_raw_data_stock(models.TransientModel):
    _name = 'generate.raw.data.stock'

    @api.model
    def _default_company(self):
        user = self.env['res.users'].browse(self.env.uid)
        return user.company_id.id


    date_from       = fields.Date(string='Start Date')
    date_to         = fields.Date(string='End Date')
    mutasi_lines    = fields.One2many(comodel_name="generate.raw.data.stock.line", inverse_name="reference", string="Raw Data Stock")
    company_id      = fields.Many2one('res.company', 'Company', default=_default_company)
    state_position  = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    data            = fields.Binary('File', readonly=True)
    name            = fields.Char('Filename', readonly=True)
    warehouse_type  = fields.Selection([('LS', 'Store'), ('LC', 'Consigment'), ('TP', 'Toko Putus'), ('CP', 'Corporate')], string='Warehouse Type')
    warehouse_id    = fields.Many2one('stock.warehouse', 'Warehouse')

    def action_generate_date(self):
        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        data_obj = self.env['generate.raw.data.stock.line']

        product_ids = self.env['product.product'].search([('active', '=', True)])
        for product in product_ids :
            parent_loc = self.env['stock.location'].search([('name', '=', self.warehouse_id.code)])
            for pl in parent_loc :
                location = self.env['stock.location'].search([('location_id', '=', pl.id),('usage', '=', 'internal')])
                for loc in location :
                    qty_begining = self.get_stock_awal(product.id,loc.id)
                    qty_receive = self.get_receive(product.id, loc.id)
                    qty_sales = self.get_sales(product.id, loc.id)
                    qty_int_transfer = self.get_internal_transfer(product.id, loc.id)
                    qty_adjustment = self.get_adjustment(product.id, loc.id)
                    qty_trans = self.get_transaction(product.id, loc.id)
                    qty_ending = qty_begining + qty_trans

                    data_vals = {
                        'reference': self.id,
                        'warehouse_type': self.warehouse_type,
                        'warehouse_id': self.warehouse_id.id,
                        'location_id': loc.id,
                        'product_category_id': product.product_category_id.id,
                        'categ_id': product.categ_id.id,
                        'product_id': product.id,
                        'uom_id': product.uom_id.id,
                        'qty_begining': qty_begining,
                        'qty_receive': qty_receive,
                        'qty_sales': qty_sales,
                        'qty_int_transfer': qty_int_transfer,
                        'qty_adjustment': qty_adjustment,
                        'qty_ending': qty_ending
                    }
                    data_obj.create(data_vals)

        return {
            'name': ('LIST DATA '+date_from+' s/d '+date_to),
            'view_type': 'form',
            'view_mode': 'tree,pivot',
            'res_model': 'generate.raw.data.stock.line',
            'domain': [('reference', '=', self.id)],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current'

        }

    @api.multi
    def get_stock_awal(self, product_id, location_id):
        cursor = self.env.cr
        qty_in = 0
        qty_out = 0
        for line in self:
            if product_id and location_id and line.date_from:
                cursor.execute("""
                                select a.qty_in, b.qty_out
                                from
                                (select sum(a.product_uom_qty) as qty_in
                                from
                                stock_move as a, stock_location as b
                                where a.location_dest_id = b.id and
                                a.state = 'done' and
                                a.product_id= %s and
                                b.id = %s and
                                a.location_id != %s and
                                (a.date + interval '7 hour')::date < %s) as a,
                                (select
                                sum(a.product_uom_qty) as qty_out
                                from stock_move as a, stock_location as b
                                where a.location_id = b.id and
                                a.state = 'done' and
                                a.product_id= %s and
                                b.id = %s and
                                a.location_dest_id != %s and
                                (a.date + interval '7 hour')::date < %s) as b
                                       """, (product_id, location_id, location_id, line.date_from, product_id, location_id, location_id, line.date_from))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
                if val[1] != None:
                    qty_out = val[1]
            qty = qty_in - qty_out
        return qty

    @api.multi
    def get_receive(self, product_id, location_id):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if product_id and location_id and line.date_from:
                cursor.execute("""
                                select
                                    sum(a.product_uom_qty) as qty_in
                                from
                                    stock_move as a, stock_location as b
                                where a.location_dest_id = b.id and
                                    a.state = 'done' and
                                    a.product_id= %s and
                                    b.id = %s and
                                    a.location_id = 8 and
                                    (a.date + interval '7 hour')::date between %s and %s
                                """,(product_id, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]

        return qty_in

    @api.multi
    def get_sales(self, product_id, location_id):
        cursor = self.env.cr
        qty_out = 0
        for line in self:
            if product_id and location_id and line.date_from:
                cursor.execute("""
                                select
                                    sum(a.product_uom_qty) as qty_out
                                from
                                    stock_move as a, stock_location as b
                                where
                                    a.location_id = b.id and
                                    a.state = 'done' and
                                    a.product_id = %s and
                                    b.id = %s and
                                    a.location_dest_id = 9 and
                                    (a.date + interval '7 hour')::date between %s and %s
                                   """, (product_id, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_out = val[0]
        return qty_out

    @api.multi
    def get_internal_transfer(self, product_id, location_id):
        cursor = self.env.cr
        qty_in = 0
        qty_out = 0
        for line in self:
            if product_id and location_id and line.date_from:
                cursor.execute("""
                                   select a.qty_in, b.qty_out
                                   from
                                   (select sum(a.product_uom_qty) as qty_in
                                   from
                                   stock_move as a, stock_location as b
                                   where a.location_dest_id = b.id and
                                   a.state = 'done' and
                                   a.product_id= %s and
                                   b.id = %s and
                                   a.location_id != %s and
                                   b.usage in ('internal','transit') and
                                   (a.date + interval '7 hour')::date between %s and %s) as a,
                                   (select
                                   sum(a.product_uom_qty) as qty_out
                                   from stock_move as a, stock_location as b
                                   where a.location_id = b.id and
                                   a.state = 'done' and
                                   a.product_id= %s and
                                   b.id = %s and
                                   b.usage in ('internal','transit') and
                                   a.location_dest_id != %s and
                                   (a.date + interval '7 hour')::date between %s and %s) as b
                                          """, (
                product_id, location_id, location_id, line.date_from, line.date_to, product_id, location_id, location_id,line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
                if val[1] != None:
                    qty_out = val[1]
            qty = qty_in - qty_out
        return qty

    @api.multi
    def get_adjustment(self, product_id, location_id):
        cursor = self.env.cr
        qty_in = 0
        qty_out = 0
        for line in self:
            if product_id and location_id and line.date_from:
                cursor.execute("""
                                      select a.qty_in, b.qty_out
                                      from
                                      (select sum(a.product_uom_qty) as qty_in
                                      from
                                      stock_move as a, stock_location as b
                                      where a.location_dest_id = b.id and
                                      a.state = 'done' and
                                      a.product_id= %s and
                                      b.id = %s and
                                      a.location_id != %s and
                                      b.usage in ('inventory') and
                                      (a.date + interval '7 hour')::date between %s and %s) as a,
                                      (select
                                      sum(a.product_uom_qty) as qty_out
                                      from stock_move as a, stock_location as b
                                      where a.location_id = b.id and
                                      a.state = 'done' and
                                      a.product_id= %s and
                                      b.id = %s and
                                      b.usage in ('inventory') and
                                      a.location_dest_id != %s and
                                      (a.date + interval '7 hour')::date between %s and %s) as b
                                             """, (
                    product_id, location_id, location_id, line.date_from, line.date_to, product_id, location_id,
                    location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
                if val[1] != None:
                    qty_out = val[1]
            qty = qty_in - qty_out
        return qty

    @api.multi
    def get_transaction(self, product_id, location_id):
        cursor = self.env.cr
        qty_in = 0
        qty_out = 0
        for line in self:
            if product_id and location_id and line.date_from:
                cursor.execute("""
                                         select a.qty_in, b.qty_out
                                         from
                                         (select sum(a.product_uom_qty) as qty_in
                                         from
                                         stock_move as a, stock_location as b
                                         where a.location_dest_id = b.id and
                                         a.state = 'done' and
                                         a.product_id= %s and
                                         b.id = %s and
                                         a.location_id != %s and
                                         (a.date + interval '7 hour')::date between %s and %s) as a,
                                         (select
                                         sum(a.product_uom_qty) as qty_out
                                         from stock_move as a, stock_location as b
                                         where a.location_id = b.id and
                                         a.state = 'done' and
                                         a.product_id= %s and
                                         b.id = %s and
                                         a.location_dest_id != %s and
                                         (a.date + interval '7 hour')::date between %s and %s) as b
                                                """, (
                    product_id, location_id, location_id, line.date_from, line.date_to, product_id, location_id,location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
                if val[1] != None:
                    qty_out = val[1]
            qty = qty_in - qty_out
        return qty


class generate_raw_data_stock_line(models.TransientModel):
    _name = 'generate.raw.data.stock.line'

    reference           = fields.Many2one('generate.raw.data.stock', 'Reference ID')
    warehouse_type      = state = fields.Selection([('LS','Store'),('LC','Consigment'),('TP','Toko Putus'),('CP','Corporate')], string='Warehouse Type')
    warehouse_id        = fields.Many2one('stock.warehouse', 'Warehouse')
    location_id         = fields.Many2one('stock.location', 'Location')
    product_category_id = fields.Many2one('lea.product.category', 'Product Category')
    categ_id            = fields.Many2one('product.category', 'Article')
    product_id          = fields.Many2one('product.product', 'Barcode')
    uom_id              = fields.Many2one('product.uom', 'UOM')
    qty_begining        = fields.Float('Qty Beginning')
    qty_receive         = fields.Float('Qty Receive')
    qty_sales           = fields.Float('Qty Sales')
    qty_int_transfer    = fields.Float('Qty Internal Transfer')
    qty_adjustment      = fields.Float('Qty Adjusment')
    qty_ending          = fields.Float('Qty Ending')











