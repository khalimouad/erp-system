# PRISM ERP System

## Overview

PRISM ERP is a comprehensive Enterprise Resource Planning system designed specifically for the Moroccan market. It extends Odoo 18 with features and functionality that ensure compliance with Moroccan regulations and business practices.

## Key Features

- **Moroccan Compliance**: Built from the ground up to comply with Moroccan tax, accounting, and business regulations
- **Multi-language Support**: Available in French, Arabic, and English
- **Comprehensive Modules**: Covers all aspects of business operations including inventory, sales, purchases, accounting, and more
- **Customizable**: Easily adaptable to specific business needs
- **Modern Interface**: User-friendly interface designed for efficiency and ease of use

## Modules

### Core Modules

- **PRISM Core**: Core functionality and system-wide settings with Moroccan-specific extensions
- **PRISM Theme**: Custom PRISM theme with Moroccan design elements
- **PRISM Company**: Company management with Moroccan-specific fields
- **PRISM User**: User management with role-based access control

### Business Modules

- **PRISM Partner**: Customer and vendor management with Moroccan tax ID validation
- **PRISM Product**: Product management with Moroccan-specific categorization
- **PRISM Inventory**: Comprehensive inventory management with customs, temperature control, and lot tracking
- **PRISM Sales**: Sales order management with Moroccan tax calculations
- **PRISM Purchase**: Purchase order management with Moroccan tax calculations

### Financial Modules

- **PRISM Accounting**: Accounting system with Moroccan chart of accounts
- **PRISM Tax**: Tax management with Moroccan tax rules
- **PRISM Payroll**: Payroll management with Moroccan labor laws

## Project Structure

The project follows a modular structure, with each module having its own directory:

```
erp-system/
├── prism_core/            # Core functionality and system-wide settings
├── prism_theme/           # PRISM theme
├── prism_company/         # Company management
├── prism_partner/         # Partner management
├── prism_product/         # Product management
├── prism_inventory/       # Inventory management
├── prism_sales/           # Sales management
├── prism_purchase/        # Purchase management
├── prism_accounting/      # Accounting management
├── prism_tax/             # Tax management
├── prism_payroll/         # Payroll management
├── prism_user/            # User management
└── README.md              # This file
```

Each module follows a standard Odoo module structure:

```
module_name/
├── __init__.py            # Python package initialization
├── __manifest__.py        # Module manifest
├── data/                  # Data files
├── models/                # Model definitions
├── security/              # Security files
├── static/                # Static assets
│   ├── description/       # Module description
│   └── src/               # Source files (JS, CSS, etc.)
└── views/                 # View definitions
```

## Installation

### Prerequisites

- Odoo 18
- PostgreSQL 14 or higher
- Python 3.10 or higher

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/numexia/prism-erp.git
   ```

2. Add the repository path to your Odoo addons path:
   ```bash
   # In your Odoo configuration file (odoo.conf)
   addons_path = /path/to/odoo/addons,/path/to/prism-erp
   ```

3. Update the module list in Odoo:
   - Go to Apps menu
   - Click on "Update Apps List"
   - Click on "Update"

4. Install the required modules:
   - Go to Apps menu
   - Search for "PRISM"
   - Install the modules you need

## Development

### Setting Up Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Development Guidelines

- Follow the [Odoo Guidelines](https://www.odoo.com/documentation/18.0/developer/reference/guidelines.html)
- Use meaningful commit messages
- Write tests for new features
- Document your code
- Keep backward compatibility in mind

## Documentation

- [Project Status](PRISM_ERP_STATUS.md): Current development status
- [Implementation Roadmap](PRISM_ERP_ROADMAP.md): Detailed implementation plan
- [User Manual](docs/user_manual.md): User documentation (coming soon)
- [Developer Guide](docs/developer_guide.md): Developer documentation (coming soon)

## License

This project is licensed under the LGPL-3 License - see the LICENSE file for details.

## Contact

For more information, please contact:

- **Email**: info@numexia.com
- **Website**: https://dev.numexia.com
