import frappe

from erpnext.accounts.report.balance_sheet.balance_sheet import execute as execute_balance_sheet

from datetime import datetime, timedelta

def generate_date_range(start_date_str="01-04-2025", end_date_str="31-03-2026"):
    # Convert string to datetime
    start_date = datetime.strptime(start_date_str, "%d-%m-%Y")
    end_date = datetime.strptime(end_date_str, "%d-%m-%Y")
    
    # Generate list of dates
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime("%d-%m-%Y"))
        current_date += timedelta(days=1)
    
    return date_list

def analyze_stock_reconcile():


    for d in generate_date_range():
        columns, data = execute_balance_sheet(filters=frappe._dict({
            "company": "Touchstone Foundation Jaipur",
            "filter_based_on": "Date Range",
            "period_start_date": d,
            "period_end_date": d,
            "periodicity": "Yearly",
            "accumulated_values": 1,
        }))
        # print(columns)
        print(data)
        break


