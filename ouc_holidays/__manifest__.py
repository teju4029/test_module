{
    'name': 'HR Public Holidays',
    'version': '10.0.1.0.0',
    'category': 'hr holidays',
    'author': "OpenERP4You",
    'summary': "Manage Public and Rest days Holidays",
    'depends': [
        'hr',
        'hr_holidays',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_public_holidays_view.xml',
        'views/rest_days_view.xml'
    ],
    'demo': [],
    'test': [],
    'application':True,
    'installable': True,
    'auto_install': False,
}
