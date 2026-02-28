from datetime import date, timedelta

from hkm.hkm_pay.notify_user import send_statement_email , send_notification_to_user
import frappe
from hkm.expense_summary.main import ExpenseSummary 


def mrn_close():
    past_date = frappe.utils.now() - timedelta(days=90)
    ninety_days_ago_str = past_date.strftime("%Y-%m-%d")
    for i in frappe.get_all(
        "Material Request",
        filters={
            "creation": [">", ninety_days_ago_str],
            "status": "Pending",
            "docstatus": ["!=", 2],
        },
        pluck="name",
    ):
        doc = frappe.get_doc("Material Request", i)
        doc.cancel()

from frappe.utils import getdate, today
import calendar

def summary_report_expenses_monthly():
    today_date = getdate(today())
    last_day = calendar.monthrange(today_date.year, today_date.month)[1]

    if today_date.day != last_day:
        return  # Not last day, exit

    cost_heads = frappe.get_all(
        "Cost Head Concerned Person",
        fields=["parent", "user"],
    )
    user_dict = {}
    for cost_head in cost_heads:
        user_dict[cost_head.get("user")] = []
        user_dict[cost_head.get("user")].append(cost_head.get("parent"))

    for key, value in user_dict.items():
        cost_heads = list(set(value))
        user = [key]
        descendent_cost_heads = frappe.get_all(
            "Cost Head",
            filters={
                "parent_cost_head": ["in", cost_heads],
            },
            pluck="name",
        )
        cost_heads.extend(descendent_cost_heads)

        start_date, end_date = get_current_month_range()
        # cost_heads = ["CDT"]
        # user = ["vishnu.sharma@hkmjaipur.org", "arorapriyanshu33@gmail.com"]
        expense_summary = ExpenseSummary(cost_heads, start_date, end_date, user)
        # break


def get_current_month_range():
    today = date.today()
    first_day_this_month = today.replace(day=1)
    last_day_prev_month = first_day_this_month - timedelta(days=1)
    start = last_day_prev_month.replace(day=1)
    end = last_day_prev_month

    return start, end


def notify_users_about_pending_bills():
    for user in frappe.get_all("HKMP User", filters={"enabled": 1}):
        print(user.name)
        send_statement_email(user.name)
        

    # today = date.today()
    # start = today.replace(day=1)

    # # Calculate end of month
    # if today.month == 12:
    #     end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    # else:
    #     end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    # return start, end


def notify_users_about_low_balance():
    send_notification_to_user()
    
    
    
def correct_item_tax_rate():
    if frappe.local.site != "hkmjerp.in":
        return
    hsn = ["441400"]
    not_have_tax_template = []
    having_zero_tax_template = []
    new_rate = "5%"
    
    for i in  frappe.get_all(
        "Item",
        filters={
            "gst_hsn_code": ["in", hsn],
        },
        pluck="name",
    ):
        item = frappe.get_doc("Item", i)

        if item.get("taxes"):
            if not new_rate or str(new_rate).strip("%") == "0":
                having_zero_tax_template.append(i)
                item.taxes = []
            else:
                for tax in item.get("taxes"):
                    taxes = tax.item_tax_template
                    tax.item_tax_template = replace_percentage(
                        taxes, str(new_rate).strip("%")
                    )
        else:
            tax_template = ["GST - 5% - TSFJ"]

            if not new_rate or str(new_rate).strip("%") == "0":
                item.taxes = []
                having_zero_tax_template.append(i)
            else:
                for i in tax_template:
                    item.append(
                        "taxes",
                        {
                            "item_tax_template": replace_percentage(
                                i, str(new_rate).strip("%")
                            ),
                        },
                    )

            not_have_tax_template.append(i)

        item.save()
        

        print("\n==== SUMMARY ====")  # move to next line after loop
        print("not_have_tax_template", not_have_tax_template)
        print("having_zero_tax_template", having_zero_tax_template)
    frappe.db.commit()  # v16: OK - operations script
    
