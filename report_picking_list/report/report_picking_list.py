# pylint: disable=C0111,C0303
# -*- coding: utf-8 -*-
from odoo import _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx

class PartnerXlsx(ReportXlsx):

    def generate_xlsx_report(self, wb, data, pickings):
        if len(pickings) > 1:
            raise UserError(_('Can`t Print Report with Multiple Data Picking List'))
        user = self.env['res.users'].search([('id', '=', self.env.context.get('uid'))])
        sheet = wb.add_worksheet("Picking List")
#         sheet.set_column('A1:AH8', 2)
        #################################################################################
        title_format = wb.add_format({'font_color': '#a6a6a6', 'font_name': 'tahoma', 'font_size': '18'})
        #################################################################################
        header_format = wb.add_format({'font_size': '18', 'align': 'center', 'valign': 'vcenter'})
        #################################################################################
        line_format = wb.add_format({'align': 'center_across', 'valign': 'vcenter'})
        line_format.set_border()
        #################################################################################
        footer = wb.add_format({'valign': 'vcenter'})
        footer.set_top()
        #################################################################################
        for picking in pickings:
            sheet.merge_range('B1:D2', user.company_id.name, title_format)
            sheet.write(0, 24, 'PAGE :')
            sheet.merge_range('B2:AH2', 'PICK LIST', header_format)
            
            sheet.write(3, 1, 'Pick List No.')
            sheet.write(3, 6, ':')
            sheet.write(3, 7, picking.name)
            
            sheet.write(4, 1, 'Pick List Date ')
            sheet.write(4, 6, ':')
            sheet.write(4, 7, datetime.strptime(picking.date, "%Y-%m-%d").strftime("%d-%m-%Y"))

            sheet.write(5, 1, 'Warehouse_ID')
            sheet.write(5, 6, ':')
            sheet.write(5, 7, picking.warehouse_id.name or '')
            
            sheet.write(6, 1, 'Location')
            sheet.write(6, 6, ':')
            sheet.write(6, 7, picking.location_id.name or '')

            sheet.merge_range('B9:E9', 'Rack', line_format)
            sheet.merge_range('F9:K9', 'Barcode', line_format)
            sheet.merge_range('L9:O9', 'Qty Pick (Pcs)', line_format)
            sheet.merge_range('P9:V9', 'DO No.', line_format)
            sheet.merge_range('W9:Z9', 'Qty Picked Scan (Pcs)', line_format)
            i = 9
            qty = 0
            for line in picking.line_ids:
                sheet.merge_range('B%s:E%s'%(i+1,i+1), line.rack_id.name or '', line_format)
                sheet.merge_range('F%s:K%s'%(i+1,i+1), line.product_id.name or '', line_format)
                sheet.merge_range('L%s:O%s'%(i+1,i+1), line.qty, line_format)
                sheet.merge_range('P%s:V%s'%(i+1,i+1), line.delivery_id.name or '', line_format)
                sheet.merge_range('W%s:Z%s'%(i+1,i+1), line.qty_scan, line_format)
                qty += line.qty
                i += 1
            
            sheet.merge_range('B%s:E%s'%(i+2,i+2), 'Total DO', line_format)
            sheet.merge_range('G%s:K%s'%(i+2,i+2), 'Total Qty Picked (Pcs)', line_format)
            sheet.merge_range('B%s:E%s'%(i+3,i+3), picking.total_do, line_format)
            sheet.merge_range('G%s:K%s'%(i+3,i+3), qty, line_format)
            
            sheet.write('B%s'%(i+5), 'Picking Date ; ')
            sheet.write('I%s'%(i+5), 'Picker ; ')
            sheet.write('Q%s'%(i+5), 'Receive Date ; ')
            sheet.write('Y%s'%(i+5), 'Receiver ; ')
            
            sheet.merge_range('I%s:K%s'%(i+11,i+11), 'name & sign.', footer)
            sheet.merge_range('Y%s:AA%s'%(i+11,i+11), 'name, sign & company stamp.', footer)

PartnerXlsx('report.lea.picking.list.xlsx',
            'lea.picking.list')
