"""
Update trust types for the correct company names
"""

import frappe


def update():
    """Update trust types based on actual company names"""
    
    trust_mappings = {
        'Hare Krishna Movement Jaipur': 'Charitable',
        'Sri Radha Krishna Mandir Foundation': 'Religious',  # Updated name
        'Touchstone Foundation Jaipur': 'Business'  # Updated name
    }
    
    print("\n📊 Updating Trust Types:")
    for company, trust_type in trust_mappings.items():
        if frappe.db.exists('Company', company):
            frappe.db.set_value('Company', company, 'trust_type', trust_type)
            icon = {'Charitable': '🤲', 'Religious': '🕉️', 'Business': '💼'}.get(trust_type)
            print(f"  {icon} {company} → {trust_type} Trust")
        else:
            print(f"  ⚠️  Company '{company}' not found")
    
    frappe.db.commit()  # v16: OK - utility script
    print("\n✅ Trust types updated!")
    
    # Display all companies with trust types
    print("\n📋 All Companies:")
    companies = frappe.get_all('Company', fields=['name', 'trust_type'], order_by='name')
    for company in companies:
        trust_type = company.trust_type or 'Not Set'
        icon = {'Charitable': '🤲', 'Religious': '🕉️', 'Business': '💼'}.get(trust_type, '❓')
        print(f"  {icon} {company.name}: {trust_type}")
    
    return "Update complete"




