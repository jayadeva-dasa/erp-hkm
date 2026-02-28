from __future__ import unicode_literals
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
    get_dimensions,
)
import frappe, erpnext
from frappe import _
from frappe.utils import flt

from erpnext.accounts.doctype.pos_invoice.pos_invoice import (
    POSInvoice,
    get_stock_availability,
)
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals


class HKMPOSInvoice(POSInvoice):
    def __init__(self, *args, **kwargs):
        super(HKMPOSInvoice, self).__init__(*args, **kwargs)
        
    def calculate_taxes_and_totals(self):
        """
        Override to use fixed tax calculation that properly handles
        rounding adjustments on tax-exempt items.
        """
        # Use the fixed version of taxes calculation
        taxes_calc = HKMCalculateTaxesAndTotals(self)
        taxes_calc.calculate()

    def before_save(self):
        return super().before_save()

    def validate(self):
        super().validate()
        self.set_accounting_dimensions()
        self.validate_if_zero_rate_item()
        self.validate_full_amount()
        self.cummulative_stock_availbility()
        # Fix: Ensure tax-exempt items don't receive rounding adjustments
        self.fix_rounding_adjustment_on_exempt_items()
        return
        # FOR RTGP
        # self.validate_discount()
        # if self.coupon_code:
        # 	from erpnext.accounts.doctype.pricing_rule.utils import validate_coupon_code
        # 	validate_coupon_code(self.coupon_code)

    def fix_rounding_adjustment_on_exempt_items(self):
        """
        Validation check: Ensure no tax-exempt items have non-zero tax amounts.
        
        This is a safety check to catch any cases where the main fix in
        HKMCalculateTaxesAndTotals.adjust_rounding_in_item_wise_tax_details()
        might not have been applied correctly.
        
        Note: The main fix is now in calculate_taxes_and_totals() override
        which uses HKMCalculateTaxesAndTotals class.
        
        Date: 2025-02-09
        """
        if not self.get("item_wise_tax_details"):
            return
        
        # Validation check: ensure no tax-exempt items have non-zero amounts
        for tax_row in self.get("item_wise_tax_details"):
            item_code = tax_row.get("item_code")
            tax_rate = flt(tax_row.get("tax_rate", 0))
            tax_amount = flt(tax_row.get("tax_amount", 0))
            
            # If tax-exempt item has non-zero tax amount, log warning
            if tax_rate == 0 and abs(tax_amount) > 0.01:  # Allow tiny floating point errors
                frappe.logger().warning(
                    f"POS Invoice {self.name}: Tax-exempt item '{item_code}' has "
                    f"non-zero tax amount: {tax_amount}. This should not happen with the fix applied."
                )
    
    def set_accounting_dimensions(self):
        dimensions = get_accounting_dimensions(as_list=True)
        if self.pos_profile:
            profile = frappe.get_doc("POS Profile", self.pos_profile)
            for dimension in dimensions:
                self.update({dimension: profile.get(dimension)})
                for item in self.get("items"):
                    item.update({dimension: profile.get(dimension)})

    def validate_full_amount(self):
        if self.paid_amount != self.rounded_total:
            frappe.errprint("Paid Amount: " + str(self.paid_amount))
            frappe.errprint("Total Amount: " + str(self.rounded_total))
            frappe.throw("Please check the Paid Amount. It can't be less or more.")
        return

    def validate_if_zero_rate_item(self):
        for item in self.get("items"):
            valuation_rate = frappe.get_value("Item", item.item_code, "valuation_rate")
            if item.rate == 0:
                frappe.throw(
                    "Sale Rate of <b>Item: {}</b> can't be ZERO".format(item.item_name)
                )
            if item.rate < valuation_rate:
                frappe.throw(
                    "Sale Rate({0}) of <b>Item: {1}</b> can't be less than it's Valuation Rate ({2})".format(
                        item.rate, item.item_name, valuation_rate
                    )
                )
        return

    @frappe.whitelist()
    def get_gst_breakup(self):
        rows = []
        total_tax = 0
        for item in self.items:
            qty = item.qty
            rate = item.rate
            # item_record = frappe.get_doc('Item', item.item_code)
            GSTp = 0
            tax_templates = frappe.db.sql(
                """
											select item.gst_hsn_code, tax_template.name as template, tax_template.cumulative_tax as rate
											from `tabItem` item
											join `tabItem Tax` item_tax
												on item_tax.parent = item.name
											join `tabItem Tax Template` tax_template
												on tax_template.name = item_tax.item_tax_template
											where tax_template.company = '{}' and item.name = '{}'
											""".format(
                    self.company, item.item_code
                ),
                as_dict=1,
            )
            if len(tax_templates) > 0:
                tax_template = tax_templates[0]
                GSTp = tax_template["rate"]
                row_index = self.search_rows(rows, tax_template["gst_hsn_code"], GSTp)
                if row_index is None:
                    temp_data = {
                        "HSN": tax_template["gst_hsn_code"],
                        "GSTp": GSTp,
                        "Taxable": qty * rate,
                        "CGSTI": qty * rate * GSTp / 200,
                        "SGSTI": qty * rate * GSTp / 200,
                    }
                    rows.append(temp_data)
                else:
                    rows[row_index]["Taxable"] += qty * rate
                    rows[row_index]["CGSTI"] = (
                        rows[row_index]["CGSTI"] + qty * rate * GSTp / 200
                    )
                    rows[row_index]["SGSTI"] = (
                        rows[row_index]["SGSTI"] + qty * rate * GSTp / 200
                    )
        for row in rows:
            row["Taxable"] = round(row["Taxable"], 2)
            row["CGSTI"] = round(row["CGSTI"], 2)
            row["SGSTI"] = round(row["SGSTI"], 2)
            total_tax += row["CGSTI"] + row["SGSTI"]
        total_tax = round(total_tax, 2)
        cashier = frappe.db.get_value("User", self.owner, "full_name")
        return rows, total_tax, cashier

    @frappe.whitelist()
    def get_company_address(self):
        adds = frappe.db.sql(
            """
						select address.*
						from `tabAddress` address
						join `tabDynamic Link` link on link.parent = address.name
						where link.link_name = '{}' and link.link_doctype = 'Company'
						""".format(
                self.company
            ),
            as_dict=1,
        )
        address = adds[0]

        formatted_address = (
            "%(address_line1)s, %(address_line2)s, %(city)s, %(state)s - %(pincode)s"
            % address
        )

        return formatted_address

    @frappe.whitelist()
    def get_items_segregated(self):
        item_group_data = {}

        for item in self.items:
            # item_record = frappe.get_doc('Item', item.item_code)
            grp = item.item_group
            qty = item.qty
            if grp not in item_group_data:
                item_group_data.setdefault(
                    grp,
                    {
                        item.item_code: frappe._dict(
                            {"name": item.item_name, "qty": qty}
                        )
                    },
                )
            else:
                grp_data = item_group_data[grp]
                if item.item_code not in grp_data:
                    grp_data.setdefault(
                        item.item_code, {"name": item.item_name, "qty": qty}
                    )
                else:
                    grp_data[item.item_code]["qty"] = (
                        grp_data[item.item_code]["qty"] + qty
                    )
                item_group_data.setdefault(grp, grp_data)

        # For Restaurant : Get the count of this bill

        token = (
            frappe.db.sql(
                f"""
						SELECT count(name) as token
						FROM `tabPOS Invoice`
						WHERE pos_profile = '{self.pos_profile}'
						AND posting_date = '{self.posting_date}'
						AND posting_time < '{self.posting_time}'
						"""
            )[0][0]
            + 1
        )

        return item_group_data, token

    def search_rows(self, rows, HSN, GSTp):
        for idx, r in enumerate(rows):
            if r["HSN"] == HSN and r["GSTp"] == GSTp:
                return idx
        return None

    def cummulative_stock_availbility(self):
        # items = [item.item_code for item in self.get("items")]
        # unique_items = list(set(items))
        warehouse = self.set_warehouse
        unique_items_qty = {}
        for d in self.get("items"):
            if d.item_code in unique_items_qty:
                unique_items_qty[d.item_code] = unique_items_qty[d.item_code] + d.qty
            else:
                unique_items_qty[d.item_code] = d.qty

        for item in unique_items_qty:
            available_stock, is_stock_item, is_negative_stock_allowed = (
                get_stock_availability(item, warehouse)
            )
            if is_negative_stock_allowed:
                continue
            if is_stock_item and flt(available_stock) < flt(unique_items_qty[item]):
                frappe.throw(
                    _(
                        "Stock quantity not enough for Item Code: {} under warehouse {}. Available quantity {}."
                    ).format(item, warehouse, available_stock, unique_items_qty[item]),
                    title=_("Item Unavailable"),
                )
        return

    def validate_discount(self):
        amount_threshold = 3000
        pos_profiles = [
            "POS - Donwcounter",
            "POS - RKM Book Counter",
            "POS - Temple Counter",
        ]
        if (not self.is_return) and self.pos_profile in pos_profiles:
            if (
                self.grand_total < amount_threshold
                and self.additional_discount_percentage != 0
            ):
                frappe.throw(
                    "Discount is not allowed for amount < {}".fomrat(amount_threshold)
                )
            if (
                self.grand_total >= amount_threshold
                and self.additional_discount_percentage != 5
            ):
                frappe.throw(
                    "Discount is not applied on amount >= {} or applied more".format(
                        amount_threshold
                    )
                )
        return


