"""
Trust-specific category templates for automatic setup
"""

import frappe
from frappe import _


# Category templates for each trust type
CHARITABLE_TRUST_CATEGORIES = {
    'Income': [
        {'name': 'Donations - Individual', 'description': 'Individual donor contributions'},
        {'name': 'Donations - Corporate', 'description': 'Corporate CSR and donations'},
        {'name': 'Grants', 'description': 'Government and institutional grants'},
        {'name': 'Interest Income', 'description': 'Interest from corpus and deposits'},
        {'name': 'Other Income', 'description': 'Miscellaneous income'}
    ],
    'Expense': [
        {'name': 'Program Expenses', 'description': 'Direct program and charitable activities'},
        {'name': 'Administrative Expenses', 'description': 'Office, staff, and admin costs'},
        {'name': 'Fundraising Expenses', 'description': 'Marketing and fundraising costs'},
        {'name': 'Depreciation', 'description': 'Asset depreciation'}
    ],
    'Asset': [
        {'name': 'Cash & Bank Accounts', 'description': 'Liquid cash and bank balances'},
        {'name': 'Fixed Deposits', 'description': 'Term deposits and FDs'},
        {'name': 'Corpus Fund Investments', 'description': 'Long-term corpus investments'},
        {'name': 'Fixed Assets', 'description': 'Buildings, equipment, vehicles'},
        {'name': 'CWIP', 'description': 'Capital work in progress'}
    ],
    'Liability': [
        {'name': 'Accounts Payable', 'description': 'Trade and expense payables'},
        {'name': 'Advance from Donors', 'description': 'Advance donations received'},
        {'name': 'Provisions', 'description': 'Provisions for expenses'}
    ]
}

RELIGIOUS_TRUST_CATEGORIES = {
    'Income': [
        {'name': 'Donation - Deity', 'description': 'Deity donations and offerings'},
        {'name': 'Prasadam Sales', 'description': 'Prasadam and food sales'},
        {'name': 'Temple Services', 'description': 'Puja, archana, and other services'},
        {'name': 'Festival Collections', 'description': 'Festival-specific collections'},
        {'name': 'Rent Income', 'description': 'Hall and property rentals'}
    ],
    'Expense': [
        {'name': 'Deity Expenses', 'description': 'Deity worship and maintenance'},
        {'name': 'Prasadam Expenses', 'description': 'Kitchen and prasadam costs'},
        {'name': 'Festival Expenses', 'description': 'Festival celebrations'},
        {'name': 'Temple Maintenance', 'description': 'Building and facility maintenance'},
        {'name': 'Staff Salaries', 'description': 'Pujari and staff salaries'}
    ],
    'Asset': [
        {'name': 'Cash & Bank Accounts', 'description': 'Temple cash and bank balances'},
        {'name': 'Temple Building', 'description': 'Temple structure and land'},
        {'name': 'Deity Ornaments', 'description': 'Deity jewelry and ornaments'},
        {'name': 'Kitchen Equipment', 'description': 'Prasadam kitchen equipment'},
        {'name': 'Vehicles', 'description': 'Temple vehicles'}
    ],
    'Liability': [
        {'name': 'Advance Bookings', 'description': 'Advance service bookings'},
        {'name': 'Accounts Payable', 'description': 'Trade payables'},
        {'name': 'Provisions', 'description': 'Expense provisions'}
    ]
}

BUSINESS_TRUST_CATEGORIES = {
    'Income': [
        {'name': 'Guest House Revenue', 'description': 'Room bookings and services'},
        {'name': 'Bookstore Sales', 'description': 'Book and merchandise sales'},
        {'name': 'Restaurant Revenue', 'description': 'Restaurant and cafe sales'},
        {'name': 'Other Business Income', 'description': 'Other commercial income'}
    ],
    'Expense': [
        {'name': 'Cost of Goods Sold', 'description': 'Direct cost of products sold'},
        {'name': 'Operating Expenses', 'description': 'Day-to-day operations'},
        {'name': 'Marketing Expenses', 'description': 'Advertising and promotion'},
        {'name': 'Administrative Expenses', 'description': 'Office and admin costs'}
    ],
    'Asset': [
        {'name': 'Cash & Bank Accounts', 'description': 'Business cash and banks'},
        {'name': 'Inventory', 'description': 'Stock of goods for sale'},
        {'name': 'Fixed Assets', 'description': 'Property, equipment, furniture'},
        {'name': 'Investments', 'description': 'Business investments'}
    ],
    'Liability': [
        {'name': 'Trade Payables', 'description': 'Supplier payables'},
        {'name': 'Loans', 'description': 'Business loans'},
        {'name': 'Tax Payable', 'description': 'GST and income tax payable'}
    ]
}


