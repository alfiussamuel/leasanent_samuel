{
	"name": "Buku Kas dan Bank",
	"version": "10.1",
	"author": "Anna Qahhariana",
	"category": "Report",
	"description": """\
        This module provides mutation of Cash and Bank Account
    """,
    "depends"       : [
     
        'account',
        'adh_precast_keuangan'
    ],
	"data": [
		'views/buku_kasbank.xml',
		
	],
	"installable": True,
	"auto_install": False,
    "application": True,
}
