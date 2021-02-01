from odoo import fields, api, models

class ClosePeriod(models.TransientModel):
    _name           = 'close.period'
    _description    = 'Close Period'

    fiscalyear_id   = fields.Many2one('account.fiscalyear', string='Fiscal Year')
    period_id       = fields.Many2one('account.period', string='Period')
    company_id      = fields.Many2one('res.company', string='Company',  default=lambda self: self.env.user.company_id)

    @api.multi
    def close_period(self):
        for x in self :
            account_closing_id = x.create_account_closing()
            return x.return_to_form(account_closing_id)

    @api.multi
    def create_account_closing(self):
        account_closing_id = self.env['account.closing'].create({'period_id':self.period_id.id,
                                                                 'fiscalyear_id':self.fiscalyear_id.id,
                                                                 'company_id':self.company_id.id,
                                                                 'date_from':self.period_id.date_start,
                                                                 'date_to':self.period_id.date_stop,
                                                                 'state':'done'
                                                                })
        return account_closing_id

    @api.multi
    def return_to_form(self,account_closing_id):
        imd             = self.env['ir.model.data']
        action          = imd.xmlid_to_object('as_account_closing.action_account_closing')
        form_view_id    = imd.xmlid_to_res_id('as_account_closing.view_account_closing_form')

        result = {
            'name'      : action.name,
            'help'      : action.help,
            'type'      : action.type,
            'views'     : [(form_view_id, 'form')],
            'target'    : action.target,
            'context'   : self._context,
            'res_model' : action.res_model,
            'res_id'    : account_closing_id.id
        }
        return result

    @api.onchange('company_id')
    def onchange_company(self):
        dom = {}
        dom['company_id'] =[('id','child_of',[self.env.user.company_id.id])]
        return {'domain':dom}
