from odoo import fields, api, models
from odoo.exceptions import Warning
from datetime import datetime
from dateutil.relativedelta import relativedelta

class AccountFiscalYear(models.Model):
    _name        = 'account.fiscalyear'
    _description = "Fiscal Year"
    _order       = "date_start, id desc"

    name                    = fields.Char('Fiscal Year', required=True,size=4)
    code                    = fields.Char('Code', size=6, required=True)
    date_start              = fields.Date('Start Date', required=True)
    date_stop               = fields.Date('End Date', required=True)
    period_ids              = fields.One2many('account.period', 'fiscalyear_id', 'Periods')
    state                   = fields.Selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False, default='draft')

    @api.multi
    def _check_duration(self):
        obj_fy = self
        if obj_fy.date_stop < obj_fy.date_start:
            return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe start date of a fiscal year must precede its end date.', ['date_start','date_stop'])
    ]

    @api.multi
    def create_period3(self):
        return self.create_period(interv=3)

    @api.multi
    def create_period(self,interv=None):
        if interv != 3 :
            interv = 1
        period_obj = self.env['account.period']
        for fy in self:
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interv, days=-1)
                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')
                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interv)
        return True

    @api.multi
    def unlink(self):
        for x in self :
            check = all(y.state != 'draft' for y in x.period_ids)
            if not check :
                raise Warning('Some periods already closed!')
        return super(AccountFiscalYear,self).unlink()
