from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re

class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_main_wh_location = fields.Boolean('Is Main WH Location')
    address = fields.Text('Address')

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    tipe_penjualan_toko = fields.Selection([('non-jual-toko', 'Non Brg Jual Toko'), ('jual-toko', 'Brg Jual Toko')], string="Status Brg Jual")


class StockClosingGroup(models.Model):
    _name = 'stock.closing.group'

    @api.model
    def _default_company(self):
        user = self.env['res.users'].browse(self.env.uid)
        return user.company_id.id

    name            = fields.Char('Doc. No')
    period_id       = fields.Many2one('account.period', 'Period')
    date            = fields.Date('Date Start')
    date_end        = fields.Date('Date Stop')
    location_id     = fields.Many2one('stock.location', 'Location')
    closing_lines   = fields.One2many('stock.closing', 'reference_id', 'Closing Lines')
    state           = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancel')], readonly=True,default='draft', copy=False, string="Status")
    company_id      = fields.Many2one('res.company', 'Company', default=_default_company)




class StockClosing(models.Model):
    _name = 'stock.closing'

    name            = fields.Char('Doc')
    reference_id    = fields.Many2one('stock.closing.group', 'Reference')
    product_id  = fields.Many2one('product.product', 'Product')
    period_id   = fields.Many2one('account.period', 'Period')
    date        = fields.Date('Date Start')
    date_end    = fields.Date('Date Stop')
    location_id = fields.Many2one('stock.location', 'Location')
    initial_qty = fields.Float('Initial Stock')
    in_qty      = fields.Float('Stock In')
    out_qty     = fields.Float('Stock Out')
    final_qty   = fields.Float('Final Stock')


class wizard_closing_stock(models.TransientModel):
    _name = 'wizard.closing.stock'

    @api.model
    def _default_company(self):
        user = self.env['res.users'].browse(self.env.uid)
        return user.company_id.id

    product_id  = fields.Many2many('product.product', 'Product')
    period_id   = fields.Many2one('account.period', 'Period')
    date_from   = fields.Date('Date Start')
    date_to     = fields.Date('Date Stop')
    location_id = fields.Many2one('stock.location', 'Location')
    company_id  = fields.Many2one('res.company', 'Company', default=_default_company)

    def action_generate_close(self):
        a = 0


    @api.multi
    @api.onchange('period_id')
    def onchange_period_id(self):
        values = {
            'date_from': '',
            'date_to': '',
        }
        if self.period_id:
            values['date_from'] = self.period_id.date_start
            values['date_to'] = self.period_id.date_stop
        self.update(values)

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
                                           """, (
                product_id, location_id, location_id, line.date_from, product_id, location_id, location_id,
                line.date_from))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
                if val[1] != None:
                    qty_out = val[1]
            qty = qty_in - qty_out
        return qty

    @api.multi
    def get_stock(self, product_id, location_id):
        cursor = self.env.cr
        qty_in = 0
        qty_out = 0
        for line in self:
            if product_id and location_id and line.date_from and line.date_to:
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
                    product_id, location_id, location_id, line.date_from, line.date_to, product_id, location_id, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
                if val[1] != None:
                    qty_out = val[1]
            #qty = qty_in - qty_out
        return [qty_in, qty_out]




