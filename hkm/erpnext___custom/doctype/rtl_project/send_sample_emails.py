"""
Send Sample RTL Project Emails
Script to send all 4 types of email notifications with dummy data
"""

import frappe
from frappe.utils import nowdate, add_days, formatdate, getdate


@frappe.whitelist()
def send_all_sample_emails(recipient_email):
    """Send all 4 types of sample emails to test email system"""
    
    if not recipient_email:
        frappe.throw("Recipient email is required")
    
    results = []
    
    # 1. Project Creation Email
    try:
        send_sample_project_creation_email(recipient_email)
        results.append({"type": "Project Creation", "status": "Sent", "message": "✅ Success"})
    except Exception as e:
        results.append({"type": "Project Creation", "status": "Failed", "message": str(e)})
    
    # 2. Deadline Reminder Email
    try:
        send_sample_deadline_reminder_email(recipient_email)
        results.append({"type": "Deadline Reminder", "status": "Sent", "message": "✅ Success"})
    except Exception as e:
        results.append({"type": "Deadline Reminder", "status": "Failed", "message": str(e)})
    
    # 3. Daily Status Reminder Email
    try:
        send_sample_daily_status_reminder_email(recipient_email)
        results.append({"type": "Daily Status Reminder", "status": "Sent", "message": "✅ Success"})
    except Exception as e:
        results.append({"type": "Daily Status Reminder", "status": "Failed", "message": str(e)})
    
    # 4. HOD Status Matrix Email
    try:
        send_sample_hod_status_matrix_email(recipient_email)
        results.append({"type": "HOD Status Matrix", "status": "Sent", "message": "✅ Success"})
    except Exception as e:
        results.append({"type": "HOD Status Matrix", "status": "Failed", "message": str(e)})
    
    # 5. Project Completion Email
    try:
        send_sample_project_completion_email(recipient_email)
        results.append({"type": "Project Completion", "status": "Sent", "message": "✅ Success"})
    except Exception as e:
        results.append({"type": "Project Completion", "status": "Failed", "message": str(e)})
    
    return {
        "success": True,
        "message": f"Sent {len([r for r in results if r['status'] == 'Sent'])} emails to {recipient_email}",
        "results": results
    }


def send_sample_project_creation_email(recipient):
    """Sample: Project Creation Email"""
    from hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications import send_project_creation_email
    
    # Create a mock project object
    mock_project = frappe._dict({
        "name": "SAMPLE-PROJ-001",
        "project_name": "Monthly Sales Report - November 2025",
        "description": "Prepare comprehensive sales report including revenue analysis, customer segmentation, and market trends for November 2025.",
        "assigned_to": recipient,
        "status": "Not Started",
        "end_date": add_days(nowdate(), 15),
        "start_date": None,
    })
    
    send_project_creation_email(mock_project)
    frappe.logger().info(f"Sample project creation email sent to {recipient}")


