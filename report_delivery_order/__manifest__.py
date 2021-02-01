{
    'name' : 'Report Delivery Order PDF',
    'version' : '10',    
    'category': 'Custom',    
    'author' :'Hajiyanto Prakoso',        
    'depends' : ['v10_lea'],
    'data': [  
        'views/delivery_order_qweb.xml',
        'report/report_delivery_order_lea.xml',         
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
