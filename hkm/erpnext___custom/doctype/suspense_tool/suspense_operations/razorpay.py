import frappe,re
@frappe.whitelist()
def get_gl_as_dict(jv):
    return frappe.get_doc("Journal Entry",jv).as_dict()
    # gl_entry = frappe.get_all(
    #             "GL Entry",
    #             filters={"voucher_no": jv},
    #             fields=["*"],
    #         )
    # return gl_entry

def bulk_razorpay_update():
    vouchers = [
        'ACC-JV-2022-11762',
        'ACC-JV-2022-12129',
        'ACC-JV-2022-12202',
        'ACC-JV-2022-12207',
        'ACC-JV-2022-12317',
        'ACC-JV-2022-12552',
        'ACC-JV-2022-12819',
        'ACC-JV-2022-13124',
        'ACC-JV-2022-13340',
        'ACC-JV-2022-13349',
        'ACC-JV-2022-13571',
        'ACC-JV-2022-14012',
        'ACC-JV-2022-14034',
        'ACC-JV-2022-14035',
        'ACC-JV-2022-14036',
        'ACC-JV-2022-14040',
        'ACC-JV-2022-14042',
        'ACC-JV-2022-14049',
        'ACC-JV-2022-14131',
        'ACC-JV-2022-14376',
        'ACC-JV-2022-14794',
        'ACC-JV-2022-14805',
        'ACC-JV-2022-14820',
        'ACC-JV-2022-15465',
        'ACC-JV-2022-15528',
        'ACC-JV-2022-15550',
        'ACC-JV-2022-16152',
        'ACC-JV-2022-16167',
        'ACC-JV-2022-17149',
        'ACC-JV-2022-17157',
        'ACC-JV-2022-17202',
        'ACC-JV-2022-17557',
        'ACC-JV-2022-18300',
        'ACC-JV-2022-18310',
        'ACC-JV-2022-18320',
        'ACC-JV-2022-19170',
        'ACC-JV-2022-19747',
        'ACC-JV-2022-19770',
        'ACC-JV-2022-21546',
        'ACC-JV-2022-24100',
        'ACC-JV-2022-24112',
        'ACC-JV-2022-24188',
        'ACC-JV-2022-24672',
        'ACC-JV-2022-24675',
        'ACC-JV-2022-24694',
        'ACC-JV-2022-24719',
        'ACC-JV-2022-24747',
        'ACC-JV-2022-24762',
        'ACC-JV-2022-25117',
        'ACC-JV-2022-25583',
        'ACC-JV-2022-25609',
        'ACC-JV-2022-26119',
        'ACC-JV-2022-26136',
        'ACC-JV-2022-26152',
        'ACC-JV-2022-27819',
        'ACC-JV-2022-27831',
        'ACC-JV-2022-27844',
        'ACC-JV-2022-27957',
        'ACC-JV-2022-27979',
        'ACC-JV-2022-28008',
        'ACC-JV-2022-28019',
        'ACC-JV-2022-28033',
        'ACC-JV-2022-28047',
        'ACC-JV-2022-28054',
        'ACC-JV-2022-28589',
        'ACC-JV-2022-28594',
        'ACC-JV-2022-28596',
        'ACC-JV-2022-29563',
        'ACC-JV-2022-31608',
        'ACC-JV-2022-31736',
        'ACC-JV-2022-31739',
        'ACC-JV-2022-31751',
        'ACC-JV-2022-31755',
        'ACC-JV-2022-31766',
        'ACC-JV-2022-31795',
        'ACC-JV-2022-31809',
        'ACC-JV-2022-31833',
        'ACC-JV-2022-31861',
        'ACC-JV-2022-31869',
        'ACC-JV-2022-31884',
        'ACC-JV-2022-31892',
        'ACC-JV-2022-31896',
        'ACC-JV-2022-31913',
        'ACC-JV-2022-32499',
        'ACC-JV-2022-32526',
        'ACC-JV-2022-33415',
        'ACC-JV-2022-33425',
        'ACC-JV-2022-33439',
        'ACC-JV-2022-33488',
        'ACC-JV-2022-33500',
        'ACC-JV-2022-33512',
        'ACC-JV-2022-33556',
        'ACC-JV-2022-34417',
        'ACC-JV-2022-34426',
        'ACC-JV-2022-34437',
        'ACC-JV-2022-34444',
        'ACC-JV-2022-34646',
        'ACC-JV-2022-34679',
        'ACC-JV-2022-34704',
        'ACC-JV-2022-34735',
        'ACC-JV-2022-35904',
        'ACC-JV-2022-35932',
        'ACC-JV-2022-35951',
        'ACC-JV-2022-36018',
        'ACC-JV-2022-36031',
        'ACC-JV-2022-36041',
        'ACC-JV-2022-36050',
        'ACC-JV-2022-36069',
        'ACC-JV-2022-36074',
        'ACC-JV-2022-36079',
        'ACC-JV-2022-37529',
        'ACC-JV-2022-37537',
        'ACC-JV-2022-37541',
        'ACC-JV-2022-37544',
        'ACC-JV-2022-37547',
        'ACC-JV-2022-37549',
        'ACC-JV-2022-37551',
        'ACC-JV-2022-37565',
        'ACC-JV-2022-37571',
        'ACC-JV-2022-37573',
        'ACC-JV-2022-37576',
        'ACC-JV-2022-37577',
        'ACC-JV-2022-37578',
        'ACC-JV-2022-37582',
        'ACC-JV-2022-37595',
        'ACC-JV-2022-37600',
        'ACC-JV-2022-37611',
        'ACC-JV-2022-37914',
        'ACC-JV-2022-37920',
        'ACC-JV-2022-37960',
        'ACC-JV-2022-37942',
        'ACC-JV-2022-37992',
        'ACC-JV-2022-38492-1',
        'ACC-JV-2022-38500',
        'ACC-JV-2022-38506',
        'ACC-JV-2022-38924',
        'ACC-JV-2022-38929',
        'ACC-JV-2022-38983',
        'ACC-JV-2022-38957',
        'ACC-JV-2022-38962',
        'ACC-JV-2022-38971',
        'ACC-JV-2022-39954',
        'ACC-JV-2022-39956',
        'ACC-JV-2022-39980',
        'ACC-JV-2022-39998',
        'ACC-JV-2023-00042',
        'ACC-JV-2023-00049',
        'ACC-JV-2023-00051',
        'ACC-JV-2023-00061',
        'ACC-JV-2023-00065',
        'ACC-JV-2023-00067',
        'ACC-JV-2023-00070',
        'ACC-JV-2023-00076',
        'ACC-JV-2023-03596',
        'ACC-JV-2023-03607',
        'ACC-JV-2023-03628',
        'ACC-JV-2023-03631',
        'ACC-JV-2023-03639',
        'ACC-JV-2023-03731',
        'ACC-JV-2023-03738',
        'ACC-JV-2023-03749',
        'ACC-JV-2023-03760',
        'ACC-JV-2023-04024',
        'ACC-JV-2023-04030',
        'ACC-JV-2023-04037',
        'ACC-JV-2023-04044',
        'ACC-JV-2023-04049',
        'ACC-JV-2023-04088',
        'ACC-JV-2023-04091',
        'ACC-JV-2023-04093',
        'ACC-JV-2023-04096',
        'ACC-JV-2023-04100',
        'ACC-JV-2023-04106',
        'ACC-JV-2023-04110',
        'ACC-JV-2023-04112',
        'ACC-JV-2023-04116',
        'ACC-JV-2023-04117',
        'ACC-JV-2023-04118',
        'ACC-JV-2023-04123',
        'ACC-JV-2023-04129',
        'ACC-JV-2023-04131',
        'ACC-JV-2023-04314',
        'ACC-JV-2023-04315',
        'ACC-JV-2023-05282',
        'ACC-JV-2023-05286',
        'ACC-JV-2023-05291',
        'ACC-JV-2023-05299',
        'ACC-JV-2023-05473',
        'ACC-JV-2023-05478',
        'ACC-JV-2023-05482',
        'ACC-JV-2023-05493',
        'ACC-JV-2023-11090',
        'ACC-JV-2023-05633-3',
        'ACC-JV-2023-11093',
        'ACC-JV-2023-05883-2',
        'ACC-JV-2023-11095',
        'ACC-JV-2023-06858-2',
        'ACC-JV-2023-07383',
        'ACC-JV-2023-07399',
        'ACC-JV-2023-07405',
        'ACC-JV-2023-08005',
        'ACC-JV-2023-08009',
        'ACC-JV-2023-09003',
        'ACC-JV-2023-09012',
        'ACC-JV-2023-09442',
        'ACC-JV-2023-09460',
        'ACC-JV-2023-09692',
        'ACC-JV-2023-09705',
        'ACC-JV-2023-09731',
        'ACC-JV-2023-10649',
        'ACC-JV-2023-10948',
        'ACC-JV-2023-11164',
        'ACC-JV-2023-14569',
        'ACC-JV-2023-14741',
        'ACC-JV-2023-14745',
        'ACC-JV-2023-15271',
        'ACC-JV-2023-15283',
    ]
    data = []
    for v in vouchers:
        # unset_additional_fees(v)
        # set_additional_fees(v)
        set_totals(v)
    frappe.db.commit()  # v16: REVIEW - check if needed

