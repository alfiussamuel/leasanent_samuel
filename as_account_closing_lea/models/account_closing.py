from odoo import fields, api, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, RedirectWarning, ValidationError, except_orm, Warning

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

class AccountClosing(models.Model):
    _name           = 'account.closing'
    _description    = 'Account Closing'
    _inherit        = 'mail.thread'
    _order          = 'id desc'

    name                    = fields.Char(string='Closing Period')
    fiscalyear_id           = fields.Many2one('account.fiscalyear',string='Fiscal Year',ondelete='cascade')
    period_id               = fields.Many2one('account.period',string='Period',ondelete='cascade')
    company_id              = fields.Many2one('res.company', string='Company',  default=lambda self: self.env.user.company_id)
    closing_detail_ids      = fields.One2many('account.closing.detail','closing_id',string='Closing Details',track_visibility='always',domain=[('options','=','0')])
    full_closing_detail_ids = fields.One2many('account.closing.detail','closing_id',string='Full Closing Details',track_visibility='always',domain=[('options','=','1')])
    date_to                 = fields.Date('End Date')
    date_to_first_year      = fields.Date('End Date')
    date_from               = fields.Date('Start Date')
    date_from_first_year    = fields.Date('Start Date')
    state                   = fields.Selection([('draft','Open'),
                                                ('done','Closed'),
                                                ('cancel','Cancelled')
                                                ],string='State',default='draft')

    _sql_constraints = [
        ('period_company_uniq', 'unique(period_id,company_id,state)',
        ("There is already a record defined on this period\n"
          "You cannot create another : Consider cancel those record"))
    ]

    @api.multi
    def _check_period_state(self):
        for closing in self :
            datas = self.search([('period_id','=',closing.period_id.id),('company_id','=',self.company_id.id),('id','<>',closing.id)])
            for x in datas :
                if x.state != 'cancel' :
                    return False
        return True

    _constraints = [
        (_check_period_state, 'Error!\nThe period you are selecting already defined.', ['period_id']),
    ]

    @api.onchange('fiscalyear_id','period_id','company_id')
    def onchange_name(self):
        self.name = self.company_id.name + " / " + self.period_id.name + ' ' + self.fiscalyear_id.name

    @api.model
    def create(self,vals) :
        #raise UserError(_('You cannot remove Closed Account Closing2.'))
        if not vals.get('name'):
            company_id = self.env['res.company'].sudo().browse(vals['company_id'])
            period_id = self.env['account.period'].browse(vals['period_id'])
            fiscalyear_id = self.env['account.fiscalyear'].browse(vals['fiscalyear_id'])
            vals['name'] = company_id.name + " / " + period_id.name + ' ' + fiscalyear_id.name

        vals = self.get_data_account_closing(vals)
        res = super(AccountClosing,self).create(vals)
        return res

    @api.multi
    def get_data_account_closing(self,vals):
        if not vals.get('closing_detail_ids'):
            vals['closing_detail_ids'] = []
            data = self.get_data(vals)
            ress = self.get_account_lines(data['form'],vals['company_id'])
            i = 1
            for x in ress:
                vals['closing_detail_ids'].append((0, 0, {
                    'account_id': x['account_id'],
                    'debit': x['debit'],
                    'credit': x['credit'],
                    'balance': x['balance'],
                    'options': '0',
                    'sequence': i
                }))
                i += 1

        if not vals.get('full_closing_detail_ids'):
            vals['full_closing_detail_ids'] = []
            date_start = self.get_date_first_year(vals['date_from'])
            vals['date_from_first_year'] = date_start
            vals['date_to_first_year'] = vals['date_to']
            data = self.get_data(vals, first_year=True)
            ress = self.get_account_lines(data['form'],vals['company_id'])
            #####Initial Balance From Prev Year
            year = self.env['account.fiscalyear'].browse(vals.get('fiscalyear_id'))
            prev_year = int(year.name) - 1
            last_year_period_name = '12/' + str(prev_year)
            last_year_period = self.env['account.period'].search([('code', '=', last_year_period_name)])
            #raise UserError(_(last_year_period))
            i = 1
            for x in ress:
                account = self.env['account.account'].browse(x['account_id'])
                debit = x['debit']
                credit = x['credit']
                balance = x['balance']

                if account.user_type_id.id not in (14,16) and last_year_period:
                    init = self.get_init_balance(last_year_period.id, account.id, vals['company_id'])
                    debit = x['debit'] + init[0]
                    credit = x['credit'] + init[1]
                    balance = x['balance'] + init[2]

                vals['full_closing_detail_ids'].append((0, 0, {
                    'account_id': x['account_id'],
                    'debit': debit,
                    'credit': credit,
                    'balance': balance,
                    'options': '1',
                    'sequence': i
                }))
                i += 1
        return vals

    @api.multi
    def get_date_first_year(self,date_start):
        first_day_of_year = datetime.strptime(date_start,'%Y-%m-%d').replace(month=1, day=1)
        return first_day_of_year

    @api.multi
    def get_data(self,vals,first_year=False):
        data = {}
        journal_ids                     = self.env['account.journal'].search([])
        data['ids']                     = self.env.context.get('active_ids', [])
        data['model']                   = self.env.context.get('active_model', 'ir.ui.menu')
        data['form']                    = {}
        data['form']['date_from']       = vals['date_from'] if not first_year else vals['date_from_first_year']
        data['form']['date_to']         = vals['date_to'] if not first_year else vals['date_to_first_year']
        data['form']['company_id']      = vals['company_id']
        data['form']['target_move']     = 'posted'
        data['form']['journal_ids']     = [x.id for x in journal_ids]
        used_context                    = self._build_contexts(data)
        data['form']['used_context']    = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return data

    def _build_contexts(self, data):
        result = {}
        result['journal_ids']   = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state']         = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from']     = data['form']['date_from'] or False
        result['date_to']       = data['form']['date_to'] or False
        result['strict_range']  = True if result['date_from'] else False
        result['company_id']    = 'company_id' in data['form'] and data['form']['company_id'] or False
        return result

    def _compute_account_balance(self, accounts):
        """ compute the balance, debit and credit for the provided accounts
        """
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

    def _compute_report_balance(self,company_id):
        account_ids = self.env['account.account'].search([('company_id', '=',company_id)])
        res = {}
        fields = ['credit', 'debit', 'balance']
        res[1] = dict((fn, 0.0) for fn in fields)
        res[1]['account'] = self._compute_account_balance(account_ids)
        for value in res[1]['account'].values():
            for field in fields:
                res[1][field] += value.get(field)
        return res

    def get_account_lines(self, data,company_id):
        lines = []
        res = self.with_context(data.get('used_context'))._compute_report_balance(company_id)
        for account_id, value in res[1]['account'].items():
            account = self.env['account.account'].browse(account_id)
            vals = {
                'account_id': account.id,
                'balance'   : value['balance'] or 0.0,
                'debit'     : value['debit'],
                'credit'    : value['credit'],
                'code'      : account.code,
            }
            lines.append(vals)
        lines = sorted(lines, key=lambda lines: lines['code'])
        return lines

    @api.multi
    def action_close(self):
        mode = 'done'
        self._cr.execute('update account_closing set state=%s where id in %s', (mode, tuple(self._ids),))
        vals = {}
        vals['date_from']  = self.date_from
        vals['date_to']    = self.date_to
        vals['company_id'] = self.company_id.id
        vals['period_id'] = self.period_id.id
        vals['fiscalyear_id'] = self.fiscalyear_id.id
        vals = self.get_data_account_closing(vals)
        self.write(vals)
        self.invalidate_cache()
        return True

    @api.multi
    def action_cancel(self):
        mode = 'cancel'
        self._cr.execute('update account_closing set state=%s where id in %s', (mode, tuple(self._ids),))
        self.write({'closing_detail_ids':[],'full_closing_detail_ids':[]})
        self.invalidate_cache()
        return True

    @api.multi
    def action_open(self):
        mode = 'draft'
        self._cr.execute('update account_closing set state=%s where id in %s', (mode, tuple(self._ids),))
        self.write({'closing_detail_ids':[],'full_closing_detail_ids':[]})
        self.invalidate_cache()
        return True

    @api.multi
    def unlink(self):
        for x in self:
            if x.state == 'closed' :
                raise Warning('Tidak dapat menghapus data closing !')
        return super(AccountClosing,self).unlink()

    @api.multi
    def get_init_balance(self, period_id, account_id, company_id):
        cursor = self.env.cr
        debit = 0
        credit = 0
        balance = 0
        cursor.execute("""
                        select
                            b.debit as debit, b.credit as credit, b.balance as balance
                        from
                             account_closing as a,
                             account_closing_detail as b
                        where
                             a.id = b.closing_id and
                             b.options = '1' and
                             a.period_id = %s and
                             b.account_id = %s and
                             a.company_id = %s and
                             a.is_consolidation = False
                      """,(period_id, account_id, company_id))
        val = cursor.fetchone()
        if val[0] or val[0] != 0:
            debit = val[0]
        if val[1] or val[1] != 0:
            credit = val[1]
        if val[2] or val[2] != 0:
            balance = val[2]

        return [debit, credit, balance]

class AccountClosingDetail(models.Model):
    _name           = 'account.closing.detail'
    _description    = 'Account Closing Detail'
    _order          = 'sequence asc'

    closing_id          = fields.Many2one('account.closing',string='Closing Period',ondelete='cascade')
    account_id          = fields.Many2one('account.account',string='Account',ondelete='cascade')
    debit               = fields.Float(string='Debit')
    credit              = fields.Float(string='Credit')
    balance             = fields.Float(string='Balance')
    options             = fields.Selection([('0','Only This Month'),
                                            ('1','From 1st day of The Year')
                                            ],string='Options')
    sequence            = fields.Integer('No')






