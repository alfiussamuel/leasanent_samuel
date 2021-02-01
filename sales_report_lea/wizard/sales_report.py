from datetime import datetime, timedelta
from cStringIO import StringIO
import base64
import xlsxwriter
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import except_orm, Warning, RedirectWarning
from dateutil.relativedelta import relativedelta
from datetime import datetime
from dateutil import relativedelta
import time

class SalesReportLea(models.TransientModel):
    _name = 'sales.report.lea'


    company         = fields.Many2one('res.company', 'Company')
    type            = fields.Selection([('ar', 'Account Receivable'), ('link_gl', 'Link GL'), ('consigment', 'SPG Consigment')], string='Type')
    date_from       = fields.Date('Date From')
    date_to         = fields.Date('Date To')
    data            = fields.Binary('File', readonly=True)
    name            = fields.Char('Filename', readonly=True)
    state_position  = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    @api.multi
    def generate_excel_report(self):
        for res in self :
            report = False
            if res.type == 'ar':
                report = self.ar_sales_report_excel()
            elif res.type == 'link_gl':
                report = self.gl_sales_report_excel()
            elif res.type == 'consigment':
                report = self.consigment_sales_report_excel()
            return report

    @api.multi
    def ar_sales_report_excel(self):
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'AR-Sales-Report' + '_' + self.company.name + '.xlsx'
        workbook.add_format({'bold': 1, 'align': 'center'})
        # worksheet = workbook.add_worksheet('Report')
        worksheet1 = workbook.add_worksheet("Report Excel")
        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        center_title.set_font_size('12')
        # center_title.set_border()
        #################################################################################
        bold_font = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        bold_font.set_text_wrap()
        #################################################################################
        header_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        header_table.set_text_wrap()
        header_table.set_font_size('10')
        header_table.set_bg_color('#eff0f2')
        header_table.set_border()
        #################################################################################
        #################################################################################
        header_table_right = workbook.add_format(
            {'bold': 1, 'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        header_table_right.set_text_wrap()
        header_table_right.set_font_size('10')
        header_table_right.set_bg_color('#eff0f2')
        header_table_right.set_border()
        #################################################################################
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        set_right.set_text_wrap()
        set_right.set_font_size('8')
        set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_font_size('8')
        set_border.set_border()
        #################################################################################
        set_border_bold = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'bold': 1})
        set_border_bold.set_text_wrap()
        set_border_bold.set_font_size('9')
        set_border_bold.set_border()
        ################################################################################
        set_border_bold_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('9')
        set_border_bold_right.set_border()

        worksheet1.set_column('A:A', 45)
        worksheet1.set_column('B:B', 15)
        worksheet1.set_column('C:C', 15)
        worksheet1.set_column('D:D', 15)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_column('F:F', 15)
        worksheet1.set_column('G:G', 15)
        worksheet1.set_column('H:H', 15)
        worksheet1.set_column('I:I', 15)
        worksheet1.set_column('J:J', 15)
        worksheet1.set_row(0, 30)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.merge_range('A1:H1', self.company.name, center_title)
        worksheet1.merge_range('A2:H2', 'AR Sales Report', center_title)
        worksheet1.merge_range('A3:H3', date_from + ' s/d ' + date_to, center_title)

        worksheet1.merge_range('A7:A8', "Store Name", header_table)
        worksheet1.merge_range('B7:B8', "Tipe", header_table)
        worksheet1.merge_range('C7:C8', "Invoice/Struk/Doc", header_table)
        worksheet1.merge_range('D7:D8', "No. Faktur", header_table)
        worksheet1.merge_range('E7:J7', "Grand Total", header_table)
        worksheet1.write(7, 4, 'Qty', header_table)
        worksheet1.write(7, 5, 'Price (Bruto)', header_table)
        worksheet1.write(7, 6, 'Price (+disc)', header_table)
        worksheet1.write(7, 7, 'Price DPP', header_table)
        worksheet1.write(7, 8, 'Price PPN', header_table)
        worksheet1.write(7, 9, 'Price Netto', header_table)
        cursor = self.env.cr
        cursor.execute("""
                        select
                            partner_id
                        from
                            account_invoice
                        where
                            date_invoice between %s and %s and
                            state = 'open' and
                            company_id = %s
                        group by partner_id
                      """, (self.date_from, self.date_to, self.company.id))
        group_partner = cursor.fetchall()
        row = 8

        total_all_qty = 0
        total_all_before_discount = 0
        total_all_discount = 0
        total_all_amount_untaxed = 0
        total_all_amount_tax = 0
        total_all_amount_total = 0

        for partner in group_partner :


            invoice = self.env['account.invoice'].search([('partner_id', '=', partner[0]), ('date_invoice', '>=', self.date_from),('date_invoice', '<=', self.date_to), ('state', 'in', ['open','paid'])])
            partner_obj = self.env['res.partner'].browse(partner[0])
            code = ''
            if partner_obj.code_transaction == '01':
                code = '01 PKP NON WAPU'
            if partner_obj.code_transaction == '02':
                code = '02 PKP WAPU BERSYARAT'
            if partner_obj.code_transaction == '03':
                code = '03 PKP WAPU PENUH'
            if partner_obj.code_transaction == '08':
                code = '08 NON PKP'
            if partner_obj.code_transaction == 'XX':
                code = 'XX FTA'
            worksheet1.write(row, 0, partner_obj.name, set_border)
            worksheet1.write(row, 1, code, set_border)
            total_qty = 0
            total_before_discount = 0
            total_discount = 0
            total_amount_untaxed = 0
            total_amount_tax = 0
            total_amount_total = 0

            for inv in invoice:
                total_sub_qty = 0
                for d in inv.invoice_line_ids:
                    total_sub_qty = total_sub_qty + d.quantity

                worksheet1.write(row, 2, inv.number, set_border)
                worksheet1.write(row, 3, inv.nomor_faktur_id.name, set_border)
                worksheet1.write(row, 4, total_sub_qty, set_right)
                worksheet1.write(row, 5, inv.total_before_discount, set_right)
                worksheet1.write(row, 6, inv.total_discount, set_right)
                worksheet1.write(row, 7, inv.amount_untaxed, set_right)
                worksheet1.write(row, 8, inv.amount_tax, set_right)
                worksheet1.write(row, 9, inv.amount_total, set_right)
                row = row+1
                total_qty = total_qty + total_sub_qty
                total_before_discount = total_before_discount + inv.total_before_discount
                total_discount = total_discount + inv.total_discount
                total_amount_untaxed = total_amount_untaxed + inv.amount_untaxed
                total_amount_tax = total_amount_tax + inv.amount_tax
                total_amount_total = total_amount_total + inv.amount_total
            #Summary
            #row = row+1
            #worksheet1.merge_range('A' + str(row) + ':B' + str(row), partner_obj.name, set_border)
            worksheet1.write(row, 0, '', header_table_right)
            worksheet1.write(row, 1, '', header_table_right)
            worksheet1.write(row, 2, '', header_table_right)
            worksheet1.write(row, 3, '', header_table_right)
            worksheet1.write(row, 4, total_qty, header_table_right)
            worksheet1.write(row, 5, total_before_discount, header_table_right)
            worksheet1.write(row, 6, total_discount, header_table_right)
            worksheet1.write(row, 7, total_amount_untaxed, header_table_right)
            worksheet1.write(row, 8, total_amount_tax, header_table_right)
            worksheet1.write(row, 9, total_amount_total, header_table_right)
            row = row + 1

            total_all_qty = total_all_qty + total_qty
            total_all_before_discount = total_all_before_discount + total_before_discount
            total_all_discount = total_all_discount + total_discount
            total_all_amount_untaxed = total_all_amount_untaxed + total_amount_untaxed
            total_all_amount_tax = total_all_amount_tax + total_amount_tax
            total_all_amount_total = total_all_amount_total + total_amount_total

        row = row + 1
        worksheet1.write(row, 0, '', header_table_right)
        worksheet1.write(row, 1, '', header_table_right)
        worksheet1.write(row, 2, '', header_table_right)
        worksheet1.write(row, 3, '', header_table_right)
        worksheet1.write(row, 4, total_all_qty, header_table_right)
        worksheet1.write(row, 5, total_all_before_discount, header_table_right)
        worksheet1.write(row, 6, total_all_discount, header_table_right)
        worksheet1.write(row, 7, total_all_amount_untaxed, header_table_right)
        worksheet1.write(row, 8, total_all_amount_tax, header_table_right)
        worksheet1.write(row, 9, total_all_amount_total, header_table_right)

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'sales_report_lea', 'sales_report_lea_wizard')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sales.report.lea',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def gl_sales_report_excel(self):
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'GL-Sales-Report' + '_' + self.company.name + '.xlsx'
        workbook.add_format({'bold': 1, 'align': 'center'})
        # worksheet = workbook.add_worksheet('Report')
        worksheet1 = workbook.add_worksheet("Report Excel")
        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        center_title.set_font_size('12')
        # center_title.set_border()
        #################################################################################
        bold_font = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        bold_font.set_text_wrap()
        #################################################################################
        header_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        header_table.set_text_wrap()
        header_table.set_font_size('10')
        header_table.set_bg_color('#eff0f2')
        header_table.set_border()
        #################################################################################
        #################################################################################
        header_table_right = workbook.add_format(
            {'bold': 1, 'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        header_table_right.set_text_wrap()
        header_table_right.set_font_size('10')
        header_table_right.set_bg_color('#eff0f2')
        header_table_right.set_border()
        #################################################################################
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        set_right.set_text_wrap()
        set_right.set_font_size('8')
        set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_font_size('8')
        set_border.set_border()
        #################################################################################
        set_border_bold = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'bold': 1})
        set_border_bold.set_text_wrap()
        set_border_bold.set_font_size('9')
        set_border_bold.set_border()
        ################################################################################
        set_border_bold_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('9')
        set_border_bold_right.set_border()

        worksheet1.set_column('A:A', 45)
        worksheet1.set_column('B:B', 15)
        worksheet1.set_column('C:C', 15)
        worksheet1.set_column('D:D', 15)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_column('F:F', 15)
        worksheet1.set_column('G:G', 15)
        worksheet1.set_column('H:H', 15)
        worksheet1.set_column('I:I', 15)
        worksheet1.set_column('J:J', 15)
        worksheet1.set_row(0, 30)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.merge_range('A1:H1', self.company.name, center_title)
        worksheet1.merge_range('A2:H2', 'GL Sales Report', center_title)
        worksheet1.merge_range('A3:H3', date_from + ' s/d ' + date_to, center_title)

        worksheet1.merge_range('A7:A8', "Invoice/Struk/Doc", header_table)
        worksheet1.merge_range('B7:B8', "Store Name", header_table)
        worksheet1.merge_range('C7:C8', "Product Category", header_table)
        worksheet1.merge_range('D7:J7', "Grand Total", header_table)
        worksheet1.write(7, 3, 'Qty', header_table)
        worksheet1.write(7, 4, 'Bruto', header_table)
        worksheet1.write(7, 5, 'HPP', header_table)
        worksheet1.write(7, 6, 'Disc', header_table)
        worksheet1.write(7, 7, 'Price (DPP)', header_table)
        worksheet1.write(7, 8, 'Price (PPN)', header_table)
        worksheet1.write(7, 9, 'Price (netto)', header_table)
        cursor = self.env.cr
        cursor.execute("""
                            select
                                partner_id
                            from
                                account_invoice
                            where
                                date_invoice between %s and %s and
                                state = 'open' and
                                company_id = %s
                            group by partner_id
                          """, (self.date_from, self.date_to, self.company.id))
        group_partner = cursor.fetchall()
        row = 8
        total_all_qty = 0
        total_all_bruto = 0
        total_all_hpp = 0
        total_all_disc = 0
        total_all_dpp = 0
        total_all_ppn = 0
        total_all_subtotal = 0
        for partner in group_partner:
            invoice = self.env['account.invoice'].search(
                [('partner_id', '=', partner[0]), ('date_invoice', '>=', self.date_from),
                 ('date_invoice', '<=', self.date_to), ('state', '=', 'open')])

            for inv in invoice:
                worksheet1.write(row, 0,inv.number, set_border)
                worksheet1.write(row, 1, inv.partner_id.name, set_border)
                total_sub_qty = 0
                total_bruto = 0
                total_hpp = 0
                total_disc = 0
                total_dpp = 0
                total_ppn = 0
                total_subtotal = 0
                for d in inv.invoice_line_ids:
                    bruto = d.lea_sell_price * d.quantity
                    total_sub_qty = total_sub_qty + d.quantity
                    dpp = d.lea_net_amount
                    ppn = d.lea_net_amount * 0.1
                    hpp = bruto - ppn
                    subtotal_net = dpp + ppn
                    worksheet1.write(row, 2, d.product_id.product_category_id.name, set_border)
                    worksheet1.write(row, 3, d.quantity, set_right)
                    worksheet1.write(row, 4, bruto, set_right)
                    worksheet1.write(row, 5, hpp, set_right)
                    worksheet1.write(row, 6, d.lea_share_discount, set_right)
                    worksheet1.write(row, 7, dpp, set_right)
                    worksheet1.write(row, 8, ppn, set_right)
                    worksheet1.write(row, 9, subtotal_net, set_right)
                    row = row + 1
                    total_bruto = total_bruto + bruto
                    total_hpp = total_hpp + hpp
                    total_disc = total_disc + d.lea_share_discount
                    total_dpp = total_dpp + dpp
                    total_ppn = total_ppn + ppn
                    total_subtotal = total_subtotal + subtotal_net
                total_hpp = total_hpp * 0.5
                worksheet1.write(row, 0, '', set_border)
                worksheet1.write(row, 1, '', set_border)
                worksheet1.write(row, 2, '', set_border)
                worksheet1.write(row, 3, total_sub_qty, set_border_bold_right)
                worksheet1.write(row, 4, total_bruto, set_border_bold_right)
                worksheet1.write(row, 5, total_hpp, set_border_bold_right)
                worksheet1.write(row, 6, total_disc, set_border_bold_right)
                worksheet1.write(row, 7, total_dpp, set_border_bold_right)
                worksheet1.write(row, 8, total_ppn, set_border_bold_right)
                worksheet1.write(row, 9, total_subtotal, set_border_bold_right)

                total_all_qty = total_all_qty + total_sub_qty
                total_all_bruto = total_all_bruto + total_bruto
                total_all_hpp = total_all_hpp + total_hpp
                total_all_disc = total_all_disc + total_disc
                total_all_dpp = total_all_dpp + total_dpp
                total_all_ppn = total_all_ppn + total_ppn
                total_all_subtotal = total_all_subtotal + total_subtotal

                row = row + 1

        worksheet1.write(row, 0, '', set_border)
        worksheet1.write(row, 1, '', set_border)
        worksheet1.write(row, 2, '', set_border)
        worksheet1.write(row, 3, total_all_qty, set_border_bold_right)
        worksheet1.write(row, 4, total_all_bruto, set_border_bold_right)
        worksheet1.write(row, 5, total_all_hpp, set_border_bold_right)
        worksheet1.write(row, 6, total_all_disc, set_border_bold_right)
        worksheet1.write(row, 7, total_all_dpp, set_border_bold_right)
        worksheet1.write(row, 8, total_all_ppn, set_border_bold_right)
        worksheet1.write(row, 9, total_all_subtotal, set_border_bold_right)
        # Summary

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'sales_report_lea', 'sales_report_lea_wizard')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sales.report.lea',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def consigment_sales_report_excel(self):
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'Consigment-Sales-Report' + '_' + self.company.name + '.xlsx'
        workbook.add_format({'bold': 1, 'align': 'center'})
        # worksheet = workbook.add_worksheet('Report')
        worksheet1 = workbook.add_worksheet("Report Excel")
        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        center_title.set_font_size('12')
        # center_title.set_border()
        #################################################################################
        bold_font = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        bold_font.set_text_wrap()
        #################################################################################
        header_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        header_table.set_text_wrap()
        header_table.set_font_size('10')
        header_table.set_bg_color('#eff0f2')
        header_table.set_border()
        #################################################################################
        #################################################################################
        header_table_right = workbook.add_format(
            {'bold': 1, 'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        header_table_right.set_text_wrap()
        header_table_right.set_font_size('10')
        header_table_right.set_bg_color('#eff0f2')
        header_table_right.set_border()
        #################################################################################
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        set_right.set_text_wrap()
        set_right.set_font_size('8')
        set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_font_size('8')
        set_border.set_border()
        #################################################################################
        set_border_bold = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'bold': 1})
        set_border_bold.set_text_wrap()
        set_border_bold.set_font_size('9')
        set_border_bold.set_border()
        ################################################################################
        set_border_bold_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('9')
        set_border_bold_right.set_border()

        worksheet1.set_column('A:A', 45)
        worksheet1.set_column('B:B', 45)
        worksheet1.set_column('C:C', 45)

        worksheet1.set_row(0, 30)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.merge_range('A1:C1', self.company.name, center_title)
        worksheet1.merge_range('A2:C2', 'LAPORAN PENJUALAN KONSINYASI', center_title)
        worksheet1.merge_range('A3:C3', date_from + ' s/d ' + date_to, center_title)
        cursor = self.env.cr
        cursor.execute("""
                            select
                                partner_id
                            from
                                account_invoice
                            where
                                date_invoice between %s and %s and
                                state = 'open' and
                                company_id = %s
                            group by partner_id
                          """, (self.date_from, self.date_to, self.company.id))
        group_partner = cursor.fetchall()
        row = 8
        total_all_sub_qty = 0
        total_all_sub_amount = 0
        for partner in group_partner:
            partner_obj = self.env['res.partner'].browse(partner[0])
            if partner_obj.customer_type == 'CONSIGNMENT':
                invoice = self.env['account.invoice'].search([('partner_id', '=', partner[0]),
                                                          ('date_invoice', '>=', self.date_from),
                                                          ('date_invoice', '<=', self.date_to),
                                                          ('state', '=', 'open')])

                worksheet1.write(row, 0, partner_obj.name, header_table)
                total_qty       = 0
                total_amount    = 0
                for inv in invoice:
                    total_sub_qty = 0
                    total_sub_amount = 0
                    for d in inv.invoice_line_ids:
                        total_sub_qty = total_sub_qty + d.quantity
                        total_sub_amount = total_sub_amount + d.lea_net_amount
                    total_qty = total_qty + total_sub_qty
                    total_amount = total_amount + total_sub_amount

                worksheet1.write(row, 1, total_qty, header_table_right)
                worksheet1.write(row, 2, total_amount, header_table_right)
                row = row + 1

                for inv in invoice:
                    total_sub_qty = 0
                    total_sub_amount = 0
                    for d in inv.invoice_line_ids:
                        total_sub_qty = total_sub_qty + d.quantity
                        total_sub_amount = total_sub_amount + d.lea_net_amount
                    worksheet1.write(row, 0, inv.number, set_border)
                    worksheet1.write(row, 1, total_sub_qty, set_right)
                    worksheet1.write(row, 2, total_sub_amount, set_right)
                    total_all_sub_qty = total_all_sub_qty + total_sub_qty
                    total_all_sub_amount = total_all_sub_amount + total_sub_amount

                    row = row + 1
            worksheet1.write(row, 0, "GRAND TOTAL", header_table_right)
            worksheet1.write(row, 1, total_all_sub_qty, header_table_right)
            worksheet1.write(row, 2, total_all_sub_amount, header_table_right)

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'sales_report_lea', 'sales_report_lea_wizard')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sales.report.lea',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }


