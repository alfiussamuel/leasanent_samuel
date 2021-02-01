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

{
    'name': 'POS Promotional Scheme',
    'version': '1.0.1',
    'category': 'Point Of Sale',
    'sequence': 6,
    'summary': 'Touch-screen Interface for Shops',
    'description': """
This module shows the basic processes involved in the selected modules and in the sequence they occur.
======================================================================================================

**Note:** This applies to the modules containing modulename_process.xml.

**e.g.** product/process/product_process.xml.

    """,
    'author' : 'Pragmatic TechSoft Pvt Ltd.',
    'website': 'www.pragtech.co.in',
    'depends': ['point_of_sale'],
    'data': [
             'security/ir.model.access.csv',
             'views/scheme_view.xml',
             'views/templates.xml',
             ],
    'qweb': [
            'static/src/xml/pos.xml',
             ],
    'price':500,
    'currency':'EUR',
    'license': 'OPL-1',
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}

