# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
# You should have received a copy of the License along with this program.
#################################################################################

from openerp import api, models
from datetime import datetime, date, time


class report_mass_payment(models.AbstractModel):
    _name = 'report.mass_payment.report_mass_payment_temp'

    def _get_payment_list(self, data):
        payment_list = []
        for each_payment in data.account_payment_ids:
            payment_list.append({'payment_date': each_payment.payment_date,
                                   'invoice_number': each_payment.invoice_id and each_payment.invoice_id.number and each_payment.invoice_id.number or False,
                                   'name': each_payment.name and each_payment.name and each_payment.name or False,
                                   'journal_id': each_payment.journal_id.name and each_payment.journal_id.name and each_payment.journal_id.name or False,
                                   'partner_id': each_payment.partner_id.name and each_payment.partner_id.name  or False,
                                   'amount': each_payment.amount and each_payment.amount or False,
                                   'state': each_payment.state or False})
        return payment_list

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('mass_payment.report_mass_payment_temp')
        docargs = {
            'doc_ids': self.env['mass.payment'].browse(docids),
            'doc_model': report.model,
            'docs': self,
            'data':data,
            'get_payment_list' : self._get_payment_list,
        }
        return report_obj.render('mass_payment.report_mass_payment_temp', docargs)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: