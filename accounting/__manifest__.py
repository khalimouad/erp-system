{
    'name': 'PRISM Accounting',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Moroccan-compliant accounting module for PRISM ERP',
    'description': """
PRISM Accounting
===============

This module provides a comprehensive accounting system that is compliant with Moroccan accounting standards.

Features:
---------
* Moroccan Chart of Accounts
* VAT management
* Corporate Tax (IS) management
* Income Tax (IR) management
* Multi-company support
* Multi-currency support
* Bank reconciliation
* Asset management
* Budget management
* Analytic accounting
* Financial reporting
* Tax reporting
* Fiscal year management
* Period management
* Journal management
* Invoice management
* Payment management
* Automatic reconciliation
* Bank statement import
* Fiscal position management
* Tax group management
* Account tag management
* Account type management
* Account template management
* Tax template management
* Journal template management
* Fiscal position template management
* Payment term management
* Payment method management
* Reconciliation model management
* Analytic account management
* Analytic tag management
* Budget management
* Asset management
* Fiscal year management
* Period management
* Invoice management
    """,
    'author': 'PRISM ERP Team',
    'website': 'https://www.prism-erp.com',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/account_menuitem.xml',
        'data/account_data.xml',
        'data/account_tax_data.xml',
        'data/account_chart_template_data.xml',
    ],
    'demo': [
        'demo/account_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
