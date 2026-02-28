import "./dimensions";
import "./hide_accounting_dimensions_for_auditor.js";

frappe.ui.keys.add_shortcut({
  description: "Show Balance Sheet",
  shortcut: "alt+b",
  action: () => {
    frappe.set_route("List", "Journal Entry");
  },
});

frappe.ui.keys.add_shortcut({
  shortcut: "Ctrl+k",
  action: () => {
    frappe.set_route("Form", "Purchase Invoice", "new");
  },
  ignore_inputs: true,
  description: __("Create new Purchase Invoice"),
});
