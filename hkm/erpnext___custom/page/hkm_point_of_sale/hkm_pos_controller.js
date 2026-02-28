hkm.PointOfSale.Controller = class {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;
		this.setup();
	}

	setup() {
		this.prepare_dom();
		this.check_opening_entry();
	}

	prepare_dom() {
		this.wrapper.$page = $(this.wrapper).find(".page-content");
		this.wrapper.$page.empty().append(`
			<div class="hkm-pos-container">
				<div class="hkm-pos-sidebar"></div>
				<div class="hkm-pos-main">
					<div class="hkm-pos-header"></div>
					<div class="hkm-pos-products"></div>
				</div>
				<div class="hkm-pos-cart"></div>
			</div>
		`);

		this.$container = this.wrapper.$page.find(".hkm-pos-container");
		this.$sidebar = this.$container.find(".hkm-pos-sidebar");
		this.$main = this.$container.find(".hkm-pos-main");
		this.$header = this.$container.find(".hkm-pos-header");
		this.$products = this.$container.find(".hkm-pos-products");
		this.$cart = this.$container.find(".hkm-pos-cart");
	}

	check_opening_entry() {
		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.hkm_check_opening_entry",
			args: { user: frappe.session.user },
			callback: (r) => {
				if (r.message && r.message.length) {
					this.opening_entry = r.message[0];
					this.pos_profile = this.opening_entry.pos_profile;
					this.company = this.opening_entry.company;
					this.init_pos();
				} else {
					this.show_opening_dialog();
				}
			},
		});
	}

	show_opening_dialog() {
		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.get_applicable_pos_profiles",
			callback: (r) => {
				const applicable_profiles = (r.message || []).filter(Boolean);
				this._show_opening_dialog_with_profiles(applicable_profiles);
			},
		});
	}

	_show_opening_dialog_with_profiles(applicable_profiles) {
		if (!applicable_profiles.length) {
			frappe.msgprint({
				title: __("No POS Profile"),
				message: __("You are not assigned to any POS Profile. Please contact your administrator to add you in the Applicable for Users list of a POS Profile."),
				indicator: "red",
			});
			return;
		}

		const dialog = new frappe.ui.Dialog({
			title: __("Create POS Opening Entry"),
			fields: [
				{
					fieldtype: "Link",
					label: __("POS Profile"),
					fieldname: "pos_profile",
					options: "POS Profile",
					reqd: 1,
					get_query: () => ({
						filters: { name: ["in", applicable_profiles] },
					}),
					onchange: () => {
						const profile = dialog.get_value("pos_profile");
						if (profile) {
							frappe.db.get_value("POS Profile", profile, "company").then((r) => {
								dialog.set_value("company", r.message.company);
							});
						}
					},
				},
				{
					fieldtype: "Link",
					label: __("Company"),
					fieldname: "company",
					options: "Company",
					reqd: 1,
					read_only: 1,
				},
				{
					fieldtype: "Section Break",
				},
				{
					fieldtype: "Currency",
					label: __("Opening Cash"),
					fieldname: "opening_cash",
					default: 0,
				},
			],
			primary_action_label: __("Submit"),
			primary_action: (values) => {
				const balance_details = [
					{
						mode_of_payment: "Cash",
						opening_amount: values.opening_cash || 0,
					},
				];

				frappe.call({
					method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.hkm_create_opening_voucher",
					args: {
						pos_profile: values.pos_profile,
						company: values.company,
						balance_details: JSON.stringify(balance_details),
					},
					callback: (r) => {
						if (r.message) {
							dialog.hide();
							this.opening_entry = r.message;
							this.pos_profile = values.pos_profile;
							this.company = values.company;
							this.init_pos();
						}
					},
				});
			},
		});

		dialog.show();
	}

	init_pos() {
		this.load_pos_profile().then(() => {
			this.init_components();
			this.load_data();
		});
	}

	load_pos_profile() {
		return frappe.db.get_doc("POS Profile", this.pos_profile).then((profile) => {
			this.profile = profile;
			this.price_list = profile.selling_price_list;
			this.warehouse = profile.warehouse;
			this.currency = profile.currency;
			
			// Set default customer from POS Profile
			if (profile.customer) {
				this.customer = profile.customer;
				// set a fallback immediately so input shows something on first render
				this.customer_name = profile.customer;
				frappe.db.get_value("Customer", profile.customer, "customer_name").then((r) => {
					this.customer_name = r.message.customer_name || profile.customer;
					// if cart is already rendered, update the input value
					if (this.$cart) {
						this.$cart.find('.customer-search').val(this.customer_name);
					}
				});
			}
		});
	}

	init_components() {
		this.init_header();
		this.init_products();
		this.init_cart();
		this.init_sidebar();
	}

	init_header() {
		const opening_date = frappe.datetime.str_to_user(this.opening_entry.period_start_date);
		const opening_time = this.opening_entry.posting_time || '';
		
		// Get opening amount safely
		let opening_amount = 0;
		if (this.opening_entry.balance_details && this.opening_entry.balance_details.length > 0) {
			opening_amount = this.opening_entry.balance_details[0].opening_amount || 0;
		}
		
		this.$header.html(`
			<div class="hkm-pos-header-wrapper">
				<div class="hkm-pos-header-top">
					<div class="hkm-pos-opening-info">
						<div class="opening-details">
							<span class="opening-date">📅 ${opening_date} ${opening_time}</span>
							<span class="opening-amount">💰 ${format_currency(opening_amount, this.opening_entry.company_currency)}</span>
						</div>
					</div>
					<div class="opening-inline-stats">
						<div class="stat-chip">
							<span class="chip-label">${__("Invoices")}</span>
							<span class="chip-value today-invoice-count">-</span>
						</div>
						<div class="stat-chip">
							<span class="chip-label">${__("Sales")}</span>
							<span class="chip-value today-sales-amount">-</span>
						</div>
					</div>
					<div class="header-icon-actions">
						<button class="btn btn-sm btn-icon btn-recent-orders" title="${__("Recent Orders")}">
							📋
						</button>
						<button class="btn btn-sm btn-icon btn-new-order" title="${__("New Order")}">
							📄
						</button>
						<button class="btn btn-sm btn-icon btn-close-pos" title="${__("Close POS")}">
							🔒
						</button>
					</div>
				</div>
				<div class="hkm-pos-header-bottom">
					<div class="hkm-pos-search">
						<input type="text" class="form-control search-items-input" placeholder="${__("Search items by name, barcode...")}" />
					</div>
					<div class="hkm-pos-customer-select">
						<input type="text" class="form-control customer-search-header" 
							placeholder="${__("Customer...")}" 
							value="${this.customer_name || ''}" />
					</div>
				</div>
			</div>
		`);
		// Fetch running totals since opening
		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.get_closing_data",
			args: { pos_opening_entry: this.opening_entry.name },
			callback: (r) => {
				if (r.message) {
					const data = r.message;
					this.$header.find('.today-invoice-count').text(data.total_invoices || 0);
					this.$header.find('.today-sales-amount').text(
						format_currency(data.total_sales || 0, this.opening_entry.company_currency)
					);
				}
			}
		});

		this.$search = this.$header.find(".search-items-input");
		this.$search.on("input", frappe.utils.debounce(() => {
			this.search_term = this.$search.val();
			if (this.search_term) {
				this.search_and_add_item();
			} else {
				this.load_items();
			}
		}, 300));
		
		// Bind header button events
		this.$header.find(".btn-recent-orders").on("click", () => {
			this.show_recent_orders();
		});
		
		this.$header.find(".btn-new-order").on("click", () => {
			this.new_order();
		});

		// Close POS button
		this.$header.find(".btn-close-pos").on("click", () => {
			this.close_pos();
		});
	}

	init_sidebar() {
		this.$sidebar.html(`
			<div class="hkm-pos-sidebar-content">
				<div class="hkm-pos-logo">
					<div class="sidebar-company">${this.company}</div>
					<div class="sidebar-pos-profile">${this.pos_profile}</div>
				</div>
				<div class="hkm-pos-categories"></div>
			</div>
		`);

		this.$categories = this.$sidebar.find(".hkm-pos-categories");
		this.load_categories();
	}

	load_categories() {
		return frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.hkm_get_parent_item_group",
			args: { pos_profile: this.pos_profile },
			callback: (r) => {
				if (r.message) {
					this.root_item_group = r.message;
					this.current_item_group = r.message;
					this.render_categories();
					this.load_items();
				}
			},
		});
	}

	render_categories() {
		// Get item groups from POS profile (top-level)
		const item_groups = this.profile.item_groups || [];

		let html = `
			<div class="category-block" data-level="root">
				<div class="category-parent active" data-group="${this.root_item_group}">
					<span class="category-icon">📦</span>
					<span class="category-title">${__("All Items")}</span>
				</div>
			</div>
		`;

		item_groups.forEach((group) => {
			html += `
				<div class="category-block" data-level="0" data-group="${group.item_group}">
					<div class="category-parent" data-group="${group.item_group}">
						<span class="category-icon">📁</span>
						<span class="category-title">${group.item_group}</span>
						<span class="chevron">▾</span>
					</div>
					<div class="subcategory-list"></div>
				</div>
			`;
		});

		this.$categories.html(html);

		const selectGroup = (group) => {
			this.current_item_group = group;
			this.load_items();
		};

		// Toggle + select parent
		this.$categories.find('.category-parent').on('click', (e) => {
			const $parent = $(e.currentTarget);
			const group = $parent.data('group');
			const $block = $parent.closest('.category-block');
			const $list = $block.find('.subcategory-list');
			
			// toggle expanded visual state
			const wasExpanded = $block.hasClass('expanded');
			$block.toggleClass('expanded');
			
			// show/hide the list
			if (wasExpanded) {
				$list.slideUp(200);
			} else {
				$list.slideDown(200);
			}
			
			// load children if first time
			if ($list.children().length === 0) {
				this.load_child_groups(group, $list);
			}
			
			// highlight active parent and clear active child
			this.$categories.find('.category-parent').removeClass('active');
			$parent.addClass('active');
			this.$categories.find('.subcategory-item').removeClass('active');
			selectGroup(group);
		});

		// Auto-expand and select the first real parent
		const $first = this.$categories.find('.category-block[data-level="0"]').first();
		if ($first.length) {
			$first.addClass('expanded');
			const group = $first.data('group');
			const $list = $first.find('.subcategory-list');
			$list.show();
			this.load_child_groups(group, $list);
			selectGroup(group);
		}
	}

	load_child_groups(parent_group, $container) {
		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.hkm_get_child_item_groups",
			args: { parent: parent_group },
			callback: (r) => {
				if (r.message && r.message.length) {
					let html = '';
					r.message.forEach((g) => {
						html += `
							<div class="subcategory-item" data-group="${g.name}">
								<span class="subcategory-name">${g.name}</span>
								<span class="chevron sm">›</span>
							</div>
						`;
					});
					$container.html(html);
					$container.find('.subcategory-item').on('click', (e) => {
						e.stopPropagation();
						const $sub = $(e.currentTarget);
						this.$categories.find('.subcategory-item').removeClass('active');
						$sub.addClass('active');
						this.current_item_group = $sub.data('group');
						this.load_items();
					});
				}
			}
		});
	}

	init_products() {
		this.$products.html(`
			<div class="hkm-pos-products-grid"></div>
		`);
		this.$products_grid = this.$products.find(".hkm-pos-products-grid");
	}

	init_cart() {
		this.cart_items = [];
		this.render_cart();
	}

	render_cart() {
		const subtotal = this.cart_items.reduce((sum, item) => sum + (item.qty * item.rate), 0);
		const tax_amount = this.tax_amount || 0;
		const total = subtotal + tax_amount;

		let items_html = "";
		this.cart_items.forEach((item, idx) => {
			items_html += `
				<div class="cart-item compact" data-idx="${idx}">
					<div class="cart-item-row">
						<div class="cart-item-info">
							<div class="cart-item-name">${item.item_name}</div>
							<div class="cart-item-meta">${item.uom || item.stock_uom} • ${format_currency(item.rate, this.currency)}/unit</div>
						</div>
						<button class="btn-remove" data-idx="${idx}">🗑️</button>
					</div>
					<div class="cart-item-row">
						<div class="cart-item-qty">
							<button class="btn-qty-minus" data-idx="${idx}">−</button>
							<input type="number" class="qty-input" data-idx="${idx}" value="${item.qty}" min="0.001" step="0.001" />
							<button class="btn-qty-plus" data-idx="${idx}">+</button>
						</div>
						<div class="cart-item-price">
							${format_currency(item.qty * item.rate, this.currency)}
						</div>
					</div>
				</div>
			`;
		});

		// Calculate total item count
		const total_items = this.cart_items.reduce((sum, item) => sum + item.qty, 0);
		
		this.$cart.html(`
			<div class="hkm-pos-cart-content">
				<div class="cart-items">
					${items_html || '<div class="cart-empty">' + __("No items in cart") + '</div>'}
				</div>
				<div class="cart-summary compact">
					<div class="summary-row">
						<span>${__("Subtotal")} <span class="item-count">(${total_items.toFixed(1)} items)</span></span>
						<span>${format_currency(subtotal, this.currency)}</span>
					</div>
					<div class="summary-row discount-row">
						<span>${__("Discount")}</span>
						<div class="discount-controls">
							<input type="number" class="discount-input" placeholder="0" value="${this.discount_value || 0}" min="0" step="0.01" />
							<button class="btn-discount-type" data-type="${this.discount_type || 'amount'}">
								${this.discount_type === 'percent' ? '%' : '₹'}
							</button>
						</div>
					</div>
					<div class="summary-row">
						<span>${__("Tax")}</span>
						<span>${format_currency(tax_amount, this.currency)}</span>
					</div>
					<div class="summary-row total">
						<span>${__("Total")}</span>
						<span>${format_currency(total - (this.discount_amount || 0), this.currency)}</span>
					</div>
				</div>
				<div class="cart-actions">
					<button class="btn btn-primary btn-lg btn-pay-now" ${this.cart_items.length === 0 ? 'disabled' : ''}>
						${__("Generate Invoice")}
					</button>
				</div>
			</div>
		`);

		// Bind events
		this.$cart.find(".btn-qty-minus").on("click", (e) => {
			const idx = $(e.currentTarget).data("idx");
			this.update_cart_qty(idx, -1);
		});

		this.$cart.find(".btn-qty-plus").on("click", (e) => {
			const idx = $(e.currentTarget).data("idx");
			this.update_cart_qty(idx, 1);
		});

		this.$cart.find(".btn-remove").on("click", (e) => {
			const idx = $(e.currentTarget).data("idx");
			this.remove_from_cart(idx);
		});

		// Handle direct quantity input
		this.$cart.find(".qty-input").on("change", (e) => {
			const idx = $(e.currentTarget).data("idx");
			const new_qty = parseFloat($(e.currentTarget).val()) || 0;
			if (new_qty > 0) {
				this.set_cart_qty(idx, new_qty);
			} else {
				this.remove_from_cart(idx);
			}
		});

		// Setup customer autocomplete in header
		const $customer_input = this.$header.find(".customer-search-header");
		$customer_input.on("input", frappe.utils.debounce(() => {
			const term = $customer_input.val();
			if (term.length >= 2) {
				this.search_customers(term, $customer_input);
			}
		}, 300));

		this.$cart.find(".btn-pay-now").on("click", () => {
			this.process_payment();
		});

		// Handle discount input
		this.$cart.find(".discount-input").on("change", (e) => {
			this.discount_value = parseFloat($(e.currentTarget).val()) || 0;
			this.calculate_discount();
			this.render_cart();
		});

		// Handle discount type toggle
		this.$cart.find(".btn-discount-type").on("click", (e) => {
			const $btn = $(e.currentTarget);
			this.discount_type = this.discount_type === 'percent' ? 'amount' : 'percent';
			this.calculate_discount();
			this.render_cart();
		});
	}

	load_data() {
		// Items will be loaded after categories are loaded
	}

	load_items() {
		if (!this.current_item_group) {
			// Wait for categories to load first
			return;
		}

		this.$products_grid.html('<div class="loading">Loading items...</div>');

		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.hkm_get_items",
			args: {
				start: 0,
				page_length: 40,
				price_list: this.price_list,
				item_group: this.current_item_group,
				pos_profile: this.pos_profile,
				search_term: this.search_term || "",
			},
			callback: (r) => {
				if (r.message && r.message.items) {
					this.render_items(r.message.items);
				} else {
					this.$products_grid.html('<div class="no-items">No items found</div>');
				}
			},
		});
	}

	render_items(items) {
		let html = "";
		items.forEach((item) => {
			const in_stock = item.actual_qty > 0 || !item.is_stock_item;
			// Use selling_price (with GST) if available, otherwise base price
			const display_price = item.selling_price || item.price_list_rate || 0;
			// Round to whole number for display
			const rounded_price = Math.round(display_price);
			
			// Show full item code (no truncation)
			const item_code = item.item_code;
			
			// Show stock quantity with UOM
			let stock_display = '';
			if (item.is_stock_item && in_stock) {
				// Show 1 decimal for all quantities
				const qty = item.actual_qty.toFixed(1);
				const uom = item.stock_uom;
				stock_display = `<div class="product-stock">${qty} ${uom}</div>`;
			}
			
			html += `
				<div class="product-card revamped ${!in_stock ? 'out-of-stock' : ''}" data-item='${JSON.stringify(item).replace(/'/g, "&apos;")}'>
					<div class="product-card-inner">
						<div class="product-name">${item.item_name}</div>
						<div class="product-code">${item_code}</div>
						<div class="product-pricing">
							<span class="product-price">${format_currency(rounded_price, item.currency, 0)}</span>
							${stock_display}
						</div>
						${!in_stock ? '<div class="stock-badge">Out of Stock</div>' : ''}
					</div>
				</div>
			`;
		});

		this.$products_grid.html(html);

		// Click anywhere on card to add item
		this.$products_grid.find(".product-card").on("click", (e) => {
			const $card = $(e.currentTarget);
			if ($card.hasClass("out-of-stock")) {
				return;
			}
			const item = JSON.parse($card.attr("data-item").replace(/&apos;/g, "'"));
			this.add_to_cart(item);
			
			// Clear search field and show all items
			if (this.search_term) {
				this.$search.val("");
				this.search_term = "";
				this.load_items();
			}
		});
	}

	add_to_cart(item) {
		const existing_idx = this.cart_items.findIndex((i) => i.item_code === item.item_code);
		if (existing_idx !== -1) {
			// Item exists - increment qty and move to top
			const existing = this.cart_items[existing_idx];
			existing.qty += 1;
			// Remove from current position and add to top
			this.cart_items.splice(existing_idx, 1);
			this.cart_items.unshift(existing);
		} else {
			// New item - add at the top
			this.cart_items.unshift({
				item_code: item.item_code,
				item_name: item.item_name,
				rate: item.price_list_rate || 0,
				qty: 1,
				uom: item.uom,
				stock_uom: item.stock_uom,
				image: item.item_image,
			});
		}
		this.calculate_taxes();
	}

	update_cart_qty(idx, delta) {
		const item = this.cart_items[idx];
		if (item) {
			item.qty += delta;
			if (item.qty <= 0) {
				this.cart_items.splice(idx, 1);
			}
			this.calculate_taxes();
		}
	}

	set_cart_qty(idx, qty) {
		const item = this.cart_items[idx];
		if (item) {
			item.qty = qty;
			if (item.qty <= 0) {
				this.cart_items.splice(idx, 1);
			}
			this.calculate_taxes();
		}
	}

	remove_from_cart(idx) {
		this.cart_items.splice(idx, 1);
		this.calculate_taxes();
	}

	new_order() {
		this.cart_items = [];
		this.discount_amount = 0;
		this.discount_value = 0;
		this.discount_type = 'amount';
		// Keep default customer from POS Profile
		if (this.profile && this.profile.customer) {
			this.customer = this.profile.customer;
			frappe.db.get_value("Customer", this.profile.customer, "customer_name").then((r) => {
				this.customer_name = r.message.customer_name || this.profile.customer;
				this.render_cart();
			});
		} else {
			this.customer = null;
			this.customer_name = null;
			this.render_cart();
		}
	}

	search_customers(term, $input) {
		frappe.call({
			method: "frappe.desk.search.search_link",
			args: {
				doctype: "Customer",
				txt: term,
				page_length: 20
			},
			callback: (r) => {
				if (r.message && r.message.length) {
					this.show_customer_dropdown(r.message, $input);
				}
			}
		});
	}

	show_customer_dropdown(customers, $input) {
		// Remove existing dropdown
		$(".customer-dropdown").remove();

		const $dropdown = $('<div class="customer-dropdown"></div>');
		customers.forEach((customer) => {
			const $item = $(`<div class="customer-dropdown-item">${customer.value} - ${customer.description || ''}</div>`);
			$item.on("click", () => {
				this.customer = customer.value;
				this.customer_name = customer.value;
				$input.val(customer.value);
				$dropdown.remove();
				this.render_cart();
			});
			$dropdown.append($item);
		});

		// Position dropdown relative to input
		const inputOffset = $input.offset();
		const inputHeight = $input.outerHeight();
		$dropdown.css({
			position: 'absolute',
			top: inputOffset.top + inputHeight,
			left: inputOffset.left,
			width: $input.outerWidth(),
			'z-index': 1000
		});

		$('body').append($dropdown);

		// Close dropdown on outside click
		$(document).on("click.customer-dropdown", (e) => {
			if (!$(e.target).closest(".customer-dropdown, .customer-search-header").length) {
				$dropdown.remove();
				$(document).off("click.customer-dropdown");
			}
		});
	}

	process_payment() {
		// Prevent duplicate submissions
		if (this.is_processing) {
			frappe.show_alert({
				message: __("Please wait, invoice is being created..."),
				indicator: "orange",
			});
			return;
		}

		if (!this.customer) {
			frappe.msgprint(__("Please enter a customer name first"));
			return;
		}

		if (this.cart_items.length === 0) {
			frappe.msgprint(__("Cart is empty"));
			return;
		}

		// Set processing flag
		this.is_processing = true;

		// Disable button and show processing state
		const $btn = this.$cart.find(".btn-pay-now");
		$btn.prop("disabled", true);
		$btn.html(`<span class="btn-processing">⏳ ${__("Processing...")}</span>`);

		// Show loading
		frappe.show_alert({
			message: __("Creating invoice..."),
			indicator: "blue",
		});

		// Create POS Invoice
		const subtotal = this.cart_items.reduce((sum, item) => sum + (item.qty * item.rate), 0);

		// Use custom method to create and submit invoice with proper paid_amount
		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.create_pos_invoice",
			args: {
				customer: this.customer,
				pos_profile: this.pos_profile,
				company: this.company,
				items: this.cart_items.map((item) => ({
					item_code: item.item_code,
					item_name: item.item_name,
					qty: item.qty,
					rate: item.rate,
					uom: item.uom || item.stock_uom,
					warehouse: this.warehouse,
				})),
				payment_amount: subtotal,
				discount_amount: this.discount_amount || 0,
			},
			callback: (r) => {
				// Reset processing flag
				this.is_processing = false;

				if (r.message) {
					const invoice_name = r.message.name;
					
					// Show success message
					frappe.show_alert({
						message: __("Invoice {0} created successfully", [invoice_name]),
						indicator: "green",
					});

					// Print the invoice immediately
					this.print_invoice(invoice_name);

					// Clear cart for next order (this will re-enable the button)
					this.new_order();
				} else {
					// Re-enable button on error
					const $btn = this.$cart.find(".btn-pay-now");
					$btn.prop("disabled", false);
					$btn.html(__("Generate Invoice"));
				}
			},
			error: () => {
				// Reset processing flag and button on error
				this.is_processing = false;
				const $btn = this.$cart.find(".btn-pay-now");
				$btn.prop("disabled", false);
				$btn.html(__("Generate Invoice"));
			},
		});
	}

	print_invoice(invoice_name) {
		// Use sales_invoice_print_format if available, otherwise fall back to print_format
		const print_format = this.profile.sales_invoice_print_format || this.profile.print_format || "POS Invoice";
		// Always print without letterhead for POS invoices
		const url = `/printview?doctype=Sales%20Invoice&name=${invoice_name}&format=${print_format}&no_letterhead=1`;
		
		// Create hidden iframe for printing
		const printFrame = document.createElement('iframe');
		printFrame.style.position = 'absolute';
		printFrame.style.width = '0';
		printFrame.style.height = '0';
		printFrame.style.border = 'none';
		document.body.appendChild(printFrame);
		
		printFrame.onload = function() {
			try {
				printFrame.contentWindow.print();
				// Remove iframe after print dialog
				setTimeout(() => {
					if (printFrame.parentNode) {
						document.body.removeChild(printFrame);
					}
				}, 1000);
			} catch(e) {
				console.error('Print error:', e);
				if (printFrame.parentNode) {
					document.body.removeChild(printFrame);
				}
			}
		};
		
		printFrame.src = url;
	}

	search_and_add_item() {
		if (!this.current_item_group) {
			return;
		}

		this.$products_grid.html('<div class="loading">Searching...</div>');

		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.hkm_get_items",
			args: {
				start: 0,
				page_length: 40,
				price_list: this.price_list,
				item_group: this.current_item_group,
				pos_profile: this.pos_profile,
				search_term: this.search_term || "",
			},
			callback: (r) => {
				if (r.message && r.message.items) {
					const items = r.message.items;
					
					// If only one item found and it's in stock, add it automatically
					if (items.length === 1) {
						const item = items[0];
						const in_stock = item.actual_qty > 0 || !item.is_stock_item;
						
						if (in_stock) {
							this.add_to_cart(item);
							this.$search.val("");
							this.search_term = "";
							this.load_items();
							return;
						}
					}
					
					// Otherwise show all results
					this.render_items(items);
				} else {
					this.$products_grid.html('<div class="no-items">No items found</div>');
				}
			},
		});
	}

	show_recent_orders() {
		const dialog = new frappe.ui.Dialog({
			title: __("Recent Orders"),
			size: "large",
			fields: [
				{
					fieldtype: "HTML",
					fieldname: "orders_html",
				},
			],
		});

		// Load recent orders
		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.get_recent_pos_invoices",
			args: {
				pos_profile: this.pos_profile,
				limit: 20,
			},
			callback: (r) => {
				if (r.message && r.message.length) {
					let html = '<div class="recent-orders-list">';
					r.message.forEach((invoice) => {
						html += `
							<div class="recent-order-item">
								<div class="order-info">
									<div class="order-name"><strong>${invoice.name}</strong></div>
									<div class="order-customer">${invoice.customer_name || invoice.customer}</div>
									<div class="order-date">${frappe.datetime.str_to_user(invoice.posting_date)} ${invoice.posting_time}</div>
								</div>
								<div class="order-amount">
									<strong>${format_currency(invoice.grand_total, invoice.currency)}</strong>
								</div>
								<div class="order-actions">
									<button class="btn btn-sm btn-default btn-print-order" data-invoice="${invoice.name}">
										🖨️ Print
									</button>
									<button class="btn btn-sm btn-danger btn-cancel-order" data-invoice="${invoice.name}">
										✖ Cancel
									</button>
								</div>
							</div>
						`;
					});
					html += '</div>';
					
					dialog.fields_dict.orders_html.$wrapper.html(html);
					
					// Bind print buttons
					dialog.fields_dict.orders_html.$wrapper.find(".btn-print-order").on("click", (e) => {
						const invoice_name = $(e.currentTarget).data("invoice");
						this.print_invoice(invoice_name);
					});

					// Bind cancel buttons
					dialog.fields_dict.orders_html.$wrapper.find(".btn-cancel-order").on("click", (e) => {
						const invoice_name = $(e.currentTarget).data("invoice");
						frappe.confirm(
							`${__("Cancel Sales Invoice")} ${invoice_name}?`,
							() => {
								frappe.call({
									method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.cancel_pos_invoice",
									args: { name: invoice_name },
									callback: () => {
										frappe.show_alert({ message: __("Invoice cancelled"), indicator: "green" });
										dialog.hide();
									},
									error: (err) => {
										frappe.msgprint({ title: __("Error"), message: err.message || __("Failed to cancel"), indicator: "red" });
									}
								});
							}
						);
					});
				} else {
					dialog.fields_dict.orders_html.$wrapper.html('<p class="text-muted text-center" style="padding: 40px;">No recent orders found</p>');
				}
			},
		});

		dialog.show();
	}

	calculate_discount() {
		const subtotal = this.cart_items.reduce((sum, item) => sum + (item.qty * item.rate), 0);
		
		if (this.discount_type === 'percent') {
			this.discount_amount = (subtotal * (this.discount_value || 0)) / 100;
		} else {
			this.discount_amount = this.discount_value || 0;
		}
	}

	calculate_taxes() {
		if (this.cart_items.length === 0) {
			this.tax_amount = 0;
			this.render_cart();
			return;
		}

		// Call server to calculate taxes based on POS Profile settings
		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.calculate_taxes",
			args: {
				pos_profile: this.pos_profile,
				customer: this.customer || this.profile.customer,
				company: this.company,
				items: this.cart_items.map((item) => ({
					item_code: item.item_code,
					qty: item.qty,
					rate: item.rate,
					uom: item.uom || item.stock_uom,
				})),
			},
			callback: (r) => {
				if (r.message) {
					this.tax_amount = r.message.total_taxes_and_charges || 0;
					this.render_cart();
				}
			},
		});
	}

	close_pos() {
		// Check if there are unsaved items in cart
		if (this.cart_items.length > 0) {
			frappe.msgprint({
				title: __("Unsaved Items"),
				message: __("Please complete or clear the current transaction before closing POS."),
				indicator: "orange",
			});
			return;
		}

		// Check if POS profile requires cash amount
		frappe.db.get_value("POS Profile", this.pos_profile, "ask_cash_collection").then((r) => {
			const ask_cash_amount = r.message.ask_cash_collection || false;

			// Build dialog fields
			let dialog_fields = [
				{
					fieldtype: "HTML",
					fieldname: "closing_info",
				},
			];

			// Add cash amount field if enabled in POS profile
			if (ask_cash_amount) {
				dialog_fields.push({
					fieldtype: "Currency",
					fieldname: "cash_collection",
					label: __("Cash Collection"),
					description: __("Enter the total cash collected during this POS session"),
					reqd: 1,
				});
			}

			// Show closing dialog
			const dialog = new frappe.ui.Dialog({
				title: __("Close POS"),
				fields: dialog_fields,
				primary_action_label: __("Submit Closing Entry"),
				primary_action: (values) => {

					// Validate cash amount if required
					if (ask_cash_amount) {
						const cash_amount = values.cash_collection || 0;
						if (cash_amount <= 0) {
							frappe.msgprint({
								title: __("Invalid Cash Amount"),
								message: __("Cash collection must be greater than zero."),
								indicator: "red",
							});
							return;
						}
					}

					this.submit_closing_entry(dialog, values);
				},
			});

			// Load closing data
			frappe.call({
				method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.get_closing_data",
				args: {
					pos_opening_entry: this.opening_entry.name,
				},
				callback: (r) => {
					if (r.message) {
						const data = r.message;
						let html = `
							<div class="pos-closing-summary">
								<h4>POS Closing Summary</h4>
								<table class="table table-bordered">
									<tr>
										<th>Opening Entry</th>
										<td>${this.opening_entry.name}</td>
									</tr>
									<tr>
										<th>Opening Date</th>
										<td>${frappe.datetime.str_to_user(this.opening_entry.period_start_date)}</td>
									</tr>
									<tr>
										<th>Opening Amount</th>
										<td>${format_currency(data.opening_amount, this.opening_entry.company_currency)}</td>
									</tr>
									<tr>
										<th>Total Invoices</th>
										<td>${data.total_invoices}</td>
									</tr>
									<tr>
										<th>Total Sales</th>
										<td>${format_currency(data.total_sales, this.opening_entry.company_currency)}</td>
									</tr>
									<tr class="table-success">
										<th>Expected Closing Amount</th>
										<td><strong>${format_currency(data.expected_amount, this.opening_entry.company_currency)}</strong></td>
									</tr>
								</table>
								<div class="alert alert-info">
									<strong>Note:</strong> This will create a POS Closing Entry and settle all invoices.
								</div>
							</div>
						`;
						dialog.fields_dict.closing_info.$wrapper.html(html);
					}
				},
			});

			dialog.show();
		});
	}

	submit_closing_entry(dialog, values = {}) {
		dialog.hide();
		frappe.show_alert({
			message: __("Creating POS Closing Entry..."),
			indicator: "blue",
		});

		frappe.call({
			method: "hkm.erpnext___custom.page.hkm_point_of_sale.hkm_point_of_sale.create_closing_entry",
			args: {
				pos_opening_entry: this.opening_entry.name,
				cash_collection: values.cash_collection || null,
			},
			callback: (r) => {
				if (r.message) {
					frappe.show_alert({
						message: __("POS Closed Successfully: {0}", [r.message.name]),
						indicator: "green",
					});

					// Redirect to POS Opening Entry list or reload
					setTimeout(() => {
						window.location.reload();
					}, 2000);
				}
			},
			error: (r) => {
				frappe.msgprint({
					title: __("Error"),
					message: __("Failed to close POS. Please try again."),
					indicator: "red",
				});
			},
		});
	}

	refresh() {
		if (this.pos_profile) {
			this.load_items();
		}
	}
};
