from odoo.http import request
from odoo import http
import logging
import json
from odoo.addons.bus.controllers.main import BusController

_logger = logging.getLogger(__name__)

class Bus(BusController):

    def _poll(self, dbname, channels, last, options):
        channels.append((request.db, 'pos.stock.update', 101))
        return super(Bus, self)._poll(dbname, channels, last, options)

    @http.route(['/pos/get/stock'], type='json', auth="user", website=True)
    def bus_update_data(self, values):
        product_datas = []
        product_ids = values['product_ids']
        location_id = values['location_id']
        for product_id in product_ids:
            qty_available = 0
            quants = request.env['stock.quant'].search([('product_id', '=', product_id), ('location_id', '=', location_id)])
            for quant in quants:
                qty_available += quant.qty
            val = {
                'product_id': product_id,
                'qty_available': qty_available,
            }
            product_datas.append(val)
        return json.dumps(product_datas)



