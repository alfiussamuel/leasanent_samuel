# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAccountOnly(models.Model) :
    _name = 'account.account.only'
    _description = "Account Only"
    _order = "code"

    name                        = fields.Char(required=True, index=True)
    currency_id                 = fields.Many2one('res.currency', string='Account Currency',help="Forces all moves for this account to have this account currency.")
    code                        = fields.Char(size=64, required=True, index=True)
    deprecated                  = fields.Boolean(index=True, default=False)
    user_type_id                = fields.Many2one('account.account.type', string='Type', required=True, oldname="user_type",
                                    help="Account Type is used for information purpose, to generate country-specific legal reports, and set the rules to close a fiscal year and generate opening entries.")
    internal_type               = fields.Selection(related='user_type_id.type', string="Internal Type", store=True, readonly=True)
    last_time_entries_checked   = fields.Datetime(string='Latest Invoices & Payments Matching Date', readonly=True, copy=False,
                                    help='Last time the invoices & payments matching was performed on this account. It is set either if there\'s not at least '\
                                    'an unreconciled debit and an unreconciled credit Or if you click the "Done" button.')
    reconcile                   = fields.Boolean(string='Allow Reconciliation', default=False,
                                    help="Check this box if this account allows invoices & payments matching of journal items.")
    tax_ids                     = fields.Many2many('account.tax', 'account_account_only_tax_default_rel','account_id', 'tax_id', string='Default Taxes')
    note                        = fields.Text('Internal Notes')
    tag_ids                     = fields.Many2many('account.account.tag', 'account_account_account_only_tag', string='Tags', help="Optional tags you may want to assign for custom reporting")


    @api.multi
    def button_create_account(self):
        company_ids = self.env['res.company'].search([])        
        for res in self:
            for company in company_ids:                
                account_id = self.env['account.account'].search([('code', '=', res.code), ('company_id', '=', company.id)])
                if not account_id:
                    self.env['account.account'].create({
                                                        'name' : res.name,
                                                        'code' : res.code,
                                                        'user_type_id' : res.user_type_id.id,
                                                        'internal_type' : res.internal_type,
                                                        'reconcile' : res.reconcile,
                                                        'company_id' : company.id,
                                                        'account_only_id' : res.id                                                        
                                                        })
                elif account_id:
                    account_id[0].write({
                                       'account_only_id' : res.id   
                                       })

    @api.multi
    @api.depends('name','code')
    def name_get(self):
        result = []
        for account in self:
            name =  account.code + ' ' + account.name
            result.append((account.id, name))
        return result