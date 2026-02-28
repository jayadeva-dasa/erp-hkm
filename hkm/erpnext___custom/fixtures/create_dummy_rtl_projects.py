"""
Script to create dummy RTL Projects and Daily Status entries for testing.
Run with: bench execute hkm.erpnext___custom.fixtures.create_dummy_rtl_projects.create_dummy_data
"""

import frappe
from frappe.utils import nowdate, add_days, random_string
import random


def create_dummy_data():
    """Create dummy RTL Projects and Daily Status entries."""
    
    users = [
        "arorapriyanshu33@gmail.com",
        "grsd@hkmjaipur.org",
        "shubham.sharma@hkmjaipur.org",
        "nrhdasa@gmail.com",
        "nrhd@hkmjaipur.org",
        "bkvd@hkmjodhpur.org",
        "ajad@hkmjaipur.org",
        "nmcd@hkmjaipur.org",
        "guptatanish222@gmail.com",
        "vamshiviharikrsnadasa@gmail.com",
    ]
    
    project_templates = [
        "Update Vendor Master Data",
        "Reconcile Bank Statements",
        "Prepare Monthly Financial Report",
        "Clean up Customer Database",
        "Audit Inventory Records",
        "Process Pending Purchase Orders",
        "Review and Approve Expense Claims",
        "Update Employee Records",
        "Generate Sales Analytics Dashboard",
        "Migrate Legacy Data to New System",
        "Configure Email Templates",
        "Setup Automated Backup System",
        "Optimize Database Queries",
        "Create Training Documentation",
        "Implement New Approval Workflow",
        "Review Security Permissions",
        "Update Product Catalog",
        "Reconcile Tax Records",
        "Process Year-End Closing",
        "Setup Integration with Payment Gateway",
    ]
    
    progress_statuses = [
        "On Track",
        "Delayed 3-7 Days",
        "Delayed 8-15 Days",
        "Delayed >15 Days (Need Help)",
    ]
    
    descriptions = [
        "High priority task requiring immediate attention",
        "Regular maintenance activity scheduled for this month",
        "Critical business process improvement initiative",
        "Compliance requirement to be completed before audit",
        "Optimization project to improve system performance",
        "Data quality improvement initiative",
        "Process automation to reduce manual work",
        "System upgrade and enhancement project",
    ]
    
    created_projects = []
    
    # Create 2-5 projects per user
    for user in users:
        num_projects = random.randint(2, 5)
        
        for i in range(num_projects):
            project_name = random.choice(project_templates)
            # Make it unique by adding a suffix
            project_name = f"{project_name} - {random_string(3).upper()}"
            
            # Random end date between 10 days ago and 30 days from now
            end_date = add_days(nowdate(), random.randint(-10, 30))
            
            try:
                project = frappe.get_doc({
                    "doctype": "RTL Project",
                    "project_name": project_name,
                    "description": random.choice(descriptions),
                    "assigned_to": user,
                    "end_date": end_date,
                    "status": "In Process",
                })
                project.insert(ignore_permissions=True)
                
                # Set start date manually (since it's auto-set on status change)
                start_date = add_days(nowdate(), random.randint(-20, -5))
                frappe.db.set_value("RTL Project", project.name, "start_date", start_date)
                
                created_projects.append(project.name)
                print(f"Created project: {project.name} for {user}")
                
            except Exception as e:
                print(f"Error creating project for {user}: {str(e)}")
                continue
    
    frappe.db.commit()  # v16: OK - fixture script
    
    # Create daily status entries for the last 7 days
    for project_name in created_projects:
        # Random number of status entries (3-7 days)
        num_entries = random.randint(3, 7)
        
        for i in range(num_entries):
            log_date = add_days(nowdate(), -i)
            progress_status = random.choice(progress_statuses)
            
            # Weight towards better statuses for recent dates
            if i <= 2:  # Last 2 days
                progress_status = random.choices(
                    progress_statuses,
                    weights=[60, 25, 10, 5],  # More likely to be on track
                    k=1
                )[0]
            
            remarks_options = [
                "Work progressing as planned",
                "Waiting for approval from stakeholder",
                "Minor delays due to resource constraints",
                "Need additional support to complete on time",
                "Completed major milestone today",
                "Facing technical challenges, working on resolution",
                "On track to meet deadline",
                "",  # Empty remarks sometimes
            ]
            
            try:
                status_entry = frappe.get_doc({
                    "doctype": "RTL Project Daily Status",
                    "project": project_name,
                    "log_date": log_date,
                    "progress_status": progress_status,
                    "remarks": random.choice(remarks_options),
                })
                status_entry.insert(ignore_permissions=True)
                
            except Exception as e:
                # Skip if entry already exists for this date
                if "Duplicate entry" not in str(e):
                    print(f"Error creating status for {project_name} on {log_date}: {str(e)}")
                continue
    
    frappe.db.commit()  # v16: OK - fixture script
    
    print(f"\n✅ Successfully created {len(created_projects)} dummy projects with daily status entries!")
    print(f"Projects created for {len(users)} users")
    print("\nYou can now view the RTL Project Dashboard and Status Matrix.")


if __name__ == "__main__":
    create_dummy_data()
