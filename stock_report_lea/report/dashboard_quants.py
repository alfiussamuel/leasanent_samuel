from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re

class StockQuants(models.Model):
    _inherit = 'stock.quant'

    product_category_id2 = fields.Many2one('lea.product.category', 'Product Category', compute="_get_detail", store = True)
    categ_id2 = fields.Many2one('product.category', 'Article', compute="_get_detail", store = True)
    product_qc_group_id2 = fields.Many2one('lea.product.qc.group', 'QC', compute="_get_detail", store = True)
    product_moving_status_id = fields.Many2one(compute='_get_detail', comodel_name='lea.product.moving.status', 
        string='Moving Status', store=True)
    is_update = fields.Boolean('Is Update')

    product_class_category_id2 = fields.Many2one('lea.product.class.category', 'Class Category', compute="_get_detail",store=True)
    product_raw_material_id = fields.Many2one('lea.product.raw.material', 'Material', compute="_get_detail", store=True)
    product_style_id = fields.Many2one('lea.product.style', 'Style', compute="_get_detail", store=True)
    product_size_id = fields.Many2one('lea.product.size', 'Size', compute="_get_detail", store=True)
    wh_type = fields.Selection(
        [('LS', 'STORE'),
         ('LC', 'CONSIGMENT'),
         ('TP', 'TOKO PUTUS'),
         ('CP', 'CORPORATE'),
         ('MW', 'MAIN WH'),
         ], compute="_get_detail", string='WH Type', store=True)
    wh_subarea_id = fields.Many2one('lea.sub.area', 'Sub Area', compute="_get_detail", store=True)
    product_brand_id = fields.Many2one('lea.product.brand', 'Brand', compute="_get_detail",store=True)


    # @api.depends('product_id','product_id.product_brand_id','product_id.product_moving_status_id','product_id.product_class_category_id','product_id.product_raw_material_id','product_id.product_style_id','product_id.product_size_id','is_update')
    @api.multi
    def _get_detail(self):
        for res in self:
            categ_id = False
            product_qc_group_id = False
            product_category_id = False
            moving_status = False
            size = False
            class_category = False
            material = False
            style = False
            wh_type = ""
            area = False
            brand = False


            if res.product_id.categ_id :
                categ_id = res.product_id.categ_id.id
            if res.product_id.product_qc_group_id :
                product_qc_group_id = res.product_id.product_qc_group_id.id
            if res.product_id.product_category_id :
                product_category_id = res.product_id.product_category_id.id
            if res.product_id.product_moving_status_id :
                moving_status = res.product_id.product_tmpl_id.product_moving_status_id.id
            if res.product_id.product_class_category_id.id :
                class_category = res.product_id.product_class_category_id.id
            if res.product_id.product_raw_material_id :
                material = res.product_id.product_raw_material_id.id
            if res.product_id.product_style_id :
                style = res.product_id.product_style_id.id
            if res.product_id.product_size_id :
                size = res.product_id.product_size_id.id
            if res.location_id :
                wh = self.env['stock.warehouse'].search([('lot_stock_id', '=', res.location_id.id)],limit=1)
                if wh :
                    for w in wh :
                        wh_type = w.wh_type
                        area = w.wh_subarea_id.id
            if res.product_id.product_brand_id :
                brand = res.product_id.product_brand_id.id

            res.categ_id2 = categ_id
            res.product_qc_group_id2 = product_qc_group_id
            res.product_category_id2 = product_category_id
            # res.product_moving_status_id = moving_status
            res.product_class_category_id2 = class_category
            res.product_raw_material_id = material
            res.product_style_id = style
            res.product_size_id = size
            res.wh_type = wh_type
            res.wh_subarea_id = area
            res.product_brand_id = brand


class wizard_update_dashboard_stock_quants(models.TransientModel):
    _name = "wizard.update.dashboard.quants"
    _description = "Update Stock Quants"

    def action_update_dashboard(self):
        active_id = self.env.context.get('active_ids')
        for line in active_id:
            order_obj = self.env['stock.quant'].browse(line)
            order_obj.write({'is_update':True})


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_category_id2 = fields.Many2one('lea.product.category', 'Product Category', compute="_get_detail", store = True)
    categ_id2 = fields.Many2one('product.category', 'Article', compute="_get_detail", store = True)
    product_qc_group_id2 = fields.Many2one('lea.product.qc.group', 'QC', compute="_get_detail", store = True)
    product_moving_status_id = fields.Many2one('lea.product.moving.status', 'Moving Status', compute="_get_detail",store=True)
    is_update = fields.Boolean('Is Update')

    product_class_category_id2 = fields.Many2one('lea.product.class.category', 'Class Category', compute="_get_detail",store=True)
    product_raw_material_id = fields.Many2one('lea.product.raw.material', 'Material', compute="_get_detail", store=True)
    product_style_id = fields.Many2one('lea.product.style', 'Style', compute="_get_detail", store=True)
    product_size_id = fields.Many2one('lea.product.size', 'Size', compute="_get_detail", store=True)


    @api.depends('product_id','product_id.product_moving_status_id','product_id.product_class_category_id','product_id.product_raw_material_id','product_id.product_style_id','product_id.product_size_id','is_update')
    def _get_detail(self):
        for res in self:
            categ_id = False
            product_qc_group_id = False
            product_category_id = False
            moving_status = False
            size = False
            class_category = False
            material = False
            style = False

            if res.product_id.categ_id :
                categ_id = res.product_id.categ_id.id
            if res.product_id.product_qc_group_id :
                product_qc_group_id = res.product_id.product_qc_group_id.id
            if res.product_id.product_category_id :
                product_category_id = res.product_id.product_category_id.id
            if res.product_id.product_moving_status_id :
                moving_status = res.product_id.product_moving_status_id.id
            if res.product_id.product_class_category_id.id :
                class_category = res.product_id.product_class_category_id.id
            if res.product_id.product_raw_material_id :
                material = res.product_id.product_raw_material_id.id
            if res.product_id.product_style_id :
                style = res.product_id.product_style_id.id
            if res.product_id.product_size_id :
                size = res.product_id.product_size_id.id

            res.categ_id2 = categ_id
            res.product_qc_group_id2 = product_qc_group_id
            res.product_category_id2 = product_category_id
            res.product_moving_status_id = moving_status
            res.product_class_category_id2 = class_category
            res.product_raw_material_id = material
            res.product_style_id = style
            res.product_size_id = size

    class wizard_update_dashboard_stock_move(models.TransientModel):
        _name = "wizard.update.dashboard.stock.move"
        _description = "Update Stock Move"

        def action_update_dashboard(self):
            active_id = self.env.context.get('active_ids')
            for line in active_id:
                order_obj = self.env['stock.move'].browse(line)
                order_obj.write({'is_update': True})
