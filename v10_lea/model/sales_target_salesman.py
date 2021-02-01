from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re
    
STATE = [
    ('draft','Draft'),
    ('approved','Approved'),
    ('cancel','Cancel'),
]

class LeaSalesTargetSalesman(models.Model):
    _name = 'lea.sales.target.salesman'
    _rec_name = 'year'
    _order = 'year desc'
            
    #BY VALUE
    @api.depends('total_target')
    def compute_avg_target(self):
        for rec in self:
            if rec.total_target > 0:
                rec.avg_target = float(rec.total_target) / 12.00
    
    #BY QTY
    @api.depends('qty_total_target')
    def compute_avg_target_qty(self):
        for rec in self:
            if rec.qty_total_target > 0:
                rec.qty_avg_target = float(rec.qty_total_target) / 12.00

    @api.one
    def button_approved(self):
        self.state = 'approved'

    @api.one
    def button_cancel(self):
        self.state = 'cancel'

    @api.one
    def button_reset_draft(self):
        self.state = 'draft'
        self.revision = self.revision + 1

    def lock_default_target_ratio(self):
        if (self.default_month1+self.default_month2+self.default_month3+self.default_month4+self.default_month5+self.default_month6+self.default_month7+self.default_month8+self.default_month9+self.default_month10+self.default_month11+self.default_month12) != 1200:
            raise Warning('Pembagian default ratio bulanan belum sesuai, harap sesuaikan jumlah menjadi 1.200% !')
        if (self.qty_default_month1+self.qty_default_month2+self.qty_default_month3+self.qty_default_month4+self.qty_default_month5+self.qty_default_month6+self.qty_default_month7+self.qty_default_month8+self.qty_default_month9+self.qty_default_month10+self.qty_default_month11+self.qty_default_month12) != 1200:
            raise Warning('Pembagian default ratio bulanan belum sesuai, harap sesuaikan jumlah menjadi 1.200% !')

    def lock_contribution_channel(self):
        if self.channel_ids :
            contribution = 0
            for rec in self.channel_ids:
                contribution2 = 0
                contribution += rec.contribution
                for x in rec.category_ids:
                    contribution2 += x.contribution
                if float(contribution2) <= 99.99 or float(contribution2) >= 100.01:
                    raise Warning('Pembagian contribution category belum sesuai, harap sesuaikan jumlah menjadi 100% ! ' + 'Salesman : ' + rec.salesman_id.name)
            if float(contribution) <= 99.99 or float(contribution) >= 100.01:
                raise Warning('Pembagian contribution channel value belum sesuai, harap sesuaikan jumlah menjadi 100% !')

        if self.brt_ids :
            contribution = 0
            for rec in self.brt_ids:
                contribution2 = 0
                contribution += rec.contribution
                for x in rec.category_ids:
                    contribution2 += x.contribution
                if float(contribution2) <= 99.99 or float(contribution2) >= 100.01:
                    raise Warning('Pembagian contribution category belum sesuai, harap sesuaikan jumlah menjadi 100% ! ' + 'Salesman : ' + rec.salesman_id.name)
            if float(contribution) <= 99.99 or float(contribution) >= 100.01:
                raise Warning('Pembagian contribution channel value belum sesuai, harap sesuaikan jumlah menjadi 100% !')

        if self.tmr_ids :
            contribution = 0
            for rec in self.tmr_ids:
                contribution2 = 0
                contribution += rec.contribution
                for x in rec.category_ids:
                    contribution2 += x.contribution
                if float(contribution2) <= 99.99 or float(contribution2) >= 100.01:
                    raise Warning('Pembagian contribution category belum sesuai, harap sesuaikan jumlah menjadi 100% ! ' + 'Salesman : ' + rec.salesman_id.name)
            if float(contribution) <= 99.99 or float(contribution) >= 100.01:
                raise Warning('Pembagian contribution channel value belum sesuai, harap sesuaikan jumlah menjadi 100% !')

        if self.mdn_ids :
            contribution = 0
            for rec in self.mdn_ids:
                contribution2 = 0
                contribution += rec.contribution
                for x in rec.category_ids:
                    contribution2 += x.contribution
                if float(contribution2) <= 99.99 or float(contribution2) >= 100.01:
                    raise Warning('Pembagian contribution category belum sesuai, harap sesuaikan jumlah menjadi 100% ! ' + 'Salesman : ' + rec.salesman_id.name)
            if float(contribution) <= 99.99 or float(contribution) >= 100.01:
                raise Warning('Pembagian contribution channel value belum sesuai, harap sesuaikan jumlah menjadi 100% !')

        if self.qty_channel_ids :
            contribution_qty = 0
            for rec in self.qty_channel_ids:
                contribution_qty2 = 0
                contribution_qty += rec.contribution
                for x in rec.category_ids :
                    contribution_qty2 += x.contribution
                if float(contribution_qty2) <= 99.99 or float(contribution_qty2) >= 100.01:
                    raise Warning('Pembagian contribution category qty belum sesuai, harap sesuaikan jumlah menjadi 100% ! ' + 'Salesman : ' + rec.salesman_id.name)
            if float(contribution_qty) <= 99.99 or float(contribution_qty) >= 100.01:
                raise Warning('Pembagian contribution channel qty belum sesuai, harap sesuaikan jumlah menjadi 100% !')

        if self.qty_brt_ids :
            contribution_qty = 0
            for rec in self.qty_brt_ids:
                contribution_qty2 = 0
                contribution_qty += rec.contribution
                for x in rec.category_ids :
                    contribution_qty2 += x.contribution
                if float(contribution_qty2) <= 99.99 or float(contribution_qty2) >= 100.01:
                    raise Warning('Pembagian contribution category qty belum sesuai, harap sesuaikan jumlah menjadi 100% ! ' + 'Salesman : ' + rec.salesman_id.name)
            if float(contribution_qty) <= 99.99 or float(contribution_qty) >= 100.01:
                raise Warning('Pembagian contribution channel qty belum sesuai, harap sesuaikan jumlah menjadi 100% !')

        if self.qty_tmr_ids :
            contribution_qty = 0
            for rec in self.qty_tmr_ids:
                contribution_qty2 = 0
                contribution_qty += rec.contribution
                for x in rec.category_ids :
                    contribution_qty2 += x.contribution
                if float(contribution_qty2) <= 99.99 or float(contribution_qty2) >= 100.01:
                    raise Warning('Pembagian contribution category qty belum sesuai, harap sesuaikan jumlah menjadi 100% ! ' + 'Salesman : ' + rec.salesman_id.name)
            if float(contribution_qty) <= 99.99 or float(contribution_qty) >= 100.01:
                raise Warning('Pembagian contribution channel qty belum sesuai, harap sesuaikan jumlah menjadi 100% !')

        if self.qty_mdn_ids :
            contribution_qty = 0
            for rec in self.qty_mdn_ids:
                contribution_qty2 = 0
                contribution_qty += rec.contribution
                for x in rec.category_ids :
                    contribution_qty2 += x.contribution
                if float(contribution_qty2) <= 99.99 or float(contribution_qty2) >= 100.01:
                    raise Warning('Pembagian contribution category qty belum sesuai, harap sesuaikan jumlah menjadi 100% ! ' + 'Salesman : ' + rec.salesman_id.name)
            if float(contribution_qty) <= 99.99 or float(contribution_qty) >= 100.01:
                raise Warning('Pembagian contribution channel qty belum sesuai, harap sesuaikan jumlah menjadi 100% !')

    @api.multi
    def write(self, vals):
        res = super(LeaSalesTargetSalesman, self).write(vals)
        self.lock_default_target_ratio()
        self.lock_contribution_channel()
        return res

    year            = fields.Char('Year')
    state           = fields.Selection(STATE, 'State', default='draft')
    revision        = fields.Integer('Revision Number', readonly=True)
    area = fields.Selection([('all','All'),('area','Area')], "Pilih Area", default="all")
    area_id = fields.Many2one("lea.area", "Area")
    area_id_name = fields.Char("Area Name", related='area_id.name')
    qty_area = fields.Selection([('all','All'),('area','Area')], "Pilih Area", default="all")
    qty_area_id = fields.Many2one("lea.area", "Area")
    qty_area_id_name = fields.Char("Qty Area Name", related='qty_area_id.name')

    #BY VALUE
    total_target    = fields.Float('Total Target')
    avg_target      = fields.Float('Avg. Target/Month', compute='compute_avg_target', store=True)
    channel_ids     = fields.One2many(comodel_name='lea.sales.target.salesman.sales',inverse_name='reference',string='Salesman', domain=[('area','=','all')])
    brt_ids     = fields.One2many(comodel_name='lea.sales.target.salesman.sales',inverse_name='reference',string='BRT', domain=[('area','=','brt')])
    tmr_ids     = fields.One2many(comodel_name='lea.sales.target.salesman.sales',inverse_name='reference',string='TMR', domain=[('area','=','tmr')])
    mdn_ids     = fields.One2many(comodel_name='lea.sales.target.salesman.sales',inverse_name='reference',string='MDN', domain=[('area','=','mdn')])
    default_month1  = fields.Float('January', default=100)
    default_month2  = fields.Float('February', default=100)
    default_month3  = fields.Float('March', default=100)
    default_month4  = fields.Float('April', default=100)
    default_month5  = fields.Float('May', default=100)
    default_month6  = fields.Float('June', default=100)
    default_month7  = fields.Float('July', default=100)
    default_month8  = fields.Float('August', default=100)
    default_month9  = fields.Float('September', default=100)
    default_month10 = fields.Float('October', default=100)
    default_month11 = fields.Float('November', default=100)
    default_month12 = fields.Float('December', default=100)
    
    #BY QTY
    qty_total_target    = fields.Float('Total Target')
    qty_avg_target      = fields.Float('Avg. Target/Month', compute='compute_avg_target_qty', store=True)
    qty_channel_ids     = fields.One2many(comodel_name='lea.sales.target.qty.salesman.sales',inverse_name='reference',string='Salesman', domain=[('area','=','all')])
    qty_brt_ids     = fields.One2many(comodel_name='lea.sales.target.qty.salesman.sales',inverse_name='reference',string='BRT', domain=[('area','=','brt')])
    qty_tmr_ids     = fields.One2many(comodel_name='lea.sales.target.qty.salesman.sales',inverse_name='reference',string='TMR', domain=[('area','=','tmr')])
    qty_mdn_ids     = fields.One2many(comodel_name='lea.sales.target.qty.salesman.sales',inverse_name='reference',string='MDN', domain=[('area','=','mdn')])
    qty_default_month1  = fields.Float('January', default=100)
    qty_default_month2  = fields.Float('February', default=100)
    qty_default_month3  = fields.Float('March', default=100)
    qty_default_month4  = fields.Float('April', default=100)
    qty_default_month5  = fields.Float('May', default=100)
    qty_default_month6  = fields.Float('June', default=100)
    qty_default_month7  = fields.Float('July', default=100)
    qty_default_month8  = fields.Float('August', default=100)
    qty_default_month9  = fields.Float('September', default=100)
    qty_default_month10 = fields.Float('October', default=100)
    qty_default_month11 = fields.Float('November', default=100)
    qty_default_month12 = fields.Float('December', default=100)

    @api.one
    def button_generate_value(self):
        if self.total_target > 0:

            if (self.default_month1+self.default_month2+self.default_month3+self.default_month4+self.default_month5+self.default_month6+self.default_month7+self.default_month8+self.default_month9+self.default_month10+self.default_month11+self.default_month12) != 1200:
                raise Warning('Pembagian default ration bulanan belum sesuai, harap sesuaikan jumlah menjadi 1.200% !')

            #clear existing data
            for c in self.channel_ids:
                c.sudo().unlink()
            for brt in self.brt_ids:
                brt.sudo().unlink()
            for tmr in self.tmr_ids:
                tmr.sudo().unlink()
            for mdn in self.mdn_ids:
                mdn.sudo().unlink()

            category_list = []
            category_ids = self.env['lea.product.moving.status'].search([])
            for p in category_ids:
                contribution = p.default_contribution
                if contribution == 0:
                    contribution = 100.00 / float(len(category_ids))

                category_list.append((0,0,{
                    'category_id'       : p.id,
                    'contribution'      : contribution,
                    'ratio_month1'      : self.default_month1,
                    'ratio_month2'      : self.default_month2,
                    'ratio_month3'      : self.default_month3,
                    'ratio_month4'      : self.default_month4,
                    'ratio_month5'      : self.default_month5,
                    'ratio_month6'      : self.default_month6,
                    'ratio_month7'      : self.default_month7,
                    'ratio_month8'      : self.default_month8,
                    'ratio_month9'      : self.default_month9,
                    'ratio_month10'     : self.default_month10,
                    'ratio_month11'     : self.default_month11,
                    'ratio_month12'     : self.default_month12,
                }))

            if self.area == 'all':
                channel_ids = self.env['res.users'].search([('active','=',True)])
                for c in channel_ids:
                    self.env['lea.sales.target.salesman.sales'].sudo().create({
                       'reference'      : self.id,
                       'salesman_id'    : c.id,
                       'contribution'   : 100.00 / float(len(channel_ids)),
                       'ratio_month1'   : self.default_month1,
                       'ratio_month2'   : self.default_month2,
                       'ratio_month3'   : self.default_month3,
                       'ratio_month4'   : self.default_month4,
                       'ratio_month5'   : self.default_month5,
                       'ratio_month6'   : self.default_month6,
                       'ratio_month7'   : self.default_month7,
                       'ratio_month8'   : self.default_month8,
                       'ratio_month9'   : self.default_month9,
                       'ratio_month10'  : self.default_month10,
                       'ratio_month11'  : self.default_month11,
                       'ratio_month12'  : self.default_month12,
                       'category_ids'   : category_list,
                       'area'   : 'all',
                       })
            elif self.area == 'area' and self.area_id.name == 'BRT':
                channel_ids = self.env['res.users'].search([('active','=',True),('area_id.name','=','BRT')])
                for c in channel_ids:
                    self.env['lea.sales.target.salesman.sales'].sudo().create({
                       'reference'      : self.id,
                       'salesman_id'    : c.id,
                       'contribution'   : 100.00 / float(len(channel_ids)),
                       'ratio_month1'   : self.default_month1,
                       'ratio_month2'   : self.default_month2,
                       'ratio_month3'   : self.default_month3,
                       'ratio_month4'   : self.default_month4,
                       'ratio_month5'   : self.default_month5,
                       'ratio_month6'   : self.default_month6,
                       'ratio_month7'   : self.default_month7,
                       'ratio_month8'   : self.default_month8,
                       'ratio_month9'   : self.default_month9,
                       'ratio_month10'  : self.default_month10,
                       'ratio_month11'  : self.default_month11,
                       'ratio_month12'  : self.default_month12,
                       'category_ids'   : category_list,
                       'area'   : 'brt',
                       })
            elif self.area == 'area' and self.area_id.name == 'TMR':
                channel_ids = self.env['res.users'].search([('active','=',True),('area_id.name','=','TMR')])
                for c in channel_ids:
                    self.env['lea.sales.target.salesman.sales'].sudo().create({
                       'reference'      : self.id,
                       'salesman_id'    : c.id,
                       'contribution'   : 100.00 / float(len(channel_ids)),
                       'ratio_month1'   : self.default_month1,
                       'ratio_month2'   : self.default_month2,
                       'ratio_month3'   : self.default_month3,
                       'ratio_month4'   : self.default_month4,
                       'ratio_month5'   : self.default_month5,
                       'ratio_month6'   : self.default_month6,
                       'ratio_month7'   : self.default_month7,
                       'ratio_month8'   : self.default_month8,
                       'ratio_month9'   : self.default_month9,
                       'ratio_month10'  : self.default_month10,
                       'ratio_month11'  : self.default_month11,
                       'ratio_month12'  : self.default_month12,
                       'category_ids'   : category_list,
                       'area'   : 'tmr',
                       })
            elif self.area == 'area' and self.area_id.name == 'MDN':
                channel_ids = self.env['res.users'].search([('active','=',True),('area_id.name','=','MDN')])
                for c in channel_ids:
                    self.env['lea.sales.target.salesman.sales'].sudo().create({
                       'reference'      : self.id,
                       'salesman_id'    : c.id,
                       'contribution'   : 100.00 / float(len(channel_ids)),
                       'ratio_month1'   : self.default_month1,
                       'ratio_month2'   : self.default_month2,
                       'ratio_month3'   : self.default_month3,
                       'ratio_month4'   : self.default_month4,
                       'ratio_month5'   : self.default_month5,
                       'ratio_month6'   : self.default_month6,
                       'ratio_month7'   : self.default_month7,
                       'ratio_month8'   : self.default_month8,
                       'ratio_month9'   : self.default_month9,
                       'ratio_month10'  : self.default_month10,
                       'ratio_month11'  : self.default_month11,
                       'ratio_month12'  : self.default_month12,
                       'category_ids'   : category_list,
                       'area'   : 'mdn',
                       })
        else:
            raise Warning('Harap masukan nilai target terlebih dahulu !')

    @api.one
    def button_generate_qty(self):
        if self.qty_total_target > 0:

            if (self.qty_default_month1+self.qty_default_month2+self.qty_default_month3+self.qty_default_month4+self.qty_default_month5+self.qty_default_month6+self.qty_default_month7+self.qty_default_month8+self.qty_default_month9+self.qty_default_month10+self.qty_default_month11+self.qty_default_month12) != 1200:
                raise Warning('Pembagian default ration bulanan belum sesuai, harap sesuaikan jumlah menjadi 1.200% !')

            #clear existing data
            for c in self.qty_channel_ids:
                c.sudo().unlink()
            for brt in self.qty_brt_ids:
                brt.sudo().unlink()
            for tmr in self.qty_tmr_ids:
                tmr.sudo().unlink()
            for mdn in self.qty_mdn_ids:
                mdn.sudo().unlink()

            category_list = []
            category_ids = self.env['lea.product.moving.status'].search([])
            for p in category_ids:
                contribution = p.default_contribution
                if contribution == 0:
                    contribution = 100.00 / float(len(category_ids))

                category_list.append((0,0,{
                    'category_id'       : p.id,
                    'contribution'      : contribution,
                    'ratio_month1'      : self.qty_default_month1,
                    'ratio_month2'      : self.qty_default_month2,
                    'ratio_month3'      : self.qty_default_month3,
                    'ratio_month4'      : self.qty_default_month4,
                    'ratio_month5'      : self.qty_default_month5,
                    'ratio_month6'      : self.qty_default_month6,
                    'ratio_month7'      : self.qty_default_month7,
                    'ratio_month8'      : self.qty_default_month8,
                    'ratio_month9'      : self.qty_default_month9,
                    'ratio_month10'     : self.qty_default_month10,
                    'ratio_month11'     : self.qty_default_month11,
                    'ratio_month12'     : self.qty_default_month12,
                }))

            if self.qty_area == 'all':
                # channel_ids = self.env['stock.warehouse'].search([('wh_code','=like','LS_%')])
                channel_ids = self.env['res.users'].search([('active','=',True)])
                for c in channel_ids:
                    self.env['lea.sales.target.qty.salesman.sales'].sudo().create({
                       'reference'      : self.id,
                       'salesman_id'    : c.id,
                       'contribution'   : 100.00 / float(len(channel_ids)),
                       'ratio_month1'   : self.qty_default_month1,
                       'ratio_month2'   : self.qty_default_month2,
                       'ratio_month3'   : self.qty_default_month3,
                       'ratio_month4'   : self.qty_default_month4,
                       'ratio_month5'   : self.qty_default_month5,
                       'ratio_month6'   : self.qty_default_month6,
                       'ratio_month7'   : self.qty_default_month7,
                       'ratio_month8'   : self.qty_default_month8,
                       'ratio_month9'   : self.qty_default_month9,
                       'ratio_month10'  : self.qty_default_month10,
                       'ratio_month11'  : self.qty_default_month11,
                       'ratio_month12'  : self.qty_default_month12,
                       'category_ids'   : category_list,
                       'area'   : 'all',
                       })
            elif self.qty_area == 'area' and self.qty_area_id.name == 'BRT':
                channel_ids = self.env['res.users'].search([('active','=',True),('area_id.name','=','BRT')])
                for c in channel_ids:
                    self.env['lea.sales.target.qty.salesman.sales'].sudo().create({
                       'reference'      : self.id,
                       'salesman_id'    : c.id,
                       'contribution'   : 100.00 / float(len(channel_ids)),
                       'ratio_month1'   : self.qty_default_month1,
                       'ratio_month2'   : self.qty_default_month2,
                       'ratio_month3'   : self.qty_default_month3,
                       'ratio_month4'   : self.qty_default_month4,
                       'ratio_month5'   : self.qty_default_month5,
                       'ratio_month6'   : self.qty_default_month6,
                       'ratio_month7'   : self.qty_default_month7,
                       'ratio_month8'   : self.qty_default_month8,
                       'ratio_month9'   : self.qty_default_month9,
                       'ratio_month10'  : self.qty_default_month10,
                       'ratio_month11'  : self.qty_default_month11,
                       'ratio_month12'  : self.qty_default_month12,
                       'category_ids'   : category_list,
                       'area'   : 'brt',
                       })
            elif self.qty_area == 'area' and self.qty_area_id.name == 'TMR':
                channel_ids = self.env['res.users'].search([('active','=',True),('area_id.name','=','TMR')])
                for c in channel_ids:
                    self.env['lea.sales.target.qty.salesman.sales'].sudo().create({
                       'reference'      : self.id,
                       'salesman_id'    : c.id,
                       'contribution'   : 100.00 / float(len(channel_ids)),
                       'ratio_month1'   : self.qty_default_month1,
                       'ratio_month2'   : self.qty_default_month2,
                       'ratio_month3'   : self.qty_default_month3,
                       'ratio_month4'   : self.qty_default_month4,
                       'ratio_month5'   : self.qty_default_month5,
                       'ratio_month6'   : self.qty_default_month6,
                       'ratio_month7'   : self.qty_default_month7,
                       'ratio_month8'   : self.qty_default_month8,
                       'ratio_month9'   : self.qty_default_month9,
                       'ratio_month10'  : self.qty_default_month10,
                       'ratio_month11'  : self.qty_default_month11,
                       'ratio_month12'  : self.qty_default_month12,
                       'category_ids'   : category_list,
                       'area'   : 'tmr',
                       })
            elif self.qty_area == 'area' and self.qty_area_id.name == 'MDN':
                channel_ids = self.env['res.users'].search([('active','=',True),('area_id.name','=','MDN')])
                for c in channel_ids:
                    self.env['lea.sales.target.qty.salesman.sales'].sudo().create({
                       'reference'      : self.id,
                       'salesman_id'    : c.id,
                       'contribution'   : 100.00 / float(len(channel_ids)),
                       'ratio_month1'   : self.qty_default_month1,
                       'ratio_month2'   : self.qty_default_month2,
                       'ratio_month3'   : self.qty_default_month3,
                       'ratio_month4'   : self.qty_default_month4,
                       'ratio_month5'   : self.qty_default_month5,
                       'ratio_month6'   : self.qty_default_month6,
                       'ratio_month7'   : self.qty_default_month7,
                       'ratio_month8'   : self.qty_default_month8,
                       'ratio_month9'   : self.qty_default_month9,
                       'ratio_month10'  : self.qty_default_month10,
                       'ratio_month11'  : self.qty_default_month11,
                       'ratio_month12'  : self.qty_default_month12,
                       'category_ids'   : category_list,
                       'area'   : 'mdn',
                       })
        else:
            raise Warning('Harap masukan nilai target terlebih dahulu !')


