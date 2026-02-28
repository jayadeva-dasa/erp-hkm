#!/usr/bin/env python3
"""
Find failed file IDs from S3 rename operation

This script identifies which files failed to be renamed during the S3 key rename operation.

Usage:
    bench --site erp.hkmkota.org execute hkm.cursor.find_failed_files.find_failed_file_ids

Author: HKM Development Team
"""

import frappe
from frappe import _


@frappe.whitelist()
def find_failed_file_ids():
    """
    Find file IDs that failed to be renamed during the S3 rename operation
    """
    try:
        print("\n" + "="*70)
        print("Finding Failed S3 Rename File IDs")
        print("="*70)

        # Query for files that still have old S3 key format
        # These are the files that should have been renamed but weren't
        failed_files = frappe.db.sql("""
            SELECT
                name,
                file_name,
                dfp_external_storage_s3_key,
                attached_to_doctype,
                attached_to_name,
                creation
            FROM tabFile
            WHERE dfp_external_storage_s3_key != ''
            AND dfp_external_storage_s3_key IS NOT NULL
            AND (
                dfp_external_storage_s3_key NOT LIKE 'erp.hkmkota.org/__/%'
                OR dfp_external_storage_s3_key NOT REGEXP '^[^/]+/[0-9][0-9]/'
            )
            ORDER BY creation DESC
        """, as_dict=True)

        total_failed = len(failed_files)

        print(f"\nFound {total_failed} failed files that still need to be renamed:")
        print("-" * 70)

        if total_failed > 0:
            # Print first 20 failed files as examples
            for i, file_doc in enumerate(failed_files[:20], 1):
                print(f"{i:2d}. ID: {file_doc.name}")
                print(f"    File: {file_doc.file_name}")
                print(f"    S3 Key: {file_doc.dfp_external_storage_s3_key}")
                print(f"    DocType: {file_doc.attached_to_doctype or 'None'}")
                print(f"    DocName: {file_doc.attached_to_name or 'None'}")
                print(f"    Created: {file_doc.creation}")
                print()

            if total_failed > 20:
                print(f"... and {total_failed - 20} more files")
                print()

            # Group by doctype for summary
            doctype_counts = {}
            for file_doc in failed_files:
                doctype = file_doc.attached_to_doctype or 'Unspecified'
                doctype_counts[doctype] = doctype_counts.get(doctype, 0) + 1

            print("Summary by DocType:")
            print("-" * 30)
            for doctype, count in sorted(doctype_counts.items(), key=lambda x: x[1], reverse=True):
                print("15")

            # Save detailed list to a file for reference
            output_file = "/tmp/failed_s3_rename_files.txt"
            with open(output_file, 'w') as f:
                f.write("Failed S3 Rename Files\n")
                f.write("="*50 + "\n\n")
                f.write(f"Total Failed: {total_failed}\n\n")

                for file_doc in failed_files:
                    f.write(f"ID: {file_doc.name}\n")
                    f.write(f"File: {file_doc.file_name}\n")
                    f.write(f"S3 Key: {file_doc.dfp_external_storage_s3_key}\n")
                    f.write(f"DocType: {file_doc.attached_to_doctype or 'None'}\n")
                    f.write(f"DocName: {file_doc.attached_to_name or 'None'}\n")
                    f.write(f"Created: {file_doc.creation}\n")
                    f.write("-" * 40 + "\n")

            print(f"\nDetailed list saved to: {output_file}")

        else:
            print("No failed files found! All files appear to have been renamed successfully.")

        print("="*70)

        return {
            "success": True,
            "total_failed": total_failed,
            "failed_file_ids": [f.name for f in failed_files],
            "summary": {
                doctype: count for doctype, count in doctype_counts.items()
            } if total_failed > 0 else {}
        }

    except Exception as e:
        error_msg = f"Error finding failed files: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        frappe.log_error(title="Find failed S3 files error", message=str(e))

        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Command line interface"""
    print("Find Failed S3 Rename Files Tool")
    print("=" * 40)
    print()
    print("Usage:")
    print("  bench --site erp.hkmkota.org execute hkm.cursor.find_failed_files.find_failed_file_ids")
    print()


if __name__ == "__main__":
    main()
