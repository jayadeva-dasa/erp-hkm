import frappe
from hkm.cursor.fix_consolidated_pos_gst_20260211 import fix_consolidated_pos_invoice

def check_failed():
    """Check why HKMA-2601-0269 failed"""
    result = fix_consolidated_pos_invoice("HKMA-2601-0269", dry_run=True)
    return result

if __name__ == "__main__":
    check_failed()
