"""
HKM Category Analytics - Backend API
Comprehensive financial analysis dashboard with category management
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, get_first_day, get_last_day, add_months, add_years
import json
import traceback
from datetime import datetime


@frappe.whitelist()
def get_companies():
    """Get list of companies"""
    companies = frappe.get_all('Company', fields=['name'], order_by='name')
    # Return list of company names (strings) for compatibility
    return [company['name'] for company in companies]


@frappe.whitelist()
def get_dashboard_data(company, from_date, to_date):
    """
    Main API to get all dashboard data
    
    Args:
        company: Company name
        from_date: Start date
        to_date: End date
    
    Returns:
        Complete dashboard data with income, expense, trends, and comparisons
    """
    try:
        from_date = getdate(from_date)
        to_date = getdate(to_date)
        
        # Get categories from DocType
        income_categories = get_categories_from_doctype(company, 'Income')
        expense_categories = get_categories_from_doctype(company, 'Expense')
        
        # Generate monthly periods
        periods = generate_periods(from_date, to_date)
        
        # Get data for each period
        income_data = {}
        expense_data = {}
        
        for period in periods:
            period_label = period['label']
            
            # Get Income data
            income_gl = get_gl_entries(company, period['from_date'], period['to_date'], 'Income')
            income_categorized, income_accounts = categorize_accounts(income_gl, income_categories)
            
            for category, amount in income_categorized.items():
                if category not in income_data:
                    income_data[category] = {
                        'monthly': [],
                        'accounts': income_accounts.get(category, [])
                    }
                income_data[category]['monthly'].append({
                    'month': period_label,
                    'amount': amount,
                    'date': period['from_date'].strftime('%Y-%m-%d')
                })
            
            # Get Expense data
            expense_gl = get_gl_entries(company, period['from_date'], period['to_date'], 'Expense')
            expense_categorized, expense_accounts = categorize_accounts(expense_gl, expense_categories)
            
            for category, amount in expense_categorized.items():
                if category not in expense_data:
                    expense_data[category] = {
                        'monthly': [],
                        'accounts': expense_accounts.get(category, [])
                    }
                expense_data[category]['monthly'].append({
                    'month': period_label,
                    'amount': amount,
                    'date': period['from_date'].strftime('%Y-%m-%d')
                })
        
        # Calculate statistics (variance, volatility)
        income_stats = calculate_category_statistics(income_data)
        expense_stats = calculate_category_statistics(expense_data)
        
        # Get year-over-year comparison
        yoy_comparison = get_yoy_comparison(company, from_date, to_date, income_categories, expense_categories)
        
        # Calculate totals
        total_income = sum([sum([m['amount'] for m in cat['monthly']]) for cat in income_data.values()])
        total_expense = sum([sum([m['amount'] for m in cat['monthly']]) for cat in expense_data.values()])
        
        return {
            'periods': [p['label'] for p in periods],
            'income_data': income_data,
            'expense_data': expense_data,
            'income_stats': income_stats,
            'expense_stats': expense_stats,
            'yoy_comparison': yoy_comparison,
            'summary': {
                'total_income': total_income,
                'total_expense': total_expense,
                'net_income': total_income - total_expense
            }
        }
    except Exception as e:
        frappe.log_error(f'Error in get_dashboard_data: {str(e)}\n{traceback.format_exc()}', 'Category Analytics Error')
        frappe.throw(_(f'Error loading dashboard data: {str(e)}'))


def get_categories_from_doctype(company, root_type):
    """
    Get categories from HKM Analysis Category DocType
    
    Returns:
        Dictionary with category details and account mappings
    """
    try:
        # Check if doctype exists
        if not frappe.db.exists('DocType', 'HKM Analysis Category'):
            frappe.log_error('HKM Analysis Category doctype does not exist', 'Category Analytics')
            return {}
        
        # Get categories with their display names
        categories = frappe.db.sql("""
            SELECT 
                cat.name,
                cat.category_name as category_link,
                cat_name.category_name as category_display_name,
                cat.root_type
            FROM `tabHKM Analysis Category` cat
            LEFT JOIN `tabHKM Analysis Category Name` cat_name
                ON cat.category_name = cat_name.name
            WHERE cat.company = %(company)s
                AND cat.root_type = %(root_type)s
                AND cat.docstatus < 2
            ORDER BY cat_name.category_name
        """, {'company': company, 'root_type': root_type}, as_dict=True)
        
        result = {}
        for cat in categories:
            accounts = frappe.get_all(
                'HKM Analysis Category Detail',
                filters={'parent': cat.name},
                fields=['account', 'portion']
            )
            
            # Use display name as key
            display_name = cat.category_display_name or cat.category_link
            result[display_name] = {
                'doctype_name': cat.name,
                'category_link': cat.category_link,
                'root_type': cat.root_type,
                'accounts': {acc.account: acc.portion for acc in accounts}
            }
        
        return result
    except Exception as e:
        frappe.log_error(f'Error getting categories: {str(e)}', 'Category Analytics Error')
        # Return empty dict instead of crashing
        return {}


def get_gl_entries(company, from_date, to_date, root_type):
    """
    Get GL Entries for a period
    
    Returns:
        List of GL entries with account and amount
    """
    query = """
        SELECT 
            acc.name as account,
            acc.account_name,
            ROUND(SUM(CASE 
                WHEN acc.root_type = 'Income' THEN gl.credit - gl.debit 
                ELSE gl.debit - gl.credit 
            END), 2) as amount
        FROM `tabGL Entry` gl
        JOIN `tabAccount` acc ON gl.account = acc.name
        WHERE gl.company = %(company)s
            AND gl.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND gl.docstatus = 1
            AND gl.voucher_type != 'Period Closing Voucher'
            AND acc.root_type = %(root_type)s
        GROUP BY acc.name
        HAVING amount != 0
        ORDER BY acc.account_name
    """
    
    return frappe.db.sql(query, {
        'company': company,
        'from_date': from_date,
        'to_date': to_date,
        'root_type': root_type
    }, as_dict=True)


def categorize_accounts(gl_entries, categories_config):
    """
    Categorize accounts based on DocType configuration with percentage support
    
    Returns:
        Tuple of (categorized amounts, account details per category)
    """
    categorized = {}
    categorized_accounts = {}
    categorized_account_set = set()
    
    # Create lookup dict for GL entries
    gl_lookup = {entry.account: entry for entry in gl_entries}
    
    # Process each category
    for category_name, category_data in categories_config.items():
        accounts_config = category_data.get('accounts', {})
        
        if not accounts_config:
            continue
        
        category_total = 0
        category_account_list = []
        
        # Process each account in this category
        for account_name, portion in accounts_config.items():
            if account_name in gl_lookup:
                gl_entry = gl_lookup[account_name]
                # Apply portion percentage
                allocated_amount = gl_entry.amount * (portion / 100.0)
                category_total += allocated_amount
                category_account_list.append({
                    'account': account_name,
                    'account_name': gl_entry.account_name,
                    'portion': portion,
                    'amount': allocated_amount,
                    'total_amount': gl_entry.amount
                })
                categorized_account_set.add(account_name)
        
        if category_total != 0 or category_account_list:
            categorized[category_name] = category_total
            categorized_accounts[category_name] = category_account_list
    
    # Find uncategorized accounts
    uncategorized = []
    for entry in gl_entries:
        if entry.account not in categorized_account_set:
            uncategorized.append({
                'account': entry.account,
                'account_name': entry.account_name,
                'portion': 100,
                'amount': entry.amount,
                'total_amount': entry.amount
            })
    
    # Add "Uncategorized" category
    if uncategorized:
        other_total = sum([item['amount'] for item in uncategorized])
        categorized['Uncategorized'] = other_total
        categorized_accounts['Uncategorized'] = uncategorized
    
    return categorized, categorized_accounts


def generate_periods(from_date, to_date):
    """Generate monthly periods between dates"""
    periods = []
    current_date = get_first_day(from_date)
    
    while current_date <= to_date:
        period_end = get_last_day(current_date)
        if period_end > to_date:
            period_end = to_date
        
        periods.append({
            'label': current_date.strftime('%b %Y'),
            'from_date': current_date,
            'to_date': period_end
        })
        
        current_date = add_months(current_date, 1)
    
    return periods


def calculate_category_statistics(category_data):
    """
    Calculate statistics for each category (variance, volatility, trend)
    
    Returns:
        Dictionary with statistics per category
    """
    import statistics
    
    stats = {}
    
    for category, data in category_data.items():
        monthly_amounts = [m['amount'] for m in data['monthly']]
        
        if len(monthly_amounts) < 2:
            stats[category] = {
                'mean': monthly_amounts[0] if monthly_amounts else 0,
                'variance': 0,
                'std_dev': 0,
                'volatility': 'stable',
                'trend': 'neutral',
                'month_over_month': []
            }
            continue
        
        mean = statistics.mean(monthly_amounts)
        variance = statistics.variance(monthly_amounts) if len(monthly_amounts) > 1 else 0
        std_dev = statistics.stdev(monthly_amounts) if len(monthly_amounts) > 1 else 0
        
        # Calculate coefficient of variation (CV) for volatility
        cv = (std_dev / mean * 100) if mean != 0 else 0
        
        # Classify volatility
        if cv < 15:
            volatility = 'stable'
        elif cv < 30:
            volatility = 'moderate'
        else:
            volatility = 'volatile'
        
        # Calculate trend (simple linear regression slope)
        n = len(monthly_amounts)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = mean
        
        numerator = sum([(x[i] - x_mean) * (monthly_amounts[i] - y_mean) for i in range(n)])
        denominator = sum([(x[i] - x_mean) ** 2 for i in range(n)])
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Classify trend
        if slope > mean * 0.05:  # More than 5% growth per period
            trend = 'increasing'
        elif slope < -mean * 0.05:  # More than 5% decline per period
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Calculate month-over-month changes
        mom_changes = []
        for i in range(1, len(monthly_amounts)):
            prev = monthly_amounts[i-1]
            curr = monthly_amounts[i]
            change = ((curr - prev) / prev * 100) if prev != 0 else 0
            mom_changes.append({
                'month': data['monthly'][i]['month'],
                'change_percent': change,
                'change_amount': curr - prev
            })
        
        stats[category] = {
            'mean': mean,
            'variance': variance,
            'std_dev': std_dev,
            'cv': cv,
            'volatility': volatility,
            'trend': trend,
            'month_over_month': mom_changes
        }
    
    return stats


def get_yoy_comparison(company, from_date, to_date, income_categories, expense_categories):
    """
    Get year-over-year comparison for the same period last year
    
    Returns:
        Dictionary with YoY comparison data
    """
    # Calculate last year's dates
    ly_from_date = add_years(from_date, -1)
    ly_to_date = add_years(to_date, -1)
    
    # Get last year's data
    ly_income_gl = get_gl_entries(company, ly_from_date, ly_to_date, 'Income')
    ly_income_categorized, _ = categorize_accounts(ly_income_gl, income_categories)
    
    ly_expense_gl = get_gl_entries(company, ly_from_date, ly_to_date, 'Expense')
    ly_expense_categorized, _ = categorize_accounts(ly_expense_gl, expense_categories)
    
    # Get current year's data
    cy_income_gl = get_gl_entries(company, from_date, to_date, 'Income')
    cy_income_categorized, _ = categorize_accounts(cy_income_gl, income_categories)
    
    cy_expense_gl = get_gl_entries(company, from_date, to_date, 'Expense')
    cy_expense_categorized, _ = categorize_accounts(cy_expense_gl, expense_categories)
    
    # Calculate comparisons
    income_comparison = {}
    for category in cy_income_categorized.keys():
        cy_amount = cy_income_categorized.get(category, 0)
        ly_amount = ly_income_categorized.get(category, 0)
        change = cy_amount - ly_amount
        change_percent = (change / ly_amount * 100) if ly_amount != 0 else 0
        
        income_comparison[category] = {
            'current_year': cy_amount,
            'last_year': ly_amount,
            'change': change,
            'change_percent': change_percent
        }
    
    expense_comparison = {}
    for category in cy_expense_categorized.keys():
        cy_amount = cy_expense_categorized.get(category, 0)
        ly_amount = ly_expense_categorized.get(category, 0)
        change = cy_amount - ly_amount
        change_percent = (change / ly_amount * 100) if ly_amount != 0 else 0
        
        expense_comparison[category] = {
            'current_year': cy_amount,
            'last_year': ly_amount,
            'change': change,
            'change_percent': change_percent
        }
    
    return {
        'income': income_comparison,
        'expense': expense_comparison,
        'period': {
            'current': {'from': from_date.strftime('%Y-%m-%d'), 'to': to_date.strftime('%Y-%m-%d')},
            'last_year': {'from': ly_from_date.strftime('%Y-%m-%d'), 'to': ly_to_date.strftime('%Y-%m-%d')}
        }
    }


@frappe.whitelist(allow_guest=True)
def get_category_details(company, from_date, to_date, category, root_type):
    """
    Get detailed account breakdown for a specific category and month
    
    Args:
        company: Company name
        from_date: Start date
        to_date: End date
        category: Category name (or "Uncategorized")
        root_type: 'Income' or 'Expense'
    
    Returns:
        List of accounts with amounts for the category
    """
    from_date = getdate(from_date)
    to_date = getdate(to_date)
    
    # Get categories
    categories = get_categories_from_doctype(company, root_type)
    
    # Get GL entries
    gl_entries = get_gl_entries(company, from_date, to_date, root_type)
    
    # Categorize accounts
    _, categorized_accounts = categorize_accounts(gl_entries, categories)
    
    # Handle "Uncategorized" - it's already in categorized_accounts from categorize_accounts function
    if category == "Uncategorized":
        uncategorized_list = categorized_accounts.get('Uncategorized', [])
        total = sum([acc['amount'] for acc in uncategorized_list])
        
        return {
            'accounts': uncategorized_list,
            'total': total,
            'category': 'Uncategorized',
            'count': len(uncategorized_list)
        }
    
    # Regular category
    if category not in categories and category != "Uncategorized":
        return {'accounts': [], 'total': 0, 'category': category, 'count': 0}
    
    # Get accounts for the requested category
    accounts_list = categorized_accounts.get(category, [])
    total = sum([acc['amount'] for acc in accounts_list])
    
    return {
        'accounts': accounts_list,
        'total': total,
        'category': category,
        'count': len(accounts_list)
    }


# ============================================================================
# CATEGORY MANAGEMENT APIs
# ============================================================================

@frappe.whitelist()
def get_all_categories(company):
    """
    Get all categories for a company (Income, Expense, Asset, Liability)
    
    Returns:
        Dictionary with all category types
    """
    income_categories = get_categories_from_doctype(company, 'Income')
    expense_categories = get_categories_from_doctype(company, 'Expense')
    asset_categories = get_categories_from_doctype(company, 'Asset')
    liability_categories = get_categories_from_doctype(company, 'Liability')
    
    return {
        'income': income_categories,
        'expense': expense_categories,
        'asset': asset_categories,
        'liability': liability_categories
    }


@frappe.whitelist()
def get_all_accounts(company, root_type):
    """
    Get all leaf accounts for a company and root type
    
    Returns:
        List of accounts with their current category mappings
    """
    # Get all leaf accounts
    accounts = frappe.get_all(
        'Account',
        filters={
            'company': company,
            'root_type': root_type,
            'is_group': 0
        },
        fields=['name', 'account_name', 'disabled'],
        order_by='disabled asc, account_name asc'
    )
    
    # Get categories
    categories = get_categories_from_doctype(company, root_type)
    
    # Build account mapping
    account_mapping = {}
    for account in accounts:
        account_mapping[account.name] = {
            'account_name': account.account_name,
            'disabled': account.disabled or 0,
            'categories': [],
            'total_allocated': 0,
            'remaining': 100
        }
    
    # Add category information and calculate totals
    for category_name, category_data in categories.items():
        for account, portion in category_data['accounts'].items():
            if account in account_mapping:
                account_mapping[account]['categories'].append({
                    'category': category_name,
                    'portion': portion
                })
                account_mapping[account]['total_allocated'] += portion
    
    # Calculate remaining portion for each account
    for account, data in account_mapping.items():
        data['remaining'] = 100 - data['total_allocated']
    
    return {
        'accounts': account_mapping,
        'categories': list(categories.keys())
    }


@frappe.whitelist()
def save_category(company, root_type, category_name, accounts_data, old_category_name=None, description=''):
    """
    Save or update a category
    
    Args:
        company: Company name
        root_type: 'Income' or 'Expense'
        category_name: Category display name
        accounts_data: JSON string of [{account: str, portion: float}, ...]
        old_category_name: If renaming, the old display name
        description: Category description
    
    Returns:
        Success message
    """
    # Parse accounts data
    if isinstance(accounts_data, str):
        accounts_data = json.loads(accounts_data)
    
    # First, ensure the category name exists in HKM Analysis Category Name
    category_name_doc = frappe.db.exists("HKM Analysis Category Name", category_name)
    if not category_name_doc:
        # Create new category name
        cat_name_doc = frappe.get_doc({
            'doctype': 'HKM Analysis Category Name',
            'category_name': category_name,
            'root_type': root_type,
            'description': description or ''
        })
        cat_name_doc.insert(ignore_permissions=True)
        category_name_link = cat_name_doc.name
    else:
        category_name_link = category_name
        # Update description if provided
        if description:
            frappe.db.set_value("HKM Analysis Category Name", category_name_link, "description", description)
    
    # Check if category mapping exists for this company
    if old_category_name and old_category_name != category_name:
        # Renaming - find old category by display name
        old_category_link = frappe.db.get_value("HKM Analysis Category Name", old_category_name, "name")
        existing = frappe.db.get_value(
            'HKM Analysis Category',
            {
                'company': company,
                'category_name': old_category_link,
                'root_type': root_type
            },
            'name'
        )
    else:
        # Creating or updating
        existing = frappe.db.get_value(
            'HKM Analysis Category',
            {
                'company': company,
                'category_name': category_name_link,
                'root_type': root_type
            },
            'name'
        )
    
    if existing:
        # Update existing category
        doc = frappe.get_doc('HKM Analysis Category', existing)
        doc.category_name = category_name_link
        doc.accounts = []
    else:
        # Create new category
        doc = frappe.get_doc({
            'doctype': 'HKM Analysis Category',
            'company': company,
            'category_name': category_name_link,
            'root_type': root_type
        })
    
    # Add accounts
    for acc_data in accounts_data:
        doc.append('accounts', {
            'account': acc_data['account'],
            'portion': acc_data.get('portion', 100.0)
        })
    
    # Save
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)
    
    frappe.db.commit()  # v16: OK - API endpoint for category management
    
    return {
        'success': True,
        'message': f'Category "{category_name}" saved successfully',
        'doctype_name': doc.name
    }


@frappe.whitelist()
def delete_category(company, category_name, root_type):
    """
    Delete a category
    
    Args:
        company: Company name
        category_name: Category display name
        root_type: 'Income' or 'Expense'
    
    Returns:
        Success message
    """
    # Get the category name link
    category_name_link = frappe.db.get_value("HKM Analysis Category Name", category_name, "name")
    if not category_name_link:
        frappe.throw(f'Category name "{category_name}" not found')
    
    doc_name = frappe.db.get_value(
        'HKM Analysis Category',
        {
            'company': company,
            'category_name': category_name_link,
            'root_type': root_type
        },
        'name'
    )
    
    if not doc_name:
        frappe.throw(f'Category "{category_name}" not found for company "{company}"')
    
    frappe.delete_doc('HKM Analysis Category', doc_name, ignore_permissions=True)
    frappe.db.commit()  # v16: OK - API endpoint for category management
    
    return {
        'success': True,
        'message': f'Category "{category_name}" deleted successfully'
    }


@frappe.whitelist()
def move_account(company, root_type, account, source_category, target_category, portion=100.0):
    """
    Move an account from one category to another
    
    Args:
        company: Company name
        root_type: 'Income' or 'Expense'
        account: Account name
        source_category: Source category display name (or null if uncategorized)
        target_category: Target category display name
        portion: Percentage to allocate
    
    Returns:
        Success message
    """
    portion = float(portion)
    
    # Remove from source category if specified
    if source_category:
        source_category_link = frappe.db.get_value("HKM Analysis Category Name", source_category, "name")
        if source_category_link:
            source_doc_name = frappe.db.get_value(
                'HKM Analysis Category',
                {
                    'company': company,
                    'category_name': source_category_link,
                    'root_type': root_type
                },
                'name'
            )
            
            if source_doc_name:
                source_doc = frappe.get_doc('HKM Analysis Category', source_doc_name)
                source_doc.accounts = [acc for acc in source_doc.accounts if acc.account != account]
                source_doc.save(ignore_permissions=True)
    
    # Add to target category
    target_category_link = frappe.db.get_value("HKM Analysis Category Name", target_category, "name")
    if not target_category_link:
        frappe.throw(f'Target category "{target_category}" not found')
    
    target_doc_name = frappe.db.get_value(
        'HKM Analysis Category',
        {
            'company': company,
            'category_name': target_category_link,
            'root_type': root_type
        },
        'name'
    )
    
    if not target_doc_name:
        frappe.throw(f'Target category "{target_category}" not found for company "{company}"')
    
    target_doc = frappe.get_doc('HKM Analysis Category', target_doc_name)
    
    # Check if account already exists
    existing_row = None
    for acc in target_doc.accounts:
        if acc.account == account:
            existing_row = acc
            break
    
    if existing_row:
        existing_row.portion = portion
    else:
        target_doc.append('accounts', {
            'account': account,
            'portion': portion
        })
    
    target_doc.save(ignore_permissions=True)
    frappe.db.commit()  # v16: OK - API endpoint for category management
    
    return {
        'success': True,
        'message': f'Account moved to "{target_category}" with {portion}% allocation'
    }


@frappe.whitelist(allow_guest=True)
def export_to_static_html(company, from_date, to_date, report_type=None):
    """
    Export dashboard data to a standalone static HTML file with comprehensive analytics
    All data is embedded in the HTML - no server calls needed

    Args:
        company: Company name
        from_date: Start date
        to_date: End date
        report_type: Type of report - 'balance-sheet', 'pl-report', or None for combined

    Returns:
        HTML content as string
    """
    # TODO: Move comprehensive_html_export to hkm app or implement inline
    # For now, return a simple error message
    frappe.throw(_('HTML export functionality is temporarily unavailable. Please use the dashboard view instead.'))


@frappe.whitelist()
def create_public_link(company, from_date, to_date, expires_in_days=30, report_type=None):
    """
    Create a public shareable link for the dashboard
    Reuses existing link if one exists for the same filters
    
    Args:
        company: Company name
        from_date: Start date
        to_date: End date
        expires_in_days: Number of days until link expires (default 30)
        report_type: Type of report - 'balance-sheet', 'pl-report', or None for combined
    
    Returns:
        Dictionary with public link details
    """
    import secrets
    from frappe.utils import add_days, now, getdate
    
    # Check if user has permission
    if not frappe.has_permission('HKM Analysis Category', 'read'):
        frappe.throw(_('You do not have permission to create public links'))
    
    # Convert dates to proper format
    from_date = getdate(from_date)
    to_date = getdate(to_date)
    
    # Check if a link already exists for these filters
    existing_filters = {
        'doctype': 'HKM Public Dashboard Link',
        'company': company,
        'from_date': from_date,
        'to_date': to_date,
        'is_active': 1
    }
    
    # Add report_type to filter if specified
    if report_type:
        existing_filters['report_type'] = report_type
    
    existing_link = frappe.db.exists(existing_filters)
    
    if existing_link:
        # Return existing link
        doc = frappe.get_doc('HKM Public Dashboard Link', existing_link)
        return {
            'success': True,
            'token': doc.token,
            'public_url': doc.public_url,
            'expires_at': doc.expires_at,
            'expires_in_days': doc.expires_in_days,
            'report_type': doc.get('report_type'),
            'is_existing': True
        }
    
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    # Calculate expiry date
    expiry_date = add_days(now(), expires_in_days)
    
    
    
    # https://hkmjerp.in/hkm-dashboard#/category-analytics/pl-report
    # Generate public URL based on report type
    site_url = frappe.utils.get_url()
    dashboard_url = f"{site_url}/hkm-dashboard"
    
    if report_type == 'balance-sheet':
        public_url = f"{dashboard_url}#/category-analytics/balance-sheet?public_token={token}"
    elif report_type == 'pl-report':
        public_url = f"{dashboard_url}#/category-analytics/pl-report?public_token={token}"
    else:
        public_url = f"{dashboard_url}#/category-analytics?public_token={token}"
    
    # Create new public link document
    doc = frappe.get_doc({
        'doctype': 'HKM Public Dashboard Link',
        'token': token,
        'company': company,
        'from_date': from_date,
        'to_date': to_date,
        'public_url': public_url,
        'report_type': report_type,
        'created_by': frappe.session.user,
        'created_at': now(),
        'expires_at': expiry_date,
        'expires_in_days': expires_in_days,
        'is_active': 1
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()  # v16: OK - API endpoint for public link creation
    
    return {
        'success': True,
        'token': token,
        'public_url': public_url,
        'expires_at': expiry_date,
        'expires_in_days': expires_in_days,
        'report_type': report_type,
        'is_existing': False
    }


@frappe.whitelist(allow_guest=True)
def get_public_dashboard_data(token):
    """
    Get dashboard data using public token (no authentication required)
    
    Args:
        token: Public access token
    
    Returns:
        Dashboard data if token is valid
    """
    from frappe.utils import now, get_datetime
    import traceback
    
    try:
        # Check if link exists and is active
        link = frappe.db.get_value(
            'HKM Public Dashboard Link',
            {'token': token, 'is_active': 1},
            ['company', 'from_date', 'to_date', 'expires_at'],
            as_dict=True
        )
        
        if not link:
            frappe.throw(_('Invalid or expired link'), frappe.PermissionError)
        
        # Check if link has expired
        if get_datetime(link.expires_at) < get_datetime(now()):
            frappe.throw(_('This link has expired'), frappe.PermissionError)
        
        # Get fresh dashboard data - Pass ignore_permissions flag to function
        # This tells the function to temporarily elevate permissions safely
        frappe.flags.ignore_permissions = True
        frappe.in_test = True  # v16: Changed from frappe.flags.in_test
        try:
            data = get_comprehensive_data_with_bs(link.company, link.from_date, link.to_date, ignore_permissions=True)
        except Exception as e:
            error_msg = f"Error in get_comprehensive_data_with_bs: {str(e)}"
            frappe.log_error(title="Public Dashboard Data Fetch Error", message=f"{error_msg}\n\nTraceback:\n{traceback.format_exc()}")
            raise
        finally:
            frappe.flags.ignore_permissions = False
            frappe.in_test = False  # v16: Changed from frappe.flags.in_test
        
        return {
            'success': True,
            'data': data,
            'company': link.company,
            'from_date': str(link.from_date),
            'to_date': str(link.to_date),
            'expires_at': str(link.expires_at)
        }
    except Exception as e:
        error_msg = f"Error in get_public_dashboard_data: {str(e)}"
        frappe.log_error(title="Public Dashboard API Error", message=f"{error_msg}\n\nToken: {token}\n\nTraceback:\n{traceback.format_exc()}")
        raise


@frappe.whitelist()
def get_public_links(report_type=None):
    """
    Get all public links created by current user or all if System Manager
    
    Args:
        report_type: Filter by report type ('balance-sheet', 'pl-report', or None for all)
    
    Returns:
        List of public links
    """
    from frappe.utils import now, get_datetime
    
    try:
        # Check if user has permission
        if not frappe.has_permission('HKM Analysis Category', 'read'):
            frappe.throw(_('You do not have permission to view public links'))
        
        # Check if doctype exists
        if not frappe.db.exists('DocType', 'HKM Public Dashboard Link'):
            return []
        
        filters = {'is_active': 1}
        
        # Add report_type filter if specified
        if report_type:
            filters['report_type'] = report_type
        
        # If not System Manager, show only own links
        if 'System Manager' not in frappe.get_roles():
            filters['created_by'] = frappe.session.user
        
        # Get fields list - check if report_type field exists in doctype
        fields = ['name', 'token', 'company', 'from_date', 'to_date', 'public_url', 
                  'created_by', 'created_at', 'expires_at', 'expires_in_days']
        
        # Check if report_type field exists in doctype
        try:
            meta = frappe.get_meta('HKM Public Dashboard Link')
            if meta.has_field('report_type'):
                fields.append('report_type')
        except Exception:
            # If we can't get meta, just skip report_type field
            pass
        
        links = frappe.get_all(
            'HKM Public Dashboard Link',
            filters=filters,
            fields=fields,
            order_by='created_at desc'
        )
        
        # Add status for each link and handle missing/null values
        current_time = get_datetime(now())
        for link in links:
            # Handle missing report_type field
            if 'report_type' not in link:
                link['report_type'] = None
            
            # Handle None or missing expires_at
            if link.get('expires_at'):
                try:
                    expires_at = get_datetime(link.expires_at)
                    link['is_expired'] = expires_at < current_time
                    link['status'] = 'Expired' if link['is_expired'] else 'Active'
                except Exception:
                    link['is_expired'] = True
                    link['status'] = 'Invalid Date'
            else:
                link['is_expired'] = True
                link['status'] = 'No Expiry Date'
        
        return links
    
    except Exception as e:
        frappe.log_error(f"Error in get_public_links: {str(e)}", "Category Analytics Error")
        frappe.throw(_(f'Error loading public links: {str(e)}'))


@frappe.whitelist()
def revoke_public_link(token):
    """
    Revoke a public link
    
    Args:
        token: Public access token to revoke
    
    Returns:
        Success message
    """
    # Check if user has permission
    if not frappe.has_permission('HKM Analysis Category', 'write'):
        frappe.throw(_('You do not have permission to revoke public links'))
    
    # Find and deactivate the link
    link_name = frappe.db.get_value('HKM Public Dashboard Link', {'token': token}, 'name')
    
    if not link_name:
        frappe.throw(_('Link not found'))
    
    doc = frappe.get_doc('HKM Public Dashboard Link', link_name)
    doc.is_active = 0
    doc.save(ignore_permissions=True)
    frappe.db.commit()  # v16: OK - API endpoint for link revocation
    
    return {
        'success': True,
        'message': 'Public link revoked successfully'
    }


# ============================================================================
# BALANCE SHEET & TRUST-SPECIFIC APIs
# ============================================================================

# Import balance sheet functions
from hkm_dashboard.api.category_analytics.balance_sheet import (
    get_companies_by_trust_type,
    get_balance_sheet_data,
    get_comprehensive_dashboard_data as get_comprehensive_data_with_bs
)

