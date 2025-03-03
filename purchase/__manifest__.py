{
    'name': 'PRISM Purchase',
    'version': '1.0',
    'category': 'PRISM/Purchase',
    'summary': 'Purchase management for PRISM ERP',
    'description': """
PRISM Purchase Module
=================
This module extends the purchase functionality with Moroccan-specific fields and features.
It provides:
- Order type classification (standard, import, free zone, government)
- VAT reverse charge management
- Delivery terms and shipping methods
- Import and customs management
- Approval workflow for high-value and import orders
- Multi-currency support with MAD conversion
- Enhanced reporting capabilities
    """,
    'author': 'Numexia',
    'website': 'https://dev.numexia.com',
    'depends': ['base', 'purchase', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