def send_sample_deadline_reminder_email(recipient):
    """Sample: Deadline Reminder Email"""
    
    today = getdate(nowdate())
    end_date = add_days(today, 1)  # Tomorrow
    
    subject = f"⚠️ Project Deadline Alert: Quarterly Budget Review"
    
    message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #dc2626; border-bottom: 2px solid #dc2626; padding-bottom: 10px;">
            ⚠️ Project Deadline Alert
        </h2>
        
        <div style="background-color: #fef2f2; padding: 20px; border-left: 4px solid #dc2626; margin: 20px 0;">
            <h3 style="color: #991b1b; margin-top: 0;">Urgent: Action Required</h3>
            <p style="color: #7f1d1d; font-size: 16px; margin: 10px 0;">
                This project is reaching its deadline very soon. Please focus and complete it immediately.
            </p>
        </div>
        
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #1e293b; margin-top: 0;">Project Details</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #475569; width: 40%;">Project Name:</td>
                    <td style="padding: 8px 0; color: #1e293b;">Quarterly Budget Review</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #475569;">Deadline:</td>
                    <td style="padding: 8px 0; color: #ef4444; font-weight: bold;">
                        {formatdate(end_date, "dd MMM yyyy")} (in 1 day)
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #475569;">Current Status:</td>
                    <td style="padding: 8px 0;">
                        <div style="display: inline-block; background-color: #facc15; color: #000000; 
                                    padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                            Delayed 3-7 Days
                        </div>
                    </td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: #fff7ed; padding: 15px; border-left: 4px solid #f97316; margin: 20px 0;">
            <h4 style="color: #9a3412; margin-top: 0;">Description:</h4>
            <p style="color: #78350f; margin: 0; white-space: pre-wrap;">Review and analyze Q3 budget utilization, identify variances, and prepare recommendations for Q4 budget allocation.</p>
        </div>
        
        <div style="margin-top: 30px; padding: 15px; background-color: #eff6ff; border-radius: 8px;">
            <p style="margin: 0; color: #1e40af;">
                <strong>Next Steps:</strong> Please prioritize this project and update your progress status in the RTL Project Dashboard.
            </p>
        </div>
        
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
            <p style="margin: 0;">This is an automated reminder from the RTL Project Management System.</p>
        </div>
    </div>
    """
    
    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        delayed=False,
    )
    
    frappe.logger().info(f"Sample deadline reminder email sent to {recipient}")


def send_sample_daily_status_reminder_email(recipient):
    """Sample: Daily Status Reminder Email"""
    
    subject = f"📋 Daily RTL Project Status Update Required - 3 Pending"
    
    message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #f59e0b; border-bottom: 2px solid #f59e0b; padding-bottom: 10px;">
            📋 Daily Project Status Update Required
        </h2>
        
        <div style="background-color: #fef3c7; padding: 20px; border-left: 4px solid #f59e0b; margin: 20px 0;">
            <h3 style="color: #92400e; margin-top: 0;">⚠️ Action Required - Status Not Updated Today</h3>
            <p style="color: #78350f; font-size: 16px; margin: 10px 0;">
                You have <strong>3</strong> projects that need daily status updates for today.
            </p>
        </div>
        
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #1e293b; margin-top: 0;">Status Summary</h3>
            <div style="color: #475569; line-height: 1.8; font-size: 15px;">
                • <strong style='color: #dc2626;'>3</strong> projects need today's status update<br>
                • <strong>1</strong> project not yet started<br>
                • <strong style='color: #ef4444;'>7</strong> total missed updates (cumulative)
            </div>
        </div>
        
        <div style="background-color: #fee2e2; padding: 15px; border-left: 4px solid #dc2626; margin: 20px 0;">
            <h4 style="color: #991b1b; margin-top: 0;">📊 Total Missed Updates</h4>
            <p style="color: #7f1d1d; margin: 0; font-size: 15px;">
                You have <strong>7</strong> cumulative missed updates across all your projects. 
                Please ensure daily updates are completed on time going forward.
            </p>
        </div>
        
        <div style="margin-top: 30px; padding: 15px; background-color: #eff6ff; border-radius: 8px;">
            <p style="margin: 0; color: #1e40af; font-size: 15px;">
                <strong>Next Steps:</strong> Please log in to the RTL Project Dashboard and update the daily status for all your assigned projects immediately.
            </p>
        </div>
        
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
            <p style="margin: 0;">This is an automated reminder from the RTL Project Management System.</p>
            <p style="margin: 5px 0 0 0;">Date: {formatdate(nowdate(), "dd MMM yyyy")} | Time: 7:30 PM</p>
        </div>
    </div>
    """
    
    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        delayed=False,
    )
    
    frappe.logger().info(f"Sample daily status reminder email sent to {recipient}")


