from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from dateutil.relativedelta import relativedelta
import datetime
import time
from datetime import datetime
import odoo.addons.decimal_precision as dp


class product_template(models.Model):
	_inherit = 'product.template'


	default_location = fields.Many2one("stock.location", "Location")