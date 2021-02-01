from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta


class report_summary_sales_performance_channel(models.AbstractModel):

    _name = 'report.v10_lea.report_summary_sales_performance_channel'

    @api.model
    def get_detail(self, start_date=False, end_date=False, area_id=False, subarea_id=False, class_category_id=False, channel_id_store=False, channel_id_consignment=False, channel_id_toko_putus=False, channel_id_corporate=False):
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

        wh_type_list = []
        if channel_id_store:
            wh_type_list.append('LS')
        if channel_id_consignment:
            wh_type_list.append('LC')
        if channel_id_toko_putus:
            wh_type_list.append('TP')
        if channel_id_corporate:
            wh_type_list.append('CP')
        
        domain = [('wh_type','in',wh_type_list)]
        
        if area_id:
            domain += [('wh_area_id.id', '=', area_id)]

        if subarea_id:
            domain += [('wh_subarea_id.id', '=', subarea_id)]

        warehouse_ids = self.env['stock.warehouse'].sudo().search(domain)

        for wh in warehouse_ids:

            total_qty = 0
            total_value = 0
            percentage = 0

            class_category_list = []
            for c in class_category_id:
                target = self.get_target_value(wh, d1, d2, c)

                class_ids = self.env['lea.product.moving.status'].sudo().search([('id','=',c)])

                pos_order_line_ids = self.env['pos.order.line'].sudo().search([
                    ('order_id.config_id.stock_location_id.id','=',wh.lot_stock_id.id),
                    ('product_id.product_moving_status_id','=',c),
                    ('order_id.date_order','>=',date_start_convert),
                    ('order_id.date_order','<=',date_stop_convert),
                    ('order_id.state','in',['paid','done','invoiced','credited']),
                    ])

                qty = sum(l.qty for l in pos_order_line_ids)
                value = sum(l.price_subtotal_incl for l in pos_order_line_ids)

                if target == 0:
                    target = value

                if target != 0:
                    percentage = (float(value) / float(target)) * 100.00

                class_category_list.append({
                        'name'          : class_ids.name,
                        'total_qty'     : qty,
                        'total_value'   : value,
                        'percentage'    : percentage,
                    })

                total_qty += qty
                total_value += value
                percentage += percentage

            percentage = float(percentage / len(class_category_id))

            data.append({
                'channel'               : wh.name,
                'class_category_line'   : class_category_list,
                'total_qty'             : total_qty,
                'total_value'           : total_value,
                'percentage'            : percentage,
                })
        
        class_list = self.env['lea.product.moving.status'].sudo().search([('id','in',class_category_id)])

        l_channel_category = ''
        for c in class_list:
            if l_channel_category == '':
                l_channel_category = c.name
            else:
                l_channel_category += ', ' + c.name

        return{
            'channel_ids'           : data,
            'class_ids'             : class_list,
            'start_date'            : date_start_convert[:10],
            'end_date'              : date_stop_convert[:10],
            'area'                  : self.env['lea.area'].sudo().search([('id','=',area_id)],limit=1).name if area_id else 'All',
            'subarea'               : self.env['lea.sub.area'].sudo().search([('id','=',subarea_id)],limit=1).name if subarea_id else 'All',
            'channel_category'      : l_channel_category,
            'print_info'            : str(datetime.now())[:19] + ' by ' + self.env.user.name,
            }  

    def get_target_value(self, wh, d1, d2, categ_id):
        target = 0
        target_ids = self.env['lea.sales.target.store.channel.category'].sudo().search([
            ('reference.store_id.id','=',wh.id),
            ('reference.reference.year','=',str(d1.year)),
            ('category_id.id','=',categ_id),
            ],limit=1)
        
        if not target_ids or target_ids == 0:
            target = 0
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

        return target


    @api.multi
    def render_html(self, docids, data=None):
        data = dict(data or {})        
        data.update(self.get_detail(
            data['start_date'],
            data['end_date'],
            data['area_id'],
            data['subarea_id'],
            data['class_category_id'],
            data['channel_id_store'],
            data['channel_id_consignment'],
            data['channel_id_toko_putus'],
            data['channel_id_corporate'],
            ))
        return self.env['report'].render('v10_lea.report_summary_sales_performance_channel', data)

