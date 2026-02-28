#!/usr/bin/env python3
"""
Supplier Outstanding Balance Report System

Sends email reports to concerned persons about:
- Suppliers with outstanding balances
- Advance payments pending invoice submission
- Bill settlement reminders
"""

import frappe
from frappe import _
from frappe.utils import (
    flt, fmt_money, nowdate, add_days, getdate, cint
)


TEST_EMAIL = "nrhd@hkmjaipur.org"


def get_supplier_outstanding_data(supplier, company=None, from_date=None):
    """
    Get outstanding balance and advance payment details for a supplier
    Uses GL Entry based calculation like Supplier Ledger Summary report
    """
    
    # Use fiscal year start if from_date not provided
    if not from_date:
        from_date = frappe.db.get_value(
            "Fiscal Year", 
            {"disabled": 0}, 
            "year_start_date",
            order_by="year_start_date desc"
        )
    
    # Get GL Entry based balance (same as Supplier Ledger Summary)
    gl_balance = frappe.db.sql("""
        SELECT 
            SUM(credit - debit) as balance
        FROM `tabGL Entry`
        WHERE party_type = 'Supplier'
            AND party = %(supplier)s
            AND is_cancelled = 0
            {company_condition}
        GROUP BY party
    """.format(
        company_condition="AND company = %(company)s" if company else ""
    ), {"supplier": supplier, "company": company}, as_dict=1)
    
    closing_balance = flt(gl_balance[0].balance) if gl_balance else 0
    
    # If closing balance is 0 or negative (we owe them), no outstanding
    if closing_balance <= 0:
        return {
            "outstanding_invoices": [],
            "advance_payments": [],
            "total_outstanding": 0,
            "total_advances": 0,
            "overdue_invoices": [],
            "closing_balance": closing_balance
        }
    
    # Get outstanding purchase invoices (only if positive balance exists)
    outstanding_invoices = frappe.db.sql("""
        SELECT 
            name,
            posting_date,
            bill_no,
            bill_date,
            grand_total,
            outstanding_amount,
            due_date,
            currency,
            DATEDIFF(CURDATE(), due_date) as overdue_days
        FROM `tabPurchase Invoice`
        WHERE supplier = %(supplier)s
            AND docstatus = 1
            AND outstanding_amount > 0
            {company_condition}
        ORDER BY due_date ASC
    """.format(
        company_condition="AND company = %(company)s" if company else ""
    ), {"supplier": supplier, "company": company}, as_dict=1)
    
    # Check for GL-based advance (debit balance = we paid more than invoiced)
    advance_balance = frappe.db.sql("""
        SELECT 
            SUM(debit - credit) as advance
        FROM `tabGL Entry`
        WHERE party_type = 'Supplier'
            AND party = %(supplier)s
            AND is_cancelled = 0
            {company_condition}
        GROUP BY party
    """.format(
        company_condition="AND company = %(company)s" if company else ""
    ), {"supplier": supplier, "company": company}, as_dict=1)
    
    advance_amount = flt(advance_balance[0].advance) if advance_balance else 0
    
    # Get payment entries details if there's an advance
    advance_payments = []
    if advance_amount > 0.01:  # Small threshold for float comparison
        advance_payments = frappe.db.sql("""
            SELECT 
                pe.name,
                pe.posting_date,
                pe.paid_amount,
                pe.total_allocated_amount,
                (pe.paid_amount - pe.total_allocated_amount) as unallocated_amount,
                pe.paid_from_account_currency as currency,
                pe.remarks,
                DATEDIFF(CURDATE(), pe.posting_date) as pending_days
            FROM `tabPayment Entry` pe
            WHERE pe.party_type = 'Supplier'
                AND pe.party = %(supplier)s
                AND pe.docstatus = 1
                AND pe.payment_type = 'Pay'
                AND (pe.paid_amount - pe.total_allocated_amount) > 0.01
                {company_condition}
            ORDER BY pe.posting_date ASC
        """.format(
            company_condition="AND pe.company = %(company)s" if company else ""
        ), {"supplier": supplier, "company": company}, as_dict=1)
    
    return {
        "outstanding_invoices": outstanding_invoices,
        "advance_payments": advance_payments,
        "total_outstanding": sum(flt(inv.outstanding_amount) for inv in outstanding_invoices),
        "total_advances": advance_amount,
        "overdue_invoices": [inv for inv in outstanding_invoices if cint(inv.overdue_days) > 0],
        "closing_balance": closing_balance
    }


