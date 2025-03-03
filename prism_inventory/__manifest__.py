{
    'name': 'PRISM Inventory',
    'version': '1.0',
    'category': 'PRISM/Inventory',
    'summary': 'Inventory management for PRISM ERP',
    'description': """
PRISM Inventory Module
=================
This module extends the inventory functionality with Moroccan-specific fields and features.
It provides:
- Warehouse type classification (standard, bonded, free zone, transit)
- Location type classification (standard, customs, quarantine, temperature, hazardous, valuable)
- Lot/serial tracking with origin, expiry, and quality control
- Customs management for imports
- Temperature and humidity control
- Approval workflows for sensitive operations
- Enhanced inventory reporting
    """,
    'author': 'Numexia',
    'website': 'https://dev.numexia.com',
    'depends': ['prism_core', 'stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_data.xml',
        'views/stock_type_views.xml',
        'views/stock_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
