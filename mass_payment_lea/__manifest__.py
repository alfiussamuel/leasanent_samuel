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
{
    'name': 'Mass Payments',
    'version': '1.0',
    'category': 'Accounting',
    'description': """User can do mass payments to venders and receive payments from customers.""",
    'summary': 'User can do mass payments to venders and receive payments from customers.',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'depends': ['base', 'account', 'account_accountant','efaktur'],
    'price': 30,
    'currency': 'EUR',
    'data': [
        'security/ir.model.access.csv',
        'report.xml',
        'data.xml',
        'report/report_mass_payment.xml',
        'views/account_payment_view.xml',
        'views/mass_payment_view.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
