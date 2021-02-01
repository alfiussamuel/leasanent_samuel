# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': 'POS Reports',
    'category': 'Point of Sale',
    'summary': 'Allow user to print X-Report, Z-Report and Sales Summary report.',
    'description': """
Allow user to print X-Report, Z-Report and Sales Summary report.
""",
    'author': "Acespritech Solutions Pvt. Ltd.",
    'website': "http://www.acespritech.com",
    'price': 60.00, 
    'currency': 'EUR',
    'version': '1.0',
    'depends': ['point_of_sale', 'base'],
    'images': ['static/description/main_screenshot.png'],
    'data': [
        'reports.xml',
        'views/aspl_pos_report.xml',
        'views/pos_sales_report_template.xml',
        'views/pos_sales_report_pdf_template.xml',
        'views/sales_details_pdf_template.xml',
        'views/sales_details_template.xml',
        'views/front_sales_report_pdf_template.xml',
        'views/front_sales_thermal_report_template.xml',
        'wizard/wizard_pos_sale_report_view.xml',
        'wizard/wizard_sales_details_view.xml',
        'wizard/wizard_pos_x_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
