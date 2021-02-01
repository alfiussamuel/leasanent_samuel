{
    'name' : 'Report Packing List PDF',
    'version' : '10',    
    'category': 'Custom',    
    'author' :'Alif Darari Firdaus',        
    'depends' : ['v10_lea'],
    'data': [  
        'views/packing_list_generate_qweb.xml',
        'report/report_packing_list_qweb.xml',         
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
