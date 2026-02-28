#!/usr/bin/env python3
"""
S3 File Search API

Provides API endpoints for searching and browsing files in S3 bucket

Usage:
    Called from HKM Dashboard React app

Author: HKM Development Team
"""

import frappe
from frappe import _
import re
from datetime import datetime
from typing import Dict, List, Optional


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_date(date_obj) -> str:
    """Format date in human-readable format"""
    if not date_obj:
        return ""
    
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(date_obj)


def get_file_type_category(file_type: str) -> str:
    """Categorize file type"""
    if file_type.startswith('image/'):
        return 'image'
    elif file_type == 'application/pdf':
        return 'pdf'
    elif file_type.startswith('video/'):
        return 'video'
    elif 'spreadsheet' in file_type or 'excel' in file_type:
        return 'spreadsheet'
    elif 'document' in file_type or 'word' in file_type:
        return 'document'
    else:
        return 'other'


@frappe.whitelist()
def search_s3_files(
    search_term: Optional[str] = None,
    file_type: Optional[str] = None,
    size_min: Optional[float] = None,
    size_max: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    folder_path: Optional[str] = None
) -> Dict:
    """
    Search files in S3 bucket
    
    Args:
        search_term: Search term for file name
        file_type: Filter by file type category
        size_min: Minimum file size in MB
        size_max: Maximum file size in MB
        date_from: Filter files modified after this date
        date_to: Filter files modified before this date
        folder_path: Filter by folder path
        
    Returns:
        Dict with search results
    """
    try:
        # Get DFP External Storage configuration
        storage_doc = frappe.get_doc("DFP External Storage", "DFP.ES.hkmjaipur.240628.271012")
        
        if not storage_doc:
            frappe.throw(_("DFP External Storage not configured"))
        
        # Get Minio client
        client = storage_doc.client.client
        bucket_name = storage_doc.bucket_name
        
        # List all objects in bucket
        objects = client.list_objects(bucket_name, recursive=True)
        
        files = []
        total_count = 0
        
        # Convert size limits from MB to bytes
        size_min_bytes = int(size_min * 1024 * 1024) if size_min else None
        size_max_bytes = int(size_max * 1024 * 1024) if size_max else None
        
        # Parse date filters
        date_from_obj = datetime.fromisoformat(date_from) if date_from else None
        date_to_obj = datetime.fromisoformat(date_to) if date_to else None
        
        for obj in objects:
            total_count += 1
            
            # Extract file info
            file_key = obj.object_name
            file_name = file_key.split('/')[-1]
            file_size = obj.size
            last_modified = obj.last_modified
            
            # Get file extension and type
            file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
            
            # Guess file type
            import mimetypes
            file_type_guess, _ = mimetypes.guess_type(file_name)
            if not file_type_guess:
                file_type_guess = 'application/octet-stream'
            
            # Extract folder path
            folder_parts = file_key.split('/')[:-1]
            folder = '/'.join(folder_parts) if folder_parts else '/'
            
            # Apply filters
            
            # Search term filter
            if search_term and search_term.lower() not in file_name.lower():
                continue
            
            # File type filter
            if file_type:
                file_category = get_file_type_category(file_type_guess)
                if file_category != file_type:
                    continue
            
            # Size filters
            if size_min_bytes and file_size < size_min_bytes:
                continue
            if size_max_bytes and file_size > size_max_bytes:
                continue
            
            # Date filters
            if date_from_obj and last_modified < date_from_obj:
                continue
            if date_to_obj and last_modified > date_to_obj:
                continue
            
            # Folder path filter
            if folder_path and not folder.startswith(folder_path):
                continue
            
            # Generate presigned URL for file access
            try:
                from datetime import timedelta
                file_url = client.presigned_get_object(
                    bucket_name,
                    file_key,
                    expires=timedelta(hours=1)  # 1 hour
                )
            except:
                file_url = f"/api/method/hkm.cursor.s3_file_search.get_s3_file_url?file_key={file_key}"
            
            # Add to results
            files.append({
                "key": file_key,
                "file_name": file_name,
                "size": file_size,
                "size_formatted": format_size(file_size),
                "last_modified": last_modified.isoformat() if last_modified else None,
                "last_modified_formatted": format_date(last_modified),
                "url": file_url,
                "file_type": file_type_guess,
                "folder_path": folder,
            })
        
        return {
            "success": True,
            "files": files,
            "total_count": total_count,
            "filtered_count": len(files),
            "search_term": search_term,
        }
        
    except Exception as e:
        frappe.log_error(title="S3 File Search Error", message=str(e))
        return {
            "success": False,
            "files": [],
            "total_count": 0,
            "filtered_count": 0,
            "error": str(e),
        }


