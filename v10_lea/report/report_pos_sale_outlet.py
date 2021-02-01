from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta


class report_pos_sale_outlet(models.AbstractModel):

    _name = 'report.v10_lea.report_pos_sale_outlet'

    @api.model
    def get_order_detail(self, start_date =False, end_date=False, outlet_ids=False, print_by_sales=False, salesman_ids=False):
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

        data = []
        pos_ids = self.env['pos.config'].sudo().search([
            ('id','in',outlet_ids),
          ])

        salesman_info = ''
        if print_by_sales:
            user_ids = self.env['res.users'].sudo().search([('id','in',salesman_ids)])
            for u in user_ids:
                if salesman_info == '' or not salesman_ids:
                    salesman_info = u.name
                else:
                    salesman_info += ', ' + u.name
        else:
            salesman_info = 'All Salesman'

        for pos in pos_ids:
            order_ids = False
            if print_by_sales:
                order_ids = self.env['pos.order.line'].sudo().search([
                    ('order_id.date_order','>=',date_start_convert),
                    ('order_id.date_order','<=',date_stop_convert),
                    ('order_id.session_id.config_id.id','=',pos.id),
                    ('order_id.user_id.id','in',salesman_ids),
                    ('order_id.state','in',['paid','done','invoiced','credited']),
                  ])
            else:
                order_ids = self.env['pos.order.line'].sudo().search([
                    ('order_id.date_order','>=',date_start_convert),
                    ('order_id.date_order','<=',date_stop_convert),
                    ('order_id.session_id.config_id.id','=',pos.id),
                    ('order_id.state','in',['paid','done','invoiced','credited']),
                  ])

            data_order = []
            for order in order_ids:
                data_order.append({
                    'date'      : order.order_id.date_order,
                    'ref'       : order.order_id.name,
                    'customer'  : order.order_id.partner_id.name,
                    'salesman'  : order.order_id.user_id.name,
                    'product'   : order.product_id.display_name,
                    'qty'       : order.qty,
                    'discount'  : order.discount,
                    'total'     : order.price_subtotal,
                    })

            payment_list = []
            for j in pos.journal_ids:
                total_payment = 0
                statement_ids = False
                if print_by_sales:
                    statement_ids = self.env['account.bank.statement.line'].sudo().search([
                        ('pos_statement_id.date_order','>=',date_start_convert),
                        ('pos_statement_id.date_order','<=',date_stop_convert),
                        ('pos_statement_id.session_id.config_id.id','=',pos.id),
                        ('pos_statement_id.user_id.id','in',salesman_ids),
                        ('pos_statement_id.state','in',['paid','done','invoiced','credited']),
                        ('journal_id.id','=',j.id),
                      ])
                else:
                    statement_ids = self.env['account.bank.statement.line'].sudo().search([
                        ('pos_statement_id.date_order','>=',date_start_convert),
                        ('pos_statement_id.date_order','<=',date_stop_convert),
                        ('pos_statement_id.session_id.config_id.id','=',pos.id),
                        ('pos_statement_id.state','in',['paid','done','invoiced','credited']),
                        ('journal_id.id','=',j.id),
                      ])
                for s in statement_ids:
                    total_payment += s.amount

                if total_payment > 0:
                    payment_list.append({
                        'name'          : j.name,
                        'total'         : total_payment
                    })

            data.append({
                'outlet'        : pos.name,
                'order_list'    : data_order,
                'payment_list'  : payment_list,
                })


        return{
            'order_ids'     : data,
            'start_date'    : start_date,
            'end_date'      : end_date,
            'salesman_info' : salesman_info,
            }  

    @api.multi
    def render_html(self, docids, data=None):
        data = dict(data or {})        
        data.update(self.get_order_detail(data['start_date'],data['end_date'],data['outlet_ids'],data['print_by_sales'],data['salesman_ids']))
        return self.env['report'].render('v10_lea.report_pos_sale_outlet', data)
