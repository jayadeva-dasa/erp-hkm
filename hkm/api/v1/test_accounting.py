# Copyright (c) 2025, HKM and contributors
# For license information, please see license.txt

import frappe

def test_get_doctypes_with_accounting_dimensions():
    """Test function to verify our API endpoint works correctly."""
    try:
        # Direct call to our function
        result = frappe.call("hkm.api.v1.accounting.get_doctypes_with_accounting_dimensions")
        print("Result:", result)
        
        if result.get("success"):
            print("Successfully fetched doctypes with accounting dimensions:")
            for doctype in result.get("data", []):
                print(f"  - {doctype}")
        else:
            print("Error:", result.get("error"))
            
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        frappe.log_error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_get_doctypes_with_accounting_dimensions()