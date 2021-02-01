from odoo import fields, api, models


class AccountFinancialReport(models.Model):
    _inherit = 'account.financial.report'

    side = fields.Selection([('left', 'Left'), ('right', 'Right')], string='Side',
                            help="Used in account financial report horizontal", default='left')
    code_number = fields.Char('Code Number')
    company_id = fields.Many2one('res.company', 'Company')
    is_detail = fields.Boolean('Is Detail?')
    is_consolidation = fields.Boolean('Is Consolidation?', default=False)
    report_group = fields.Selection([('Balance Sheet', 'Balance Sheet'), ('Profit and Loss', 'Profit and Loss')],
                                    string='Report Group')
    balance_sheet_type = fields.Selection([('Aktiva', 'Aktiva'), ('Pasiva', 'Pasiva')], string='Balance Sheet Type')

class ResCompany(models.Model):
    _inherit     = "res.company"

    re_account_id  = fields.Many2one('account.account', string="Akun Saldo Awal berjalan")
    re_account_id2 = fields.Many2one('account.account', string="Akun Saldo Periode lalu")





