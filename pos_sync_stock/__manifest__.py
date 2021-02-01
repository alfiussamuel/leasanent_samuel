{
    'name': "POS Stock",
    'version': '2.1',
    'category': 'Point of Sale',
    'author': 'TL Technology',
    'sequence': 0,
    'summary': 'POS Stock',
    'description': 'POS Stock',
    'depends': ['point_of_sale', 'stock', 'bus'],
    'data': [
        '__import__/template.xml',
        'view/pos_config.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'price': '100',
    'website': 'http://posodoo.com',
    'application': True,
    'images': ['static/description/icon.png'],
    'support': 'thanhchatvn@gmail.com',
    "currency": 'EUR',
}
