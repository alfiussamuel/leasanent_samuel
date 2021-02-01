# -*- coding: utf-8 -*-
from odoo import api,fields,models,_
from odoo.exceptions import UserError, RedirectWarning, ValidationError, except_orm, Warning
import odoorpc
import time

class Partner(models.Model):
    _inherit = "res.partner"

    #group_id = fields.Many2one('res.partner', 'Group')
    sales_head_id = fields.Many2one('res.users', 'Sales Head')