def get_concerned_person_suppliers(concerned_person):
    """Get all active suppliers for a concerned person"""
    
    suppliers = frappe.get_all(
        "Supplier",
        filters={
            "custom_concerned_person": concerned_person,
            "disabled": 0
        },
        fields=["name", "supplier_name"],
        order_by="supplier_name"
    )
    
    return suppliers


def generate_supplier_report_data(concerned_person, company=None):
    """Generate comprehensive report data for all suppliers of a concerned person"""
    
    suppliers = get_concerned_person_suppliers(concerned_person)
    
    if not suppliers:
        return None
    
    report_data = {
        "concerned_person": concerned_person,
        "total_suppliers": len(suppliers),
        "suppliers_with_outstanding": [],
        "suppliers_with_advances": [],
        "total_outstanding_amount": 0,
        "total_advance_amount": 0,
        "overdue_count": 0
    }
    
    for supplier in suppliers:
        data = get_supplier_outstanding_data(supplier.name, company)
        
        if data["outstanding_invoices"] or data["advance_payments"]:
            supplier_info = {
                "supplier_id": supplier.name,
                "supplier_name": supplier.supplier_name,
                "outstanding_invoices": data["outstanding_invoices"],
                "advance_payments": data["advance_payments"],
                "total_outstanding": data["total_outstanding"],
                "total_advances": data["total_advances"],
                "overdue_invoices": data["overdue_invoices"]
            }
            
            if data["outstanding_invoices"]:
                report_data["suppliers_with_outstanding"].append(supplier_info)
                report_data["total_outstanding_amount"] += data["total_outstanding"]
                
            if data["advance_payments"]:
                report_data["suppliers_with_advances"].append(supplier_info)
                report_data["total_advance_amount"] += data["total_advances"]
                
            if data["overdue_invoices"]:
                report_data["overdue_count"] += len(data["overdue_invoices"])
    
    return report_data


