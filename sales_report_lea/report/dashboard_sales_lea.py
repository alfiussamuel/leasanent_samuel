from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    customer_type2          = fields.Selection([('JEANS STORE', 'JEANS STORE'), ('WHOLESALE', 'WHOLESALE'), ('CORPORATE', 'CORPORATE'), ('CONSIGNMENT', 'CONSIGNMENT'),('RETAIL_ONLINE', 'RETAIL_ONLINE')],compute="_get_detail", string='Customer Type', store=True)
    product_category_id     = fields.Many2one('lea.product.category', 'Product Category', compute="_get_detail", store = True)
    categ_id                = fields.Many2one('product.category', 'Article', compute="_get_detail", store = True)
    product_qc_group_id     = fields.Many2one('lea.product.qc.group', 'QC', compute="_get_detail", store = True)
    total_order_amount      = fields.Float('Total Order Amount (Gross)', compute="_get_detail", store = True)
    total_deliver_amount    = fields.Float('Total Deliver Amount (Gross)', compute="_get_detail", store = True)
    total_net_amount        = fields.Float('Total Net Amount', compute="_get_detail", store = True)
    total_discount          = fields.Float('Total Discount', compute="_get_detail", store = True)
    percent_diff_qty6       = fields.Float('Percent Delivered (Qty)', compute="_get_detail", store = True, group_operator = 'avg')
    percent_diff_price6     = fields.Float('Percent Delivered (Price)', compute="_get_detail", store = True, group_operator = 'avg')
    is_update               = fields.Boolean('Is Update')
    product_uom_qty         = fields.Float(string='Qty Order', digits=dp.get_precision('Product Unit of Measure'), required=True,default=1.0)
    qty_delivered           = fields.Float(string='Qty Delivered', copy=False, digits=dp.get_precision('Product Unit of Measure'),default=0.0)
    is_internal             = fields.Boolean(string="Internal Sales", compute="_get_detail", store = True)
    user_id                 = fields.Many2one('res.users', 'Sales Person PIC', compute="_get_detail", store = True)
    year2                   = fields.Char('Tahun', compute="_get_detail", store = True)
    product_moving_status_id2   = fields.Many2one('lea.product.moving.status', 'Moving Status', compute="_get_detail", store = True)
    product_class_category_id2  = fields.Many2one('lea.product.class.category', 'Class Category', compute="_get_detail", store = True)
    group_id2                   = fields.Many2one('res.partner', 'Group', compute="_get_detail", store = True)
    product_style_id            = fields.Many2one('lea.product.style', 'Style', compute="_get_detail",store=True)
    product_raw_material_id     = fields.Many2one('lea.product.raw.material', 'Material', compute="_get_detail", store=True)
    location_owner_id           = fields.Many2one('res.partner', 'Owner', compute="_get_detail", store=True)
    area_id                     = fields.Many2one('lea.area', 'Area', compute="_get_detail", store=True)
    sub_area_id                 = fields.Many2one('lea.sub.area', 'Sub Area', compute="_get_detail", store=True)
    sales_head_id               = fields.Many2one('res.users', 'Sales Head', compute="_get_detail", store=True)


    @api.depends('product_id.product_style_id','product_id.product_raw_material_id','order_id.warehouse_id','order_id.partner_id.user_id','product_id.product_moving_status_id','product_id.product_class_category_id','order_id.partner_id.group_id','order_date','order_id.partner_id','order_id.partner_id.user_id','order_id.is_internal','product_id','price_unit','product_uom_qty','qty_delivered','product_id.categ_id','product_id.product_category_id','product_id.product_qc_group_id', 'is_update','order_id.partner_id.customer_type','order_id.partner_id.area_id','order_id.partner_id.sub_area_id','order_id.partner_id.sales_head_id')
    def _get_detail(self):
        for res in self:
            total_order_amount = 0
            total_deliver_amount = 0
            qty_selisih = 0
            percent_qty = 0
            price_selisih = 0
            percent_selisih = 0
            total_discount = 0
            year = ''
            moving_status = False
            class_category = False
            group_id = False
            loc_owner_id = False
            style = False
            material = False
            area = False
            subarea = False
            sales_head = False

            if res.order_id:
                res.customer_type2      = res.order_id.partner_id.customer_type
                res.product_category_id = res.product_id.product_category_id.id
                res.categ_id            = res.product_id.categ_id.id
                res.product_qc_group_id = res.product_id.product_qc_group_id.id
                res.user_id             = res.order_id.partner_id.user_id.id
                group_id                = res.order_id.partner_id.group_id.id

                if res.order_id.partner_id.area_id:
                    area = res.order_id.partner_id.area_id.id
                if res.order_id.partner_id.sub_area_id:
                    subarea = res.order_id.partner_id.sub_area_id.id
                if res.order_id.partner_id.sales_head_id :
                    sales_head = res.order_id.partner_id.sales_head_id.id

            if res.price_unit and res.product_uom_qty :
                total_order_amount = res.price_unit * res.product_uom_qty
            if res.price_unit and res.qty_delivered:
                total_deliver_amount = res.price_unit * res.qty_delivered
            if res.product_uom_qty !=0 :
                percent_qty = (res.qty_delivered/res.product_uom_qty) * 100
            if total_order_amount != 0 :
                percent_selisih = (total_deliver_amount/total_order_amount) * 100#(total_order_amount-total_deliver_amount)/total_order_amount * 100
            if res.discount != 0 :
                discount_rate = float(res.discount)/100
                total_discount = (discount_rate * total_deliver_amount) + res.manual_discount
            if res.order_date :
                date2 = datetime.strptime(res.order_date, '%Y-%m-%d')
                new_date = datetime.strftime(date2, '%Y')
                year = new_date
            if res.product_id:
                moving_status = res.product_id.product_moving_status_id.id
                class_category = res.product_id.product_class_category_id.id
                style = res.product_id.product_style_id.id
                material = res.product_id.product_raw_material_id.id

            if res.order_id.warehouse_id :
                loc_owner_id = res.order_id.warehouse_id.lot_stock_id.partner_id.id

            total_net_amount = total_deliver_amount - total_discount
            res.total_order_amount = total_order_amount
            res.total_net_amount = total_net_amount
            res.total_deliver_amount = total_deliver_amount
            res.percent_diff_qty6 = percent_qty
            res.percent_diff_price6 = percent_selisih
            res.total_discount = total_discount
            res.is_internal = res.order_id.is_internal
            res.year2 = year
            res.product_moving_status_id2 = moving_status
            res.product_class_category_id2 = class_category
            res.group_id2 = group_id
            res.product_style_id = style
            res.location_owner_id = loc_owner_id
            res.product_raw_material_id = material
            res.area_id = area
            res.sub_area_id = subarea
            res.sales_head_id = sales_head

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    customer_type2 = fields.Selection(
        [('JEANS STORE', 'JEANS STORE'), ('WHOLESALE', 'WHOLESALE'), ('CORPORATE', 'CORPORATE'),
         ('CONSIGNMENT', 'CONSIGNMENT'),('RETAIL_ONLINE', 'RETAIL_ONLINE')], compute="_get_detail", string='Customer Type', store=True)
    product_category_id = fields.Many2one('lea.product.category', 'Product Category', compute="_get_detail", store=True)
    categ_id = fields.Many2one('product.category', 'Article', compute="_get_detail", store=True)
    product_qc_group_id = fields.Many2one('lea.product.qc.group', 'QC', compute="_get_detail", store=True)
    state = fields.Selection([
                                ('draft', 'Draft'),
                                ('proforma', 'Pro-forma'),
                                ('proforma2', 'Pro-forma'),
                                ('open', 'Open'),
                                ('paid', 'Paid'),
                                ('cancel', 'Cancelled')
                            ], compute="_get_detail", string='State', store=True)

    type = fields.Selection([
                ('out_invoice', 'Customer Invoice'),
                ('in_invoice', 'Vendor Bill'),
                ('out_refund', 'Customer Refund'),
                ('in_refund', 'Vendor Refund'),
            ], compute="_get_detail", string='Type', store=True)
    date_invoice = fields.Date('Invoice Date', compute="_get_detail", store=True)
    is_internal = fields.Boolean(string="Internal Sales", compute="_get_detail", store=True)
    is_update = fields.Boolean('Is Update')
    user_id = fields.Many2one('res.users', 'Sales Person PIC', compute="_get_detail", store=True)
    year = fields.Char('Tahun', compute="_get_detail", store=True)
    product_moving_status_id = fields.Many2one('lea.product.moving.status', 'Moving Status', compute="_get_detail", store=True)
    product_class_category_id = fields.Many2one('lea.product.class.category', 'Class Category', compute="_get_detail",store=True)
    group_id = fields.Many2one('res.partner', 'Group', compute="_get_detail", store=True)
    product_style_id = fields.Many2one('lea.product.style', 'Style', compute="_get_detail", store=True)
    product_raw_material_id = fields.Many2one('lea.product.raw.material', 'Material', compute="_get_detail", store=True)
    area_id = fields.Many2one('lea.area', 'Area', compute="_get_detail", store=True)
    sub_area_id = fields.Many2one('lea.sub.area', 'Sub Area', compute="_get_detail", store=True)
    sales_head_id = fields.Many2one('res.users', 'Sales Head', compute="_get_detail", store=True)
    sale_type_id = fields.Many2one('sale.order.type', 'Sale Type', compute="_get_detail", store=True)

    @api.depends('partner_id','partner_id.group_id','partner_id.area_id','partner_id.sub_area_id','partner_id.sales_head_id', 'invoice_id.date_invoice','product_id','product_id.categ_id','product_id.product_category_id','product_id.product_qc_group_id','invoice_id.state','invoice_id.type','invoice_id.is_internal', 'is_update','partner_id.user_id','product_id.product_moving_status_id','product_id.product_class_category_id','invoice_id.sale_type_id')
    def _get_detail(self):
        for res in self:
            year = ''
            moving_status = False
            class_category = False
            group_id = False
            style = False
            material = False
            area = False
            subarea = False
            sales_head = False
            sale_type_id = False

            if res.invoice_id.date_invoice:
                date2 = datetime.strptime(res.invoice_id.date_invoice, '%Y-%m-%d')
                new_date = datetime.strftime(date2, '%Y')
                year = new_date
            if res.partner_id:
                res.customer_type2 = res.partner_id.customer_type
                res.user_id = res.partner_id.user_id.id
                group_id = res.partner_id.group_id.id
                if res.partner_id.area_id :
                    area = res.partner_id.area_id.id
                if res.partner_id.sub_area_id:
                    subarea = res.partner_id.sub_area_id.id
                if res.partner_id.sales_head_id :
                    sales_head = res.partner_id.sales_head_id.id

            if res.product_id:
                res.product_category_id = res.product_id.product_category_id.id
                res.categ_id = res.product_id.categ_id.id
                res.product_qc_group_id = res.product_id.product_qc_group_id.id
                moving_status = res.product_id.product_moving_status_id.id
                class_category = res.product_id.product_class_category_id.id
                style = res.product_id.product_style_id.id
                material = res.product_id.product_raw_material_id.id

            if res.invoice_id.sale_type_id:
                sale_type_id = res.invoice_id.sale_type_id.id


            res.state = res.invoice_id.state
            res.type = res.invoice_id.type
            res.date_invoice = res.invoice_id.date_invoice
            res.is_internal  = res.invoice_id.is_internal
            res.year = year
            res.product_moving_status_id = moving_status
            res.product_class_category_id = class_category
            res.group_id = group_id
            res.product_style_id = style
            res.product_raw_material_id = material
            res.area_id = area
            res.sub_area_id = subarea
            res.sales_head_id = sales_head
            res.sale_type_id = sale_type_id


class wizard_update_dashboard(models.TransientModel):
    _name = "wizard.update.dashboard.sales"
    _description = "Update Store Sales Detail"

    def action_update_dashboard(self):
        active_id = self.env.context.get('active_ids')
        for line in active_id:
            order_obj = self.env['sale.order.line'].browse(line)
            order_obj.write({'is_update':True})

class wizard_update_dashboard_inv(models.TransientModel):
    _name = "wizard.update.dashboard.inv"
    _description = "Update Store Invoice Detail"

    def action_update_dashboard(self):
        active_id = self.env.context.get('active_ids')
        for line in active_id:
            order_obj = self.env['account.invoice.line'].browse(line)
            order_obj.write({'is_update':True})





