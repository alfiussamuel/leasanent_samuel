from odoo import api, fields, models, _

class AccountAccount(models.Model) :
    _inherit = 'account.account'

    account_only_id = fields.Many2one('account.account.only',string='Account Only')
    
    