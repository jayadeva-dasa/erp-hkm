// frappe.ui.form.on("Supplier", {
//   refresh: function (frm) {
//     frm.add_custom_button(
//       __("Send Statement"),
//       function () {
//         frappe.prompt(
//           [
//             {
//               fieldname: "email",
//               label: __("Email"),
//               fieldtype: "Data",
//               reqd: 1,
//             },
//             {
//               fieldname: "from_date",
//               label: __("From Date"),
//               fieldtype: "Date",
//               reqd: 1,
//             },
//             {
//               fieldname: "to_date",
//               label: __("To Date"),
//               fieldtype: "Date",
//               reqd: 1,
//             },
//           ],
//           function (data) {
//             if (data.to_date < data.from_date) {
//               frappe.msgprint(__("To Date cannot be less than From Date"));
//             } else {
//               frappe.call({
//                 method:
//                   "hkm.erpnext___custom.extend.supplier.send_supplier_statement",
//                 args: {
//                   supplier: frm.doc.name,
//                   from_date: data.from_date,
//                   to_date: data.to_date,
//                   email: data.email,
//                 },
//                 callback: function (r) {
//                   frappe.msgprint(__("Statement Sent"));
//                 },
//               });
//             }
//           }
//         );
//       },
//       "Actions"
//     );
//   },
// });
