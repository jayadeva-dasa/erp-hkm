frappe.ui.form.on("Payment Entry", {
    refresh: function (frm) {

        if (frm.fields_dict["volunteer"]) {
            frm.set_query("volunteer", function () {
                return {
                    filters: { enabled: 1 }
                };
            });
        } else {
            console.log("Volunteer field does not exist in this Doctype");
        }

    },
    onload: function (frm) {
        if (frm.fields_dict["volunteer"]) {
            frm.set_query("volunteer", function () {
                return {
                    filters: { enabled: 1 }
                };
            });
        } else {
            console.log("Volunteer field does not exist in this Doctype");
        }
    }
});