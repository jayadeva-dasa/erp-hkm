frappe.treeview_settings["Cost Head"] = {
  breadcrumb: "Cost Heads",
  get_tree_root: false,
  root_label: "All Cost Head",
  get_tree_nodes:
    "hkm.erpnext___custom.doctype.cost_head.cost_head.get_children",
  add_tree_node: "hkm.erpnext___custom.doctype.cost_head.cost_head.add_node",
  ignore_fields: ["parent_cost_head"],
  onload: function (treeview) {
    treeview.make_tree();
  },
  fields: [
    {
      fieldtype: "Check",
      fieldname: "is_group",
      label: __("Is Group"),
    },
  ],
};
