frappe.listview_settings["HKM Payment Request"] = {

    has_indicator_for_draft: true,
    has_indicator_for_cancelled: true,

    add_fields: ["batch_number", "request_id" , "status", "creation"],

    get_indicator: function (doc) {
        // console.log("hare krishna");


        if (doc.docstatus == 2) {
            return [__("Cancelled"), "red", "docstatus,=,2"];
        }

        if (doc.docstatus === 1) {
            // console.log(doc);

            if (!doc.batch_number && !doc.request_id) {
                return [__("Submitted"), "green", "docstatus,=,1"];
            }

           return [doc.status, "green", "docstatus,=,1"];
        }

        // fallback
        return [__("Draft"), "gray", "docstatus,=,0"];
    },
    
    // Add formatter to display creation date in list view
    formatters: {
        creation: function(value, df, doc) {
            if (value) {
                return frappe.datetime.str_to_user(value);
            }
            return "";
        }
    },
    
    // Method to prepare data for list view rendering
    prepare_data: function(data) {
        if (data.creation) {
            data.formatted_creation = frappe.datetime.str_to_user(data.creation);
        }
        return data;
    }
};