from odoo import api, models, fields
from lxml import etree
from cStringIO import StringIO
import xlsxwriter
from collections import OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta

BULAN_SELECTION = [
    ('1','Januari'),
    ('2','Februari'),
    ('3','Maret'),
    ('4','April'),
    ('5','Mei'),
    ('6','Juni'),
    ('7','Juli'),
    ('8','Agustus'),
    ('9','September'),
    ('10','Oktober'),
    ('11','November'),
    ('12','Desember'),
]

class AccountingReport(models.TransientModel):
    _name               = "as.accounting.report"
    _description        = "Accounting Report Horizontal"

    @api.model
    def _get_years(self):
        years = []
        show_year = 0
        next_year = datetime.today().year + 1
        while show_year < 4:
            years.append(next_year)
            next_year -= 1
            show_year += 1
        return [(str(year), year) for year in years]

    @api.model
    def _get_this_year(self):
        return str(datetime.today().year)

    @api.model
    def _get_this_month(self):
        current = datetime.today().month
        return str(current)

    @api.model
    def _get_account_report(self):
        reports = []
        if self._context.get('active_id'):
            menu = self.env['ir.ui.menu'].browse(self._context.get('active_id')).name
            reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    #financial_report
    account_report_id   = fields.Many2one('account.financial.report', string='Account Reports', required=True, default=_get_account_report)

    #common
    company_id          = fields.Many2one('res.company', string='Company',  default=lambda self: self.env.user.company_id)
    journal_ids         = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([]))
    date_from           = fields.Date(string='Start Date')
    date_to             = fields.Date(string='End Date')
    target_move         = fields.Selection([('posted', 'All Posted Entries'),
                                            ('draft','All Unposted Entries'),
                                            ('all', 'All Entries'),], string='Target Moves', required=True, default='posted')
    month               = fields.Selection(BULAN_SELECTION,string='Month', default=_get_this_month)
    year                = fields.Selection('_get_years', string='Year', default=_get_this_year,copy=True)

    #files
    name                = fields.Char(string = "File Name")
    state_x             = fields.Selection([('choose', 'choose'), ('get', 'get')], default = 'choose')
    data_x              = fields.Binary('File', readonly = True)
    wbf = {}

    @api.onchange('company_id')
    def onchange_company(self):
        if self.company_id and self.account_report_id.company_id.id != self.company_id.id:
            self.account_report_id = False

    @api.onchange('month', 'date_from', 'date_to', 'year','account_report_id')
    def change_month(self):
        today = datetime.now()
        year = str(datetime.today().year)
        if self.month and self.year:
            current = datetime.today().month
            index = int(self.month)
            end_index = index - current + 1
            select_year = int(self.year)
            this_year = int(year)
            diff = select_year - this_year

            if  self.account_report_id.report_group == 'Balance Sheet' :
                tanggal = datetime.strptime(self.year, '%Y')
            else :
                start_index =  index - current
                tanggal = today + relativedelta(day=1, months=start_index, years=diff)

            self.date_from = tanggal
            self.date_to = today + relativedelta(day=1, months=end_index, days=-1, years=diff)

    @api.multi
    def get_date(self,month_value,year_value):
        today = datetime.now()
        year = str(datetime.today().year)
        current = datetime.today().month
        index = month_value
        end_index = index - current + 1

        select_year = year_value
        this_year = int(year)

        diff = select_year - this_year
        date_from = datetime.strptime(str(year_value), '%Y')
        date_to = today + relativedelta(day=1, months=end_index, days=-1, years=diff)
        return date_from, date_to

    def _build_contexts(self, data):
        result = {}
        result['journal_ids']   = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state']         = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from']     = data['form']['date_from'] or False
        result['date_to']       = data['form']['date_to'] or False
        result['strict_range']  = True if result['date_from'] else False
        #result['company_id'] = 'company_id' in data['form'] and data['form']['company_id'] or False
        return result

    #context last month
    def _build_cmp_1_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        #result['company_id'] = 'company_id' in data['form'] and data['form']['company_id'] or False

        if self.month == '1' :
            month = 12
            year = int(self.year) - 1
        else :
            month = int(self.month) - 1
            year = int(self.year)

        date_from, date_to = self.get_date(month,year)
        result['date_from'] = date_from
        result['date_to'] = date_to
        result['strict_range'] = True
        return result

    #laba rugi : sampai dengan bulan ini
    def _build_cmp_3_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        #result['company_id'] = 'company_id' in data['form'] and data['form']['company_id'] or False

        month = int(self.month)
        year = int(self.year)
        date_from, date_to = self.get_date(month,year)

        result['date_from'] = date_from
        result['date_to'] = date_to
        result['strict_range'] = True
        return result

    #december last year
    def _build_cmp_2_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        #result['company_id'] = 'company_id' in data['form'] and data['form']['company_id'] or False
        month = 12
        year = int(self.year) - 1
        date_from, date_to = self.get_date(month,year)
        result['date_from'] = date_from
        result['date_to'] = date_to
        result['strict_range'] = True
        return result

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids']     = self.env.context.get('active_ids', [])
        data['model']   = self.env.context.get('active_model', 'ir.ui.menu')
        data['form']    = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        # data['form']['company_id'] = self.company_id.id
        used_context    = self._build_contexts(data)
        cmp_1_context = self._build_cmp_1_context(data)
        if self.account_report_id.report_group == 'Balance Sheet' :
            cmp_2_context = self._build_cmp_2_context(data)
        else :
            cmp_2_context = self._build_cmp_3_context(data)

        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        data['form']['cmp_1_context'] = cmp_1_context
        data['form']['cmp_2_context'] = cmp_2_context
        return self.print_excel_report(data)

    def _compute_account_balance(self, accounts):
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }
        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                       " FROM " + tables + \
                       " WHERE account_id IN %s " \
                            + filters + \
                       " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(report.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        las_month_res = self.with_context(data.get('cmp_1_context'))._compute_report_balance(child_reports)
        december_res = self.with_context(data.get('cmp_2_context'))._compute_report_balance(child_reports)
        for report_id, value in las_month_res.items():
            res[report_id]['cmp_1_bal'] = value['balance']
            report_acc = res[report_id].get('account')
            if report_acc:
                for account_id, val in las_month_res[report_id].get('account').items():
                    report_acc[account_id]['cmp_1_bal'] = val['balance']

        for report_id, value in december_res.items():
            res[report_id]['cmp_2_bal'] = value['balance']
            report_acc = res[report_id].get('account')
            if report_acc:
                for account_id, val in december_res[report_id].get('account').items():
                    report_acc[account_id]['cmp_2_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * report.sign,
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False,
                'parent_id':report.parent_id.id,
                'parent':report.parent_id,
                'id':report.id,
                'side':report.side,
                'code_number':report.code_number
            }
            vals['balance_cmp_1'] = res[report.id]['cmp_1_bal'] * report.sign
            vals['balance_cmp_2'] = res[report.id]['cmp_2_bal'] * report.sign

            lines.append(vals)
            if report.display_detail == 'no_detail':
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': account.name,
                        'balance': value['balance'] * report.sign or 0.0,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                        'is_account':True
                     }
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    vals['balance_cmp_1'] = value['cmp_1_bal'] * report.sign
                    vals['balance_cmp_2'] = value['cmp_2_bal'] * report.sign

                    if not account.company_id.currency_id.is_zero(vals['balance_cmp_1']):
                        flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance_cmp_2']):
                        flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines

    @api.multi
    def print_excel_report(self,data):
        is_balance_sheet = True if self.account_report_id.report_group == 'Balance Sheet' else False
        is_profit_loss = True if self.account_report_id.report_group == 'Profit and Loss' else False
        #balance_sheet
        balance_sheet_search = self.env['account.financial.report'].search([('report_group','=','Balance Sheet'),('parent_id','=',False)])
        balance_sheet_ids = [x.id for x in balance_sheet_search]
        #profitloss
        profit_and_loss_search = self.env['account.financial.report'].search([('report_group','=','Profit and Loss'),('parent_id','=',False)])
        profit_and_loss_ids = [x.id for x in profit_and_loss_search]
        #aktiva
        asset_search = self.env['account.financial.report'].search([('report_group','=','Balance Sheet'),('balance_sheet_type','=','Aktiva')])
        asset_ids = [x.id for x in asset_search]
        #pasiva
        liability_search = self.env['account.financial.report'].search([('report_group','=','Balance Sheet'),('balance_sheet_type','=','Pasiva')])
        liability_ids = [x.id for x in liability_search]

        bulan = dict(BULAN_SELECTION)[self.month]
        if self.month == '1' :
            month = 12
            prev_month_year = int(self.year) - 1
        else :
            month = int(self.month) - 1
            prev_month_year = int(self.year)
        prev_month = dict(BULAN_SELECTION)[str(month)]
        year = int(self.year)
        prev_year = year - 1

        data['form'].update(self.read(['account_report_id','target_move'])[0])
        ress = self.get_account_lines(data['form'])

        ### Set Template ######################
        template = self.env['xlsx.report.template']
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp, {'default_date_format': 'dd/mm/yy'})
        workbook, wbf = template.workbook_format(workbook, self.wbf)
        workbook.formats[0].font_name = 'Arial'
        workbook.formats[0].font_size = 10
        header_title_1 = OrderedDict()
        header_title_2 = OrderedDict()
        row = 6
        header_row = row

        filename = self.account_report_id.name+' - '+self.company_id.name+' - '+bulan+' '+self.year+'.xlsx'
        worksheet = workbook.add_worksheet('Report')

        if is_balance_sheet :
            header_title_1['No'] = [9, wbf['content_center']]
            header_title_1['Aktiva'] = [35, wbf['content']]
            header_title_1['Per %s %s' % (bulan, str(year))] = [18, wbf['content_float']]
            header_title_1['Per %s %s' % (prev_month, str(prev_month_year))] = [18, wbf['content_float']]
            header_title_1['Per Akhir Desember %s' % (str(prev_year))] = [18, wbf['content_float']]

            col = 0
            worksheet.set_column(col, col, len(header_title_1))
            for key, value in header_title_1.items():
                worksheet.set_column(col, col, value[0], value[1])
                worksheet.write_string(row, col, key, wbf['header_no'])
                col += 1

            template._get_report_title(worksheet, self.company_id.name.upper(), 10, wbf, 2)
            template._get_report_title(worksheet, self.account_report_id.name.upper(), 10, wbf, 3)
            template._get_report_title(worksheet, 'Per %s %s' % (bulan, str(year)), 10, wbf, 4)

            header_title_2['No'] = [9, wbf['content_number_center']]
            header_title_2['Pasiva'] = [45, wbf['content']]
            header_title_2['Per %s %s' % (bulan, str(year))] = [18, wbf['content_float']]
            header_title_2['Per %s %s' % (prev_month, str(prev_month_year))] = [18, wbf['content_float']]
            header_title_2['Per Akhir Desember %s' % (str(prev_year))] = [18, wbf['content_float']]

            col = 5
            worksheet.set_column(col, col, len(header_title_2))
            for key, value in header_title_2.items():
                worksheet.set_column(col, col, value[0], value[1])
                worksheet.write_string(row, col, key, wbf['header_no'])
                col += 1
        else :
            header_title_1['No'] = [9, wbf['content_number_center']]
            header_title_1['Nama Perkiraan'] = [60, wbf['content']]
            header_title_1['Bulan Ini'] = [18, wbf['content_float']]
            header_title_1['s/d Bulan Lalu'] = [18, wbf['content_float']]
            header_title_1['s/d Bulan Ini'] = [18, wbf['content_float']]

            col = 0
            worksheet.set_column(col, col, len(header_title_1))
            for key, value in header_title_1.items():
                worksheet.set_column(col, col, value[0], value[1])
                worksheet.write_string(row, col, key, wbf['header_no'])
                col += 1

            template._get_report_title(worksheet, self.company_id.name.upper(), 5, wbf, 2)
            template._get_report_title(worksheet, self.account_report_id.name.upper(), 5, wbf, 3)
            template._get_report_title(worksheet, 'Per %s %s' % (bulan, str(year)), 5, wbf, 4)
        row = 7
        worksheet.set_row(6, 30)

        total = 0.0
        total_cmp_1 = 0.0
        total_cmp_2 = 0.0
        last_row = 0
        last_row_liability = 0

        total_balance_asset = 0.0
        total_balance_cmp_1_asset = 0.0
        total_balance_cmp_2_asset = 0.0
        total_balance_liability = 0.0
        total_balance_cmp_1_liability = 0.0
        total_balance_cmp_2_liability = 0.0

        no = 1
        change = False
        reset_row = False
        side = 'left'
        count_view_left = 0
        count_view_right = 0
        parent_id = False
        total_data = {}
        for res in ress:
            if res.get('id') in balance_sheet_ids or res.get('id') in profit_and_loss_ids:
                continue

            parent_id = res.get('parent') if res.get('parent') else parent_id
            
            if is_balance_sheet:
                if res.get('account_type') == 'sum':
                    prev_total_data = total_data
                    total_data = {'id': res['id'],
                                  'name': res['name'],
                                  'balance': res['balance'],
                                  'balance_cmp_1': res['balance_cmp_1'],
                                  'balance_cmp_2': res['balance_cmp_2']}
                    if res.get('id') in asset_ids:
                        total_balance_asset = res['balance']
                        total_balance_cmp_1_asset = res['balance_cmp_1']
                        total_balance_cmp_2_asset = res['balance_cmp_2']
                    elif res.get('id') in liability_ids:
                        total_balance_liability = res['balance']
                        total_balance_cmp_1_liability = res['balance_cmp_1']
                        total_balance_cmp_2_liability = res['balance_cmp_2']

                    if res.get('side') :
                        side = res.get('side')
                    if res.get('parent_id',False) in balance_sheet_ids :
                        if reset_row == False :
                            row = 7
                            reset_row = True
            elif is_profit_loss :
                if res.get('account_type') == 'sum':
                    total += res['balance'] if res.get('balance') else 0
                    total_cmp_1 += res['balance_cmp_1'] if res.get('balance_cmp_1') else 0
                    total_cmp_2 += res['balance_cmp_2'] if res.get('balance_cmp_2') else 0

            if row - 7 >= 40 and not is_profit_loss:
                row = 7
                
            if side == 'left' or is_profit_loss:                
                if is_balance_sheet:                    
                    if res.get('account_type') == 'sum' and count_view_left > 1:                        
                        worksheet.write(row, 0, 'TOTAL', wbf['total_mid_center'])
                        worksheet.write(row, 1, prev_total_data['name'] if prev_total_data.get('name') else '', wbf['total_mid'])
                        worksheet.write(row, 2, prev_total_data['balance'] if prev_total_data.get('balance') else 0.0, wbf['total_mid_float'])
                        worksheet.write(row, 3, prev_total_data['balance_cmp_1'] if prev_total_data.get('balance_cmp_1') else 0.0, wbf['total_mid_float'])
                        worksheet.write(row, 4, prev_total_data['balance_cmp_2'] if prev_total_data.get('balance_cmp_2') else 0.0, wbf['total_mid_float'])

                        worksheet.write(row+2, 0, 'TOTAL', wbf['total_mid_center'])
                        worksheet.write(row+2, 1, total_data['name'] if total_data.get('name') else '', wbf['total_mid'])
                        worksheet.write(row+2, 2, total_data['balance'] if total_data.get('balance') else 0.0, wbf['total_mid_float'])
                        worksheet.write(row+2, 3, total_data['balance_cmp_1'] if total_data.get('balance_cmp_1') else 0.0, wbf['total_mid_float'])
                        worksheet.write(row+2, 4, total_data['balance_cmp_2'] if total_data.get('balance_cmp_2') else 0.0, wbf['total_mid_float'])

                        row +=1

                if (is_profit_loss and res.get('account_type') == 'account_type') or res.get('account_type') == 'sum':                        
                    worksheet.write(row, 0, res['code_number'] if res.get('code_number') else ' ', wbf['content_number_center_bold'])
                    worksheet.write(row, 1, res['name'] if res.get('name') else '', wbf['content_bold'])
                    if is_profit_loss :
                        worksheet.write(row, 2, res['balance'] if res.get('balance') else 0, wbf['content_float_bold'])
                        worksheet.write(row, 3, res['balance_cmp_1'] if res.get('balance_cmp_1') else 0, wbf['content_float_bold'])
                        worksheet.write(row, 4, res['balance_cmp_2'] if res.get('balance_cmp_2') else 0, wbf['content_float_bold'])
                    else :
                        worksheet.write(row, 2, '', wbf['content_float_bold'])
                        worksheet.write(row, 3, '', wbf['content_float_bold'])
                        worksheet.write(row, 4, '', wbf['content_float_bold'])
                else :                    
                    worksheet.write(row, 0, res['code_number'] if res.get('code_number') else ' ')
                    worksheet.write(row, 1, res['name'] if res.get('name') else '')
                    worksheet.write(row, 2, res['balance'] if res.get('balance') else 0)
                    worksheet.write(row, 3, res['balance_cmp_1'] if res.get('balance_cmp_1') else 0)
                    worksheet.write(row, 4, res['balance_cmp_2'] if res.get('balance_cmp_2') else 0)

                if is_balance_sheet :                    
                    if res.get('account_type') != 'sum' and count_view_left > 0:                        
                        count_view_left += 1
                        worksheet.write(row+1, 0, 'TOTAL', wbf['total_mid_center'])
                        worksheet.write(row+1, 1, total_data['name'] if total_data.get('name') else '', wbf['total_mid'])
                        worksheet.write(row+1, 2, total_data['balance'] if total_data.get('balance') else 0.0, wbf['total_mid_float'])
                        worksheet.write(row+1, 3, total_data['balance_cmp_1'] if total_data.get('balance_cmp_1') else 0.0, wbf['total_mid_float'])
                        worksheet.write(row+1, 4, total_data['balance_cmp_2'] if total_data.get('balance_cmp_2') else 0.0, wbf['total_mid_float'])
                    elif res.get('account_type') == 'sum' :
                        count_view_left += 1
                last_row = row

            elif side == 'right' :
                if change == False :
                    row = 7
                    change = True

                if res.get('account_type') == 'sum' and count_view_right > 1:
                    worksheet.write(row, 5, 'TOTAL', wbf['total_mid_center'])
                    worksheet.write(row, 6, prev_total_data['name'] if prev_total_data.get('name') else '', wbf['total_mid'])
                    worksheet.write(row, 7, prev_total_data['balance'] if prev_total_data.get('balance') else 0.0, wbf['total_mid_float'])
                    worksheet.write(row, 8, prev_total_data['balance_cmp_1'] if prev_total_data.get('balance_cmp_1') else 0.0, wbf['total_mid_float'])
                    worksheet.write(row, 9, prev_total_data['balance_cmp_2'] if prev_total_data.get('balance_cmp_2') else 0.0, wbf['total_mid_float'])
                    
                    worksheet.write(row+2, 5, 'TOTAL', wbf['total_mid_center'])
                    worksheet.write(row+2, 6, total_data['name'] if total_data.get('name') else '', wbf['total_mid'])
                    worksheet.write(row+2, 7, total_data['balance'] if total_data.get('balance') else 0.0, wbf['total_mid_float'])
                    worksheet.write(row+2, 8, total_data['balance_cmp_1'] if total_data.get('balance_cmp_1') else 0.0, wbf['total_mid_float'])
                    worksheet.write(row+2, 9, total_data['balance_cmp_2'] if total_data.get('balance_cmp_2') else 0.0, wbf['total_mid_float'])

                    row +=1

                if res.get('account_type') != 'sum':
                    worksheet.write(row, 5, res['code_number'] if res.get('code_number') else ' ')
                    worksheet.write(row, 6, res['name'] if res.get('name') else '')
                    worksheet.write(row, 7, res['balance'] if res.get('balance') else 0)
                    worksheet.write(row, 8, res['balance_cmp_1'] if res.get('balance_cmp_1') else 0)
                    worksheet.write(row, 9, res['balance_cmp_2'] if res.get('balance_cmp_2') else 0)
                else :
                    worksheet.write(row, 5, res['code_number'] if res.get('code_number') else '', wbf['content_number_center_bold'])
                    worksheet.write(row, 6, res['name'] if res.get('name') else '', wbf['content_bold'])
                    worksheet.write(row, 7, '')
                    worksheet.write(row, 8, '')
                    worksheet.write(row, 9, '')

                if res.get('account_type') != 'sum' and count_view_right > 1:
                    count_view_right += 1
                    worksheet.write(row+1, 5, 'TOTAL', wbf['total_mid_center'])
                    worksheet.write(row+1, 6, total_data['name'] if total_data.get('name') else '', wbf['total_mid'])
                    worksheet.write(row+1, 7, total_data['balance'] if total_data.get('balance') else 0.0, wbf['total_mid_float'])
                    worksheet.write(row+1, 8, total_data['balance_cmp_1'] if total_data.get('balance_cmp_1') else 0.0, wbf['total_mid_float'])
                    worksheet.write(row+1, 9, total_data['balance_cmp_2'] if total_data.get('balance_cmp_2') else 0.0, wbf['total_mid_float'])
                elif res.get('account_type') == 'sum' :
                    count_view_right += 1
                last_row_liability = row

            no += 1
            row += 1

        max_row = (max([last_row_liability,last_row]) + 2) +1
        if is_balance_sheet :
            worksheet.merge_range('A%s:B%s'%(max_row,max_row), 'Total Aktiva' , wbf['total'])
            worksheet.merge_range('F%s:G%s'%(max_row,max_row), 'Total Liabilitas' , wbf['total'])
            worksheet.write(max_row - 1, 2, total_balance_asset, wbf['total_float'])
            worksheet.write(max_row - 1, 3, total_balance_cmp_1_asset, wbf['total_float'])
            worksheet.write(max_row - 1, 4, total_balance_cmp_2_asset, wbf['total_float'])
            worksheet.write(max_row - 1, 7, total_balance_liability, wbf['total_float'])
            worksheet.write(max_row - 1, 8, total_balance_cmp_1_liability, wbf['total_float'])
            worksheet.write(max_row - 1, 9, total_balance_cmp_2_liability, wbf['total_float'])
        else :
            worksheet.merge_range('A%s:B%s' % (max_row, max_row), 'Total', wbf['total'])
            worksheet.write(max_row - 1, 2, total, wbf['total_float'])
            worksheet.write(max_row - 1, 3, total_cmp_1, wbf['total_float'])
            worksheet.write(max_row - 1, 4, total_cmp_2, wbf['total_float'])

        worksheet.freeze_panes(header_row + 1,0)

        # Module Alias
        module_name = 'as_accounting_financial_report_horizontal'
        reference = 'as_accounting_report_view'
        class_name = self.__class__.__name__

        return template._return_to_form(self, workbook, fp, filename, module_name, reference, class_name)

