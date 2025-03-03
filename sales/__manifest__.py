{
    'name': 'PRISM Sales',
    'version': '1.0',
    'category': 'PRISM/Sales',
    'summary': 'Sales management for PRISM ERP',
    'description': """
PRISM Sales Module
=================
This module extends the sales functionality with Moroccan-specific fields and features.
It provides:
- Order type classification (standard, export, free zone, government)
- Bon de Livraison (BL) workflow for Moroccan delivery notes
- End-of-month invoicing based on BLs
- VAT exemption management
- Delivery terms and shipping methods
- Approval workflow for high-value and export orders
- Multi-currency support with MAD conversion
- Enhanced reporting capabilities
    """,
    'author': 'Numexia',
    'website': 'https://dev.numexia.com',
    'depends': ['base', 'sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_views.xml',
        'report/bon_de_livraison_report.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
