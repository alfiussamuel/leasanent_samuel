# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import fields, models,tools,api

class pos_config(models.Model):
    _inherit = 'pos.config' 

    defaut_customer = fields.Many2one("res.partner",string="Default Customer", domain=[('customer','=',True)])