#TARGET BY VALUE
class LeaSalesTargetSalesmanSales(models.Model):
    _name = 'lea.sales.target.salesman.sales'
    _rec_name = 'salesman_id'
            
    @api.depends('contribution','reference.total_target')
    def compute_contribution_value(self):
        for rec in self:
            if rec.contribution > 0:
                rec.contribution_value = float(rec.contribution) / 100.00 * rec.reference.total_target

    @api.depends('contribution_value')
    def compute_avg_target(self):
        for rec in self:
            if rec.contribution_value > 0:
                rec.avg_target = float(rec.contribution_value) / 12.00

    def lock_default_target_ratio(self):
        if (self.ratio_month1+self.ratio_month2+self.ratio_month3+self.ratio_month4+self.ratio_month5+self.ratio_month6+self.ratio_month7+self.ratio_month8+self.ratio_month9+self.ratio_month10+self.ratio_month11+self.ratio_month12) != 1200:
            raise Warning('Pembagian default ratio bulanan belum sesuai, harap sesuaikan jumlah menjadi 1.200% ! ' + 'Salesman : ' + self.salesman_id.name)

    @api.multi
    def write(self, vals):
        res = super(LeaSalesTargetSalesmanSales, self).write(vals)
        self.lock_default_target_ratio()
        return res


    reference               = fields.Many2one(comodel_name='lea.sales.target.salesman',string='Target ID', ondelete="cascade" )
    contribution            = fields.Float('Contribution (%)')
    contribution_value      = fields.Float('Contribution (Rp.)', compute='compute_contribution_value', store=True)
    avg_target              = fields.Float('Avg. Target/Month', compute='compute_avg_target', store=True)
    # store_id                = fields.Many2one(comodel_name='stock.warehouse',string='Channel')
    salesman_id             = fields.Many2one(comodel_name='res.users',string='Salesman')
    ratio_month1            = fields.Float('January', default=100)
    ratio_month2            = fields.Float('February', default=100)
    ratio_month3            = fields.Float('March', default=100)
    ratio_month4            = fields.Float('April', default=100)
    ratio_month5            = fields.Float('May', default=100)
    ratio_month6            = fields.Float('June', default=100)
    ratio_month7            = fields.Float('July', default=100)
    ratio_month8            = fields.Float('August', default=100)
    ratio_month9            = fields.Float('September', default=100)
    ratio_month10           = fields.Float('October', default=100)
    ratio_month11           = fields.Float('November', default=100)
    ratio_month12           = fields.Float('December', default=100)
    category_ids            = fields.One2many(comodel_name='lea.sales.target.salesman.sales.category',inverse_name='reference',string='Category')
    area = fields.Selection([('all','All'),('brt','BRT'),('tmr','TMR'),('mdn','MDN')], "Area")


