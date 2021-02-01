# -*- coding: utf-8 -*-
from odoo import api, models

class InvoiceReportCustomPkp(models.AbstractModel):
    """Render report Purchase Payment"""
    _name = 'report.report_invoice.invoice_template_report_pkp'

    def get_sale(self, origin):
        res = {}
        mapping = []
        if origin:
            sale = self.env['sale.order'].search([('name','ilike', origin)])
            data_do = ""
            data_picking_name = ""
            data_picking_date = ""
            word_pcking = ""
            for picking in sale.picking_ids:
                if picking:
                    data_picking_name += "%s, " % picking.name
                    word = data_picking_name.split('GUDANG_HO')
                    word_pcking = ''.join(word)
                    data_picking_date += "%s, " % picking.min_date

            data_do = data_picking_name[:9] + word_pcking


            res = {
            'do_number' : data_do or '-',
            'do_date': data_picking_date or '-'  ,
            }
            mapping.append(res)
        return mapping

    def get_disc(self, inv):
        ttl_disc = 0
        for line in inv.invoice_line_ids:
            ttl_disc += line.price_unit * line.discount / 100
        return ttl_disc

    @api.multi
    def render_html(self, docids, data=None):
        res = self.env['account.invoice'].search([('id','in',docids)])
        
        #update number of print
        for line in res:
            line.write({'number_of_print':line.number_of_print+1})

        model = self.env.context.get('active_model')
        docargs = {
            'docs': res,
            'get_sale': self.get_sale(res.origin),
            'get_disc': self.get_disc,
        }
        return self.env['report'].render('report_invoice.invoice_template_report_pkp', docargs)


class InvoiceReportCustomNonPkp(models.AbstractModel):
    """Render report Purchase Payment"""
    _name = 'report.report_invoice.invoice_template_report_non_pkp'

    def get_sale(self, origin):
        res = {}
        mapping = []
        if origin:
            sale = self.env['sale.order'].search([('name','ilike', origin)])
            data_do = ""
            data_picking_name = ""
            data_picking_date = ""
            word_pcking = ""
            for picking in sale.picking_ids:
                if picking:
                    data_picking_name += "%s, " % picking.name
                    word = data_picking_name.split('GUDANG_HO')
                    word_pcking = ''.join(word)
                    data_picking_date += "%s, " % picking.min_date

            data_do = data_picking_name[:9] + word_pcking


            res = {
            'do_number' : data_do or '-',
            'do_date': data_picking_date or '-'  ,
            }
            mapping.append(res)
        return mapping

    def get_disc(self, inv):
        ttl_disc = 0
        for line in inv.invoice_line_ids:
            ttl_disc += line.price_unit * line.discount / 100
        return ttl_disc

        
    @api.multi
    def render_html(self, docids, data=None):
        res = self.env['account.invoice'].search([('id','in',docids)])

        #update number of print
        for line in res:
            line.write({'number_of_print':line.number_of_print+1})
            
        model = self.env.context.get('active_model')
        docargs = {
            'docs': res,
            'get_sale': self.get_sale(res.origin),
            'get_disc': self.get_disc
        }
        return self.env['report'].render('report_invoice.invoice_template_report_non_pkp', docargs)


class InvoiceReportCustomRetur(models.AbstractModel):
    """Render report Purchase Payment"""
    _name = 'report.report_invoice.invoice_template_report_retur'

    def get_sale(self, origin):
        res = {}
        mapping = []
        if origin:
            sale = self.env['sale.order'].search([('name', 'ilike', origin)])
            data_do = ""
            data_picking_name = ""
            data_picking_date = ""
            word_pcking = ""
            for picking in sale.picking_ids:
                if picking:
                    data_picking_name += "%s, " % picking.name
                    word = data_picking_name.split('GUDANG_HO')
                    word_pcking = ''.join(word)
                    data_picking_date += "%s, " % picking.min_date

            data_do = data_picking_name[:9] + word_pcking

            res = {
                'do_number': data_do or '-',
                'do_date': data_picking_date or '-',
            }
            mapping.append(res)
        return mapping

    def get_disc(self, inv):
        ttl_disc = 0
        for line in inv.invoice_line_ids:
            ttl_disc += line.price_unit * line.discount / 100
        return ttl_disc

    @api.multi
    def render_html(self, docids, data=None):
        res = self.env['account.invoice'].search([('id', 'in', docids)])

        # update number of print
        for line in res:
            line.write({'number_of_print': line.number_of_print + 1})

        model = self.env.context.get('active_model')
        docargs = {
            'docs': res,
            'get_sale': self.get_sale(res.origin),
            'get_disc': self.get_disc,
        }
        return self.env['report'].render('report_invoice.invoice_template_report_retur', docargs)
