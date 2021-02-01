{
	"name": "Account Report Format For LEA SANENT",
	"version": "10.1",
	"author": "Anna Qahhariana",
	"category": "Report",
	"description": """
	This module provides report accounting such as General Ledger, Profit Loss, and Balance Sheet
    """,
    "depends"       : [
        'account','as_account_lea','as_account_closing_lea',
    ],
	"data": [
		'view/account_transaction.xml',
        'report/report_pengeluaran_biaya.xml',
        'report/report_vendor_bill.xml',
	],
	"installable": True,
	"auto_install": False,
    "application": True,
}