@frappe.whitelist()
def get_s3_stats() -> Dict:
    """
    Get S3 bucket statistics
    
    Returns:
        Dict with bucket stats
    """
    try:
        # Get DFP External Storage configuration
        storage_doc = frappe.get_doc("DFP External Storage", "DFP.ES.hkmjaipur.240628.271012")
        
        if not storage_doc:
            frappe.throw(_("DFP External Storage not configured"))
        
        # Get Minio client
        client = storage_doc.client.client
        bucket_name = storage_doc.bucket_name
        
        # List all objects
        objects = client.list_objects(bucket_name, recursive=True)
        
        total_files = 0
        total_size = 0
        file_types = {}
        
        for obj in objects:
            total_files += 1
            total_size += obj.size
            
            # Get file type
            file_name = obj.object_name.split('/')[-1]
            import mimetypes
            file_type_guess, _ = mimetypes.guess_type(file_name)
            if not file_type_guess:
                file_type_guess = 'application/octet-stream'
            
            category = get_file_type_category(file_type_guess)
            file_types[category] = file_types.get(category, 0) + 1
        
        return {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_formatted": format_size(total_size),
            "file_types": file_types,
        }
        
    except Exception as e:
        frappe.log_error(title="S3 Stats Error", message=str(e))
        return {
            "total_files": 0,
            "total_size": 0,
            "total_size_formatted": "0 B",
            "file_types": {},
            "error": str(e),
        }


@frappe.whitelist()
def get_s3_file_url(file_key: str) -> str:
    """
    Get presigned URL for S3 file
    
    Args:
        file_key: S3 object key
        
    Returns:
        Presigned URL
    """
    try:
        storage_doc = frappe.get_doc("DFP External Storage", "DFP.ES.hkmjaipur.240628.271012")
        client = storage_doc.client.client
        bucket_name = storage_doc.bucket_name
        
        # Import timedelta for expires parameter
        from datetime import timedelta
        
        url = client.presigned_get_object(
            bucket_name,
            file_key,
            expires=timedelta(hours=1)  # 1 hour
        )
        
        return url
        
    except Exception as e:
        frappe.log_error(title="S3 File URL Error", message=str(e))
        frappe.throw(_("Failed to generate file URL: {0}").format(str(e)))


@frappe.whitelist()
def download_s3_file(file_key: str):
    """
    Download file from S3
    
    Args:
        file_key: S3 object key
    """
    try:
        storage_doc = frappe.get_doc("DFP External Storage", "DFP.ES.hkmjaipur.240628.271012")
        client = storage_doc.client.client
        bucket_name = storage_doc.bucket_name
        
        # Get file data
        response = client.get_object(bucket_name, file_key)
        
        # Get file name
        file_name = file_key.split('/')[-1]
        
        # Set response headers
        frappe.local.response.filename = file_name
        frappe.local.response.filecontent = response.read()
        frappe.local.response.type = "download"
        
    except Exception as e:
        frappe.log_error(title="S3 File Download Error", message=str(e))
        frappe.throw(_("Failed to download file: {0}").format(str(e)))


def main():
    """Command line interface"""
    print("S3 File Search API")
    print("=" * 50)
    print()
    print("Available endpoints:")
    print("  - search_s3_files: Search files in S3 bucket")
    print("  - get_s3_stats: Get bucket statistics")
    print("  - get_s3_file_url: Get presigned URL for file")
    print("  - download_s3_file: Download file from S3")
    print()


if __name__ == "__main__":
    main()

