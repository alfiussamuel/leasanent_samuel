# -*- coding: utf-8 -*-
import base64
from cStringIO import StringIO
from odoo import api, fields, models
import xlsxwriter
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError



class buku_kasbank(models.TransientModel):
    _name = 'buku.kasbank'

    @api.model
    def _default_company(self):
        user = self.env['res.users'].browse(self.env.uid)
        return user.company_id.id

    journal_id          = fields.Many2one('account.journal','Jurnal')
    account_id          = fields.Many2one('account.account','Account')
    partner_id          = fields.Many2one('res.partner','Partner')
    date_from           = fields.Date(string='Start Date')
    date_to             = fields.Date(string='End Date')
    state_move          = fields.Selection([('posted', 'Posted'), ('all', 'All')], default='all')
    init_balance        = fields.Float(string='Saldo Awal')
    current_debit       = fields.Float(string='Mutasi Debit')
    current_credit      = fields.Float(string='Mutasi Credit')
    ending_balance      = fields.Float(string='Saldo Saat ini')
    mutasi_lines       = fields.One2many(comodel_name="buku.kasbank.line", inverse_name="wizard_id", string="Daftar Transaksi")
    company_id = fields.Many2one('res.company','Company',default=_default_company)
    state_position = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    
    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id:
            self.account_id = self.journal_id.default_debit_account_id.id
            self.partner_id = self.journal_id.bank_id.partner_id.id

    
    @api.multi
    def generate_report(self):
        fp = StringIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook.add_format()
        filename = 'laporan_buku_kas_dan_bank.xlsx'
        workbook.add_format({'bold': 1, 'align':'center'})
        

        worksheet1 = workbook.add_worksheet("Report Excel")
        #################################################################################
        center_title = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center'})
        center_title.set_font_size('14')
        center_title.set_border()
        #################################################################################
        bold_font = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'left'})
        bold_font.set_text_wrap()
        #################################################################################
        header_table = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'center'})
        header_table.set_text_wrap()
        header_table.set_bg_color('#eff0f2')
        header_table.set_border()
        #################################################################################
        footer_table = workbook.add_format({'bold': 1, 'valign':'vcenter', 'align':'right'})
        footer_table.set_text_wrap()
        footer_table.set_border()
        #################################################################################
        set_right = workbook.add_format({'valign':'vcenter', 'align':'right'})
        set_right.set_text_wrap()
        set_right.set_border()
        #################################################################################
        set_border = workbook.add_format({'valign':'vcenter', 'align':'left'})
        set_border.set_text_wrap()
        set_border.set_border()
        #################################################################################

        worksheet1.set_column('A:A', 20)
        worksheet1.set_column('B:B', 20)
        worksheet1.set_column('C:C', 20)
        worksheet1.set_column('D:D', 20)
        
        worksheet1.set_row(0, 30)
        worksheet1.merge_range('A1:D1', 'BUKU KAS DAN BANK', center_title)

        worksheet1.write(2, 0, 'JURNAL', bold_font)
        worksheet1.write(3, 0, 'AKUN', bold_font)
        worksheet1.write(4, 0, 'TANGGAL MULAI', bold_font)
        worksheet1.write(5, 0, 'TANGGAL SELESAI', bold_font)
        
        worksheet1.write(2, 1, self.journal_id.name, bold_font)
        worksheet1.write(3, 1, self.account_id.name, bold_font)
        worksheet1.write(4, 1, self.date_from, bold_font)
        worksheet1.write(5, 1, self.date_to, bold_font)
        
    
        
        worksheet1.write(7, 0, 'Tanggal', header_table)
        worksheet1.write(7, 1, 'Debit', header_table)
        worksheet1.write(7, 2, 'Kredit', header_table)
        worksheet1.write(7, 3, 'Keterangan', header_table)
       
        if self.state_move == 'posted':
            status = ['posted']
        else:
            status = ['draft','posted']
            
        # domain_ji = [('contract_fleet_id.company_id', '=', self.company.id)] 
        #journal_op = self.env['account.journal'].search([('name', '=', 'Opening Balance'),('company_id', '=', self.company_id.id)], limit=1)
        aml_initial = self.env['account.move.line'].search([('partner_id', '=', self.partner_id.id),('account_id', '=', self.account_id.id),('date', '<', self.date_from),('move_id.state', 'in', status),('company_id', '=', self.company_id.id)])  
        #aml_initial_opname = self.env['account.move.line'].search([('journal_id', '=', journal_op.id),('partner_id', '=', self.partner_id.id),('account_id', '=', self.account_id.id),('date', '<', self.date_from),('move_id.state', 'in', status),('company_id', '=', self.company_id.id)]) 
          
        aml = self.env['account.move.line'].search([('partner_id', '=', self.partner_id.id),('account_id', '=', self.account_id.id),('date', '>=', self.date_from),('date', '<=', self.date_to),('move_id.state', 'in', status),('company_id', '=', self.company_id.id)])
        #aml_opname = self.env['account.move.line'].search([('journal_id', '=', journal_op.id),('partner_id', '=', self.partner_id.id),('account_id', '=', self.account_id.id),('date', '>=', self.date_from),('date', '<=', self.date_to),('move_id.state', 'in', status),('company_id', '=', self.company_id.id)])
        #worksheet1.write(7, 12, 'tes '+str(len(aml)))
        
        init_debit = 0
        init_credit = 0
        bk_line = self.env['buku.kasbank.line']
        i = 8
        for init in aml_initial:
            
            init_debit = init_debit + init.debit
            init_credit = init_credit + init.credit
            
        saldo_awal = init_debit - init_credit
        
       
        curr_debit = 0
        curr_credit = 0
        
        for a in aml:
            curr_debit = curr_debit + a.debit
            curr_credit = curr_credit + a.credit
            
            worksheet1.write(i, 0, a.date)
            worksheet1.write(i, 1, a.debit)
            worksheet1.write(i, 2, a.credit)
            worksheet1.write(i, 3, a.name)
            
            bk_line.create({
                            'wizard_id': self.id,
                            'date': a.date,
                            'mutasi_debit': a.debit,
                            'mutasi_credit': a.credit,
                            'desc': a.name,
                           
                        })
            i=i+1
        """
        for b in aml_opname:
            curr_debit = curr_debit + b.debit
            curr_credit = curr_credit + b.credit
            
            worksheet1.write(i, 0, b.date)
            worksheet1.write(i, 1, b.debit)
            worksheet1.write(i, 2, b.credit)
            worksheet1.write(i, 3, b.name)
            bk_line.create({
                            'wizard_id': self.id,
                            'date': b.date,
                            'mutasi_debit': b.debit,
                            'mutasi_credit': b.credit,
                            'desc': b.name,
                           
                        })
            i=i+1
        """
        current_mutasi = curr_debit - curr_credit
        saldo_final = saldo_awal + current_mutasi
        i= i + 1
        worksheet1.write(i,   0, 'Saldo Awal', bold_font)
        worksheet1.write(i+1, 0, 'Mutasi Debit', bold_font)
        worksheet1.write(i+2, 0, 'Mutasi Kredit', bold_font)
        worksheet1.write(i+3, 0, 'Saldo Saat Ini', bold_font)
        
        worksheet1.write(i,   1, saldo_awal,  bold_font)
        worksheet1.write(i+1, 1, curr_debit,  bold_font)
        worksheet1.write(i+2, 1, curr_credit, bold_font)
        worksheet1.write(i+3, 1, saldo_final, bold_font)

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'data':out,
                    'name': filename, 
                    'state_position': 'get',
                    'init_balance':saldo_awal,
                    'current_debit':curr_debit,
                    'current_credit':curr_credit,
                    'ending_balance':saldo_final})
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference(
            'an_buku_kasbank_report', 'report_buku_kasbank_wizard')
        form_id = form_res and form_res[1] or False
        return {
            'name': ('Download XLS'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'buku.kasbank',
            'res_id': self.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }
        
class buku_kasbank_line(models.TransientModel):
    _name = 'buku.kasbank.line'

  
    wizard_id           = fields.Many2one('buku.kasbank','Buku Kasbank ID')
    date                = fields.Date('Tanggal')
    mutasi_debit        = fields.Float('Mutasi Debit')
    mutasi_credit       = fields.Float('Mutasi Credit')
    desc                = fields.Char('Keterangan')

