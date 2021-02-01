from odoo import fields, api, models
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning

class AccountPeriod(models.Model):
    _name           = "account.period"
    _description    = "Account period"
    _order          = "date_start asc"

    name                    = fields.Char('Period Name', required=True)
    code                    = fields.Char('Code', size=12)
    date_start              = fields.Date('Start of Period', required=True, states={'done':[('readonly',True)]})
    date_stop               = fields.Date('End of Period', required=True, states={'done':[('readonly',True)]})
    fiscalyear_id           = fields.Many2one('account.fiscalyear', 'Fiscal Year', required=True, states={'done':[('readonly',True)]}, index=True,ondelete='cascade')
    state                   = fields.Selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False, default='draft',
                                        help='When monthly periods are created. The status is \'Draft\'. At the end of monthly period it is in \'Done\' status.')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The name of the period must be unique!'),
    ]

    @api.multi
    def _check_duration(self):
        obj_period = self
        if obj_period.date_stop < obj_period.date_start:
            return False
        return True

    @api.multi
    def _check_year_limit(self):
        for obj_period in self:
            if obj_period.fiscalyear_id.date_stop < obj_period.date_stop or \
               obj_period.fiscalyear_id.date_stop < obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_start or \
               obj_period.fiscalyear_id.date_start > obj_period.date_stop:
                return False

            pids = self.search([('date_stop','>=',obj_period.date_start),('date_start','<=',obj_period.date_stop),('id','<>',obj_period.id)])
            if pids:
                return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe duration of the Period(s) is/are invalid.', ['date_stop']),
        (_check_year_limit, 'Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.', ['date_stop'])
    ]

    @api.multi
    def action_draft(self):
        mode = 'draft'
        for period in self:
            if period.fiscalyear_id.state == 'done':
                raise Warning('You can not re-open a period which belongs to closed fiscal year')
        self._cr.execute('update account_period set state=%s where id in %s', (mode, tuple(self._ids),))
        self.invalidate_cache()
        return True

    @api.multi
    def action_close(self):
        mode = 'done'
        self._cr.execute('update account_period set state=%s where id in %s', (mode, tuple(self._ids),))
        self.invalidate_cache()
        return True
