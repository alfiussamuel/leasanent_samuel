from odoo import api,fields,models,_
import time
from odoo.exceptions import UserError, RedirectWarning, ValidationError, except_orm, Warning
from datetime import datetime
import re
import base64
from cStringIO import StringIO
import xlsxwriter


class pengeluaran_biaya(models.Model):
    _name = "pengeluaran.biaya"
    name = fields.Char('No Bukti')
    date = fields.Date('Tanggal')
    company_id = fields.Many2one(comodel_name="res.company", string="Organisasi",
                                 default=lambda self: self.env.user.company_id)
    created_by = fields.Many2one('res.users', 'Created by', default=lambda self: self.env.user)
    journal_id = fields.Many2one('account.journal', 'Metode Pembayaran',
                                 domain=['|', ('type', '=', 'cash'), ('type', '=', 'bank')])
    state = fields.Selection([('Draft', 'Draft'),('Approved2', 'Approved 2'),('Approved', 'Approved'),('Posted', 'Posted')], string='Status', default="Draft")
    line_ids = fields.One2many('pengeluaran.biaya.line', 'reference', 'Detail Pengeluaran', copy=True)
    total_amount = fields.Float(compute="_get_total_amount", string='Total Pengeluaran')
    move_id = fields.Many2one(comodel_name="account.move", string="Jurnal ID")
    journal_count = fields.Integer('#Journal Entries', compute='_compute_journal_count')
    department_id = fields.Many2one(comodel_name="account.department", string="Department")


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('pengeluaran.biaya')
        return super(pengeluaran_biaya, self).create(vals)

    @api.depends('line_ids.amount')
    def _get_total_amount(self):
        for res in self:
            total = 0
            for line in res.line_ids:
                total += line.amount
            res.total_amount = total

    @api.one
    def button_approved(self):
        state = 'Approved'
        if self.total_amount > 25000000:
            state = 'Approved2'
        self.state = state

    @api.one
    def button_approved2(self):
        self.state = 'Approved'

    @api.one
    def button_post(self):
        move = self.env['account.move']
        total = 0
        data = []
        for i in self.line_ids:
            move_d = {
                'journal_id': self.journal_id.id,
                'account_id': i.account_id.id,
                'date': self.date,
                'name': i.name,
                'credit': 0,
                'debit': i.amount
            }
            total = total + i.amount
            data.append(((0, 0, move_d)))

            move_c = {
                    'journal_id': self.journal_id.id,
                    'account_id': self.journal_id.default_credit_account_id.id,
                    'date': self.date,
                    'name': i.name,
                    'credit':i.amount,
                    'debit': 0
            }
            data.append(((0, 0, move_c)))

        move_vals = {
            'name': '/',
            'journal_id': self.journal_id.id,
            'date': self.date,
            'line_ids': data,
            'ref': self.name
        }
        move_id = move.create(move_vals)
        self.write({'move_id': move_id.id,'state':"Posted"})

    @api.one
    def button_cancel(self):
        for res in self:
            if res.move_id:
                res.move_id.unlink()
            self.state = "Draft"

    @api.multi
    def action_view_journal(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id', '=', self.move_id.id)]
        action['context'] = {}
        return action

    @api.one
    def _compute_journal_count(self):
        for res in self:
            journal_ids = self.env['account.move'].search([('id', '=', res.move_id.id)])
            if journal_ids:
                res.journal_count = len(journal_ids)


class pengeluaran_biaya_line(models.Model):
    _name = "pengeluaran.biaya.line"
    reference = fields.Many2one('pengeluaran.biaya', 'Reference')
    account_biaya_id = fields.Many2one('account.biaya', 'Nama Biaya')
    account_id = fields.Many2one('account.account', 'COA')
    amount = fields.Float('Harga')
    name = fields.Char('Keterangan')

    @api.onchange('account_biaya_id')
    def onchange_biaya_id(self):
        if self.account_biaya_id:
            self.account_id = self.account_biaya_id.account_id.id


class Company(models.Model):
    _inherit = "res.company"
    ayat_silang_id = fields.Many2one("account.account", string="Ayat Silang")


class transaksi_bank(models.Model):
    _name = "transaksi.bank"

    name = fields.Char('No. Dokumen')
    date = fields.Date('Tanggal Dokumen', default=fields.Date.today())
    company_id = fields.Many2one(comodel_name="res.company", string="Organisasi",
                                 default=lambda self: self.env.user.company_id)
    journal_count = fields.Integer('# Journal Entries', compute='_compute_journal_count')
    state = fields.Selection([('Draft', 'Draft'), ('Posted', 'Posted')], string="Status", default="Draft")
    journal_bank_id = fields.Many2one('account.journal', 'Dari')
    journal_cash_id = fields.Many2one('account.journal', 'Tujuan Transfer')
    amount = fields.Float('Nilai Transaksi')
    no_cek = fields.Char('No. Check')
    keterangan = fields.Char('Keterangan')


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('transaksi.bank')
        return super(transaksi_bank, self).create(vals)

    @api.one
    def button_cancel(self):
        for res in self:
            move_ids = self.env['account.move'].search([('ref', '=', res.name)])
            if move_ids:
                for move_id in move_ids:
                    if move_id.state == "posted":
                        move_id.button_cancel()
                        move_id.unlink()
                    else:
                        move_id.unlink()
            self.state = "Draft"

    @api.multi
    def action_view_journal(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('ref', '=', self.name)]
        action['context'] = {}
        return action

    @api.one
    def _compute_journal_count(self):
        for res in self:
            journal_ids = self.env['account.move'].search([('ref', '=', res.name)])
            if journal_ids:
                res.journal_count = len(journal_ids)

    @api.multi
    def button_post(self):
        for res in self:
            vals_credit = {}
            vals_debit = {}
            debit_amount = 0
            credit_amount = 0

            # Rekening untuk Bank
            account_debit_only_id = res.company_id.ayat_silang_id.id
            account_debit_id = res.company_id.ayat_silang_id.id

            if not account_debit_id:
                raise Warning('Belum tersedia Perkiraan Ayat Silang untuk Organisasi ini')
            if not res.journal_bank_id.default_debit_account_id.id:
                raise Warning('Belum tersedia Perkiraan untuk Jurnal Bank')

            label_bank = self.keterangan
            label_ays =  self.keterangan

            vals_debit['name'] = label_ays  # res.name
            vals_debit['partner_id'] = res.company_id.partner_id.id or ''
            vals_debit['journal_id'] = res.journal_bank_id.id or ''
            vals_debit['date'] = res.date
            vals_debit['company_id'] = res.company_id.id or ''
            vals_debit['account_id'] = account_debit_id or ''
            vals_debit['debit'] = res.amount
            vals_debit['credit'] = 0

            vals_credit['name'] = label_bank
            vals_credit['partner_id'] = res.company_id.partner_id.id or ''
            vals_credit['journal_id'] = res.journal_bank_id.id or ''
            vals_credit['date'] = res.date
            vals_credit['company_id'] = res.company_id.id or ''
            vals_credit['account_id'] = res.journal_bank_id.default_debit_account_id.id or ''
            vals_credit['credit'] = res.amount
            vals_credit['debit'] = 0

            move_bank_id = self.env['account.move'].create({
                'ref': res.name,
                'journal_id': res.journal_bank_id.id,
                'date': res.date,
                'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)]
            })
            # move_bank_id.post()


            # Rekening untuk Cash
            vals_credit = {}
            vals_debit = {}
            debit_amount = 0
            credit_amount = 0

            account_credit_id = res.company_id.ayat_silang_id.id

            if not account_credit_id:
                raise Warning('Belum tersedia Perkiraan Ayat Silang untuk Organisasi ini')
            if not res.journal_cash_id.default_debit_account_id.id:
                raise Warning('Belum tersedia Perkiraan untuk Jurnal Tujuan')

            vals_debit['name'] = label_ays
            vals_debit['partner_id'] = res.company_id.partner_id.id or ''
            vals_debit['journal_id'] = res.journal_cash_id.id or ''
            vals_debit['date'] = res.date
            vals_debit['company_id'] = res.company_id.id or ''
            vals_debit['account_id'] = account_credit_id or ''
            vals_debit['credit'] = res.amount
            vals_debit['debit'] = 0

            vals_credit['name'] = label_ays
            vals_credit['partner_id'] = res.company_id.partner_id.id or ''
            vals_credit['journal_id'] = res.journal_cash_id.id or ''
            vals_credit['date'] = res.date
            vals_credit['company_id'] = res.company_id.id or ''
            vals_credit['account_id'] = res.journal_cash_id.default_debit_account_id.id or ''
            vals_credit['debit'] = res.amount
            vals_credit['credit'] = 0

            move_cash_id = self.env['account.move'].create({
                'ref': res.name,
                'journal_id': res.journal_cash_id.id,
                'date': res.date,
                'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)]
            })
            # move_cash_id.post()

            res.state = "Posted"

class AccountMove(models.Model):
    _inherit = "account.move"
    area_lks = fields.Many2one('account.area.location', 'Area/Lks')
    no_bukti = fields.Char(string="No. Bukti")

    @api.multi
    def button_print(self):
        return {
            'name': ('Print Excel'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.print.journal',
            'context': {'id': self.id},
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class account_area_location(models.Model):
    _name = "account.area.location"

    name = fields.Char(string="Area/LKS")
    keterangan = fields.Char(string="Keterangan")


class AccountMove(models.Model):
    _inherit = "account.move.line"
    area_lks = fields.Many2one('account.area.location', 'Area/Lks', compute="_get_detail", store=True)
    no_bukti = fields.Char('No. Bukti', compute="_get_detail", store=True)
    cif_code = fields.Char('CF Code', compute="_get_cif_code")

    @api.depends('move_id.area_lks')
    def _get_detail(self):
        for res in self:
            area_lks = False
            if res.move_id.area_lks:
                area_lks = res.move_id.area_lks.id
            res.area_lks = area_lks
            res.no_bukti = res.move_id.no_bukti

    @api.depends('account_id.cif_code')
    def _get_cif_code(self):
        for res in self:
            code = ''
            if res.account_id:
                code = res.account_id.cif_code
            res.cif_code = code

class wizard_print_journal(models.TransientModel):
    _name = 'wizard.print.journal'

    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)

    @api.multi
    def print_excel(self):
        id = self._context.get('active_ids')
        journal = self.env['account.move'].browse(id)
        ### Set Template ######################
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'Journal' + '-' + journal.no_bukti + '.xlsx'
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
        worksheet1.set_column('B:B', 30)
        worksheet1.set_column('C:C', 30)
        worksheet1.set_column('D:D', 20)
        worksheet1.set_column('E:E', 20)

        worksheet1.set_row(0, 30)

        date_to_raw = datetime.strptime(journal.date, '%Y-%m-%d')
        date_to = datetime.strftime(date_to_raw, '%d-%B-%Y')

        worksheet1.write(0, 0, 'No. Bukti', set_border_bold)
        worksheet1.write(1, 0, 'Tanggal', set_border_bold)
        worksheet1.write(2, 0, 'No. Internal', set_border_bold)

        worksheet1.write(0, 1, journal.no_bukti, set_border)
        worksheet1.write(1, 1, date_to, set_border)
        worksheet1.write(2, 1, journal.name or '', set_border)

        worksheet1.write(0, 2, 'Area', set_border_bold)
        worksheet1.write(1, 2, 'Ref', set_border_bold)
        worksheet1.write(2, 2, '', set_border)


        worksheet1.write(0, 3, journal.area_lks.name, set_border)
        worksheet1.write(1, 3, journal.ref, set_border)
        worksheet1.write(2, 3, '', set_border)


        worksheet1.write(5, 0, 'Perkiraan', header_table)
        worksheet1.write(5, 1, 'Partner', header_table)
        worksheet1.write(5, 2, 'Label', header_table)
        worksheet1.write(5, 3, 'Debit', header_table)
        worksheet1.write(5, 4, 'Kredit', header_table)

        row = 6
        total_debit = 0
        total_credit= 0
        for line in journal.line_ids :
            worksheet1.write(row, 0, line.account_id.code + ' '+ line.account_id.name, set_border)
            worksheet1.write(row, 1, line.partner_id.name, set_border)
            worksheet1.write(row, 2, line.name, set_border)
            worksheet1.write(row, 3, line.debit, set_right)
            worksheet1.write(row, 4, line.credit, set_right)
            row = row + 1
            total_debit = line.debit
            total_credit = line.credit
        worksheet1.write(row, 0, '', header_table)
        worksheet1.write(row, 1, '', header_table)
        worksheet1.write(row, 2, '', header_table)
        worksheet1.write(row, 3, total_debit, header_table_right)
        worksheet1.write(row, 4, total_credit, header_table_right)
        workbook.close()
        out = base64.encodestring(fp.getvalue())

        self.write({'data': out,
                    'name': filename,
                    'state_position': 'get',
                    })
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'acc_transaction_lea', 'wizard_print_journal')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.print.journal',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }


class invoice_reconcilement(models.Model):
    _name = "invoice.reconcilement"

    @api.model
    def _default_type(self):
        type = self._context.get('default_type')
        return type

    name        = fields.Char('No Dokumen')
    date        = fields.Date('Tanggal')
    company_id  = fields.Many2one(comodel_name="res.company", string="Organisasi",default=lambda self: self.env.user.company_id)
    created_by  = fields.Many2one('res.users', 'Created by', default=lambda self: self.env.user)
    type        = fields.Selection([('out_invoice', 'Customer Invoice'), ('in_invoice', 'Vendor Bill')], string='Type')
    invoice_id  = fields.Many2one('account.invoice', 'Invoice', domain=[('state', '=', 'open')])
    account_id  = fields.Many2one('account.account', 'Account')
    state       = fields.Selection([('Draft', 'Draft'), ('Posted', 'Posted')], string='Status', default="Draft")
    move_line_ids   = fields.Many2many('account.move.line', string='Move Line')
    partner_id      = fields.Many2one('res.partner', 'Partner')
    total_amount    = fields.Float('Total Invoice', compute='_compute_amount', store=True)
    total_paid      = fields.Float('Total Paid', compute='_compute_amount', store=True)

    @api.depends('invoice_id','move_line_ids','type','invoice_id.partner_id')
    def _compute_amount(self):
        for res in self:
            total_amount = 0
            total_paid   = 0
            if res.invoice_id :
                total_amount = res.invoice_id.amount_total
            if res.move_line_ids:
                for l in res.move_line_ids :
                    if res.type =='out_invoice':
                        total_paid = total_paid + l.credit
                    else :
                        total_paid = total_paid + l.debit
            res.total_amount = total_amount
            res.total_paid   = total_paid


    @api.model
    def create(self, vals):
        if vals.get('type') == 'out_invoice':
            vals['name'] = self.env['ir.sequence'].get('invoice.reconcilement')
        else :
            vals['name'] = self.env['ir.sequence'].get('vendor.invoice.reconcilement')
        return super(invoice_reconcilement, self).create(vals)

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id:
            self.account_id = self.invoice_id.account_id.id
            self.partner_id = self.invoice_id.partner_id.id


    @api.multi
    @api.onchange('account_id','type')
    def onchange_account_id(self):
        if self.account_id:
            if self.type == 'out_invoice':
                return {'domain': {'move_line_ids': [('partner_id', '=', self.partner_id.id),('account_id', '=', self.account_id.id),('debit', '=', 0)]}}
            else :
                return {'domain': {'move_line_ids': [('partner_id', '=', self.partner_id.id),('account_id', '=', self.account_id.id),('credit', '=', 0)]}}

    @api.multi
    def button_post(self):
        for res in self :
            for l in res.move_line_ids:
                res.invoice_id.assign_outstanding_credit(l.id)
        self.state = 'Posted'

    @api.multi
    def button_cancel(self):
        for res in self:
            for l in res.move_line_ids:
                l.remove_move_reconcile()
        self.state = 'Draft'

class account_department(models.Model):
    _name = "account.department"

    name = fields.Char(string="Departemen")


class account_biaya(models.Model):
    _name = "account.biaya"

    name = fields.Char(string="Nama Biaya")
    code = fields.Char(string="Code")
    account_id = fields.Many2one('account.account', 'Account')
    cif_code   = fields.Char('CF Code', compute="_get_cif_code", store=True)
    cif_name   = fields.Char('CF Name', compute="_get_cif_code", store=True)

    @api.depends('account_id.cif_code','account_id.cif_name')
    def _get_cif_code(self):
        for res in self:
            code = ''
            name = ''
            if res.account_id:
                code = res.account_id.cif_code
                name = res.account_id.cif_name
            res.cif_code = code
            res.cif_name = name

class account_account(models.Model):
    _inherit = "account.account"

    cif_code = fields.Char(string="Code CF")
    cif_name = fields.Char(string="Name CF")













