#!/usr/bin/env python3
"""
Multiprocessing script to rename S3 file keys with standardized naming pattern

This script uses all available CPU cores to rename files in parallel.

Usage:
    bench --site hkmjerp.in execute hkm_jaipur.rename_s3_multiprocess.rename_all_parallel

Author: HKM Jaipur Development Team
"""

import os
import re
import random
import string
import frappe
from frappe import _
import multiprocessing as mp
from multiprocessing import Pool, Manager, Lock
import time
from datetime import datetime


def generate_random_suffix(length=6):
    """Generate a random alphanumeric suffix"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_new_s3_key(file_doc):
    """
    Generate new S3 key based on the standardized naming pattern with folder structure
    
    Pattern:
    - With doctype: {site_name}/{year}/{DocType}/{DocName} {FileName}-{Random6}.{ext}
    - Without doctype: {site_name}/{year}/Unspecified/{FileName}-{Random6}.{ext}
    """
    # Get site name
    site_name = frappe.local.site
    
    # Get file creation date to extract year
    creation_date = file_doc.creation or frappe.utils.now()
    
    # Extract 2-digit year
    if hasattr(creation_date, 'year'):
        year_2digit = str(creation_date.year)[-2:]
    else:
        from frappe.utils import getdate
        try:
            parsed_date = getdate(creation_date)
            year_2digit = str(parsed_date.year)[-2:]
        except:
            year_2digit = str(frappe.utils.now().year)[-2:]
    
    # Get file name and split into name and extension
    file_name = file_doc.file_name or "file"
    
    # Split filename and extension
    if '.' in file_name:
        name_parts = file_name.rsplit('.', 1)
        file_name_base = name_parts[0]
        file_extension = name_parts[1]
    else:
        file_name_base = file_name
        file_extension = ""
    
    # Generate random suffix (6 characters)
    random_suffix = generate_random_suffix()
    
    # Check if attached to a document
    if file_doc.attached_to_doctype and file_doc.attached_to_name:
        doctype = file_doc.attached_to_doctype
        docname = file_doc.attached_to_name
        
        if file_extension:
            s3_key = f"{site_name}/{year_2digit}/{doctype}/{docname} {file_name_base}-{random_suffix}.{file_extension}"
        else:
            s3_key = f"{site_name}/{year_2digit}/{doctype}/{docname} {file_name_base}-{random_suffix}"
    else:
        if file_extension:
            s3_key = f"{site_name}/{year_2digit}/Unspecified/{file_name_base}-{random_suffix}.{file_extension}"
        else:
            s3_key = f"{site_name}/{year_2digit}/Unspecified/{file_name_base}-{random_suffix}"
    
    return s3_key


def is_already_updated(s3_key):
    """Check if the S3 key is already in the new format"""
    if not s3_key:
        return True
    
    # New format pattern: site/year/doctype/filename or site/year/Unspecified/filename
    # Pattern has 3 slashes minimum
    parts = s3_key.split('/')
    if len(parts) >= 4:
        # Check if second part is a 2-digit year
        if len(parts[1]) == 2 and parts[1].isdigit():
            return True
    
    return False


def rename_single_file(file_id, site_name, stats_dict, lock):
    """
    Rename a single file's S3 key
    Worker function for multiprocessing
    """
    try:
        # Initialize Frappe for this process
        frappe.init(site=site_name)
        frappe.connect()
        
        # Get the file document
        file_doc = frappe.get_doc("File", file_id)
        
        # Check if already updated
        if is_already_updated(file_doc.dfp_external_storage_s3_key):
            with lock:
                stats_dict['skipped'] += 1
            return {"success": True, "skipped": True, "file_id": file_id}
        
        old_key = file_doc.dfp_external_storage_s3_key
        
        if not old_key:
            with lock:
                stats_dict['skipped'] += 1
            return {"success": True, "skipped": True, "file_id": file_id}
        
        # Get storage document
        storage_doc = file_doc.dfp_external_storage_doc
        if not storage_doc:
            with lock:
                stats_dict['failed'] += 1
            return {"success": False, "error": "Storage document not found", "file_id": file_id}
        
        # Generate new key
        new_key = generate_new_s3_key(file_doc)
        
        # Get client from storage doc
        client_wrapper = storage_doc.client
        if not client_wrapper:
            with lock:
                stats_dict['failed'] += 1
            return {"success": False, "error": "Could not get storage client", "file_id": file_id}
        
        # Get the underlying Minio client
        minio_client = client_wrapper.client
        bucket_name = storage_doc.bucket_name
        
        # Copy object to new key in S3 using Minio's copy_object
        from minio.commonconfig import CopySource
        
        copy_source = CopySource(bucket_name, old_key)
        
        minio_client.copy_object(
            bucket_name=bucket_name,
            object_name=new_key,
            source=copy_source
        )
        
        # Delete old key from S3
        client_wrapper.remove_object(
            bucket_name=bucket_name,
            object_name=old_key
        )
        
        # Update the file document in ERP
        file_doc.dfp_external_storage_s3_key = new_key
        
        # Update file_url if it contains the old key
        if file_doc.file_url and old_key in file_doc.file_url:
            file_doc.file_url = file_doc.file_url.replace(old_key, new_key)
        
        file_doc.save(ignore_permissions=True)
        frappe.db.commit()  # v16: REVIEW - check if needed
        
        with lock:
            stats_dict['success'] += 1
        
        return {
            "success": True,
            "old_key": old_key,
            "new_key": new_key,
            "file_id": file_id
        }
        
    except Exception as e:
        with lock:
            stats_dict['failed'] += 1
        
        error_msg = str(e)
        return {
            "success": False,
            "error": error_msg,
            "file_id": file_id
        }
    finally:
        frappe.destroy()


@frappe.whitelist()
def rename_all_parallel(num_processes=None):
    """
    Rename all S3 file keys using multiprocessing
    
    Args:
        num_processes: Number of processes to use (default: CPU count)
    """
    try:
        site_name = frappe.local.site
        
        # Determine number of processes
        if num_processes is None:
            num_processes = mp.cpu_count()
        
        print(f"\n{'='*60}")
        print(f"Starting Multiprocessing S3 Key Rename")
        print(f"{'='*60}")
        print(f"Site: {site_name}")
        print(f"Processes: {num_processes}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Get all files that need to be updated (not in new format)
        files = frappe.db.sql("""
            SELECT name 
            FROM tabFile 
            WHERE dfp_external_storage_s3_key != ''
            AND dfp_external_storage_s3_key IS NOT NULL
            AND (
                dfp_external_storage_s3_key NOT LIKE 'hkmjerp.in/__/%'
                OR dfp_external_storage_s3_key NOT REGEXP '^[^/]+/[0-9][0-9]/'
            )
        """, as_dict=True)
        
        file_ids = [f['name'] for f in files]
        total_files = len(file_ids)
        
        print(f"Found {total_files} files to update\n")
        
        if total_files == 0:
            print("No files to process!")
            return {"success": True, "total": 0, "processed": 0}
        
        # Create shared statistics dictionary
        manager = Manager()
        stats_dict = manager.dict()
        stats_dict['success'] = 0
        stats_dict['failed'] = 0
        stats_dict['skipped'] = 0
        lock = manager.Lock()
        
        # Create progress file
        progress_file = f"/tmp/s3_rename_progress_{site_name}.txt"
        
        # Start time
        start_time = time.time()
        
        # Create pool of workers
        pool = Pool(processes=num_processes)
        
        # Process files in parallel
        results = []
        for file_id in file_ids:
            result = pool.apply_async(
                rename_single_file,
                args=(file_id, site_name, stats_dict, lock)
            )
            results.append(result)
        
        # Monitor progress
        completed = 0
        last_update = 0
        
        while completed < total_files:
            completed = sum(1 for r in results if r.ready())
            
            # Update progress every 100 files or every 10 seconds
            current_time = time.time()
            if completed - last_update >= 100 or current_time - start_time > 10:
                elapsed = current_time - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                remaining = (total_files - completed) / rate if rate > 0 else 0
                
                progress_pct = (completed / total_files) * 100
                
                progress_msg = (
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"Progress: {completed}/{total_files} ({progress_pct:.1f}%) | "
                    f"Success: {stats_dict['success']} | "
                    f"Failed: {stats_dict['failed']} | "
                    f"Skipped: {stats_dict['skipped']} | "
                    f"Rate: {rate:.1f} files/sec | "
                    f"ETA: {remaining/60:.1f} min"
                )
                
                print(progress_msg)
                
                # Write to progress file
                with open(progress_file, 'w') as f:
                    f.write(progress_msg + '\n')
                
                last_update = completed
            
            time.sleep(1)
        
        # Close pool
        pool.close()
        pool.join()
        
        # Final statistics
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print(f"Bulk Rename Operation Completed!")
        print(f"{'='*60}")
        print(f"Total Files: {total_files}")
        print(f"Success: {stats_dict['success']}")
        print(f"Failed: {stats_dict['failed']}")
        print(f"Skipped: {stats_dict['skipped']}")
        print(f"Time Taken: {elapsed_time/60:.2f} minutes")
        print(f"Average Rate: {total_files/elapsed_time:.2f} files/sec")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "total": total_files,
            "processed": completed,
            "success_count": int(stats_dict['success']),
            "failed_count": int(stats_dict['failed']),
            "skipped_count": int(stats_dict['skipped']),
            "elapsed_time": elapsed_time
        }
        
    except Exception as e:
        error_msg = f"Error during bulk rename: {str(e)}"
        print(f"\n❌ {error_msg}\n")
        frappe.log_error(title="Multiprocess S3 rename error", message=str(e))
        
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Command line interface"""
    print("DFP External Storage S3 Key Rename Tool (Multiprocessing)")
    print("=" * 60)
    print()
    print("Usage:")
    print("  bench --site hkmjerp.in execute hkm_jaipur.rename_s3_multiprocess.rename_all_parallel")
    print()


if __name__ == "__main__":
    main()

