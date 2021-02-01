{
    'name' : 'Report Replenishment PDF',
    'version' : '10',    
    'category': 'Custom',    
    'author' :'HajiYp',        
    'depends' : ['v10_lea','report_qweb_element_page_visibility'],
    'data': [                    
        'view/report_replenishment.xml',
        'report/report_template_replenishment.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
