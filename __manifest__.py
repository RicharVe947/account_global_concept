# -*- coding: utf-8 -*-

{
    'name': "Account Global Concept",
    'summary': """Account Global Concept""",
    'description': """Generación de facturas con concepto global""",
    'author': "Munin",
    'category': 'account',
    'version': '1.0.0',
    'depends': ['sale_order_line_menu', 'account'],
    'data': [
        'data/ir_actions.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
        'wizard/sale_advance_payment_inv.xml',
    ],
    'installable': True,
    'License': 'LGPL-3',
}
