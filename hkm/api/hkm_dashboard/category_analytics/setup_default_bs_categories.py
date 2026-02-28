"""
Setup Default Balance Sheet Categories
Creates standard categories for Assets and Liabilities that can be used for financial indicators
"""

import frappe
from frappe import _

# Default Balance Sheet Categories
DEFAULT_CATEGORIES = {
    'Asset': {
        'Current Assets': {
            'description': 'Assets that can be converted to cash within one year',
            'accounts': []  # Will be populated by user
        },
        'Cash & Bank': {
            'description': 'Cash in hand and bank balances',
            'accounts': []
        },
        'Accounts Receivable': {
            'description': 'Money owed by customers',
            'accounts': []
        },
        'Loans/Advances': {
            'description': 'Loans given and advances (including imprest accounts and security deposits)',
            'accounts': []
        },
        'Inventory': {
            'description': 'Stock and inventory items',
            'accounts': []
        },
        'Fixed Assets': {
            'description': 'Long-term assets like property, equipment',
            'accounts': []
        },
        'Investments': {
            'description': 'Long-term investments and securities',
            'accounts': []
        },
        'Other Assets': {
            'description': 'Other miscellaneous assets',
            'accounts': []
        }
    },
    'Liability': {
        'Current Liabilities': {
            'description': 'Liabilities due within one year',
            'accounts': []
        },
        'Accounts Payable': {
            'description': 'Money owed to suppliers',
            'accounts': []
        },
        'Short-term Loans': {
            'description': 'Loans due within one year',
            'accounts': []
        },
        'Long-term Liabilities': {
            'description': 'Liabilities due after one year',
            'accounts': []
        },
        'Long-term Loans': {
            'description': 'Loans due after one year',
            'accounts': []
        },
        'Other Liabilities': {
            'description': 'Other miscellaneous liabilities',
            'accounts': []
        }
    }
}


def setup_default_categories(company):
    """
    Set up default Balance Sheet categories for a company
    
    Args:
        company: Company name
    """
    frappe.db.begin()
    
    try:
        for root_type, categories in DEFAULT_CATEGORIES.items():
            print(f"\n{'='*60}")
            print(f"Setting up {root_type} categories for {company}")
            print(f"{'='*60}")
            
            for category_name, category_data in categories.items():
                # Check if category name already exists
                cat_name_exists = frappe.db.exists("HKM Analysis Category Name", category_name)
                
                if not cat_name_exists:
                    # Create category name
                    cat_name_doc = frappe.get_doc({
                        'doctype': 'HKM Analysis Category Name',
                        'category_name': category_name,
                        'root_type': root_type,
                        'description': category_data['description']
                    })
                    cat_name_doc.insert(ignore_permissions=True)
                    print(f"✅ Created category name: {category_name}")
                else:
                    print(f"ℹ️  Category name already exists: {category_name}")
                
                # Check if category mapping exists for this company
                cat_mapping_exists = frappe.db.exists(
                    'HKM Analysis Category',
                    {
                        'company': company,
                        'category_name': category_name,
                        'root_type': root_type
                    }
                )
                
                if not cat_mapping_exists:
                    # Create category mapping (empty for now - user will add accounts)
                    cat_mapping_doc = frappe.get_doc({
                        'doctype': 'HKM Analysis Category',
                        'company': company,
                        'category_name': category_name,
                        'root_type': root_type
                    })
                    cat_mapping_doc.insert(ignore_permissions=True)
                    print(f"   → Created category mapping for {company}")
                else:
                    print(f"   → Category mapping already exists for {company}")
        
        frappe.db.commit()  # v16: REVIEW - check if needed
        print(f"\n{'='*60}")
        print(f"✅ Successfully set up default Balance Sheet categories!")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'message': 'Default Balance Sheet categories created successfully'
        }
        
    except Exception as e:
        frappe.db.rollback()
        print(f"\n❌ Error: {str(e)}")
        frappe.log_error(f"Error setting up default categories: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }


@frappe.whitelist()
def setup_for_company(company):
    """
    Whitelisted method to set up default categories for a company
    
    Args:
        company: Company name
    """
    return setup_default_categories(company)


@frappe.whitelist()
def setup_for_all_companies():
    """
    Set up default categories for all companies
    """
    companies = frappe.get_all('Company', fields=['name'])
    results = []
    
    for company in companies:
        result = setup_default_categories(company['name'])
        results.append({
            'company': company['name'],
            'result': result
        })
    
    return results


def execute():
    """
    Execute from bench console or as a patch
    """
    # Set up for Hare Krishna Movement Jaipur by default
    company = 'Hare Krishna Movement Jaipur'
    return setup_default_categories(company)


if __name__ == '__main__':
    execute()