class LeaSalesTargetSalesmanSalesCategory(models.Model):
    _name = 'lea.sales.target.salesman.sales.category'
    _rec_name = 'category_id'
         
    @api.depends('contribution','reference.contribution','reference.contribution_value','reference.reference.total_target')
    def compute_contribution_value(self):
        for rec in self:
            if rec.contribution > 0:
                rec.contribution_value = float(rec.contribution) / 100.00 * rec.reference.contribution_value

    @api.depends('contribution','ratio_month1','ratio_month2','ratio_month3','ratio_month4','ratio_month5','ratio_month6','ratio_month7','ratio_month8','ratio_month9','ratio_month10','ratio_month11','ratio_month12')
    def compute_ratio(self):
        for rec in self:
            if rec.contribution > 0:
                if rec.ratio_month1 > 0:
                    rec.value_month1 = (rec.contribution_value / 12.00) * (float(rec.ratio_month1) / 100.00)
                if rec.ratio_month2 > 0:
                    rec.value_month2 = (rec.contribution_value / 12.00) * (float(rec.ratio_month2) / 100.00)
                if rec.ratio_month3 > 0:
                    rec.value_month3 = (rec.contribution_value / 12.00) * (float(rec.ratio_month3) / 100.00)
                if rec.ratio_month4 > 0:
                    rec.value_month4 = (rec.contribution_value / 12.00) * (float(rec.ratio_month4) / 100.00)
                if rec.ratio_month5 > 0:
                    rec.value_month5 = (rec.contribution_value / 12.00) * (float(rec.ratio_month5) / 100.00)
                if rec.ratio_month6 > 0:
                    rec.value_month6 = (rec.contribution_value / 12.00) * (float(rec.ratio_month6) / 100.00)
                if rec.ratio_month7 > 0:
                    rec.value_month7 = (rec.contribution_value / 12.00) * (float(rec.ratio_month7) / 100.00)
                if rec.ratio_month8 > 0:
                    rec.value_month8 = (rec.contribution_value / 12.00) * (float(rec.ratio_month8) / 100.00)
                if rec.ratio_month9 > 0:
                    rec.value_month9 = (rec.contribution_value / 12.00) * (float(rec.ratio_month9) / 100.00)
                if rec.ratio_month10 > 0:
                    rec.value_month10 = (rec.contribution_value / 12.00) * (float(rec.ratio_month10) / 100.00)
                if rec.ratio_month11 > 0:
                    rec.value_month11 = (rec.contribution_value / 12.00) * (float(rec.ratio_month11) / 100.00)
                if rec.ratio_month12 > 0:
                    rec.value_month12 = (rec.contribution_value / 12.00) * (float(rec.ratio_month12) / 100.00)

    def lock_default_target_ratio(self):
        if (self.ratio_month1+self.ratio_month2+self.ratio_month3+self.ratio_month4+self.ratio_month5+self.ratio_month6+self.ratio_month7+self.ratio_month8+self.ratio_month9+self.ratio_month10+self.ratio_month11+self.ratio_month12) != 1200:
            raise Warning('Pembagian default ratio bulanan belum sesuai, harap sesuaikan jumlah menjadi 1.200% ! ' + 'Salesman : ' + self.reference.salesman_id.name + ', ' + 'Category : ' + self.category_id.name)

    @api.multi
    def write(self, vals):
        res = super(LeaSalesTargetSalesmanSalesCategory, self).write(vals)
        self.lock_default_target_ratio()
        return res

    reference               = fields.Many2one(comodel_name='lea.sales.target.salesman.sales',string='Channel ID', ondelete="cascade" )
    category_id             = fields.Many2one(comodel_name='lea.product.moving.status',string='Category')
    contribution            = fields.Float('Contribution (%)')
    contribution_value      = fields.Float('Contribution (Rp.)', compute='compute_contribution_value', store=True)
    ratio_month1            = fields.Float('January', default=100)
    ratio_month2            = fields.Float('February', default=100)
    ratio_month3            = fields.Float('March', default=100)
    ratio_month4            = fields.Float('April', default=100)
    ratio_month5            = fields.Float('May', default=100)
    ratio_month6            = fields.Float('June', default=100)
    ratio_month7            = fields.Float('July', default=100)
    ratio_month8            = fields.Float('August', default=100)
    ratio_month9            = fields.Float('September', default=100)
    ratio_month10           = fields.Float('October', default=100)
    ratio_month11           = fields.Float('November', default=100)
    ratio_month12           = fields.Float('December', default=100)

    value_month1            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month2            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month3            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month4            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month5            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month6            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month7            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month8            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month9            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month10           = fields.Float('Value', compute='compute_ratio', store=True)
    value_month11           = fields.Float('Value', compute='compute_ratio', store=True)
    value_month12           = fields.Float('Value', compute='compute_ratio', store=True)
    
