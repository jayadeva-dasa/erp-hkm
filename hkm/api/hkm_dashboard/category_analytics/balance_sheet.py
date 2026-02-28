"""
Balance Sheet Integration for Category Analytics
Uses ERPNext's standard Balance Sheet APIs for consistency
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days

from erpnext.accounts.report.financial_statements import (
    get_data,
    get_period_list
)


@frappe.whitelist()
def get_companies_by_trust_type():
    """
    Get companies grouped by trust type
    
    Returns:
        Dictionary with companies grouped by trust type
    """
    companies = frappe.get_all(
        'Company',
        fields=['name', 'abbr', 'trust_type'],
        order_by='name'
    )
    
    result = {
        'charitable': [],
        'religious': [],
        'business': [],
        'other': []
    }
    
    for company in companies:
        trust_type = (company.trust_type or '').lower()
        if trust_type in result:
            result[trust_type].append({
                'name': company.name,
                'abbr': company.abbr,
                'trust_type': company.trust_type
            })
        else:
            result['other'].append({
                'name': company.name,
                'abbr': company.abbr,
                'trust_type': company.trust_type or 'Not Set'
            })
    
    return result


@frappe.whitelist()
def get_balance_sheet_data(company, from_date, to_date, periodicity='Monthly'):
    """
    Get balance sheet data using ERPNext's standard functions
    This ensures consistency with Balance Sheet report
    
    Args:
        company: Company name
        from_date: Start date
        to_date: End date
        periodicity: 'Monthly', 'Quarterly', 'Yearly'
    
    Returns:
        Categorized balance sheet data
    """
    from_date = getdate(from_date)
    to_date = getdate(to_date)
    
    # Create filters object (similar to Balance Sheet report)
    filters = frappe._dict({
        'company': company,
        'period_start_date': from_date,
        'period_end_date': to_date,
        'filter_based_on': 'Date Range',
        'periodicity': periodicity,
        'accumulated_values': 1,  # For balance sheet, always accumulated
        'presentation_currency': frappe.get_cached_value('Company', company, 'default_currency')
    })
    
    # Get period list (handles fiscal years automatically)
    period_list = get_period_list(
        None,  # from_fiscal_year
        None,  # to_fiscal_year
        filters.period_start_date,
        filters.period_end_date,
        filters.filter_based_on,
        filters.periodicity,
        company=filters.company
    )
    
    # Get Asset data using ERPNext's function
    asset_data = get_data(
        company,
        "Asset",
        "Debit",
        period_list,
        only_current_fiscal_year=False,
        filters=filters,
        accumulated_values=filters.accumulated_values
    )
    
    # Get Liability data
    liability_data = get_data(
        company,
        "Liability",
        "Credit",
        period_list,
        only_current_fiscal_year=False,
        filters=filters,
        accumulated_values=filters.accumulated_values
    )
    
    # Get Equity data
    equity_data = get_data(
        company,
        "Equity",
        "Credit",
        period_list,
        only_current_fiscal_year=False,
        filters=filters,
        accumulated_values=filters.accumulated_values
    )
    
    # Categorize using our category system
    categorized_assets = categorize_balance_sheet_data(asset_data, company, 'Asset', period_list)
    categorized_liabilities = categorize_balance_sheet_data(liability_data, company, 'Liability', period_list)
    categorized_equity = categorize_balance_sheet_data(equity_data, company, 'Equity', period_list)
    
    # Calculate summary
    summary = calculate_balance_sheet_summary(
        categorized_assets,
        categorized_liabilities,
        categorized_equity,
        period_list
    )
    
    return {
        'period_list': [{'key': p.key, 'label': p.label, 'from_date': str(p.from_date), 'to_date': str(p.to_date)} for p in period_list],
        'assets': categorized_assets,
        'liabilities': categorized_liabilities,
        'equity': categorized_equity,
        'summary': summary
    }


def categorize_balance_sheet_data(erpnext_data, company, root_type, period_list):
    """
    Take ERPNext's balance sheet data and apply our category mappings
    
    Args:
        erpnext_data: Output from get_data() - list of account rows with period values
        company: Company name
        root_type: 'Asset', 'Liability', or 'Equity'
        period_list: List of period objects
    
    Returns:
        Categorized data structure similar to our income/expense format
    """
    from hkm_dashboard.api.category_analytics.dashboard import get_categories_from_doctype
    
    # Get our category mappings
    categories = get_categories_from_doctype(company, root_type)
    
    # Build account lookup from ERPNext data - ONLY LEAF ACCOUNTS (non-group)
    account_lookup = {}
    if erpnext_data:
        for row in erpnext_data:
            account_name = row.get('account')
            # Skip if:
            # 1. No account name
            # 2. Starts with "'" (total/summary rows in ERPNext reports)
            # 3. Has indent < max indent (means it's a parent/group account)
            # 4. Account is marked as group account
            if not account_name or account_name.startswith("'"):
                continue
            
            # Check if this is a leaf account (not a group)
            # In ERPNext financial reports, leaf accounts have the highest indent level
            # We need to verify this is not a group account
            is_group = frappe.db.get_value('Account', account_name, 'is_group')
            if not is_group:  # Only include leaf accounts
                account_lookup[account_name] = row
    
    # Categorize accounts
    categorized = {}
    categorized_account_set = set()
    
    for category_name, category_data in categories.items():
        accounts_config = category_data.get('accounts', {})
        
        if not accounts_config:
            continue
        
        category_monthly = []
        category_accounts = []
        
        # Process each account in this category
        for account_name, portion in accounts_config.items():
            if account_name in account_lookup:
                row = account_lookup[account_name]
                
                # Extract period values
                account_period_data = []
                for period in period_list:
                    value = flt(row.get(period.key, 0)) * (portion / 100.0)
                    account_period_data.append({
                        'month': period.label,
                        'amount': value,
                        'date': str(period.to_date)
                    })
                
                # Calculate total for this account
                total_value = sum([p['amount'] for p in account_period_data])
                
                category_accounts.append({
                    'account': account_name,
                    'account_name': row.get('account_name', account_name),
                    'portion': portion,
                    'amount': total_value,
                    'monthly': account_period_data
                })
                
                categorized_account_set.add(account_name)
        
        # Aggregate category monthly totals
        if category_accounts:
            for period in period_list:
                period_total = sum([
                    acc['monthly'][i]['amount'] 
                    for i, p in enumerate(period_list) 
                    if p.key == period.key
                    for acc in category_accounts
                ])
                category_monthly.append({
                    'month': period.label,
                    'amount': period_total,
                    'date': str(period.to_date)
                })
            
            categorized[category_name] = {
                'monthly': category_monthly,
                'accounts': category_accounts,
                'total': sum([acc['amount'] for acc in category_accounts])
            }
    
    # Handle uncategorized accounts (already filtered to leaf accounts only)
    uncategorized_accounts = []
    for account_name, row in account_lookup.items():
        if account_name not in categorized_account_set:
            # Double-check it's a leaf account (should already be filtered, but safety check)
            is_group = frappe.db.get_value('Account', account_name, 'is_group')
            if is_group:
                continue
                
            account_period_data = []
            for period in period_list:
                value = flt(row.get(period.key, 0))
                account_period_data.append({
                    'month': period.label,
                    'amount': value,
                    'date': str(period.to_date)
                })
            
            total_value = sum([p['amount'] for p in account_period_data])
            
            uncategorized_accounts.append({
                'account': account_name,
                'account_name': row.get('account_name', account_name),
                'portion': 100,
                'amount': total_value,
                'monthly': account_period_data
            })
    
    if uncategorized_accounts:
        uncategorized_monthly = []
        for period in period_list:
            period_total = sum([
                acc['monthly'][i]['amount']
                for i, p in enumerate(period_list)
                if p.key == period.key
                for acc in uncategorized_accounts
            ])
            uncategorized_monthly.append({
                'month': period.label,
                'amount': period_total,
                'date': str(period.to_date)
            })
        
        categorized['Uncategorized'] = {
            'monthly': uncategorized_monthly,
            'accounts': uncategorized_accounts,
            'total': sum([acc['amount'] for acc in uncategorized_accounts])
        }
    
    return categorized


def calculate_balance_sheet_summary(assets, liabilities, equity, period_list):
    """
    Calculate summary metrics from categorized balance sheet data
    
    Returns:
        Dictionary with summary metrics
    """
    # Get latest period values - use -1 for last period
    latest_period_idx = -1
    
    # Helper function to safely get amount from monthly data
    def get_latest_amount(cat_data):
        if not cat_data.get('monthly'):
            return 0
        monthly = cat_data['monthly']
        if not monthly or len(monthly) == 0:
            return 0
        # Get the last period's amount
        return flt(monthly[latest_period_idx].get('amount', 0))
    
    # Sum up all asset values for latest period
    total_assets = sum([
        get_latest_amount(cat_data)
        for cat_data in assets.values()
    ])
    
    total_liabilities = sum([
        get_latest_amount(cat_data)
        for cat_data in liabilities.values()
    ])
    
    total_equity = sum([
        get_latest_amount(cat_data)
        for cat_data in equity.values()
    ])
    
    # Identify current assets and liabilities (simplified - can be enhanced)
    current_asset_keywords = ['cash', 'bank', 'receivable', 'inventory', 'prepaid', 'current']
    current_liability_keywords = ['payable', 'outstanding', 'short', 'current']
    
    current_assets = sum([
        get_latest_amount(cat_data)
        for cat_name, cat_data in assets.items()
        if any(keyword in cat_name.lower() for keyword in current_asset_keywords)
    ])
    
    current_liabilities = sum([
        get_latest_amount(cat_data)
        for cat_name, cat_data in liabilities.items()
        if any(keyword in cat_name.lower() for keyword in current_liability_keywords)
    ])
    
    return {
        'total_assets': flt(total_assets),
        'total_liabilities': flt(total_liabilities),
        'total_equity': flt(total_equity),
        'current_assets': flt(current_assets),
        'current_liabilities': flt(current_liabilities),
        'fixed_assets': flt(total_assets - current_assets),
        'long_term_liabilities': flt(total_liabilities - current_liabilities),
        'working_capital': flt(current_assets - current_liabilities),
        'balance_check': flt(abs(total_assets - (total_liabilities + total_equity)))  # Should be ~0
    }


@frappe.whitelist()
def get_comprehensive_dashboard_data(company, from_date, to_date, ignore_permissions=False):
    """
    Get complete dashboard data including P&L and Balance Sheet
    
    Args:
        company: Company name
        from_date: Start date
        to_date: End date
        ignore_permissions: If True, bypass all permission checks (for public links)
    
    Returns:
        Complete dashboard data
    """
    from hkm_dashboard.api.category_analytics.dashboard import get_dashboard_data
    
    # If ignore_permissions is requested, set flags
    if ignore_permissions:
        old_user = frappe.session.user
        frappe.set_user('Administrator')
    
    try:
        # Get P&L data (existing function)
        pl_data = get_dashboard_data(company, from_date, to_date)
        
        # Get Balance Sheet data (new function)
        bs_data = get_balance_sheet_data(company, from_date, to_date)
        
        # Get trust type
        trust_type = frappe.db.get_value('Company', company, 'trust_type')
        
        # Calculate financial ratios
        ratios = calculate_financial_ratios(bs_data['summary'], pl_data['summary'])
        
        # Calculate trust-specific ratios
        trust_ratios = calculate_trust_specific_ratios(
            bs_data,
            pl_data,
            trust_type
        )
        
        return {
            # P&L Data (keep original structure for compatibility)
            'income_data': pl_data.get('income_data'),
            'expense_data': pl_data.get('expense_data'),
            'income_stats': pl_data.get('income_stats'),
            'expense_stats': pl_data.get('expense_stats'),
            'yoy_comparison': pl_data.get('yoy_comparison'),
            'summary': pl_data.get('summary'),  # Changed from pl_summary to summary
            'periods': pl_data.get('periods'),  # Add periods for charts
            
            # Balance Sheet Data (nested structure)
            'balance_sheet_data': {
                'assets': bs_data.get('assets'),
                'liabilities': bs_data.get('liabilities'),
                'equity': bs_data.get('equity'),
                'summary': bs_data.get('summary'),
                'periods': bs_data.get('period_list')
            },
            
            # Ratios
            'financial_ratios': ratios,
            'trust_specific_ratios': trust_ratios,
            
            # Meta
            'company': company,
            'trust_type': trust_type,
            'from_date': str(from_date),
            'to_date': str(to_date)
        }
    finally:
        # Reset user if we changed it
        if ignore_permissions:
            frappe.set_user(old_user)


def calculate_financial_ratios(bs_summary, pl_summary):
    """
    Calculate standard financial ratios
    
    Returns:
        Dictionary with financial ratios
    """
    ratios = {}
    
    # Safely get values with defaults
    total_assets = flt(bs_summary.get('total_assets', 0))
    total_liabilities = flt(bs_summary.get('total_liabilities', 0))
    total_equity = flt(bs_summary.get('total_equity', 0))
    current_assets = flt(bs_summary.get('current_assets', 0))
    current_liabilities = flt(bs_summary.get('current_liabilities', 0))
    net_income = flt(pl_summary.get('net_income', 0)) if pl_summary else 0
    
    # Liquidity Ratios
    if current_liabilities > 0:
        ratios['current_ratio'] = flt(current_assets / current_liabilities, 2)
        ratios['quick_ratio'] = flt((current_assets * 0.8) / current_liabilities, 2)  # Simplified
    else:
        ratios['current_ratio'] = None
        ratios['quick_ratio'] = None
    
    # Solvency Ratios
    if total_equity > 0:
        ratios['debt_to_equity'] = flt(total_liabilities / total_equity, 2)
    else:
        ratios['debt_to_equity'] = None
    
    if total_assets > 0:
        ratios['debt_ratio'] = flt(total_liabilities / total_assets, 2)
        ratios['equity_ratio'] = flt(total_equity / total_assets, 2)
    else:
        ratios['debt_ratio'] = None
        ratios['equity_ratio'] = None
    
    # Profitability Ratios
    if total_assets > 0:
        ratios['roa'] = flt((net_income / total_assets) * 100, 2)
    else:
        ratios['roa'] = None
    
    if total_equity > 0:
        ratios['roe'] = flt((net_income / total_equity) * 100, 2)
    else:
        ratios['roe'] = None
    
    # Working Capital
    ratios['working_capital'] = flt(bs_summary.get('working_capital', 0))
    
    return ratios


def calculate_trust_specific_ratios(bs_data, pl_data, trust_type):
    """
    Calculate trust-specific ratios based on trust type
    
    Returns:
        Dictionary with trust-specific ratios
    """
    if not trust_type:
        return {}
    
    trust_type = trust_type.lower()
    
    if trust_type == 'charitable':
        return calculate_charitable_trust_ratios(bs_data, pl_data)
    elif trust_type == 'religious':
        return calculate_religious_trust_ratios(bs_data, pl_data)
    elif trust_type == 'business':
        return calculate_business_trust_ratios(bs_data, pl_data)
    
    return {}


def calculate_charitable_trust_ratios(bs_data, pl_data):
    """Calculate ratios specific to charitable trusts"""
    
    expense_data = pl_data.get('expense_data', {})
    income_data = pl_data.get('income_data', {})
    
    # Total expenses
    total_expenses = sum([cat.get('total', 0) for cat in expense_data.values()])
    total_income = sum([cat.get('total', 0) for cat in income_data.values()])
    
    # Program Efficiency Ratio (Program Expenses / Total Expenses)
    program_expenses = sum([
        cat.get('total', 0)
        for cat_name, cat in expense_data.items()
        if 'program' in cat_name.lower()
    ])
    
    program_efficiency = (program_expenses / total_expenses * 100) if total_expenses > 0 else 0
    
    # Fundraising Efficiency
    fundraising_expenses = sum([
        cat.get('total', 0)
        for cat_name, cat in expense_data.items()
        if 'fundraising' in cat_name.lower() or 'marketing' in cat_name.lower()
    ])
    
    fundraising_efficiency = (fundraising_expenses / total_income * 100) if total_income > 0 else 0
    
    # Corpus Ratio (Corpus / Annual Expenses)
    corpus_investments = sum([
        cat.get('total', 0)
        for cat_name, cat in bs_data.get('assets', {}).items()
        if 'corpus' in cat_name.lower() or 'investment' in cat_name.lower()
    ])
    
    corpus_ratio = (corpus_investments / total_expenses) if total_expenses > 0 else 0
    
    # Donation Dependency
    donation_income = sum([
        cat.get('total', 0)
        for cat_name, cat in income_data.items()
        if 'donation' in cat_name.lower() or 'grant' in cat_name.lower()
    ])
    
    donation_dependency = (donation_income / total_income * 100) if total_income > 0 else 0
    
    return {
        'program_efficiency_ratio': program_efficiency,
        'fundraising_efficiency': fundraising_efficiency,
        'corpus_ratio': corpus_ratio,
        'donation_dependency': donation_dependency
    }


def calculate_religious_trust_ratios(bs_data, pl_data):
    """Calculate ratios specific to religious trusts"""
    
    income_data = pl_data.get('income_data', {})
    expense_data = pl_data.get('expense_data', {})
    
    total_income = sum([cat.get('total', 0) for cat in income_data.values()])
    total_expenses = sum([cat.get('total', 0) for cat in expense_data.values()])
    
    # Self-Sustainability Ratio
    service_income = sum([
        cat.get('total', 0)
        for cat_name, cat in income_data.items()
        if any(keyword in cat_name.lower() for keyword in ['service', 'prasadam', 'sales', 'rent'])
    ])
    
    self_sustainability = (service_income / total_income * 100) if total_income > 0 else 0
    
    # Prasadam Margin
    prasadam_income = sum([
        cat.get('total', 0)
        for cat_name, cat in income_data.items()
        if 'prasadam' in cat_name.lower()
    ])
    
    prasadam_expense = sum([
        cat.get('total', 0)
        for cat_name, cat in expense_data.items()
        if 'prasadam' in cat_name.lower()
    ])
    
    prasadam_margin = ((prasadam_income - prasadam_expense) / prasadam_income * 100) if prasadam_income > 0 else 0
    
    # Temple Maintenance Ratio
    maintenance_expense = sum([
        cat.get('total', 0)
        for cat_name, cat in expense_data.items()
        if 'maintenance' in cat_name.lower() or 'repair' in cat_name.lower()
    ])
    
    maintenance_ratio = (maintenance_expense / total_expenses * 100) if total_expenses > 0 else 0
    
    return {
        'self_sustainability_ratio': self_sustainability,
        'prasadam_margin': prasadam_margin,
        'temple_maintenance_ratio': maintenance_ratio
    }


def calculate_business_trust_ratios(bs_data, pl_data):
    """Calculate ratios specific to business trusts"""
    
    income_data = pl_data.get('income_data', {})
    expense_data = pl_data.get('expense_data', {})
    
    total_revenue = sum([cat.get('total', 0) for cat in income_data.values()])
    
    # COGS
    cogs = sum([
        cat.get('total', 0)
        for cat_name, cat in expense_data.items()
        if 'cogs' in cat_name.lower() or 'cost of goods' in cat_name.lower()
    ])
    
    # Gross Profit Margin
    gross_profit = total_revenue - cogs
    gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Operating Expenses
    operating_expenses = sum([
        cat.get('total', 0)
        for cat_name, cat in expense_data.items()
        if 'operating' in cat_name.lower() or 'administrative' in cat_name.lower()
    ])
    
    # Operating Profit Margin
    operating_profit = gross_profit - operating_expenses
    operating_margin = (operating_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Inventory Turnover (simplified)
    inventory = sum([
        cat.get('total', 0)
        for cat_name, cat in bs_data.get('assets', {}).items()
        if 'inventory' in cat_name.lower()
    ])
    
    inventory_turnover = (cogs / inventory) if inventory > 0 else 0
    
    return {
        'gross_profit_margin': gross_margin,
        'operating_profit_margin': operating_margin,
        'inventory_turnover': inventory_turnover
    }

