# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name' : 'Customer Credit Limit',
    'version' : '10.0.0.1',    
    'summary' : 'This apps help to Manage credit limit of your customers',
    'description': """ This openerp module show credit limit on partner, Account receivable amount agaist credit limit, Partner credit limit Warning, customer credit limit Warning, Total Account Receivable amount on sale. AR on sales,Partner AR agaist credit limit, ovedue warning, customer warning , customer credit warning,Customer Credit limit Warning on Sales, Sales Credit Warning Against AR.Payment credit warning, Account limit warning, Client overdemand warning, Client overlimit warning.
    Customer Credit limit, credit limit of customer,customer credit approval, partner credit limit, credit limit on customer, credit limit on partner, customer credit account, customer credit limit agiast account,customer account credit limit, credit limit on customer cart
    """,
    'category' : 'Sales',
    'price': '20',
    'currency': "EUR",
    'author' : 'Browseinfo',
    'website' : 'www.browseinfo.in',
    'depends' : ['base', 'sale'],
    'data' : [
                #'views/view_credit_limit.xml',
                'wizard/wizard_credit_limit.xml',
                'edi/customer_credit_limit_mail.xml'
              ],
    
    'demo' : '',
    
    'installable' : True,
    "images":['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
