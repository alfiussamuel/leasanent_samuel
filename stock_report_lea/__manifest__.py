{
	"name": "Stock Raw Data Report For LEA SANENT",
	"version": "10.1",
	"author": "Anna Qahhariana",
	"category": "Report",
	"description": """
	This module provides report raw data stock based on PT. Lea Sanent format
    """,
    "depends"       : [
        'stock','v10_lea','as_account_closing_lea','account'
    ],
	"data": [
		'view/closing_stock.xml',
		'view/picking.xml',
		'report/dashboard_quants.xml',
		'report/stock_report.xml',
        'report/delivery_order_sales.xml',
        'report/delivery_order_internal.xml',
		'wizard/generate_raw_data_stock.xml',
	],
	"installable": True,
	"auto_install": False,
    "application": True,
}