def set_totals(jv):
    jv_doc = frappe.get_doc("Journal Entry",jv)
    suspense_jv = None
    for a in jv_doc.accounts:
        if re.search('suspense', a.account, re.IGNORECASE):
            suspense_jv = a
    if suspense_jv is None:
        frappe.throw("ERROR")
    
    frappe.db.set_value(
                "Journal Entry", jv_doc.name,
                {
                    'total_debit': suspense_jv.credit,
                    'total_credit': suspense_jv.credit,
                },
                update_modified=False
            )


@frappe.whitelist()
def unset_additional_fees(jv):
    jv_doc = frappe.get_doc("Journal Entry",jv)
    bank_jv = None
    suspense_jv = None
    gateway_jv = None
    # frappe.throw(f"{jv_doc.accounts[2].account}")
    for a in jv_doc.accounts:
        if not (re.search('suspense', a.account, re.IGNORECASE) or re.search('gateway', a.account, re.IGNORECASE)):
            bank_jv = a
        elif re.search('suspense', a.account, re.IGNORECASE):
            suspense_jv = a
        elif re.search('gateway', a.account, re.IGNORECASE):
            gateway_jv = a
    if suspense_jv == None or bank_jv == None or gateway_jv == None:
        frappe.throw(f"Missing...in {jv} : {suspense_jv} {bank_jv} {gateway_jv} {jv_doc.accounts}")
    
    suspense_amount = bank_jv.debit
    # Update Suspense JV
    frappe.db.set_value(
                        "Journal Entry Account",
                        suspense_jv.name,
                        {
                            'credit': bank_jv.debit,
                            'credit_in_account_currency': bank_jv.debit
                        },
                        update_modified=False
                    )
    gl_entry = frappe.get_all(
                "GL Entry",
                filters={"voucher_no": jv_doc.name, "account": ["=", suspense_jv.account]},
                fields=["*"],
            )
    frappe.db.set_value(
                "GL Entry", gl_entry[0]["name"],
                {
                            'credit': bank_jv.debit,
                            'credit_in_account_currency': bank_jv.debit
                        },
                        update_modified=False
            )
    
    # Delete Extra Row
    frappe.delete_doc('Journal Entry Account', gateway_jv.name,ignore_permissions=True,)

    gl_entry = frappe.get_all(
                "GL Entry",
                filters={"voucher_no": jv_doc.name, "account": ["=", gateway_jv.account]},
                fields=["*"],
            )

    frappe.db.sql(f"""
                    delete from `tabGL Entry` where name = '{gl_entry[0]['name']}'
                    """)
    # frappe.delete_doc('GL Entry', gl_entry[0]['name'],ignore_permissions=True,)



