# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, api, models,_

class account_period_close(models.TransientModel):
    """
        close period
    """
    _name        = "account.period.close"
    _description = "period close"

    sure = fields.Boolean('Check this box')

    @api.multi
    def data_save(self):
        for form in self.read():
            if form['sure']:
                periods = self.env['account.period'].browse(self._context['active_ids'])
                for period in periods:
                    period.action_close()
        return {'type': 'ir.actions.act_window_close'}
