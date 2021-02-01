from odoo import fields, api, models,_
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning

class AcccountInvoice(models.Model) :
    _inherit = 'account.invoice'

    @api.onchange('partner_id','company_id')
    def _onchange_partner_id(self):
        res = super(AcccountInvoice,self)._onchange_partner_id()
        account_id = False
        company_id = self.company_id.id
        p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
        type = self.type
        if p:
            rec_account = p.property_account_only_receivable_id
            pay_account = p.property_account_only_payable_id

            account = self.env['account.account']
            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _(
                    'Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('out_invoice', 'out_refund'):
                rec_account = account.search([('account_only_id','=',rec_account.id),('company_id','=',company_id)])
                if not rec_account :
                    raise Warning('Cannot find Receivable Account for selectable partner, You should configure it.')
                elif len(rec_account) > 1 :
                    raise Warning('Found more than one corresponding receivable account, please fix it before continue.')
                account_id = rec_account.id
            else:
                pay_account = account.search([('account_only_id', '=', pay_account.id), ('company_id', '=', company_id)])
                if not rec_account:
                    raise Warning('Cannot find Payable Account for selectable partner, You should configure it.')
                elif len(rec_account) > 1:
                    raise Warning(
                        'Found more than one corresponding payable account, please fix it before continue.')
                account_id = pay_account.id
        self.account_id = account_id
        return res