class SalesPartnerReportLea(models.TransientModel):
    _name = 'sales.partner.report.lea'


    company         = fields.Many2one('res.company', 'Company')
    partner_id      = fields.Many2one('res.partner', 'Partner')
    date_from       = fields.Date('Date From')
    date_to         = fields.Date('Date To')
    data            = fields.Binary('File', readonly=True)
    name            = fields.Char('Filename', readonly=True)
    state_position  = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    @api.multi
    def generate_excel_report(self):
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'Sales-Report-Per_Partner' + '_' + self.company.name + '.xlsx'
        workbook.add_format({'bold': 1, 'align': 'center'})
        # worksheet = workbook.add_worksheet('Report')
        worksheet1 = workbook.add_worksheet("Report Excel")
        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        center_title.set_font_size('12')
        # center_title.set_border()
        #################################################################################
        bold_font = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        bold_font.set_text_wrap()
        #################################################################################
        header_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        header_table.set_text_wrap()
        header_table.set_font_size('10')
        header_table.set_bg_color('#eff0f2')
        header_table.set_border()
        #################################################################################
        #################################################################################
        header_table_right = workbook.add_format(
            {'bold': 1, 'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        header_table_right.set_text_wrap()
        header_table_right.set_font_size('10')
        header_table_right.set_bg_color('#eff0f2')
        header_table_right.set_border()
        #################################################################################
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        set_right.set_text_wrap()
        set_right.set_font_size('8')
        set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_font_size('8')
        set_border.set_border()
        #################################################################################
        set_border_bold = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'bold': 1})
        set_border_bold.set_text_wrap()
        set_border_bold.set_font_size('9')
        set_border_bold.set_border()
        ################################################################################
        set_border_bold_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('9')
        set_border_bold_right.set_border()

        worksheet1.set_column('A:A', 45)
        worksheet1.set_column('B:B', 15)
        worksheet1.set_column('C:C', 15)
        worksheet1.set_column('D:D', 15)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_row(0, 30)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.merge_range('A1:E1', self.company.name, center_title)
        worksheet1.merge_range('A2:E2', 'Sales Report Per Partner', center_title)
        worksheet1.merge_range('A3:E3', date_from + ' s/d ' + date_to, center_title)
        worksheet1.merge_range('A4:E4', self.partner_id.name, center_title)

        worksheet1.write(7, 0, 'Date', header_table)
        worksheet1.write(7, 1, 'Qty', header_table)
        worksheet1.write(7, 2, 'Gross', header_table)
        worksheet1.write(7, 3, 'Disc', header_table)
        worksheet1.write(7, 4, 'Rupiah', header_table)
        sale_order_line = self.env['sale.order.line'].search([('order_partner_id', '=', self.partner_id.id), ('order_date', '>=', self.date_from),('order_date', '<=', self.date_to), ('order_id.state', 'not in', ['draft','cancel'])])
        row = 8
        cursor = self.env.cr
        cursor.execute("""
                        select
                          a.order_date as date_order
                        from
                          sale_order_line as a,
                          sale_order as b
                        where
                          a.order_id = b.id and
                          a.order_date between %s and %s and
                          b.state not in ('draft','cancel') and
                          b.partner_id = %s group by a.order_date
                       """, (self.date_from, self.date_to, self.partner_id.id))
        group_date = cursor.fetchall()
        total_all_qty       = 0
        total_all_gross     = 0
        total_all_discount  = 0
        total_all_amount    = 0
        for d in group_date :
            sale_order_line = self.env['sale.order.line'].search([('order_partner_id', '=', self.partner_id.id), ('order_date', '=', d[0]), ('order_id.state', 'not in', ['draft', 'cancel'])])
            sub_qty = 0
            sub_gross = 0
            sub_discount = 0
            sub_amount = 0
            for line in sale_order_line:
                gross = line.product_uom_qty * line.price_unit
                discount = (line.discount/100) * gross
                amount =  line.price_total

                sub_qty = sub_qty + line.product_uom_qty
                sub_gross = sub_gross + gross
                sub_discount = sub_discount + discount
                sub_amount = sub_amount + amount

            date_order_raw = datetime.strptime(d[0], '%Y-%m-%d')
            date_order = datetime.strftime(date_order_raw, '%d-%B-%Y')
            worksheet1.write(row, 0, date_order, set_border)
            worksheet1.write(row, 1, sub_qty, set_border)
            worksheet1.write(row, 2, sub_gross, set_border)
            worksheet1.write(row, 3, sub_discount, set_border)
            worksheet1.write(row, 4, sub_amount, set_border)
            total_all_qty = total_all_qty + sub_qty
            total_all_gross = total_all_gross + sub_gross
            total_all_discount = total_all_discount + sub_discount
            total_all_amount = total_all_amount + sub_amount
            row = row + 1

        worksheet1.write(row, 0, '', set_border)
        worksheet1.write(row, 1, total_all_qty, set_border)
        worksheet1.write(row, 2, total_all_gross, set_border)
        worksheet1.write(row, 3, total_all_discount, set_border)
        worksheet1.write(row, 4, total_all_amount, set_border)


        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'sales_report_lea', 'sales_partner_report_lea_wizard')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sales.partner.report.lea',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }


