# coding: utf-8
from datetime import datetime
from odoo import models, fields, api


class PosSaleOutletReport(models.TransientModel):
    _name = "pos.sale.outlet.report"
    _description = "POS Sales Outlet Report"

    start_date              = fields.Date('Start Date', required=True, default=fields.Date.today())
    end_date                = fields.Date('End Date', required=True, default=fields.Date.today())
    outlet_ids              = fields.Many2many('pos.config',string='Outlet(s)', required=True)
    print_by_sales          = fields.Boolean('Print by Salesman(s)')
    salesman_ids            = fields.Many2many('res.users',string='Salesman(s)', required=False)

    @api.multi
    def print_report(self):
        outlet_ids = []
        for o in self.outlet_ids:
            outlet_ids.append(o.id)
            
        salesman_ids = []
        for s in self.salesman_ids:
            salesman_ids.append(s.id)

        data = {
            'start_date'        : self.start_date,
            'end_date'          : self.end_date,
            'outlet_ids'        : outlet_ids,
            'print_by_sales'    : self.print_by_sales,
            'salesman_ids'      : salesman_ids,
        }
        return self.env['report'].get_action([], 'v10_lea.report_pos_sale_outlet',data=data)