{
    'name': 'PRISM Partner',
    'version': '1.0',
    'category': 'PRISM/Partner',
    'summary': 'Partner management for PRISM ERP',
    'description': """
PRISM Partner Module
=================
This module extends the partner model with Moroccan-specific fields and functionality.
It provides:
- Partner type selection (customer, vendor, or both)
- Additional Moroccan-specific fields (ICE, RC, CNSS numbers)
- Enhanced contact information
- Payment and credit management
- Due and overdue invoice tracking
- Custom views (form, kanban, list)
    """,
    'author': 'Numexia',
    'website': 'https://dev.numexia.com',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
