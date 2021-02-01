from odoo import api, models


class PosReceiptReport(models.AbstractModel):
    # _name = 'report.pos_orders_reprint.report_receipt'
    _name = 'report.pos_order_operations.report_receipt'

    @api.model
    def render_html(self, docids, data=None):
        Report = self.env['report']
        # return Report.sudo().render('pos_orders_reprint.report_receipt', {'docs': self.env['pos.order'].sudo().browse(docids)})
        return Report.sudo().render('pos_order_operations.report_receipt', {'docs': self.env['pos.order'].sudo().browse(docids)})