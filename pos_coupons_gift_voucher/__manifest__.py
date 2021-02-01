# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    "name" : "POS Coupons Discount & Gift Vouchers",
    "version" : "10.0.0.1",
    "category" : "Point of Sale",
    "depends" : ['base','sale','point_of_sale'],
    "author": "BrowseInfo",
    "price": '39.00',
    "currency": 'EUR',
    'summary': 'Coupons/Discount/Gift Vouchers/Promo-code on point of sale.',
    "description": """
    
    Purpose :- 
Create Gift Vouchers/Coupons for discount on special occasions for grabbing more customers.
POS discount, Point of Sale Discount, POS Gift Vouchers, Point of Sale Gift Voucher, Point of sale Coupons
POS coupon code, point of sales coupon code, POS promo-code, Point of sale promocode, POS promocode, Point of sale promo-code, Point of sales Discount.Discount on POS, Disount on point of sales, Deducation on POS, POS deducation, Point of sale deduction, Gift Voucher on POS, Gift Voucher on Point of sales.
    """,
    "website" : "www.browseinfo.in",
    "data": [
        'security/ir.model.access.csv',
        'views/custom_pos_view.xml',
        'views/pos_gift_coupon.xml',
        'views/pos_gift_voucher_setting.xml',
        'views/pos_order_view.xml',
        'views/report_pos_gift_coupon.xml',
        'views/gift_coupon_report.xml'
    ],
    'qweb': [
        'static/src/xml/pos_coupons_gift_voucher.xml',
    ],
    "auto_install": False,
    "installable": True,
    "images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
