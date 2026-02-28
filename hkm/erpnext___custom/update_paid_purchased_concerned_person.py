#!/usr/bin/env python3
"""
Update concerned_person for "Paid & Purchased" suppliers

Maps supplier prefix to corresponding user email:
- "NRHD - Paid & Purchased" -> nrhd@hkmjaipur.org
- "AJAD - Paid & Purchased" -> ajad@hkmjaipur.org
- etc.
"""

import frappe
import re


def get_user_email_from_prefix(prefix):
    """
    Convert supplier prefix to user email
    
    Args:
        prefix: Department code or name (e.g., "NRHD", "AJAD", "Ankit Sharma")
    
    Returns:
        User email if found, None otherwise
    """
    
    # Clean prefix
    prefix = prefix.strip()
    
    # Pattern 1: Department codes (NRHD, AJAD, etc.)
    # Convert to lowercase and add @hkmjaipur.org
    dept_code_pattern = r'^[A-Z]{3,5}D?$'
    if re.match(dept_code_pattern, prefix):
        email = f"{prefix.lower()}@hkmjaipur.org"
        if frappe.db.exists("User", {"name": email, "enabled": 1}):
            return email
    
    # Pattern 2: Full names like "Ankit Sharma(civil)"
    # Remove anything in parentheses and convert to firstname.lastname
    name_clean = re.sub(r'\([^)]*\)', '', prefix).strip()
    
    # Try firstname.lastname@hkmjaipur.org
    if ' ' in name_clean:
        parts = name_clean.lower().split()
        if len(parts) >= 2:
            email_variations = [
                f"{parts[0]}.{parts[1]}@hkmjaipur.org",  # first.last
                f"{parts[0]}.{parts[-1]}@hkmjaipur.org",  # first.last (if middle name)
                f"{'.'.join(parts)}@hkmjaipur.org",  # all parts
            ]
            
            for email in email_variations:
                if frappe.db.exists("User", {"name": email, "enabled": 1}):
                    return email
    
    # Pattern 3: Try direct email
    email = f"{prefix.lower().replace(' ', '.')}@hkmjaipur.org"
    if frappe.db.exists("User", {"name": email, "enabled": 1}):
        return email
    
    return None


def update_paid_purchased_suppliers():
    """Update concerned_person for all Paid & Purchased suppliers"""
    
    frappe.init(site='hkmjerp.in')
    frappe.connect()
    frappe.local.lang = frappe.db.get_default("lang") or 'en'
    
    try:
        # Get all Paid & Purchased suppliers
        suppliers = frappe.db.sql("""
            SELECT 
                name,
                supplier_name,
                custom_concerned_person
            FROM tabSupplier
            WHERE supplier_name LIKE '%Paid%Purchased%'
                OR supplier_name LIKE '%Paid & Purchased%'
            ORDER BY supplier_name
        """, as_dict=1)
        
        print(f"\n{'='*100}")
        print(f"Updating Concerned Person for Paid & Purchased Suppliers")
        print(f"{'='*100}")
        print(f"Total Suppliers Found: {len(suppliers)}\n")
        
        updated_count = 0
        skipped_count = 0
        no_match_count = 0
        
        results = {
            "updated": [],
            "skipped": [],
            "no_match": []
        }
        
        for supplier in suppliers:
            # Extract prefix from supplier name
            # Patterns:
            # 1. "NRHD - Paid & Purchased" -> NRHD
            # 2. "Ankit Sharma(civil)-Paid & Purchased" -> Ankit Sharma(civil)
            # 3. "Folk Dormitory - Paid & Purchased" -> Folk Dormitory
            
            prefix = None
            
            # Try " - Paid" split first
            if " - Paid" in supplier.supplier_name:
                prefix = supplier.supplier_name.split(" - Paid")[0].strip()
            # Try "-Paid" (no space)
            elif "-Paid" in supplier.supplier_name:
                prefix = supplier.supplier_name.split("-Paid")[0].strip()
            # Try " Paid" (space but no dash)
            elif " Paid" in supplier.supplier_name:
                prefix = supplier.supplier_name.split(" Paid")[0].strip()
            
            if not prefix:
                print(f"⚠️  Skipped {supplier.supplier_name}: Could not extract prefix")
                results["no_match"].append(supplier.supplier_name)
                no_match_count += 1
                continue
            
            # Get user email from prefix
            user_email = get_user_email_from_prefix(prefix)
            
            if not user_email:
                print(f"⚠️  No match for {supplier.supplier_name} (prefix: {prefix})")
                results["no_match"].append(f"{supplier.supplier_name} (prefix: {prefix})")
                no_match_count += 1
                continue
            
            # Check if already set to this user
            if supplier.custom_concerned_person == user_email:
                print(f"-  Skipped {supplier.supplier_name}: Already set to {user_email}")
                results["skipped"].append(supplier.supplier_name)
                skipped_count += 1
                continue
            
            # Update the concerned person
            frappe.db.set_value(
                "Supplier",
                supplier.name,
                "custom_concerned_person",
                user_email,
                update_modified=False
            )
            
            print(f"✓  Updated {supplier.supplier_name}")
            print(f"   Prefix: {prefix} -> Email: {user_email}")
            print(f"   Old: {supplier.custom_concerned_person or 'None'} -> New: {user_email}\n")
            
            results["updated"].append({
                "supplier": supplier.supplier_name,
                "prefix": prefix,
                "email": user_email,
                "old": supplier.custom_concerned_person
            })
            updated_count += 1
        
        # Commit changes
        frappe.db.commit()  # v16: OK - utility script
        
        print(f"\n{'='*100}")
        print(f"Summary:")
        print(f"  Total Suppliers: {len(suppliers)}")
        print(f"  Updated: {updated_count}")
        print(f"  Skipped (already correct): {skipped_count}")
        print(f"  No Match Found: {no_match_count}")
        print(f"{'='*100}\n")
        
        # Show detailed results
        if results["updated"]:
            print(f"\n{'='*100}")
            print(f"Updated Suppliers ({len(results['updated'])}):")
            print(f"{'='*100}")
            for item in results["updated"]:
                print(f"  {item['supplier']}")
                print(f"    Prefix: {item['prefix']} -> Email: {item['email']}")
                print(f"    Old: {item['old'] or 'None'}\n")
        
        if results["no_match"]:
            print(f"\n{'='*100}")
            print(f"No Match Found ({len(results['no_match'])}):")
            print(f"{'='*100}")
            for item in results["no_match"]:
                print(f"  {item}")
        
        return results
        
    except Exception as e:
        frappe.db.rollback()
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        frappe.destroy()


if __name__ == "__main__":
    update_paid_purchased_suppliers()

