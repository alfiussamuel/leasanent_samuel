# -*- coding: utf-8 -*-

{
    'name': 'Pos order operations',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'WebVeer',
    'summary': "Pos order operation module allows you to reprint the receipt by posbox thermal printer and normal printer, reorder and order return." ,
    'description': """

=======================

Pos order operation module allows you to reprint the receipt by posbox thermal printer and normal printer, reorder and order return.

""",
    'depends': ['point_of_sale'],
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'report/point_of_sale_report.xml',
        'report/report_receipt.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/butt.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 49,
    'currency': 'EUR',
}
