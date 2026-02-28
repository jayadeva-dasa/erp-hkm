from hkm.cursor.fix_consolidated_pos_gst_20260211 import fix_consolidated_pos_invoice

def fix_glf():
    """Fix GLF-2602-0134"""
    result = fix_consolidated_pos_invoice("GLF-2602-0134", dry_run=False)
    return result

if __name__ == "__main__":
    fix_glf()
