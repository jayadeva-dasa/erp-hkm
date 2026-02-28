"""
File Management Operations for hkmerp.in
Wrapper functions that reference hkm_jaipur scripts
"""

import frappe
import sys
import os

# Add hkm_jaipur to path so we can import its modules
bench_path = frappe.utils.get_bench_path()
hkm_jaipur_path = os.path.join(bench_path, 'apps', 'hkm_jaipur', 'hkm_jaipur')
if hkm_jaipur_path not in sys.path:
    sys.path.insert(0, hkm_jaipur_path)


@frappe.whitelist()
def validate_references_dry_run():
    """Validate and fix file references - DRY RUN"""
    frappe.only_for("System Manager")
    from cursor.validate_and_fix_references import run_dry_run
    return run_dry_run()


@frappe.whitelist()
def validate_references_live():
    """Validate and fix file references - LIVE RUN"""
    frappe.only_for("System Manager")
    from cursor.validate_and_fix_references import run_live
    return run_live()


@frappe.whitelist()
def fix_broken_references_dry_run():
    """Fix broken file references - DRY RUN"""
    frappe.only_for("System Manager")
    from cursor.fix_broken_file_references import run_dry_run
    return run_dry_run()


@frappe.whitelist()
def fix_broken_references_live():
    """Fix broken file references - LIVE RUN"""
    frappe.only_for("System Manager")
    from cursor.fix_broken_file_references import run_live
    return run_live()


@frappe.whitelist()
def fix_library_duplicates_dry_run():
    """Fix library file duplicates - DRY RUN"""
    frappe.only_for("System Manager")
    from cursor.fix_library_file_duplicates import run_dry_run
    return run_dry_run()


@frappe.whitelist()
def fix_library_duplicates_live():
    """Fix library file duplicates - LIVE RUN"""
    frappe.only_for("System Manager")
    from cursor.fix_library_file_duplicates import run_live
    return run_live()


@frappe.whitelist()
def recover_old_pattern_files_dry_run():
    """Recover all old pattern files - DRY RUN"""
    frappe.only_for("System Manager")
    from cursor.recover_all_old_pattern_files_complete import run_dry_run
    return run_dry_run()


@frappe.whitelist()
def recover_old_pattern_files_live():
    """Recover all old pattern files - LIVE RUN"""
    frappe.only_for("System Manager")
    from cursor.recover_all_old_pattern_files_complete import run_live
    return run_live()


@frappe.whitelist()
def final_audit():
    """Run final audit"""
    frappe.only_for("System Manager")
    from cursor.final_audit_kota import run_audit
    return run_audit()

