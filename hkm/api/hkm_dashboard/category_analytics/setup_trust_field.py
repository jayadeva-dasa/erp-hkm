"""
Setup script to add trust_type field to Company
Run in bench console or via: bench --site hkmjerp.in execute hkm_jaipur.api.category_analytics.setup_trust_field.setup
"""

import frappe


def setup():
    """Add trust_type field to Company DocType and set values"""
    
    # Check if field already exists
    existing_field = frappe.db.exists('Custom Field', {
        'dt': 'Company',
        'fieldname': 'trust_type'
    })
    
    if not existing_field:
        # Create custom field
        custom_field = frappe.get_doc({
            'doctype': 'Custom Field',
            'dt': 'Company',
            'fieldname': 'trust_type',
            'label': 'Trust Type',
            'fieldtype': 'Select',
            'options': '\nCharitable\nReligious\nBusiness',
            'insert_after': 'company_name',
            'description': 'Type of trust/organization for specialized financial analysis'
        })
        custom_field.insert(ignore_permissions=True)
        frappe.db.commit()  # v16: REVIEW - check if needed
        print("✅ Created trust_type field in Company DocType")
    else:
        print("ℹ️  trust_type field already exists")
    
    # Set trust types for the three companies
    trust_mappings = {
        'Hare Krishna Movement Jaipur': 'Charitable',
        'Radha Krishna Mandir': 'Religious',
        'Touchstone Foundation': 'Business'
    }
    
    for company, trust_type in trust_mappings.items():
        if frappe.db.exists('Company', company):
            frappe.db.set_value('Company', company, 'trust_type', trust_type)
            print(f"✅ Set {company} as {trust_type} Trust")
        else:
            print(f"⚠️  Company '{company}' not found")
    
    frappe.db.commit()  # v16: REVIEW - check if needed
    print("\n✅ Trust type setup complete!")
    
    # Display current status
    print("\n📊 Current Trust Types:")
    companies = frappe.get_all('Company', fields=['name', 'trust_type'])
    for company in companies:
        trust_type = company.trust_type or 'Not Set'
        icon = {'Charitable': '🤲', 'Religious': '🕉️', 'Business': '💼'}.get(trust_type, '❓')
        print(f"  {icon} {company.name}: {trust_type}")
    
    return "Setup complete"




