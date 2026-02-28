frappe.provide("hkm.PointOfSale");

frappe.pages["hkm-point-of-sale"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("HKM Point of Sale"),
		single_column: true,
	});

	wrapper.hkm_pos = new hkm.PointOfSale.Controller(wrapper);
	window.cur_hkm_pos = wrapper.hkm_pos;
};

frappe.pages["hkm-point-of-sale"].refresh = function (wrapper) {
	if (wrapper.hkm_pos) {
		wrapper.hkm_pos.refresh();
	}
};
