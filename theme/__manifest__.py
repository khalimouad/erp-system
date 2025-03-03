{
    'name': 'PRISM Theme',
    'version': '1.0',
    'category': 'PRISM/Theme',
    'summary': 'Theme module for PRISM ERP',
    'description': """
PRISM Theme Module
================
This module customizes the appearance of Odoo to match the PRISM branding.
It includes custom CSS, JS, and XML templates to rebrand the system.
    """,
    'author': 'Numexia',
    'website': 'https://dev.numexia.com',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'theme/static/src/scss/backend.scss',
            'theme/static/src/js/prism_branding.js',
        ],
        'web.assets_frontend': [
            'theme/static/src/scss/frontend.scss',
        ],
        'web.login_layout': [
            'theme/static/src/scss/login.scss',
        ],
        'web.assets_common': [
            'theme/static/src/scss/common.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 2,
    'license': 'LGPL-3',
}
