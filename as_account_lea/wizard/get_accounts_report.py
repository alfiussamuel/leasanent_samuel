# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class AccountOnlyCreateAccount(models.TransientModel):
    _name = "account.only.create.account"    

    @api.multi
    def create_account(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['account.account.only'].browse(active_ids):            
            record.button_create_account()
        return {'type': 'ir.actions.act_window_close'}
