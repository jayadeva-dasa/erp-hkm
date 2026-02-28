# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import json
import frappe
from urllib.parse import quote


class FileProcessor:
    """Class to handle file processing for detailed reports"""
    
    @staticmethod
    def process_files(files_json):
        """Process files and create HTML links"""
        files = json.loads(files_json)
        files_html = ""
        for ind, f in enumerate(files):
            file_url = f.get("url")
            if file_url:
                if file_url.startswith("/file/"):
                    encoded_path = quote(file_url[len("/file/") :])
                    full_url = f"{frappe.utils.get_url()}/file/{encoded_path}"
                else:
                    full_url = f"{frappe.utils.get_url()}{quote(file_url)}"

                file_link = f'<a href="{full_url}" target="_blank">F {ind + 1}</a>'
                files_html += file_link + " | "
        return files_html
    
    @staticmethod
    def create_voucher_link(voucher_type, voucher_no):
        """Create voucher link"""
        voucher_link = frappe.utils.get_url_to_form(voucher_type, voucher_no)
        return (
            f'<a href="{voucher_link}" target="_blank">{voucher_no}</a>'
            if voucher_link
            else voucher_no or ""
        ) 