#TARGET BY QTY
class LeaSalesTargetQtySalesmanSales(models.Model):
    _name = 'lea.sales.target.qty.salesman.sales'
    _rec_name = 'salesman_id'
            
    @api.depends('contribution','reference.qty_total_target')
    def compute_contribution_value(self):
        for rec in self:
            if rec.contribution > 0:
                rec.contribution_value = float(rec.contribution) / 100.00 * rec.reference.qty_total_target

    @api.depends('contribution_value')
    def compute_avg_target(self):
        for rec in self:
            if rec.contribution_value > 0:
                rec.avg_target = float(rec.contribution_value) / 12.00

    def lock_default_target_ratio(self):
        if (self.ratio_month1+self.ratio_month2+self.ratio_month3+self.ratio_month4+self.ratio_month5+self.ratio_month6+self.ratio_month7+self.ratio_month8+self.ratio_month9+self.ratio_month10+self.ratio_month11+self.ratio_month12) != 1200:
            raise Warning('Pembagian default ratio bulanan belum sesuai, harap sesuaikan jumlah menjadi 1.200% ! ' + 'Salesman : ' + self.salesman_id.name)

    @api.multi
    def write(self, vals):
        res = super(LeaSalesTargetQtySalesmanSales, self).write(vals)
        self.lock_default_target_ratio()
        return res


    reference               = fields.Many2one(comodel_name='lea.sales.target.salesman',string='Target ID', ondelete="cascade" )
    contribution            = fields.Float('Contribution (%)')
    contribution_value      = fields.Float('Contribution (Rp.)', compute='compute_contribution_value', store=True)
    avg_target              = fields.Float('Avg. Target/Month', compute='compute_avg_target', store=True)
    # store_id                = fields.Many2one(comodel_name='stock.warehouse',string='Channel')
    salesman_id             = fields.Many2one(comodel_name='res.users',string='Salesman')
    ratio_month1            = fields.Float('January', default=100)
    ratio_month2            = fields.Float('February', default=100)
    ratio_month3            = fields.Float('March', default=100)
    ratio_month4            = fields.Float('April', default=100)
    ratio_month5            = fields.Float('May', default=100)
    ratio_month6            = fields.Float('June', default=100)
    ratio_month7            = fields.Float('July', default=100)
    ratio_month8            = fields.Float('August', default=100)
    ratio_month9            = fields.Float('September', default=100)
    ratio_month10           = fields.Float('October', default=100)
    ratio_month11           = fields.Float('November', default=100)
    ratio_month12           = fields.Float('December', default=100)
    category_ids            = fields.One2many(comodel_name='lea.sales.target.qty.salesman.sales.category',inverse_name='reference',string='Category')
    area = fields.Selection([('all','All'),('brt','BRT'),('tmr','TMR'),('mdn','MDN')], "Area")


