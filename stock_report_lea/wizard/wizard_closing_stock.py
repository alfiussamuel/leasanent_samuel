import base64
from cStringIO import StringIO
from odoo import api, fields, models
import xlsxwriter
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class wizard_closing_stock(models.TransientModel):
    _name = 'wizard.closing.stock'

    @api.model
    def _default_company(self):
        user = self.env['res.users'].browse(self.env.uid)
        return user.company_id.id

    product_id2      = fields.Many2many('product.product', 'Product')
    period_id        = fields.Many2one('account.period', 'Period')
    location_id      = fields.Many2one('stock.location', 'Location')
    company_id       = fields.Many2one('res.company', 'Company', default=_default_company)


