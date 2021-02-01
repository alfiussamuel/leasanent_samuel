from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class stock_quant(models.Model):

    _inherit = "stock.quant"


    def get_current_qty_available(self, product_id, stock_location_id):
        qty_available = 0
        quants = self.search([('product_id', '=', product_id), ('location_id', '=', stock_location_id)])
        for quant in quants:
            qty_available += quant.qty
        return {
            'stock_location_id': stock_location_id,
            'qty_available': qty_available,
            'product_id': product_id
        }

    @api.model
    def create(self, vals):
        res = super(stock_quant, self).create(vals)
        self.sync_pos(vals['product_id'])
        return res

    @api.multi
    def write(self, vals):
        res = super(stock_quant, self).write(vals)
        for record in self:
            self.sync_pos(record.product_id.id)
        return res

    def sync_pos(self, product_id):
        sql = "select stock_location_id from pos_config"
        self.env.cr.execute(sql)
        stock_location_ids = self.env.cr.fetchall()
        for stock_location_id in stock_location_ids:
            result = self.get_current_qty_available(product_id, stock_location_id[0])
            notifications = [[(self._cr.dbname, 'pos.stock.update', 101), result]]
            _logger.info('send notification update stock')
        self.env['bus.bus'].sendmany(notifications)

    # def sync_pos(self, product_id):
    #     sql = "select stock_location_id from pos_config"
    #     self.env.cr.execute(sql)
    #     stock_location_ids = self.env.cr.fetchall()
    #     notifications = []
    #     for stock_location_id in stock_location_ids:
    #         result = self.get_current_qty_available(product_id, stock_location_id[0])
    #         notifications.append([(self._cr.dbname, 'pos.stock.update', 101), result])
    #     self.env['bus.bus'].sendmany(notifications)