class LeaSalesTargetQtySalesmanSalesCategory(models.Model):
    _name = 'lea.sales.target.qty.salesman.sales.category'
    _rec_name = 'category_id'
         
    @api.depends('contribution','reference.contribution','reference.contribution_value','reference.reference.qty_total_target')
    def compute_contribution_value(self):
        for rec in self:
            if rec.contribution > 0:
                rec.contribution_value = float(rec.contribution) / 100.00 * rec.reference.contribution_value

    @api.depends('ratio_month1','ratio_month2','ratio_month3','ratio_month4','ratio_month5','ratio_month6','ratio_month7','ratio_month8','ratio_month9','ratio_month10','ratio_month11','ratio_month12')
    def compute_ratio(self):
        for rec in self:
            if rec.contribution > 0:
                if rec.ratio_month1 > 0:
                    rec.value_month1 = (rec.contribution_value / 12.00) * (float(rec.ratio_month1) / 100.00)
                if rec.ratio_month2 > 0:
                    rec.value_month2 = (rec.contribution_value / 12.00) * (float(rec.ratio_month2) / 100.00)
                if rec.ratio_month3 > 0:
                    rec.value_month3 = (rec.contribution_value / 12.00) * (float(rec.ratio_month3) / 100.00)
                if rec.ratio_month4 > 0:
                    rec.value_month4 = (rec.contribution_value / 12.00) * (float(rec.ratio_month4) / 100.00)
                if rec.ratio_month5 > 0:
                    rec.value_month5 = (rec.contribution_value / 12.00) * (float(rec.ratio_month5) / 100.00)
                if rec.ratio_month6 > 0:
                    rec.value_month6 = (rec.contribution_value / 12.00) * (float(rec.ratio_month6) / 100.00)
                if rec.ratio_month7 > 0:
                    rec.value_month7 = (rec.contribution_value / 12.00) * (float(rec.ratio_month7) / 100.00)
                if rec.ratio_month8 > 0:
                    rec.value_month8 = (rec.contribution_value / 12.00) * (float(rec.ratio_month8) / 100.00)
                if rec.ratio_month9 > 0:
                    rec.value_month9 = (rec.contribution_value / 12.00) * (float(rec.ratio_month9) / 100.00)
                if rec.ratio_month10 > 0:
                    rec.value_month10 = (rec.contribution_value / 12.00) * (float(rec.ratio_month10) / 100.00)
                if rec.ratio_month11 > 0:
                    rec.value_month11 = (rec.contribution_value / 12.00) * (float(rec.ratio_month11) / 100.00)
                if rec.ratio_month12 > 0:
                    rec.value_month12 = (rec.contribution_value / 12.00) * (float(rec.ratio_month12) / 100.00)

    def lock_default_target_ratio(self):
        if (self.ratio_month1+self.ratio_month2+self.ratio_month3+self.ratio_month4+self.ratio_month5+self.ratio_month6+self.ratio_month7+self.ratio_month8+self.ratio_month9+self.ratio_month10+self.ratio_month11+self.ratio_month12) != 1200:
            raise Warning('Pembagian default ratio bulanan belum sesuai, harap sesuaikan jumlah menjadi 1.200% ! ' + 'Salesman : ' + self.reference.salesman_id.name + ', ' + 'Category : ' + self.category_id.name)

    @api.multi
    def write(self, vals):
        res = super(LeaSalesTargetQtySalesmanSalesCategory, self).write(vals)
        self.lock_default_target_ratio()
        return res

    reference               = fields.Many2one(comodel_name='lea.sales.target.qty.salesman.sales',string='Channel ID', ondelete="cascade" )
    category_id             = fields.Many2one(comodel_name='lea.product.moving.status',string='Category')
    contribution            = fields.Float('Contribution (%)')
    contribution_value      = fields.Float('Contribution (Rp.)', compute='compute_contribution_value', store=True)
    ratio_month1            = fields.Float('January', default=100)
    ratio_month2            = fields.Float('February', default=100)
    ratio_month3            = fields.Float('March', default=100)
    ratio_month4            = fields.Float('April', default=100)
    ratio_month5            = fields.Float('May', default=100)
    ratio_month6            = fields.Float('June', default=100)
    ratio_month7            = fields.Float('July', default=100)
    ratio_month8            = fields.Float('August', default=100)
    ratio_month9            = fields.Float('September', default=100)
    ratio_month10           = fields.Float('October', default=100)
    ratio_month11           = fields.Float('November', default=100)
    ratio_month12           = fields.Float('December', default=100)

    value_month1            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month2            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month3            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month4            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month5            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month6            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month7            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month8            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month9            = fields.Float('Value', compute='compute_ratio', store=True)
    value_month10           = fields.Float('Value', compute='compute_ratio', store=True)
    value_month11           = fields.Float('Value', compute='compute_ratio', store=True)
    value_month12           = fields.Float('Value', compute='compute_ratio', store=True)
    
