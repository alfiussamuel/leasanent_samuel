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

class report_stock_lea_wizard(models.TransientModel):
    _name = 'report.stock.lea.wizard'

    company     = fields.Many2one('res.company', 'Company')
    type        = fields.Selection([('stock_move_toko', 'Stock Move Per Toko'),
                             ('stock_replenishment_toko', 'Analisa Stock Replenishment Toko'),
                             ('product_sell_thru', 'Analisa Product Sell Thru'),
                             ('analisa_level_stock', 'Analisa level Stock dan Average Penjualan'),
                             ],
                            string='Type')
    period_id   = fields.Many2one('account.period', 'Period')
    stock_type     = fields.Selection([('MH', 'Main WH'),
                                       ('ST', 'Store'),
                                ],
                               string='WH Type')

    wh_type     = fields.Selection([('LS', 'Store'),
                                 ('LC', 'Consigment'),
                                 ('TP', 'Toko Putus'),
                                 ('CP', 'Consigment'),
                                 ('MW', 'MAIN WH'),
                             ],
                            string='WH Type')
    user_pds_id = fields.Many2one('res.users', 'User PDS', default=lambda self:self.env.user.id)
    date_from   = fields.Date('Date From')
    date_to     = fields.Date('Date To')
    data        = fields.Binary('File', readonly=True)
    name        = fields.Char('Filename', readonly=True)
    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    location_ids3   = fields.Many2many('stock.warehouse',string='Warehouse')
    location_main_wh_ids2  = fields.Many2many('stock.location', string='Location Main WH')

    @api.multi
    @api.onchange('period_id')
    def onchange_period_id(self):
        values = {
            'date_from': '',
            'date_to': '',
        }
        if self.period_id:
            values['date_from'] = self.period_id.date_start
            values['date_to'] = self.period_id.date_stop
        self.update(values)


    @api.multi
    @api.onchange('user_pds_id')
    def onchange_account_id(self):
        user = []
        if self.user_pds_id:
            return {'domain': {'location_ids3': [('responsible_id', 'in', [self.user_pds_id.id])]}}

    @api.multi
    def generate_excel_report(self):
        for res in self:
            report = False
            if res.type == 'stock_move_toko':
                report = self.stock_move_toko_report_excel()
            return report

    @api.multi
    @api.onchange('wh_type')
    def onchange_wh_type(self):
        list = []
        values = {
            'location_ids3': list,

        }
        if self.wh_type:
            loc = self.env['stock.warehouse'].search([('wh_type', '=', self.wh_type)])
            for l in loc :
                list.append(l.id)

            values['location_ids3'] = list
        self.update(values)


    @api.multi
    def generate_stock_move_toko_report_excel(self):
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'Stock Move Per- Toko' + '_' + self.company.name + '.xlsx'
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
        header_table_right = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
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

        worksheet1.merge_range('A1:J1', self.company.name, center_title)
        worksheet1.merge_range('A2:J2', 'Stock Move Per Toko', center_title)
        worksheet1.merge_range('A3:J3', date_from + ' s/d ' + date_to, center_title)

        worksheet1.merge_range('A7:A9', "Dept. Store", header_table)
        worksheet1.merge_range('B7:B9', "Grade", header_table)
        worksheet1.merge_range('C7:C9', "Kapasitas", header_table)
        worksheet1.merge_range('D7:L7', '', header_table)
        worksheet1.write(7, 3, 'Stock Awal', header_table)
        worksheet1.merge_range('E8:G8','In', header_table)
        worksheet1.merge_range('H8:J8','Out', header_table)

        worksheet1.merge_range('M7:M9', 'Stock Akhir', header_table)
        worksheet1.merge_range('N7:N9', 'Over', header_table)
        worksheet1.write(7, 10, 'Sale', header_table)
        worksheet1.write(7, 11, 'Loss', header_table)
        worksheet1.write(8, 3, '', header_table)

        worksheet1.write(8, 4, 'mfg (non-trans)', header_table)
        worksheet1.write(8, 5, 'mfg (trans)', header_table)
        worksheet1.write(8, 6, 'rfg', header_table)

        worksheet1.write(8, 7, 'mfg (non-trans)', header_table)
        worksheet1.write(8, 8, 'mfg (trans)', header_table)
        worksheet1.write(8, 9, 'rfg', header_table)

        worksheet1.write(8, 10, '', header_table)
        worksheet1.write(8, 11, '', header_table)

        worksheet1.write(8, 12, '', header_table)
        worksheet1.write(8, 13, '', header_table)


        row = 9
        #worksheet1.write(9, 9, str( self.location_ids2))
        #raise Warning(self.location_ids2)
        ###hitung stock awal digudang
        stock_awal_gudang = 0
        if self.location_main_wh_ids2 :
            for lm in self.location_main_wh_ids2 :
                init_wh_stock = self.get_stock_awal(lm.id)
                stock_awal_gudang = stock_awal_gudang + init_wh_stock

        #Print dan Hitung stock masing2 lokasi
        if self.stock_type == 'ST':
            for lc in self.location_ids3 :
                wh = self.env['stock.warehouse'].browse(lc.id)
                grade = ''
                capacity = 0
                if wh :
                    grade = wh.wh_grade
                    capacity = wh.wh_capacity
                loc = wh.lot_stock_id.id
                stock_awal = self.get_stock_awal(loc)
                stock_in_internal = self.get_stock_in_transit(loc) # in mmw/mfg (stock barang masuk dengan lokasi asal tipe transit
                stock_in_internal_non = self.get_stock_in_non_transit(loc) # in mmw/mfg (stock barang masuk dengan lokasi asal tipe internal
                stock_in_adjustment = self.get_stock_in_adjustment(loc) # in rfg (stock barang masuk dengan lokasi asal inventory adjusment

                stock_out_internal = self.get_stock_out_transit(loc) #out mfg (stock barang keluar dengan lokasi tujuan tipe transit
                stock_out_internal_non = self.get_stock_out_transit_non(loc)  # out mfg (stock barang keluar dengan lokasi tujuan tipe internal
                stock_out_adjusment = self.get_stock_out_adjustment(loc) #out mfg (stock barang keluar dengan lokasi tujuan tipe non transit exc. customer

                stock_out_sale = self.get_stock_out_sale(loc) #out sale (stock barang keluar dengan lokasi tujuan tipe customer
                stock_awal_total =  stock_awal
                stock_akhir = stock_awal_total + ((stock_in_internal + stock_in_internal_non + stock_in_adjustment)-(stock_out_internal + stock_out_internal_non + stock_out_adjusment + stock_out_sale))
                over = stock_akhir - capacity

                worksheet1.write(row, 0, lc.name, set_border)
                worksheet1.write(row, 1, grade,set_border)
                worksheet1.write(row, 2, capacity, set_right)
                worksheet1.write(row, 3, stock_awal_total, set_right)
                worksheet1.write(row, 4, stock_in_internal_non, set_right)
                worksheet1.write(row, 5, stock_in_internal, set_right)
                worksheet1.write(row, 6, stock_in_adjustment, set_right)

                worksheet1.write(row, 7, stock_out_internal_non, set_right)
                worksheet1.write(row, 8, stock_out_internal, set_right)
                worksheet1.write(row, 9, stock_out_adjusment, set_right)
                worksheet1.write(row, 10, stock_out_sale, set_right)
                worksheet1.write(row, 11, '',set_right)
                worksheet1.write(row, 12, stock_akhir,set_right)
                worksheet1.write(row, 13, over,set_right)
                row = row + 1
        else :

            for lc in self.location_main_wh_ids2 :
                grade = ''
                capacity = 0
                loc = lc.id

                stock_in_internal = self.get_stock_in_transit2(loc)  # in mmw/mfg (stock barang masuk dengan lokasi asal tipe supplier)
                stock_in_internal_non = self.get_stock_in_transit2_non(loc)  #in mmw/mfg (stock barang masuk dengan lokasi asal tipe internal)
                stock_in_adjustment = self.get_stock_in_adjustment2(loc) #in mmw/mfg (stock barang masuk dengan lokasi asal tipe adjusment)

                stock_out_internal = self.get_stock_out_transit(loc) #out mfg (stock barang keluar dengan lokasi tujuan tipe transit
                stock_out_internal_non = self.get_stock_out_transit_non(loc)  # out mfg (stock barang keluar dengan lokasi tujuan tipe internal
                stock_out_adjusment = self.get_stock_out_adjustment(loc) #out mfg (stock barang keluar dengan lokasi tujuan tipe adjusment exc. customer
                stock_out_sale = self.get_stock_out_sale(loc) #out sale (stock barang keluar dengan lokasi tujuan tipe customer
                stock_awal_total = stock_awal_gudang
                stock_akhir = stock_awal_total + ((stock_in_internal + stock_in_internal_non + stock_in_adjustment)-(stock_out_internal + stock_out_internal_non + stock_out_adjusment + stock_out_sale))

                worksheet1.write(row, 0, lc.name, set_border)
                worksheet1.write(row, 1, grade,set_border)
                worksheet1.write(row, 2, capacity, set_right)
                worksheet1.write(row, 3, stock_awal_total, set_right)
                worksheet1.write(row, 4, stock_in_internal_non, set_right)
                worksheet1.write(row, 5, stock_in_internal, set_right)
                worksheet1.write(row, 6, stock_in_adjustment, set_right)
                worksheet1.write(row, 7, stock_out_internal_non, set_right)
                worksheet1.write(row, 8, stock_out_internal, set_right)
                worksheet1.write(row, 9, stock_out_adjusment, set_right)

                worksheet1.write(row, 10, stock_out_sale, set_right)
                worksheet1.write(row, 11, '',set_right)
                worksheet1.write(row, 12, stock_akhir,set_right)
                worksheet1.write(row, 13, '',set_right)
                row = row + 1


        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference('stock_report_lea', 'report_stock_lea_wizard_form')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.stock.lea.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_stock_awal(self, location_id):
        cursor = self.env.cr
        qty_in = 0
        qty_out = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                   select
                                     a.qty_in, b.qty_out
                                     from
                                     (select sum(a.product_uom_qty) as qty_in
                                     from
                                     stock_move as a, stock_location as b
                                     where a.location_dest_id = b.id and
                                     a.state = 'done' and
                                     a.location_dest_id = %s and
                                     (a.date + interval '7 hour')::date < %s) as a,
                                     (select sum(a.product_uom_qty) as qty_out
                                     from stock_move as a, stock_location as b
                                     where a.location_id = b.id and
                                     a.state = 'done' and
                                     a.location_id = %s and
                                     (a.date + interval '7 hour')::date < %s) as b
                                """, (location_id, line.date_from, location_id,line.date_from))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
                if val[1] != None:
                    qty_out = val[1]
            qty = qty_in - qty_out
        return qty

    @api.multi
    def get_stock_in_transit(self, location_id):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                select a.qty_in
                                 from
                                 (select sum(a.product_uom_qty) as qty_in
                                 from
                                 stock_move as a, stock_location as b
                                 where
                                 a.location_id = b.id and
                                 a.location_dest_id = %s and
                                 a.state = 'done' and
                                 b.usage in ('transit') and
                                 (a.date + interval '7 hour')::date between %s and %s) as a
                               """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_in_non_transit(self, location_id):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                    select a.qty_in
                                     from
                                     (select sum(a.product_uom_qty) as qty_in
                                     from
                                     stock_move as a, stock_location as b
                                     where
                                     a.location_id = b.id and
                                     a.location_dest_id = %s and
                                     a.state = 'done' and
                                     b.usage in ('internal') and
                                     (a.date + interval '7 hour')::date between %s and %s) as a
                                   """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_in_adjustment(self, location_id):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                    select a.qty_in
                                     from
                                     (select sum(a.product_uom_qty) as qty_in
                                     from
                                     stock_move as a, stock_location as b
                                     where
                                     a.location_id = b.id and
                                     a.location_dest_id = %s and
                                     a.state = 'done' and
                                     b.id = 5 and
                                     (a.date + interval '7 hour')::date between %s and %s) as a
                                   """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_in_transit2(self, location_id):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                    select a.qty_in
                                     from
                                     (select sum(a.product_uom_qty) as qty_in
                                     from
                                     stock_move as a, stock_location as b
                                     where
                                     a.location_id = b.id and
                                     a.location_dest_id = %s and
                                     a.state = 'done' and
                                     b.usage in ('supplier') and
                                     (a.date + interval '7 hour')::date between %s and %s) as a
                                   """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_in_transit2_non(self, location_id):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                        select a.qty_in
                                         from
                                         (select sum(a.product_uom_qty) as qty_in
                                         from
                                         stock_move as a, stock_location as b
                                         where
                                         a.location_id = b.id and
                                         a.location_dest_id = %s and
                                         a.state = 'done' and
                                         b.usage in ('internal') and
                                         (a.date + interval '7 hour')::date between %s and %s) as a
                                       """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_in_adjustment2(self, location_id):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                        select a.qty_in
                                         from
                                         (select sum(a.product_uom_qty) as qty_in
                                         from
                                         stock_move as a, stock_location as b
                                         where
                                         a.location_id = b.id and
                                         a.location_dest_id = %s and
                                         a.state = 'done' and
                                         b.id = 5 and
                                         (a.date + interval '7 hour')::date between %s and %s) as a
                                       """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_out_transit(self, location_id):
        cursor = self.env.cr
        qty_out = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                  select a.qty_out
                                         from
                                         (select sum(a.product_uom_qty) as qty_out
                                         from
                                         stock_move as a, stock_location as b
                                         where
                                         a.location_dest_id = b.id and
                                         a.location_id = %s and
                                         a.state = 'done' and
                                         b.usage in ('transit') and
                                         (a.date + interval '7 hour')::date between %s and %s) as a
                                   """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_out = val[0]
        return qty_out

    @api.multi
    def get_stock_out_transit_non(self, location_id):
        cursor = self.env.cr
        qty_out = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                     select a.qty_out
                                            from
                                            (select sum(a.product_uom_qty) as qty_out
                                            from
                                            stock_move as a, stock_location as b
                                            where
                                            a.location_dest_id = b.id and
                                            a.location_id = %s and
                                            a.state = 'done' and
                                            b.usage in ('internal') and
                                            (a.date + interval '7 hour')::date between %s and %s) as a
                                      """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_out = val[0]
        return qty_out

    @api.multi
    def get_stock_out_adjustment(self, location_id):
        cursor = self.env.cr
        qty_out = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                      select a.qty_out
                                             from
                                             (select sum(a.product_uom_qty) as qty_out
                                             from
                                             stock_move as a, stock_location as b
                                             where
                                             a.location_dest_id = b.id and
                                             a.location_id = %s and
                                             a.state = 'done' and
                                             b.id = 5 and
                                             (a.date + interval '7 hour')::date between %s and %s) as a
                                       """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_out = val[0]
        return qty_out

    @api.multi
    def get_stock_out_sale(self, location_id):
        cursor = self.env.cr
        qty_out = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                     select a.qty_out
                                            from
                                            (select sum(a.product_uom_qty) as qty_out
                                            from
                                            stock_move as a, stock_location as b
                                            where
                                            a.location_dest_id = b.id and
                                            a.location_id = %s and
                                            a.state = 'done' and
                                            b.usage in ('customer') and
                                            (a.date + interval '7 hour')::date between %s and %s) as a
                                      """, (location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_out = val[0]
        return qty_out

class report_replenishment_wizard(models.TransientModel):
    _name = 'report.replenishment.wizard'

    company         = fields.Many2one('res.company', 'Company')
    period_id       = fields.Many2one('account.period', 'Period')
    wh_type         = fields.Selection([('LS', 'Store'),
                                 ('LC', 'Consigment'),
                                 ('TP', 'Toko Putus'),
                                 ('CP', 'Consigment'),
                                 ('MW', 'MAIN WH'),
                             ],string='WH Type')
    date_from       = fields.Date('Date From')
    date_to         = fields.Date('Date To')
    data            = fields.Binary('File', readonly=True)
    name            = fields.Char('Filename', readonly=True)
    state_position  = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    location_ids2   = fields.Many2many('stock.warehouse',string='Warehouse')
    location_main_wh_ids2 = fields.Many2many('stock.location', string='Location Main WH')
    product_category_ids2 = fields.Many2many('lea.product.category', string='Product Category')
    article_ids     = fields.Many2many('product.category', string='Article')
    class_category_ids  = fields.Many2many('lea.product.class.category', string='Class Category')
    is_stock_awal       = fields.Boolean('Stock Awal', default=True)
    is_stock_sale       = fields.Boolean('Stock Sale', default=True)
    is_stock_retur      = fields.Boolean('Stock Retur', default=True)
    is_stock_akhir      = fields.Boolean('Stock Akhir', default=True)
    is_stock_in         = fields.Boolean('Stock Masuk', default=True)
    is_stock_gudang     = fields.Boolean('Stock Gudang', default=True)
    line_ids            = fields.One2many('replenishment.wizard.line', 'reference', string="Analisa Stock Replenishment")
    user_pds_id         = fields.Many2one('res.users', 'User PDS', default=lambda self: self.env.user.id)

    @api.multi
    @api.onchange('user_pds_id')
    def onchange_user_pds_id(self):
        user = []
        if self.user_pds_id:
            return {'domain': {'location_ids2': [('responsible_id', 'in', [self.user_pds_id.id])]}}

    @api.multi
    @api.onchange('period_id')
    def onchange_period_id(self):
        values = {
            'date_from': '',
            'date_to': '',
        }
        if self.period_id:
            values['date_from'] = self.period_id.date_start
            values['date_to'] = self.period_id.date_stop
        self.update(values)


    @api.multi
    @api.onchange('wh_type')
    def onchange_wh_type(self):
        list = []
        values = {
            'location_ids2': list,

        }
        if self.wh_type:
            loc = self.env['stock.warehouse'].search([('wh_type', '=', self.wh_type)])
            for l in loc:
                list.append(l.id)
            values['location_ids2'] = list
        self.update(values)



    @api.multi
    def generate_report_excel_old(self):
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'Analisa Stock Replenishment Per - Toko' + '_' + self.company.name + '.xlsx'
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

        worksheet1.set_column('A:A', 30)
        worksheet1.set_column('B:B', 15)
        worksheet1.set_column('C:C', 15)
        worksheet1.set_column('D:D', 15)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_column('F:F', 15)
        worksheet1.set_column('G:BZ',5)
        worksheet1.set_row(0, 30)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.merge_range('A1:J1', self.company.name, center_title)
        worksheet1.merge_range('A2:J2', 'Analisa Replenishment Per Toko', center_title)
        worksheet1.merge_range('A3:J3', date_from + ' s/d ' + date_to, center_title)
        ###Header Size#####
        size = []
        info_stock = []
        if self.is_stock_awal == True :
            info_stock.append(['STOCK AWAL',1])
        if self.is_stock_sale == True :
            info_stock.append(['SALE',2])
        if self.is_stock_retur == True :
            info_stock.append(['RETUR',3])
        if self.is_stock_akhir == True :
            info_stock.append(['STOCK AKHIR',4])
        if self.is_stock_gudang == True :
            info_stock.append(['STOCK GUDANG',5])
        if self.is_stock_in == True :
            info_stock.append(['STOCK MASUK',6])

        size_ids = self.env['lea.product.size'].search([])
        for s in size_ids:
            size.append([s.id,s.name])


        worksheet1.write(7, 0, 'Product Category', header_table)
        worksheet1.write(7, 1, 'Article Code', header_table)
        worksheet1.write(7, 2, 'Detail', header_table)
        worksheet1.write(7, 3, 'Warehouse', header_table)
        worksheet1.write(7, 4, 'Warehouse Name', header_table)
        worksheet1.write(7, 5, 'Status', header_table)
        col = 6
        if len(size) > 0 :
            for hs in size:
                worksheet1.write(7, col, hs[1], header_table)
                col = col + 1
        row = 8
        cursor = self.env.cr
        for wh in self.location_ids2 :
            for ar in self.article_ids :
                for inf in info_stock:
                    #product_article_ids = self.env['product.product'].search([('product_class_category_id', '=', ar.id)])
                    worksheet1.write(row, 0, '', set_border_bold)
                    worksheet1.write(row, 1, ar.name, set_border_bold)
                    worksheet1.write(row, 2, inf[0], set_border_bold)
                    worksheet1.write(row, 3, '', set_border_bold)
                    worksheet1.write(row, 4, wh.name, set_border_bold)
                    worksheet1.write(row, 5, '', set_border_bold)
                    col = 6
                    for hs in size_ids:
                        stock_awal_gudang = 0
                        stock_awal_toko   = 0
                        stock_sale        = 0
                        stock_retur       = 0
                        stock_in          = 0

                        product_ids = self.env['product.product'].search([('product_size_id','=',hs.id),('categ_id','=',ar.id)])
                        if product_ids:
                            for p in product_ids:
                                for l in self.location_main_wh_ids2:
                                    sa = self.get_stock_awal(l.id, p.id)
                                    stock_awal_gudang = stock_awal_gudang + sa
                                st = self.get_stock_awal(wh.lot_stock_id.id, p.id)
                                ss = self.get_stock_out_sale(wh.lot_stock_id.id, p.id)
                                sr = self.get_stock_in_transit(wh.lot_stock_id.id, p.id)
                                si = self.get_stock_in(wh.lot_stock_id.id, p.id)
                                stock_awal_toko = stock_awal_toko + st
                                stock_sale = stock_sale + ss
                                stock_retur = stock_retur + sr
                                stock_in = stock_in + si

                        stock_gudang = stock_awal_gudang
                        stock_awal = stock_awal_toko
                        stock_akhir = stock_awal + stock_in + stock_retur - stock_sale

                        if inf[1] == 5:
                            worksheet1.write(row, col, stock_gudang, set_border_bold_right)

                        if inf[1] == 1:
                            worksheet1.write(row, col, stock_awal, set_border_bold_right)

                        if inf[1] == 6:
                            worksheet1.write(row, col, stock_in, set_border_bold_right)

                        if inf[1] == 2:
                            worksheet1.write(row, col, stock_sale, set_border_bold_right)

                        if inf[1] == 3:
                            worksheet1.write(row, col, stock_retur , set_border_bold_right)

                        if inf[1] == 4:
                            worksheet1.write(row, col, stock_akhir, set_border_bold_right)

                        col = col + 1
                    row = row + 1


        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference('stock_report_lea', 'report_replenishment_wizard_form')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.replenishment.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def generate_report_excel(self):
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'Analisa Stock Replenishment Per - Toko' + '_' + self.company.name + '.xlsx'
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

        worksheet1.set_column('A:A', 30)
        worksheet1.set_column('B:B', 15)
        worksheet1.set_column('C:C', 15)
        worksheet1.set_column('D:D', 15)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_column('F:F', 15)
        worksheet1.set_column('G:BZ', 5)
        worksheet1.set_row(0, 30)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.merge_range('A1:J1', self.company.name, center_title)
        worksheet1.merge_range('A2:J2', 'Analisa Replenishment Per Toko', center_title)
        worksheet1.merge_range('A3:J3', date_from + ' s/d ' + date_to, center_title)
        cursor = self.env.cr
        ###Header Size#####
        size = []
        info_stock = []
        if self.is_stock_gudang == True:
            info_stock.append(['STOCK GUDANG', 5])
        if self.is_stock_awal == True:
            info_stock.append(['STOCK AWAL', 1])
        if self.is_stock_in == True:
            info_stock.append(['STOCK MASUK', 6])
        if self.is_stock_sale == True:
            info_stock.append(['SALE', 2])
        if self.is_stock_retur == True:
            info_stock.append(['RETUR', 3])
        if self.is_stock_akhir == True:
            info_stock.append(['STOCK AKHIR', 4])



        main_wh = []
        all_loc = []
        for l in self.location_main_wh_ids2:
            main_wh.append(l.id)
            all_loc.append(l.id)

        for wh2 in self.location_ids2:
            all_loc.append(wh2.lot_stock_id.id)

        #size_ids = self.env['lea.product.size'].search([])
        cursor.execute("""
                               select
                                 c.product_size_id, d.name
                               from
                                 stock_move as a,
                                 product_product as b,
                                 product_template as c,
                                 lea_product_size as d
                               where
                                 a.product_id = b.id and
                                 b.product_tmpl_id = c.id and
                                 c.product_size_id = d.id and
                                 a.state = 'done' and
                                 (a.date + interval '7 hour')::date <= %s and
                                 (a.location_id in %s or a.location_dest_id in %s)
                                 group by c.product_size_id, d.name order by d.name asc
                               """, (self.date_to, tuple(all_loc), tuple(all_loc)))
        size_ids = cursor.fetchall()

        for s in size_ids:
            size.append([s[0], s[1]])

        worksheet1.write(7, 0, 'Product Category', header_table)
        worksheet1.write(7, 1, 'Article Code', header_table)
        worksheet1.write(7, 2, 'Detail', header_table)
        worksheet1.write(7, 3, 'Warehouse', header_table)
        worksheet1.write(7, 4, 'Warehouse Name', header_table)
        worksheet1.write(7, 5, 'Status', header_table)
        col = 6
        if len(size) > 0:
            for hs in size:
                worksheet1.write(7, col, hs[1], header_table)
                col = col + 1
        row = 8

        for wh in self.location_ids2:
            for ar in self.product_category_ids2:
                cursor.execute("""
                                    select
                                        c.categ_id
                                    from
                                        stock_move as a,
                                        product_product as b,
                                        product_template as c
                                    where
                                        a.product_id = b.id and
                                        b.product_tmpl_id = c.id and
                                        a.state = 'done' and
                                        c.product_category_id = %s and
                                        (a.date + interval '7 hour')::date <= %s and
                                        (a.location_id in %s or a.location_dest_id in %s)
                                        group by c.categ_id
                                    """, (ar.id, self.date_to, tuple(all_loc), tuple(all_loc)))
                categ = cursor.fetchall()
                for cat in categ:
                    article = self.env['product.category'].browse(cat[0])
                    for inf in info_stock:
                        # product_article_ids = self.env['product.product'].search([('product_class_category_id', '=', ar.id)])
                        worksheet1.write(row, 0, ar.name, set_border_bold)
                        worksheet1.write(row, 1, article.name, set_border_bold)
                        worksheet1.write(row, 2, inf[0], set_border_bold)
                        worksheet1.write(row, 3, '', set_border_bold)
                        if inf[1] == 5:
                            worksheet1.write(row, 4, wh.name, set_border_bold)
                        else:
                            worksheet1.write(row, 4, wh.name, set_border_bold)
                        worksheet1.write(row, 5, '', set_border_bold)
                        col = 6
                        for hs in size_ids:
                            stock_awal_gudang = 0
                            if len(main_wh) > 0:
                                stock_awal_gudang = self.get_stock_awal_new(article.id, hs[0], main_wh)
                            stock_awal_toko = self.get_stock_awal_new(article.id, hs[0], [wh.lot_stock_id.id])
                            stock_in = self.get_stock_in_new(article.id, hs[0], [wh.lot_stock_id.id])
                            stock_sale = self.get_stock_out_sale_new(article.id, hs[0], [wh.lot_stock_id.id])
                            stock_retur = self.get_stock_out_retur_new(article.id, hs[0], [wh.lot_stock_id.id])
                            stock_gudang = stock_awal_gudang
                            stock_awal = stock_awal_toko + stock_awal_gudang
                            stock_akhir = stock_awal + stock_in - stock_retur - stock_sale

                            if inf[1] == 5:
                                if stock_gudang == 0:
                                    worksheet1.write(row, col, '', set_border_bold_right)
                                else:
                                    worksheet1.write(row, col, stock_gudang, set_border_bold_right)

                            if inf[1] == 1:
                                if stock_awal == 0:
                                    worksheet1.write(row, col, '', set_border_bold_right)
                                else:
                                    worksheet1.write(row, col, stock_awal, set_border_bold_right)

                            if inf[1] == 6:
                                if stock_in == 0:
                                    worksheet1.write(row, col, '', set_border_bold_right)
                                else:
                                    worksheet1.write(row, col, stock_in, set_border_bold_right)

                            if inf[1] == 2:
                                if stock_sale == 0:
                                    worksheet1.write(row, col, '', set_border_bold_right)
                                else:
                                    worksheet1.write(row, col, stock_sale, set_border_bold_right)

                            if inf[1] == 3:
                                if stock_retur == 0:
                                    worksheet1.write(row, col, '', set_border_bold_right)
                                else:
                                    worksheet1.write(row, col, stock_retur, set_border_bold_right)

                            if inf[1] == 4:
                                if stock_akhir == 0:
                                    worksheet1.write(row, col, '', set_border_bold_right)
                                else:
                                    worksheet1.write(row, col, stock_akhir, set_border_bold_right)

                            col = col + 1
                        row = row + 1
                    row = row + 1
        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference('stock_report_lea', 'report_replenishment_wizard_form')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.replenishment.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_stock_awal_new(self, categ_id, size_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_to = line.date_from
            if categ_id and size_id and location_ids and date_to:
                cursor.execute("""
                                     select
                                     a.qty_in - b.qty_out as balance_qty
                                     from
                                     (select sum(a.product_uom_qty) as qty_in
                                     from
                                     stock_move as a, stock_location as b, product_product as c, product_template as d
                                     where a.location_dest_id = b.id and
                                     a.product_id = c.id and
                                     c.product_tmpl_id = d.id and
                                     a.state = 'done' and
                                     d.categ_id = %s and
                                     d.product_size_id = %s and
                                     a.location_dest_id in %s and
                                     (a.date + interval '7 hour')::date < %s) as a,
                                     (select sum(a.product_uom_qty) as qty_out
                                     from stock_move as a, stock_location as b, product_product as c, product_template as d
                                     where a.location_id = b.id and
                                     a.product_id = c.id and
                                     c.product_tmpl_id = d.id and
                                     a.state = 'done' and
                                     d.categ_id = %s and
                                     d.product_size_id = %s and
                                     a.location_id in %s and
                                     (a.date + interval '7 hour')::date < %s) as b
                                   """, (categ_id, size_id, tuple(location_ids), date_to, categ_id,size_id, tuple(location_ids), date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_in_new(self, categ_id, size_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.date_from
            date_to = line.date_from
            if categ_id and size_id and location_ids and date_to:
                cursor.execute("""
                                         select sum(a.product_uom_qty) as qty_in
                                         from
                                         stock_move as a, stock_location as b, product_product as c, product_template as d
                                         where a.location_dest_id = b.id and
                                         a.product_id = c.id and
                                         c.product_tmpl_id = d.id and
                                         a.state = 'done' and
                                         d.categ_id = %s and
                                         d.product_size_id = %s and
                                         a.location_dest_id in %s and
                                         (a.date + interval '7 hour')::date between %s and %s
                                       """, (categ_id, size_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_out_sale_new(self, categ_id, size_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.date_from
            date_to = line.date_from
            if categ_id and size_id and location_ids and date_to:
                cursor.execute("""
                                            select sum(a.product_uom_qty) as qty_out
                                            from
                                            stock_move as a, stock_location as b, product_product as c, product_template as d
                                            where
                                            a.location_dest_id = b.id and
                                            a.product_id = c.id and
                                            c.product_tmpl_id = d.id and
                                            a.state = 'done' and
                                            d.categ_id = %s and
                                            d.product_size_id = %s and
                                            a.location_id in %s and
                                            b.usage = 'customer' and
                                            (a.date + interval '7 hour')::date between %s and %s
                                          """,
                               (categ_id, size_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_out_retur_new(self, categ_id, size_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.date_from
            date_to = line.date_from
            if categ_id and size_id and location_ids and date_to:
                cursor.execute("""
                                                select sum(a.product_uom_qty) as qty_out
                                                from
                                                stock_move as a, stock_location as b, product_product as c, product_template as d
                                                where
                                                a.location_dest_id = b.id and
                                                a.product_id = c.id and
                                                c.product_tmpl_id = d.id and
                                                a.state = 'done' and
                                                d.categ_id = %s and
                                                d.product_size_id = %s and
                                                a.location_id in %s and
                                                b.usage != 'customer' and
                                                (a.date + interval '7 hour')::date between %s and %s
                                              """,
                               (categ_id, size_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty


    @api.multi
    def get_stock_awal(self, location_id, product_id):
        cursor = self.env.cr
        qty_in = 0
        qty_out = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                       select a.qty_in, b.qty_out
                                       from
                                       (select sum(a.product_uom_qty) as qty_in
                                       from
                                       stock_move as a, stock_location as b
                                       where a.location_dest_id = b.id and
                                       a.state = 'done' and
                                       b.id = %s and
                                       a.location_id != %s and
                                       a.product_id = %s and
                                       (a.date + interval '7 hour')::date < %s) as a,
                                       (select
                                       sum(a.product_uom_qty) as qty_out
                                       from stock_move as a, stock_location as b
                                       where a.location_id = b.id and
                                       a.state = 'done' and
                                       b.id = %s and
                                       a.location_dest_id != %s and
                                       a.product_id = %s and
                                       (a.date + interval '7 hour')::date < %s) as b
                                    """, (location_id, location_id, product_id, line.date_from, location_id, location_id,  product_id, line.date_from))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
                if val[1] != None:
                    qty_out = val[1]
            qty = qty_in - qty_out
        return qty

    @api.multi
    def get_stock_out_sale(self, location_id, product_id):
        cursor = self.env.cr
        qty_out = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                       select a.qty_out
                                              from
                                              (select sum(a.product_uom_qty) as qty_out
                                              from
                                              stock_move as a, stock_location as b
                                              where
                                              a.location_dest_id = b.id and
                                              a.location_id = %s and
                                              a.product_id = %s and
                                              a.state = 'done' and
                                              b.usage = 'customer' and
                                              (a.date + interval '7 hour')::date between %s and %s) as a
                                        """, (location_id, product_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_out = val[0]
        return qty_out

    @api.multi
    def get_stock_in_transit(self, location_id, product_id):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                    select a.qty_in
                                     from
                                     (select sum(a.product_uom_qty) as qty_in
                                     from
                                     stock_move as a, stock_location as b
                                     where
                                     a.location_id = b.id and
                                     a.location_dest_id = %s and
                                     a.product_id = %s and
                                     a.state = 'done' and
                                     b.usage = 'transit' and
                                     (a.date + interval '7 hour')::date between %s and %s) as a
                                   """, (location_id, product_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_in(self, location_id, product_id):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from:
                cursor.execute("""
                                        select a.qty_in
                                         from
                                         (select sum(a.product_uom_qty) as qty_in
                                         from
                                         stock_move as a, stock_location as b
                                         where
                                         a.location_id = b.id and
                                         a.location_dest_id = %s and
                                         a.product_id = %s and
                                         a.state = 'done' and
                                         b.usage not in ('transit') and
                                         (a.date + interval '7 hour')::date between %s and %s) as a
                                       """, (location_id, product_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def generate_report_old(self):
        location = []
        all_location = []
        location_main_wh = []

        stop = self.date_to
        cursor = self.env.cr
        line_obj = self.env['replenishment.wizard.line']

        for mwh in self.location_main_wh_ids2:
            location_main_wh.append(mwh.id)
            all_location.append(mwh.id)

        for wh in self.location_ids2:
            location.append(wh.lot_stock_id.id)
            all_location.append(wh.lot_stock_id.id)

        article = []
        for a in self.product_category_ids2 :
            article.append(a.id)

        cursor.execute("""
                        select
                            a.product_id
                        from
                            stock_move as a,
                            product_product as b,
                            product_template as c
                        where
                            a.product_id = b.id and
                            b.product_tmpl_id = c.id and
                            a.state = 'done' and
                            (a.date + interval '7 hour')::date <= %s and
                            (a.location_id in %s or a.location_dest_id in %s) and
                            c.product_category_id in %s
                            group by a.product_id
                       """, (stop, tuple(all_location), tuple(all_location), tuple(article)))
        res_ids = cursor.fetchall()

        for prod in res_ids :
            product = self.env['product.product'].browse(prod[0])
            stock_awal = self.get_stock_awal_new2(prod[0],location)
            stock_in   = self.get_stock_in_new2(prod[0],location)
            stock_retur = self.get_stock_out_retur_new2(prod[0],location)
            stock_sales = self.get_stock_out_sale_new2(prod[0],location)
            stock_akhir = stock_awal + stock_in - stock_retur - stock_sales
            stock_akhir_gudang = self.get_stock_akhir_gudang_new2(prod[0],location_main_wh)

            if stock_awal + stock_in + stock_retur + stock_sales + stock_akhir+ stock_akhir_gudang != 0 :
                for  wh in self.location_ids2:
                    stock_awal_wh = self.get_stock_awal_new2(prod[0], [wh.lot_stock_id.id])
                    stock_in_wh = self.get_stock_in_new2(prod[0], [wh.lot_stock_id.id])
                    stock_retur_wh = self.get_stock_out_retur_new2(prod[0], [wh.lot_stock_id.id])
                    stock_sales_wh = self.get_stock_out_sale_new2(prod[0], [wh.lot_stock_id.id])
                    stock_akhir_wh = stock_awal_wh + stock_in_wh - stock_retur_wh - stock_sales_wh
                    if stock_awal_wh + stock_in_wh + stock_retur_wh + stock_sales_wh + stock_akhir_wh != 0:
                        line_vals = {
                            'reference': self.id,
                            'mv_id': product.product_moving_status_id.id,
                            'class_category_id': product.product_class_category_id.id,
                            'category_id': product.product_category_id.id,
                            'categ_id': product.categ_id.id,
                            'product_id': prod[0],
                            'stock_awal': stock_awal_wh,
                            'stock_in': stock_in_wh,
                            'stock_retur': stock_retur_wh,
                            'stock_sale': stock_sales_wh,
                            'stock_akhir': stock_akhir_wh,
                            'stock_gudang': stock_akhir_gudang,
                            'warehouse_id':wh.id,
                            'location_id': wh.lot_stock_id.id,
                        }
                        # data.append(line_vals)
                        line_obj.create(line_vals)

        # raise Warning(data)
        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        title = 'Stock Replenishment Toko ' + str(date_from) + ' s/d ' + str(date_to)
        return {
            'name': (title),
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'replenishment.wizard.line',
            'domain': [('reference', '=', self.id)],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def generate_report(self):
        location = []
        all_location = []
        location_main_wh = []
        stop = self.date_to
        cursor = self.env.cr
        line_obj = self.env['replenishment.wizard.line']

        for mwh in self.location_main_wh_ids2:
            location_main_wh.append(mwh.id)
            all_location.append(mwh.id)

        for wh in self.location_ids2:
            location.append(wh.lot_stock_id.id)
            all_location.append(wh.lot_stock_id.id)

        article = []
        for a in self.product_category_ids2:
            article.append(a.id)

        cursor.execute("""
                            select
                                a.product_id
                            from
                                stock_move as a,
                                product_product as b,
                                product_template as c
                            where
                                a.product_id = b.id and
                                b.product_tmpl_id = c.id and
                                a.state = 'done' and
                                (a.date + interval '7 hour')::date <= %s and
                                (a.location_id in %s or a.location_dest_id in %s) and
                                c.product_category_id in %s
                                group by a.product_id
                           """, (stop, tuple(all_location), tuple(all_location), tuple(article)))
        res_ids = cursor.fetchall()

        for prod in res_ids:
            product = self.env['product.product'].browse(prod[0])
            #stock_awal = self.get_stock_awal_new2(prod[0], location)
            #stock_in = self.get_stock_in_new2(prod[0], location)
            #stock_retur = self.get_stock_out_retur_new2(prod[0], location)
            #stock_sales = self.get_stock_out_sale_new2(prod[0], location)
            #stock_akhir = stock_awal + stock_in - stock_retur - stock_sales
            stock_akhir_gudang = self.get_stock_akhir_gudang_new2(prod[0], location_main_wh)
            #if stock_awal + stock_in + stock_retur + stock_sales + stock_akhir + stock_akhir_gudang != 0:
            for wh in self.location_ids2:
                stock_awal_wh = self.get_stock_awal_new2(prod[0], [wh.lot_stock_id.id])
                stock_in_wh = self.get_stock_in_new2(prod[0], [wh.lot_stock_id.id])
                stock_retur_wh = self.get_stock_out_retur_new2(prod[0], [wh.lot_stock_id.id])
                stock_sales_wh = self.get_stock_out_sale_new2(prod[0], [wh.lot_stock_id.id])
                stock_akhir_wh = stock_awal_wh + stock_in_wh - stock_retur_wh - stock_sales_wh
                #if stock_awal_wh + stock_in_wh + stock_retur_wh + stock_sales_wh + stock_akhir_gudang != 0:
                if stock_akhir_wh + stock_akhir_gudang != 0 :
                    line_vals = {
                                        'reference': self.id,
                                        'mv_id': product.product_moving_status_id.id,
                                        'class_category_id': product.product_class_category_id.id,
                                        'category_id': product.product_category_id.id,
                                        'categ_id': product.categ_id.id,
                                        'product_id': prod[0],
                                        'stock_awal': stock_awal_wh,
                                        'stock_in': stock_in_wh,
                                        'stock_retur': stock_retur_wh,
                                        'stock_sale': stock_sales_wh,
                                        'stock_akhir': stock_akhir_wh,
                                        'stock_gudang': stock_akhir_gudang,
                                        'warehouse_id': wh.id,
                                        'location_id': wh.lot_stock_id.id,
                                }
                                # data.append(line_vals)
                    line_obj.create(line_vals)

        # raise Warning(data)
        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        title = 'Stock Replenishment Toko ' + str(date_from) + ' s/d ' + str(date_to)
        return {
            'name': (title),
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'replenishment.wizard.line',
            'domain': [('reference', '=', self.id)],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_stock_awal_new2(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.date_from
            if product_id and location_ids and date_from:
                cursor.execute("""
                                    select
                                         a.qty_in - b.qty_out as balance_qty
                                         from
                                         (select sum(a.product_uom_qty) as qty_in
                                         from
                                         stock_move as a, stock_location as b
                                         where a.location_dest_id = b.id and
                                         a.state = 'done' and
                                         a.product_id = %s and
                                         a.location_dest_id in %s and
                                         (a.date + interval '7 hour')::date < %s) as a,
                                         (select sum(a.product_uom_qty) as qty_out
                                         from stock_move as a, stock_location as b
                                         where a.location_id = b.id and
                                         a.state = 'done' and
                                         a.product_id = %s and
                                         a.location_id in %s and
                                         (a.date + interval '7 hour')::date < %s) as b
                                       """, (product_id, tuple(location_ids), date_from, product_id, tuple(location_ids), date_from))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_in_new2(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.date_from
            date_to = line.date_to
            if product_id and location_ids and date_to and date_from:
                cursor.execute("""
                                    select sum(a.product_uom_qty) as qty_in
                                        from
                                        stock_move as a, stock_location as b
                                        where a.location_id = b.id and
                                        a.state = 'done' and
                                        b.usage in ('transit') and
                                        a.product_id = %s and
                                        a.location_dest_id in %s and
                                        (a.date + interval '7 hour')::date between %s and %s
                                """, (product_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_out_retur_new2(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.date_from
            date_to = line.date_to
            if product_id and location_ids and date_to and date_from:
                cursor.execute("""
                                select sum(a.product_uom_qty) as qty_out
                                from
                                stock_move as a, stock_location as b
                                where
                                a.location_dest_id = b.id and
                                a.state = 'done' and
                                a.product_id = %s and
                                a.location_id in %s and
                                b.usage in ('transit') and
                                (a.date + interval '7 hour')::date between %s and %s
                             """,
                               (product_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_out_sale_new2(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.date_from
            date_to = line.date_to
            if product_id and location_ids and date_to:
                cursor.execute("""
                                               select sum(a.product_uom_qty) as qty_out
                                               from
                                               stock_move as a, stock_location as b
                                               where
                                               a.location_dest_id = b.id and
                                               a.state = 'done' and
                                               a.product_id = %s and
                                               a.location_id in %s and
                                               b.usage in ('customer') and
                                               (a.date + interval '7 hour')::date between %s and %s
                                             """,(product_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_akhir_gudang_new2(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_to = line.date_to
            if product_id and location_ids and date_to:
                cursor.execute("""
                                        select
                                             a.qty_in - b.qty_out as balance_qty
                                             from
                                             (select sum(a.product_uom_qty) as qty_in
                                             from
                                             stock_move as a, stock_location as b
                                             where a.location_dest_id = b.id and
                                             a.state = 'done' and
                                             a.product_id = %s and
                                             a.location_dest_id in %s and
                                             (a.date + interval '7 hour')::date <= %s) as a,
                                             (select sum(a.product_uom_qty) as qty_out
                                             from stock_move as a, stock_location as b
                                             where a.location_id = b.id and
                                             a.state = 'done' and
                                             a.product_id = %s and
                                             a.location_id in %s and
                                             (a.date + interval '7 hour')::date <= %s) as b
                                           """,
                               (product_id, tuple(location_ids), date_to, product_id, tuple(location_ids), date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty


class report_analisa_level_stock_wizard(models.TransientModel):
    _name = 'report.analisa.level.stock.wizard'

    company = fields.Many2one('res.company', 'Company')
    period_start = fields.Many2one('account.period', 'Period Start')
    period_stop = fields.Many2one('account.period', 'Period Stop')
    location_ids2 = fields.Many2many('stock.warehouse', string='Warehouse')
    location_main_wh_ids2 = fields.Many2many('stock.location', string='Location Main WH')
    type_pds = fields.Selection([('non-pds', 'Non PDS'), ('pds', 'PDS')], string='Type PDS')
    user_pds_id = fields.Many2one('res.users', 'User PDS', default=lambda self: self.env.user.id)
    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    @api.multi
    @api.onchange('user_pds_id')
    def onchange_account_id(self):
        user = []
        if self.user_pds_id:
            return {'domain': {'location_ids2': [('responsible_id', 'in', [self.user_pds_id.id])]}}

    @api.multi
    def generate_report_excel(self):
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'analisa_level_stock' + '_' + self.company.name + '.xlsx'
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

        worksheet1.set_column('A:A', 30)
        worksheet1.set_column('B:B', 15)
        worksheet1.set_column('C:C', 15)
        worksheet1.set_column('D:D', 15)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_column('F:F', 15)
        worksheet1.set_column('G:BZ', 5)
        worksheet1.set_row(0, 30)

        date1 = datetime.strptime(self.period_start.date_start, '%Y-%m-%d')
        date2 = datetime.strptime(self.period_stop.date_stop, '%Y-%m-%d')
        r = relativedelta.relativedelta(date2, date1)
        m = r.months + 1


        worksheet1.merge_range('A1:J1', self.company.name, center_title)
        worksheet1.merge_range('A2:J2', 'Analisa Level Stock dan Average Penjualan', center_title)
        worksheet1.merge_range('A3:J3', self.period_start.name + ' s/d ' + self.period_stop.name, center_title)
        ###Header Size#####
        moving_status = []
        location =[]
        location_main_wh = []
        all_location = []

        for mwh in self.location_main_wh_ids2:
            location_main_wh.append(mwh.id)
            all_location.append(mwh.id)


        if self.type_pds == 'non-pds':
            wh_nasional = self.env['stock.warehouse'].search([('tipe_penjualan_toko','=','jual-toko')])
            for wh in wh_nasional:
                location.append(wh.lot_stock_id.id)
                all_location.append(wh.lot_stock_id.id)
        else :
            for wh in self.location_ids2:
                location.append(wh.lot_stock_id.id)
                all_location.append(wh.lot_stock_id.id)

        mv_ids = self.env['lea.product.moving.status'].search([])
        class_category_ids = self.env['lea.product.class.category'].search([])
        for s in mv_ids:
            moving_status.append([s.id, s.name])

        #SUM OF SALE
        worksheet1.write(6, 0, 'SUM OF SALE', set_border_bold)
        worksheet1.write(7, 0, 'Article Category Code', header_table)
        col = 1
        if len(moving_status) > 0:
            for mv in moving_status:
                worksheet1.write(7, col, mv[1], header_table)
                col = col + 1
        worksheet1.write(7, col, 'Grand Total', header_table)
        row = 8
        for line in class_category_ids :
            worksheet1.write(row, 0, line.name, set_border_bold)
            col = 1
            total_sales_x =0
            for mv in moving_status:
                qty_sales = self.get_qty_sales(line.id,mv[0],all_location)
                worksheet1.write(row, col, qty_sales, set_right)
                col = col + 1
                total_sales_x = total_sales_x + qty_sales
            worksheet1.write(row, col, total_sales_x , set_border_bold_right)
            row=row+1
        worksheet1.write(row, 0, 'Grand Total', header_table)
        col = 1
        total_sales_y = 0
        if len(moving_status) > 0:
            for mv in moving_status:
                qty_sales_mv = self.get_qty_sales_mv(mv[0], all_location)
                worksheet1.write(row, col, qty_sales_mv, header_table_right)
                total_sales_y = total_sales_y + qty_sales_mv
                col = col + 1
        worksheet1.write(row, col, total_sales_y, header_table_right)

        row = row + 2

        # SUM OF STOCK AKHIR
        worksheet1.write(row, 0, 'SUM OF STOCK AKHIR', set_border_bold)
        row = row + 1
        worksheet1.write(row, 0, 'Article Category Code', header_table)
        col = 1
        if len(moving_status) > 0:
            for mv in moving_status:
                worksheet1.write(row, col, mv[1], header_table)
                col = col + 1
        worksheet1.write(row, col, 'Grand Total', header_table)
        row = row + 1
        for line in class_category_ids:
            worksheet1.write(row, 0, line.name, set_border_bold)
            col = 1
            total_inventory_x = 0
            for mv in moving_status:
                #############rumus baru#########################################################
                if self.type_pds == 'non-pds':
                    qty_awal = self.get_qty_awal_new(line.id, mv[0],all_location)
                    qty_in   = self.get_qty_in_new2(line.id, mv[0],location_main_wh)
                    qty_sale = self.get_qty_sales(line.id,mv[0],all_location)
                else:
                    qty_awal = self.get_qty_awal_new(line.id, mv[0],location)
                    qty_in = self.get_qty_in_new(line.id, mv[0],location)
                    qty_sale = self.get_qty_sales(line.id,mv[0],location)

                qty_akhir_inv = qty_awal + qty_in - qty_sale

                worksheet1.write(row, col, qty_akhir_inv, set_right)
                total_inventory_x = total_inventory_x + qty_akhir_inv
                col = col + 1
            worksheet1.write(row, col, total_inventory_x, set_border_bold_right)
            row = row + 1

        worksheet1.write(row, 0, 'Grand Total', header_table)
        col = 1
        total_inventory_y = 0
        if len(moving_status) > 0:
            for mv in moving_status:
                #rumus baru
                if self.type_pds == 'non-pds':
                    qty_awal_mv = self.get_qty_awal_new_mv(mv[0],all_location)
                    qty_in_mv   = self.get_qty_in_new2_mv(mv[0],location_main_wh)
                    qty_sale_mv = self.get_qty_sales_mv(mv[0],all_location)
                else:
                    qty_awal_mv = self.get_qty_awal_new_mv(mv[0],location)
                    qty_in_mv = self.get_qty_in_new_mv(mv[0],location)
                    qty_sale_mv = self.get_qty_sales_mv(mv[0],location)

                qty_akhir_inv_mv = qty_awal_mv + qty_in_mv - qty_sale_mv


                worksheet1.write(row, col, qty_akhir_inv_mv, header_table_right)
                col = col + 1
                total_inventory_y = total_inventory_y + qty_akhir_inv_mv
        worksheet1.write(row, col, total_inventory_y, header_table_right)
        row = row + 2

        # AVERAGE SALE
        worksheet1.write(row, 0, 'AVERAGE SALE', set_border_bold)
        row = row + 1
        worksheet1.write(row, 0, 'Article Category Code', header_table)
        col = 1
        if len(moving_status) > 0:
            for mv in moving_status:
                worksheet1.write(row, col, mv[1], header_table)
                col = col + 1
        worksheet1.write(row, col, 'Grand Total', header_table)
        row = row + 1
        for line in class_category_ids:
            worksheet1.write(row, 0, line.name, set_border_bold)
            col = 1
            total_average_sales_x = 0
            for mv in moving_status:
                qty_sales_average = 0
                if m > 0 :
                    qty_sales_average = self.get_qty_sales(line.id, mv[0], all_location)/float(m)
                worksheet1.write(row, col, qty_sales_average, set_right)
                total_average_sales_x = total_average_sales_x + qty_sales_average
                col = col + 1
            worksheet1.write(row, col, total_average_sales_x, set_border_bold_right)
            row = row + 1

        worksheet1.write(row, 0, 'Grand Total', header_table)
        col = 1
        total_average_sales_y = 0
        if len(moving_status) > 0:
            for mv in moving_status:
                qty_average_sales_mv = 0
                if m > 0:
                    qty_average_sales_mv = self.get_qty_sales_mv(mv[0], all_location)/float(m)
                worksheet1.write(row, col, qty_average_sales_mv, header_table_right)
                total_average_sales_y = total_average_sales_y + qty_average_sales_mv
                col = col + 1
        worksheet1.write(row, col, total_average_sales_y, header_table_right)

        row = row + 2

        # STOCK LEVEL
        worksheet1.write(row, 0, 'STOCK LEVEL', set_border_bold)
        row = row + 1
        worksheet1.write(row, 0, 'Article Category Code', header_table)
        col = 1
        if len(moving_status) > 0:
            for mv in moving_status:
                worksheet1.write(row, col, mv[1], header_table)
                col = col + 1
        worksheet1.write(row, col, 'Grand Total', header_table)
        row = row + 1
        for line in class_category_ids:
            worksheet1.write(row, 0, line.name, set_border_bold)
            col = 1
            total_average_akhir_x = 0
            for mv in moving_status:
                if self.type_pds == 'non-pds':
                    qty_awal = self.get_qty_awal_new(line.id, mv[0],all_location)
                    qty_in   = self.get_qty_in_new2(line.id, mv[0],location_main_wh)
                    qty_sale = self.get_qty_sales(line.id,mv[0],all_location)
                else:
                    qty_awal = self.get_qty_awal_new(line.id, mv[0],location)
                    qty_in = self.get_qty_in_new(line.id, mv[0],location)
                    qty_sale = self.get_qty_sales(line.id,mv[0],location)
                qty_akhir_inv = qty_awal + qty_in - qty_sale
                qty_sales_average = 0
                qty_akhir_average = 0
                if m > 0:
                    qty_sales_average = self.get_qty_sales(line.id, mv[0], all_location) / float(m)
                if qty_sales_average > 0 :
                    qty_akhir_average = qty_akhir_inv / float(qty_sales_average)

                worksheet1.write(row, col, qty_akhir_average, set_right)
                total_average_akhir_x = total_average_akhir_x + qty_akhir_average
                col = col + 1
            worksheet1.write(row, col, total_average_akhir_x, set_border_bold_right)
            row = row + 1

        worksheet1.write(row, 0, 'Grand Total', header_table)
        col = 1
        total_average_akhir_y = 0
        if len(moving_status) > 0:
            for mv in moving_status:
                if self.type_pds == 'non-pds':
                    qty_awal_mv = self.get_qty_awal_new_mv(mv[0],all_location)
                    qty_in_mv   = self.get_qty_in_new2_mv(mv[0],location_main_wh)
                    qty_sale_mv = self.get_qty_sales_mv(mv[0],all_location)
                else:
                    qty_awal_mv = self.get_qty_awal_new_mv(mv[0],location)
                    qty_in_mv = self.get_qty_in_new_mv(mv[0],location)
                    qty_sale_mv = self.get_qty_sales_mv(mv[0],location)
                qty_akhir_inv_mv = qty_awal_mv + qty_in_mv - qty_sale_mv
                qty_average_sales_mv = 0
                qty_akhir_average_mv = 0
                if m > 0:
                    qty_average_sales_mv = self.get_qty_sales_mv(mv[0], location) / float(m)
                if qty_average_sales_mv > 0 :
                    qty_akhir_average_mv = qty_akhir_inv_mv / float(qty_average_sales_mv)
                worksheet1.write(row, col, qty_akhir_average_mv, header_table_right)
                total_average_akhir_y = total_average_akhir_y + qty_akhir_average_mv
                col = col + 1
        worksheet1.write(row, col, total_average_akhir_y, header_table_right)

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference('stock_report_lea', 'report_analisa_level_stock_form')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.analisa.level.stock.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_qty_sales(self, class_category, move_status, location_ids):
        cursor = self.env.cr
        qty    = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if class_category and move_status and location_ids and date_from and date_to :
                cursor.execute("""
                                select a.qty_out
                                from
                                (select sum(a.product_uom_qty) as qty_out
                                from
                                stock_move as a, stock_location as b, product_product as c, product_template as d
                                where
                                a.location_dest_id = b.id and
                                a.product_id = c.id and
                                c.product_tmpl_id = d.id and
                                d.product_class_category_id = %s and
                                d.product_moving_status_id = %s and
                                a.location_id in %s and
                                a.state = 'done' and
                                b.usage = 'customer' and
                                (a.date + interval '7 hour')::date between %s and %s) as a
                             """, (class_category, move_status, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_sales_mv(self, move_status, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if move_status and location_ids and date_from and date_to:
                cursor.execute("""
                                    select a.qty_out
                                    from
                                    (select sum(a.product_uom_qty) as qty_out
                                    from
                                    stock_move as a, stock_location as b, product_product as c, product_template as d
                                    where
                                    a.location_dest_id = b.id and
                                    a.product_id = c.id and
                                    c.product_tmpl_id = d.id and
                                    d.product_moving_status_id = %s and
                                    a.location_id in %s and
                                    a.state = 'done' and
                                    b.usage = 'customer' and
                                    (a.date + interval '7 hour')::date between %s and %s) as a
                                 """, (move_status, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_final_inventory(self, class_category,  move_status, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_to = line.period_stop.date_stop
            if class_category and move_status and location_ids  and date_to:
                cursor.execute("""
                                 select
                                 a.qty_in - b.qty_out as balance_qty
                                 from
                                 (select sum(a.product_uom_qty) as qty_in
                                 from
                                 stock_move as a, stock_location as b, product_product as c, product_template as d
                                 where a.location_dest_id = b.id and
                                 a.product_id = c.id and
                                 c.product_tmpl_id = d.id and
                                 a.state = 'done' and
                                 d.product_class_category_id = %s and
                                 d.product_moving_status_id = %s and
                                 b.id in %s and
                                 a.location_id not in %s and
                                 (a.date + interval '7 hour')::date <= %s) as a,
                                 (select sum(a.product_uom_qty) as qty_out
                                 from stock_move as a, stock_location as b, product_product as c, product_template as d
                                 where a.location_id = b.id and
                                 a.product_id = c.id and
                                 c.product_tmpl_id = d.id and
                                 a.state = 'done' and
                                 d.product_class_category_id = %s and
                                 d.product_moving_status_id = %s and
                                 b.id in %s and
                                 a.location_dest_id not in %s and
                                 (a.date + interval '7 hour')::date <= %s) as b
                               """, (class_category, move_status, tuple(location_ids), tuple(location_ids), date_to, class_category, move_status, tuple(location_ids), tuple(location_ids), date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_final_inventory_mv(self, move_status, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_to = line.period_stop.date_stop
            if move_status and location_ids and date_to:
                cursor.execute("""
                                    select
                                    a.qty_in - b.qty_out as balance_qty
                                    from
                                    (select sum(a.product_uom_qty) as qty_in
                                    from
                                    stock_move as a, stock_location as b, product_product as c, product_template as d
                                    where a.location_dest_id = b.id and
                                    a.product_id = c.id and
                                    c.product_tmpl_id = d.id and
                                    a.state = 'done' and
                                    d.product_moving_status_id = %s and
                                    b.id in %s and
                                    a.location_id not in %s and
                                    (a.date + interval '7 hour')::date <= %s) as a,
                                    (select sum(a.product_uom_qty) as qty_out
                                    from stock_move as a, stock_location as b, product_product as c, product_template as d
                                    where a.location_id = b.id and
                                    a.product_id = c.id and
                                    c.product_tmpl_id = d.id and
                                    a.state = 'done' and
                                    d.product_moving_status_id = %s and
                                    b.id in %s and
                                    a.location_dest_id not in %s and
                                    (a.date + interval '7 hour')::date <= %s) as b
                                  """, (move_status, tuple(location_ids), tuple(location_ids), date_to, move_status, tuple(location_ids), tuple(location_ids), date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_awal_new(self,class_category, move_status, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_to = line.period_start.date_start
            if move_status and location_ids and date_to and class_category:
                cursor.execute("""
                                select
                                    a.qty_in - b.qty_out as balance_qty
                                    from
                                    (select sum(a.product_uom_qty) as qty_in
                                    from
                                    stock_move as a, stock_location as b, product_product as c, product_template as d
                                    where a.location_dest_id = b.id and
                                    a.product_id = c.id and
                                    c.product_tmpl_id = d.id and
                                    a.state = 'done' and
                                    d.product_class_category_id = %s and
                                    d.product_moving_status_id = %s and

                                    b.id in %s and
                                    a.location_id not in %s and
                                    (a.date + interval '7 hour')::date < %s) as a,

                                    (select sum(a.product_uom_qty) as qty_out
                                    from stock_move as a, stock_location as b, product_product as c, product_template as d
                                    where a.location_id = b.id and
                                    a.product_id = c.id and
                                    c.product_tmpl_id = d.id and
                                    a.state = 'done' and
                                    d.product_class_category_id = %s and
                                    d.product_moving_status_id = %s and

                                    b.id in %s and
                                    a.location_dest_id not in %s and
                                    (a.date + interval '7 hour')::date < %s) as b
                                """, (class_category, move_status, tuple(location_ids), tuple(location_ids), date_to, class_category, move_status, tuple(location_ids), tuple(location_ids), date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_awal_new_mv(self, move_status, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_to = line.period_start.date_start
            if move_status and location_ids and date_to:
                cursor.execute("""
                                    select
                                        a.qty_in - b.qty_out as balance_qty
                                        from
                                        (select sum(a.product_uom_qty) as qty_in
                                        from
                                        stock_move as a, stock_location as b, product_product as c, product_template as d
                                        where a.location_dest_id = b.id and
                                        a.product_id = c.id and
                                        c.product_tmpl_id = d.id and
                                        a.state = 'done' and

                                        d.product_moving_status_id = %s and

                                        b.id in %s and
                                        a.location_id not in %s and
                                        (a.date + interval '7 hour')::date < %s) as a,

                                        (select sum(a.product_uom_qty) as qty_out
                                        from stock_move as a, stock_location as b, product_product as c, product_template as d
                                        where a.location_id = b.id and
                                        a.product_id = c.id and
                                        c.product_tmpl_id = d.id and
                                        a.state = 'done' and

                                        d.product_moving_status_id = %s and

                                        b.id in %s and
                                        a.location_dest_id not in %s and
                                        (a.date + interval '7 hour')::date < %s) as b
                                    """, (move_status, tuple(location_ids), tuple(location_ids), date_to, move_status, tuple(location_ids), tuple(location_ids), date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_in_new2(self, class_category, move_status, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if  move_status and location_ids and date_to  and date_from and class_category:
                cursor.execute("""
                                          select
                                              a.qty_in
                                          from
                                              (select sum(a.product_uom_qty) as qty_in
                                          from
                                              stock_move as a, stock_location as b, product_product as c, product_template as d
                                          where
                                               a.location_id = b.id and
                                               a.product_id = c.id and
                                               c.product_tmpl_id = d.id and
                                               a.state = 'done' and
                                               d.product_class_category_id = %s and
                                               d.product_moving_status_id = %s and
                                               b.usage in ('supplier') and
                                               a.location_dest_id in %s and
                                               a.location_id not in %s and
                                              (a.date + interval '7 hour')::date between %s and %s) as a
                                         """, (class_category, move_status, tuple(location_ids), tuple(location_ids), date_from,date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_in_new(self, class_category, move_status, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if move_status and location_ids and date_to and date_from and class_category :
                cursor.execute("""
                                             select
                                                 a.qty_in
                                             from
                                                 (select sum(a.product_uom_qty) as qty_in
                                             from
                                                 stock_move as a, stock_location as b, product_product as c, product_template as d
                                             where
                                                  a.location_id = b.id and
                                                  a.product_id = c.id and
                                                  c.product_tmpl_id = d.id and
                                                  a.state = 'done' and
                                                  d.product_class_category_id = %s and
                                                  d.product_moving_status_id = %s and
                                                  b.usage in ('transit') and
                                                  a.location_dest_id in %s and
                                                  a.location_id not in %s and
                                                 (a.date + interval '7 hour')::date between %s and %s) as a
                                            """,
                               (class_category, move_status, tuple(location_ids), tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_in_new2_mv(self, move_status, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if move_status and location_ids and date_to and date_from:
                cursor.execute("""
                                              select
                                                  a.qty_in
                                              from
                                                  (select sum(a.product_uom_qty) as qty_in
                                              from
                                                  stock_move as a, stock_location as b, product_product as c, product_template as d
                                              where
                                                   a.location_id = b.id and
                                                   a.product_id = c.id and
                                                   c.product_tmpl_id = d.id and
                                                   a.state = 'done' and
                                                   d.product_moving_status_id = %s and
                                                   b.usage in ('supplier') and
                                                   a.location_dest_id in %s and
                                                   a.location_id not in %s and
                                                  (a.date + interval '7 hour')::date between %s and %s) as a
                                             """, (move_status, tuple(location_ids), tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_in_new_mv(self, move_status, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if move_status and location_ids and date_to and date_from:
                cursor.execute("""
                                                 select
                                                     a.qty_in
                                                 from
                                                     (select sum(a.product_uom_qty) as qty_in
                                                 from
                                                     stock_move as a, stock_location as b, product_product as c, product_template as d
                                                 where
                                                      a.location_id = b.id and
                                                      a.product_id = c.id and
                                                      c.product_tmpl_id = d.id and
                                                      a.state = 'done' and
                                                      d.product_moving_status_id = %s and
                                                      b.usage in ('transit') and
                                                      a.location_dest_id in %s and
                                                      a.location_id not in %s and
                                                     (a.date + interval '7 hour')::date between %s and %s) as a
                                                """,(move_status, tuple(location_ids), tuple(location_ids), date_from,
                                date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty


class report_analisa_product_thru_wizard(models.TransientModel):
    _name = 'report.analisa.product.thru.wizard'
    company = fields.Many2one('res.company', 'Company')
    period_start = fields.Many2one('account.period', 'Period Start')
    period_stop = fields.Many2one('account.period', 'Period Stop')
    location_ids2 = fields.Many2many('stock.warehouse', string='Warehouse')
    location_main_wh_ids2 = fields.Many2many('stock.location', string='Location Main WH')
    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    type_pds = fields.Selection([('non-pds', 'Non PDS'), ('pds', 'PDS')], string='Type PDS')
    user_pds_id = fields.Many2one('res.users', 'User PDS', default=lambda self: self.env.user.id)
    line_ids = fields.One2many('analisa.product.thru.wizard.line', 'reference', string="Analisa Product Thru")
    product_category_ids2 = fields.Many2many('lea.product.category', string='Product Category')

    @api.multi
    @api.onchange('user_pds_id')
    def onchange_account_id(self):
        user = []
        if self.user_pds_id:
            return {'domain': {'location_ids2': [('responsible_id', 'in', [self.user_pds_id.id])]}}

    @api.multi
    def generate_report_excel(self):
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'analisa_product_and_sell_thru' + '_' + self.company.name + '.xlsx'
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
        #set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_font_size('8')
        #set_border.set_border()
        #################################################################################
        set_border_bold = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'bold': 1})
        set_border_bold.set_text_wrap()
        set_border_bold.set_font_size('9')
        #set_border_bold.set_border()
        ################################################################################
        set_border_bold_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('9')
        #set_border_bold_right.set_border()

        worksheet1.set_column('A:A', 30)
        worksheet1.set_column('B:B', 30)
        worksheet1.set_column('C:C', 30)
        worksheet1.set_column('D:BZ', 20)

        worksheet1.set_row(0, 30)

        date1 = datetime.strptime(self.period_start.date_start, '%Y-%m-%d')
        date2 = datetime.strptime(self.period_stop.date_stop, '%Y-%m-%d')
        r = relativedelta.relativedelta(date2, date1)
        m = r.months + 1

        worksheet1.merge_range('A1:K1', self.company.name, center_title)
        worksheet1.merge_range('A2:K2', 'Analisa Product dan Sell Thru', center_title)
        worksheet1.merge_range('A3:K3', self.period_start.name + ' s/d ' + self.period_stop.name, center_title)
        ###Header Size#####
        moving_status = []
        location = []
        location_main_wh = []

        for wh in self.location_ids2:
            location.append(wh.lot_stock_id.id)

        for mwh in self.location_main_wh_ids2:
            location_main_wh.append(mwh.id)

        mv_ids = self.env['lea.product.moving.status'].search([])
        class_category_ids = self.env['lea.product.class.category'].search([])
        category_ids = self.env['lea.product.category'].search([])

        worksheet1.write(6, 0, 'Article Status 2', header_table)
        worksheet1.write(6, 1, 'Article Category Code', header_table)
        worksheet1.write(6, 2, 'Product Category', header_table)

        worksheet1.write(6, 3, 'Stock Awal', header_table)
        worksheet1.write(6, 4, 'Brg Masuk', header_table)
        worksheet1.write(6, 5, 'Sale', header_table)
        worksheet1.write(6, 6, 'Stock Akhir', header_table)
        worksheet1.write(6, 7, 'Sell Thru', header_table)
        worksheet1.write(6, 8, 'Avrg Sale/bln', header_table)
        row = 7
        total_stock_awal_grand = 0
        total_stock_in_grand = 0
        total_stock_sales_grand = 0
        total_stock_end_grand = 0
        sell_thru_grand = 0
        average_sale_grand = 0
        for mv in mv_ids :
            #worksheet1.write(row, 0, mv.name, set_border_bold)
            total_stock_awal_mv  = 0
            total_stock_in_mv = 0
            total_stock_sales_mv = 0
            total_stock_end_mv = 0
            sell_thru_mv = 0
            average_sale_mv = 0
            i = 0
            for class_categ in class_category_ids :
                total_stock_awal_class_categ = 0
                total_stock_in_class_categ = 0
                total_stock_sales_class_categ = 0
                total_stock_end_class_categ = 0
                sell_thru_class_categ = 0
                average_sale_class_categ = 0
                l= 0
                for categ in category_ids :
                    stock_awal_main_wh = self.get_qty_awal(class_categ.id,mv.id,location_main_wh,categ.id)
                    stock_awal         = self.get_qty_awal(class_categ.id,mv.id,location,categ.id) + stock_awal_main_wh
                    stock_in           = self.get_qty_in(class_categ.id,mv.id,location,categ.id)
                    if self.type_pds  == 'non-pds':
                        stock_in = self.get_qty_in(class_categ.id, mv.id,location_main_wh, categ.id)
                    stock_out_sales    = self.get_qty_sales(class_categ.id,mv.id,location,categ.id)
                    stock_end          = stock_awal + stock_in - stock_out_sales
                    sell_thru          = 0
                    average_sale       = 0

                    if stock_end + stock_out_sales != 0 :
                        sell_thru = (stock_out_sales/float(stock_end + stock_out_sales)) * 100

                    if m != 0 :
                        average_sale = stock_out_sales/float(m)

                    if stock_awal + stock_in + stock_out_sales + stock_end != 0 :
                        worksheet1.write(row, 2, categ.name, set_border)
                        worksheet1.write(row, 3, stock_awal, set_right)
                        worksheet1.write(row, 4, stock_in, set_right)
                        worksheet1.write(row, 5, stock_out_sales, set_right)
                        worksheet1.write(row, 6, stock_end, set_right)
                        worksheet1.write(row, 7, sell_thru, set_right)
                        worksheet1.write(row, 8, average_sale, set_right)

                        total_stock_awal_class_categ = total_stock_awal_class_categ + stock_awal
                        total_stock_in_class_categ = total_stock_in_class_categ + stock_in
                        total_stock_sales_class_categ = total_stock_sales_class_categ + stock_out_sales
                        total_stock_end_class_categ = total_stock_end_class_categ + stock_end
                        row = row + 1
                        l=l+1
                        i = i + 1

                if total_stock_sales_class_categ + total_stock_end_class_categ != 0:
                    sell_thru_class_categ = (total_stock_sales_class_categ / float(total_stock_end_class_categ + total_stock_sales_class_categ)) * 100

                if m != 0:
                    average_sale_class_categ = total_stock_sales_class_categ / float(m)

                if total_stock_awal_class_categ + total_stock_in_class_categ + total_stock_sales_class_categ + total_stock_end_class_categ != 0 :
                    worksheet1.write(row-l, 1, class_categ.name, set_border)
                    worksheet1.write(row, 0, '', set_border)
                    worksheet1.write(row, 1, class_categ.name+' Total', set_border_bold)
                    worksheet1.write(row, 2, '', set_border)
                    worksheet1.write(row, 3, total_stock_awal_class_categ, set_border_bold_right)
                    worksheet1.write(row, 4, total_stock_in_class_categ, set_border_bold_right)
                    worksheet1.write(row, 5, total_stock_sales_class_categ, set_border_bold_right)
                    worksheet1.write(row, 6, total_stock_end_class_categ, set_border_bold_right)
                    worksheet1.write(row, 7, sell_thru_class_categ, set_border_bold_right)
                    worksheet1.write(row, 8, average_sale_class_categ, set_border_bold_right)

                    total_stock_awal_mv = total_stock_awal_mv + total_stock_awal_class_categ
                    total_stock_in_mv   = total_stock_in_mv + total_stock_in_class_categ
                    total_stock_sales_mv = total_stock_sales_mv + total_stock_sales_class_categ
                    total_stock_end_mv = total_stock_end_mv + total_stock_end_class_categ
                    row = row + 1
                    i = i + 1

            if total_stock_sales_mv + total_stock_end_mv!= 0 :
                sell_thru_mv = (total_stock_sales_mv/ float(total_stock_end_mv + total_stock_sales_mv)) * 100

            if m != 0:
                average_sale_mv = total_stock_sales_mv / float(m)

            if total_stock_awal_mv + total_stock_in_mv + total_stock_sales_mv + total_stock_end_mv != 0 :
                #row = row + 1
                worksheet1.write(row-i, 0, mv.name, set_border_bold)

                worksheet1.write(row, 0, mv.name+' Total', header_table)
                worksheet1.write(row, 1, '', header_table)
                worksheet1.write(row, 2, '', header_table)
                worksheet1.write(row, 3, total_stock_awal_mv, header_table_right)
                worksheet1.write(row, 4, total_stock_in_mv, header_table_right)
                worksheet1.write(row, 5, total_stock_sales_mv, header_table_right)
                worksheet1.write(row, 6, total_stock_end_mv, header_table_right)
                worksheet1.write(row, 7, sell_thru_mv, header_table_right)
                worksheet1.write(row, 8, average_sale_mv, header_table_right)

                total_stock_awal_grand = total_stock_awal_grand + total_stock_awal_mv
                total_stock_in_grand      = total_stock_in_grand + total_stock_in_mv
                total_stock_sales_grand = total_stock_sales_grand + total_stock_sales_mv
                total_stock_end_grand = total_stock_end_grand + total_stock_end_mv

                row = row + 1

        if total_stock_sales_grand + total_stock_end_grand != 0:
            sell_thru_grand = (total_stock_sales_grand / float(total_stock_end_grand + total_stock_sales_grand)) * 100

        if m != 0:
            average_sale_grand = total_stock_sales_grand / float(m)

        worksheet1.write(row, 0, 'GRAND TOTAL', header_table)
        worksheet1.write(row, 1, '', header_table)
        worksheet1.write(row, 2, '', header_table)
        worksheet1.write(row, 3, total_stock_awal_grand, header_table_right)
        worksheet1.write(row, 4, total_stock_in_grand, header_table_right)
        worksheet1.write(row, 5, total_stock_sales_grand, header_table_right)
        worksheet1.write(row, 6, total_stock_end_grand, header_table_right)
        worksheet1.write(row, 7, sell_thru_grand, header_table_right)
        worksheet1.write(row, 8, average_sale_grand, header_table_right)

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference('stock_report_lea', 'report_analisa_product_thru_form')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.analisa.product.thru.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_qty_awal(self, class_category, move_status, location_ids, category):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_to = line.period_start.date_start
            if class_category and move_status and location_ids and date_to and category:
                cursor.execute("""
                                    select
                                    a.qty_in - b.qty_out as balance_qty
                                    from
                                    (select sum(a.product_uom_qty) as qty_in
                                    from
                                    stock_move as a, stock_location as b, product_product as c, product_template as d
                                    where a.location_dest_id = b.id and
                                    a.product_id = c.id and
                                    c.product_tmpl_id = d.id and
                                    a.state = 'done' and
                                    d.product_class_category_id = %s and
                                    d.product_moving_status_id = %s and
                                    d.product_category_id = %s and
                                    b.id in %s and
                                    a.location_id not in %s and
                                    (a.date + interval '7 hour')::date <= %s) as a,

                                    (select sum(a.product_uom_qty) as qty_out
                                    from stock_move as a, stock_location as b, product_product as c, product_template as d
                                    where a.location_id = b.id and
                                    a.product_id = c.id and
                                    c.product_tmpl_id = d.id and
                                    a.state = 'done' and
                                    d.product_class_category_id = %s and
                                    d.product_moving_status_id = %s and
                                    d.product_category_id = %s and
                                    b.id in %s and
                                    a.location_dest_id not in %s and
                                    (a.date + interval '7 hour')::date < %s) as b
                                  """, (class_category, move_status, category , tuple(location_ids), tuple(location_ids), date_to, class_category, move_status, category, tuple(location_ids), tuple(location_ids), date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_in(self, class_category, move_status, location_ids, category):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if class_category and move_status and location_ids and date_to and category and date_from:
                cursor.execute("""
                                select
                                    a.qty_in
                                from
                                    (select sum(a.product_uom_qty) as qty_in
                                from
                                    stock_move as a, stock_location as b, product_product as c, product_template as d
                                where
                                     a.location_dest_id = b.id and
                                     a.product_id = c.id and
                                     c.product_tmpl_id = d.id and
                                     a.state = 'done' and
                                     d.product_class_category_id = %s and
                                     d.product_moving_status_id = %s and
                                     d.product_category_id = %s and
                                     b.id in %s and
                                     a.location_id not in %s and
                                    (a.date + interval '7 hour')::date between %s and %s) as a
                               """, (class_category, move_status, category, tuple(location_ids), tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_sales(self, class_category, move_status, location_ids, category):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if class_category and move_status and location_ids and date_from and date_to and category:
                cursor.execute("""
                                   select a.qty_out
                                   from
                                   (select sum(a.product_uom_qty) as qty_out
                                   from
                                   stock_move as a, stock_location as b, product_product as c, product_template as d
                                   where
                                   a.location_dest_id = b.id and
                                   a.product_id = c.id and
                                   c.product_tmpl_id = d.id and
                                   d.product_class_category_id = %s and
                                   d.product_moving_status_id = %s and
                                   d.product_category_id = %s and
                                   a.location_id in %s and
                                   a.state = 'done' and
                                   b.usage = 'customer' and
                                   (a.date + interval '7 hour')::date between %s and %s) as a
                                """, (class_category, move_status, category, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def generate_report(self):
        location = []
        all_location =[]
        location_main_wh = []
        start = self.period_start.date_start
        stop = self.period_start.date_stop
        cursor = self.env.cr
        line_obj = self.env['analisa.product.thru.wizard.line']
        for mwh in self.location_main_wh_ids2:
            location_main_wh.append(mwh.id)
            all_location.append(mwh.id)

        if self.type_pds == 'non-pds':
            wh_nasional = self.env['stock.warehouse'].search([('tipe_penjualan_toko','=','jual-toko')])
            for wh in wh_nasional:
                location.append(wh.lot_stock_id.id)
                all_location.append(wh.lot_stock_id.id)
            loc = all_location
        else :
            for wh in self.location_ids2:
                location.append(wh.lot_stock_id.id)
                all_location.append(wh.lot_stock_id.id)
            loc = location
        #raise Warning(all_location)

        article = []
        for a in self.product_category_ids2:
            article.append(a.id)

        cursor.execute("""
                                select
                                    a.product_id
                                from
                                    stock_move as a,
                                    product_product as b,
                                    product_template as c
                                where
                                    a.product_id = b.id and
                                    b.product_tmpl_id = c.id and
                                    a.state = 'done' and
                                    (a.date + interval '7 hour')::date <= %s and
                                    (a.location_id in %s or a.location_dest_id in %s)
                                    group by a.product_id
                               """, (stop, tuple(loc), tuple(loc)))
        res_ids = cursor.fetchall()


        date1 = datetime.strptime(self.period_start.date_start, '%Y-%m-%d')
        date2 = datetime.strptime(self.period_stop.date_stop, '%Y-%m-%d')
        r = relativedelta.relativedelta(date2, date1)
        m = r.months + 1

        if self.type_pds == 'non-pds':
            for c in res_ids:
                product = self.env['product.product'].browse(c[0])

                article = product.categ_id.id
                mv      = product.product_moving_status_id.id
                class_categ   = product.product_class_category_id.id
                product_categ = product.product_category_id.id
                brand = product.product_brand_id.id
                #raise Warning(mv)
                if self.type_pds == 'non-pds':
                    stock_awal = self.get_stock_awal_new2(c[0],loc)
                    stock_in = self.get_stock_in_nonpds(c[0],location_main_wh)
                    stock_sale = self.get_stock_out_sale_new2(c[0],loc)
                    stock_retur = self.get_stock_out_retur_new2(c[0],loc)
                else:
                    stock_awal = self.get_stock_awal_new2(c[0], loc)
                    stock_in = self.get_stock_in_pds(c[0], loc)
                    stock_sale = self.get_stock_out_sale_new2(c[0], loc)
                    stock_retur = self.get_stock_out_retur_new2(c[0], loc)
                stock_akhir = stock_awal + stock_in - stock_sale - stock_retur
                sell_thru = 0
                average_sale = 0
                stock_level = 0
                if stock_akhir + stock_sale != 0:
                    sell_thru = (stock_sale / float(stock_akhir + stock_sale)) * 100

                if m != 0:
                    average_sale = stock_sale / float(m)

                if average_sale != 0:
                    stock_level = stock_akhir/float(average_sale)


                if stock_awal + stock_in + stock_sale + stock_akhir + sell_thru + average_sale != 0 :
                    line_vals = {
                        'reference': self.id,
                        'mv_id': mv,
                        'class_category_id': class_categ,
                        'category_id': product_categ,
                        'categ_id': article,
                        'product_id' : c[0],
                        'stock_awal': stock_awal,
                        'stock_in': stock_in,
                        'stock_sale': stock_sale,
                        'stock_retur': stock_retur,
                        'stock_akhir': stock_akhir,
                        'sell_thru': sell_thru,
                        'avg_sale_month': average_sale,
                        'stock_level': stock_level,
                        'product_brand_id':brand,
                        'warehouse':'ALL'
                    }
                    #data.append(line_vals)
                    line_obj.create(line_vals)
        else :
            for wh in self.location_ids2:
                for c in res_ids:
                    product = self.env['product.product'].browse(c[0])
                    unit_loc = [wh.lot_stock_id.id]
                    article = product.categ_id.id
                    mv = product.product_moving_status_id.id
                    class_categ = product.product_class_category_id.id
                    product_categ = product.product_category_id.id
                    brand = product.product_brand_id.id

                    stock_awal = self.get_stock_awal_new2(c[0], unit_loc)
                    stock_in = self.get_stock_in_pds(c[0], unit_loc)
                    stock_sale = self.get_stock_out_sale_new2(c[0], unit_loc)
                    stock_retur = self.get_stock_out_retur_new2(c[0], unit_loc)

                    stock_akhir = stock_awal + stock_in - stock_sale - stock_retur
                    sell_thru = 0
                    average_sale = 0
                    stock_level = 0
                    if stock_akhir + stock_sale != 0:
                        sell_thru = (stock_sale / float(stock_akhir + stock_sale)) * 100

                    if m != 0:
                        average_sale = stock_sale / float(m)

                    if average_sale != 0:
                        stock_level = stock_akhir / float(average_sale)

                    if stock_awal + stock_in + stock_sale + stock_akhir + sell_thru + average_sale != 0:
                        line_vals = {
                            'reference': self.id,
                            'mv_id': mv,
                            'class_category_id': class_categ,
                            'category_id': product_categ,
                            'categ_id': article,
                            'product_id': c[0],
                            'stock_awal': stock_awal,
                            'stock_in': stock_in,
                            'stock_sale': stock_sale,
                            'stock_retur': stock_retur,
                            'stock_akhir': stock_akhir,
                            'sell_thru': sell_thru,
                            'avg_sale_month': average_sale,
                            'stock_level': stock_level,
                            'product_brand_id': brand,
                            'warehouse':wh.name
                        }
                        # data.append(line_vals)
                        line_obj.create(line_vals)


        #raise Warning(data)
        title = 'Analisa Product Sell Thru, Avg Sales, dan Level Stock '+self.period_start.name + ' s/d ' + self.period_stop.name
        return {
            'name': (title),
            'view_type': 'form',
            'view_mode': 'tree,pivot',
            'res_model': 'analisa.product.thru.wizard.line',
            'domain': [('reference', '=', self.id)],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current'

        }

    @api.multi
    def get_qty_awal_new(self, class_category, move_status, location_ids, category, artc):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_to = line.period_start.date_start
            if class_category and move_status and location_ids and date_to and category:
                cursor.execute("""
                                    select
                                    a.qty_in - b.qty_out as balance_qty
                                    from
                                    (select sum(a.product_uom_qty) as qty_in
                                    from
                                    stock_move as a, stock_location as b, product_product as c, product_template as d
                                    where a.location_dest_id = b.id and
                                    a.product_id = c.id and
                                    c.product_tmpl_id = d.id and
                                    a.state = 'done' and
                                    d.product_class_category_id = %s and
                                    d.product_moving_status_id = %s and
                                    d.product_category_id = %s and
                                    d.categ_id = %s and
                                    b.id in %s and
                                    a.location_id not in %s and
                                    (a.date + interval '7 hour')::date < %s) as a,

                                    (select sum(a.product_uom_qty) as qty_out
                                    from stock_move as a, stock_location as b, product_product as c, product_template as d
                                    where a.location_id = b.id and
                                    a.product_id = c.id and
                                    c.product_tmpl_id = d.id and
                                    a.state = 'done' and
                                    d.product_class_category_id = %s and
                                    d.product_moving_status_id = %s and
                                    d.product_category_id = %s and
                                    d.categ_id = %s and
                                    b.id in %s and
                                    a.location_dest_id not in %s and
                                    (a.date + interval '7 hour')::date < %s) as b
                                  """, (class_category, move_status, category, artc , tuple(location_ids), tuple(location_ids), date_to, class_category, move_status, category, artc, tuple(location_ids), tuple(location_ids), date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_in_new(self, class_category, move_status, location_ids, category, artc):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if class_category and move_status and location_ids and date_to and category and date_from:
                cursor.execute("""
                                   select
                                       a.qty_in
                                   from
                                       (select sum(a.product_uom_qty) as qty_in
                                   from
                                       stock_move as a, stock_location as b, product_product as c, product_template as d
                                   where
                                        a.location_id = b.id and
                                        a.product_id = c.id and
                                        c.product_tmpl_id = d.id and
                                        a.state = 'done' and
                                        d.product_class_category_id = %s and
                                        d.product_moving_status_id = %s and
                                        d.product_category_id = %s and
                                        d.categ_id = %s and
                                        b.usage in ('transit') and
                                        a.location_dest_id in %s and
                                        a.location_id not in %s and
                                       (a.date + interval '7 hour')::date between %s and %s) as a
                                  """, (
                class_category, move_status, category, artc, tuple(location_ids), tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_in_new2(self, class_category, move_status, location_ids, category, artc):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if class_category and move_status and location_ids and date_to and category and date_from:
                cursor.execute("""
                                      select
                                          a.qty_in
                                      from
                                          (select sum(a.product_uom_qty) as qty_in
                                      from
                                          stock_move as a, stock_location as b, product_product as c, product_template as d
                                      where
                                           a.location_id = b.id and
                                           a.product_id = c.id and
                                           c.product_tmpl_id = d.id and
                                           a.state = 'done' and
                                           d.product_class_category_id = %s and
                                           d.product_moving_status_id = %s and
                                           d.product_category_id = %s and
                                           d.categ_id = %s and
                                           b.usage in ('supplier') and
                                           a.location_dest_id in %s and
                                           a.location_id not in %s and
                                          (a.date + interval '7 hour')::date between %s and %s) as a
                                     """, (
                    class_category, move_status, category, artc, tuple(location_ids), tuple(location_ids), date_from,
                    date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_qty_sales_new(self, class_category, move_status, location_ids, category, artc):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if class_category and move_status and location_ids and date_from and date_to and category:
                cursor.execute("""
                                      select a.qty_out
                                      from
                                      (select sum(a.product_uom_qty) as qty_out
                                      from
                                      stock_move as a, stock_location as b, product_product as c, product_template as d
                                      where
                                      a.location_dest_id = b.id and
                                      a.product_id = c.id and
                                      c.product_tmpl_id = d.id and
                                      d.product_class_category_id = %s and
                                      d.product_moving_status_id = %s and
                                      d.product_category_id = %s and
                                      d.categ_id = %s and
                                      a.location_id in %s and
                                      a.state = 'done' and
                                      b.usage = 'customer' and
                                      (a.date + interval '7 hour')::date between %s and %s) as a
                                   """,
                               (class_category, move_status, category, artc, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty
    ###################################################New Query Again ############################################################################
    @api.multi
    def get_stock_awal_new2(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            if product_id and location_ids and date_from:
                cursor.execute("""
                                       select
                                            a.qty_in - b.qty_out as balance_qty
                                            from
                                            (select sum(a.product_uom_qty) as qty_in
                                            from
                                            stock_move as a, stock_location as b
                                            where a.location_dest_id = b.id and
                                            a.state = 'done' and
                                            a.product_id = %s and
                                            a.location_dest_id in %s and
                                            (a.date + interval '7 hour')::date < %s) as a,
                                            (select sum(a.product_uom_qty) as qty_out
                                            from stock_move as a, stock_location as b
                                            where a.location_id = b.id and
                                            a.state = 'done' and
                                            a.product_id = %s and
                                            a.location_id in %s and
                                            (a.date + interval '7 hour')::date < %s) as b
                                          """,
                               (product_id, tuple(location_ids), date_from, product_id, tuple(location_ids), date_from))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_in_pds(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if product_id and location_ids and date_to and date_from:
                cursor.execute("""
                                       select sum(a.product_uom_qty) as qty_in
                                           from
                                           stock_move as a, stock_location as b
                                           where a.location_id = b.id and
                                           a.state = 'done' and
                                           b.usage in ('transit') and
                                           a.product_id = %s and
                                           a.location_dest_id in %s and
                                           (a.date + interval '7 hour')::date between %s and %s
                                   """, (product_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_in_nonpds(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if product_id and location_ids and date_to and date_from:
                cursor.execute("""
                                          select sum(a.product_uom_qty) as qty_in
                                              from
                                              stock_move as a, stock_location as b
                                              where a.location_id = b.id and
                                              a.state = 'done' and
                                              b.usage in ('supplier') and
                                              a.product_id = %s and
                                              a.location_dest_id in %s and
                                              (a.date + interval '7 hour')::date between %s and %s
                                      """, (product_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty



    @api.multi
    def get_stock_out_sale_new2(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if product_id and location_ids and date_to:
                cursor.execute("""
                                                  select sum(a.product_uom_qty) as qty_out
                                                  from
                                                  stock_move as a, stock_location as b
                                                  where
                                                  a.location_dest_id = b.id and
                                                  a.state = 'done' and
                                                  a.product_id = %s and
                                                  a.location_id in %s and
                                                  b.usage in ('customer') and
                                                  (a.date + interval '7 hour')::date between %s and %s
                                                """, (product_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty

    @api.multi
    def get_stock_out_retur_new2(self, product_id, location_ids):
        cursor = self.env.cr
        qty = 0
        for line in self:
            date_from = line.period_start.date_start
            date_to = line.period_stop.date_stop
            if product_id and location_ids and date_to:
                cursor.execute("""
                                                      select sum(a.product_uom_qty) as qty_out
                                                      from
                                                      stock_move as a, stock_location as b
                                                      where
                                                      a.location_dest_id = b.id and
                                                      a.state = 'done' and
                                                      a.product_id = %s and
                                                      a.location_id in %s and
                                                      b.usage in ('transit') and
                                                      (a.date + interval '7 hour')::date between %s and %s
                                                    """, (product_id, tuple(location_ids), date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty = val[0]
        return qty



class analisa_product_thru_wizard_line(models.TransientModel):
    _name = 'analisa.product.thru.wizard.line'

    reference         = fields.Many2one(string="Wizard ID", comodel_name="report.analisa.product.thru.wizard")
    mv_id             = fields.Many2one(string="Moving Status", comodel_name="lea.product.moving.status")
    class_category_id = fields.Many2one(string="Class Category", comodel_name="lea.product.class.category")
    category_id       = fields.Many2one(string="Category", comodel_name="lea.product.category")
    categ_id          = fields.Many2one(string="Article", comodel_name="product.category")
    product_id        = fields.Many2one(string="Product Barcode", comodel_name="product.product")
    stock_awal        = fields.Float(string="Stock Awal")
    stock_in          = fields.Float(string="Barang Masuk")
    stock_sale        = fields.Float(string="Stock Sale")
    stock_retur       = fields.Float(string="Stock Retur")
    stock_akhir       = fields.Float(string="Stock Akhir")
    sell_thru         = fields.Float(string="Sell Thru")
    avg_sale_month    = fields.Float(string="Avrg Sale/bln")
    stock_level       = fields.Float(string="Stock Level")
    warehouse         = fields.Char(string="Warehouse Location")
    product_brand_id  = fields.Many2one(string="Brand", comodel_name="lea.product.brand")


class replenishment_wizard_line(models.TransientModel):
    _name = 'replenishment.wizard.line'

    reference = fields.Many2one(string="Wizard ID", comodel_name="report.replenishment.wizard")
    mv_id     = fields.Many2one(string="Moving Status", comodel_name="lea.product.moving.status")
    class_category_id = fields.Many2one(string="Class Category", comodel_name="lea.product.class.category")
    category_id       = fields.Many2one(string="Category", comodel_name="lea.product.category")
    categ_id          = fields.Many2one(string="Article", comodel_name="product.category")
    product_id        = fields.Many2one(string="Product Barcode", comodel_name="product.product")
    stock_awal        = fields.Float('Stock Awal', default=True)
    stock_in          = fields.Float('Stock Masuk', default=True)
    stock_retur       = fields.Float('Stock Retur', default=True)
    stock_sale        = fields.Float('Stock Sale', default=True)
    stock_akhir       = fields.Float('Stock Akhir', default=True)
    stock_gudang      = fields.Float('Stock Gudang', default=True)
    warehouse_id      = fields.Many2one(string="Warehouse", comodel_name="stock.warehouse")
    location_id       = fields.Many2one(string="Location", comodel_name="stock.location")



class stock_lea_detail_wizard(models.TransientModel):
    _name = 'stock.lea.detail.wizard'

    company     = fields.Many2one('res.company', 'Company')
    type        = fields.Selection([('stock_move_toko', 'Stock Move Per Toko'),
                             ('stock_replenishment_toko', 'Analisa Stock Replenishment Toko'),
                             ('product_sell_thru', 'Analisa Product Sell Thru'),
                             ('analisa_level_stock', 'Analisa level Stock dan Average Penjualan'),
                             ],
                            string='Type')
    period_id   = fields.Many2one('account.period', 'Period')
    stock_type     = fields.Selection([('MH', 'Main WH'),
                                       ('ST', 'Store'),
                                ],
                               string='WH Type')

    wh_type     = fields.Selection([('LS', 'Store'),
                                 ('LC', 'Consigment'),
                                 ('TP', 'Toko Putus'),
                                 ('CP', 'Consigment'),
                                 ('MW', 'MAIN WH'),
                             ],
                            string='WH Type')
    user_pds_id = fields.Many2one('res.users', 'User PDS', default=lambda self:self.env.user.id)
    date_from   = fields.Date('Date From')
    date_to     = fields.Date('Date To')
    data        = fields.Binary('File', readonly=True)
    name        = fields.Char('Filename', readonly=True)
    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    location_ids3   = fields.Many2one('stock.warehouse',string='Warehouse')
    location_main_wh_ids2  = fields.Many2one('stock.location', string='Location Main WH')

    @api.multi
    @api.onchange('period_id')
    def onchange_period_id(self):
        values = {
            'date_from': '',
            'date_to': '',
        }
        if self.period_id:
            values['date_from'] = self.period_id.date_start
            values['date_to'] = self.period_id.date_stop
        self.update(values)



    @api.multi
    def generate_excel_report(self):
        for res in self:
            report = False
            if res.type == 'stock_move_toko':
                report = self.stock_move_toko_report_excel()
            return report



    @api.multi
    def generate_stock_move_toko_report_excel(self):
        cursor = self.env.cr

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')
        line_obj = self.env['stock.lea.detail.wizard.line']
        stop = self.date_to
        loc_name = ''
        #Print dan Hitung stock masing2 lokasi
        if self.stock_type == 'ST':
            for lc in self.location_ids3 :
                wh = self.env['stock.warehouse'].browse(lc.id)
                loc_name = wh.name
                loc = wh.lot_stock_id.id
                cursor.execute("""
                                               select
                                                   a.product_id
                                               from
                                                   stock_move as a,
                                                   product_product as b,
                                                   product_template as c
                                               where
                                                   a.product_id = b.id and
                                                   b.product_tmpl_id = c.id and
                                                   a.state = 'done' and
                                                   (a.date + interval '7 hour')::date <= %s and
                                                   (a.location_id = %s or a.location_dest_id = %s)
                                               group by a.product_id
                                """, (stop, loc, loc))
                res_ids = cursor.fetchall()
                for prod in res_ids :
                    product = self.env['product.product'].browse(prod[0])
                    article = product.categ_id.id
                    mv = product.product_moving_status_id.id
                    class_categ = product.product_class_category_id.id
                    product_categ = product.product_category_id.id

                    stock_awal = self.get_stock_awal(loc,prod[0])
                    stock_in_internal = self.get_stock_in_transit(loc, prod[0]) # in mmw/mfg (stock barang masuk dengan lokasi asal tipe transit
                    stock_in_adjustment = self.get_stock_in_adjustment(loc, prod[0]) # in rfg (stock barang masuk dengan lokasi asal tipe non transit
                    stock_out_internal = self.get_stock_out_transit(loc, prod[0]) #out mfg (stock barang keluar dengan lokasi tujuan tipe transit
                    stock_out_adjusment = self.get_stock_out_adjustment(loc, prod[0]) #out mfg (stock barang keluar dengan lokasi tujuan tipe non transit exc. customer
                    stock_out_sale = self.get_stock_out_sale(loc, prod[0]) #out sale (stock barang keluar dengan lokasi tujuan tipe customer
                    stock_awal_total =  stock_awal
                    stock_akhir = stock_awal_total + ((stock_in_internal + stock_in_adjustment)-(stock_out_internal + stock_out_adjusment + stock_out_sale))
                    if stock_awal + stock_in_internal + stock_in_adjustment + stock_out_internal + stock_out_adjusment + stock_out_sale + stock_awal_total + stock_akhir :
                        line_vals = {
                            'reference': self.id,
                            'mv_id': mv,
                            'class_category_id': class_categ,
                            'category_id': product_categ,
                            'categ_id': article,
                            'product_id': prod[0],
                            'stock_awal': stock_awal,
                            'stock_in_mfg': stock_in_internal,
                            'stock_in_rfg': stock_in_adjustment,
                            'stock_out_mfg': stock_out_internal,
                            'stock_out_rfg' : stock_out_adjusment,
                            'stock_sale': stock_out_sale,
                            'stock_akhir': stock_akhir

                        }
                        # data.append(line_vals)
                        line_obj.create(line_vals)


        else :
            for lc in self.location_main_wh_ids2 :
                loc = lc.id
                loc_name = lc.name
                cursor.execute("""
                                select
                                    a.product_id
                                from
                                    stock_move as a,
                                    product_product as b,
                                    product_template as c
                                where
                                    a.product_id = b.id and
                                    b.product_tmpl_id = c.id and
                                    a.state = 'done' and
                                    (a.date + interval '7 hour')::date <= %s and
                                    (a.location_id = %s or a.location_dest_id = %s)
                                group by a.product_id
                                """, (stop, loc, loc))
                res_ids = cursor.fetchall()
                for prod in res_ids:
                    product = self.env['product.product'].browse(prod[0])
                    article = product.categ_id.id
                    mv = product.product_moving_status_id.id
                    class_categ = product.product_class_category_id.id
                    product_categ = product.product_category_id.id

                    init_wh_stock = self.get_stock_awal(loc,prod[0])
                    stock_in_internal = self.get_stock_in_transit2(loc,prod[0])  #in mmw/mfg (stock barang masuk dengan lokasi asal tipe supplier)
                    stock_in_adjustment = self.get_stock_in_adjustment2(loc, prod[0]) #in mmw/mfg (stock barang masuk dengan lokasi asal tipe non-supplier)
                    stock_out_internal = self.get_stock_out_transit(loc, prod[0]) #out mfg (stock barang keluar dengan lokasi tujuan tipe transit
                    stock_out_adjusment = self.get_stock_out_adjustment(loc, prod[0]) #out mfg (stock barang keluar dengan lokasi tujuan tipe non transit exc. customer
                    stock_out_sale = self.get_stock_out_sale(loc, prod[0]) #out sale (stock barang keluar dengan lokasi tujuan tipe customer
                    stock_awal_total = init_wh_stock
                    stock_akhir = stock_awal_total + ((stock_in_internal + stock_in_adjustment)-(stock_out_internal + stock_out_adjusment + stock_out_sale))
                    if stock_in_internal + stock_in_adjustment + stock_out_internal + stock_out_adjusment + stock_out_sale + stock_awal_total + stock_akhir:
                        line_vals = {
                            'reference': self.id,
                            'mv_id': mv,
                            'class_category_id': class_categ,
                            'category_id': product_categ,
                            'categ_id': article,
                            'product_id': prod[0],
                            'stock_awal': stock_awal_total,
                            'stock_in_mfg': stock_in_internal,
                            'stock_in_rfg': stock_in_adjustment,
                            'stock_out_mfg': stock_out_internal,
                            'stock_out_rfg': stock_out_adjusment,
                            'stock_sale': stock_out_sale,
                            'stock_akhir': stock_akhir

                        }
                        # data.append(line_vals)
                        line_obj.create(line_vals)

        title = 'Stock Move Detail '+loc_name+ '  ' + date_from + ' s/d ' + date_to
        return {
            'name': (title),
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'stock.lea.detail.wizard.line',
            'domain': [('reference', '=', self.id)],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current'

        }

    @api.multi
    def get_stock_awal(self, location_id, prod):
        cursor = self.env.cr
        qty_in = 0
        qty_out = 0
        for line in self:
            if location_id and line.date_from and prod:
                cursor.execute("""
                                   select
                                     a.qty_in, b.qty_out
                                     from
                                     (select sum(a.product_uom_qty) as qty_in
                                     from
                                     stock_move as a, stock_location as b
                                     where a.location_dest_id = b.id and
                                     a.state = 'done' and
                                     a.product_id = %s and
                                     a.location_dest_id = %s and
                                     (a.date + interval '7 hour')::date < %s) as a,
                                     (select sum(a.product_uom_qty) as qty_out
                                     from stock_move as a, stock_location as b
                                     where a.location_id = b.id and
                                     a.state = 'done' and
                                     a.product_id = %s and
                                     a.location_id = %s and
                                     (a.date + interval '7 hour')::date < %s) as b
                                """, (prod, location_id, line.date_from, prod, location_id,line.date_from))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
                if val[1] != None:
                    qty_out = val[1]
            qty = qty_in - qty_out
        return qty

    @api.multi
    def get_stock_in_transit(self, location_id, prod):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from and prod:
                cursor.execute("""
                                select a.qty_in
                                 from
                                 (select sum(a.product_uom_qty) as qty_in
                                 from
                                 stock_move as a, stock_location as b
                                 where
                                 a.location_id = b.id and
                                 a.product_id = %s and
                                 a.location_dest_id = %s and
                                 a.state = 'done' and
                                 b.usage in ('transit') and
                                 (a.date + interval '7 hour')::date between %s and %s) as a
                               """, (prod, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_in_adjustment(self, location_id, prod):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from and prod:
                cursor.execute("""
                                    select a.qty_in
                                     from
                                     (select sum(a.product_uom_qty) as qty_in
                                     from
                                     stock_move as a, stock_location as b
                                     where
                                     a.location_id = b.id and
                                     a.product_id = %s and
                                     a.location_dest_id = %s and
                                     a.state = 'done' and
                                     b.usage not in ('transit') and
                                     (a.date + interval '7 hour')::date between %s and %s) as a
                                   """, (prod, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_in_transit2(self, location_id, prod):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from and prod:
                cursor.execute("""
                                    select a.qty_in
                                     from
                                     (select sum(a.product_uom_qty) as qty_in
                                     from
                                     stock_move as a, stock_location as b
                                     where
                                     a.location_id = b.id and
                                     a.product_id = %s and
                                     a.location_dest_id = %s and
                                     a.state = 'done' and
                                     b.usage in ('supplier') and
                                     (a.date + interval '7 hour')::date between %s and %s) as a
                                   """, (prod, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_in_adjustment2(self, location_id, prod):
        cursor = self.env.cr
        qty_in = 0
        for line in self:
            if location_id and line.date_from and prod:
                cursor.execute("""
                                        select a.qty_in
                                         from
                                         (select sum(a.product_uom_qty) as qty_in
                                         from
                                         stock_move as a, stock_location as b
                                         where
                                         a.location_id = b.id and
                                         a.product_id = %s and
                                         a.location_dest_id = %s and
                                         a.state = 'done' and
                                         b.usage not in ('supplier') and
                                         (a.date + interval '7 hour')::date between %s and %s) as a
                                       """, (prod, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_in = val[0]
        return qty_in

    @api.multi
    def get_stock_out_transit(self, location_id, prod):
        cursor = self.env.cr
        qty_out = 0
        for line in self:
            if location_id and line.date_from and prod:
                cursor.execute("""
                                  select a.qty_out
                                         from
                                         (select sum(a.product_uom_qty) as qty_out
                                         from
                                         stock_move as a, stock_location as b
                                         where
                                         a.location_dest_id = b.id and
                                         a.product_id = %s and
                                         a.location_id = %s and
                                         a.state = 'done' and
                                         b.usage in ('transit') and
                                         (a.date + interval '7 hour')::date between %s and %s) as a
                                   """, (prod, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_out = val[0]
        return qty_out

    @api.multi
    def get_stock_out_adjustment(self, location_id, prod):
        cursor = self.env.cr
        qty_out = 0
        for line in self:
            if location_id and line.date_from and prod:
                cursor.execute("""
                                      select a.qty_out
                                             from
                                             (select sum(a.product_uom_qty) as qty_out
                                             from
                                             stock_move as a, stock_location as b
                                             where
                                             a.location_dest_id = b.id and
                                             a.product_id = %s and
                                             a.location_id = %s and
                                             a.state = 'done' and
                                             b.usage not in ('transit','customer') and
                                             (a.date + interval '7 hour')::date between %s and %s) as a
                                       """, (prod, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_out = val[0]
        return qty_out

    @api.multi
    def get_stock_out_sale(self, location_id, prod):
        cursor = self.env.cr
        qty_out = 0
        for line in self:
            if location_id and line.date_from and prod:
                cursor.execute("""
                                     select a.qty_out
                                            from
                                            (select sum(a.product_uom_qty) as qty_out
                                            from
                                            stock_move as a, stock_location as b
                                            where
                                            a.location_dest_id = b.id and
                                            a.product_id = %s and
                                            a.location_id = %s and
                                            a.state = 'done' and
                                            b.usage in ('customer') and
                                            (a.date + interval '7 hour')::date between %s and %s) as a
                                      """, (prod, location_id, line.date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    qty_out = val[0]
        return qty_out

class stock_lea_detail_wizard(models.TransientModel):
    _name = 'stock.lea.detail.wizard.line'

    reference = fields.Many2one(string="Wizard ID", comodel_name="stock.lea.detail.wizard")
    mv_id     = fields.Many2one(string="Moving Status", comodel_name="lea.product.moving.status")
    class_category_id = fields.Many2one(string="Class Category", comodel_name="lea.product.class.category")
    category_id       = fields.Many2one(string="Category", comodel_name="lea.product.category")
    categ_id          = fields.Many2one(string="Article", comodel_name="product.category")
    product_id        = fields.Many2one(string="Product Barcode", comodel_name="product.product")
    stock_awal        = fields.Float('Stock Awal')
    stock_in_mfg      = fields.Float('Stock In mmw/mfg')
    stock_in_rfg      = fields.Float('Stock In rfg')
    stock_out_mfg     = fields.Float('Stock Out mmw/mfg')
    stock_out_rfg     = fields.Float('Stock Out rfg')
    stock_sale        = fields.Float('Stock Sale')
    stock_akhir       = fields.Float('Stock Akhir')


class report_inventory_value_acc(models.TransientModel):
    _name = 'report.inventory.value.acc'
    company = fields.Many2one('res.company', 'Company')
    date = fields.Date('Date')
    location_ids2 = fields.Many2many('stock.warehouse', string='Warehouse')
    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    line_ids = fields.One2many('report.inventory.value.acc.line', 'reference', string="Inventory Value")

    @api.depends('product_id')
    def _get_volume_stock(self):
        for res in self:
            total = 0
            warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', res.reference.dest_company_id.id)])
            if warehouse_id:
                location_id = warehouse_id[0].lot_stock_id
                if location_id:
                    product_ids = self.env['stock.quant'].search(
                        [('product_id', '=', res.product_id.id), ('location_id', '=', location_id.id)])
                    if product_ids:
                        for product in product_ids:
                            total += product.qty
            res.volume_stock = total

    @api.multi
    def generate_data_pivot(self):
        cursor = self.env.cr
        loc = []
        in_date = self.date+' 23:59:59'
        line_obj = self.env['report.inventory.value.acc.line']
        date_to_raw = datetime.strptime(self.date, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        for l in self.location_ids2:
            loc.append(l.lot_stock_id.id)
        cursor.execute("""
                        select product_id
                        from stock_quant
                        where
                        location_id in %s
                        and
                        (in_date + interval '7 hour')::date <= %s
                        group by product_id
                   """, (tuple(loc), self.date))
        prod_ids = cursor.fetchall()

        for p in prod_ids :
            for wh in self.location_ids2 :
                product = self.env['product.product'].browse(p[0])
                article = product.categ_id.id
                mv = product.product_moving_status_id.id
                class_categ = product.product_class_category_id.id
                product_categ = product.product_category_id.id
                brand = product.product_brand_id.id
                subarea = wh.wh_subarea_id.id
                area = wh.wh_area_id.id
                wh_type = wh.wh_type


                quant_ids = self.env['stock.quant'].search([('product_id', '=', product.id), ('location_id', '=', wh.lot_stock_id.id), ('in_date', '<=', in_date)])
                total_stock = 0
                total_inventory = 0
                if quant_ids :
                    for q in quant_ids:
                        total_stock = total_stock + q.qty
                        total_inventory = total_inventory + q.inventory_value
                cost_unit = 0
                if total_stock != 0 :
                    cost_unit = total_inventory/float(total_stock)

                    line_vals = {
                                'reference': self.id,
                                'mv_id': mv,
                                'location_id':wh.lot_stock_id.id,
                                'wh_id':wh.id,
                                'wh_type': wh_type,
                                'wh_subarea_id':subarea,
                                'wh_area_id':area,
                                'class_category_id': class_categ,
                                'category_id': product_categ,
                                'categ_id': article,
                                'product_brand_id':brand,
                                'product_id': p[0],
                                'stock_akhir': total_stock,
                                'cost_unit': cost_unit,
                                'total':total_inventory

                            }
                    #data.append(line_vals)
                    line_obj.create(line_vals)

        title = 'Stock Inventory Value ' + date_to
        return {
            'name': (title),
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'report.inventory.value.acc.line',
            'domain': [('reference', '=', self.id)],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current'

        }


class report_inventory_value_acc_line(models.TransientModel):
    _name = 'report.inventory.value.acc.line'

    reference         = fields.Many2one(string="Wizard ID", comodel_name="report.inventory.value.acc")
    wh_id             = fields.Many2one(string="Warehouse", comodel_name="stock.warehouse")
    location_id       = fields.Many2one(string="Location", comodel_name="stock.location")
    mv_id             = fields.Many2one(string="Moving Status", comodel_name="lea.product.moving.status")
    class_category_id = fields.Many2one(string="Class Category", comodel_name="lea.product.class.category")
    category_id       = fields.Many2one(string="Category", comodel_name="lea.product.category")
    categ_id          = fields.Many2one(string="Article", comodel_name="product.category")
    product_brand_id  = fields.Many2one(string="Brand", comodel_name="lea.product.brand")
    wh_type           = fields.Selection(
                        [('LS', 'STORE'),
                         ('LC', 'CONSIGMENT'),
                         ('TP', 'TOKO PUTUS'),
                         ('CP', 'CORPORATE'),
                         ('MW', 'MAIN WH'),
                         ], string='WH Type')
    wh_subarea_id     = fields.Many2one('lea.sub.area', 'Sub Area')
    wh_area_id        = fields.Many2one('lea.area', 'Area')
    product_id        = fields.Many2one(string="Product Barcode", comodel_name="product.product")
    stock_akhir       = fields.Float('Stock Akhir')
    cost_unit         = fields.Float('Cost Per Unit')
    total             = fields.Float('Total')





















