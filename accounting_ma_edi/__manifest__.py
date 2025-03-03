{
    'name': 'Morocco DGI EDI Integration',
    'version': '1.0',
    'category': 'Accounting/Localizations/EDI',
    'summary': 'Electronic filing of tax declarations for Morocco',
    'description': """
Morocco DGI EDI Integration
===========================
This module allows you to generate and send tax declarations to the Moroccan tax authorities (DGI)
in EDI format as required by law.

Supported declarations:
- TVA Retenue à la Source (SIMPL-TVA)
- Traitements et Salaires (SIMPL-IR)
- IS (SIMPL-IS)
    """,
    'author': 'PRISM ERP Team',
    'website': 'https://www.prism-erp.com',
    'depends': ['accounting', 'hr', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/tva_teledeclaration_views.xml',
        'views/ir_salary_declaration_views.xml',
        'views/simplis_declaration_views.xml',
        'views/edi_declaration_views.xml',
        'wizards/simplis_generate_xml_wizard_views.xml',
        'data/tva_teledeclaration_data.xml',
        'data/dgi_commune_data.xml',
    ],
    'external_dependencies': {
        'python': ['lxml'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