class HKMCalculateTaxesAndTotals(calculate_taxes_and_totals):
    """
    Extended taxes and totals calculator with fix for rounding adjustment
    on tax-exempt items.
    
    Issue: Core ERPNext applies rounding adjustments to the "last row" in
    item_wise_tax_details without checking if it's a tax-exempt item (0% rate).
    
    Fix: Override adjust_rounding_in_item_wise_tax_details() to skip items
    with 0% tax rate when selecting the row for rounding adjustment.
    
    Date: 2025-02-09
    Ref: /apps/hkm_jaipur/hkm_jaipur/cursor/fix_rounding_adjustment_tax_exempt_items_20250209/
    """
    
    def adjust_rounding_in_item_wise_tax_details(self):
        """
        FIXED VERSION: Adjust rounding differences in item-wise tax details.
        
        This method ensures that tax-exempt items (0% tax rate) are never
        selected as the target for rounding adjustments, regardless of their
        position in the items list or the charge type of the tax.
        
        Changes from original:
        - Line ~507: Added check for flt(d.rate) == 0 to skip ALL tax-exempt items
        - Original only skipped "Actual" charge types with 0 rate
        - Now skips percentage-based charges with 0% rate as well
        """
        def ignore_item_wise_tax_details(doc):
            # Helper to check if we should skip this calculation
            return doc.get("_action") == "submit" and frappe.flags.in_patch
        
        if ignore_item_wise_tax_details(self.doc):
            return

        if not self.doc.get("_item_wise_tax_details"):
            return

        invalid_rows = []

        # Reset temporary attributes
        for tax in self.doc.taxes:
            tax._total_tax_breakup = 0
            tax._last_row_idx = None

        for idx, d in enumerate(self.doc._item_wise_tax_details):
            tax = d.get("tax")
            
            # FIXED: Skip if no tax OR if rate is 0
            # This check skips:
            # 1. Tax-exempt percentage items (0% rate) - PRIMARY FIX
            #    Original bug only checked "Actual" charges, missing percentage charges at 0%
            # 2. "Actual" charge type (rate is always 0 for fixed-amount charges)
            #    These have their own rounding mechanism (see line 424-427 in taxes_and_totals.py)
            # 3. Any other edge cases with 0 rate
            #
            # WHY: Rounding adjustments should only go to items with calculated tax amounts.
            # Items with rate=0 either have no tax (exempt) or use a different calculation (Actual).
            if not tax or flt(d.rate) == 0:
                continue

            tax._total_tax_breakup += d.amount or 0
            tax._last_row_idx = idx

        # Apply rounding difference to the last taxable row
        for tax in self.doc.taxes:
            last_idx = tax._last_row_idx
            
            # Skip if no taxable items found (e.g., all items are tax-exempt or Actual charges)
            if last_idx is None:
                # Log warning if there's a significant rounding difference with no taxable items
                if frappe.conf.get("developer_mode"):
                    expected = flt(tax.base_tax_amount_after_discount_amount, 5)
                    actual = flt(tax._total_tax_breakup, 5)
                    diff = expected - actual
                    if abs(diff) > 0.01:
                        frappe.logger().warning(
                            f"Tax row {tax.idx} ({tax.description}): Rounding difference of {diff} "
                            f"but no taxable items to apply adjustment. All items have 0% rate."
                        )
                continue

            multiplier = -1 if tax.get("add_deduct_tax") == "Deduct" else 1
            expected_amount = tax.base_tax_amount_after_discount_amount * multiplier
            actual_breakup = tax._total_tax_breakup
            diff = flt(expected_amount - actual_breakup, 5)

            # Apply adjustment if within tolerance
            if abs(diff) <= 0.5:
                detail_row = self.doc._item_wise_tax_details[last_idx]
                
                # Safety check: Verify this is actually a taxable item
                if flt(detail_row.get("rate", 0)) == 0:
                    frappe.logger().error(
                        f"CRITICAL: Attempting to apply rounding adjustment to item with 0% rate! "
                        f"This should not happen. last_idx={last_idx}"
                    )
                    invalid_rows.append(
                        f"Row {tax.idx} (Error: Adjustment target has 0% rate)"
                    )
                    continue
                
                detail_row["amount"] = flt(detail_row["amount"] + diff, 5)
                
               
            else:
                invalid_rows.append(f"Row {tax.idx} (Difference: {diff})")

        if self.doc.flags.ignore_validate:
            return

        if invalid_rows:
            message = (
                _("Item Wise Tax Details do not match with Taxes and Charges at the following rows:")
                + "<br>"
                + "<br>".join(invalid_rows)
            )
            frappe.throw(_(message))
