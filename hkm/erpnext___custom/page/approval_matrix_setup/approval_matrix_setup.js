/**
 * Approval Matrix Setup Page
 * Modern implementation following dimension_value philosophy
 */

frappe.pages['approval_matrix_setup'].on_page_load = function(wrapper) {
	new ApprovalMatrixSetup(wrapper);
};

class ApprovalMatrixSetup {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Approval Matrix Setup',
			single_column: true
		});

		this.current_matrix = null;
		this.rules = []; // Array of {dimension_value, conditions: [{condition, approving_authority}]}
		this.doctypes = [];
		this.dimensions = [];
		this.dimension_values = [];
		this.user_names_cache = {}; // Cache for user full names
		this.ANY_DIMENSION_KEY = '__HKM_ANY_DIMENSION__';

		// Render the HTML template
		this.render_page();
		
		this.init();
	}

	async call_api(method, args = {}) {
		try {
			const { message } = await frappe.call({
				method: `hkm.erpnext___custom.page.approval_matrix_setup.approval_matrix_setup.${method}`,
				args,
				freeze: false
			});
			return message;
		} catch (error) {
			throw error;
		}
	}

	render_page() {
		// Get the main container
		this.body = this.page.main;
		
		// Render the HTML template
		$(frappe.render_template('approval_matrix_setup', {})).appendTo(this.body);
	}

	async init() {
		// Load initial data
		await this.load_master_data();
		
		// Setup UI
		this.setup_ui();
		this.bind_events();
		
		// Load matrices
		await this.load_matrices();
	}

	async load_master_data() {
		try {
			// Load doctypes, dimensions, and users in parallel
			const [doctypes, dimensions, users] = await Promise.all([
				this.call_api('get_doctypes'),
				this.call_api('get_dimensions'),
				this.call_api('get_users')
			]);

			this.doctypes = doctypes || [];
			this.dimensions = dimensions || [];
			this.users = users || [];
			
			// Build user names cache
			this.load_user_names();

		} catch (error) {
			frappe.msgprint(__('Error loading master data: {0}', [error.message]));
		}
	}

	load_user_names() {
		// Fetch all enabled users and cache their full names
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'User',
				filters: {
					enabled: 1,
					user_type: 'System User'
				},
				fields: ['name', 'full_name'],
				limit_page_length: 0
			},
			callback: (r) => {
				if (r.message) {
					r.message.forEach(user => {
						this.user_names_cache[user.name] = user.full_name || user.name;
					});
				}
			}
		});
	}

	setup_ui() {
		// Populate doctype dropdown
		const doctype_select = this.body.find('[data-field="target_doctype"]');
		doctype_select.empty().append('<option value="">Select DocType...</option>');
		this.doctypes.forEach(dt => {
			doctype_select.append(`<option value="${dt.name}">${dt.label}</option>`);
		});

		// Populate dimension dropdown
		const dimension_select = this.body.find('[data-field="dimension"]');
		dimension_select.empty().append('<option value="">Select Dimension...</option>');
		this.dimensions.forEach(dim => {
			dimension_select.append(`<option value="${dim.name}">${dim.label || dim.name}</option>`);
		});
	}

	bind_events() {
		const self = this;

		// Create new matrix
		this.body.on('click', '[data-action="create-new"]', () => {
			this.show_new_matrix_dialog();
		});

		// Cancel edit
		this.body.on('click', '[data-action="cancel-edit"]', () => {
			this.show_list();
		});

		// Print matrix
		this.body.on('click', '[data-action="print-matrix"]', () => {
			this.print_matrix();
		});


		// Save matrix
		this.body.on('click', '[data-action="save-matrix"]', () => {
			this.save_matrix();
		});

		// Add rule (new dimension value)
		this.body.on('click', '[data-action="add-rule"]', () => {
			this.add_rule();
		});

		// Add condition to existing rule
		this.body.on('click', '[data-action="add-condition"]', function() {
			const dimensionKey = $(this).data('dimension');
			self.add_condition_to_rule(dimensionKey);
		});

		// Remove rule
		this.body.on('click', '[data-action="remove-rule"]', function() {
			const dimensionKey = $(this).data('dimension');
			self.remove_rule(dimensionKey);
		});

		// Remove condition
		this.body.on('click', '[data-action="remove-condition"]', function() {
			const dimensionKey = $(this).data('dimension');
			const cond_idx = $(this).data('cond-idx');
			self.remove_condition(dimensionKey, cond_idx);
		});

		// Edit matrix
		this.body.on('click', '[data-action="edit-matrix"]', function() {
			const name = $(this).data('name');
			self.edit_matrix(name);
		});

		// Delete matrix
		this.body.on('click', '[data-action="delete-matrix"]', function() {
			const name = $(this).data('name');
			self.delete_matrix(name);
		});


		// Dimension change - load dimension values
		this.body.on('change', '[data-field="dimension"]', function() {
			const dimension = $(this).val();
			self.load_dimension_values(dimension);
		});
	}

	normalizeDimensionValue(value) {
		if (value === undefined || value === null || value === '' || value === 'null' || value === 'undefined' || value === this.ANY_DIMENSION_KEY) {
			return null;
		}
		return value;
	}

	getDimensionKey(value) {
		const normalized = this.normalizeDimensionValue(value);
		return normalized === null ? this.ANY_DIMENSION_KEY : normalized;
	}

	getDimensionLabel(value) {
		const normalized = this.normalizeDimensionValue(value);
		return normalized === null ? __('Any Dimension') : normalized;
	}

	findRuleByKey(dimensionKey) {
		const normalized = this.normalizeDimensionValue(dimensionKey);
		return this.rules.find(rule => this.normalizeDimensionValue(rule.dimension_value) === normalized);
	}

	removeRuleByKey(dimensionKey) {
		const normalized = this.normalizeDimensionValue(dimensionKey);
		this.rules = this.rules.filter(rule => this.normalizeDimensionValue(rule.dimension_value) !== normalized);
	}

	async load_matrices() {
		try {
			const matrices = await this.call_api('get_approval_matrices');
			this.render_matrices_list(matrices || []);
		} catch (error) {
			frappe.msgprint(__('Error loading matrices: {0}', [error.message]));
		}
	}

	render_matrices_list(matrices) {
		const container = this.body.find('[data-section="matrices-list"]');
		const empty_state = this.body.find('[data-section="empty-state"]');

		if (!matrices || matrices.length === 0) {
			container.hide();
			empty_state.show();
			return;
		}

		container.show();
		empty_state.hide();
		container.empty();

		matrices.forEach(matrix => {
			const card = this.create_matrix_card(matrix);
			container.append(card);
		});
	}

	create_matrix_card(matrix) {
		const self = this;
		const $card = $(`
			<div class="matrix-card" data-name="${matrix.name}" style="cursor: pointer;">
				<div class="matrix-card-header">
					<div class="matrix-info">
						<h5>${matrix.target_doctype}</h5>
						<div class="matrix-meta">
							<span class="badge badge-info">${matrix.dimension}</span>
							<span class="text-muted">${matrix.transition_count} rules</span>
						</div>
					</div>
					<div class="matrix-actions">
						<button class="btn btn-xs btn-danger" data-action="delete-matrix" data-name="${matrix.name}" 
							title="Delete matrix" onclick="event.stopPropagation();">
							<svg class="icon icon-xs"><use href="#icon-delete"></use></svg>
						</button>
					</div>
				</div>
				${matrix.fields_applicable ? `
					<div class="matrix-card-body">
						<small class="text-muted">Fields: ${matrix.fields_applicable}</small>
					</div>
				` : ''}
			</div>
		`);
		
		// Click anywhere on card to edit
		$card.on('click', function(e) {
			// Don't trigger if clicking delete button
			if (!$(e.target).closest('[data-action="delete-matrix"]').length) {
				self.edit_matrix(matrix.name);
			}
		});
		
		return $card;
	}

	show_new_matrix_dialog() {
		const self = this;
		
		// Show dialog to select target doctype and dimension
		const d = new frappe.ui.Dialog({
			title: __('Create New Approval Matrix'),
			fields: [
				{
					fieldtype: 'Select',
					fieldname: 'target_doctype',
					label: __('Target DocType'),
					options: this.doctypes.map(dt => dt.name),
					reqd: 1
				},
				{
					fieldtype: 'Select',
					fieldname: 'dimension',
					label: __('Dimension'),
					options: this.dimensions.map(dim => dim.name),
					reqd: 1,
					description: __('The primary dimension for routing approvals')
				},
				{
					fieldtype: 'Data',
					fieldname: 'fields_applicable',
					label: __('Fields Applicable'),
					description: __('Comma-separated fields for conditions (optional)')
				}
			],
			primary_action_label: __('Create Matrix'),
			primary_action: function(values) {
				self.show_editor(null, values.target_doctype, values.dimension, values.fields_applicable);
				d.hide();
			}
		});
		
		d.show();
	}

	show_editor(matrix = null, target_doctype = null, dimension = null, fields_applicable = null) {
		this.body.find('[data-section="matrices-list"]').parent().hide();
		this.body.find('[data-section="matrix-editor"]').show();

		if (matrix) {
			// Editing existing matrix
			this.current_matrix = matrix;
			this.body.find('[data-editor="title"]').text(`Edit: ${matrix.target_doctype}`);
			this.populate_editor(matrix);
			this.make_basic_config_readonly(true);
		} else {
			// Creating new matrix with selected doctype and dimension
			this.current_matrix = null;
			this.body.find('[data-editor="title"]').text('New Approval Matrix');
			this.clear_editor();
			
			// Set the values from dialog
			if (target_doctype) {
				this.body.find('[data-field="target_doctype"]').val(target_doctype);
			}
			if (dimension) {
				this.body.find('[data-field="dimension"]').val(dimension).trigger('change');
			}
			if (fields_applicable) {
				this.body.find('[data-field="fields_applicable"]').val(fields_applicable);
			}
			
			// Make target_doctype and dimension readonly
			this.make_basic_config_readonly(true);
		}
	}

	make_basic_config_readonly(readonly) {
		const $target_doctype = this.body.find('[data-field="target_doctype"]');
		const $dimension = this.body.find('[data-field="dimension"]');
		
		if (readonly) {
			$target_doctype.prop('disabled', true).css({
				'background-color': 'var(--bg-light-gray)',
				'cursor': 'not-allowed'
			});
			$dimension.prop('disabled', true).css({
				'background-color': 'var(--bg-light-gray)',
				'cursor': 'not-allowed'
			});
		} else {
			$target_doctype.prop('disabled', false).css({
				'background-color': '',
				'cursor': ''
			});
			$dimension.prop('disabled', false).css({
				'background-color': '',
				'cursor': ''
			});
		}
	}

	show_list() {
		this.body.find('[data-section="matrix-editor"]').hide();
		this.body.find('[data-section="matrices-list"]').parent().show();
		this.load_matrices();
	}

	populate_editor(matrix) {
		this.body.find('[data-field="target_doctype"]').val(matrix.target_doctype);
		this.body.find('[data-field="dimension"]').val(matrix.dimension).trigger('change');
		this.body.find('[data-field="fields_applicable"]').val(matrix.fields_applicable || '');

		// Convert flat transitions to grouped rules
		this.rules = this.group_transitions_by_dimension(matrix.transitions || []);
		this.render_rules();
	}

	clear_editor() {
		this.body.find('[data-field="target_doctype"]').val('');
		this.body.find('[data-field="dimension"]').val('');
		this.body.find('[data-field="fields_applicable"]').val('');

		this.rules = [];
		this.render_rules();
	}

	async load_dimension_values(dimension) {
		if (!dimension) {
			this.dimension_values = [];
			return;
		}

		try {
			this.dimension_values = await this.call_api('get_dimension_values', { dimension });
			this.render_rules(); // Re-render to update dropdowns
		} catch (error) {
			frappe.msgprint(__('Error loading dimension values: {0}', [error.message]));
		}
	}

	// Group flat transitions by dimension_value
	group_transitions_by_dimension(transitions) {
		const grouped = new Map();
		
		transitions.forEach(t => {
			const key = this.normalizeDimensionValue(t.dimension_value);
			if (!grouped.has(key)) {
				grouped.set(key, []);
			}
			grouped.get(key).push({
				condition: t.condition || '',
				approving_authority: t.approving_authority || '',
				idx: t.idx
			});
		});

		// Convert to array format
		return Array.from(grouped.entries()).map(([dim_val, conditions]) => ({
			dimension_value: dim_val,
			conditions
		}));
	}

	// Convert grouped rules back to flat transitions for saving
	flatten_rules_to_transitions() {
		const transitions = [];
		let idx = 1;

		this.rules.forEach(rule => {
			rule.conditions.forEach(cond => {
				transitions.push({
					idx: idx++,
					dimension_value: this.normalizeDimensionValue(rule.dimension_value),
					condition: cond.condition,
					approving_authority: cond.approving_authority,
					disabled: 0
				});
			});
		});

		return transitions;
	}

	add_rule() {
		const self = this;
		const dimension = this.body.find('[data-field="dimension"]').val();
		
		if (!dimension) {
			frappe.msgprint(__('Please select a dimension first'));
			return;
		}

		// Show dialog to select dimension value
		const d = new frappe.ui.Dialog({
			title: __('Add New Rule'),
			fields: [
				{
					fieldtype: 'Check',
					fieldname: 'apply_to_all',
					label: __('Apply to all dimension values')
				},
				{
					fieldtype: 'Select',
					fieldname: 'dimension_value',
					label: __('Dimension Value'),
					options: this.dimension_values || [],
					depends_on: 'eval:!doc.apply_to_all',
					mandatory_depends_on: 'eval:!doc.apply_to_all'
				}
			],
			primary_action_label: __('Add Rule'),
			primary_action: function(values) {
				const apply_to_all = values.apply_to_all ? true : false;
				const dimensionValue = apply_to_all ? null : values.dimension_value;

				if (!apply_to_all && !dimensionValue) {
					frappe.msgprint(__('Please choose a dimension value or enable the all-dimension option'));
					return;
				}

				if (apply_to_all) {
					const existingGlobal = self.findRuleByKey(self.ANY_DIMENSION_KEY);
					if (existingGlobal) {
						frappe.msgprint(__('A rule for all dimension values already exists'));
						return;
					}
				}

				// Check if rule already exists for this dimension value
				const existing = self.rules.find(r => self.normalizeDimensionValue(r.dimension_value) === self.normalizeDimensionValue(dimensionValue));
				if (existing) {
					frappe.msgprint(__('Rule for this dimension value already exists'));
					return;
				}

				// Add new rule at the beginning (top)
				self.rules.unshift({
					dimension_value: self.normalizeDimensionValue(dimensionValue),
					conditions: [{
						condition: '',
						approving_authority: '',
						idx: Date.now()
					}]
				});

				self.render_rules();
				d.hide();
				
				frappe.show_alert({
					message: __('Rule added for {0}', [self.getDimensionLabel(dimensionValue)]),
					indicator: 'green'
				}, 3);
			}
		});
		
		d.show();
	}

	remove_rule(dimensionKey) {
		this.removeRuleByKey(dimensionKey);
		this.render_rules(true);
		this.auto_save_matrix();
	}

	duplicate_rule(dimensionKey) {
		const self = this;
		const original_rule = this.findRuleByKey(dimensionKey);
		
		if (!original_rule) return;

		// Show dialog to select new dimension value for the duplicate
		const d = new frappe.ui.Dialog({
			title: __('Duplicate Rule'),
			fields: [
				{
					fieldtype: 'HTML',
					options: `<p class="text-muted">Duplicating rule for: <strong>${self.getDimensionLabel(original_rule.dimension_value)}</strong></p>`
				},
				{
					fieldtype: 'Select',
					fieldname: 'new_dimension_value',
					label: __('New Dimension Value'),
					options: this.dimension_values || [],
					reqd: 1
				}
			],
			primary_action_label: __('Duplicate'),
			primary_action: function(values) {
				// Check if rule already exists for this dimension value
				const existing = self.rules.find(r => self.normalizeDimensionValue(r.dimension_value) === self.normalizeDimensionValue(values.new_dimension_value));
				if (existing) {
					frappe.msgprint(__('Rule for this dimension value already exists'));
					return;
				}

				// Deep clone the original rule
				const duplicated_rule = {
					dimension_value: self.normalizeDimensionValue(values.new_dimension_value),
					conditions: original_rule.conditions.map(cond => ({
						condition: cond.condition,
						approving_authority: cond.approving_authority,
						idx: Date.now() + Math.random() // New unique ID
					}))
				};

				// Add duplicated rule at the beginning (top)
				self.rules.unshift(duplicated_rule);
				self.render_rules();
				d.hide();
				
				frappe.show_alert({
					message: __('Rule duplicated to {0}', [self.getDimensionLabel(values.new_dimension_value)]),
					indicator: 'green'
				}, 3);
			}
		});
		
		d.show();
	}

	add_condition_to_rule(dimensionKey) {
		const rule = this.findRuleByKey(dimensionKey);
		if (rule) {
			rule.conditions.push({
				condition: '',
				approving_authority: '',
				idx: Date.now() // Temporary unique ID
			});
			this.render_rules();
		}
	}

	remove_condition(dimensionKey, condition_idx) {
		const rule = this.findRuleByKey(dimensionKey);
		if (rule) {
			rule.conditions = rule.conditions.filter(c => c.idx !== condition_idx);
			// If no conditions left, remove the rule
			if (rule.conditions.length === 0) {
				this.remove_rule(dimensionKey);
			} else {
				this.render_rules(true);
				this.auto_save_matrix();
			}
			frappe.show_alert({
				message: __('Condition removed and saved'),
				indicator: 'orange'
			}, 2);
		}
	}

	render_rules(preserve_search = false) {
		const self = this;
		const $container = this.body.find('[data-container="rules"]');
		const empty_section = this.body.find('[data-section="empty-rules"]');
		
		// Store existing search input value and cursor position before clearing
		let existing_search_value = '';
		let cursor_position = 0;
		if (preserve_search) {
			const $existingSearch = $container.find('.rules-search');
			if ($existingSearch.length) {
				existing_search_value = $existingSearch.val();
				cursor_position = $existingSearch[0].selectionStart;
			}
		}
		
		$container.empty();

		if (this.rules.length === 0) {
			empty_section.show();
			return;
		}

		// Add search/filter box
		const $filterBox = $(
			`<div class="rules-filter-section" style="margin-bottom: 15px;">
				<div class="row">
					<div class="col-md-6">
						<input type="text" class="form-control form-control-sm rules-search" 
							placeholder="Search by dimension value or 'Any Dimension'..." />
					</div>
					<div class="col-md-6 text-right">
						<span class="text-muted rules-count-text"></span>
					</div>
				</div>
			</div>`
		);
		$container.append($filterBox);
		
		// Restore search value and cursor position if preserving
		if (preserve_search && existing_search_value) {
			const $searchInput = $filterBox.find('.rules-search');
			$searchInput.val(existing_search_value);
			setTimeout(() => {
				$searchInput[0].setSelectionRange(cursor_position, cursor_position);
				$searchInput.focus();
			}, 0);
		}

		// Initialize load more functionality
		if (!this.rules_loaded_count) this.rules_loaded_count = 5;
		if (!this.rules_per_load) this.rules_per_load = 5;
		if (!this.rules_search_text) this.rules_search_text = '';

		// Filter rules based on search
		let filtered_rules = this.rules;
		if (this.rules_search_text) {
			const searchText = this.rules_search_text.toLowerCase();
			filtered_rules = this.rules.filter(rule => {
				const dim_value = this.getDimensionLabel(rule.dimension_value).toLowerCase();
				return dim_value.includes(searchText);
			});
		}

		// Update count text
		const visible_count = Math.min(this.rules_loaded_count, filtered_rules.length);
		$filterBox.find('.rules-count-text').text(
			`Showing ${visible_count} of ${filtered_rules.length} rule(s)`
		);

		// Get rules to display (load more approach)
		const rules_to_display = filtered_rules.slice(0, this.rules_loaded_count);

		// Bind search with debounce
		const $searchInput = $filterBox.find('.rules-search').val(this.rules_search_text);
		
		let search_timeout;
		$searchInput.on('input', function() {
			const search_text = $(this).val();
			
			// Update filtered count immediately without re-rendering
		let temp_filtered = self.rules;
		if (search_text) {
			const searchLower = search_text.toLowerCase();
			temp_filtered = self.rules.filter(rule => {
				const dim_value = self.getDimensionLabel(rule.dimension_value).toLowerCase();
				return dim_value.includes(searchLower);
			});
		}
			$filterBox.find('.rules-count-text').text(
				`Showing ${temp_filtered.length} of ${self.rules.length} rule(s)`
			);
			
			// Debounce the actual re-render
			clearTimeout(search_timeout);
			search_timeout = setTimeout(function() {
				self.rules_search_text = search_text;
				self.rules_loaded_count = self.rules_per_load; // Reset to initial load count
				self.render_rules(true); // Preserve search input focus
			}, 500); // Wait 500ms after user stops typing
		});

		$container.show();
		empty_section.hide();

		// Render visible rules
		rules_to_display.forEach((rule, rule_index) => {
			const card = this.create_rule_card(rule, rule_index);
			$container.append(card);
		});

		// Add "Load More" button if there are more rules to show
		if (this.rules_loaded_count < filtered_rules.length) {
			const remaining_count = filtered_rules.length - this.rules_loaded_count;
			const next_load_count = Math.min(this.rules_per_load, remaining_count);
			
			const $loadMoreBtn = $(`
				<div class="load-more-container" style="margin-top: 20px; text-align: center;">
					<button class="btn btn-sm btn-primary load-more-btn">
						<svg class="icon icon-xs"><use href="#icon-down"></use></svg>
						Load More (${next_load_count} more)
					</button>
					<div style="margin-top: 8px; color: var(--text-muted); font-size: 12px;">
						${remaining_count} rule(s) remaining
					</div>
				</div>
			`);

			$loadMoreBtn.find('.load-more-btn').on('click', function() {
				// Increase the loaded count by 5
				self.rules_loaded_count += self.rules_per_load;
				self.render_rules(true); // Preserve search state
				
				// Scroll to the newly loaded content
				setTimeout(() => {
					const $lastCard = $container.find('.rule-card').eq(self.rules_loaded_count - self.rules_per_load);
					if ($lastCard.length) {
						$lastCard[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
					}
				}, 100);
			});

			$container.append($loadMoreBtn);
		}
	}

	create_rule_card(rule, rule_index) {
		const self = this;
		const ruleKey = this.getDimensionKey(rule.dimension_value);
		const dimensionLabel = this.getDimensionLabel(rule.dimension_value);
		const dimension_options = (this.dimension_values || []).map(val => 
			`<option value="${val}" ${rule.dimension_value === val ? 'selected' : ''}>${val}</option>`
		).join('');

		// Create conditions HTML
		const conditions_html = rule.conditions.map((cond, cond_idx) => {
			const authorities_list = (cond.approving_authority || '').split('\n').filter(a => a.trim());
			const authorities_html = authorities_list.map(auth => {
				// Get user full name from cache or show email
				const user_name = self.user_names_cache?.[auth] || auth;
				return `<div class="authority-tag">
					<span class="authority-name" title="${auth}">${user_name}</span>
					<span class="remove-authority" data-authority="${auth}" data-dimension="${ruleKey}" data-cond-idx="${cond.idx}">×</span>
				</div>`;
			}).join('');

			return `
				<div class="condition-row" data-cond-idx="${cond.idx}" draggable="true">
					<div class="condition-drag-handle" title="Drag to reorder">
						<svg class="icon icon-sm" style="cursor: move;"><use href="#icon-drag"></use></svg>
					</div>
					<div class="condition-content">
						<div class="row">
							<div class="col-md-5">
								<div class="form-group">
									<label>Condition (Optional)</label>
									<div style="position: relative;">
									<input type="text" class="form-control form-control-sm" 
										data-field="condition" data-dimension="${ruleKey}" data-cond-idx="${cond.idx}"
											placeholder="e.g., type == 'CAPEX' and grand_total <= 5000"
											value="${cond.condition || ''}" />
									<button class="btn btn-xs btn-success condition-save-btn" 
										data-action="save-condition" data-dimension="${ruleKey}" data-cond-idx="${cond.idx}"
											style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); display: none;">
											<svg class="icon icon-xs"><use href="#icon-check"></use></svg>
										</button>
									</div>
								</div>
							</div>
							<div class="col-md-6">
								<div class="form-group">
									<label>Approving Authorities <span class="text-danger">*</span></label>
									<div class="authorities-container">
									<div class="authorities-list">${authorities_html}</div>
									<div class="authority-search-field" data-dimension="${ruleKey}" data-cond-idx="${cond.idx}"></div>
									</div>
								</div>
							</div>
							<div class="col-md-1" style="text-align: right;">
							<button class="btn btn-xs condition-delete-btn" 
								data-action="remove-condition" data-dimension="${ruleKey}" data-cond-idx="${cond.idx}"
									title="Remove condition">
									<svg class="icon icon-xs"><use href="#icon-delete"></use></svg>
								</button>
							</div>
						</div>
					</div>
				</div>
			`;
		}).join('');

		const card = $(`
			<div class="rule-card" data-dimension="${ruleKey}">
				<div class="rule-card-header">
					<div class="rule-info">
						<div style="display: flex; align-items: center; gap: 12px;">
							<div style="flex: 1;">
								<label style="margin-bottom: 4px; font-size: 11px; color: var(--text-muted);">Dimension Value</label>
								<div style="font-weight: 600; font-size: 15px;">${dimensionLabel}</div>
							</div>
							<div class="condition-count-badge">
								${rule.conditions.length} condition${rule.conditions.length !== 1 ? 's' : ''}
							</div>
						</div>
					</div>
					<div class="rule-actions">
						<button class="btn btn-xs btn-default" data-action="add-condition" data-dimension="${ruleKey}">
							<svg class="icon icon-xs"><use href="#icon-add"></use></svg>
							Add Condition
						</button>
						<button class="btn btn-xs btn-default" data-action="duplicate-rule" data-dimension="${ruleKey}" title="Duplicate this rule">
							<svg class="icon icon-xs"><use href="#icon-duplicate"></use></svg>
							Duplicate
						</button>
						<button class="btn btn-xs btn-danger" data-action="remove-rule" data-dimension="${ruleKey}">
							<svg class="icon icon-xs"><use href="#icon-delete"></use></svg>
						</button>
					</div>
				</div>
				<div class="rule-card-body">
					<div class="conditions-container">
						${conditions_html}
					</div>
				</div>
			</div>
		`);

		// Duplicate rule button
		card.on('click', '[data-action="duplicate-rule"]', function() {
			const dimension_value = $(this).data('dimension');
			self.duplicate_rule(dimension_value);
		});

		// Show save button when condition is edited
		card.find('[data-field="condition"]').on('input', function() {
			const $saveBtn = $(this).siblings('.condition-save-btn');
			$saveBtn.show();
		});
		
		// Save condition when clicking the tick button
		card.on('click', '[data-action="save-condition"]', function() {
			const cond_idx = $(this).data('cond-idx');
			const $textarea = card.find(`[data-field="condition"][data-cond-idx="${cond_idx}"]`);
			const condition = rule.conditions.find(c => c.idx === cond_idx);
			
			if (condition) {
				condition.condition = $textarea.val();
				// Auto-save to backend
				self.auto_save_matrix();
				// Hide the save button
				$(this).hide();
				frappe.show_alert({
					message: __('Condition saved'),
					indicator: 'green'
				}, 2);
			}
		});

		// Create Frappe Link controls for authority search
		card.find('.authority-search-field').each(function() {
			self.setup_authority_link_field($(this), rule, ruleKey);
		});

		// Bind remove authority
		card.on('click', '.remove-authority', function() {
			const authority = $(this).data('authority');
			const cond_idx = $(this).data('cond-idx');
			const condition = rule.conditions.find(c => c.idx === cond_idx);
			if (condition) {
				const authorities = condition.approving_authority.split('\n').filter(a => a.trim());
				condition.approving_authority = authorities.filter(a => a !== authority).join('\n');
				
				// Remove the tag from DOM instead of re-rendering
				$(this).closest('.authority-tag').remove();
				
				// Auto-save after removing authority
				self.auto_save_matrix();
				frappe.show_alert({
					message: __('Authority removed and saved'),
					indicator: 'orange'
				}, 2);
			}
		});

		// Setup drag and drop for conditions
		self.setup_condition_drag_drop(card, rule);

		return card;
	}

	setup_authority_link_field($container, rule, ruleKey) {
		const self = this;
		const cond_idx = $container.data('cond-idx');
		
		// Create Frappe Link field control
		const link_field = frappe.ui.form.make_control({
			df: {
				fieldname: 'user_search_' + cond_idx,
				label: __('Search User'),
				fieldtype: 'Link',
				options: 'User',
				placeholder: __('Type to search users...'),
				only_select: true,
				get_query: function() {
					return {
						filters: {
							enabled: 1,
							user_type: 'System User'
						}
					};
				},
				change: function() {
					const selected_user = this.get_value();
					if (selected_user) {
						const condition = rule.conditions.find(c => c.idx === cond_idx);
						if (condition) {
							const authorities = condition.approving_authority ? 
								condition.approving_authority.split('\n').filter(a => a.trim()) : [];
							
							if (!authorities.includes(selected_user)) {
								authorities.push(selected_user);
								condition.approving_authority = authorities.join('\n');
								
								// Don't re-render, just update the authorities list
								const $authList = $container.siblings('.authorities-list');
								const $newTag = $(
									`<div class="authority-tag">
										${selected_user}
										<span class="remove-authority" data-authority="${selected_user}" data-dimension="${ruleKey}" data-cond-idx="${cond_idx}">×</span>
									</div>`
								);
								$authList.append($newTag);
								
								// Auto-save after adding authority
								self.auto_save_matrix();
								frappe.show_alert({
									message: __('Authority added and saved'),
									indicator: 'green'
								}, 2);
							}
						}
						// Clear the field
						setTimeout(() => {
							this.set_value('');
						}, 100);
					}
				}
			},
			parent: $container,
			render_input: true,
			only_input: true
		});
		
		// Remove the label that Frappe adds
		$container.find('.control-label').remove();
		$container.find('.clearfix').remove();
	}

	setup_condition_drag_drop(card, rule) {
		const self = this;
		let draggedElement = null;
		let draggedIdx = null;

		// Add drag event listeners to all condition rows
		card.find('.condition-row').each(function() {
			const $row = $(this);
			const condIdx = $row.data('cond-idx');

			// Dragstart
			$row.on('dragstart', function(e) {
				draggedElement = this;
				draggedIdx = condIdx;
				$(this).addClass('dragging');
				e.originalEvent.dataTransfer.effectAllowed = 'move';
				e.originalEvent.dataTransfer.setData('text/html', this.innerHTML);
			});

			// Dragend
			$row.on('dragend', function(e) {
				$(this).removeClass('dragging');
				card.find('.condition-row').removeClass('drag-over');
			});

			// Dragover
			$row.on('dragover', function(e) {
				if (e.preventDefault) {
					e.preventDefault();
				}
				e.originalEvent.dataTransfer.dropEffect = 'move';
				
				if (draggedElement !== this) {
					$(this).addClass('drag-over');
				}
				return false;
			});

			// Dragleave
			$row.on('dragleave', function(e) {
				$(this).removeClass('drag-over');
			});

			// Drop
			$row.on('drop', function(e) {
				if (e.stopPropagation) {
					e.stopPropagation();
				}
				e.preventDefault();

				const dropIdx = $(this).data('cond-idx');
				
				if (draggedIdx !== dropIdx) {
					// Find the conditions in the rule
					const draggedCondition = rule.conditions.find(c => c.idx === draggedIdx);
					const dropCondition = rule.conditions.find(c => c.idx === dropIdx);
					
					if (draggedCondition && dropCondition) {
						// Get indices
						const draggedIndex = rule.conditions.indexOf(draggedCondition);
						const dropIndex = rule.conditions.indexOf(dropCondition);
						
						// Reorder the array
						rule.conditions.splice(draggedIndex, 1);
						const newDropIndex = rule.conditions.indexOf(dropCondition);
						rule.conditions.splice(newDropIndex + (draggedIndex < dropIndex ? 1 : 0), 0, draggedCondition);
						
						// Re-render the rules to show new order
						self.render_rules(true);
						
						// Auto-save
						self.auto_save_matrix();
						
						frappe.show_alert({
							message: __('Condition order updated'),
							indicator: 'blue'
						}, 2);
					}
				}
				
				$(this).removeClass('drag-over');
				return false;
			});
		});
	}

	async auto_save_matrix() {
		// Silent auto-save without validation messages
		const target_doctype = this.body.find('[data-field="target_doctype"]').val();
		const dimension = this.body.find('[data-field="dimension"]').val();
		const fields_applicable = this.body.find('[data-field="fields_applicable"]').val();

		if (!target_doctype || !dimension || this.rules.length === 0) {
			return; // Skip if basic config is missing
		}

		// Convert grouped rules to flat transitions
		const transitions = this.flatten_rules_to_transitions();

		// Prepare data
		const data = {
			name: this.current_matrix ? this.current_matrix.name : null,
			target_doctype,
			dimension,
			fields_applicable,
			transitions: transitions
		};

		try {
			const result = await this.call_api('save_matrix', { data: JSON.stringify(data) });
			// Update current matrix name if it's a new save
			if (result && result.name && !this.current_matrix) {
				this.current_matrix = { name: result.name };
			}
		} catch (error) {
			console.error('Auto-save error:', error);
		}
	}

	async save_matrix() {
		// Validate
		const target_doctype = this.body.find('[data-field="target_doctype"]').val();
		const dimension = this.body.find('[data-field="dimension"]').val();
		const fields_applicable = this.body.find('[data-field="fields_applicable"]').val();

		if (!target_doctype) {
			frappe.msgprint(__('Please select a target doctype'));
			return;
		}

		if (!dimension) {
			frappe.msgprint(__('Please select a dimension'));
			return;
		}

		if (this.rules.length === 0) {
			frappe.msgprint(__('Please add at least one approval rule'));
			return;
		}

		// Validate rules
		const seenKeys = new Set();
		for (const rule of this.rules) {
			const ruleKey = this.getDimensionKey(rule.dimension_value);
			if (seenKeys.has(ruleKey)) {
				frappe.msgprint(__('Duplicate rules found for {0}. Please consolidate them before saving.', [this.getDimensionLabel(rule.dimension_value)]));
				return;
			}
			seenKeys.add(ruleKey);
			
			if (!rule.conditions || rule.conditions.length === 0) {
				frappe.msgprint(__('Each rule must include at least one condition'));
				return;
			}
			
			for (const cond of rule.conditions) {
				if (!cond.approving_authority || !cond.approving_authority.trim()) {
					frappe.msgprint(__('Please select approving authorities for all conditions'));
					return;
				}
			}
		}

		// Convert grouped rules to flat transitions
		const transitions = this.flatten_rules_to_transitions();

		// Prepare data
		const data = {
			name: this.current_matrix ? this.current_matrix.name : null,
			target_doctype,
			dimension,
			fields_applicable,
			transitions: transitions
		};

		try {
			const result = await this.call_api('save_matrix', { data: JSON.stringify(data) });
			frappe.show_alert({
				message: __('Approval Matrix saved successfully'),
				indicator: 'green'
			});
			this.show_list();
		} catch (error) {
			frappe.msgprint(__('Error saving matrix: {0}', [error.message]));
		}
	}

	async edit_matrix(name) {
		try {
			const matrix = await this.call_api('get_matrix_details', { matrix_name: name });
			this.show_editor(matrix);
		} catch (error) {
			frappe.msgprint(__('Error loading matrix: {0}', [error.message]));
		}
	}

	async delete_matrix(name) {
		frappe.confirm(
			__('Are you sure you want to delete this approval matrix?'),
			async () => {
				try {
					await this.call_api('delete_matrix', { matrix_name: name });
					frappe.show_alert({
						message: __('Approval Matrix deleted successfully'),
						indicator: 'green'
					});
					this.load_matrices();
				} catch (error) {
					frappe.msgprint(__('Error deleting matrix: {0}', [error.message]));
				}
			}
		);
	}


	print_matrix() {
		if (!this.current_matrix) {
			frappe.msgprint(__('Please save the matrix first'));
			return;
		}

		// Prepare print data
		const target_doctype = this.body.find('[data-field="target_doctype"]').val();
		const dimension = this.body.find('[data-field="dimension"]').val();
		const fields_applicable = this.body.find('[data-field="fields_applicable"]').val();

		// Build HTML for print view
		let html = `
			<div style="font-family: Arial, sans-serif; padding: 20px;">
				<h1 style="text-align: center; color: #333; margin-bottom: 30px;">Approval Matrix</h1>
				
				<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 30px;">
					<table style="width: 100%; border-collapse: collapse;">
						<tr>
							<td style="padding: 8px; font-weight: bold; width: 200px;">Target DocType:</td>
							<td style="padding: 8px;">${target_doctype}</td>
						</tr>
						<tr>
							<td style="padding: 8px; font-weight: bold;">Dimension:</td>
							<td style="padding: 8px;">${dimension}</td>
						</tr>
						${fields_applicable ? `
						<tr>
							<td style="padding: 8px; font-weight: bold;">Fields Applicable:</td>
							<td style="padding: 8px;">${fields_applicable}</td>
						</tr>
						` : ''}
					</table>
				</div>

				<h2 style="color: #333; margin-bottom: 20px;">Approval Rules</h2>
		`;

		// Add each rule
		this.rules.forEach((rule, idx) => {
			html += `
				<div style="border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin-bottom: 20px; page-break-inside: avoid;">
					<h3 style="color: #495057; margin-top: 0; margin-bottom: 15px;">
						${idx + 1}. ${rule.dimension_value}
						<span style="font-size: 14px; color: #6c757d; font-weight: normal;">
							(${rule.conditions.length} condition${rule.conditions.length !== 1 ? 's' : ''})
						</span>
					</h3>
			`;

			rule.conditions.forEach((cond, cond_idx) => {
				const authorities = (cond.approving_authority || '').split('\n').filter(a => a.trim());
				const authority_names = authorities.map(auth => this.user_names_cache?.[auth] || auth);

				html += `
					<div style="background: #f8f9fa; padding: 15px; border-left: 3px solid #007bff; margin-bottom: 15px;">
						<div style="margin-bottom: 10px;">
							<strong style="color: #495057;">Condition ${cond_idx + 1}:</strong>
							<div style="font-family: 'Courier New', monospace; background: white; padding: 8px; margin-top: 5px; border-radius: 4px;">
								${cond.condition || '<em style="color: #6c757d;">No condition (applies to all)</em>'}
							</div>
						</div>
						<div>
							<strong style="color: #495057;">Approving Authorities:</strong>
							<div style="margin-top: 5px;">
								${authority_names.map(name => `
									<span style="display: inline-block; background: #e7f3ff; color: #0066cc; padding: 4px 10px; border-radius: 12px; margin: 3px; font-size: 13px;">
										${name}
									</span>
								`).join('')}
							</div>
						</div>
					</div>
				`;
			});

			html += `</div>`;
		});

		html += `
				<div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; color: #6c757d; font-size: 12px;">
					Generated on ${frappe.datetime.now_datetime()}
				</div>
			</div>
		`;

		// Open print window
		const print_window = window.open('', '_blank');
		print_window.document.write(`
			<!DOCTYPE html>
			<html>
				<head>
					<meta charset="utf-8">
					<title>Approval Matrix - ${target_doctype}</title>
					<style>
						body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f1f3f5; }
					</style>
				</head>
				<body>
					${html}
				</body>
			</html>
		`);
		print_window.document.close();
		print_window.focus();
		setTimeout(() => {
			print_window.print();
		}, 300);
	}
}