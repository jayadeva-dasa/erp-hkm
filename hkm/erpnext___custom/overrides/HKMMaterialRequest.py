from datetime import datetime, timedelta
from erpnext.stock.doctype.material_request import material_request
import frappe
from frappe import _

from erpnext.stock.doctype.material_request.material_request import MaterialRequest
from hkm.erpnext___custom.overrides.buying_validations import (
    check_items_are_not_from_template,
    validate_work_order_item,
)
from frappe.desk.form.utils import add_comment


class HKMMaterialRequest(MaterialRequest):
    def __init__(self, *args, **kwargs):
        super(HKMMaterialRequest, self).__init__(*args, **kwargs)

    def on_submit(self):
        super().on_submit()
        self.send_mrn_approval_notification()

    def send_mrn_approval_notification(self):
        if (
            self.material_request_type == "Material Issue"
            or self.material_request_type == "Material Transfer"
        ):
            # Get item names
            item_names = [item.item_name for item in self.items if item.item_name]
            item_names_str = ", ".join(item_names[:5])  # Limit to first 5 items
            if len(item_names) > 5:
                item_names_str += f" and {len(item_names) - 5} more item(s)"

            subject = f"MRN Approval for Items: {item_names_str}"

            # Get document URL
            doc_url = frappe.utils.get_url_to_form(self.doctype, self.name)

            message = f"""
            <h3>Hare Krishna!</h3>

            <h3>Please check the below MRN</h3>

            <a 
            style="
              background-color: #4CAF50;
              border: none;
              color: white;
              padding: 15px 32px;
              text-align: center;
              text-decoration: none;
              display: inline-block;
              font-size: 16px;
            "
            href="{doc_url}">
            Click to open Document
            </a>
            """

            # Get recipients - try to get stock issuer from warehouse, else use default
            recipients = []
            if self.items and self.set_warehouse:
                # Get both stock issuers in one query
                warehouse_data = frappe.db.get_value(
                    "Warehouse",
                    self.set_warehouse,
                    ["stock_issuer", "secondary_stock_issuer"],
                    as_dict=True,
                )

                # Collect all stock issuer user names
                stock_issuer_users = [
                    user
                    for user in [
                        warehouse_data.get("stock_issuer"),
                        warehouse_data.get("secondary_stock_issuer"),
                    ]
                    if user
                ]

                # Get all emails in one query
                if stock_issuer_users:
                    user_emails = frappe.db.get_all(
                        "User",
                        filters={"name": ["in", stock_issuer_users]},
                        pluck="email",
                    )
                    recipients.extend([email for email in user_emails if email])
            # Fallback to default stock issuer if no warehouse issuer found
            if not recipients:
                try:
                    settings = frappe.get_cached_doc("HKM General Settings")
                    if (
                        hasattr(settings, "default_stock_issuer")
                        and settings.default_stock_issuer
                    ):
                        user_email = frappe.db.get_value(
                            "User", settings.default_stock_issuer, "email"
                        )
                        if user_email:
                            recipients.append(user_email)
                except frappe.DoesNotExistError:
                    pass

            # Final fallback to owner if no stock issuer configured
            # if not recipients:
            #     recipients.append(self.owner)

            if recipients:
                email_args = {
                    "recipients": recipients,
                    "message": message,
                    "subject": subject,
                    "reference_doctype": self.doctype,
                    "reference_name": self.name,
                    "reply_to": self.owner,
                    "delayed": False,
                    "sender": self.owner,
                }
                frappe.enqueue(
                    method=frappe.sendmail,
                    queue="short",
                    timeout=300,
                    is_async=True,
                    **email_args,
                )
                add_comment(
                    reference_doctype=self.doctype,
                    reference_name=self.name,
                    content="MRN Approval Notification Sent",
                    comment_email=self.owner,
                    comment_by=frappe.db.get_value("User", self.owner, "full_name"),
                )

    def before_save(self):
        super().before_save()
        prefix = ""
        wo = self.for_a_work_order
        if self.material_request_type == "Purchase" and wo == 1:
            prefix = "Work Request"
        elif self.material_request_type == "Purchase":
            prefix = "Purchase"
        elif self.material_request_type == "Material Issue":
            prefix = "Material Issue"
        elif self.material_request_type == "Material Transfer":
            prefix = "Material Transfer"
        else:
            prefix = "MRN"
        item_names = []
        for item in self.items:
            item_names.append(item.item_name)
        item_names = ",".join(item_names)
        item_names = (
            item_names[0:39] + "..." if len(item_names) > 40 else item_names[0:39]
        )

        self.title = prefix + " for " + item_names

    def validate(self):
        super().validate()
        check_items_are_not_from_template(self)
        validate_work_order_item(self)
        self.validate_purchase_item()
        self.validate_asset_item()
        self.validate_work_head()
        self.validate_disabled_items()
        return

    def validate_disabled_items(self):
        item_codes = [item.item_code for item in self.items if item.item_code]
        disabled_items = frappe.get_list(
            "Item",
            pluck="name",
            filters={"disabled": 1, "name": ["in", item_codes]},
        )
        if disabled_items:
            # Find the first disabled item in self.items to get the correct row number
            disabled_items_set = set(disabled_items)
            for item in self.items:
                if item.item_code in disabled_items_set:
                    frappe.throw(
                        _(
                            "Row#{0}: Item {1} is disabled. Please select a different item."
                        ).format(
                            item.idx,
                            frappe.bold(item.item_code),
                        ),
                        title=_("Invalid Item"),
                    )
        return

    def validate_work_head(self):
        ##TODO : It is not being used now.
        return
        if self.work_head:
            work_request_head_doc = frappe.get_doc("Work Request Head", self.work_head)
            if work_request_head_doc.status == "Completed":
                frappe.throw(
                    "Work Request is not allowed in this Work Request Head as it is COMPLETED."
                )
        return

    def validate_asset_item(self):
        if not self.material_request_type == "Material Issue":
            return
        invalid_items = []
        asset_items = frappe.get_list(
            "Item", pluck="name", filters={"disabled": 0, "is_fixed_asset": 1}
        )
        for d in self.get("items"):
            if d.item_code in asset_items:
                invalid_items.append(d)
        for d in invalid_items:
            frappe.throw(
                _(
                    "Row#{0}: Asset Item {1} is not allowed for MRN of Issue.<br> Please select a stock item."
                ).format(
                    d.idx,
                    frappe.bold(d.item_code),
                ),
                title=_("Invalid Item"),
            )
        return

    def validate_purchase_item(self):
        if not self.material_request_type == "Purchase":
            return

        if self.for_a_work_order:
            return

        purchase_for_stock = False

        # allowed_role = frappe.db.get_single_value('HKM ERPNext Settings', 'purchase_request_creator_for_stock')

        allowed_role = "Stock User"

        if allowed_role in frappe.get_roles(frappe.session.user):
            purchase_for_stock = True

        for d in self.get("items"):
            item = frappe.get_doc("Item", d.item_code)
            if item.is_stock_item and not purchase_for_stock:
                frappe.throw(
                    _(
                        "Row#{0}: {1} is a Stock Item. So you can't make a Purchase MRN for that. It should be routed through Store<br>It is allowed only for Role : {2}"
                    ).format(
                        d.idx,
                        frappe.bold(d.item_name),
                        frappe.bold(allowed_role),
                    ),
                    title=_("Not Allowed"),
                )
        return

    def on_cancel(self):
        super().on_cancel()
        # TODO: This needs to be relooked after major refactoring of OLD MRNs
        # self.notify_on_cancellation()

    def notify_on_cancellation(self):
        material_purchase_link = self.material_purchase_link
        if material_purchase_link:
            mrn_purchase = frappe.get_doc(self.doctype, material_purchase_link)
            message = """
					<h3>Hare Krishna,</h3>
					<p>The MRN below has been cancelled by the user.</p>
					<h3><span style="color: #000080;">MRN Details:</span></h3>
					<p>MRN Issue Link : {}</p>
					<p>MRN Purchase Link : {}</p>
					<p>Cancelled By : {}</p>
					""".format(
                frappe.utils.get_url_to_form(self.doctype, self.name),
                frappe.utils.get_url_to_form(self.doctype, material_purchase_link),
                frappe.session.user,
            )
            email_args = {
                "recipients": [mrn_purchase.owner, self.owner],
                "message": message,
                "subject": "Issue MRN :{} Cancelled".format(self.name),
                "reference_doctype": self.doctype,
                "reference_name": self.name,
                "reply_to": self.owner,
                "delayed": False,
                "sender": self.owner,
            }
            frappe.enqueue(
                method=frappe.sendmail,
                queue="short",
                timeout=300,
                is_async=True,
                **email_args,
            )
            # frappe.sendmail(**email_args)


