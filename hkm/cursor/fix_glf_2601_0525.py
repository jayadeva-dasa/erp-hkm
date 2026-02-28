from hkm.cursor.fix_consolidated_pos_gst_20260211 import fix_consolidated_pos_invoice

def fix_invoice():
    """Fix GLF-2601-0525"""
    result = fix_consolidated_pos_invoice("GLF-2601-0525", dry_run=False)
    return result

if __name__ == "__main__":
    fix_invoice()
