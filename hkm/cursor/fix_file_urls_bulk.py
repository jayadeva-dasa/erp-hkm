#!/usr/bin/env python3
"""
Bulk fix file_url for files where file_id doesn't match the URL

This script identifies and fixes File documents where:
1. dfp_external_storage_s3_key is set (S3 files only)
2. file_url follows pattern /file/{file_id}/{file_name}
3. file_id in URL doesn't match the actual File document name

Usage:
    # Test with one file first
    bench --site erp.hkmkota.org execute hkm.cursor.fix_file_urls_bulk.fix_one_file
    
    # After verification, fix all files
    bench --site erp.hkmkota.org execute hkm.cursor.fix_file_urls_bulk.fix_all_files

Author: HKM Development Team
"""

import frappe
from frappe import _
import re


def get_files_with_wrong_url():
    """
    Get all files where file_url has wrong file_id
    
    Returns:
        list: List of file documents with wrong URLs
    """
    # Get all files with S3 keys and file_url matching the pattern
    files = frappe.db.sql("""
        SELECT 
            name,
            file_name,
            file_url,
            attached_to_doctype,
            attached_to_name,
            attached_to_field,
            dfp_external_storage_s3_key
        FROM tabFile
        WHERE dfp_external_storage_s3_key IS NOT NULL
        AND dfp_external_storage_s3_key != ''
        AND file_url LIKE '/file/%'
        ORDER BY creation DESC
    """, as_dict=True)
    
    wrong_files = []
    dfp_file_url_pattern = r"^/file/([^/]+)/(.+)$"
    
    for file_doc in files:
        match = re.match(dfp_file_url_pattern, file_doc.file_url)
        if match:
            file_id_in_url = match.group(1)
            # Check if file_id in URL doesn't match the actual file name
            if file_id_in_url != file_doc.name:
                file_doc['file_id_in_url'] = file_id_in_url
                wrong_files.append(file_doc)
    
    return wrong_files


@frappe.whitelist()
def fix_one_file():
    """
    Fix one file as a test - finds the first file with wrong URL and fixes it
    """
    try:
        print(f"\n{'='*70}")
        print("Testing File URL Fix - Single File")
        print(f"{'='*70}\n")
        
        # Get files with wrong URLs
        wrong_files = get_files_with_wrong_url()
        
        if not wrong_files:
            print("✅ No files found with incorrect file_url!")
            print("All files are already correct.\n")
            return {
                "success": True,
                "message": "No files need fixing"
            }
        
        print(f"Found {len(wrong_files)} files with incorrect file_url\n")
        print("Testing with first file...\n")
        
        # Get the first file
        file_data = wrong_files[0]
        
        print(f"File Details:")
        print(f"{'='*70}")
        print(f"File ID: {file_data.name}")
        print(f"File Name: {file_data.file_name}")
        print(f"Current URL: {file_data.file_url}")
        print(f"File ID in URL: {file_data.file_id_in_url} ❌ (wrong)")
        print(f"Attached To: {file_data.attached_to_doctype} - {file_data.attached_to_name}")
        print(f"Attached Field: {file_data.attached_to_field or 'None'}")
        print(f"S3 Key: {file_data.dfp_external_storage_s3_key}")
        print(f"{'='*70}\n")
        
        # Generate correct file_url
        new_file_url = f"/file/{file_data.name}/{file_data.file_name}"
        
        print(f"Proposed Fix:")
        print(f"  Old URL: {file_data.file_url}")
        print(f"  New URL: {new_file_url} ✓")
        print()
        
        # Update the file document
        print("Updating File document...")
        frappe.db.set_value(
            "File",
            file_data.name,
            "file_url",
            new_file_url,
            update_modified=False
        )
        print("✅ File document updated")
        
        # Update attached document field if exists
        if file_data.attached_to_doctype and file_data.attached_to_name and file_data.attached_to_field:
            print(f"\nUpdating attached document field...")
            print(f"  DocType: {file_data.attached_to_doctype}")
            print(f"  DocName: {file_data.attached_to_name}")
            print(f"  Field: {file_data.attached_to_field}")
            
            try:
                # Check if the field value matches the old URL
                current_field_value = frappe.db.get_value(
                    file_data.attached_to_doctype,
                    file_data.attached_to_name,
                    file_data.attached_to_field
                )
                
                if current_field_value == file_data.file_url:
                    frappe.db.set_value(
                        file_data.attached_to_doctype,
                        file_data.attached_to_name,
                        file_data.attached_to_field,
                        new_file_url,
                        update_modified=False
                    )
                    print("✅ Attached document field updated")
                else:
                    print(f"ℹ️  Field value doesn't match old URL, skipping field update")
                    print(f"  Current value: {current_field_value}")
            except Exception as e:
                print(f"⚠️  Could not update attached field: {str(e)}")
        else:
            print("\nℹ️  No attached field to update")
        
        frappe.db.commit()  # v16: REVIEW - check if needed
        
        print(f"\n{'='*70}")
        print("✅ Test Fix Completed Successfully!")
        print(f"{'='*70}")
        print(f"\nPlease verify:")
        print(f"1. Open document: {file_data.attached_to_doctype} - {file_data.attached_to_name}")
        print(f"2. Check if attachment is accessible")
        print(f"3. Try to download/view the file")
        print(f"\nIf everything works, run: fix_all_files()")
        print(f"{'='*70}\n")
        
        return {
            "success": True,
            "file_id": file_data.name,
            "old_url": file_data.file_url,
            "new_url": new_file_url,
            "attached_to": f"{file_data.attached_to_doctype} - {file_data.attached_to_name}",
            "total_files_needing_fix": len(wrong_files)
        }
        
    except Exception as e:
        error_msg = f"Error fixing file: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        frappe.log_error(title="Fix file URL error", message=str(e))
        frappe.db.rollback()
        
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def fix_all_files():
    """
    Fix all files with incorrect file_url
    """
    try:
        print(f"\n{'='*70}")
        print("Bulk Fix File URLs - All Files")
        print(f"{'='*70}\n")
        
        # Get files with wrong URLs
        wrong_files = get_files_with_wrong_url()
        
        if not wrong_files:
            print("✅ No files found with incorrect file_url!")
            print("All files are already correct.\n")
            return {
                "success": True,
                "message": "No files need fixing",
                "total": 0,
                "fixed": 0
            }
        
        total_files = len(wrong_files)
        print(f"Found {total_files} files with incorrect file_url\n")
        print("Starting bulk fix...\n")
        
        fixed_count = 0
        failed_count = 0
        failed_files = []
        
        for idx, file_data in enumerate(wrong_files, 1):
            try:
                # Generate correct file_url
                new_file_url = f"/file/{file_data.name}/{file_data.file_name}"
                
                # Update the file document
                frappe.db.set_value(
                    "File",
                    file_data.name,
                    "file_url",
                    new_file_url,
                    update_modified=False
                )
                
                # Update attached document field if exists
                if file_data.attached_to_doctype and file_data.attached_to_name and file_data.attached_to_field:
                    try:
                        # Check if the field value matches the old URL
                        current_field_value = frappe.db.get_value(
                            file_data.attached_to_doctype,
                            file_data.attached_to_name,
                            file_data.attached_to_field
                        )
                        
                        if current_field_value == file_data.file_url:
                            frappe.db.set_value(
                                file_data.attached_to_doctype,
                                file_data.attached_to_name,
                                file_data.attached_to_field,
                                new_file_url,
                                update_modified=False
                            )
                    except Exception:
                        # Field update failed, but file URL is fixed
                        pass
                
                fixed_count += 1
                
                # Progress update every 10 files
                if idx % 10 == 0 or idx == total_files:
                    progress_pct = (idx / total_files) * 100
                    print(f"Progress: {idx}/{total_files} ({progress_pct:.1f}%) | Fixed: {fixed_count} | Failed: {failed_count}")
                
            except Exception as e:
                failed_count += 1
                failed_files.append({
                    "file_id": file_data.name,
                    "error": str(e)
                })
                print(f"❌ Failed to fix {file_data.name}: {str(e)}")
        
        frappe.db.commit()  # v16: REVIEW - check if needed
        
        print(f"\n{'='*70}")
        print("Bulk Fix Completed!")
        print(f"{'='*70}")
        print(f"Total Files: {total_files}")
        print(f"Fixed: {fixed_count}")
        print(f"Failed: {failed_count}")
        print(f"{'='*70}\n")
        
        if failed_files:
            print("Failed Files:")
            for failed in failed_files[:10]:  # Show first 10
                print(f"  - {failed['file_id']}: {failed['error']}")
            if len(failed_files) > 10:
                print(f"  ... and {len(failed_files) - 10} more")
            print()
        
        return {
            "success": True,
            "total": total_files,
            "fixed": fixed_count,
            "failed": failed_count,
            "failed_files": failed_files
        }
        
    except Exception as e:
        error_msg = f"Error during bulk fix: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        frappe.log_error(title="Bulk fix file URLs error", message=str(e))
        frappe.db.rollback()
        
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def check_files_status():
    """
    Check how many files need fixing without making any changes
    """
    try:
        print(f"\n{'='*70}")
        print("File URL Status Check")
        print(f"{'='*70}\n")
        
        # Get all S3 files
        total_s3_files = frappe.db.count("File", {
            "dfp_external_storage_s3_key": ["!=", ""]
        })
        
        print(f"Total S3 Files: {total_s3_files}")
        
        # Get files with wrong URLs
        wrong_files = get_files_with_wrong_url()
        wrong_count = len(wrong_files)
        
        print(f"Files with Wrong URL: {wrong_count}")
        print(f"Files with Correct URL: {total_s3_files - wrong_count}")
        print()
        
        if wrong_count > 0:
            print("Sample of files needing fix (first 5):")
            print(f"{'='*70}")
            for file_data in wrong_files[:5]:
                print(f"File ID: {file_data.name}")
                print(f"  Current URL: {file_data.file_url}")
                print(f"  Should be: /file/{file_data.name}/{file_data.file_name}")
                print(f"  Attached to: {file_data.attached_to_doctype} - {file_data.attached_to_name}")
                print()
        
        print(f"{'='*70}\n")
        
        return {
            "success": True,
            "total_s3_files": total_s3_files,
            "files_needing_fix": wrong_count,
            "files_correct": total_s3_files - wrong_count
        }
        
    except Exception as e:
        error_msg = f"Error checking status: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Command line interface"""
    print("File URL Bulk Fix Tool")
    print("=" * 70)
    print()
    print("Available commands:")
    print("  1. Check status:")
    print("     bench --site erp.hkmkota.org execute hkm.cursor.fix_file_urls_bulk.check_files_status")
    print()
    print("  2. Fix one file (test):")
    print("     bench --site erp.hkmkota.org execute hkm.cursor.fix_file_urls_bulk.fix_one_file")
    print()
    print("  3. Fix all files:")
    print("     bench --site erp.hkmkota.org execute hkm.cursor.fix_file_urls_bulk.fix_all_files")
    print()


if __name__ == "__main__":
    main()