@frappe.whitelist()
def set_additional_fees(jv):
    jv_doc = frappe.get_doc("Journal Entry",jv)
    suspense_jv = None
    for a in jv_doc.accounts:
        if re.search('suspense', a.account, re.IGNORECASE):
            suspense_jv = a
    base_amount = suspense_jv.credit
    actual_donation = round(base_amount * 100 /( 100 - 2.36))
    fees = actual_donation - base_amount
    # Update Suspense Row with Additional Amount
    frappe.db.set_value(
                        "Journal Entry Account",
                        suspense_jv.name,
                        {
                            'credit': actual_donation,
                            'credit_in_account_currency': actual_donation
                        },
                        update_modified=False
                    )
    gl_entry = frappe.get_all(
                "GL Entry",
                filters={"voucher_no": jv_doc.name, "account": ["=", suspense_jv.account]},
                fields=["*"],
            )
    frappe.db.set_value(
                "GL Entry", gl_entry[0]["name"],
                {
                            'credit': actual_donation,
                            'credit_in_account_currency': actual_donation
                        },
                        update_modified=False
            )
    # Add Extra Row
    fees_doc = frappe.get_doc({
        "doctype": "Journal Entry Account",
        "parent":jv_doc.name,
        "parentfield":"accounts",
        "parenttype":"Journal Entry",
        "idx":3,
        "account":"Gateway Charges - HKMJ",
        "account_type":"Expense Account",
        "cost_center":"Main - HKMJ",
        "account_currency":"INR",
        "debit_in_account_currency":fees,
        "debit":fees,
        "exchange_rate":1.0
    })
    fees_doc.insert(ignore_permissions=True)

    gl_fees_doc = frappe.get_doc({
        "doctype":"GL Entry",
        "docstatus":1,
        "posting_date":gl_entry[0]["posting_date"],
        "account":"Gateway Charges - HKMJ",
        "cost_center":"Main - HKMJ",
        "debit":fees,
        "debit_in_account_currency":fees,
        "account_currency":"INR",
        "voucher_type":"Journal Entry",
        "voucher_no":gl_entry[0]["voucher_no"],
        "remarks":gl_entry[0]["remarks"],
        "fiscal_year":gl_entry[0]["fiscal_year"],
        "company":gl_entry[0]["company"],
    })
    gl_fees_doc.insert(ignore_permissions=True)

    # Update Overall Voucher

    frappe.db.set_value(
                "Journal Entry", jv_doc.name,
                {
                    'total_debit': actual_donation,
                    'total_credit': actual_donation
                },
                update_modified=False
            )
    # return base_amount, actual_donation, fees,fees_doc.as_dict()
    # frappe.db.sql("update ")
    # return jv_doc.as_dict()
