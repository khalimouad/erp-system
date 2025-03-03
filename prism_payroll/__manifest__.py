# -*- coding: utf-8 -*-
{
    'name': 'PRISM Moroccan Payroll',
    'version': '1.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Moroccan Payroll Management',
    'description': """
PRISM Moroccan Payroll Management
===========================

This module extends Odoo's payroll functionality to support Moroccan payroll requirements:

* CNSS (Social Security) calculations
* AMO (Health Insurance) calculations
* IR (Income Tax) calculations according to Moroccan tax brackets
* Seniority bonuses according to Moroccan labor law
* Professional expenses deductions
* Family charges deductions
* Moroccan-specific payslip report
* Integration with accounting for automatic journal entries

Key Features:
------------
* Complete implementation of Moroccan payroll rules
* Configurable parameters for rates and thresholds
* Automatic calculation of all mandatory deductions
* Detailed payslip with all Moroccan-specific fields
* Support for various allowances and bonuses
* Employee management with all required Moroccan fields
* Contract management with Moroccan-specific terms
* Reporting for tax and social security declarations
    """,
    'author': 'PRISM ERP',
    'website': 'https://www.prism-erp.com',
    'depends': [
        'prism_core',
        'hr',
        'hr_payroll',
        'hr_contract',
        'hr_holidays',
        'hr_holidays_public',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',
        'data/hr_payroll_maroc_data.xml',
        'views/hr_payroll_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_payroll_maroc_views.xml',
        'reports/payslip_report.xml',
        'reports/bulletin_paie_template.xml',
        'reports/bulletin_paie_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