def send_sample_hod_status_matrix_email(recipient):
    """Sample: HOD Daily Status Matrix Email"""
    
    subject = f"Daily RTL Project Status Report - Finance Department"
    today = getdate(nowdate())
    
    message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto;">
        <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
            Daily RTL Project Status Report
        </h2>
        
        <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; color: #475569;">
                <strong>Department:</strong> Finance Department<br>
                <strong>Date:</strong> {formatdate(today, "dd MMM yyyy")}
            </p>
        </div>
        
        <h3 style="color: #1e293b; margin-top: 30px;">📊 Project Summary</h3>
        <div style="display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 150px; background-color: #f1f5f9; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #64748b;">2</div>
                <div style="color: #475569; font-size: 14px; margin-top: 5px;">Not Started</div>
            </div>
            <div style="flex: 1; min-width: 150px; background-color: #dbeafe; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #2563eb;">8</div>
                <div style="color: #1e40af; font-size: 14px; margin-top: 5px;">In Process</div>
            </div>
            <div style="flex: 1; min-width: 150px; background-color: #dcfce7; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #16a34a;">5</div>
                <div style="color: #15803d; font-size: 14px; margin-top: 5px;">Completed</div>
            </div>
        </div>
        
        <h3 style="color: #1e293b; margin-top: 30px;">✅ Completed Today</h3>
        <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin: 10px 0; border-radius: 4px;">
            <ul style="margin: 0; padding-left: 20px; color: #15803d;">
                <li style="margin: 5px 0;"><strong>Monthly Expense Report</strong> by Priyanshu Arora</li>
                <li style="margin: 5px 0;"><strong>Bank Reconciliation October</strong> by Monesh Dadhich</li>
            </ul>
        </div>
        
        <h3 style="color: #1e293b; margin-top: 30px;">⚠️ Alerts & Warnings</h3>
        
        <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 10px 0; border-radius: 4px;">
            <div style="font-weight: bold; color: #991b1b; margin-bottom: 8px;">🚨 Critical Issues</div>
            <ul style="margin: 0; padding-left: 20px; color: #7f1d1d;">
                <li style="margin: 5px 0;"><strong>GST Filing Preparation</strong> assigned to Raksha Kabra is severely delayed and needs immediate attention.</li>
            </ul>
        </div>
        
        <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 15px; margin: 10px 0; border-radius: 4px;">
            <div style="font-weight: bold; color: #9a3412; margin-bottom: 8px;">⚠️ Warnings</div>
            <ul style="margin: 0; padding-left: 20px; color: #78350f;">
                <li style="margin: 5px 0;"><strong>Audit Documentation</strong> assigned to Pukhraj Garg is significantly delayed.</li>
            </ul>
        </div>
        
        <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 10px 0; border-radius: 4px;">
            <div style="font-weight: bold; color: #1e40af; margin-bottom: 8px;">ℹ️ Information</div>
            <ul style="margin: 0; padding-left: 20px; color: #1e3a8a;">
                <li style="margin: 5px 0;"><strong>Investment Analysis</strong> assigned to Monesh Dadhich has no status update yet.</li>
                <li style="margin: 5px 0;"><strong>Tax Planning Q4</strong> assigned to Priyanshu Arora is due in 2 days.</li>
            </ul>
        </div>
        
        <h3 style="color: #1e293b; margin-top: 30px;">📋 Status Matrix</h3>
        <p style="color: #64748b; font-size: 14px; margin-bottom: 15px;">
            Current status overview for all in-process projects
        </p>
        
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="background-color: #f1f5f9;">
                        <th style="padding: 12px; text-align: left; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Assignee</th>
                        <th style="padding: 12px; text-align: center; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Projects</th>
                        <th style="padding: 12px; text-align: center; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Missed Updates</th>
                        <th style="padding: 12px; text-align: center; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Project 1</th>
                        <th style="padding: 12px; text-align: center; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Project 2</th>
                        <th style="padding: 12px; text-align: center; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Project 3</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; font-weight: 500; color: #1e293b;">Priyanshu Arora</td>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; text-align: center; font-weight: bold; color: #2563eb;">3</td>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; text-align: center; color: #22c55e; font-weight: 600;">0</td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #22c55e; color: #ffffff; text-align: center;">
                            <div style="font-weight: 500; font-size: 12px;">Tax Planning Q4</div>
                        </td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #22c55e; color: #ffffff; text-align: center;">
                            <div style="font-weight: 500; font-size: 12px;">ITR Filing Preparation</div>
                        </td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #facc15; color: #000000; text-align: center;">
                            <div style="font-weight: 500; font-size: 12px;">Budget Forecast Review</div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; font-weight: 500; color: #1e293b;">Monesh Dadhich</td>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; text-align: center; font-weight: bold; color: #2563eb;">2</td>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; text-align: center; color: #f59e0b; font-weight: 600;">3</td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #e2e8f0; color: #64748b; text-align: center;">
                            <div style="font-weight: 500; font-size: 12px;">Investment Analysis</div>
                            <div style="font-size: 10px; margin-top: 2px;">No Status</div>
                        </td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #22c55e; color: #ffffff; text-align: center;">
                            <div style="font-weight: 500; font-size: 12px;">Cost Center Review</div>
                        </td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #fafafa;"></td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; font-weight: 500; color: #1e293b;">Raksha Kabra</td>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; text-align: center; font-weight: bold; color: #2563eb;">3</td>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; text-align: center; color: #dc2626; font-weight: 600;">12</td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #22c55e; color: #ffffff; text-align: center;">
                            <div style="font-weight: 500; font-size: 12px;">Fixed Assets Reco</div>
                        </td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #ef4444; color: #ffffff; text-align: center;">
                            <div style="font-weight: 500; font-size: 12px;">GST Filing Preparation</div>
                        </td>
                        <td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #f97316; color: #ffffff; text-align: center;">
                            <div style="font-weight: 500; font-size: 12px;">Audit Documentation</div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div style="margin-top: 15px; padding: 10px; background-color: #f8fafc; border-radius: 6px;">
            <div style="font-weight: 600; color: #475569; margin-bottom: 8px; font-size: 12px;">Status Legend:</div>
            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 16px; height: 16px; background-color: #22c55e; border-radius: 3px;"></div>
                    <span style="font-size: 11px; color: #64748b;">On Track</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 16px; height: 16px; background-color: #facc15; border-radius: 3px;"></div>
                    <span style="font-size: 11px; color: #64748b;">Delayed 3-7 Days</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 16px; height: 16px; background-color: #f97316; border-radius: 3px;"></div>
                    <span style="font-size: 11px; color: #64748b;">Delayed 8-15 Days</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 16px; height: 16px; background-color: #ef4444; border-radius: 3px;"></div>
                    <span style="font-size: 11px; color: #64748b;">Delayed >15 Days</span>
                </div>
                <div style="display: flex; align-items: center; gap: 5px;">
                    <div style="width: 16px; height: 16px; background-color: #e2e8f0; border-radius: 3px;"></div>
                    <span style="font-size: 11px; color: #64748b;">No Status</span>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
            <p style="margin: 0;">This is an automated daily report from the RTL Project Management System.</p>
            <p style="margin: 5px 0 0 0;">Generated at 7:00 PM</p>
        </div>
    </div>
    """
    
    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        delayed=False,
    )
    
    frappe.logger().info(f"Sample HOD status matrix email sent to {recipient}")


def send_sample_project_completion_email(recipient):
    """Sample: Project Completion Email to HOD"""
    
    subject = f"✅ Project Completed: Annual Audit Report 2024-25"
    
    message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #22c55e; border-bottom: 2px solid #22c55e; padding-bottom: 10px;">
            ✅ Project Completed
        </h2>
        
        <div style="background-color: #f0fdf4; padding: 20px; border-left: 4px solid #22c55e; margin: 20px 0;">
            <h3 style="color: #166534; margin-top: 0;">Good News!</h3>
            <p style="color: #14532d; font-size: 16px; margin: 10px 0;">
                A project assigned to <strong>Monesh Dadhich</strong> has been successfully completed.
            </p>
        </div>
        
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #1e293b; margin-top: 0;">Project Details</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #475569; width: 40%;">Project Name:</td>
                    <td style="padding: 8px 0; color: #1e293b;">Annual Audit Report 2024-25</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #475569;">Assigned To:</td>
                    <td style="padding: 8px 0; color: #1e293b;">Monesh Dadhich</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #475569;">Completed On:</td>
                    <td style="padding: 8px 0; color: #22c55e; font-weight: bold;">
                        {formatdate(nowdate(), "dd MMM yyyy")}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #475569;">Start Date:</td>
                    <td style="padding: 8px 0; color: #1e293b;">{formatdate(add_days(nowdate(), -20), "dd MMM yyyy")}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #475569;">End Date:</td>
                    <td style="padding: 8px 0; color: #1e293b;">{formatdate(add_days(nowdate(), 2), "dd MMM yyyy")}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #475569;">Missed Updates:</td>
                    <td style="padding: 8px 0; color: #22c55e; font-weight: bold;">
                        0 days
                    </td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: #fff7ed; padding: 15px; border-left: 4px solid #f97316; margin: 20px 0;">
            <h4 style="color: #9a3412; margin-top: 0;">Description:</h4>
            <p style="color: #78350f; margin: 0; white-space: pre-wrap;">Complete annual audit report with financial statements, compliance checklist, and management recommendations for FY 2024-25.</p>
        </div>
        
        <div style="margin-top: 30px; padding: 15px; background-color: #eff6ff; border-radius: 8px;">
            <p style="margin: 0; color: #1e40af;">
                <strong>Department:</strong> Finance Department
            </p>
        </div>
        
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
            <p style="margin: 0;">This is an automated notification from the RTL Project Management System.</p>
        </div>
    </div>
    """
    
    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        delayed=False,
    )
    
    frappe.logger().info(f"Sample project completion email sent to {recipient}")