# def is_eligible_mrn(mrn):
# 	if mrn.material_request_type == 'Material Issue':
# 		return True
# 	elif mrn.material_request_type == 'Purchase' and mrn.for_a_work_order == 1:
# 		return True
# 	else:
# 		return False

# # Exclusive for SYSP
# DEPARTMENTS_TO_BE_NOTIFIED = ['Maintenance - HKMJ','Civil Department - HKMJ', 'Annakoot-TSFJ']
# def notify_mrn(self,method):
# return # No More Required as asked by SYSP
# if self.department in DEPARTMENTS_TO_BE_NOTIFIED and is_eligible_mrn(self):
# 	item_string = ""
# 	for idx,item in enumerate(self.items):
# 			item_string = item_string+"""
# 										<tr style="height: 18px;">
# 										<td style="width: 6.50568%; height: 18px; text-align: center;"> {} </td>
# 										<td style="width: 45.7103%; height: 18px; text-align: center;"> {} </td>
# 										<td style="width: 7.21585%; height: 18px; text-align: center;"> {} </td>
# 										<td style="width: 12.1874%; height: 18px; text-align: center;"> {} </td>
# 										</tr>
# 									  """.format(idx+1,item.item_name,item.uom,item.qty)

# 	items_string = """
# 				<table style="border-collapse: collapse; width: 100%; height: 36px;" border="1">
# 				<tbody>
# 				<tr style="height: 18px;">
# 				<td style="width: 6.50568%; height: 18px; text-align: center;"><strong><span style="color: #800000;">S.No.</span></strong></td>
# 				<td style="width: 45.7103%; height: 18px; text-align: center;"><strong><span style="color: #800000;">Item Name</span></strong></td>
# 				<td style="width: 7.21585%; height: 18px; text-align: center;"><strong><span style="color: #800000;">UOM</span></strong></td>
# 				<td style="width: 12.1874%; height: 18px; text-align: center;"><strong><span style="color: #800000;">Quantity</span></strong></td>
# 				</tr>
# 				{}
# 				</tbody>
# 				</table>
# 			   """.format(item_string)
# 	message = """
# 			<h3>Hare Krishna,</h3>
# 			<p>The MRN has been submitted just now.</p>
# 			<h3><span style="color: #000080;">MRN Details:</span></h3>
# 			<p>Department : {}</p>
# 			<p>MRN Link : {}</p>
# 			<p>Submitted By : {}</p>
# 			<hr>
# 			<p>Purpose : {}</p>
# 			<h3><span style="color: #000080;">Item Details:</span></h3>
# 			{}
# 			""".format(
# 				self.department,
# 				frappe.utils.get_url_to_form(self.doctype, self.name),
# 				#frappe.utils.get_url_to_form(self.doctype, material_purchase_link),
# 				frappe.session.user,
# 				self.purpose,
# 				items_string
# 				)
# 	email_args = {
# 		"recipients": ['sysd@hkm-group.org'],
# 		"message": message,
# 		"subject": 'MRN :{} Created'.format(self.name),
# 		"reference_doctype": self.doctype,
# 		"reference_name": self.name,
# 		"reply_to": frappe.session.user,
# 		"delayed":False,
# 		"sender":frappe.session.user
# 		}
# 	frappe.enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)
# return


