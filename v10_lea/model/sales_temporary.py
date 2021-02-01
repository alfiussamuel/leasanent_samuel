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

class LeaSalesSummary(models.Model):
    _name = 'lea.sales.summary'

    year                    = fields.Char('Year', default='2019')
    state                   = fields.Selection(STATE, 'State', default='draft')
    warehouse_id            = fields.Many2one(comodel_name='stock.warehouse',string='Warehouse', required=True)
    product_id              = fields.Many2one(comodel_name='product.template',string='Product')
    total_qty_1             = fields.Integer(string='Jan')
    total_qty_2             = fields.Integer(string='Feb')
    total_qty_3             = fields.Integer(string='March')
    total_qty_4             = fields.Integer(string='April')
    total_qty_5             = fields.Integer(string='May')
    total_qty_6             = fields.Integer(string='June')
    total_qty_7             = fields.Integer(string='July')
    total_qty_8             = fields.Integer(string='Aug')
    total_qty_9             = fields.Integer(string='Sep')
    total_qty_10             = fields.Integer(string='Oct')
    total_qty_11             = fields.Integer(string='Nov')
    total_qty_12             = fields.Integer(string='Dec')
    total_sales             = fields.Integer(string='Total Sales', compute='compute_total', store=True)

    @api.depends('total_qty_1','total_qty_2','total_qty_3','total_qty_4','total_qty_5','total_qty_6','total_qty_7','total_qty_8','total_qty_9','total_qty_10','total_qty_11','total_qty_12')
    def compute_total(self):
        for rec in self:
            rec.total_sales = rec.total_qty_1 + rec.total_qty_2 + rec.total_qty_3 + rec.total_qty_4 + rec.total_qty_5 + rec.total_qty_6 + rec.total_qty_7 + rec.total_qty_8 + rec.total_qty_9 + rec.total_qty_10 + rec.total_qty_11 + rec.total_qty_12
