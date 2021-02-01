from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta


class report_summary_sales_performance_class(models.AbstractModel):

    _name = 'report.v10_lea.report_summary_sales_performance_class'

    @api.model
    def get_detail(self, start_date=False, end_date=False, area_id=False, subarea_id=False, channel_id=False, grade=False):
        data = []

        if start_date:
            start_date = fields.Date.from_string(start_date)
        else:
            # start by default today 00:00:00
            start_date = today

        if end_date:
            # set time to 23:59:59
            end_date = fields.Date.from_string(end_date)
        else:
            # stop by default today 23:59:59
            end_date = today + timedelta(days=1, seconds=-1)

        # avoid a date_stop smaller than date_start
        end_date = max(end_date, start_date)

        date_start = fields.Date.to_string(start_date)
        date_stop = fields.Date.to_string(end_date)
        date_start_convert = datetime.strptime(date_start + " 00:00:00", '%Y-%m-%d %H:%M:%S') - timedelta(hours=7)
        date_stop_convert = datetime.strptime(date_stop + " 23:59:59", '%Y-%m-%d %H:%M:%S') - timedelta(hours=7)
        date_start_convert = date_start_convert.strftime("%Y-%m-%d %H:%M:%S")
        date_stop_convert = date_stop_convert.strftime("%Y-%m-%d %H:%M:%S")

        #for get target
        d1 = datetime.strptime(date_start, '%Y-%m-%d')
        d2 = datetime.strptime(date_stop, '%Y-%m-%d')

        data = []
        domain = []

        if channel_id == 'store':
            domain += [('wh_code','=like','LS_%')]
        elif channel_id == 'consigment':
            domain += [('wh_code','=like','LC_%')]
        elif channel_id == 'toko_putus':
            domain += [('wh_code','=like','TP_%')]
        elif channel_id == 'corporate':
            domain += [('wh_code','=like','CP_%')]
        
        if area_id:
            domain += [('wh_area_id.id', '=', area_id.id)]

        if subarea_id:
            domain += [('wh_subarea_id.id', '=', subarea_id.id)]

        if grade:
            domain += [('wh)grade', '=', grade)]

        warehouse_ids = self.env['stock.warehouse'].sudo().search(domain)

        data = []
        for wh in warehouse_ids:
            pos_order_ids = self.env['pos.order'].sudo().search([
                ('config_id.stock_location_id.id','=',wh.lot_stock_id.id),
                ('date_order','>=',date_start_convert),
                ('date_order','<=',date_stop_convert),
                ('state','in',['paid','done','invoiced','credited']),
                ])

            pos_order_line_ids = self.env['pos.order.line'].sudo().search([
                ('order_id.config_id.stock_location_id.id','=',wh.lot_stock_id.id),
                ('order_id.date_order','>=',date_start_convert),
                ('order_id.date_order','<=',date_stop_convert),
                ('order_id.state','in',['paid','done','invoiced','credited']),
                ])

            target = 0
            realisasi = sum(line.amount_total for line in pos_order_ids)
            target_ids = self.env['lea.sales.target.store.channel'].sudo().search([
                ('store_id.id','=',wh.id),
                ('reference.year','=',str(d1.year)),
                ],limit=1)
            
            if not target_ids or target_ids == 0:
                target = realisasi
            else:
                for m in range(d1.month, d2.month+1):
                    if m == 1:
                        target += (float(target_ids.ratio_month1) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 2:
                        target += (float(target_ids.ratio_month2) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 3:
                        target += (float(target_ids.ratio_month3) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 4:
                        target += (float(target_ids.ratio_month4) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 5:
                        target += (float(target_ids.ratio_month5) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 6:
                        target += (float(target_ids.ratio_month6) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 7:
                        target += (float(target_ids.ratio_month7) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 8:
                        target += (float(target_ids.ratio_month8) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 9:
                        target += (float(target_ids.ratio_month9) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 10:
                        target += (float(target_ids.ratio_month10) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 11:
                        target += (float(target_ids.ratio_month11) / 100.00) * (target_ids.contribution_value / 12.00)
                    elif m == 12:
                        target += (float(target_ids.ratio_month12) / 100.00) * (target_ids.contribution_value / 12.00)

            data.append({
                'channel'                       : wh.name,
                'total_qty'                     : sum(line.qty for line in pos_order_line_ids),
                'total_sales_value'             : sum(line.amount_total for line in pos_order_ids),
                'total_target_sales_value'      : float(target),
                'achieve'                       : (float(realisasi) / float(target)) * 100.00,
                })

        return{
            'channel_ids'     : data,
            # 'start_date'    : start_date,
            }  

    @api.multi
    def render_html(self, docids, data=None):
        data = dict(data or {})        
        data.update(self.get_detail(data['start_date'],data['end_date'],data['area_id'],data['subarea_id'],data['channel_id'],data['grade']))
        return self.env['report'].render('v10_lea.report_summary_sales_performance_class', data)
