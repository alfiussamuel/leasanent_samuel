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
import re

BULAN_SELECTION = [
    ('1', 'Januari'),
    ('2', 'Februari'),
    ('3', 'Maret'),
    ('4', 'April'),
    ('5', 'Mei'),
    ('6', 'Juni'),
    ('7', 'Juli'),
    ('8', 'Agustus'),
    ('9', 'September'),
    ('10', 'Oktober'),
    ('11', 'November'),
    ('12', 'Desember'),
]

class GeneralLedgerLeaWizard(models.TransientModel):
    _name = 'general.ledger.lea.wizard'


    company         = fields.Many2one('res.company', 'Company')
    account         = fields.Many2many('account.account')
    partner         = fields.Many2one('res.partner')
    area_lks_id     = fields.Many2many('account.area.location')
    period_id       = fields.Many2one('account.period')
    date_from       = fields.Date('Date From')
    date_to         = fields.Date('Date To')
    data            = fields.Binary('File', readonly=True)
    name            = fields.Char('Filename', readonly=True)
    target          = fields.Selection([('all', 'All'), ('posted', 'Posted')], default='posted')
    state_position  = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

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
    def generate_general_ledger_excel(self):

        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'General_Ledger' + '_' + self.company.name +'.xlsx'
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
        header_table_right = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right','num_format': '#,##0.00'})
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
        set_border_bold_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('9')
        set_border_bold_right.set_border()

        worksheet1.set_column('A:A', 10)
        worksheet1.set_column('B:B', 10)
        worksheet1.set_column('C:C', 15)
        worksheet1.set_column('D:D', 15)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_column('F:F', 45)
        worksheet1.set_column('G:G', 25)
        worksheet1.set_column('H:H', 25)
        worksheet1.set_column('I:I', 25)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.set_row(0, 30)
        worksheet1.merge_range('A1:G1', self.company.name, center_title)
        worksheet1.merge_range('A2:G2', 'General Ledger', center_title)
        worksheet1.merge_range('A3:G3', date_from+' s/d '+date_to, center_title)

        account = self.env['account.account'].search([('company_id','=',self.company.id)])
        if self.account :
            account = self.account

        states = ['posted']
        if self.target == 'all':
            states = ['draft', 'posted']

        area =[]
        for ar in self.area_lks_id :
            area.append(ar.id)

        row = 4

        for acc in account :
            # Search Move Line Transaction
            total_debit_check = 0
            total_credit_check = 0
            saldo_awal = self.get_balance(acc, self.date_from, self.company, area, states)
            aml = self.env['account.move.line'].search([('account_id', '=', acc.id), ('date', '>=', self.date_from), ('date', '<=', self.date_to),('move_id.state', 'in', states), ('company_id', '=', self.company.id)])
            if self.area_lks_id:
                aml = self.env['account.move.line'].search([('account_id', '=', acc.id), ('date', '>=', self.date_from), ('date', '<=', self.date_to),('move_id.state', 'in', states),('move_id.area_lks', 'in', area), ('company_id', '=', self.company.id)])

            for line in aml:
                total_debit_check = total_debit_check + line.debit
                total_credit_check = total_credit_check + line.credit

            total_check = saldo_awal[2] + total_debit_check + total_credit_check
            if total_check != 0 :
                worksheet1.write(row, 0, 'No.Rek')
                worksheet1.write(row, 1, acc.code+' - '+acc.name)
                row = row + 1
                worksheet1.write(row, 0, 'Tanggal', header_table)
                worksheet1.write(row, 1, 'Area', header_table)
                worksheet1.write(row, 2, 'No. Internal', header_table)
                worksheet1.write(row, 3, 'No. Bukti', header_table)
                worksheet1.write(row, 4, 'Rek. Lawan', header_table)
                worksheet1.write(row, 5, 'Uraian', header_table)
                worksheet1.write(row, 6, 'Debit', header_table)
                worksheet1.write(row, 7, 'Kredit', header_table)
                worksheet1.write(row, 8, 'Saldo', header_table)
                #Computing Initial Balance

                row = row + 1
                worksheet1.write(row, 0, '', set_border)
                worksheet1.write(row, 1, '', set_border)
                worksheet1.write(row, 2, '', set_border)
                worksheet1.write(row, 3, '', set_border)
                worksheet1.write(row, 4, '', set_border)
                worksheet1.write(row, 5, 'SALDO AWAL', set_border)
                worksheet1.write(row, 6, 0, set_right)
                worksheet1.write(row, 7, 0, set_right)
                worksheet1.write(row, 8, saldo_awal[2], set_right)
                #Search Move Line Transaction
                row = row + 1
                saldo = saldo_awal[2]
                total_debit = 0
                total_credit = 0
                if aml :
                    for line in aml.sorted(key=lambda l: l.date) :
                        counter = ''
                        counterpart = self.env['account.move.line'].search([('account_id', '!=', acc.id),('move_id', '=', line.move_id.id)])
                        for c in counterpart :
                            counter += c.account_id.code+'  '
                        date_move_raw = datetime.strptime(line.date, '%Y-%m-%d')
                        date_move = datetime.strftime(date_move_raw, '%d-%m-%Y')
                        total_debit = total_debit + line.debit
                        total_credit = total_credit + line.credit
                        saldo = saldo + line.debit - line.credit
                        worksheet1.write(row, 0, date_move, set_border)
                        worksheet1.write(row, 1, line.move_id.area_lks.name, set_border)
                        worksheet1.write(row, 2, line.move_id.name, set_border)
                        worksheet1.write(row, 3, line.move_id.no_bukti, set_border)
                        worksheet1.write(row, 4, counter, set_border)
                        worksheet1.write(row, 5, line.name, set_border)
                        worksheet1.write(row, 6, line.debit, set_right)
                        worksheet1.write(row, 7, line.credit, set_right)
                        worksheet1.write(row, 8, saldo, set_right)
                        row = row + 1
                #Summary
                row = row + 1
                total = saldo_awal[2]+ total_debit - total_credit
                worksheet1.merge_range('A'+str(row)+':F'+str(row), "Total", header_table)
                row= row - 1
                worksheet1.write(row, 6, total_debit, header_table_right)
                worksheet1.write(row, 7, total_credit, header_table_right)
                worksheet1.write(row, 8, total, header_table_right)
                row = row + 2




        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'account_report_lea', 'general_ledger_lea_wizard_view_forms')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'general.ledger.lea.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_balance(self, account, date, company, area, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0
        for line in self:
            if account :
                if not area :
                    cursor.execute("""
                                    select
                                        sum(a.debit) as debit,
                                        sum(a.credit) as credit,
                                        sum(a.debit - a.credit) as balance
                                    from
                                        account_move_line as a, account_move as b
                                    where
                                        a.move_id = b.id and
                                        a.account_id = %s and
                                        a.date < %s and
                                        b.state in %s and
                                        b.company_id = %s
                                        """, (account.id, date, tuple(states), company.id))
                else :
                    cursor.execute("""
                                    select
                                        sum(a.debit) as debit,
                                        sum(a.credit) as credit,
                                        sum(a.debit - a.credit) as balance
                                    from
                                        account_move_line as a, account_move as b
                                    where
                                        a.move_id = b.id and
                                        a.account_id = %s and
                                        a.date < %s and
                                        b.state in %s and
                                        b.company_id = %s and
                                        b.area_lks in %s
                                    """, (account.id, date, tuple(states), company.id, tuple(area)))
                val = cursor.fetchone()
                if val[0] != None:
                    debit = val[0]
                if val[1] != None:
                    credit = val[1]
                if val[2] != None:
                    balance = val[2]
        return [debit,credit,balance]

