{
	"name": "Sales Report Format For LEA SANENT",
	"version": "10.1",
	"author": "Anna Qahhariana",
	"category": "Report",
	"description": """
	This module provides report sales based on PT. Lea Sanent format
    """,
    "depends"       : [
        'account','as_account_lea','v10_lea','efaktur','point_of_sale','purchase'
    ],
	"data": [
		'view/invoice.xml',
		'view/sale.xml',
		'view/partner.xml',
		'wizard/sales_report.xml',
		'report/dashboard_sales_lea.xml',
		'report/dashboard_pos_lea.xml',


	],
	"installable": True,
	"auto_install": False,
    "application": True,
}
