/**
 * Approval Matrix Viewer Page
 * Read-only view of approval matrices by dimension value
 */

frappe.pages['approval_matrix_viewer'].on_page_load = function(wrapper) {
	new ApprovalMatrixViewer(wrapper);
};

class ApprovalMatrixViewer {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Approval Matrix Viewer',
			single_column: true
		});

		this.dimensions = [];
		this.dimension_values = [];
		this.current_dimension = null;
		this.current_dimension_value = null;

		// Render the HTML template
		this.render_page();
		this.init();
	}

	async call_api(method, args = {}) {
		try {
			const { message } = await frappe.call({
				method: `hkm.erpnext___custom.page.approval_matrix_viewer.approval_matrix_viewer.${method}`,
				args,
				freeze: true,
				freeze_message: __('Loading...')
			});
			return message;
		} catch (error) {
			frappe.msgprint(__('Error: {0}', [error.message]));
			throw error;
		}
	}

	render_page() {
		this.body = this.page.main;
		$(frappe.render_template('approval_matrix_viewer', {})).appendTo(this.body);
	}

	async init() {
		await this.load_dimensions();
		this.setup_filters();
		this.bind_events();
	}

	async load_dimensions() {
		try {
			this.dimensions = await this.call_api('get_dimensions');
			this.populate_dimension_dropdown();
		} catch (error) {
			frappe.msgprint(__('Error loading dimensions: {0}', [error.message]));
		}
	}

	populate_dimension_dropdown() {
		const $dimension_select = this.body.find('[data-filter="dimension"]');
		$dimension_select.empty().append('<option value="">Select Dimension...</option>');
		
		this.dimensions.forEach(dim => {
			$dimension_select.append(`<option value="${dim.name}">${dim.label || dim.name}</option>`);
		});
	}

	setup_filters() {
		const self = this;

		// Dimension change event
		this.body.find('[data-filter="dimension"]').on('change', async function() {
			const dimension = $(this).val();
			self.current_dimension = dimension;
			
			if (dimension) {
				await self.load_dimension_values(dimension);
			} else {
				self.body.find('[data-filter="dimension_value"]')
					.empty()
					.append('<option value="">Select Value...</option>');
				self.dimension_values = [];
			}
		});
	}

	async load_dimension_values(dimension) {
		try {
			this.dimension_values = await this.call_api('get_dimension_values', { dimension });
			
			const $value_select = this.body.find('[data-filter="dimension_value"]');
			$value_select.empty().append('<option value="">Select Value...</option>');
			
			this.dimension_values.forEach(val => {
				$value_select.append(`<option value="${val}">${val}</option>`);
			});
		} catch (error) {
			frappe.msgprint(__('Error loading dimension values: {0}', [error.message]));
		}
	}

	bind_events() {
		const self = this;

		// Load matrices button
		this.body.on('click', '[data-action="load-matrices"]', async function() {
			await self.load_matrices();
		});

		// Clear filters button
		this.body.on('click', '[data-action="clear-filters"]', function() {
			self.clear_filters();
		});

		// Print view button
		this.body.on('click', '[data-action="print-view"]', function() {
			self.print_view();
		});
	}

	async load_matrices() {
		const dimension = this.body.find('[data-filter="dimension"]').val();
		const dimension_value = this.body.find('[data-filter="dimension_value"]').val();

		if (!dimension) {
			frappe.msgprint(__('Please select a dimension'));
			return;
		}

		if (!dimension_value) {
			frappe.msgprint(__('Please select a dimension value'));
			return;
		}

		this.current_dimension = dimension;
		this.current_dimension_value = dimension_value;

		try {
			const matrices = await this.call_api('get_matrices_by_dimension_value', {
				dimension: dimension,
				dimension_value: dimension_value
			});

			if (!matrices || matrices.length === 0) {
				this.show_no_results();
			} else {
				this.render_matrices(matrices);
			}
		} catch (error) {
			frappe.msgprint(__('Error loading matrices: {0}', [error.message]));
		}
	}

	render_matrices(matrices) {
		const $container = this.body.find('[data-container="matrices"]');
		const $results = this.body.find('[data-section="results"]');
		const $empty = this.body.find('[data-section="empty-state"]');
		const $no_results = this.body.find('[data-section="no-results"]');

		// Update header label
		const dimension_label = this.dimensions.find(d => d.name === this.current_dimension)?.label || this.current_dimension;
		this.body.find('[data-display="dimension-value-label"]').text(
			`${dimension_label}: ${this.current_dimension_value}`
		);

		// Clear container
		$container.empty();

		// Show results section
		$empty.hide();
		$no_results.hide();
		$results.show();

		// Render each matrix
		matrices.forEach(matrix => {
			const card = this.create_matrix_card(matrix);
			$container.append(card);
		});
	}

	create_matrix_card(matrix) {
		const transitions_html = matrix.transitions.map(t => {
			const approvers_html = (t.approvers || []).map(approver => {
				return `<span class="approver-tag">${approver.full_name}</span>`;
			}).join('');

			return `
				<div class="rule-row">
					<div class="rule-meta">
						<div class="rule-dimension-value">
							<strong>${t.dimension_value}</strong>
						</div>
						${t.condition ? `
							<div class="rule-condition">
								<small class="text-muted">Condition:</small>
								<code>${t.condition}</code>
							</div>
						` : ''}
					</div>
					<div class="rule-approvers">
						<small class="text-muted">Approving Authorities:</small>
						<div class="approvers-list">
							${approvers_html || '<span class="text-muted">No approvers assigned</span>'}
						</div>
					</div>
				</div>
			`;
		}).join('');

		return $(`
			<div class="matrix-card">
				<div class="matrix-card-header">
					<div class="matrix-info">
						<h5>${matrix.target_doctype}</h5>
						<div class="matrix-meta">
							<span class="badge badge-info">${matrix.dimension}</span>
							<span class="text-muted">${matrix.transitions.length} rule(s)</span>
						</div>
					</div>
				</div>
				${matrix.fields_applicable ? `
					<div class="matrix-fields">
						<small class="text-muted"><strong>Applicable Fields:</strong> ${matrix.fields_applicable}</small>
					</div>
				` : ''}
				<div class="matrix-card-body">
					${transitions_html}
				</div>
			</div>
		`);
	}

	show_no_results() {
		this.body.find('[data-section="empty-state"]').hide();
		this.body.find('[data-section="results"]').hide();
		this.body.find('[data-section="no-results"]').show();
	}

	clear_filters() {
		this.body.find('[data-filter="dimension"]').val('').trigger('change');
		this.body.find('[data-filter="dimension_value"]').val('');
		this.current_dimension = null;
		this.current_dimension_value = null;

		this.body.find('[data-section="results"]').hide();
		this.body.find('[data-section="no-results"]').hide();
		this.body.find('[data-section="empty-state"]').show();
	}

	print_view() {
		const dimension_label = this.dimensions.find(d => d.name === this.current_dimension)?.label || this.current_dimension;
		const title = `Approval Matrix - ${dimension_label}: ${this.current_dimension_value}`;
		
		const $print_content = this.body.find('[data-container="matrices"]').clone();
		
		// Create print window
		const print_window = window.open('', '', 'height=600,width=800');
		print_window.document.write('<html><head><title>' + title + '</title>');
		print_window.document.write('<style>');
		print_window.document.write(`
			body { font-family: Arial, sans-serif; padding: 20px; }
			h1 { color: #333; margin-bottom: 20px; }
			.matrix-card { 
				border: 1px solid #ddd; 
				margin-bottom: 20px; 
				padding: 15px; 
				page-break-inside: avoid;
			}
			.matrix-card-header h5 { 
				margin: 0 0 10px 0; 
				color: #333; 
			}
			.matrix-meta { 
				margin-bottom: 10px; 
			}
			.badge { 
				display: inline-block; 
				padding: 3px 8px; 
				background: #007bff; 
				color: white; 
				border-radius: 3px; 
				font-size: 12px; 
			}
			.rule-row { 
				border-left: 3px solid #007bff; 
				padding: 10px; 
				margin-bottom: 10px; 
				background: #f8f9fa; 
			}
			.rule-dimension-value { 
				font-weight: bold; 
				margin-bottom: 5px; 
			}
			.rule-condition { 
				margin: 5px 0; 
				font-size: 13px; 
			}
			.rule-approvers { 
				margin-top: 8px; 
			}
			.approver-tag { 
				display: inline-block; 
				padding: 4px 10px; 
				background: #e3f2fd; 
				color: #1976d2; 
				border-radius: 12px; 
				margin: 3px; 
				font-size: 13px; 
			}
			code { 
				background: #fff; 
				padding: 2px 6px; 
				border: 1px solid #ddd; 
				border-radius: 3px; 
			}
			@media print {
				.matrix-card { page-break-inside: avoid; }
			}
		`);
		print_window.document.write('</style></head><body>');
		print_window.document.write('<h1>' + title + '</h1>');
		print_window.document.write($print_content.html());
		print_window.document.write('</body></html>');
		print_window.document.close();
		
		setTimeout(() => {
			print_window.print();
		}, 250);
	}
}
