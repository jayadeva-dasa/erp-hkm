import frappe
from hkm.erpnext___custom.supplier_verification_email import send_verification_email

frappe.init(site='hkmjerp.in')
frappe.connect()

print("\n" + "="*100)
print("Testing Disabled User Email Routing")
print("="*100)

# Test with a disabled user
disabled_user = "govind.chhabra@hkm-group.org"
result = send_verification_email(disabled_user, test_mode=True)

if result["success"]:
    print(f"\n✓ SUCCESS!")
    print(f"  Concerned Person: {disabled_user}")
    print(f"  User Status: {'DISABLED' if result.get('user_disabled') else 'ENABLED'}")
    print(f"  Email would be sent to: {'Vishnu Sharma (vishnu.sharma@hkmjaipur.org)' if result.get('user_disabled') else disabled_user}")
    print(f"  Test Mode Email Sent To: nrhd@hkmjaipur.org")
    print(f"  Supplier Count: {result['supplier_count']}")
else:
    print(f"\n✗ FAILED: {result['message']}")

print("="*100 + "\n")

frappe.db.commit()  # v16: REVIEW - check if needed
frappe.destroy()

