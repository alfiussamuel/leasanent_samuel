from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta


class report_summary_sales_performance_comparison(models.AbstractModel):

    _name = 'report.v10_lea.report_summary_sales_performance_comparison'

    @api.model
    def get_detail(self, start_date=False, end_date=False, area_id=False, subarea_id=False, channel_id_store=False, channel_id_consignment=False, channel_id_toko_putus=False, channel_id_corporate=False):
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
        product_class_ids = self.env['lea.product.class.category'].sudo().search([])
       
        #SUMMARY GRAND TOTAL
        gt_qty_current  = 0
        gt_value_current = 0
        gt_qty_before = 0
        gt_value_before = 0

        ga_qty_current = 0
        ga_value_current = 0
        ga_qty_before = 0
        ga_value_before = 0
    
        data = []
        for pc in product_class_ids:

            channel_data = []
            year_data = []

            t_qty_current = 0
            t_value_current = 0
            t_qty_before = 0
            t_value_before = 0

            avg_qty_current = 0
            avg_value_current = 0
            avg_qty_before = 0
            avg_value_before = 0

            for wh in wh_type_list:

                #SEARCH FOR CURRENT YEAR
                total_qty_current           = self.get_value(pc.id,wh,start_date.year)[0]
                total_value_current         = self.get_value(pc.id,wh,start_date.year)[1]

                #SEARCH FOR PREVIOUS YEAR
                total_qty_before            = self.get_value(pc.id,wh,start_date.year-1)[0]
                total_value_before          = self.get_value(pc.id,wh,start_date.year-1)[1]

                channel_data.append({
                        'name'                  : self.get_channel_label(wh),

                        'total_qty_current'     : total_qty_current,
                        'total_value_current'   : total_value_current,
                        'total_qty_before'      : total_qty_before,
                        'total_value_before'    : total_value_before,

                        'avg_qty_current'       : int(total_qty_current / 12),
                        'avg_value_current'     : int(total_value_current / 12),
                        'avg_qty_before'        : int(total_qty_before / 12),
                        'avg_value_before'      : int(total_value_before / 12),

                        'percentage_qty'        : (total_qty_current/total_qty_before * 100.00) if total_qty_before > 0 else 100,
                        'percentage_value'      : (total_value_current/total_value_before * 100.00) if total_value_before > 0 else 100,
                    })

                #SUMMARY TOTAL
                t_qty_current += total_qty_current
                t_value_current += total_value_current
                t_qty_before += total_qty_before
                t_value_before += total_value_before

                avg_qty_current += int(total_qty_current / 12)
                avg_value_current += int(total_value_current / 12)
                avg_qty_before += int(total_qty_before / 12)
                avg_value_before += int(total_value_before / 12)

            data.append({
                'class_name'            : pc.name,
                'channel_data_line'     : channel_data,
                'percentage_qty'        : (t_qty_current / t_qty_before * 100.00) if t_qty_before > 0 else 100,
                'percentage_value'      : (t_value_current / t_value_before * 100.00) if t_value_before > 0 else 100,
                })

        #COLLECT GRAND TOTAL DATA
        grand_total_data = []
        for wh in wh_type_list:
            t_qty_1 = self.get_grand_total_data(start_date.year-1, wh)[0]
            t_qty_2 = self.get_grand_total_data(start_date.year, wh)[0]
            t_value_1 = self.get_grand_total_data(start_date.year-1, wh)[1]
            t_value_2 = self.get_grand_total_data(start_date.year, wh)[1]

            grand_total_data.append({
                'name' : self.get_channel_label(wh),
                'row1' : t_qty_1,
                'row2' : t_value_1,
                'row3' : t_qty_2,
                'row4' : t_value_2,

                'row5' : self.get_grand_total_data(start_date.year-1, wh)[2],
                'row6' : self.get_grand_total_data(start_date.year-1, wh)[3],
                'row7' : self.get_grand_total_data(start_date.year, wh)[2],
                'row8' : self.get_grand_total_data(start_date.year, wh)[3],

                'row9' : t_qty_2 / t_qty_1 if t_qty_1 > 0 else 0,
                'row10': t_value_2 / t_value_1 if t_value_1 > 0 else 0,
                })

        return{
            'product_class_ids'     : data,
            'channel_data_line'     : channel_data,
            'grand_total_data'      : grand_total_data,
            'year_list'             : [str(start_date.year - 1), str(start_date.year)],
            'start_date'            : date_start_convert[:10],
            'end_date'              : date_stop_convert[:10],
            'area'                  : self.env['lea.area'].sudo().search([('id','=',area_id)],limit=1).name if area_id else 'All',
            'subarea'               : self.env['lea.sub.area'].sudo().search([('id','=',subarea_id)],limit=1).name if subarea_id else 'All',
            'print_info'            : str(datetime.now())[:19] + ' by ' + self.env.user.name,
            }  

    def get_grand_total_data(self, y, wh):
        date_start_convert = datetime.strptime(str(y) + '-01-01 00:00:00', '%Y-%m-%d %H:%M:%S') - timedelta(hours=7)
        date_start_convert = date_start_convert.strftime("%Y-%m-%d %H:%M:%S")
        date_stop_convert = datetime.strptime(str(y) + '-12-31 23:59:59', '%Y-%m-%d %H:%M:%S') - timedelta(hours=7)
        date_stop_convert = date_stop_convert.strftime("%Y-%m-%d %H:%M:%S")

        #search all location based on warehouse type
        location_list = []
        wh_ids = self.env['stock.warehouse'].sudo().search([('wh_type','=',wh)])
        for w in wh_ids:
            location_list.append(w.lot_stock_id.id)

        pos_order_line_ids = self.env['pos.order.line'].sudo().search([
            ('order_id.config_id.stock_location_id.id','in',location_list),
            ('order_id.date_order','>=',date_start_convert),
            ('order_id.date_order','<=',date_stop_convert),
            ('order_id.state','in',['paid','done','invoiced','credited']),
            ])

        total_qty = sum(l.qty for l in pos_order_line_ids)
        total_value = sum(l.price_subtotal_incl for l in pos_order_line_ids)
        avg_qty = total_qty / 12
        avg_value = total_value / 12

        return [total_qty, total_value, avg_qty, avg_value]

    def get_value(self, pc, wh, y):
        #TEMP VARIABEL
        date_start_convert = datetime.strptime(str(y) + '-01-01 00:00:00', '%Y-%m-%d %H:%M:%S') - timedelta(hours=7)
        date_start_convert = date_start_convert.strftime("%Y-%m-%d %H:%M:%S")
        date_stop_convert = datetime.strptime(str(y) + '-12-31 23:59:59', '%Y-%m-%d %H:%M:%S') - timedelta(hours=7)
        date_stop_convert = date_stop_convert.strftime("%Y-%m-%d %H:%M:%S")

        #search all location based on warehouse type
        location_list = []
        wh_ids = self.env['stock.warehouse'].sudo().search([('wh_type','=',wh)])
        for w in wh_ids:
            location_list.append(w.lot_stock_id.id)

        pos_order_line_ids = self.env['pos.order.line'].sudo().search([
            ('order_id.config_id.stock_location_id.id','in',location_list),
            ('product_id.product_class_category_id.id','=',pc),
            ('order_id.date_order','>=',date_start_convert),
            ('order_id.date_order','<=',date_stop_convert),
            ('order_id.state','in',['paid','done','invoiced','credited']),
            ])

        total_qty = sum(l.qty for l in pos_order_line_ids)
        total_value = sum(l.price_subtotal_incl for l in pos_order_line_ids)

        return [total_qty,total_value]

    #GET CHANNEL LABEL FROM CHANNEL CODE
    def get_channel_label(self, ch_code):
        if ch_code == 'LS':
            return 'Store'
        elif ch_code == 'LC':
            return 'Consignment'
        elif ch_code == 'TP':
            return 'Toko Putus'
        elif ch_code == 'CP':
            return 'Corporate'

    @api.multi
    def render_html(self, docids, data=None):
        data = dict(data or {})        
        data.update(self.get_detail(data['start_date'],data['end_date'],data['area_id'],data['subarea_id'],data['channel_id_store'],data['channel_id_consignment'],data['channel_id_toko_putus'],data['channel_id_corporate']))
        return self.env['report'].render('v10_lea.report_summary_sales_performance_comparison', data)
