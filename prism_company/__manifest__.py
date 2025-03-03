{
    'name': 'PRISM Company',
    'version': '1.0',
    'category': 'PRISM/Company',
    'summary': 'Company management for PRISM ERP',
    'description': """
PRISM Company Module
=================
This module extends the company model with Moroccan-specific fields and functionality.
It provides:
- Additional legal information fields (ICE, RC, CNSS numbers)
- Business classification (SME, exporter, free zone)
- Tax exemption information
- Fiscal year and accounting settings
- Social media information
    """,
    'author': 'Numexia',
    'website': 'https://dev.numexia.com',
    'depends': ['prism_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
