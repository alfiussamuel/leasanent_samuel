# -*- coding: utf-8 -*-
#╔══════════════════════════════════════════════════════════════════╗
#║                                                                  ║
#║                ╔═══╦╗       ╔╗  ╔╗     ╔═══╦═══╗                 ║
#║                ║╔═╗║║       ║║ ╔╝╚╗    ║╔═╗║╔═╗║                 ║
#║                ║║ ║║║╔╗╔╦╦══╣╚═╬╗╔╬╗ ╔╗║║ ╚╣╚══╗                 ║
#║                ║╚═╝║║║╚╝╠╣╔╗║╔╗║║║║║ ║║║║ ╔╬══╗║                 ║
#║                ║╔═╗║╚╣║║║║╚╝║║║║║╚╣╚═╝║║╚═╝║╚═╝║                 ║
#║                ╚╝ ╚╩═╩╩╩╩╩═╗╠╝╚╝╚═╩═╗╔╝╚═══╩═══╝                 ║
#║                          ╔═╝║     ╔═╝║                           ║
#║                          ╚══╝     ╚══╝                           ║
#║ SOFTWARE DEVELOPED AND SUPPORTED BY ALMIGHTY CONSULTING SERVICES ║
#║                   COPYRIGHT (C) 2016 - TODAY                     ║
#║                   http://www.almightycs.com                      ║
#║                                                                  ║
#╚══════════════════════════════════════════════════════════════════╝
{
    'name': 'Merge Mutiple Invoices',
    'summary': """Allow your users to Merge Mutiple Invoices.""",
    'description': """
        Allow your users to Merge Mutiple Invoices
        merge invoice invoices mergeing invoice mergeing merge invoices merging invoice merging invoices
    """,
    'version': '1.0.1',
    'category': 'Accounting',
    'author': 'Almighty Consulting Services',
    'website': 'http://www.almightycs.com',
    'depends': ["account"],
    'data' : [
        'wizard/merge_wizard_view.xml',
    ],
    'images': [
        'static/description/acs_merge_invoice_almightycs_cover.jpg',
    ],
    'installable': True,
    'sequence': 1,
    'price': 20,
    'currency': 'EUR',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: