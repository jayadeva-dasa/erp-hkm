"""Static knowledge used to turn terse errors into "what happened + how to fix it".

HINT_RULES: (regex on the plain-text error message, how-to-fix text).
    First matching rule wins. Regexes are matched case-insensitively against the
    message with HTML stripped. `{1}`, `{2}` ... in the fix text are filled from the
    regex groups.
"""

HINT_RULES = [
    # ---------------------------------------------------------------- GST / India Compliance
    (
        r"Please set (.+) to ensure Company GSTIN is fetched",
        "Select <b>{1}</b> on the form. It must be an Address of <b>your Company</b> that has the "
        "Company GSTIN filled. If none exists, open the Company &rarr; <b>Address &amp; Contact</b> "
        "&rarr; <b>Add Address</b> (Line 1, City, State, Pincode, GSTIN, GST Category) and then select it here.",
    ),
    (
        r"(.*address.*) is a mandatory field for GST Transactions",
        "Select the <b>{1}</b>. If none exists, open the party/company, go to the "
        "<b>Address &amp; Contact</b> tab and click <b>Add Address</b>. The address needs "
        "Line 1, City, State, Pincode, Country and (for registered parties) GSTIN + GST Category.",
    ),
    (
        r"(.*GSTIN.*) is a mandatory field for GST Transactions",
        "The selected address has no GSTIN. Either pick an address that has one, or open the "
        "Address and fill GSTIN / GST Category (use <i>Unregistered</i> if the party has no GSTIN).",
    ),
    (
        r"(.+) is a mandatory field for GST Transactions",
        "Fill in <b>{1}</b> &mdash; it is required because this transaction is liable for GST.",
    ),
    (
        r"Cannot charge GST in Row #?(\d+) since purchase is from a Supplier without GSTIN",
        "The supplier has no GSTIN. Either set the supplier's GST Category to <i>Unregistered</i> "
        "and remove the GST tax rows (or pick a 0% tax template), or add the supplier's GSTIN "
        "to its Address.",
    ),
    (
        r"Cannot charge GST in Row #?(\d+) since Company GSTIN and Party GSTIN are same",
        "Company and party share the same GSTIN. Check you picked the right Supplier/Customer "
        "and Billing Address, or remove the GST tax rows if this is an internal transfer.",
    ),
    (
        r"Cannot charge GST in Row #?(\d+) since export is without payment of GST",
        "This is an export without payment of GST. Remove the GST tax rows, or untick "
        "<i>Export without payment of GST</i> if tax should be charged.",
    ),
    (
        r"Cannot claim Input GST in Row #?(\d+) since purchase is being made from a dealer registered under Composition",
        "Composition-scheme suppliers cannot charge GST. Remove the GST tax rows from this document.",
    ),
    (
        r"Row #?(\d+): (.+) is not a valid GST account",
        "Pick a GST account that is set up in <b>GST Settings &rarr; GST Accounts</b> for this "
        "company, or ask Accounts to add it there.",
    ),
    (
        r"not a valid Place of Supply",
        "Re-select <b>Place of Supply</b> from the dropdown instead of typing it.",
    ),
    (
        r"Invalid HSN/SAC|HSN/SAC.*(?:mandatory|required|digits)",
        "Open the Item (or the item row) and correct <b>GST HSN Code</b>. Valid codes are "
        "digits only and of the length required for your turnover.",
    ),
    (
        r"Cannot use different Item Tax Templates in different rows",
        "Use the same <b>Item Tax Template</b> in every row that has the same item.",
    ),
    # ---------------------------------------------------------------- dates
    (
        r"To Date cannot be less than From Date|From Date must be before To Date",
        "Change the dates so that <b>From Date</b> is on or before <b>To Date</b>.",
    ),
    (
        r"From Date and To Date are mandatory",
        "Fill both <b>From Date</b> and <b>To Date</b> in the filters/form.",
    ),
    (
        r"Posting Date .* cannot be before Purchase Order date",
        "Set <b>Posting Date</b> on or after the Purchase Order date, or fix the order date on the PO.",
    ),
    (
        r"Due Date cannot be before (?:Posting|Supplier Invoice) Date|Due Date cannot be before",
        "Set <b>Due Date</b> on or after the posting / invoice date.",
    ),
    (
        r"Required By .*(?:before|cannot)|Reqd By Date|Required by Date",
        "Set <b>Required By</b> on or after the transaction date.",
    ),
    (
        r"not authorized to add or update entries before|Accounts Frozen|accounts? (?:is|are) frozen",
        "Accounts are frozen up to a date. Use a posting date after the freeze date, or ask a "
        "user with the <i>Accounts Frozen Date</i> role to unfreeze.",
    ),
    # ---------------------------------------------------------------- masters / links
    (
        r"Could not find (.+)",
        "The value you entered doesn't exist as a record. Clear the field and pick one from the "
        "dropdown, or create the missing record first (open its list and click <b>Add</b>).",
    ),
    (
        r"Item (.+) is disabled|(.+) is disabled",
        "Enable the item/record in its master, or remove it from this document.",
    ),
    (
        r"Company is mandatory|Company and Posting Date is mandatory",
        "Select the <b>Company</b> (and Posting Date) at the top of the form.",
    ),
    (
        r"Supplier Creation Request|not allowed to create a Supplier without GSTIN",
        "Suppliers without GSTIN cannot be created directly. Raise a <b>Supplier Creation "
        "Request</b> instead (or enter a valid GSTIN to create the supplier directly).",
    ),
    (
        r"Row #?(\d+): Item None does not exist",
        "Row {1} has no <b>Item Code</b>. Select an item in that row, or delete the empty row.",
    ),
    (
        r"(?:Quantity|Qty) .*cannot be zero|Quantity must be greater than zero",
        "Enter a quantity greater than 0 in that row, or delete the row.",
    ),
    (
        r"Warehouse required for stock Item",
        "Fill <b>Warehouse</b> in that row, or change the item so it is not a stock item.",
    ),
    (
        r"Target Warehouse is mandatory for internal transfers",
        "Fill <b>Target Warehouse</b> in that row.",
    ),
    (
        r"Accepted Warehouse and Rejected Warehouse cannot be same",
        "Choose a different <b>Rejected Warehouse</b> (or clear it if nothing is rejected).",
    ),
    (
        r"Conversion Factor is mandatory|UOM Conversion factor",
        "Open the Item &rarr; <b>Units of Measure</b> table and add the conversion between the "
        "stock UOM and the UOM used here, then set the same factor in the row.",
    ),
    (
        r"Unable to find exchange rate",
        "Open <b>Currency Exchange</b> and add a rate for that currency/date, or type the "
        "<b>Exchange Rate</b> manually in the form.",
    ),
    (
        r"Insufficient stock|Insufficient Stock|not enough stock",
        "Reduce the quantity, receive more stock first (Purchase Receipt / Stock Entry), or pick "
        "another warehouse.",
    ),
    (
        r"Item (.+) is not a stock Item|(.+) is not a stock Item",
        "Use a stock item here, or tick <b>Maintain Stock</b> on the Item.",
    ),
    (
        r"Cannot set quantity less than received",
        "The quantity can't go below what is already received. Raise it, or cancel the related receipt first.",
    ),
    # ---------------------------------------------------------------- accounting
    (
        r"Total Debit must be equal to Total Credit",
        "Adjust the debit/credit amounts in the Accounts table so both totals match (the message "
        "shows the difference).",
    ),
    (
        r"Both Debit and Credit values cannot be zero",
        "Enter an amount in either Debit or Credit for that row, or delete the empty row.",
    ),
    (
        r"Reference No and Reference Date is mandatory|Please enter Reference date",
        "For a Bank Entry fill <b>Cheque/Reference No</b> and <b>Cheque/Reference Date</b>.",
    ),
    (
        r"Party Type and Party is required for Receivable / Payable account",
        "In that row choose <b>Party Type</b> and <b>Party</b> (the account is a Receivable/Payable account).",
    ),
    (
        r"Cost Center is required for .Profit and Loss. account|Accounting Dimension .* is required for",
        "Fill <b>Cost Center</b> (and any accounting dimension named) in that row.",
    ),
    (
        r"Difference Amount must be zero",
        "Adjust the amounts until <b>Difference Amount</b> is 0.",
    ),
    (
        r"Please set default (.+) Account in Company",
        "Open the <b>Company</b> record &rarr; Accounts defaults and set the missing account, "
        "or select the account explicitly in the row.",
    ),
    (
        r"Paid Amount cannot be greater than",
        "Lower the <b>Paid Amount</b> to at most the outstanding amount.",
    ),
    # ---------------------------------------------------------------- HKM approval flow
    (
        r"has not been checked by the Purchase Manager",
        "Ask the Purchase Manager to open this document and click <b>Check</b> first.",
    ),
    (
        r"not the Current Approving Authority",
        "Only the current approver can approve. Wait for your turn, or ask the approver / "
        "System Manager to reassign.",
    ),
    (
        r"Document is locked, not allowed to modify field",
        "This field is locked after approval started. Cancel / amend the document, or ask a "
        "System Manager to unlock it.",
    ),
    (
        r"Cannot edit cancelled document",
        "Cancelled documents are read-only. Use <b>Amend</b> to create an editable copy.",
    ),
    # ---------------------------------------------------------------- framework
    (
        r"has been modified after you have opened it",
        "Someone else (or another tab) saved this document after you opened it. Click "
        "<b>Reload</b> (or press F5), re-apply your changes and save again.",
    ),
    (
        r"Insufficient Permission for (.+)|No permission for (.+)|Not permitted",
        "You don't have the role needed for this action. Ask your System Manager to grant it "
        "via <b>Role Permission Manager</b>.",
    ),
    (
        r"Cannot (?:delete|cancel) .* because it is linked|is linked with|Linked with",
        "Open the linked documents listed in the message and cancel/delete them first.",
    ),
    (
        r"Duplicate (?:Entry|entry)|already exists",
        "A record with this name/value already exists. Open the existing one, or use a different name.",
    ),
    (
        r"Cannot (?:edit|save) .* after submit|Not allowed to change .* after submission",
        "Submitted documents are locked. Cancel and amend the document to change this field.",
    ),
    # generic wording used all over ERPNext - keep these last
    (
        r"^(?:Row #?\d+:\s*)?(.+?) is (?:mandatory|required)\.?$",
        "Fill in <b>{1}</b> (in the row named in the message, if any) and save again.",
    ),
    (
        r"^Please (?:enter|select|set|specify) (.+?)\.?$",
        "Fill in <b>{1}</b> and try again.",
    ),
]


