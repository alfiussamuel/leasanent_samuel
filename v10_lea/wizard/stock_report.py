# coding: utf-8
from datetime import datetime
from odoo import models, fields, api


class StockReportWizard(models.TransientModel):
    _name = "stock.report.wizard"
    _description = "Stock Report Wizard"

    location_id       = fields.Many2one('stock.location',string='Location',ondelete='cascade')
    product_category3_id       = fields.Many2one('lea.product.category3',string='Category',ondelete='cascade')    

    @api.multi
    def generate_stock_report(self):
        report_obj = self.env['report']
        template = 'v10_lea.stock_report'
        report = report_obj._get_report_from_name(template)
        domain = {
            'location_id': self.location_id.id,
            'product_category3_id': self.product_category3_id.id,
            'location_name': self.location_id.name,            
        }
        values = {
            'ids' : self.ids,
            'model' : report.model,
            'form': domain
        }
        return report_obj.get_action(self, template, data=values)
