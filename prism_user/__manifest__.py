{
    'name': 'PRISM User Management',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'User management with Moroccan-specific roles and approval workflows',
    'description': """
PRISM User Management
====================

This module extends the standard Odoo user management with Moroccan-specific features:

* User roles specific to Moroccan business contexts
* User approval workflows
* Enhanced security features
* Role-based access control
* User activity tracking
* Compliance with Moroccan regulations
    """,
    'author': 'PRISM Team',
    'website': 'https://www.prism-erp.com',
    'depends': [
        'prism_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/user_role_views.xml',
        'views/user_approval_views.xml',
        'views/user_menuitem.xml',
        'data/user_role_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
