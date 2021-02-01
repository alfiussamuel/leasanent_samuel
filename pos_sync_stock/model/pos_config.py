from odoo import api, fields, models

class pos_config(models.Model):

    _inherit = "pos.config"

    display_onhand = fields.Boolean('Display Qty on hand', default=1, help='Display quantity on hand all products to pos screen')
    allow_order_out_of_stock = fields.Boolean('Allow order when out-of-stock', default=1)
    allow_syncing_stock = fields.Boolean('Syncing Backend', help="When field is checked, backend change product's quantity of stock location, will syncing to pos screen", default=1)