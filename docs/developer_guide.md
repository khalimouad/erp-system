# PRISM ERP Developer Guide

*This document is under development and will be available soon.*

## Introduction

Welcome to the PRISM ERP Developer Guide. This comprehensive guide is designed to help developers understand the architecture, extend functionality, and contribute to the PRISM ERP system. PRISM ERP is built on top of Odoo 18 and is specifically tailored for the Moroccan market.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Coding Standards](#coding-standards)
4. [Module Development](#module-development)
5. [API Reference](#api-reference)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

The PRISM ERP system is built on top of Odoo 18 and follows a modular architecture. Each module is responsible for a specific business function and can be installed independently. The system is designed to be extensible, allowing developers to add new features and customize existing ones.

### Core Modules

- **Base**: Contains core functionality and dependencies
- **PRISM Base**: Extends the base module with PRISM-specific functionality
- **Theme**: Provides custom styling and branding
- **Company**: Manages company information and settings
- **Partner**: Manages customer and vendor information
- **Product**: Manages product information and pricing
- **Sales**: Manages sales orders and invoicing
- **Purchase**: Manages purchase orders and vendor bills
- **Inventory**: Manages inventory and warehouse operations
- **Accounting**: Manages financial transactions and reporting
- **Tax**: Manages tax calculations and reporting
- **Payroll**: Manages employee payroll and benefits
- **User**: Manages user accounts and permissions

### Module Dependencies

```
Base
├── PRISM Base
├── Theme
├── Company
├── Partner
├── Product
│   └── Inventory
├── Sales
│   ├── Partner
│   ├── Product
│   └── Tax
├── Purchase
│   ├── Partner
│   ├── Product
│   └── Tax
├── Inventory
│   ├── Product
│   └── Company
├── Accounting
│   ├── Company
│   └── Tax
├── Tax
│   └── Company
├── Payroll
│   ├── Company
│   └── Partner
└── User
    └── Company
```

## Development Environment Setup

### Prerequisites

- Python 3.10 or later
- PostgreSQL 14 or later
- Node.js 16 or later
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/numexia/prism-erp.git
   cd prism-erp
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python -m odoo -d prism_erp -i base,prism_base,theme,company,partner,product,sales,purchase,inventory,prism_inventory
   ```

5. Start the development server:
   ```bash
   python -m odoo -d prism_erp
   ```

## Coding Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use 4 spaces for indentation
- Maximum line length: 120 characters
- Use docstrings for all classes and methods
- Use type hints where appropriate

### JavaScript Code Style

- Follow ESLint guidelines
- Use 2 spaces for indentation
- Maximum line length: 120 characters
- Use JSDoc for all functions and classes

### XML Code Style

- Use 2 spaces for indentation
- Use double quotes for attribute values
- Keep element names and attribute names lowercase
- Use meaningful IDs and names

## Module Development

### Module Structure

Each module follows a standard structure:

```
module_name/
├── __init__.py
├── __manifest__.py
├── data/
│   └── module_data.xml
├── models/
│   ├── __init__.py
│   └── model_name.py
├── security/
│   └── ir.model.access.csv
├── static/
│   ├── description/
│   │   ├── index.html
│   │   └── icon.png
│   └── src/
│       ├── js/
│       │   └── module_name.js
│       └── scss/
│           └── module_name.scss
├── views/
│   └── view_name.xml
└── wizards/
    ├── __init__.py
    └── wizard_name.py
```

### Creating a New Module

1. Create a new directory with the module name
2. Create the `__init__.py` and `__manifest__.py` files
3. Define your models, views, and other components
4. Register your module in the `__manifest__.py` file

### Example: Warehouse Type Model

The warehouse type model is a good example of how to implement a model with Moroccan-specific features. It defines different types of warehouses with specific properties, such as customs requirements, VAT exemption, and inspection frequency.

```python
class StockWarehouseType(models.Model):
    _name = 'stock.warehouse.type'
    _description = 'Warehouse Type'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', required=True, translate=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    # Customs and regulatory fields
    requires_customs = fields.Boolean(string='Requires Customs', default=False, tracking=True,
                                    help="Whether warehouses of this type require customs documentation")
    
    is_vat_exempt = fields.Boolean(string='VAT Exempt', default=False, tracking=True,
                                 help="Whether warehouses of this type are exempt from VAT")
    
    # Categorization fields
    category = fields.Selection([
        ('standard', 'Standard'),
        ('bonded', 'Bonded'),
        ('free_zone', 'Free Zone'),
        ('transit', 'Transit'),
        ('export', 'Export'),
        ('special', 'Special Economic Zone')
    ], string='Category', required=True, default='standard', tracking=True,
       help="The category of the warehouse type according to Moroccan regulations")
    
    # Business logic methods
    @api.constrains('category', 'requires_customs')
    def _check_category_customs(self):
        """Ensure customs requirements are consistent with category"""
        for warehouse_type in self:
            if warehouse_type.category in ['bonded', 'transit', 'free_zone'] and not warehouse_type.requires_customs:
                raise ValidationError(_("Warehouse types in the '%s' category must require customs documentation.") % warehouse_type.category)
```

The warehouse model then uses this type to define its properties:

```python
class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    warehouse_type_id = fields.Many2one('stock.warehouse.type', string="Warehouse Type", 
                                      required=True, 
                                      help="Type of warehouse according to Moroccan regulations")
    
    is_vat_exempt = fields.Boolean(string="VAT Exempt", 
                                 related='warehouse_type_id.is_vat_exempt', 
                                 readonly=True, store=True,
                                 help="Whether goods in this warehouse are exempt from VAT")
    
    requires_customs_clearance = fields.Boolean(string="Requires Customs Clearance", 
                                              related='warehouse_type_id.requires_customs',
                                              readonly=True, store=True)
```

This approach allows for flexible configuration of warehouse types while ensuring consistency with Moroccan regulations.

### Example: Bon de Livraison (BL) Workflow

In Morocco, sales are handled differently than in many other countries. The "Bon de Livraison" (BL) or delivery note is a critical document that combines aspects of both sales orders and delivery slips. Here's how to implement this Moroccan-specific workflow:

```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Add state for Bon de Livraison
    state = fields.Selection(selection_add=[
        ('bl', 'Bon de Livraison'),
        ('to_invoice', 'To Invoice'),
    ])
    
    is_bl = fields.Boolean(string="Is Bon de Livraison", compute='_compute_is_bl', store=True)
    bl_number = fields.Char(string="BL Number", readonly=True, copy=False)
    bl_date = fields.Date(string="BL Date")
    
    @api.depends('state')
    def _compute_is_bl(self):
        for order in self:
            order.is_bl = order.state == 'bl'
    
    def action_confirm(self):
        """Override to add BL-specific logic when confirming a sale order"""
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            # Generate BL number if not already set
            if not order.bl_number:
                order.bl_number = self.env['ir.sequence'].next_by_code('sale.order.bl')
            order.write({'state': 'bl', 'bl_date': fields.Date.today()})
        return res
    
    def action_create_invoice(self):
        """Create invoice from BL"""
        self.ensure_one()
        if self.state != 'bl':
            raise UserError(_("You can only create an invoice for a Bon de Livraison."))
        # Create invoice logic
        invoice = self._create_invoices()
        self.write({'state': 'to_invoice'})
        return invoice
    
    def action_return_bl(self):
        """Process a return for this BL"""
        self.ensure_one()
        if self.state != 'bl':
            raise UserError(_("You can only return a Bon de Livraison."))
        # Create return picking
        return_picking = self._create_return_picking()
        self.write({'state': 'cancel'})
        return return_picking
```

The key aspects of this implementation are:

1. **Merged Functionality**: The BL combines sales order and delivery slip functionality
2. **Workflow States**: The sale order goes through specific states: draft → sale order → BL → to invoice
3. **Return Process**: When a BL is returned, it goes back to canceled state
4. **End-of-Month Invoicing**: Companies often deliver products with BL and send invoices at the end of the month

This approach ensures that the system follows Moroccan business practices while maintaining compatibility with the standard Odoo workflow.

## API Reference

*Coming soon*

## Testing

*Coming soon*

## Deployment

*Coming soon*

## Troubleshooting

*Coming soon*

---

This guide will be continuously updated as the PRISM ERP system evolves. For the latest version, please visit our documentation portal or contact our development team.
