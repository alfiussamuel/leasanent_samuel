{
    'name' : 'Report Putaway PDF',
    'version' : '10',    
    'category': 'Custom',    
    'author' :'APR',        
    'depends' : ['v10_lea','report_qweb_element_page_visibility'],
    'data': [                    
        'views/report_type_xlsx.xml',
        'report/report_putaway_qweb.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
