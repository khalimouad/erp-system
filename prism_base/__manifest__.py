{
    'name': 'PRISM Base',
    'version': '1.0',
    'category': 'PRISM/Base',
    'summary': 'Base module for PRISM ERP',
    'description': """
PRISM Base Module
================
This module serves as the foundation for the PRISM ERP system.
It provides common functionality and configurations used by other PRISM modules.
    """,
    'author': 'Numexia',
    'website': 'https://dev.numexia.com',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
}
