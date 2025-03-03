{
    'name': 'PRISM Core',
    'version': '1.0',
    'category': 'PRISM/Core',
    'summary': 'Core module for PRISM ERP with Moroccan-specific features',
    'description': """
PRISM Core Module
================
This module serves as the foundation for the PRISM ERP system.
It provides common functionality and configurations used by other PRISM modules,
with specific extensions for Moroccan business requirements.
    """,
    'author': 'Numexia',
    'website': 'https://dev.numexia.com',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Add CSS and JS files here
        ],
        'web.assets_frontend': [
            # Add CSS and JS files here
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
    'license': 'LGPL-3',
}
