# -*- coding: utf-8 -*-
{
    'name': 'PRISM Tax Management',
    'version': '1.0',
    'category': 'Accounting/Taxes',
    'summary': 'Manage tax types, rates, exemptions, declarations, and reports',
    'description': """
PRISM Tax Management
=============
This module provides a comprehensive tax management system for Odoo, with a focus on Moroccan tax requirements.

Features:
---------
* Tax Types: Define different types of taxes (VAT, Corporate Tax, Income Tax, etc.)
* Tax Rates: Configure rates for each tax type with validity periods
* Tax Exemptions: Manage tax exemptions with legal references
* Tax Declarations: Generate and submit tax declarations to authorities
* Tax Reports: Create various tax reports for analysis and compliance

Moroccan Specific Features:
--------------------------
* Predefined Moroccan tax types and rates
* Support for Moroccan tax declarations (TVA, IS, IR, etc.)
* Integration with Moroccan tax authority requirements
    """,
    'author': 'PRISM ERP',
    'website': 'https://www.prism-erp.com',
    'depends': [
        'prism_core',
        'prism_accounting',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/tax_type_data.xml',
        'data/tax_rate_data.xml',
        'views/tax_type_views.xml',
        'views/tax_rate_views.xml',
        'views/tax_exemption_views.xml',
        'views/tax_declaration_views.xml',
        'views/tax_report_views.xml',
        'views/tax_menuitem.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