@frappe.whitelist()
def get_trust_category_template(trust_type):
    """
    Get category template for a trust type
    
    Args:
        trust_type: 'Charitable', 'Religious', or 'Business'
    
    Returns:
        Dictionary with category templates
    """
    templates = {
        'Charitable': CHARITABLE_TRUST_CATEGORIES,
        'Religious': RELIGIOUS_TRUST_CATEGORIES,
        'Business': BUSINESS_TRUST_CATEGORIES
    }
    
    return templates.get(trust_type, {})


@frappe.whitelist()
def setup_trust_categories(company, trust_type=None):
    """
    Auto-create categories based on trust type
    
    Args:
        company: Company name
        trust_type: Optional trust type (will fetch from company if not provided)
    
    Returns:
        Success message with created categories
    """
    # Get trust type from company if not provided
    if not trust_type:
        trust_type = frappe.db.get_value('Company', company, 'trust_type')
    
    if not trust_type:
        return {
            'success': False,
            'message': f'Trust type not set for company {company}'
        }
    
    # Get template
    template = get_trust_category_template(trust_type)
    
    if not template:
        return {
            'success': False,
            'message': f'No template found for trust type: {trust_type}'
        }
    
    created_categories = []
    
    # Create categories
    for root_type, categories in template.items():
        for category_info in categories:
            category_name = category_info['name']
            description = category_info.get('description', '')
            
            # Check if category name already exists
            category_name_doc = frappe.db.exists('HKM Analysis Category Name', category_name)
            
            if not category_name_doc:
                # Create category name
                cat_name_doc = frappe.get_doc({
                    'doctype': 'HKM Analysis Category Name',
                    'category_name': category_name,
                    'root_type': root_type,
                    'description': description
                })
                cat_name_doc.insert(ignore_permissions=True)
                category_name_link = cat_name_doc.name
            else:
                category_name_link = category_name
            
            # Check if category mapping exists for this company
            existing = frappe.db.exists('HKM Analysis Category', {
                'company': company,
                'category_name': category_name_link,
                'root_type': root_type
            })
            
            if not existing:
                # Create category mapping (without accounts initially)
                cat_doc = frappe.get_doc({
                    'doctype': 'HKM Analysis Category',
                    'company': company,
                    'category_name': category_name_link,
                    'root_type': root_type
                })
                cat_doc.insert(ignore_permissions=True)
                created_categories.append(f"{root_type}: {category_name}")
    
    frappe.db.commit()  # v16: REVIEW - check if needed
    
    return {
        'success': True,
        'message': f'Created {len(created_categories)} categories for {trust_type} trust',
        'categories': created_categories,
        'trust_type': trust_type
    }


@frappe.whitelist()
def get_trust_info(company):
    """
    Get trust information and category setup status
    
    Args:
        company: Company name
    
    Returns:
        Trust information and setup status
    """
    trust_type = frappe.db.get_value('Company', company, 'trust_type')
    
    if not trust_type:
        return {
            'has_trust_type': False,
            'message': 'Trust type not set for this company'
        }
    
    # Get existing categories
    existing_categories = frappe.get_all(
        'HKM Analysis Category',
        filters={'company': company},
        fields=['name', 'category_name', 'root_type']
    )
    
    # Get template
    template = get_trust_category_template(trust_type)
    template_count = sum([len(cats) for cats in template.values()])
    
    return {
        'has_trust_type': True,
        'trust_type': trust_type,
        'existing_categories_count': len(existing_categories),
        'template_categories_count': template_count,
        'is_setup_complete': len(existing_categories) >= template_count,
        'template': template
    }




