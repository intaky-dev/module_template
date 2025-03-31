{
    'name': 'My Module',
    'version': '1.0.0',
    'summary': 'A clean Odoo module template.',
    'author': 'Your Name',
    'website': 'https://github.com/yourname',
    'category': 'Tools',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/my_model_views.xml',
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
