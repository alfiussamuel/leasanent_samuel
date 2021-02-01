from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def compute_total_by_article_size(self):
        item_line = self.env['stock.picking.article']
        old_line = item_line.search([('reference', '=', self.id)])
        if old_line:
            old_line.unlink()
        cursor = self.env.cr
        cursor.execute("""
            select
                d.id
            from
                stock_pack_operation as a,
                product_product as b,
                product_template as c,
                product_category as d,
                lea_product_size as e
            where
                a.product_id = b.id and
                b.product_tmpl_id = c.id and
                c.categ_id = d.id and
                c.product_size_id = e.id and
                picking_id = %s
                group by
                d.id""",(self.id,))
        res_ids = cursor.fetchall()
        for r in res_ids:
            categ = self.env['product.category'].browse(r)
            size24 = size25 = size26 = size27 = size28 = size29 = size30 = size31 = size32 = size33 = size34 = size35 = size36 = size37 = size38 = size39 = size40 = size41 = size42 = 0
            sizexs = sizes = sizem = sizel = sizexl = sizexxl = sizeal = sizex = sizey = sizez = 0
            for line in self.move_lines :
                if line.product_id.categ_id.id == categ.id :
                    if line.product_id.product_size_id.name == "24":
                        size24 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "25":
                        size25 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "26":
                        size26 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "27":
                        size27 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "28":
                        size28 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "29":
                        size29 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "30":
                        size30 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "31":
                        size31 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "32":
                        size32 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "33":
                        size33 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "34":
                        size34 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "35":
                        size35 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "36":
                        size36 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "37":
                        size37 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "38":
                        size38 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "39":
                        size39 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "40":
                        size40 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "41":
                        size41 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "42":
                        size42 += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "XS":
                        sizexs += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "S":
                        sizes += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "M":
                        sizem += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "L":
                        sizel += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "XL":
                        sizexl += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "XXL":
                        sizexxl += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "AL":
                        sizeal += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "X":
                        sizex += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "Y":
                        sizey += line.product_uom_qty
                    elif line.product_id.product_size_id.name == "Z":
                        sizez += line.product_uom_qty
            self.env['stock.picking.article'].create({
                'reference': self.id,
                'article_code': categ.name,
                'size24': size24,
                'size25': size25,
                'size26': size26,
                'size27': size27,
                'size28': size28,
                'size29': size29,
                'size30': size30,
                'size31': size31,
                'size32': size32,
                'size33': size33,
                'size34': size34,
                'size35': size35,
                'size36': size36,
                'size37': size37,
                'size38': size38,
                'size39': size39,
                'size40': size40,
                'size41': size41,
                'size42': size42,
                'sizexs': sizexs,
                'sizes': sizes,
                'sizem': sizem,
                'sizel': sizel,
                'sizexl': sizexl,
                'sizexxl': sizexxl,
                'sizeal': sizeal,
                'sizex': sizex,
                'sizey': sizey,
                'sizez': sizez,
            })

class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_transfer2(self):
        self.action_confirm()
        self.force_assign()
        self.action_done()


