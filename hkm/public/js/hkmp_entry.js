frappe.listview_settings["HKMP Entry"] = {



     add_fields: ["status"],

     get_indicator: function (doc) {

          if (doc.status === "Pending") {
               return [__("Pending"), "yellow", "status,=,Pending"];
          } else if (doc.status === "Processing") {
               return [__("Processing"), "orange", "status,=,Processing"];
          } else if (doc.status === "Success") {
               return [__("Success"), "green", "status,=,Success"];
          } else if (doc.status === "Failed") {
               return [__("Failed"), "red", "status,=,Failed"];
          }


     },
};