def remove_unused_mrns():
    settings = frappe.get_cached_doc("HKM General Settings")
    if settings.material_request_expiry:
        past_date_str = (
            datetime.now() - timedelta(days=settings.material_request_expiry)
        ).strftime("%Y-%m-%d")

        for i in frappe.get_all(
            "Material Request",
            filters={"creation": ["<", past_date_str], "status": "Pending"},
            pluck="name",
        ):
            doc = frappe.get_doc("Material Request", i)

            if frappe.db.sql_list(
                """
                SELECT mr.name
                WHERE mr.name = %s
                JOIN `tabPurchase Order Item` poi
                    ON poi.material_request = mr.name
                LEFT JOIN `tabPurchase Order` po
                    ON po.name = poi.parent
                WHERE po.docstatus != 2
            """,
                i,
            ):
                continue

            if doc.docstatus == 1:
                try:
                    doc.cancel()
                except frappe.exceptions.LinkExistsError as e:
                    print(e)
            elif doc.docstatus == 0:
                frappe.delete_doc("Material Request", i)


def remove_unused_purchase_orders():
    settings = frappe.get_cached_doc("HKM General Settings")
    if settings.purchase_order_expiry:
        past_date_str = (
            datetime.now() - timedelta(days=settings.purchase_order_expiry)
        ).strftime("%Y-%m-%d")

        today = datetime.now().date()
        cutoff_date = today - timedelta(days=15)

        purchase_orders = frappe.db.sql(
            f"""
            SELECT po.name as name , 
            po.docstatus as docstatus
            -- pri.purchase_order as purchase_receipt,
            -- pii.purchase_order as purchase_invoice,
            -- pei.reference_name as payment_entry
            FROM `tabPurchase Order` po
            JOIN `tabPurchase Order Item` poi
                ON po.name = poi.parent
            LEFT JOIN `tabPurchase Receipt Item` pri
                ON pri.purchase_order = po.name AND pri.docstatus != 2
            LEFT JOIN `tabPurchase Invoice Item` pii
                ON pii.purchase_order = po.name AND pii.docstatus != 2
            LEFT JOIN `tabPayment Entry Reference` pei
                ON pei.reference_name = po.name AND pei.reference_doctype = "Purchase Order" AND pei.docstatus != 2
            WHERE po.per_billed = 0
            AND po.per_received = 0
            AND po.docstatus != 2
            AND pri.purchase_order IS NULL
            AND pii.purchase_order IS NULL
            AND pei.reference_name IS NULL
            AND po.transaction_date > "2024-09-01"
            AND po.creation < '{past_date_str}'
             AND po.modified < '{cutoff_date}'
            GROUP BY po.name    
            """,
            as_dict=True,  # This makes the result a single list of tuples
        )
        for po in purchase_orders:
            try:
                if po.docstatus == 1:
                    doc = frappe.get_doc("Purchase Order", po.name)
                    doc.cancel()
                    frappe.db.set_value(
                        "Purchase Order", po.name, "workflow_state", "Cancelled"
                    )
                elif po.docstatus == 0:
                    frappe.delete_doc("Purchase Order", po.name)
            except Exception as e:
                print(e)
        frappe.db.commit()  # v16: REVIEW - check if needed
