# coding: utf-8
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning

CHANNEL = [
    ('store','Store'),
    ('consignment','Consignment'),
    ('toko_putus','Toko Putus'),
    ('corporate','Corporate')
]

GRADE = [
    ('A','A'),
    ('B','B'),
    ('C','C'),
    ('D','D'),
]


class WizardSummarySalesPerformanceClass(models.TransientModel):
    _name = "wizard.summary.sales.performance.class"
    _description = "Summary Sales Performance per Class"

    @api.onchange('channel_id')
    def onchange_channel_id(self):
        area_list = []
        if self.channel_id:
            wh_ids = False
            subarea_list = []
            if self.channel_id == 'store':
                wh_ids = self.env['stock.warehouse'].sudo().search([('wh_code','=like','LS_%')])
            elif self.channel_id == 'consignment':
                wh_ids = self.env['stock.warehouse'].sudo().search([('wh_code','=like','LC_%')])
            elif self.channel_id == 'toko_putus':
                wh_ids = self.env['stock.warehouse'].sudo().search([('wh_code','=like','TP_%')])
            elif self.channel_id == 'corporate':
                wh_ids = self.env['stock.warehouse'].sudo().search([('wh_code','=like','CP_%')])
            
            if wh_ids:
                for w in wh_ids:
                    if w.wh_area_id.id not in area_list:
                        area_list.append(w.wh_area_id.id)

        domain = {'area_id': [('id', 'in', area_list)]} 
        return {'domain':domain}

    @api.onchange('area_id')
    def onchange_area_id(self):
        if self.area_id:
            domain = {'subarea_id': [('area_id.id', '=', self.area_id.id)]} 
            return {'domain':domain}

    start_date              = fields.Date('Start Date', required=True, default=fields.Date.today())
    end_date                = fields.Date('End Date', required=True, default=fields.Date.today())
    channel_id              = fields.Selection(CHANNEL, string='Channel', required=True)
    area_id                 = fields.Many2one('lea.area', string='Area')
    subarea_id              = fields.Many2one('lea.sub.area', string='Sub-Area')
    grade                   = fields.Selection(GRADE, string='Grade')

    @api.multi
    def print_report(self):
        #year checking (must same)
        start_date = fields.Date.from_string(self.start_date)
        end_date = fields.Date.from_string(self.end_date)
        
        if start_date.year != end_date.year:
            raise Warning('Periode cetak harus dalam tahun yang sama !')

        data = {
            'start_date'        : self.start_date,
            'end_date'          : self.end_date,
            'area_id'           : self.area_id.id or False,
            'subarea_id'        : self.subarea_id.id or False,
            'channel_id'        : self.channel_id,
            'grade'             : self.grade,
        }
        return self.env['report'].get_action([], 'v10_lea.report_summary_sales_performance_class',data=data)