def generate_email_html(report_data):
    """Generate HTML email content from report data"""
    
    if not report_data:
        return None
    
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto;">
        <h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">
            Supplier Outstanding Balance Report
        </h2>
        
        <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #34495e;">Summary</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px;"><strong>Total Suppliers:</strong></td>
                    <td style="padding: 8px;">{report_data['total_suppliers']}</td>
                    <td style="padding: 8px;"><strong>Suppliers with Outstanding:</strong></td>
                    <td style="padding: 8px;">{len(report_data['suppliers_with_outstanding'])}</td>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Suppliers with Advances:</strong></td>
                    <td style="padding: 8px;">{len(report_data['suppliers_with_advances'])}</td>
                    <td style="padding: 8px;"><strong>Overdue Invoices:</strong></td>
                    <td style="padding: 8px; color: #e74c3c;"><strong>{report_data['overdue_count']}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Total Outstanding:</strong></td>
                    <td style="padding: 8px; color: #e74c3c;"><strong>₹ {fmt_money(report_data['total_outstanding_amount'])}</strong></td>
                    <td style="padding: 8px;"><strong>Total Advance Payments:</strong></td>
                    <td style="padding: 8px; color: #27ae60;"><strong>₹ {fmt_money(report_data['total_advance_amount'])}</strong></td>
                </tr>
            </table>
        </div>
    """
    
    # Suppliers with Advance Payments
    if report_data['suppliers_with_advances']:
        html += """
        <div style="margin: 30px 0;">
            <h3 style="color: #e67e22; border-bottom: 2px solid #e67e22; padding-bottom: 5px;">
                ⚠️ Suppliers with Advance Payments - Invoice Submission Pending
            </h3>
            <p style="color: #7f8c8d;">
                The following suppliers have received advance payments but invoices have not been submitted yet. 
                Please request them to submit their invoices for settlement.
            </p>
        """
        
        for supplier in report_data['suppliers_with_advances']:
            if not supplier['advance_payments']:
                continue
                
            html += f"""
            <div style="background-color: #fff3cd; padding: 15px; margin: 15px 0; border-left: 4px solid #e67e22; border-radius: 3px;">
                <h4 style="margin-top: 0; color: #34495e;">
                    {supplier['supplier_name']} ({supplier['supplier_id']})
                </h4>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                            <th style="padding: 10px; text-align: left;">Payment ID</th>
                            <th style="padding: 10px; text-align: left;">Date</th>
                            <th style="padding: 10px; text-align: right;">Paid Amount</th>
                            <th style="padding: 10px; text-align: right;">Unallocated</th>
                            <th style="padding: 10px; text-align: center;">Pending Days</th>
                            <th style="padding: 10px; text-align: left;">Remarks</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for payment in supplier['advance_payments']:
                html += f"""
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px;">{payment.name}</td>
                    <td style="padding: 8px;">{frappe.format(payment.posting_date, {'fieldtype': 'Date'})}</td>
                    <td style="padding: 8px; text-align: right;">₹ {fmt_money(payment.paid_amount)}</td>
                    <td style="padding: 8px; text-align: right; color: #e67e22;"><strong>₹ {fmt_money(payment.unallocated_amount)}</strong></td>
                    <td style="padding: 8px; text-align: center;">{payment.pending_days} days</td>
                    <td style="padding: 8px;">{payment.remarks or '-'}</td>
                </tr>
                """
            
            html += f"""
                    </tbody>
                </table>
                <div style="margin-top: 10px; padding: 10px; background-color: #ffffff; border-radius: 3px;">
                    <strong>Total Unallocated: ₹ {fmt_money(supplier['total_advances'])}</strong>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # Suppliers with Outstanding Invoices
    if report_data['suppliers_with_outstanding']:
        html += """
        <div style="margin: 30px 0;">
            <h3 style="color: #c0392b; border-bottom: 2px solid #c0392b; padding-bottom: 5px;">
                📋 Suppliers with Outstanding Bills
            </h3>
            <p style="color: #7f8c8d;">
                The following suppliers have outstanding invoices. Please review and process payments accordingly.
            </p>
        """
        
        for supplier in report_data['suppliers_with_outstanding']:
            if not supplier['outstanding_invoices']:
                continue
                
            overdue_count = len(supplier['overdue_invoices'])
            bg_color = "#ffebee" if overdue_count > 0 else "#e8f5e9"
            border_color = "#c0392b" if overdue_count > 0 else "#27ae60"
            
            html += f"""
            <div style="background-color: {bg_color}; padding: 15px; margin: 15px 0; border-left: 4px solid {border_color}; border-radius: 3px;">
                <h4 style="margin-top: 0; color: #34495e;">
                    {supplier['supplier_name']} ({supplier['supplier_id']})
                    {f'<span style="color: #c0392b; margin-left: 10px;">⚠️ {overdue_count} Overdue</span>' if overdue_count > 0 else ''}
                </h4>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                            <th style="padding: 10px; text-align: left;">Invoice</th>
                            <th style="padding: 10px; text-align: left;">Bill No</th>
                            <th style="padding: 10px; text-align: left;">Bill Date</th>
                            <th style="padding: 10px; text-align: left;">Due Date</th>
                            <th style="padding: 10px; text-align: right;">Grand Total</th>
                            <th style="padding: 10px; text-align: right;">Outstanding</th>
                            <th style="padding: 10px; text-align: center;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for invoice in supplier['outstanding_invoices']:
                is_overdue = cint(invoice.overdue_days) > 0
                status_color = "#c0392b" if is_overdue else "#27ae60"
                status_text = f"OVERDUE ({invoice.overdue_days} days)" if is_overdue else "Due"
                
                html += f"""
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px;">{invoice.name}</td>
                    <td style="padding: 8px;">{invoice.bill_no or '-'}</td>
                    <td style="padding: 8px;">{frappe.format(invoice.bill_date, {'fieldtype': 'Date'}) if invoice.bill_date else '-'}</td>
                    <td style="padding: 8px;">{frappe.format(invoice.due_date, {'fieldtype': 'Date'}) if invoice.due_date else '-'}</td>
                    <td style="padding: 8px; text-align: right;">₹ {fmt_money(invoice.grand_total)}</td>
                    <td style="padding: 8px; text-align: right; color: {status_color};"><strong>₹ {fmt_money(invoice.outstanding_amount)}</strong></td>
                    <td style="padding: 8px; text-align: center; color: {status_color};"><strong>{status_text}</strong></td>
                </tr>
                """
            
            html += f"""
                    </tbody>
                </table>
                <div style="margin-top: 10px; padding: 10px; background-color: #ffffff; border-radius: 3px;">
                    <strong>Total Outstanding: ₹ {fmt_money(supplier['total_outstanding'])}</strong>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # Action Items
    html += """
    <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #17a2b8;">
        <h3 style="margin-top: 0; color: #0c5460;">Action Required</h3>
        <ul style="color: #0c5460; line-height: 1.8;">
            <li><strong>For Advance Payments:</strong> Please contact the suppliers and request them to submit their invoices for the payments already made.</li>
            <li><strong>For Outstanding Bills:</strong> Review the outstanding invoices and process payments as per your company's payment terms.</li>
            <li><strong>For Overdue Bills:</strong> Prioritize overdue payments to maintain good supplier relationships.</li>
        </ul>
    </div>
    """
    
    html += f"""
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #bdc3c7; color: #7f8c8d; font-size: 12px;">
            <p>This is an automated report generated on {frappe.format(nowdate(), {'fieldtype': 'Date'})}.</p>
            <p>For any queries, please contact the Accounts team.</p>
        </div>
    </div>
    """
    
    return html


def send_supplier_outstanding_report(concerned_person, test_mode=True, company=None):
    """
    Send supplier outstanding report to concerned person
    
    Args:
        concerned_person: Email ID of the concerned person
        test_mode: If True, sends email to TEST_EMAIL instead
        company: Filter by company (optional)
    """
    
    try:
        # Generate report data
        report_data = generate_supplier_report_data(concerned_person, company)
        
        if not report_data:
            frappe.logger().info(f"No suppliers found for {concerned_person}")
            return {
                "success": False,
                "message": f"No suppliers found for {concerned_person}"
            }
        
        # Skip if no outstanding or advances
        if not report_data['suppliers_with_outstanding'] and not report_data['suppliers_with_advances']:
            frappe.logger().info(f"No outstanding or advance payments for {concerned_person}")
            return {
                "success": False,
                "message": f"No outstanding or advance payments for {concerned_person}"
            }
        
        # Generate email HTML
        email_html = generate_email_html(report_data)
        
        if not email_html:
            return {
                "success": False,
                "message": "Failed to generate email content"
            }
        
        # Determine recipient
        recipient = TEST_EMAIL if test_mode else concerned_person
        
        # Send email
        frappe.sendmail(
            recipients=[recipient],
            subject=f"Supplier Outstanding Balance Report - {frappe.format(nowdate(), {'fieldtype': 'Date'})}",
            message=email_html,
            header=["Supplier Outstanding Report", "orange"],
        )
        
        return {
            "success": True,
            "message": f"Email sent to {recipient}",
            "report_data": {
                "total_suppliers": report_data['total_suppliers'],
                "suppliers_with_outstanding": len(report_data['suppliers_with_outstanding']),
                "suppliers_with_advances": len(report_data['suppliers_with_advances']),
                "total_outstanding": report_data['total_outstanding_amount'],
                "total_advances": report_data['total_advance_amount'],
                "overdue_count": report_data['overdue_count']
            }
        }
        
    except Exception as e:
        frappe.log_error(
            message=f"Error sending supplier outstanding report to {concerned_person}: {str(e)}",
            title="Supplier Outstanding Report Error"
        )
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def test_run_for_top_concerned_person():
    """
    Test run: Send report for the concerned person with most suppliers
    Email will be sent to TEST_EMAIL for review
    """
    
    frappe.init(site='hkmjerp.in')
    frappe.connect()
    
    try:
        # Find concerned person with most suppliers
        result = frappe.db.sql("""
            SELECT 
                custom_concerned_person,
                COUNT(*) as supplier_count
            FROM tabSupplier
            WHERE custom_concerned_person IS NOT NULL
                AND disabled = 0
            GROUP BY custom_concerned_person
            ORDER BY supplier_count DESC
            LIMIT 1
        """, as_dict=1)
        
        if not result:
            print("No concerned persons found")
            return
        
        concerned_person = result[0].custom_concerned_person
        supplier_count = result[0].supplier_count
        
        print(f"\n{'='*80}")
        print(f"TEST RUN - Supplier Outstanding Report")
        print(f"{'='*80}")
        print(f"Concerned Person: {concerned_person}")
        print(f"Total Suppliers: {supplier_count}")
        print(f"Test Email: {TEST_EMAIL}")
        print(f"{'='*80}\n")
        
        # Send report in test mode
        result = send_supplier_outstanding_report(
            concerned_person=concerned_person,
            test_mode=True
        )
        
        if result["success"]:
            print("✓ SUCCESS!")
            print(f"  Email sent to: {TEST_EMAIL}")
            print(f"\nReport Summary:")
            print(f"  Total Suppliers: {result['report_data']['total_suppliers']}")
            print(f"  Suppliers with Outstanding: {result['report_data']['suppliers_with_outstanding']}")
            print(f"  Suppliers with Advances: {result['report_data']['suppliers_with_advances']}")
            print(f"  Total Outstanding: ₹ {fmt_money(result['report_data']['total_outstanding'])}")
            print(f"  Total Advance Payments: ₹ {fmt_money(result['report_data']['total_advances'])}")
            print(f"  Overdue Invoices: {result['report_data']['overdue_count']}")
        else:
            print(f"✗ FAILED: {result['message']}")
        
        frappe.db.commit()  # v16: REVIEW - check if needed
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


def send_to_all_concerned_persons(test_mode=False):
    """
    Send supplier outstanding reports to all concerned persons
    
    Args:
        test_mode: If True, sends all emails to TEST_EMAIL instead
    """
    
    frappe.init(site='hkmjerp.in')
    frappe.connect()
    
    try:
        # Get all concerned persons with suppliers
        concerned_persons = frappe.db.sql("""
            SELECT 
                custom_concerned_person,
                COUNT(*) as supplier_count
            FROM tabSupplier
            WHERE custom_concerned_person IS NOT NULL
                AND disabled = 0
            GROUP BY custom_concerned_person
            ORDER BY custom_concerned_person
        """, as_dict=1)
        
        print(f"\n{'='*80}")
        print(f"Sending Supplier Outstanding Reports to All Concerned Persons")
        print(f"Mode: {'TEST (all emails to ' + TEST_EMAIL + ')' if test_mode else 'PRODUCTION'}")
        print(f"Total Concerned Persons: {len(concerned_persons)}")
        print(f"{'='*80}\n")
        
        results = {
            "total": len(concerned_persons),
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "details": []
        }
        
        for idx, cp in enumerate(concerned_persons, 1):
            print(f"[{idx}/{len(concerned_persons)}] Processing {cp.custom_concerned_person} ({cp.supplier_count} suppliers)...")
            
            result = send_supplier_outstanding_report(
                concerned_person=cp.custom_concerned_person,
                test_mode=test_mode
            )
            
            if result["success"]:
                print(f"  ✓ Sent successfully")
                results["success"] += 1
            else:
                if "No outstanding" in result["message"]:
                    print(f"  - Skipped (no data)")
                    results["skipped"] += 1
                else:
                    print(f"  ✗ Failed: {result['message']}")
                    results["failed"] += 1
            
            results["details"].append({
                "concerned_person": cp.custom_concerned_person,
                "supplier_count": cp.supplier_count,
                "status": result["success"],
                "message": result["message"]
            })
        
        frappe.db.commit()  # v16: REVIEW - check if needed
        
        print(f"\n{'='*80}")
        print(f"Summary:")
        print(f"  Total: {results['total']}")
        print(f"  Sent: {results['success']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Failed: {results['failed']}")
        print(f"{'='*80}\n")
        
        return results
        
    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


def send_sample_report_for_user(user_email):
    """Send a sample report for a specific concerned person to TEST_EMAIL"""
    
    frappe.init(site='hkmjerp.in')
    frappe.connect()
    
    try:
        # Check how many suppliers this user has
        supplier_count = frappe.db.count(
            "Supplier",
            {
                "custom_concerned_person": user_email,
                "disabled": 0
            }
        )
        
        print(f"\n{'='*80}")
        print(f"Sample Report for {user_email}")
        print(f"{'='*80}")
        print(f"Total Suppliers: {supplier_count}")
        print(f"Test Email: {TEST_EMAIL}")
        print(f"{'='*80}\n")
        
        if supplier_count == 0:
            print(f"No suppliers found for {user_email}")
            return
        
        # Send report in test mode
        result = send_supplier_outstanding_report(
            concerned_person=user_email,
            test_mode=True
        )
        
        if result["success"]:
            print("✓ SUCCESS!")
            print(f"  Email sent to: {TEST_EMAIL}")
            print(f"\nReport Summary:")
            print(f"  Total Suppliers: {result['report_data']['total_suppliers']}")
            print(f"  Suppliers with Outstanding: {result['report_data']['suppliers_with_outstanding']}")
            print(f"  Suppliers with Advances: {result['report_data']['suppliers_with_advances']}")
            print(f"  Total Outstanding: ₹ {result['report_data']['total_outstanding']:,.2f}")
            print(f"  Total Advance Payments: ₹ {result['report_data']['total_advances']:,.2f}")
            print(f"  Overdue Invoices: {result['report_data']['overdue_count']}")
        else:
            print(f"✗ FAILED: {result['message']}")
        
        frappe.db.commit()  # v16: REVIEW - check if needed
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


if __name__ == "__main__":
    test_run_for_top_concerned_person()

