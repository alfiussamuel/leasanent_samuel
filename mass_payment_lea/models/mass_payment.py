from openerp import fields, models, api, _
from datetime import datetime, date, timedelta
from openerp.exceptions import Warning, UserError
from openerp.osv import osv


class MassPaymentLine(models.Model):
    _name = 'mass.payment.line'
    
    reference = fields.Many2one('mass.payment', 'Reference')
    invoice_id = fields.Many2one('account.invoice', 'Nomor Invoice')
    partner_id = fields.Many2one('res.partner', 'Pihak')    
    date = fields.Date('Tanggal Pembayaran')
    due_date = fields.Date('Tanggal Jatuh Tempo')
    due_amount = fields.Float('Sisa Tagihan')
    payment_amount = fields.Float('Jumlah Bayar')
    nomor_faktur = fields.Char('Nomor Faktur')


class MassPaymentLineBiaya(models.Model):
    _name = 'mass.payment.line.biaya'

    reference = fields.Many2one('mass.payment', 'Reference')
    account_id = fields.Many2one('account.account', 'Account')
    amount = fields.Float('Amount')
    
    
class mass_payment(models.Model):
    _name = 'mass.payment'

    @api.one
    @api.depends('line_ids')
    def _get_amount_total(self):
        total = 0.0
        if self.line_ids:
            for each_payment in self.line_ids:
                total += each_payment.payment_amount
        self.total = total

    name        = fields.Char(string="Name")
    company_id  = fields.Many2one('res.company', string="Organisasi", default=lambda self:self.env.user.company_id)
    partner_ids = fields.Many2many('res.partner', string="Partner")
    partner_id  = fields.Many2one('res.partner', string="Pihak")
    journal_id  = fields.Many2one('account.journal', string="Journal")
    journal_id      = fields.Many2one('account.journal', string="Kas/Bank", domain=[('type', 'in', ('bank', 'cash'))])
    partner_type    = fields.Selection([('customer', 'Customer'), ('supplier', 'Supplier')], string="Partner Type")
    no_of_day       = fields.Integer(string="Number of Days Old")
    state           = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancel')], readonly=True, default='draft', copy=False, string="Status")
    account_payment_ids = fields.One2many('account.payment', 'mass_payment_id', string="Payments")
    line_ids            = fields.One2many('mass.payment.line', 'reference', string="Payments")
    total               = fields.Float(string="Total", compute='_get_amount_total')
    journal_count       = fields.Integer('# Journal Entries', compute='_compute_journal_count')
    payment_date        = fields.Date(string="Payment Date")
    move_id             = fields.Many2one('account.move', string="Jurnal")
    is_residual         = fields.Boolean('Is residual', default=False)
    residual            = fields.Float('Kekurangan/Kelebihan')
    total_paid          = fields.Float('Total Pembayaran')
    account_residual_id = fields.Many2one('account.account', string="Account Kekurangan/Kelebihan")
    line_biaya_ids      = fields.One2many('mass.payment.line.biaya', 'reference', string="Biaya")
    invoice_ids         = fields.Many2many('account.invoice', string='Daftar Invoice')


    @api.multi
    @api.onchange('total_paid')
    def onchange_total_paid(self):
        values = {
            'is_residual': False,
            'residual': 0
        }
        total = self.total - self.total_paid
        if total != 0:
            values['is_residual'] = True
            values['residual'] = total
        self.update(values)

    @api.one
    def button_cancel_old(self):
        for res in self:            
            move_ids = self.env['account.move'].search([('ref','=',res.name)])
            if move_ids:
                for move_id in move_ids:
                    if move_id.state == "posted":
                        move_id.button_cancel()
                        move_id.unlink()
                    else:
                        move_id.unlink()
            self.state = "draft"

    @api.one
    def button_cancel(self):
        for res in self:
            if self.move_id:
                # for move_id in self.move_ids:
                # fungsi untuk unreconcile jurnal nya
                for line in self.move_id.line_ids:
                    if line.reconciled == True and line.mass_payment_line_id:
                        line.remove_move_reconcile()
                        ####################################
                if self.move_id.state == "posted":
                    self.move_id.button_cancel()
                    self.move_id.unlink()
                else:
                    self.move_id.unlink()
            self.state = "draft"

            
    @api.multi
    def action_view_journal(self):      
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('ref', '=', self.name)]
        action['context'] = {}
        return action
    
    @api.one
    def _compute_journal_count(self):
        for res in self:
            journal_ids = self.env['account.move'].search([('ref','=',res.name)])
            if journal_ids:         
                res.journal_count = len(journal_ids)
                
    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            if self.partner_type=='customer':
                return {'domain': {
                                   'partner_ids': [('customer', '=', True)],
                                   # 'journal_id': [('type', 'in', ('cash','bank')),('company_id','=',self.env.user.company_id.id)]
                                   }}
            else:
                return {'domain': {'partner_ids': [('supplier', '=', True)]}}

    @api.multi
    def button_confirm(self):
        self.state = "confirmed"
    
    @api.model
    def create(self, vals):
        if vals.get('partner_type') and vals.get('partner_type') == 'customer':
            vals['name'] = self.env['ir.sequence'].next_by_code('customer.mass.payment') or '/'
        elif vals.get('partner_type') and vals.get('partner_type') == 'supplier':
            vals['name'] = self.env['ir.sequence'].next_by_code('supplier.mass.payment') or '/'
        return super(mass_payment, self).create(vals)

    @api.multi
    def post(self):
        if self.line_ids:
            #Penerimaan Customer
            if self.partner_type == 'customer':
                acc_obj = self.pool['account.invoice']
                journal_id = self.journal_id.id
                account_debit_id = self.journal_id.default_debit_account_id.id
                data  = []
                if not account_debit_id:
                    raise Warning('Belum tersedia Perkiraan untuk Jurnal Kas/Bank yang dipilih')

                for each_payment_id in self.line_ids:                                    
                    vals_credit = {}
                    vals_debit = {}                                
                    debit_amount = 0
                    credit_amount = 0
                    move_id = ''
                    credit_line_vals = {
                        'name': self.name,
                        'partner_id': each_payment_id.partner_id.id or '',
                        'journal_id': journal_id or '',
                        'date': self.payment_date,
                        'credit': each_payment_id.payment_amount,
                        'debit': 0,
                        'account_id': each_payment_id.invoice_id.account_id.id or '',
                        'mass_payment_line_id': each_payment_id.id,
                        'invoice_id': each_payment_id.invoice_id.id or False,
                        'company_id': self.env.user.company_id.id or ''
                    }
                    data.append(((0, 0, credit_line_vals)))

                if self.residual < 0 :
                    debit_line_vals_res = {
                        'name': self.name,
                        'partner_id': self.company_id.partner_id.id or '',
                        'journal_id': journal_id or '',
                        'date': self.payment_date,
                        'credit': abs(self.residual),
                        'debit': 0,
                        'account_id': self.account_residual_id.id,
                        'company_id': self.env.user.company_id.id or ''

                    }
                    data.append(((0, 0, debit_line_vals_res)))


                elif self.residual > 0:
                    debit_line_vals_res = {
                        'name': self.name,
                        'partner_id': self.company_id.partner_id.id or '',
                        'journal_id': journal_id or '',
                        'date': self.payment_date,
                        'credit': 0,
                        'debit': abs(self.residual),
                        'account_id': self.account_residual_id.id,
                        'company_id': self.env.user.company_id.id or ''

                    }
                    data.append(((0, 0, debit_line_vals_res)))

                total_biaya = 0
                for l in self.line_biaya_ids:
                    debit_biaya_line_vals = {
                        'name': self.name,
                        'partner_id': self.company_id.partner_id.id or '',
                        'journal_id': journal_id or '',
                        'date': self.payment_date,
                        'credit': 0,
                        'debit': l.amount,
                        'account_id': l.account_id.id or '',
                        'company_id': self.env.user.company_id.id or ''

                    }
                    data.append(((0, 0, debit_biaya_line_vals)))
                    total_biaya = total_biaya + l.amount

                total_final_bank = self.total_paid - total_biaya

                debit_line_vals = {
                    'name': self.name,
                    'partner_id': self.company_id.partner_id.id or '',
                    'journal_id': journal_id or '',
                    'date': self.payment_date,
                    'credit': 0,
                    'debit': total_final_bank,
                    'account_id': account_debit_id or '',
                    'company_id':self.env.user.company_id.id or ''

                }
                data.append(((0, 0, debit_line_vals)))
                #raise Warning(str(data))
                    
                move_id = self.env['account.move'].create({
                                                    'ref': self.name,                                        
                                                    'journal_id': journal_id,
                                                    'date': self.payment_date,
                                                    'line_ids': data,
                                                    })                
                    #move_id.post()
                self.write({'move_id': move_id.id})
                    

            #Pembayaran Vendor           
            if self.partner_type == 'supplier':
                for each_payment_id in self.line_ids:
                    vals_credit = {}
                    vals_debit = {}                                
                    debit_amount = 0
                    credit_amount = 0
                    move_id = ''           
                    
                    #Rekening untuk Kantor Pusat                
                    journal_id = self.journal_id.id
                    account_credit_id = self.journal_id.default_credit_account_id.id
                                                    
                    if not account_credit_id:
                        raise Warning('Belum tersedia Perkiraan untuk Jurnal Kas/Bank yang dipilih')

    
                    vals_debit['name'] = self.name
                    vals_debit['partner_id'] = each_payment_id.partner_id.id or ''                
                    vals_debit['journal_id'] = journal_id or ''
                    vals_debit['date'] = self.payment_date
                    vals_debit['company_id'] = self.company_id.id or ''
                    vals_debit['account_id'] = each_payment_id.invoice_id.account_id.id or ''
                    vals_debit['debit'] = each_payment_id.payment_amount
                    vals_debit['credit'] = 0
                    vals_debit['mass_payment_line_id'] = each_payment_id.id
                    
                    vals_credit['name'] = self.name
                    vals_credit['partner_id'] = each_payment_id.partner_id.id or ''                
                    vals_credit['journal_id'] = journal_id or ''
                    vals_credit['date'] = self.payment_date
                    vals_credit['company_id'] = self.company_id.id or ''
                    vals_credit['account_id'] = account_credit_id or ''
                    vals_credit['credit'] = each_payment_id.payment_amount
                    vals_credit['debit'] = 0            
                    
                    move_id = self.env['account.move'].create({
                                                    'ref': self.name,                                        
                                                    'journal_id': journal_id,
                                                    'date': fields.date.today(),                                                
                                                    'line_ids': [(0, 0, vals_credit), (0, 0, vals_debit)],                                                                                               
                                                    })                
                    #move_id.post()
                    self.write({'move_id': move_id.id})

            for line in self.line_ids:
                credit_aml = self.env['account.move.line'].search([('mass_payment_line_id', '=', line.id)])
                for c in credit_aml:
                    line.invoice_id.assign_outstanding_credit(c.id)
                
            #===============================================================
            """
            acc_obj = self.pool['account.invoice']
            for each_payment_id in self.account_payment_ids:
                ctx = dict(self._context)
                ctx.update({'force_company': each_payment_id.company_invoice_id.id})
                each_payment_id.with_context(ctx).state = 'posted'

                if each_payment_id.state == 'posted':
                    for each_move_line in each_payment_id.move_line_ids:
                        if self.partner_type == 'customer':
                            if each_move_line.credit > 0 and each_move_line.debit == 0 and each_payment_id.invoice_id:
                                each_payment_id.invoice_id.assign_outstanding_credit(each_move_line.id)
                            else:
                                if each_move_line.credit == 0 and each_move_line.debit > 0 and each_payment_id.invoice_id:
                                    each_payment_id.invoice_id.assign_outstanding_credit(each_move_line.id)
            """
            #===========================================================
            if all(['posted' == x.state for x in self.account_payment_ids]):
                self.state = "posted"


    @api.multi
    def create_draft_payment(self):
        for res in self:
            """
            if res.partner_type == 'customer':
                invoice_ids = self.env['account.invoice'].search([('company_id', '=', res.company_id.id),
                                                          ('partner_id', '=', res.partner_id.id),
                                                          ('type', '=', 'out_invoice'),
                                                          ('state', '=', 'open')])
            else:
                invoice_ids = self.env['account.invoice'].search([('partner_id', '=', res.partner_id.id),
                                                          ('type', '=', 'in_invoice'),
                                                          ('company_id', '=', res.company_id.id),
                                                          ('state', '=', 'open')])
            """
            invoice_ids = res.invoice_ids
            if invoice_ids:
                current_ids = self.env['mass.payment.line'].search([('reference','=',res.id)])
                if current_ids:
                    for current in current_ids:
                        current.unlink()
                
                for invoice in invoice_ids:
                    nomor_faktur = ''
                    if invoice.type == 'out_invoice':
                        nomor_faktur = invoice.nomor_faktur_id.name
                    self.env['mass.payment.line'].create({
                                                          'reference' : res.id,
                                                          'invoice_id' : invoice.id,
                                                          'nomor_faktur': nomor_faktur,
                                                          'partner_id' : res.partner_id.id,    
                                                          'date' : fields.Date.today(),
                                                          'due_date' : invoice.date_due,
                                                          'due_amount' : invoice.residual,
                                                          'payment_amount' : invoice.residual
                                                          })
                
        #=======================================================================
        # account_invoice_obj = self.env['account.invoice']
        # if self.account_payment_ids:
        #     for each_id in self.account_payment_ids:
        #         each_id.unlink()
        # if self and self.partner_type:
        #     company_id = self.company_id                        
        #     if not self.partner_ids:
        #         if self.partner_type == 'customer':
        #             partner_ids = [each_partner.id for each_partner in self.env['res.partner'].search([('customer', '=', True)])]
        #         else:
        #             partner_ids = [each_partner.id for each_partner in self.env['res.partner'].search([('supplier', '=', True)])]
        #     else:
        #         partner_ids = [each_partner.id for each_partner in self.partner_ids]
        #     if not self.no_of_day:
        #         to_date = date.today()
        #     else:
        #         if self.no_of_day < 0:
        #             raise Warning(_("No of day must be in positive."))
        #         to_date = date.today() - timedelta(days=int(self.no_of_day))
        #     payment_list = []
        #     if self.partner_type == 'customer':
        #         invoice_ids = account_invoice_obj.search([('company_id', '=', company_id.id),
        #                                                   ('partner_id', 'in', partner_ids),
        #                                                   ('type', '=', 'out_invoice'),
        #                                                   ('date_invoice', '<=', to_date),
        #                                                   ('state', '=', 'open')])
        #     else:
        #         invoice_ids = account_invoice_obj.search([('partner_id', 'in', partner_ids),
        #                                                   ('type', '=', 'in_invoice'),                                                          
        #                                                   ('status_hutang', '=', 'Kantor Pusat'),
        #                                                   ('state', '=', 'open')])
        #                                                   
        #     if invoice_ids:
        #         payments_default_data = self.env['account.payment'].default_get(['currency_id','payment_date','state','name'])
        #         for each_invoice in invoice_ids:
        #             print each_invoice.company_id.name                    
        #             if not self.journal_id:
        #                 journal_id = self.env['account.journal'].search([('company_id', '=', company_id.id),('type', '=', 'bank')], limit=1)
        #             else:
        #                 journal_id = self.journal_id
        #             if journal_id:
        #                 payment_list.append((0, 0, {'currency_id': payments_default_data.get('currency_id'),
        #                                             'payment_date': payments_default_data.get('payment_date'),
        #                                             'state': payments_default_data.get('state'),
        #                                             'name': payments_default_data.get('name'),
        #                                             'payment_type': self._context.get('default_payment_type'),
        #                                             'partner_type': self._context.get('default_partner_type'),
        #                                             'partner_id': each_invoice.partner_id.id,
        #                                             'invoice_id': each_invoice.id,
        #                                             'journal_id': journal_id.id,
        #                                             'residual': each_invoice.residual,
        #                                             'amount': each_invoice.residual,
        #                                             'payment_method_id': 2,
        #                                             #'company_id': company_pusat_id.id,
        #                                             'company_invoice_id': each_invoice.company_id.id
        #                                             }))
        #         self.account_payment_ids = payment_list
        # return True
        #=======================================================================

    @api.multi
    def action_view_journal_entries(self):
        if self.account_payment_ids:
            journal_entries_id = []
            for each_payment_id in self.account_payment_ids:
                if each_payment_id.move_line_ids:
                    journal_entries_id.append(each_payment_id.move_line_ids[0].move_id.id)
            if journal_entries_id:
                return {"type": "ir.actions.act_window",
                 "res_model": "account.move",
                 'view_type': 'form',
                 'view_mode': 'tree',
                 "target": "current",
                 'domain': [('id', 'in', journal_entries_id)]
                }