class AccountFin(models.TransientModel):
    _name = "as.accounting.closing.report.final"
    _description = "Accounting Report After Closing"

    # common
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    fiscalyear_id = fields.Many2one('account.fiscalyear', string='Fiscal Year')
    period_id = fields.Many2one('account.period', string='Period')
    closing_id = fields.Many2one('account.closing', string='Account Closing')

    # files
    name = fields.Char(string="File Name")
    state_x = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    data_x = fields.Binary('File', readonly=True)
    wbf = {}

    @api.multi
    def check_report(self):
        per = re.split("/", self.period_id.name)
        mm = int(per[0])
        #raise UserError(_(str(mm)))
        bulan = dict(BULAN_SELECTION)[str(mm)]
        if mm == 1:
            month = 12
            prev_month_year = int(self.fiscalyear_id.code) - 1
            prev_period = '12/'+str(int(self.fiscalyear_id.code) - 1)
        else:
            month = mm - 1
            prev_month_year = int(self.fiscalyear_id.code)
            if month < 10 :
                prev_period = '0'+str(month)+'/'+ self.fiscalyear_id.code
            else :
                prev_period = str(month)+'/'+self.fiscalyear_id.code

        first_period = '0/'+str(self.fiscalyear_id.code)

        #raise UserError(_(prev_period))
        #prev_month = dict(BULAN_SELECTION)[str(month)]
        #year = int(self.fiscalyear_id.code)
        #prev_year = year - 1

        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'ClosingFinancialReport' + ' - ' + self.company_id.name + ' - ' + bulan + ' ' + self.fiscalyear_id.code + '.xlsx'
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
        header_table_right = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right','num_format': '#,##0.00'})
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
        set_border_bold_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('9')
        set_border_bold_right.set_border()

        worksheet1.set_column('A:A', 15)
        worksheet1.set_column('B:B', 45)
        worksheet1.set_column('C:C', 15)
        worksheet1.set_column('D:D', 15)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_column('F:F', 15)
        worksheet1.set_column('G:G', 15)
        worksheet1.set_column('H:H', 15)
        worksheet1.set_column('I:I', 15)
        worksheet1.set_column('J:J', 15)
        worksheet1.set_column('K:K', 15)
        worksheet1.set_column('L:L', 15)

        worksheet1.set_row(0, 30)
        worksheet1.merge_range('A1:F1', self.company_id.name, center_title)
        worksheet1.merge_range('A2:F2', 'Neraca Mutasi', center_title)
        worksheet1.merge_range('A3:F3', "Per " + bulan + " " + self.fiscalyear_id.code, center_title)

        worksheet1.merge_range('A7:A8', "Code", header_table)
        worksheet1.merge_range('B7:B8', "Account", header_table)

        #Saldo Per 1 january, akun neraca ambil per akhir 31 desember tahun lalu, akun laba rugi 0 (Kosong)
        worksheet1.merge_range('C7:D7', "Saldo Per 1 Januari", header_table)
        worksheet1.write(7, 2, 'Debit', header_table)
        worksheet1.write(7, 3, 'Credit', header_table)

        # Mutasi Bulan ini, Mutasi this month
        worksheet1.merge_range('E7:F7', "Mutasi Bulan ini", header_table)
        worksheet1.write(7, 4, 'Debit', header_table)
        worksheet1.write(7, 5, 'Credit', header_table)

        worksheet1.merge_range('G7:H7', "Mutasi s/d Bulan lalu", header_table)
        worksheet1.write(7, 6, 'Debit', header_table)
        worksheet1.write(7, 7, 'Credit', header_table)

        worksheet1.merge_range('I7:J7', "Mutasi s/d Bulan ini", header_table)
        worksheet1.write(7, 8, 'Debit', header_table)
        worksheet1.write(7, 9, 'Credit', header_table)

        worksheet1.merge_range('K7:L7', "Saldo Akhir", header_table)
        worksheet1.write(7, 10, 'Debit', header_table)
        worksheet1.write(7, 11, 'Credit', header_table)

        #worksheet1.merge_range('M7:N7', "Test", header_table)
        #worksheet1.write(7, 12, 'Debit', header_table)
        #worksheet1.write(7, 13, 'Credit', header_table)

        account = self.env['account.account'].search([('company_id', '=', self.company_id.id)])
        row = 8

        total_debit_bulan_lalu = 0
        total_credit_bulan_lalu = 0
        closing_id_bulan_lalu = self.env['account.closing'].search([('period_id.name', '=', prev_period),('company_id', '=', self.company_id.id),('is_consolidation', '=', self.closing_id.is_consolidation)])
        closing_id_first_period = self.env['account.closing'].search([('period_id.name', '=', first_period), ('company_id', '=', self.company_id.id),('is_consolidation', '=', self.closing_id.is_consolidation)])
        #raise UserError(_(closing_id_first_period))
        total_debit_awal = 0
        total_credit_awal = 0

        total_debit_bulan_ini = 0
        total_credit_bulan_ini = 0

        total_debit_final = 0
        total_credit_final = 0

        total_debit_akhir  = 0
        total_credit_akhir = 0

        total_debit_cek = 0
        total_credit_cek = 0

        for ac in account :
            #Saldo Per 1 january, diambil dari closing periode 0
            debit_awal = 0
            credit_awal = 0
            if closing_id_first_period :
                if ac.user_type_id.id not in (14,16) :
                    mutasi_awal = self.get_final_mutation(closing_id_first_period, ac)
                    selisih_awal = mutasi_awal[2]
                    debit_awal = selisih_awal
                    credit_awal = 0
                    if selisih_awal < 0 :
                        debit_awal = 0
                        credit_awal = abs(selisih_awal)
            total_debit_awal = total_debit_awal + debit_awal
            total_credit_awal = total_credit_awal + credit_awal

            # Mutasi s/d Bulan ini, Diambil dari Balance Akhir Dari Closing Bulan INI
            debit_sampai_bulan_ini = 0
            credit_sampai_bulan_ini = 0

            balance_tahun_lalu = self.get_final_mutation(closing_id_first_period, ac)
            saldo_akhir = self.get_final_mutation(self.closing_id, ac)
            #if closing_id_first_period:
            """
                if ac.user_type_id.id not in (14, 16):
                    debit_sampai_bulan_ini = saldo_akhir[0] - balance_tahun_lalu[0]
                    credit_sampai_bulan_ini = saldo_akhir[1] - balance_tahun_lalu [1]
                else :
            """
            debit_sampai_bulan_ini = saldo_akhir[0]
            credit_sampai_bulan_ini = saldo_akhir[1]
            total_debit_final = total_debit_final + debit_sampai_bulan_ini
            total_credit_final = total_credit_final + credit_sampai_bulan_ini

            # Mutasi Bulan ini, Mutasi this month
            mutasi_bulan_ini = self.get_this_mutation(self.closing_id, ac)
            total_debit_bulan_ini = total_debit_bulan_ini + mutasi_bulan_ini[0]
            total_credit_bulan_ini = total_credit_bulan_ini + mutasi_bulan_ini[1]


            #debit_bulan_lalu = 0
            #credit_bulan_lalu = 0
            #if closing_id_bulan_lalu :
            #mutasi_bulan_lalu = self.get_final_mutation(closing_id_bulan_lalu[0],ac)
            #mutasi s/d Bulan Lalu, Debit/Credit sampai bulan ini dikurangi Debit/Credit This Month
            debit_bulan_lalu =  debit_sampai_bulan_ini - mutasi_bulan_ini[0]
            credit_bulan_lalu = credit_sampai_bulan_ini - mutasi_bulan_ini[1]


            total_debit_bulan_lalu = total_debit_bulan_lalu + debit_bulan_lalu
            total_credit_bulan_lalu = total_credit_bulan_lalu + credit_bulan_lalu
            #saldo akhir, Debit/Credit awal 1 January +  Debit/Credit sampai bulan ini
            #debit_saldo_akhir = debit_awal - debit_sampai_bulan_ini
            #credit_saldo_akhir = credit_awal - credit_sampai_bulan_inisss
            #init_balance =  0
            init_balance = 0
            if closing_id_first_period :
                mutasi_awal_ = self.get_final_mutation(closing_id_first_period, ac)
                init_balance = mutasi_awal[2]
            saldo = init_balance + (debit_sampai_bulan_ini-credit_sampai_bulan_ini)
            final_debit = saldo
            final_credit = 0
            if saldo < 0 :
                final_debit = 0
                final_credit = abs(saldo)
            total_debit_akhir = total_debit_akhir + final_debit
            total_credit_akhir = total_credit_akhir + final_credit

            total_debit_cek = total_debit_cek + saldo_akhir[0]
            total_credit_cek = total_credit_cek + saldo_akhir[1]

            if mutasi_bulan_ini[0]+ mutasi_bulan_ini[1]+saldo_akhir[0]+saldo_akhir[1]+debit_bulan_lalu+credit_bulan_lalu+final_debit+final_credit+debit_awal+credit_awal != 0 :
                worksheet1.write(row, 0, ac.code, set_border)
                worksheet1.write(row, 1, ac.name, set_border)
                worksheet1.write(row, 2, debit_awal, set_right)
                worksheet1.write(row, 3, credit_awal, set_right)
                worksheet1.write(row, 4, mutasi_bulan_ini[0], set_right)
                worksheet1.write(row, 5, mutasi_bulan_ini[1], set_right)
                worksheet1.write(row, 6, debit_bulan_lalu, set_right)
                worksheet1.write(row, 7, credit_bulan_lalu, set_right)
                worksheet1.write(row, 8, debit_sampai_bulan_ini, set_right)
                worksheet1.write(row, 9, credit_sampai_bulan_ini, set_right)
                worksheet1.write(row, 10, final_debit, set_right)
                worksheet1.write(row, 11, final_credit, set_right)
                #worksheet1.write(row, 12, saldo_akhir[0], set_right)
                #worksheet1.write(row, 13, saldo_akhir[1], set_right)
                #worksheet1.write(row, 14, balance_tahun_lalu[0], set_right)
                #worksheet1.write(row, 15, balance_tahun_lalu [1], set_right)
                row = row + 1

        #Summary
        row = row +1
        worksheet1.merge_range('A'+str(row)+':B'+str(row), 'TOTAL', header_table)
        row = row -1
        worksheet1.write(row, 2, total_debit_awal, header_table_right)
        worksheet1.write(row, 3, total_credit_awal, header_table_right)
        worksheet1.write(row, 4, total_debit_bulan_ini, header_table_right)
        worksheet1.write(row, 5, total_credit_bulan_ini, header_table_right)
        worksheet1.write(row, 6, total_debit_bulan_lalu, header_table_right)
        worksheet1.write(row, 7, total_credit_bulan_lalu, header_table_right)
        worksheet1.write(row, 8, total_debit_final, header_table_right)
        worksheet1.write(row, 9, total_credit_final, header_table_right)
        worksheet1.write(row, 10, total_debit_akhir, header_table_right)
        worksheet1.write(row, 11, total_credit_akhir, header_table_right)
        #worksheet1.write(row, 12, total_debit_cek, header_table_right)
        #worksheet1.write(row, 13, total_credit_cek, header_table_right)

        """
        worksheet1.merge_range('C7:D7', "Saldo per 1 Januari", wbf['content_float'])
        worksheet1.set_column(2, 3, 16, wbf['content_float'])
        worksheet1.write_string(row, 2, "Saldo per 1 Januari", wbf['header_no'])
        worksheet1.write_string(row + 1, 2, "Debit", wbf['header_no'])
        worksheet1.write_string(row + 1, 3, "Credit", wbf['header_no'])

        worksheet1.merge_range('E7:F7', "Mutasi Bulan ini", wbf['content_float'])
        worksheet1.set_column(4, 5, 16, wbf['content_float'])
        worksheet1.write_string(row, 4, "Mutasi Bulan ini", wbf['header_no'])
        worksheet1.write_string(row + 1, 4, "Debit", wbf['header_no'])
        worksheet1.write_string(row + 1, 5, "Credit", wbf['header_no'])

        worksheet1.merge_range('G7:H7', "Mutasi s/d Bulan Lalu", wbf['content_float'])
        worksheet1.set_column(6, 7, 16, wbf['content_float'])
        worksheet1.write_string(row, 6, "Mutasi s/d Bulan Lalu", wbf['header_no'])
        worksheet1.write_string(row + 1, 6, "Debit", wbf['header_no'])
        worksheet1.write_string(row + 1, 7, "Credit", wbf['header_no'])

        worksheet1.merge_range('I7:J7', "Mutasi s/d Bulan ini", wbf['content_float'])
        worksheet1.set_column(8, 9, 16, wbf['content_float'])
        worksheet1.write_string(row, 8, "Mutasi s/d Bulan ini", wbf['header_no'])
        worksheet1.write_string(row + 1, 8, "Debit", wbf['header_no'])
        worksheet1.write_string(row + 1, 9, "Credit", wbf['header_no'])

        worksheet1.merge_range('K7:L7', "Saldo Akhir", wbf['content_float'])
        worksheet1.set_column(10, 11, 16, wbf['content_float'])
        worksheet1.write_string(row, 10, "Saldo Akhir", wbf['header_no'])
        worksheet1.write_string(row + 1, 10, "Debit", wbf['header_no'])
        worksheet1.write_string(row + 1, 11, "Credit", wbf['header_no'])
        """
        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data_x': out,
                    'name': filename,
                    'state_x': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'as_account_closing_financial_report', 'as_accounting_closing_report_final_view')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'as.accounting.closing.report.final',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_this_mutation(self, closing_id, account_id):

        debit = 0
        credit = 0
        balance = 0
        mutation = self.env['account.closing.detail'].search([('closing_id', '=', closing_id.id),('account_id', '=', account_id.id),('options', '=', '0')])
        if mutation :
            debit = mutation[0].debit
            credit = mutation[0].credit
            balance = mutation[0].balance

        return  [debit,credit,balance]

    @api.multi
    def get_final_mutation(self, closing_id, account_id):

        debit = 0
        credit = 0
        balance = 0
        mutation = self.env['account.closing.detail'].search(
            [('closing_id', '=', closing_id.id), ('account_id', '=', account_id.id), ('options', '=', '1')])
        if mutation:
            debit = mutation[0].debit
            credit = mutation[0].credit
            balance = mutation[0].balance

        return [debit, credit, balance]


class TialBalanceReportLea(models.TransientModel):
    _name = 'trial.balance.report.lea.wizard'


    company_id         = fields.Many2one('res.company', 'Company')
    account_report_id  = fields.Many2one('account.financial.report', string='Reports', required=True)
    fiscalyear_id      = fields.Many2one('account.fiscalyear')
    period_id          = fields.Many2one('account.period')
    date_from          = fields.Date('Date From')
    date_to            = fields.Date('Date To')
    target             = fields.Selection([('all', 'All'), ('posted', 'Posted')], default='posted')
    data               = fields.Binary('File', readonly=True)
    name               = fields.Char('Filename', readonly=True)
    state_position     = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    area_lks_id        = fields.Many2many('account.area.location')

    @api.multi
    @api.onchange('period_id')
    def onchange_period_id(self):
        list = []
        values = {
            'date_from': False,
            'date_to'  : False

        }
        if self.period_id:
            values['date_from'] = self.period_id.date_start
            values['date_to']   = self.period_id.date_stop
        self.update(values)


    @api.multi
    def generate_report(self):
        company = self.env['res.company'].sudo().search([('parent_id', '=', False)])
        account_report = self.env['account.financial.report'].sudo().search([('id', '=', self.account_report_id.id)])

        per = re.split("/", self.period_id.name)
        mm = int(per[0])
        bulan = dict(BULAN_SELECTION)[str(mm)]

        year = int(self.fiscalyear_id.code)
        prev_year = year - 1

        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = self.account_report_id.name + ' - ' + self.company_id.name + ' - ' + bulan + ' ' + self.fiscalyear_id.name + '.xlsx'
        workbook.add_format({'bold': 1, 'align': 'center'})
        # worksheet = workbook.add_worksheet('Report')
        worksheet1 = workbook.add_worksheet("Report Excel")
        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        center_title.set_font_size('10')
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
        header_table_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        header_table_right.set_text_wrap()
        header_table_right.set_font_size('10')
        header_table_right.set_bg_color('#eff0f2')
        header_table_right.set_border()
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        set_right.set_text_wrap()
        set_right.set_font_size('8')
        # set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_font_size('8')
        # set_border.set_border()
        #################################################################################
        set_border_bold = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'bold': 1})
        set_border_bold.set_text_wrap()
        set_border_bold.set_font_size('8')
        # set_border_bold.set_border()
        ################################################################################
        set_border_bold_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('8')
        # set_border_bold_right.set_border()

        ###TITLE REPORT ##############################################
        worksheet1.set_column('A:A', 60)
        worksheet1.set_column('B:Z', 30)

        worksheet1.set_row(0, 30)
        worksheet1.write(0, 0, company[0].name, center_title)
        worksheet1.write(1, 0, self.account_report_id.name, center_title)
        worksheet1.write(2, 0, 'Per ' + bulan + ' ' + self.fiscalyear_id.name, center_title)
        states = ['posted']
        if self.target == 'all':
            states = ['draft','posted']


        ###GENERATE BALANCE SHEET####################################

        if self.account_report_id.report_group == 'Balance Sheet':
            #Saldo Awal
            root_pl = self.env['account.financial.report'].sudo().search([('name', '=', 'LABA RUGI')], limit=1)
            account_ids_pl = self.get_account_ids_tuple(root_pl)


            #saldo berjalan
            current_balance_pl = self.get_current_balance(account_ids_pl, states) * 1
            init_balance_pl = self.get_init_balance_pl(account_ids_pl, states) * 1
            last_balance_pl = init_balance_pl + current_balance_pl

            #saldo tahun lalu
            init_pl_re = self.get_init_balance([self.company_id.re_account_id.id],states) * 1
            init_balance_pl2 =  (self.get_init_balance_pl2(account_ids_pl, states) * 1) + (init_pl_re)
            current_balance_pl2 = 0
            last_balance_pl2 = init_balance_pl2 + current_balance_pl2

            worksheet1.write(3, 0, "Periode/Uraian", header_table)
            worksheet1.write(3, 1, "S/D BULAN LALU", header_table)
            worksheet1.write(3, 2, "BULAN INI", header_table)
            worksheet1.write(3, 3, "S/D BULAN INI", header_table)
            root_lv1 = self.env['account.financial.report'].sudo().search([('parent_id', '=', self.account_report_id.id)])
            row = 4
            for lv1 in root_lv1:
                worksheet1.write(row, 0, lv1.name, set_border_bold)
                row = row + 1
                root_lv2 = self.env['account.financial.report'].sudo().search([('parent_id', '=', lv1.id)])
                for lv2 in root_lv2:
                    if lv2.type != 'accounts':
                        root_lv3 = self.env['account.financial.report'].sudo().search([('parent_id', '=', lv2.id)])
                        worksheet1.write(row, 0, lv2.name, set_border_bold)
                        row = row + 1
                        for lv3 in root_lv3 :
                            if lv3.type != 'accounts':
                                root_lv4 = self.env['account.financial.report'].sudo().search([('parent_id', '=', lv3.id)])
                                worksheet1.write(row, 0, lv3.name, set_border_bold)
                                row = row + 1
                                for lv4 in root_lv4:
                                    if lv4.type != 'accounts':
                                        worksheet1.write(row, 0, lv4.name, set_border_bold)
                                        account_ids     = self.get_account_ids_tuple(lv4)
                                        init_balance    = self.get_init_balance(account_ids,states) * lv4.sign
                                        current_balance = self.get_current_balance(account_ids,states) * lv4.sign
                                        if lv4.name in ('PASIVA'):
                                            init_balance += init_balance_pl + init_balance_pl2
                                            current_balance += current_balance_pl + current_balance_pl2
                                        last_balance    = init_balance + current_balance
                                        worksheet1.write(row, 0, 'TOTAL '+ lv4.name, header_table)
                                        worksheet1.write(row, 1, init_balance, header_table_right)
                                        worksheet1.write(row, 2, current_balance, header_table_right)
                                        worksheet1.write(row, 3, last_balance, header_table_right)
                                        row = row + 1
                                    else:
                                        account_ids = self.get_account_ids_tuple(lv4)
                                        init_balance = self.get_init_balance(account_ids, states) * lv4.sign
                                        current_balance = self.get_current_balance(account_ids, states) * lv4.sign

                                        if lv4.name in ('EKUITAS'):
                                            init_balance += init_balance_pl + init_balance_pl2
                                            current_balance += current_balance_pl + current_balance_pl2

                                        last_balance = init_balance + current_balance

                                        worksheet1.write(row, 0, lv4.name, set_border_bold)
                                        worksheet1.write(row, 1, init_balance, set_border_bold_right)
                                        worksheet1.write(row, 2, current_balance, set_border_bold_right)
                                        worksheet1.write(row, 3, last_balance, set_border_bold_right)
                                        row = row + 1
                                        for acc in lv4.account_ids:
                                            account_ids = [acc.id]
                                            init_balance = self.get_init_balance(account_ids, states) * lv4.sign
                                            current_balance = self.get_current_balance(account_ids, states) * lv4.sign
                                            last_balance = init_balance + current_balance
                                            check_zero = init_balance + current_balance + last_balance
                                            if check_zero != 0 :
                                                worksheet1.write(row, 0, '  ' + acc.code + ' ' + acc.name, set_border)
                                                worksheet1.write(row, 1, init_balance, set_right)
                                                worksheet1.write(row, 2, current_balance, set_right)
                                                worksheet1.write(row, 3, last_balance, set_right)
                                                row = row + 1
                                            if acc.code == '31200':
                                                worksheet1.write(row, 0,'  ' + self.company_id.re_account_id2.code + ' ' + self.company_id.re_account_id2.name,set_border)
                                                worksheet1.write(row, 1, init_balance_pl2, set_right)
                                                worksheet1.write(row, 2, current_balance_pl2, set_right)
                                                worksheet1.write(row, 3, last_balance_pl2, set_right)
                                                row = row + 1


                                                worksheet1.write(row, 0, '  ' + self.company_id.re_account_id.code + ' ' + self.company_id.re_account_id.name, set_border)
                                                worksheet1.write(row, 1, init_balance_pl, set_right)
                                                worksheet1.write(row, 2, current_balance_pl, set_right)
                                                worksheet1.write(row, 3, last_balance_pl, set_right)
                                                row = row + 1




                                        row = row + 1
                            else :
                                account_ids = self.get_account_ids_tuple(lv3)
                                init_balance = self.get_init_balance(account_ids, states) * lv3.sign
                                current_balance = self.get_current_balance(account_ids, states) * lv3.sign

                                if lv3.name in ('EKUITAS'):
                                    init_balance += init_balance_pl + init_balance_pl2
                                    current_balance += current_balance_pl + current_balance_pl2

                                last_balance = init_balance + current_balance
                                worksheet1.write(row, 0, lv3.name, set_border_bold)
                                worksheet1.write(row, 1, init_balance, set_border_bold_right)
                                worksheet1.write(row, 2, current_balance, set_border_bold_right)
                                worksheet1.write(row, 3, last_balance, set_border_bold_right)
                                row = row + 1
                                for acc in lv3.account_ids:
                                    account_ids = [acc.id]
                                    init_balance = self.get_init_balance(account_ids, states) * lv3.sign
                                    current_balance = self.get_current_balance(account_ids, states) * lv3.sign
                                    last_balance = init_balance + current_balance
                                    check_zero = init_balance + current_balance + last_balance
                                    if check_zero != 0 :
                                        worksheet1.write(row, 0, '  ' + acc.code + ' ' + acc.name, set_border)
                                        worksheet1.write(row, 1, init_balance, set_right)
                                        worksheet1.write(row, 2, current_balance, set_right)
                                        worksheet1.write(row, 3, last_balance, set_right)
                                        row = row + 1
                                    if acc.code == '31200':
                                        worksheet1.write(row, 0,'  ' + self.company_id.re_account_id2.code + ' ' + self.company_id.re_account_id2.name,set_border)
                                        worksheet1.write(row, 1, init_balance_pl2, set_right)
                                        worksheet1.write(row, 2, current_balance_pl2, set_right)
                                        worksheet1.write(row, 3, last_balance_pl2, set_right)
                                        row = row + 1

                                        worksheet1.write(row, 0,'  ' + self.company_id.re_account_id.code + ' ' + self.company_id.re_account_id.name,set_border)
                                        worksheet1.write(row, 1, init_balance_pl, set_right)
                                        worksheet1.write(row, 2, current_balance_pl, set_right)
                                        worksheet1.write(row, 3, last_balance_pl, set_right)
                                        row = row + 1
                                row = row + 1

                        account_ids = self.get_account_ids_tuple(lv2)
                        init_balance = self.get_init_balance(account_ids, states) * lv2.sign
                        current_balance = self.get_current_balance(account_ids, states) * lv2.sign
                        if lv2.name in ('PASIVA'):
                            init_balance += init_balance_pl + init_balance_pl2
                            current_balance += current_balance_pl + current_balance_pl2
                        last_balance = init_balance + current_balance

                        worksheet1.write(row, 0, 'TOTAL ' + lv2.name, header_table)
                        worksheet1.write(row, 1, init_balance, header_table_right)
                        worksheet1.write(row, 2, current_balance, header_table_right)
                        worksheet1.write(row, 3, last_balance, header_table_right)
                        row = row + 1
                    else:
                        account_ids = self.get_account_ids_tuple(lv2)
                        init_balance = self.get_init_balance(account_ids, states) * lv2.sign
                        current_balance = self.get_current_balance(account_ids, states) * lv2.sign
                        if lv2.name in ('EKUITAS'):
                            init_balance += init_balance_pl + init_balance_pl2
                            current_balance += current_balance_pl + current_balance_pl2
                        last_balance = init_balance + current_balance
                        worksheet1.write(row, 0, lv2.name, set_border_bold)
                        worksheet1.write(row, 1, init_balance, set_border_bold_right)
                        worksheet1.write(row, 2, current_balance, set_border_bold_right)
                        worksheet1.write(row, 3, last_balance, set_border_bold_right)
                        row = row + 1
                        for acc in lv2.account_ids :
                            account_ids = [acc.id]
                            init_balance = self.get_init_balance(account_ids, states) * lv2.sign
                            current_balance = self.get_current_balance(account_ids, states) * lv2.sign

                            last_balance = init_balance + current_balance
                            check_zero = init_balance + current_balance + last_balance

                            if check_zero != 0:
                                worksheet1.write(row, 0, '  '+acc.code+' '+acc.name, set_border)
                                worksheet1.write(row, 1, init_balance, set_right)
                                worksheet1.write(row, 2, current_balance, set_right)
                                worksheet1.write(row, 3, last_balance, set_right)
                                row = row + 1
                            if acc.code == '31200':
                                worksheet1.write(row, 0,'  ' + self.company_id.re_account_id2.code + ' ' + self.company_id.re_account_id2.name,set_border)
                                worksheet1.write(row, 1, init_balance_pl2, set_right)
                                worksheet1.write(row, 2, current_balance_pl2, set_right)
                                worksheet1.write(row, 3, last_balance_pl2, set_right)
                                row = row + 1

                                worksheet1.write(row, 0, '  ' + self.company_id.re_account_id.code + ' ' + self.company_id.re_account_id.name,set_border)
                                worksheet1.write(row, 1, init_balance_pl, set_right)
                                worksheet1.write(row, 2, current_balance_pl, set_right)
                                worksheet1.write(row, 3, last_balance_pl, set_right)
                                row = row + 1
                        row = row + 1

                account_ids = self.get_account_ids_tuple(lv1)
                init_balance = self.get_init_balance(account_ids, states) * lv1.sign
                current_balance = self.get_current_balance(account_ids, states) * lv1.sign

                if lv1.name in ('PASIVA'):
                    init_balance += init_balance_pl + init_balance_pl2
                    current_balance += current_balance_pl + current_balance_pl2
                last_balance = init_balance + current_balance

                worksheet1.write(row, 0, 'TOTAL ' + lv1.name, header_table)
                worksheet1.write(row, 1, init_balance, header_table_right)
                worksheet1.write(row, 2, current_balance, header_table_right)
                worksheet1.write(row, 3, last_balance, header_table_right)
                row = row + 2


        if self.account_report_id.report_group == 'Profit and Loss':
            worksheet1.write(3, 0, "Uraian test", header_table)
            worksheet1.write(3, 1, 'S/D BULAN LALU', header_table)
            worksheet1.write(3, 2, 'BULAN INI', header_table)
            worksheet1.write(3, 3, 'S/D BULAN INI', header_table)

            root_lv1 = self.env['account.financial.report'].sudo().search([('parent_id', '=', self.account_report_id.id)])
            row = 4
            total_curr_laba = 0
            total_init_laba = 0
            total_last_laba = 0
            for lv1 in root_lv1:
                if lv1.type != 'accounts':
                    account_ids = self.get_account_ids_tuple(lv1)
                    init_balance = self.get_init_balance_pl(account_ids, states) * lv1.sign
                    current_balance = self.get_current_balance(account_ids, states) * lv1.sign
                    last_balance = init_balance + current_balance

                    worksheet1.write(row, 0, lv1.name, set_border_bold)
                    worksheet1.write(row, 1, init_balance, set_border_bold_right)
                    worksheet1.write(row, 2, current_balance, set_border_bold_right)
                    worksheet1.write(row, 3, last_balance, set_border_bold_right)

                    row = row + 1
                    root_lv2 = self.env['account.financial.report'].sudo().search([('parent_id', '=', lv1.id)])
                    for lv2 in root_lv2 :
                        if lv2.type != 'accounts':
                            account_ids = self.get_account_ids_tuple(lv2)
                            init_balance = self.get_init_balance_pl(account_ids, states) * lv2.sign
                            current_balance = self.get_current_balance(account_ids, states) * lv2.sign
                            last_balance = init_balance + current_balance

                            worksheet1.write(row, 0, lv2.name, set_border_bold)
                            worksheet1.write(row, 1, init_balance, set_border_bold_right)
                            worksheet1.write(row, 2, current_balance, set_border_bold_right)
                            worksheet1.write(row, 3, last_balance, set_border_bold_right)
                            row = row + 1
                            root_lv3 = self.env['account.financial.report'].sudo().search([('parent_id', '=', lv2.id)])
                            for lv3 in root_lv3 :
                                if lv3.type != 'accounts':
                                    account_ids = self.get_account_ids_tuple(lv3)
                                    init_balance = self.get_init_balance_pl(account_ids, states) * lv3.sign
                                    current_balance = self.get_current_balance(account_ids, states) * lv3.sign
                                    last_balance = init_balance + current_balance
                                    worksheet1.write(row, 0, lv3.name, set_border_bold)
                                    worksheet1.write(row, 1, init_balance, set_border_bold_right)
                                    worksheet1.write(row, 2, current_balance, set_border_bold_right)
                                    worksheet1.write(row, 3, last_balance, set_border_bold_right)
                                    row = row + 1

                                    root_lv4 = self.env['account.financial.report'].sudo().search([('parent_id', '=', lv3.id)])
                                    for lv4 in root_lv4 :
                                        if lv4.type != 'accounts':
                                            account_ids = self.get_account_ids_tuple(lv4)
                                            init_balance = self.get_init_balance_pl(account_ids, states) * lv4.sign
                                            current_balance = self.get_current_balance(account_ids, states) * lv4.sign
                                            last_balance = init_balance + current_balance

                                            worksheet1.write(row, 0, lv4.name, set_border_bold)
                                            worksheet1.write(row, 1, init_balance, set_border_bold_right)
                                            worksheet1.write(row, 2, current_balance, set_border_bold_right)
                                            worksheet1.write(row, 3, last_balance, set_border_bold_right)

                                            row = row + 1
                                        else:
                                            account_ids = self.get_account_ids_tuple(lv4)
                                            init_balance = self.get_init_balance_pl(account_ids, states) * lv4.sign
                                            current_balance = self.get_current_balance(account_ids, states) * lv4.sign
                                            last_balance = init_balance + current_balance


                                            worksheet1.write(row, 0, '  ' + lv4.name, set_border_bold)
                                            worksheet1.write(row, 1, init_balance, set_border_bold_right)
                                            worksheet1.write(row, 2, current_balance, set_border_bold_right)
                                            worksheet1.write(row, 3, last_balance, set_border_bold_right)

                                            row = row + 1
                                            for acc in lv4.account_ids:
                                                account_ids = [acc.id]
                                                init_balance = self.get_init_balance_pl(account_ids, states) * lv4.sign
                                                current_balance = self.get_current_balance(account_ids,states) * lv4.sign
                                                last_balance = init_balance + current_balance
                                                check_zero = init_balance + current_balance + last_balance
                                                if check_zero != 0:
                                                    worksheet1.write(row, 0, '  ' + acc.code + ' ' + acc.name, set_border)
                                                    worksheet1.write(row, 1, init_balance, set_right)
                                                    worksheet1.write(row, 2, current_balance, set_right)
                                                    worksheet1.write(row, 3, last_balance, set_right)
                                                    row = row + 1

                                            row = row + 1
                                else:

                                    account_ids = self.get_account_ids_tuple(lv3)
                                    init_balance = self.get_init_balance_pl(account_ids, states) * lv3.sign
                                    current_balance = self.get_current_balance(account_ids, states) * lv3.sign
                                    last_balance = init_balance + current_balance

                                    worksheet1.write(row, 0, '  ' + lv3.name, set_border_bold)
                                    worksheet1.write(row, 1, init_balance, set_border_bold_right)
                                    worksheet1.write(row, 2, current_balance, set_border_bold_right)
                                    worksheet1.write(row, 3, last_balance, set_border_bold_right)

                                    row = row + 1
                                    for acc in lv3.account_ids:
                                        account_ids = [acc.id]
                                        init_balance = self.get_init_balance_pl(account_ids, states) * lv3.sign
                                        current_balance = self.get_current_balance(account_ids, states) * lv3.sign
                                        last_balance = init_balance + current_balance
                                        check_zero = init_balance + current_balance + last_balance
                                        if check_zero != 0:
                                            worksheet1.write(row, 0, '  ' + acc.code + ' ' + acc.name, set_border)
                                            worksheet1.write(row, 1, init_balance, set_right)
                                            worksheet1.write(row, 2, current_balance, set_right)
                                            worksheet1.write(row, 3, last_balance, set_right)

                                            row = row + 1

                                    row = row + 1
                            row = row + 1
                            summary = '  TOTAL ' + lv2.name
                            summary_laba = 'LABA ' + lv2.name

                            account_ids = self.get_account_ids_tuple(lv2)
                            init_balance = self.get_init_balance_pl(account_ids, states) * lv2.sign
                            current_balance = self.get_current_balance(account_ids, states) * lv2.sign
                            last_balance = init_balance + current_balance

                            worksheet1.write(row, 0, summary, set_border_bold)
                            worksheet1.write(row, 1, init_balance, set_border_bold_right)
                            worksheet1.write(row, 2, current_balance, set_border_bold_right)
                            worksheet1.write(row, 3, last_balance, set_border_bold_right)


                        else :
                            account_ids = self.get_account_ids_tuple(lv2)
                            init_balance = self.get_init_balance_pl(account_ids, states) * lv2.sign
                            current_balance = self.get_current_balance(account_ids, states) * lv2.sign
                            last_balance = init_balance + current_balance

                            worksheet1.write(row, 0, '  ' + lv2.name, set_border_bold)
                            worksheet1.write(row, 1, init_balance, set_border_bold_right)
                            worksheet1.write(row, 2, current_balance, set_border_bold_right)
                            worksheet1.write(row, 3, last_balance, set_border_bold_right)

                            row = row + 1
                            for acc in lv2.account_ids:
                                account_ids = [acc.id]
                                init_balance = self.get_init_balance_pl(account_ids, states) * lv2.sign
                                current_balance = self.get_current_balance(account_ids, states) * lv2.sign
                                last_balance = init_balance + current_balance
                                check_zero = init_balance + current_balance + last_balance
                                if check_zero != 0:
                                    worksheet1.write(row, 0, '  ' + acc.code + ' ' + acc.name, set_border)
                                    worksheet1.write(row, 1, init_balance, set_right)
                                    worksheet1.write(row, 2, current_balance, set_right)
                                    worksheet1.write(row, 3, last_balance, set_right)

                                    row = row + 1

                            row = row + 1

                    row = row + 1


                else :
                    account_ids = self.get_account_ids_tuple(lv1)
                    init_balance = self.get_init_balance_pl(account_ids, states) * lv1.sign
                    current_balance = self.get_current_balance(account_ids, states) * lv1.sign
                    last_balance = init_balance + current_balance

                    worksheet1.write(row, 0, '  '+lv1.name, set_border_bold)
                    worksheet1.write(row, 1, init_balance, set_border_bold_right)
                    worksheet1.write(row, 2, current_balance, set_border_bold_right)
                    worksheet1.write(row, 3, last_balance, set_border_bold_right)

                    row = row + 1
                    for acc in lv1.account_ids:
                        account_ids = [acc.id]
                        init_balance = self.get_init_balance_pl(account_ids, states) * lv1.sign
                        current_balance = self.get_current_balance(account_ids, states) * lv1.sign
                        last_balance = init_balance + current_balance
                        check_zero = init_balance + current_balance + last_balance
                        if check_zero != 0:
                            worksheet1.write(row, 0, '  ' + acc.code + ' ' + acc.name, set_border)
                            worksheet1.write(row, 1, init_balance, set_right)
                            worksheet1.write(row, 2, current_balance, set_right)
                            worksheet1.write(row, 3, last_balance, set_right)
                            row = row + 1

                    summary = '  TOTAL ' + lv1.name
                    summary_laba = ''

                    if lv1.sequence == 2:
                        summary_laba = '  LABA (RUGI) KOTOR'
                    elif lv1.sequence == 5:
                        summary_laba = '  LABA (RUGI) USAHA'
                    elif lv1.sequence == 7:
                        summary_laba = '  LABA (RUGI) BERSIH'

                    account_ids = self.get_account_ids_tuple(lv1)
                    init_balance = self.get_init_balance_pl(account_ids, states) * lv1.sign
                    current_balance = self.get_current_balance(account_ids, states) * lv1.sign
                    last_balance = init_balance + current_balance

                    worksheet1.write(row, 0, summary, set_border_bold)
                    worksheet1.write(row, 1, init_balance, set_border_bold_right)
                    worksheet1.write(row, 2, current_balance, set_border_bold_right)
                    worksheet1.write(row, 3, last_balance, set_border_bold_right)

                    total_curr_laba = total_curr_laba + current_balance
                    total_init_laba = total_init_laba + init_balance
                    total_last_laba = total_last_laba + last_balance
                    row = row + 1

                    if lv1.sequence not in (1,3,4,6):
                        worksheet1.write(row, 0, summary_laba, set_border_bold)
                        worksheet1.write(row, 1, total_init_laba, set_border_bold_right)
                        worksheet1.write(row, 2, total_curr_laba, set_border_bold_right)
                        worksheet1.write(row, 3, total_last_laba, set_border_bold_right)
                    else :
                        row = row - 1

                    row = row + 2


        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'account_report_lea', 'trial_balance_lea_report_wizard')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'trial.balance.report.lea.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_account_ids(self, report_id):
        account_report = self.env['account.financial.report'].sudo().search([('id', '=', report_id)])
        child_reports = account_report._get_children_by_order()
        account_ids = []
        for report in child_reports:
            if report.type != 'sum':
                for account in report.account_ids:
                    account_ids.append(account.id)
        return account_ids

    @api.multi
    def get_account_ids_tuple(self, report_id):
        account_ids = []
        for r in report_id:
            account_report = self.env['account.financial.report'].sudo().search([('id', '=', r.id)])
            child_reports = account_report._get_children_by_order()
            for report in child_reports:
                if report.type != 'sum':
                    for account in report.account_ids:
                        account_ids.append(account.id)
        return account_ids

    @api.multi
    def get_current_balance(self, account_id, states):
        cursor = self.env.cr
        debit   = 0
        credit  = 0
        balance = 0

        area = []
        for ar in self.area_lks_id:
            area.append(ar.id)

        if account_id :
            for line in self:
                if not self.area_lks_id :
                    cursor.execute(
                    """
                    select
                        sum(a.debit) as debit,
                        sum(a.credit) as credit,
                        sum(a.debit) - sum(a.credit) as balance
                    from
                        account_move_line as a,account_move as b
                    where
                        b.id = a.move_id and
                        b.state in %s and
                        a.account_id in %s and
                        a.date between %s and %s

                    """, (tuple(states), tuple(account_id), line.date_from, line.date_to))
                else :
                    cursor.execute(
                    """
                        select
                            sum(a.debit) as debit,
                            sum(a.credit) as credit,
                            sum(a.debit) - sum(a.credit) as balance
                        from
                            account_move_line as a,account_move as b
                        where
                            b.id = a.move_id and
                            b.state in %s and
                            b.area_lks in %s and
                            a.account_id in %s and
                            a.date between %s and %s
                    """, (tuple(states), tuple(area), tuple(account_id), line.date_from, line.date_to,))

            val = cursor.fetchone()
            if val[0] != None:
                debit = val[0]
            if val[1] != None:
                credit = val[1]
            if val[2] != None:
                balance = val[2]
        return balance

    @api.multi
    def get_init_balance(self, account_id, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0
        area = []
        for ar in self.area_lks_id:
            area.append(ar.id)

        if account_id :
            for line in self:
                if not self.area_lks_id:
                    cursor.execute(
                        """
                        select
                            sum(a.debit) as debit,
                            sum(a.credit) as credit,
                            sum(a.debit) - sum(a.credit) as balance
                        from
                            account_move_line as a,account_move as b
                        where
                            b.id = a.move_id and
                            b.state in %s and
                            a.account_id in %s and
                            a.date < %s

                        """, (tuple(states), tuple(account_id), line.date_from))
                else :
                    cursor.execute(
                        """
                        select
                            sum(a.debit) as debit,
                            sum(a.credit) as credit,
                            sum(a.debit) - sum(a.credit) as balance
                        from
                            account_move_line as a,account_move as b
                        where
                            b.id = a.move_id and
                            b.state in %s and
                            b.area_lks in %s and
                            a.account_id in %s and
                            a.date < %s
                        """, (tuple(states), tuple(area), tuple(account_id), line.date_from,))
                val = cursor.fetchone()
                if val[0] != None:
                    debit = val[0]
                if val[1] != None:
                    credit = val[1]
                if val[2] != None:
                    balance = val[2]
        return balance

    @api.multi
    def get_init_balance_pl(self, account_id, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0

        per = re.split("/", self.period_id.name)
        mm = int(per[0])

        date_from = str(self.fiscalyear_id.name)+'-01-01'

        area = []
        for ar in self.area_lks_id:
            area.append(ar.id)

        if mm != 1 :
            if account_id:
                for line in self:
                    if not self.area_lks_id:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date < %s

                            """, (tuple(states), tuple(account_id), date_from, line.date_from))
                    else:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                b.area_lks in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date < %s
                            """, (tuple(states), tuple(area), tuple(account_id), date_from, line.date_from))
                    val = cursor.fetchone()
                    if val[0] != None:
                        debit = val[0]
                    if val[1] != None:
                        credit = val[1]
                    if val[2] != None:
                        balance = val[2]
        return balance


    @api.multi
    def get_init_balance_pl_last(self, account_id, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0

        per = re.split("/", self.period_id.name)
        mm = int(per[0])

        date_from = str(int(self.fiscalyear_id.name)-1) + '-01-01'
        date_to   = str(int(self.fiscalyear_id.name)-1) + '-12-31'

        area = []
        for ar in self.area_lks_id:
            area.append(ar.id)

        if mm != 1:
            if account_id:
                for line in self:
                    if not self.area_lks_id:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date <= %s

                            """, (tuple(states), tuple(account_id), date_from, date_to))
                    else:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                b.area_lks in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date <= %s
                            """, (tuple(states), tuple(area), tuple(account_id), date_from, date_to))
                    val = cursor.fetchone()
                    if val[0] != None:
                        debit = val[0]
                    if val[1] != None:
                        credit = val[1]
                    if val[2] != None:
                        balance = val[2]
        return balance

    @api.multi
    def get_init_balance_pl2(self, account_id, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0

        per = re.split("/", self.period_id.name)
        mm = int(per[0])
        last_year = int(self.fiscalyear_id.name)-1
        date_from = str(last_year) + '-01-01'
        date_to   = str(last_year) + '-12-31'

        area = []
        for ar in self.area_lks_id:
            area.append(ar.id)

        if mm != 1:
            if account_id:
                for line in self:
                    if not self.area_lks_id:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date < %s

                            """, (tuple(states), tuple(account_id), date_from, date_to))
                    else:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                b.area_lks in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date < %s
                            """, (tuple(states), tuple(area), tuple(account_id), date_from, date_to))
                    val = cursor.fetchone()
                    if val[0] != None:
                        debit = val[0]
                    if val[1] != None:
                        credit = val[1]
                    if val[2] != None:
                        balance = val[2]
        return balance



class RekapBukuBesar(models.TransientModel):
    _name = 'rekap.buku.besar.wizard'


    company         = fields.Many2one('res.company', 'Company')
    account         = fields.Many2many('account.account')
    partner         = fields.Many2one('res.partner')
    area_lks_id     = fields.Many2many('account.area.location')
    period_id       = fields.Many2one('account.period')
    date_from       = fields.Date('Date From')
    date_to         = fields.Date('Date To')
    data            = fields.Binary('File', readonly=True)
    name            = fields.Char('Filename', readonly=True)
    target          = fields.Selection([('all', 'All'), ('posted', 'Posted')], default='posted')
    state_position  = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

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
    def generate_excel(self):

        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'Rekapitulasi Buku Besar' + '_' + self.company.name + '.xlsx'
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

        worksheet1.set_column('A:A', 10)
        worksheet1.set_column('B:B', 45)
        worksheet1.set_column('C:AC', 15)


        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.set_row(0, 30)
        worksheet1.merge_range('A1:G1', self.company.name, center_title)
        worksheet1.merge_range('A2:G2', 'Rekapitulasi Buku Besar', center_title)
        worksheet1.merge_range('A3:G3', date_from + ' s/d ' + date_to, center_title)

        account = self.env['account.account'].search([('company_id', '=', self.company.id)])
        if self.account:
            account = self.account

        states = ['posted']
        if self.target == 'all':
            states = ['draft', 'posted']

        area = []
        area_nama = ''
        for ar in self.area_lks_id:
            area.append(ar.id)
            area_nama += ar.name+' '

        worksheet1.merge_range('A4:G4', ' cabang ' + area_nama, center_title)

        worksheet1.write(5, 0, 'No. Rek', header_table)
        worksheet1.write(5, 1, 'Nama Rekening', header_table)
        worksheet1.write(5, 2, 'S.Awal (D)', header_table)
        worksheet1.write(5, 3, 'S.Awal (K)', header_table)
        worksheet1.write(5, 4, 'Mutasi Debit', header_table)
        worksheet1.write(5, 5, 'Mutasi Kredit', header_table)
        worksheet1.write(5, 6, 'Rugi Debit', header_table)
        worksheet1.write(5, 7, '/Laba Kredit', header_table)
        worksheet1.write(5, 8, 'Neraca Debit', header_table)
        worksheet1.write(5, 9, 'Neraca Kredit', header_table)

        row = 6

        sum_sa_debit = 0
        sum_sa_credit = 0

        sum_mutasi_debit = 0
        sum_mutasi_credit = 0

        sum_lr_debit = 0
        sum_lr_credit = 0

        sum_neraca_debit = 0
        sum_neraca_credit = 0

        for acc in account:
            # Search Move Line Transaction

            if acc.user_type_id.name in ('Expenses','Income'):
                saldo_awal = self.get_init_balance_pl([acc.id], states)
            else:
                saldo_awal = self.get_balance(acc, self.date_from, self.company, area, states)
            mutasi     = self.get_balance2(acc, self.date_from, self.date_to, self.company, area, states)
            saldo_akhir = saldo_awal[2] + mutasi[2]
            saldo_awal_debit = saldo_awal[2]
            saldo_awal_kredit = 0
            if saldo_awal[2] < 0 :
                saldo_awal_debit = 0
                saldo_awal_kredit = abs(saldo_awal[2])
            rugi_debit = 0
            laba_kredit = 0
            neraca_debit = 0
            neraca_kredit = 0
            if acc.user_type_id.name in ('Expenses','Income'):
                rugi_debit = saldo_akhir
                laba_kredit = 0
                if saldo_akhir < 0 :
                    rugi_debit = 0
                    laba_kredit = abs(saldo_akhir)
            else:
                neraca_debit = saldo_akhir
                neraca_kredit = 0
                if saldo_akhir < 0 :
                    neraca_debit = 0
                    neraca_kredit = abs(saldo_akhir)
            if saldo_awal_kredit + saldo_awal_debit + mutasi[0] + mutasi[1]+rugi_debit + laba_kredit + neraca_debit + neraca_kredit !=0 :
                worksheet1.write(row, 0, acc.code, set_border)
                worksheet1.write(row, 1, acc.name, set_border)
                worksheet1.write(row, 2, saldo_awal_debit, set_right)
                worksheet1.write(row, 3, saldo_awal_kredit, set_right)
                worksheet1.write(row, 4, mutasi[0], set_right)
                worksheet1.write(row, 5, mutasi[1], set_right)
                worksheet1.write(row, 6, rugi_debit, set_right)
                worksheet1.write(row, 7, laba_kredit, set_right)
                worksheet1.write(row, 8, neraca_debit, set_right)
                worksheet1.write(row, 9, neraca_kredit, set_right)
                row = row + 1

            sum_sa_debit = sum_sa_debit + saldo_awal_debit
            sum_sa_credit = sum_sa_credit + saldo_awal_kredit

            sum_mutasi_debit = sum_mutasi_debit + mutasi[0]
            sum_mutasi_credit = sum_mutasi_credit + mutasi[1]

            sum_lr_debit = sum_lr_debit + rugi_debit
            sum_lr_credit = sum_lr_credit + laba_kredit

            sum_neraca_debit = sum_neraca_debit + neraca_debit
            sum_neraca_credit = sum_neraca_credit + neraca_kredit

        worksheet1.write(row, 0, '', set_border_bold)
        worksheet1.write(row, 1, '', set_border_bold)
        worksheet1.write(row, 2, sum_sa_debit, set_border_bold_right)
        worksheet1.write(row, 3, sum_sa_credit, set_border_bold_right)
        worksheet1.write(row, 4, sum_mutasi_debit, set_border_bold_right)
        worksheet1.write(row, 5, sum_mutasi_credit, set_border_bold_right)
        worksheet1.write(row, 6, sum_lr_debit, set_border_bold_right)
        worksheet1.write(row, 7, sum_lr_credit, set_border_bold_right)
        worksheet1.write(row, 8, sum_neraca_debit, set_border_bold_right)
        worksheet1.write(row, 9, sum_neraca_credit, set_border_bold_right)

        row = row + 1


        selisih_lr = sum_lr_credit - sum_lr_debit
        posisi_lr_debit = abs(selisih_lr)
        posisi_lr_credit = 0
        if selisih_lr > 0 :
            posisi_lr_debit = 0
            posisi_lr_credit = abs(selisih_lr)

        selisih_neraca = sum_neraca_credit - sum_neraca_debit
        posisi_nrc_debit = abs(selisih_neraca)
        posisi_nrc_credit = 0
        if selisih_neraca > 0 :
            posisi_nrc_debit = 0
            posisi_nrc_credit = abs(selisih_neraca)

        worksheet1.write(row, 0, '', set_border_bold)
        worksheet1.write(row, 1, 'Saldo Laba/Rugi', set_border_bold)
        worksheet1.write(row, 2,'', set_border_bold_right)
        worksheet1.write(row, 3,'', set_border_bold_right)
        worksheet1.write(row, 4,'', set_border_bold_right)
        worksheet1.write(row, 5,'', set_border_bold_right)
        worksheet1.write(row, 6, posisi_lr_debit, set_border_bold_right)
        worksheet1.write(row, 7, posisi_lr_credit, set_border_bold_right)
        worksheet1.write(row, 8, posisi_nrc_debit, set_border_bold_right)
        worksheet1.write(row, 9, posisi_nrc_credit, set_border_bold_right)

        row = row + 1
        total_posisi_lr_debit = sum_lr_debit + posisi_lr_debit
        total_posisi_lr_credit = sum_lr_credit + posisi_lr_credit

        total_posisi_nrc_debit = sum_neraca_debit + posisi_nrc_debit
        total_posisi_nrc_credit = sum_neraca_credit + posisi_nrc_credit

        worksheet1.write(row, 0, '', set_border_bold)
        worksheet1.write(row, 1, '', set_border_bold)
        worksheet1.write(row, 2, '', set_border_bold_right)
        worksheet1.write(row, 3, '', set_border_bold_right)
        worksheet1.write(row, 4, '', set_border_bold_right)
        worksheet1.write(row, 5, '', set_border_bold_right)
        worksheet1.write(row, 6, total_posisi_lr_debit, set_border_bold_right)
        worksheet1.write(row, 7, total_posisi_lr_credit, set_border_bold_right)
        worksheet1.write(row, 8, total_posisi_nrc_debit, set_border_bold_right)
        worksheet1.write(row, 9, total_posisi_nrc_credit, set_border_bold_right)



        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'account_report_lea', 'rekap_buku_besar_lea_wizard_view_forms')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rekap.buku.besar.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_balance(self, account, date, company, area, state):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0
        for line in self:
            if account:
                if not area :
                    cursor.execute("""
                                        select
                                            sum(a.debit) as debit,
                                            sum(a.credit) as credit,
                                            sum(a.debit - a.credit) as balance
                                        from
                                            account_move_line as a, account_move as b
                                        where
                                            a.move_id = b.id and
                                            a.account_id = %s and
                                            a.date < %s and
                                            b.state in %s and
                                            b.company_id = %s
                                            """, (account.id, date, tuple(state), company.id))
                else:
                    cursor.execute("""
                                        select
                                            sum(a.debit) as debit,
                                            sum(a.credit) as credit,
                                            sum(a.debit - a.credit) as balance
                                        from
                                            account_move_line as a, account_move as b
                                        where
                                            a.move_id = b.id and
                                            a.account_id = %s and
                                            a.date < %s and
                                            b.state in %s and
                                            b.area_lks in %s and
                                            b.company_id = %s
                                            """, (account.id, date, tuple(state), tuple(area), company.id))
                val = cursor.fetchone()
                if val[0] != None:
                    debit = val[0]
                if val[1] != None:
                    credit = val[1]
                if val[2] != None:
                    balance = val[2]
        return [debit, credit, balance]

    @api.multi
    def get_balance2(self, account, date_from, date_to, company, area, state):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0
        for line in self:
            if account:
                if not area:
                    cursor.execute("""
                                           select
                                               sum(a.debit) as debit,
                                               sum(a.credit) as credit,
                                               sum(a.debit - a.credit) as balance
                                           from
                                               account_move_line as a, account_move as b
                                           where
                                               a.move_id = b.id and
                                               a.account_id = %s and
                                               b.state in %s and
                                               b.company_id = %s and
                                               a.date between %s and %s
                                               """, (account.id, tuple(state), company.id, date_from, date_to))
                else:
                    cursor.execute("""
                                           select
                                               sum(a.debit) as debit,
                                               sum(a.credit) as credit,
                                               sum(a.debit - a.credit) as balance
                                           from
                                               account_move_line as a, account_move as b
                                           where
                                               a.move_id = b.id and
                                               a.account_id = %s and
                                               b.state in %s and
                                               b.area_lks in %s and
                                               b.company_id = %s and
                                               a.date between %s and %s
                                               """, (account.id, tuple(state), tuple(area), company.id, date_from, date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    debit = val[0]
                if val[1] != None:
                    credit = val[1]
                if val[2] != None:
                    balance = val[2]
        return [debit, credit, balance]

    @api.multi
    def get_init_balance_pl(self, account_id, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0

        per = re.split("/", self.period_id.name)
        mm = int(per[0])

        date_from = str(self.period_id.fiscalyear_id.name) + '-01-01'

        area = []
        for ar in self.area_lks_id:
            area.append(ar.id)

        if mm != 1:
            if account_id:
                for line in self:
                    if not self.area_lks_id:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date < %s

                            """, (tuple(states), tuple(account_id), date_from, line.date_from))
                    else:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                b.area_lks in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date < %s
                            """, (tuple(states), tuple(area), tuple(account_id), date_from, line.date_from))
                    val = cursor.fetchone()
                    if val[0] != None:
                        debit = val[0]
                    if val[1] != None:
                        credit = val[1]
                    if val[2] != None:
                        balance = val[2]
        return [debit,credit,balance]


class CashFlowReportLea(models.TransientModel):
    _name = 'cf.report.lea.wizard'


    company_id         = fields.Many2one('res.company', 'Company')
    account_report_id  = fields.Many2one('account.financial.report', string='Reports', required=True)
    fiscalyear_id      = fields.Many2one('account.fiscalyear')
    period_id          = fields.Many2one('account.period')
    date_from          = fields.Date('Date From')
    date_to            = fields.Date('Date To')
    target             = fields.Selection([('all', 'All'), ('posted', 'Posted')], default='posted')
    data               = fields.Binary('File', readonly=True)
    name               = fields.Char('Filename', readonly=True)
    state_position     = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    area_lks_id        = fields.Many2many('account.area.location')

    @api.multi
    @api.onchange('period_id')
    def onchange_period_id(self):
        list = []
        values = {
            'date_from': False,
            'date_to'  : False

        }
        if self.period_id:
            values['date_from'] = self.period_id.date_start
            values['date_to']   = self.period_id.date_stop
        self.update(values)


    @api.multi
    def generate_report(self):
        company = self.env['res.company'].sudo().search([('parent_id', '=', False)])
        account_report = self.env['account.financial.report'].sudo().search([('id', '=', self.account_report_id.id)])

        per = re.split("/", self.period_id.name)
        mm = int(per[0])
        bulan = dict(BULAN_SELECTION)[str(mm)]

        year = int(self.fiscalyear_id.code)
        prev_year = year - 1

        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = self.account_report_id.name + ' - ' + self.company_id.name + ' - ' + bulan + ' ' + self.fiscalyear_id.name + '.xlsx'
        workbook.add_format({'bold': 1, 'align': 'center'})
        # worksheet = workbook.add_worksheet('Report')
        worksheet1 = workbook.add_worksheet("Report Excel")
        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        center_title.set_font_size('10')
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
        header_table_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        header_table_right.set_text_wrap()
        header_table_right.set_font_size('10')
        header_table_right.set_bg_color('#eff0f2')
        header_table_right.set_border()
        #################################################################################
        header_table_pink = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        header_table_pink.set_text_wrap()
        header_table_pink.set_font_size('10')
        header_table_pink.set_bg_color('#ffcccc')
        header_table_pink.set_border()
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        set_right.set_text_wrap()
        set_right.set_font_size('8')
        # set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_font_size('8')
        # set_border.set_border()
        #################################################################################
        set_border_bold = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'bold': 1})
        set_border_bold.set_text_wrap()
        set_border_bold.set_font_size('8')
        # set_border_bold.set_border()
        ################################################################################
        set_border_bold_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('8')
        # set_border_bold_right.set_border()

        ###TITLE REPORT ##############################################
        worksheet1.set_column('A:A', 10)
        worksheet1.set_column('B:B', 40)
        worksheet1.set_column('C:C', 5)
        worksheet1.set_column('D:Z', 20)

        worksheet1.set_row(0, 30)
        worksheet1.write(0, 0, company[0].name, center_title)
        worksheet1.write(1, 0, self.account_report_id.name, center_title)
        worksheet1.write(2, 0, 'Per ' + bulan + ' ' + self.fiscalyear_id.name, center_title)
        states = ['posted']
        if self.target == 'all':
            states = ['draft','posted']

        ###GENERATE BALANCE SHEET###################################
        if self.account_report_id.report_group == 'Profit and Loss':
            worksheet1.write(3, 0, "Kode CF", header_table)
            worksheet1.write(3, 1, 'Keterangan', header_table)
            worksheet1.write(3, 2, ' ', header_table)
            worksheet1.write(3, 3, 'Bulan Ini', header_table)
            worksheet1.write(3, 4, 'YTD', header_table)
            root_lv1 = self.env['account.financial.report'].sudo().search([('parent_id', '=', self.account_report_id.id)])
            row = 4
            for lv1 in root_lv1:
                if lv1.type != 'accounts':

                    this_month = 0
                    amount_ytd = 0
                    worksheet1.write(row, 0, ' ', header_table)
                    worksheet1.write(row, 1, lv1.name, header_table)
                    worksheet1.write(row, 2, ' ', header_table)
                    worksheet1.write(row, 3, ' ', header_table)
                    worksheet1.write(row, 4, ' ', header_table)
                    row = row + 1

                    root_lv2 = self.env['account.financial.report'].sudo().search([('parent_id', '=', lv1.id)])
                    for lv2 in root_lv2 :
                        if lv2.type != 'accounts':
                            account_ids = self.get_account_ids_tuple(lv2)
                            worksheet1.write(row, 0, lv2.code_number, header_table_pink)
                            worksheet1.write(row, 1, lv2.name, header_table_pink)
                            worksheet1.write(row, 2, ' ', header_table_pink)
                            worksheet1.write(row, 3, ' ', header_table_pink)
                            worksheet1.write(row, 4, ' ', header_table_pink)
                            root_lv3 = self.env['account.financial.report'].sudo().search([('parent_id', '=', lv2.id)])
                            row = row + 1
                            for lv3 in root_lv3:
                                if lv3.type != 'accounts':
                                    account_ids = self.get_account_ids_tuple(lv3)
                                    worksheet1.write(row, 0, lv3.code_number, header_table_pink)
                                    worksheet1.write(row, 1, lv3.name, header_table_pink)
                                    worksheet1.write(row, 2, ' ', header_table_pink)
                                    worksheet1.write(row, 3, ' ', header_table_pink)
                                    worksheet1.write(row, 4, ' ', header_table_pink)
                                    root_lv4 = self.env['account.financial.report'].sudo().search([('parent_id', '=', lv3.id)])
                                    row = row + 1
                                    for lv4 in root_lv4:
                                        if lv4.type != 'accounts':
                                            account_ids = self.get_account_ids_tuple(lv4)
                                            worksheet1.write(row, 0, lv4.code_number, header_table_pink)
                                            worksheet1.write(row, 1, lv4.name, header_table_pink)
                                            worksheet1.write(row, 2, ' ', header_table_pink)
                                            worksheet1.write(row, 3, ' ', header_table_pink)
                                            worksheet1.write(row, 4, ' ', header_table_pink)
                                            row = row + 1
                                        else:
                                            account_ids = self.get_account_ids_tuple(lv4)
                                            this_month = self.get_current_balance(account_ids, states) * lv4.sign
                                            amount_ytd = self.get_ytd_balance(account_ids, states) * lv4.sign
                                            worksheet1.write(row, 0, lv4.code_number)
                                            worksheet1.write(row, 1, lv4.name)
                                            worksheet1.write(row, 2, ' ')
                                            worksheet1.write(row, 3, this_month, set_right)
                                            worksheet1.write(row, 4, amount_ytd, set_right)
                                            row = row + 1

                                else:
                                    account_ids = self.get_account_ids_tuple(lv3)
                                    this_month = self.get_current_balance(account_ids, states) * lv3.sign
                                    amount_ytd = self.get_ytd_balance(account_ids, states) * lv3.sign
                                    worksheet1.write(row, 0, lv3.code_number)
                                    worksheet1.write(row, 1, lv3.name)
                                    worksheet1.write(row, 2, ' ')
                                    worksheet1.write(row, 3, this_month, set_right)
                                    worksheet1.write(row, 4, amount_ytd, set_right)
                                    row = row + 1
                        else:
                            account_ids = self.get_account_ids_tuple(lv2)
                            this_month = self.get_current_balance(account_ids,states) * lv2.sign
                            amount_ytd = self.get_ytd_balance(account_ids, states) * lv2.sign
                            worksheet1.write(row, 0, lv2.code_number)
                            worksheet1.write(row, 1, lv2.name)
                            worksheet1.write(row, 2, ' ')
                            worksheet1.write(row, 3, this_month, set_right)
                            worksheet1.write(row, 4, amount_ytd, set_right)
                            row = row + 1

                    if lv1.level == 1 :
                        account_ids = self.get_account_ids_tuple(lv1)
                        this_month = self.get_current_balance(account_ids,states) * lv1.sign
                        amount_ytd = self.get_ytd_balance(account_ids, states) * lv1.sign
                        worksheet1.write(row, 0, ' ', header_table)
                        worksheet1.write(row, 1, 'Total '+lv1.name, header_table)
                        worksheet1.write(row, 2, ' ', header_table)
                        worksheet1.write(row, 3, this_month, header_table_right)
                        worksheet1.write(row, 4, amount_ytd, header_table_right)
                        row = row + 2

                else:
                    account_ids = self.get_account_ids_tuple(lv1)
                    this_month = self.get_current_balance(account_ids, states) * lv1.sign
                    amount_ytd = self.get_ytd_balance(account_ids,states) * lv1.sign
                    worksheet1.write(row, 0, lv1.code_number)
                    worksheet1.write(row, 1, lv1.name)
                    worksheet1.write(row, 2, ' ')
                    worksheet1.write(row, 3, this_month, set_right)
                    worksheet1.write(row, 4, amount_ytd, set_right)
                    row = row + 1



        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'account_report_lea', 'cf_lea_report_wizard')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cf.report.lea.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_account_ids(self, report_id):
        account_report = self.env['account.financial.report'].sudo().search([('id', '=', report_id)])
        child_reports = account_report._get_children_by_order()
        account_ids = []
        for report in child_reports:
            if report.type != 'sum':
                for account in report.account_ids:
                    account_ids.append(account.id)
        return account_ids

    @api.multi
    def get_account_ids_tuple(self, report_id):
        account_ids = []
        for r in report_id:
            account_report = self.env['account.financial.report'].sudo().search([('id', '=', r.id)])
            child_reports = account_report._get_children_by_order()
            for report in child_reports:
                if report.type != 'sum':
                    for account in report.account_ids:
                        account_ids.append(account.id)
        return account_ids

    @api.multi
    def get_current_balance(self, account_id, states):
        cursor = self.env.cr
        debit   = 0
        credit  = 0
        balance = 0

        if account_id :
            for line in self:
                cursor.execute(
                    """
                    select
                        sum(a.debit) as debit,
                        sum(a.credit) as credit,
                        sum(a.debit) - sum(a.credit) as balance
                    from
                        account_move_line as a,account_move as b
                    where
                        b.id = a.move_id and
                        b.state in %s and
                        a.account_id in %s and
                        a.date between %s and %s
                    """
            , (tuple(states), tuple(account_id), line.date_from, line.date_to))

                val = cursor.fetchone()
            if val[0] != None:
                debit = val[0]
            if val[1] != None:
                credit = val[1]
            if val[2] != None:
                balance = val[2]
        return balance


    @api.multi
    def get_ytd_balance(self, account_id, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0
        area = []
        date_from = str(self.fiscalyear_id.name) + '-01-01'
        if account_id :
            for line in self:
                cursor.execute(
                        """
                        select
                            sum(a.debit) as debit,
                            sum(a.credit) as credit,
                            sum(a.debit) - sum(a.credit) as balance
                        from
                            account_move_line as a,account_move as b
                        where
                            b.id = a.move_id and
                            b.state in %s and
                            a.account_id in %s and
                            a.date between %s and %s

                """, (tuple(states), tuple(account_id), date_from, line.date_to))
                val = cursor.fetchone()
                if val[0] != None:
                    debit = val[0]
                if val[1] != None:
                    credit = val[1]
                if val[2] != None:
                    balance = val[2]
        return balance

    @api.multi
    def get_init_balance_pl(self, account_id, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0

        per = re.split("/", self.period_id.name)
        mm = int(per[0])

        date_from = str(self.fiscalyear_id.name)+'-01-01'

        area = []
        for ar in self.area_lks_id:
            area.append(ar.id)

        if mm != 1 :
            if account_id:
                for line in self:
                    if not self.area_lks_id:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date < %s

                            """, (tuple(states), tuple(account_id), date_from, line.date_from))
                    else:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                b.area_lks in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date < %s
                            """, (tuple(states), tuple(area), tuple(account_id), date_from, line.date_from))
                    val = cursor.fetchone()
                    if val[0] != None:
                        debit = val[0]
                    if val[1] != None:
                        credit = val[1]
                    if val[2] != None:
                        balance = val[2]
        return balance


    @api.multi
    def get_init_balance_pl_last(self, account_id, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0

        per = re.split("/", self.period_id.name)
        mm = int(per[0])

        date_from = str(int(self.fiscalyear_id.name)-1) + '-01-01'
        date_to   = str(int(self.fiscalyear_id.name)-1) + '-12-31'

        area = []
        for ar in self.area_lks_id:
            area.append(ar.id)

        if mm != 1:
            if account_id:
                for line in self:
                    if not self.area_lks_id:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date <= %s

                            """, (tuple(states), tuple(account_id), date_from, date_to))
                    else:
                        cursor.execute(
                            """
                            select
                                sum(a.debit) as debit,
                                sum(a.credit) as credit,
                                sum(a.debit) - sum(a.credit) as balance
                            from
                                account_move_line as a,account_move as b
                            where
                                b.id = a.move_id and
                                b.state in %s and
                                b.area_lks in %s and
                                a.account_id in %s and
                                a.date >= %s and
                                a.date <= %s
                            """, (tuple(states), tuple(area), tuple(account_id), date_from, date_to))
                    val = cursor.fetchone()
                    if val[0] != None:
                        debit = val[0]
                    if val[1] != None:
                        credit = val[1]
                    if val[2] != None:
                        balance = val[2]
        return balance

class ReportTransaksiAPLea(models.TransientModel):
    _name = 'report.transaksi.ap.lea'


    company_id         = fields.Many2one('res.company', 'Company')
    date_from          = fields.Date('Date From')
    date_to            = fields.Date('Date To')
    target             = fields.Selection([('all','All'),('draft', 'Draft'), ('open', 'Open'),('paid', 'Paid')], string='Status')
    vendor_ids          = fields.Many2many('res.partner')
    data               = fields.Binary('File', readonly=True)
    name               = fields.Char('Filename', readonly=True)
    state_position     = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    @api.multi
    def generate_report(self):

        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'laporan_transaksi_ap.xlsx'
        workbook.add_format({'bold': 1, 'align': 'center'})
        # worksheet = workbook.add_worksheet('Report')
        worksheet1 = workbook.add_worksheet("Report Excel")
        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        center_title.set_font_size('10')
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
        header_table_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        header_table_right.set_text_wrap()
        header_table_right.set_font_size('10')
        header_table_right.set_bg_color('#eff0f2')
        header_table_right.set_border()
        #################################################################################
        header_table_pink = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        header_table_pink.set_text_wrap()
        header_table_pink.set_font_size('10')
        header_table_pink.set_bg_color('#ffcccc')
        header_table_pink.set_border()
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        set_right.set_text_wrap()
        set_right.set_font_size('8')
        # set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_font_size('8')
        # set_border.set_border()
        #################################################################################
        set_border_bold = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'bold': 1})
        set_border_bold.set_text_wrap()
        set_border_bold.set_font_size('8')
        # set_border_bold.set_border()
        ################################################################################
        set_border_bold_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('8')
        # set_border_bold_right.set_border()

        ###TITLE REPORT ##############################################
        worksheet1.set_column('A:A', 40)
        worksheet1.set_column('B:B', 40)
        worksheet1.set_column('C:H', 40)
        worksheet1.set_column('I:Z', 20)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.set_row(0, 30)
        worksheet1.write(0, 0, self.company_id.name, center_title)
        worksheet1.write(1, 0, 'Laporan Transaksi AP', center_title)
        worksheet1.write(2, 0, date_from+' s/d '+date_to, center_title)
        states = [self.target]
        if self.target == 'all':
            states = ['draft', 'open','paid']

        vendor = []

        invoice_ids = self.env['account.invoice'].search([('type', '=', 'in_invoice'),('date_invoice', '>=', self.date_from),('date_invoice', '<=', self.date_to),('state', 'in', states)])
        if self.vendor_ids :
            for v in self.vendor_ids:
                vendor.append(v.id)
            invoice_ids = self.env['account.invoice'].search([('partner_id', 'in', vendor),('type', '=', 'in_invoice'), ('date_invoice', '>=', self.date_from),('date_invoice', '<=', self.date_to), ('state', 'in', states)])

        worksheet1.write(3, 0, "Nama Supplier", header_table)
        worksheet1.write(3, 1, 'Tgl Bukti Hutang', header_table)
        worksheet1.write(3, 2, 'No. Bukti Hutang', header_table)
        worksheet1.write(3, 3, 'No.PO', header_table)
        worksheet1.write(3, 4, 'Tgl Jatuh Tempo', header_table)
        worksheet1.write(3, 5, 'Faktur Pajak', header_table)
        worksheet1.write(3, 6, 'No. MR', header_table)
        worksheet1.write(3, 7, 'Tgl. Barang Masuk', header_table)
        worksheet1.write(3, 8, 'Nilai Bruto', header_table)
        worksheet1.write(3, 9, 'PPN/PPH', header_table)
        worksheet1.write(3, 10,'Nilai OS', header_table)
        worksheet1.write(3, 11,'Nilai Paid', header_table)
        worksheet1.write(3, 12,'Sisa OS', header_table)
        worksheet1.write(3, 13,'Status AP', header_table)

        row = 4
        total_untaxed = 0
        total_tax = 0
        total_all = 0
        total_paid = 0
        total_residual = 0
        for inv in invoice_ids.sorted(key=lambda l: l.date_invoice) :
            date_inv_raw = datetime.strptime(inv.date_invoice, '%Y-%m-%d')
            date_inv = datetime.strftime(date_inv_raw, '%d-%m-%Y')

            date_due_raw = datetime.strptime(inv.date_due, '%Y-%m-%d')
            date_due = datetime.strftime(date_due_raw, '%d-%m-%Y')

            mr = ''
            date_incoming = ''
            for pick in inv.picking_lines:
                mr += str(pick.name)+' '
                date_in_raw = datetime.strptime(pick.date_done, '%Y-%m-%d %H:%M:%S')
                date_in_raw += timedelta(hours=7)
                date_in = datetime.strftime(date_in_raw, '%d-%m-%Y')
                date_incoming +=str(date_in)+' ; '
            paid = 0
            for pay in inv.payment_move_line_ids:
                paid += pay.debit

            worksheet1.write(row, 0, inv.partner_id.name, set_border_bold)
            worksheet1.write(row, 1, date_inv, set_border_bold)
            worksheet1.write(row, 2, inv.name, set_border_bold)
            worksheet1.write(row, 3, inv.origin, set_border_bold)
            worksheet1.write(row, 4, date_due, set_border_bold)
            worksheet1.write(row, 5, inv.no_faktur_vendor, set_border_bold)
            worksheet1.write(row, 6, mr, set_border_bold)
            worksheet1.write(row, 7, date_incoming, set_border_bold)
            worksheet1.write(row, 8, inv.amount_untaxed, set_border_bold_right)
            worksheet1.write(row, 9, inv.amount_tax, set_border_bold_right)
            worksheet1.write(row, 10, inv.amount_total, set_border_bold_right)
            worksheet1.write(row, 11, paid, set_border_bold_right)
            worksheet1.write(row, 12, inv.residual, set_border_bold_right)
            worksheet1.write(row, 13, inv.state, set_border_bold)
            row = row + 1
            total_untaxed += inv.amount_untaxed
            total_tax += inv.amount_tax
            total_all += inv.amount_total
            total_paid += paid
            total_residual += inv.residual

        worksheet1.write(row, 0, "", header_table)
        worksheet1.write(row, 1, '', header_table)
        worksheet1.write(row, 2, '', header_table)
        worksheet1.write(row, 3, '', header_table)
        worksheet1.write(row, 4, '', header_table)
        worksheet1.write(row, 5, '', header_table)
        worksheet1.write(row, 6, '', header_table)
        worksheet1.write(row, 7, '', header_table)
        worksheet1.write(row, 8, total_untaxed, header_table_right)
        worksheet1.write(row, 9, total_tax, header_table_right)
        worksheet1.write(row, 10, total_all, header_table_right)
        worksheet1.write(row, 11, total_paid, header_table_right)
        worksheet1.write(row, 12, total_residual, header_table_right)
        worksheet1.write(row, 13, '', header_table_right)



        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'account_report_lea', 'report_transaksi_ap_lea_wizard')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.transaksi.ap.lea',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

class ReportOSLea(models.TransientModel):
    _name = 'report.transaksi.os.lea'

    company_id         = fields.Many2one('res.company', 'Company')
    date_from          = fields.Date('Date From')
    date_to            = fields.Date('Date To')
    vendor_ids          = fields.Many2many('res.partner')
    data               = fields.Binary('File', readonly=True)
    name               = fields.Char('Filename', readonly=True)
    state_position     = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    @api.multi
    def generate_report(self):

        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'laporan_transaksi_os.xlsx'
        workbook.add_format({'bold': 1, 'align': 'center'})
        # worksheet = workbook.add_worksheet('Report')
        worksheet1 = workbook.add_worksheet("Report Excel")
        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'left'})
        center_title.set_font_size('10')
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
        header_table_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        header_table_right.set_text_wrap()
        header_table_right.set_font_size('10')
        header_table_right.set_bg_color('#eff0f2')
        header_table_right.set_border()
        #################################################################################
        header_table_pink = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'center'})
        header_table_pink.set_text_wrap()
        header_table_pink.set_font_size('10')
        header_table_pink.set_bg_color('#ffcccc')
        header_table_pink.set_border()
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'num_format': '#,##0.00'})
        set_right.set_text_wrap()
        set_right.set_font_size('8')
        # set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign': 'vcenter', 'align': 'left'})
        set_border.set_text_wrap()
        set_border.set_font_size('8')
        # set_border.set_border()
        #################################################################################
        set_border_bold = workbook.add_format({'valign': 'vcenter', 'align': 'left', 'bold': 1})
        set_border_bold.set_text_wrap()
        set_border_bold.set_font_size('8')
        # set_border_bold.set_border()
        ################################################################################
        set_border_bold_right = workbook.add_format(
            {'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('8')
        # set_border_bold_right.set_border()

        ###TITLE REPORT ##############################################
        worksheet1.set_column('A:A', 40)
        worksheet1.set_column('B:B', 20)
        worksheet1.set_column('C:H', 20)
        worksheet1.set_column('I:Z', 20)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.set_row(0, 30)
        worksheet1.write(0, 0, self.company_id.name, center_title)
        worksheet1.write(1, 0, 'Laporan Transaksi OS', center_title)
        worksheet1.write(2, 0, date_from + ' s/d ' + date_to, center_title)
        states = ['open', 'paid']
        vendor = []


        if self.vendor_ids:
            for v in self.vendor_ids:
                vendor.append(v.id)
        else :
            cursor = self.env.cr
            cursor.execute("""
                            select
                                partner_id
                            from
                                account_invoice
                            where
                                state in %s and
                                company_id = %s and
                                type = 'in_invoice'
                            group by partner_id
                            """, (tuple(states), self.company_id.id))
            group_partner = cursor.fetchall()
            for g in group_partner :
                vendor.append(g[0])


        worksheet1.write(3, 0, "Nama Supplier", header_table)
        worksheet1.write(3, 1, 'S. Awal', header_table)
        worksheet1.write(3, 2, 'Pembelian/Validate/Open', header_table)
        worksheet1.write(3, 3, 'Pembayaran', header_table)
        worksheet1.write(3, 4, 'S. Akhir', header_table)

        row = 4
        for p in vendor :
            partner = self.env['res.partner'].browse(p)
            saldo_awal = self.get_saldo_awal(partner.id,states)
            pembelian  = self.get_pembelian(partner.id,states)
            paid       = self.get_pembayaran(partner.id,states)
            saldo_akhir = saldo_awal + pembelian - paid

            worksheet1.write(row, 0, partner.name, set_border_bold)
            worksheet1.write(row, 1, saldo_awal, set_border_bold_right)
            worksheet1.write(row, 2, pembelian, set_border_bold_right)
            worksheet1.write(row, 3, paid, set_border_bold_right)
            worksheet1.write(row, 4, saldo_akhir, set_border_bold_right)

            row = row + 1



        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'account_report_lea', 'report_transaksi_os_lea_wizard')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.transaksi.os.lea',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_saldo_awal(self,partner_id, states):
        invoice_ids = self.env['account.invoice'].search([('type', '=', 'in_invoice'), ('date_invoice', '<', self.date_from), ('partner_id', '=', partner_id),('state', 'in', states)])
        total_due = 0
        total_paid = 0
        for inv in invoice_ids :
            total_due = total_due + inv.amount_total
            for payment in inv.payment_move_line_ids:
                if payment.date < self.date_from :
                    total_paid = total_paid + payment.debit
        residual = total_due - total_paid
        return residual

    @api.multi
    def get_pembelian(self, partner_id, states):
        invoice_ids = self.env['account.invoice'].search([('type', '=', 'in_invoice'), ('date_invoice', '>=', self.date_from), ('date_invoice', '<=', self.date_to), ('partner_id', '=', partner_id),('state', 'in', states)])
        total_due = 0
        for inv in invoice_ids:
            total_due = total_due + inv.amount_total

        return total_due

    @api.multi
    def get_pembayaran(self, partner_id, states):
        invoice_ids = self.env['account.invoice'].search([('type', '=', 'in_invoice'), ('date_invoice', '<=', self.date_to), ('partner_id', '=', partner_id), ('state', 'in', states)])
        total_paid = 0
        for inv in invoice_ids:
            for payment in inv.payment_move_line_ids:
                if payment.date >= self.date_from and payment.date <= self.date_to :
                    total_paid = total_paid + payment.debit
        return total_paid

class GeneralLedgerLeaWizardCF(models.TransientModel):
    _name = 'general.ledger.lea.cf.wizard'


    company         = fields.Many2one('res.company', 'Company')
    account         = fields.Many2many('account.account')
    partner         = fields.Many2one('res.partner')
    area_lks_id     = fields.Many2many('account.area.location')
    period_id       = fields.Many2one('account.period')
    date_from       = fields.Date('Date From')
    date_to         = fields.Date('Date To')
    data            = fields.Binary('File', readonly=True)
    name            = fields.Char('Filename', readonly=True)
    target          = fields.Selection([('all', 'All'), ('posted', 'Posted')], default='posted')
    state_position  = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

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
    def generate_general_ledger_excel(self):

        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'Mutasi_CF' + '_' + self.company.name +'.xlsx'
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
        header_table_right = workbook.add_format({'bold': 1, 'valign': 'vcenter', 'align': 'right','num_format': '#,##0.00'})
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
        set_border_bold_right = workbook.add_format({'valign': 'vcenter', 'align': 'right', 'bold': 1, 'num_format': '#,##0.00'})
        set_border_bold_right.set_text_wrap()
        set_border_bold_right.set_font_size('9')
        set_border_bold_right.set_border()

        worksheet1.set_column('A:A', 10)
        worksheet1.set_column('B:B', 10)
        worksheet1.set_column('C:C', 15)
        worksheet1.set_column('D:D', 15)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_column('F:F', 45)
        worksheet1.set_column('G:G', 25)
        worksheet1.set_column('H:H', 25)
        worksheet1.set_column('I:I', 25)

        date_from_raw = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_from = datetime.strftime(date_from_raw, '%d-%B-%Y')

        date_to_raw = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.set_row(0, 30)
        worksheet1.merge_range('A1:G1', self.company.name, center_title)
        worksheet1.merge_range('A2:G2', 'Mutasi Transaksi CF', center_title)
        worksheet1.merge_range('A3:G3', date_from+' s/d '+date_to, center_title)

        account = self.env['account.account'].search([('company_id','=',self.company.id)])
        if self.account :
            account = self.account

        states = ['posted']
        if self.target == 'all':
            states = ['draft', 'posted']

        area =[]
        for ar in self.area_lks_id :
            area.append(ar.id)

        row = 4

        for acc in account :
            # Search Move Line Transaction
            total_debit_check = 0
            total_credit_check = 0
            saldo_awal = self.get_balance(acc, self.date_from, self.company, area, states)
            aml = self.env['account.move.line'].search([('account_id', '=', acc.id), ('date', '>=', self.date_from), ('date', '<=', self.date_to),('move_id.state', 'in', states), ('company_id', '=', self.company.id)])
            if self.area_lks_id:
                aml = self.env['account.move.line'].search([('account_id', '=', acc.id), ('date', '>=', self.date_from), ('date', '<=', self.date_to),('move_id.state', 'in', states),('move_id.area_lks', 'in', area), ('company_id', '=', self.company.id)])

            for line in aml:
                total_debit_check = total_debit_check + line.debit
                total_credit_check = total_credit_check + line.credit

            total_check = saldo_awal[2] + total_debit_check + total_credit_check
            if total_check != 0 :
                worksheet1.write(row, 0, 'No.Rek /Code CF')
                worksheet1.write(row, 1, acc.code+' - '+acc.name+' / '+acc.code_cf)
                row = row + 1
                worksheet1.write(row, 0, 'Tanggal', header_table)
                worksheet1.write(row, 1, 'Area', header_table)
                worksheet1.write(row, 2, 'No. Internal', header_table)
                worksheet1.write(row, 3, 'No. Bukti', header_table)
                worksheet1.write(row, 4, 'Rek. Lawan', header_table)
                worksheet1.write(row, 5, 'Uraian', header_table)
                worksheet1.write(row, 6, 'Debit', header_table)
                worksheet1.write(row, 7, 'Kredit', header_table)
                worksheet1.write(row, 8, 'Saldo', header_table)
                #Computing Initial Balance

                row = row + 1
                worksheet1.write(row, 0, '', set_border)
                worksheet1.write(row, 1, '', set_border)
                worksheet1.write(row, 2, '', set_border)
                worksheet1.write(row, 3, '', set_border)
                worksheet1.write(row, 4, '', set_border)
                worksheet1.write(row, 5, 'SALDO AWAL', set_border)
                worksheet1.write(row, 6, 0, set_right)
                worksheet1.write(row, 7, 0, set_right)
                worksheet1.write(row, 8, saldo_awal[2], set_right)
                #Search Move Line Transaction
                row = row + 1
                saldo = saldo_awal[2]
                total_debit = 0
                total_credit = 0
                if aml :
                    for line in aml.sorted(key=lambda l: l.date) :
                        counter = ''
                        counterpart = self.env['account.move.line'].search([('account_id', '!=', acc.id),('move_id', '=', line.move_id.id)])
                        for c in counterpart :
                            counter += c.account_id.code_cf+'  '
                        date_move_raw = datetime.strptime(line.date, '%Y-%m-%d')
                        date_move = datetime.strftime(date_move_raw, '%d-%m-%Y')
                        total_debit = total_debit + line.debit
                        total_credit = total_credit + line.credit
                        saldo = saldo + line.debit - line.credit
                        worksheet1.write(row, 0, date_move, set_border)
                        worksheet1.write(row, 1, line.move_id.area_lks.name, set_border)
                        worksheet1.write(row, 2, line.move_id.name, set_border)
                        worksheet1.write(row, 3, line.move_id.no_bukti, set_border)
                        worksheet1.write(row, 4, counter, set_border)
                        worksheet1.write(row, 5, line.name, set_border)
                        worksheet1.write(row, 6, line.debit, set_right)
                        worksheet1.write(row, 7, line.credit, set_right)
                        worksheet1.write(row, 8, saldo, set_right)
                        row = row + 1
                #Summary
                row = row + 1
                total = saldo_awal[2]+ total_debit - total_credit
                worksheet1.merge_range('A'+str(row)+':F'+str(row), "Total", header_table)
                row= row - 1
                worksheet1.write(row, 6, total_debit, header_table_right)
                worksheet1.write(row, 7, total_credit, header_table_right)
                worksheet1.write(row, 8, total, header_table_right)
                row = row + 2




        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'account_report_lea', 'general_ledger_lea_cf_wizard_view_forms')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'general.ledger.lea.cf.wizard',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    @api.multi
    def get_balance(self, account, date, company, area, states):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0
        for line in self:
            if account :
                if not area :
                    cursor.execute("""
                                    select
                                        sum(a.debit) as debit,
                                        sum(a.credit) as credit,
                                        sum(a.debit - a.credit) as balance
                                    from
                                        account_move_line as a, account_move as b
                                    where
                                        a.move_id = b.id and
                                        a.account_id = %s and
                                        a.date < %s and
                                        b.state in %s and
                                        b.company_id = %s
                                        """, (account.id, date, tuple(states), company.id))
                else :
                    cursor.execute("""
                                    select
                                        sum(a.debit) as debit,
                                        sum(a.credit) as credit,
                                        sum(a.debit - a.credit) as balance
                                    from
                                        account_move_line as a, account_move as b
                                    where
                                        a.move_id = b.id and
                                        a.account_id = %s and
                                        a.date < %s and
                                        b.state in %s and
                                        b.company_id = %s and
                                        b.area_lks in %s
                                    """, (account.id, date, tuple(states), company.id, tuple(area)))
                val = cursor.fetchone()
                if val[0] != None:
                    debit = val[0]
                if val[1] != None:
                    credit = val[1]
                if val[2] != None:
                    balance = val[2]
        return [debit,credit,balance]


















