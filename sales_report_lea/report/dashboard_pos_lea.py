from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'


    customer_type2      = fields.Selection([('JEANS STORE', 'JEANS STORE'), ('WHOLESALE', 'WHOLESALE'), ('CORPORATE', 'CORPORATE'), ('CONSIGNMENT', 'CONSIGNMENT'),('RETAIL_ONLINE', 'RETAIL ONLINE')],compute="_get_detail", string='Customer Type', store=True)
    product_category_id = fields.Many2one('lea.product.category', 'Product Category', compute="_get_detail", store = True)
    categ_id            = fields.Many2one('product.category', 'Article', compute="_get_detail", store = True)
    product_qc_group_id = fields.Many2one('lea.product.qc.group', 'QC', compute="_get_detail", store = True)
    product_moving_status_id2  = fields.Many2one('lea.product.moving.status', 'Moving Status', compute="_get_detail",store=True)
    product_class_category_id2 = fields.Many2one('lea.product.class.category', 'Class Category', compute="_get_detail",store=True)
    group_id2                  = fields.Many2one('res.partner', 'Group', compute="_get_detail", store=True)
    is_update                  = fields.Boolean('Is Update')
    partner_id                 = fields.Many2one('res.partner', 'Partner', compute="_get_detail",store=True)
    price_subtotal3            = fields.Float(compute="_get_detail", digits=0, string='Subtotal w/o Tax', store= True)
    location_id                = fields.Many2one('stock.location', 'location', compute="_get_detail", store=True)
    user_id                    = fields.Many2one('res.users', 'Salesman', compute="_get_detail", store=True)
    state                      = fields.Selection([('draft', 'New'), ('cancel', 'Cancelled'), ('paid', 'Paid'), ('done', 'Posted'), ('invoiced', 'Invoiced')],'Status', compute="_get_detail", store=True)
    date_order2                = fields.Date('Date Order', compute="_get_detail", store=True)
    year                       = fields.Char('Tahun', compute="_get_detail", store=True)
    price_category             = fields.Char('Price Category', compute="_get_detail", store=True)
    product_style_id = fields.Many2one('lea.product.style', 'Style', compute="_get_detail", store=True)
    product_raw_material_id = fields.Many2one('lea.product.raw.material', 'Material', compute="_get_detail", store=True)
    location_owner_id = fields.Many2one('res.partner', 'Owner', compute="_get_detail", store=True)

    @api.depends('product_id.product_style_id','product_id.product_raw_material_id','order_id.date_order','discount','price_unit','qty','is_update','order_id.partner_id.user_id','order_id.state','product_id.product_moving_status_id',
                 'product_id.product_class_category_id', 'order_id.partner_id.group_id',
                 'order_id.partner_id', 'product_id', 'product_id.categ_id','product_id.product_category_id', 'product_id.product_qc_group_id', 'order_id.partner_id.customer_type','order_id.user_id')
    def _get_detail(self):
        for res in self:
            moving_status = False
            class_category = False
            group_id = False
            customer_type = ''
            product_category_id = False
            categ_id = False
            product_qc_group_id = False
            #sales_id = False
            partner_id = False
            location_id = False
            user_id = False
            state = ""
            loc_owner_id = False
            style = False
            material = False

            if res.order_id:
                customer_type = res.order_id.partner_id.customer_type

                user_id = res.order_id.user_id.id

                group_id = res.order_id.partner_id.group_id.id
                partner_id = res.order_id.partner_id.id
                location_id = res.order_id.location_id.id
                loc_owner_id = res.order_id.location_id.partner_id.id
                #sales_id = res.order_id.user_id.id
                state = res.order_id.state
                date2 = datetime.strptime(res.order_id.date_order, '%Y-%m-%d %H:%M:%S')
                date2 += timedelta(hours=7)
                date_order = date2.date()
                new_date = datetime.strftime(date2, '%Y')
                year = new_date
            if res.product_id:
                moving_status = res.product_id.product_moving_status_id.id
                class_category = res.product_id.product_class_category_id.id
                product_category_id = res.product_id.product_category_id.id
                categ_id = res.product_id.categ_id.id
                product_qc_group_id = res.product_id.product_qc_group_id.id
                style = res.product_id.product_style_id.id
                material = res.product_id.product_raw_material_id.id

            price = res.price_unit * (1 - (res.discount or 0.0) / 100.0)
            price_subtotal = price * res.qty
            price_category = "Normal Price"
            if res.discount > 0 :
                price_category = 'Discount '+str(res.discount)+'%'

            res.product_moving_status_id2 = moving_status
            res.product_class_category_id2 = class_category
            res.group_id2 = group_id
            res.product_category_id = product_category_id
            res.categ_id = categ_id
            res.product_qc_group_id = product_qc_group_id
            res.customer_type2 = customer_type
            res.user_id = user_id
            res.partner_id = partner_id
            res.location_id = location_id
            res.state = state
            res.price_subtotal3 = price_subtotal
            res.date_order2 = date_order
            res.year = year
            res.price_category = price_category
            res.product_style_id = style
            res.location_owner_id = loc_owner_id
            res.product_raw_material_id = material


class wizard_update_dashboard(models.TransientModel):
    _name = "wizard.update.dashboard.pos"
    _description = "Update POS Detail"

    def action_update_dashboard(self):
        active_id = self.env.context.get('active_ids')
        for line in active_id:
            order_obj = self.env['pos.order.line'].browse(line)
            order_obj.write({'is_update':True})
