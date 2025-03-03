{
    'name': 'PRISM Product',
    'version': '1.0',
    'category': 'PRISM/Product',
    'summary': 'Product management for PRISM ERP',
    'description': """
PRISM Product Module
=================
This module extends the product models with Moroccan-specific fields and functionality.
It provides:
- VAT rate management for products (20%, 14%, 10%, 7%, 0%)
- Enhanced product classification
- Improved inventory management
- Accounting integration
- Custom views (form, kanban, list)
    """,
    'author': 'Numexia',
    'website': 'https://dev.numexia.com',
    'depends': ['prism_core', 'product', 'uom', 'prism_accounting'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
