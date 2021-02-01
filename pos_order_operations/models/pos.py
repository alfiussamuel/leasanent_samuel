# -*- coding: utf-8 -*-


from odoo import fields, models,tools,api, _
import logging
from functools import partial
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import pytz



class pos_order(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, default=_default_currency, track_visibility='always')
    posreference_number = fields.Char()
    
    @api.model
    def _order_fields(self, ui_order):
        res = super(pos_order, self)._order_fields(ui_order)
        if ui_order.has_key('reference_number'):
            res['posreference_number'] = ui_order['reference_number']
        if ui_order.has_key('order_id') and ui_order['order_id'] != '0':
            for order_line in ui_order['lines']:
                if order_line[2].has_key('order_line_id'):
                    wpos_order_line = self.env['pos.order.line'].browse(int(order_line[2]['order_line_id']))
                    if wpos_order_line:
                        wpos_order_line.returned_qty = wpos_order_line.returned_qty + abs(order_line[2]['qty'])
        return res

    @api.model
    def search_return_orders(self, order_id):
        pos_orders = self.search([('id','=',order_id)])
        if pos_orders:
            pos_order = pos_orders[0]
            payment_lines = []
            change = 0
            for i in pos_order.statement_ids:
                if i.amount > 0:
                    temp = {
                        'amount': i.amount,
                        'name': i.journal_id.name
                    }
                    payment_lines.append(temp)
                else:
                    change += i.amount
            discount = 0
            order_line = []
            tax_details = {}
            for line in pos_order.lines:
                discount += (line.price_unit * line.qty * line.discount) / 100
                order_line.append({
                    'line_id':line.id,
                    'returned_qty':line.returned_qty,
                    'product_name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'is_not_returnable':line.product_id.is_not_returnable,
                    'qty': line.qty,
                    'price_unit': line.price_unit,
                    'unit_name':line.product_id.uom_id.name,
                    'discount': line.discount,
                    'price_subtotal':line.price_subtotal,
                    'price_subtotal_incl':line.price_subtotal_incl,
                    })
                for tax_d in line.tax_ids_after_fiscal_position:
                    if tax_details.has_key(tax_d.name):
                        tax_details[tax_d.name] += (tax_d.amount/100)*line.price_unit*line.qty
                    else:
                        tax_details[tax_d.name] = (tax_d.amount/100)*line.price_unit*line.qty

            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            # order_date = datetime.strftime(pytz.utc.localize(datetime.strptime(pos_order.date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%m/%d/%Y %I:%M %p") 
            order_date = ""
            if pos_order.date_order:
                order_date = datetime.strptime(pos_order.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
            tax_details2 = []
            if tax_details:
                for k in tax_details:
                    tax_details2.append([k,round(tax_details[k],2)])

            return {
                'session_id':pos_order.session_id.name,
                'customer_name':pos_order.partner_id.name or "",
                'order_name':pos_order.name,
                'order_line':order_line,
                'payment_lines':payment_lines,
                'discount':discount,
                'change':change,
                'tax_details2':tax_details2,
                'order_id':pos_order.id,
                'name':pos_order.pos_reference,
                'date_order':order_date.strftime("%d/%m/%Y %H:%M:%S") if order_date else "",
                'amount_total':pos_order.amount_total,
                'amount_tax':pos_order.amount_tax,
                'cashier':pos_order.user_id.name if pos_order.user_id else "",
            }

class pos_order_line(models.Model):
    _inherit = 'pos.order.line'

    returned_qty = fields.Float("Returned Qty")


class product_product(models.Model):
    _inherit = 'product.product'

    is_not_returnable = fields.Boolean("Is Not Returnable",default=False) 
    
class pos_config(models.Model):
    _inherit = 'pos.config' 
    
    pos_order_reprint = fields.Boolean("Allow Orders",default=True)
    wv_order_date = fields.Integer(string="Order days")
    order_reprint = fields.Boolean("Allow Order Reprint",default=True)
    pos_reorder = fields.Boolean("Allow ReOrder",default=True)
    allow_order_return = fields.Boolean('Allow order return', default=True)



    @api.model
    def get_reorder_detail(self, order_id):
        pos_order = self.env['pos.order'].browse(order_id)
        order_line = []    
        for line in pos_order.lines:
            order_line.append({
                'product_id': line.product_id.id,
                'qty': line.qty,
                })
        return {
            'order_line':order_line,
            'partner_id':pos_order.partner_id.id,
            }


    @api.model
    def get_order_detail(self, order_id):
        pos_order = self.env['pos.order'].browse(order_id)
        payment_lines = []
        change = 0
        for i in pos_order.statement_ids:
            if i.amount > 0:
                temp = {
                    'amount': i.amount,
                    'name': i.journal_id.name
                }
                payment_lines.append(temp)
            else:
                change += i.amount
        discount = 0
        order_line = []
        tax_details = {}
        for line in pos_order.lines:
            discount += (line.price_unit * line.qty * line.discount) / 100
            order_line.append({
                'product_id': line.product_id.name,
                'qty': line.qty,
                'price_unit': line.price_unit,
                'unit_name':line.product_id.uom_id.name,
                'discount': line.discount,
                })
            for tax_d in line.tax_ids_after_fiscal_position:
                if tax_details.has_key(tax_d.name):
                    tax_details[tax_d.name] += (tax_d.amount/100)*line.price_unit*line.qty
                else:
                    tax_details[tax_d.name] = (tax_d.amount/100)*line.price_unit*line.qty

        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        # order_date = datetime.strftime(pytz.utc.localize(datetime.strptime(pos_order.date_order,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%m/%d/%Y %I:%M %p") 
        order_date = ""
        if pos_order.date_order:
            order_date = datetime.strptime(pos_order.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
        tax_details2 = []
        if tax_details:
            for k in tax_details:
                tax_details2.append([k,round(tax_details[k],2)])
        order = {
            'order_id':pos_order.id,
        	'name':pos_order.pos_reference,
            'date_order':order_date.strftime("%d/%m/%Y %H:%M:%S") if order_date else "",
        	'amount_total':pos_order.amount_total,
        	'amount_tax':pos_order.amount_tax,
            # 'table': pos_order.table_id.name if pos_order.table_id else "",
            # 'customer_count':pos_order.customer_count,
            'cashier':pos_order.user_id.name if pos_order.user_id else "",
            'posreference_number':pos_order.posreference_number,
        }

        return {
        	'order_line':order_line,
        	'payment_lines':payment_lines,
        	'discount':discount,
        	'change':change,
        	'order':order,
            'tax_details2':tax_details2,
        	}


class PosReceiptReport(models.AbstractModel):
    _name = 'report.point_of_sale.report_receipts'

    @api.model
    def render_html(self, docids, data=None):
        Report = self.env['report']
        # return Report.sudo().render('pos_orders_reprint.receipt_report', {'docs': self.env['pos.order'].sudo().browse(docids)})
        return Report.sudo().render('pos_order_operations.receipt_report', {'docs': self.env['pos.order'].sudo().browse(docids)})