# Hint text per field type for "missing mandatory field".
FIELD_TYPE_HINTS = {
    "Link": "Pick a <b>{options}</b> from the dropdown. If it isn't in the list, create it first in the {options} list.",
    "Dynamic Link": "Pick a value from the dropdown (first fill the field that decides which type of record it is).",
    "Table": "Add at least one row to this table (click <b>Add Row</b>) and fill it.",
    "Table MultiSelect": "Pick at least one value.",
    "Select": "Choose one of the available options from the dropdown.",
    "Date": "Pick a date.",
    "Datetime": "Pick a date and time.",
    "Time": "Pick a time.",
    "Int": "Enter a whole number (0 counts as empty here &mdash; use 1 or more).",
    "Float": "Enter a number greater than 0.",
    "Currency": "Enter an amount greater than 0.",
    "Percent": "Enter a percentage.",
    "Attach": "Attach a file.",
    "Attach Image": "Attach an image.",
}

DEFAULT_FIELD_HINT = "Enter a value."

# Mandatory Link fields that point at these doctypes get extra, specific guidance.
LINK_DOCTYPE_HINTS = {
    "Address": (
        "Select an Address. If the party has none, open the Supplier/Customer/Company &rarr; "
        "<b>Address &amp; Contact</b> tab &rarr; <b>Add Address</b> (Line 1, City, State, Pincode, "
        "Country; add GSTIN for registered parties)."
    ),
    "Contact": (
        "Select a Contact. If none exists, open the Supplier/Customer &rarr; "
        "<b>Address &amp; Contact</b> tab &rarr; <b>Add Contact</b>."
    ),
    "Cost Center": "Pick the Cost Center from the dropdown (ask Accounts if you are unsure which one applies).",
    "Warehouse": "Pick the Warehouse from the dropdown; it must belong to the same Company.",
    "Item": "Pick the Item from the dropdown. If it doesn't exist, create it in the Item list first.",
    "Supplier": "Pick the Supplier. New suppliers must be created via Supplier Creation Request.",
    "Bank": "Pick the Bank. If it isn't listed, create it in the <b>Bank</b> list first.",
}

# Exception class name -> (what happened, how to fix). Used when nothing more specific is known.
EXCEPTION_HINTS = {
    "ZeroDivisionError": (
        "A calculation tried to divide by zero.",
        "Check that <b>Qty</b>, <b>Conversion Factor</b>, <b>Exchange Rate</b> and <b>Rate</b> "
        "are not 0 in every row, then save again.",
    ),
    "IndexError": (
        "The document is missing a table row that the system expects to exist.",
        "Make sure the <b>Items</b> (and other required tables) have at least one filled row.",
    ),
    "ValueError": (
        "One of the values has the wrong format (for example text in a number or date field).",
        "Check date fields use a valid date and number fields contain only digits.",
    ),
    "TypeError": (
        "A required value is empty, so the system could not complete a calculation or naming step.",
        "Fill in all required fields (marked red) and save again.",
    ),
    "AttributeError": (
        "A required value is empty, so the system could not continue.",
        "Fill in all required fields (marked red) and save again.",
    ),
    "KeyError": (
        "A value the system needs was not found in the document.",
        "Reload the form (F5), re-enter the details and save again.",
    ),
}