class account_payment(models.Model):
    _inherit = "account.payment"

    mass_payment_id = fields.Many2one('mass.payment', string="Mass Payment ID")
    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    residual = fields.Float('Residual')
    company_invoice_id = fields.Many2one('res.company', 'Company')

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if not self.mass_payment_id:
            return
        if self.invoice_id:
            self.amount = self.invoice_id.residual
            self.residual = self.invoice_id.residual
            self.currency_id = self.invoice_id.currency_id.id


class account_journal(models.Model):
    _inherit = 'account.journal'
 
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('mass_payment_journal_id'):
            args = args or []
            args.append(('id', '=', self._context.get('mass_payment_journal_id')))
            recs = self.browse()
            if name:
                recs = self.search([('number', '=', name)] + args, limit=limit)
            if not recs:
                recs = self.search([('name', operator, name)] + args, limit=limit)
            return recs.name_get()
        return super(account_journal, self).name_search(name, args, operator, limit)


class AccountMoveLine(models.Model):    
    _inherit = 'account.move.line'

    mass_payment_line_id = fields.Many2one('mass.payment.line', 'Mass Payment Line')
    
    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        print "YUHUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU"
        #Perform all checks on lines
        company_ids = set()
        all_accounts = []
        partners = set()
        for line in self:
            print "BASHJS ", line.account_id.name
            print "BASHJS ", line.account_id.company_id.name
            print "*&%P$*$%$%$%$ ", line.company_id.name
            company_ids.add(line.company_id.id)
            all_accounts.append(line.account_id)
            if (line.account_id.internal_type in ('receivable', 'payable')):
                partners.add(line.partner_id.id)
            if line.reconciled:
                raise UserError(_('You are trying to reconcile some entries that are already reconciled!'))
        if len(company_ids) > 1:
            print "IKIIIIIIIIIIIII LO"
            raise UserError(_('To reconcile the entries company should be the same for all entries!'))
        if len(set(all_accounts)) > 1:
            raise UserError(_('Entries are not of the same account!'))
        if not all_accounts[0].reconcile:
            raise UserError(_('The account %s (%s) is not marked as reconciliable !') % (all_accounts[0].name, all_accounts[0].code))
        if len(partners) > 1:
            raise UserError(_('The partner has to be the same on all lines for receivable and payable accounts!'))

        #reconcile everything that can be
        remaining_moves = self.auto_reconcile_lines()

        #if writeoff_acc_id specified, then create write-off move with value the remaining amount from move in self
        if writeoff_acc_id and writeoff_journal_id and remaining_moves:
            all_aml_share_same_currency = all([x.currency_id == self[0].currency_id for x in self])
            writeoff_vals = {
                'account_id': writeoff_acc_id.id,
                'journal_id': writeoff_journal_id.id
            }
            if not all_aml_share_same_currency:
                writeoff_vals['amount_currency'] = False
            writeoff_to_reconcile = remaining_moves._create_writeoff(writeoff_vals)
            #add writeoff line to reconcile algo and finish the reconciliation
            remaining_moves = (remaining_moves + writeoff_to_reconcile).auto_reconcile_lines()
            return writeoff_to_reconcile
        return True


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        self.ensure_one()
        credit_aml = self.env['account.move.line'].browse(credit_aml_id)
        if not credit_aml.currency_id and self.currency_id != self.company_id.currency_id:
            credit_aml.with_context(allow_amount_currency=True).write({
                'amount_currency': self.company_id.currency_id.with_context(date=credit_aml.date).compute(credit_aml.balance, self.currency_id),
                'currency_id': self.currency_id.id})
        if credit_aml.payment_id:
            credit_aml.payment_id.write({'invoice_ids': [(4, self.id, None)]})
        return self.register_payment(credit_aml)
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('from_mass_payment') and self._context.get('partner_type') and \
            self._context.get('partner_id') and self._context.get('company_id'):
            args = args or []
            args.append(('company_id', '=', self._context.get('company_id')))
            args.append(('partner_id', '=', self._context.get('partner_id')))
            args.append(('state', '=', 'open'))
            if self._context.get('partner_type') == 'customer':
                args.append(('type', '=', 'out_invoice'))
            else:
                args.append(('type', '=', 'in_invoice'))
            if self._context.get('no_of_day'):
                to_date = date.today() - timedelta(days=int(self._context.get('no_of_day')))
                args.append(('date_invoice', '<=', to_date))
            recs = self.browse()
            if name:
                recs = self.search([('number', '=', name)] + args, limit=limit)
            if not recs:
                recs = self.search([('name', operator, name)] + args, limit=limit)
            return recs.name_get()
        return super(AccountInvoice, self).name_search(name, args, operator, limit)




class res_partner(osv.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name, args=None, operator='ilike',limit=100):
        if self._context.get('from_mass_payment'):
            args = args or []
            if self._context.get('partner_ids') and self._context.get('partner_ids')[0][2]:
                args.append(('id', 'in', self._context.get('partner_ids')[0][2]))
            recs = self.browse(cr, uid, [])
            if name:
                recs = self.search([('number', '=', name)] + args, limit=limit)
            if not recs:
                recs = self.search([('name', operator, name)] + args, limit=limit)
            recs = self.browse(recs)
            return recs.name_get()
        return super(res_partner,self).name_search(name, args, operator=operator, limit=limit)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: