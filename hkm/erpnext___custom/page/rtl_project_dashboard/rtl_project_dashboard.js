frappe.provide('hkm.pages');

frappe.pages['rtl_project_dashboard'].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('RTL Project Dashboard'),
        single_column: true,
    });

    wrapper.rtl_project_dashboard = new hkm.pages.RTLProjectDashboard(page);
};

hkm.pages.RTLProjectDashboard = class {
    constructor(page) {
        this.page = page;
        this.$main = $('<div class="rtl-project-dashboard"></div>').appendTo(this.page.main);
        this.state = {
            context: null,
            assigneeOptions: null,
            viewMode: 'table', // 'table' or 'card'
            displayCount: 10, // Number of items to display initially
            loadMoreIncrement: 10, // How many more items to load each time
            sectionLimits: {
                not_started: 5,
                in_process: 5,
                completed: 5,
            },
        };
        this.renderSkeleton();
        this.bindStaticEvents();
        this.load();
    }

    renderSkeleton() {
        const markup = `
            <div class="dashboard-content">
                <!-- Global Dashboard Header - Always Visible -->
                <div class="dashboard-global-header">
                    <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
                        <div class="view-toggle-container">
                            <button type="button" class="view-btn active" data-view="table">
                                <div class="view-btn-content">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="3" width="7" height="7"></rect>
                                        <rect x="14" y="3" width="7" height="7"></rect>
                                        <rect x="14" y="14" width="7" height="7"></rect>
                                        <rect x="3" y="14" width="7" height="7"></rect>
                                    </svg>
                                    <span class="view-label">${__('Table')}</span>
                                </div>
                            </button>
                            <button type="button" class="view-btn" data-view="card">
                                <div class="view-btn-content">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="3" width="18" height="7" rx="2"></rect>
                                        <rect x="3" y="14" width="18" height="7" rx="2"></rect>
                                    </svg>
                                    <span class="view-label">${__('Cards')}</span>
                                </div>
                            </button>
                            <button type="button" class="view-btn" data-view="matrix">
                                <div class="view-btn-content">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="3" width="18" height="4"></rect>
                                        <rect x="3" y="10" width="18" height="4"></rect>
                                        <rect x="3" y="17" width="18" height="4"></rect>
                                    </svg>
                                    <span class="view-label">${__('Matrix')}</span>
                                </div>
                            </button>
                            <button type="button" class="view-btn" data-view="schedules" data-role="schedules-view-btn" style="display: none;">
                                <div class="view-btn-content">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                        <line x1="16" y1="2" x2="16" y2="6"></line>
                                        <line x1="8" y1="2" x2="8" y2="6"></line>
                                        <line x1="3" y1="10" x2="21" y2="10"></line>
                                    </svg>
                                    <span class="view-label">${__('Schedules')}</span>
                                </div>
                            </button>
                            <button type="button" class="view-btn" data-view="calendar">
                                <div class="view-btn-content">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="12" cy="12" r="10"></circle>
                                        <path d="M12 6v6l4 2"></path>
                                    </svg>
                                    <span class="view-label">${__('Leaves')}</span>
                                </div>
                            </button>
                        </div>
                        <div class="dashboard-controls-section" data-role="admin-actions">
                            <div class="controls-row">
                                <div class="filter-group" data-role="assignee-filter"></div>
                                <button class="btn btn-primary create-project-btn" data-action="new-project" data-role="create-project-btn" style="display: none;">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
                                        <path d="M12 5v14M5 12h14"></path>
                                    </svg>
                                    ${__('Create Project')}
                                </button>
                                <button class="btn btn-success daily-update-btn" data-action="open-daily-update" data-role="daily-update-btn">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
                                        <path d="M12 5v14M5 12h14"></path>
                                    </svg>
                                    ${__('Daily Update')}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Status Matrix Section -->
                <div class="status-matrix-section content-card" style="display: none;">
                    <div class="section-header">
                        <h3>${__('Status Matrix')}</h3>
                        <p class="subtitle">${__('Current status overview for all in-process projects')}</p>
                    </div>
                    <div class="matrix-legend">
                        <span class="legend-title">${__('Status Legend')}:</span>
                        <div class="legend-item">
                            <span class="legend-color" style="background-color: #22c55e"></span>
                            <span class="legend-label">${__('On Track')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background-color: #facc15"></span>
                            <span class="legend-label">${__('Delayed 3-7 Days')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background-color: #f97316"></span>
                            <span class="legend-label">${__('Delayed 8-15 Days')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background-color: #ef4444"></span>
                            <span class="legend-label">${__('Delayed >15 Days (Need Help)')}</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background-color: #e2e8f0"></span>
                            <span class="legend-label">${__('No Status')}</span>
                        </div>
                    </div>
                    <div class="matrix-container" data-role="status-matrix"></div>
                </div>
                
                <!-- Projects Section -->
                <div class="projects-section content-card">
                    <div class="content-body">
                        <div class="table-view-container" style="display: block;">
                            <div class="table-controls">
                                <input type="text" class="form-control search-input" placeholder="${__('Search projects...')}" data-role="search">
                                <div class="pagination-info" data-role="pagination-info"></div>
                            </div>
                            <div class="table-wrapper" data-role="table-wrapper"></div>
                            <div class="pagination-controls" data-role="pagination"></div>
                        </div>
                        <div class="panels" style="display: none;">
                            <div class="panel" data-section="not_started">
                                <div class="panel-header"><h3>${__('Not Started')}</h3></div>
                                <div class="panel-body" data-role="list"></div>
                            </div>
                            <div class="panel" data-section="in_process">
                                <div class="panel-header"><h3>${__('In Process')}</h3></div>
                                <div class="panel-body" data-role="list"></div>
                            </div>
                            <div class="panel" data-section="completed">
                                <div class="panel-header"><h3>${__('Completed')}</h3></div>
                                <div class="panel-body" data-role="list"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Schedules Section -->
                <div class="schedules-section content-card" style="display: none;">
                    <div class="section-header">
                        <div class="d-flex justify-content-between align-items-center">
                            <h3 class="mb-0">${__('Project Schedules')}</h3>
                            <button class="btn btn-primary btn-sm" data-action="new-schedule" data-role="create-schedule-btn">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px;">
                                    <line x1="12" y1="5" x2="12" y2="19"></line>
                                    <line x1="5" y1="12" x2="19" y2="12"></line>
                                </svg>
                                ${__('Create Schedule')}
                            </button>
                        </div>
                    </div>
                    <div class="schedules-container" data-role="schedules-container"></div>
                </div>
            </div>
        `;

        this.$main.html(markup);
        this.$adminActions = this.$main.find('[data-role="admin-actions"]');
        this.$assigneeFilterWrapper = this.$main.find('[data-role="assignee-filter"]');
        this.$bulkSection = this.$main.find('[data-role="bulk-section"]');
        this.$bulkForm = this.$main.find('[data-role="bulk-form"]');
        this.$bulkRows = this.$main.find('[data-role="bulk-rows"]');
        this.$tableWrapper = this.$main.find('[data-role="table-wrapper"]');
        this.$searchInput = this.$main.find('[data-role="search"]');
        this.$tableContainer = this.$main.find('.table-view-container');
        this.$panelsContainer = this.$main.find('.panels');
        this.$paginationControls = this.$main.find('[data-role="pagination"]');
        this.$paginationInfo = this.$main.find('[data-role="pagination-info"]');
        this.$statusMatrix = this.$main.find('[data-role="status-matrix"]');
        this.initAssigneeControl();
    }

    bindStaticEvents() {
        this.$main.on('click', '[data-action="new-project"]', () => this.openProjectDialog());
        
        this.$main.on('click', '[data-action="open-daily-update"]', () => this.openDailyUpdateDialog());
        
        this.$main.on('click', '[data-action="add-leave"]', () => this.openAddLeaveDialog());
        
        this.$main.on('click', '[data-action="edit-leave"]', (e) => {
            const $btn = $(e.currentTarget);
            const leaveId = $btn.data('leave-id');
            const fromDate = $btn.data('from-date');
            const toDate = $btn.data('to-date');
            const reason = $btn.data('reason') || '';
            this.openEditLeaveDialog(leaveId, fromDate, toDate, reason);
        });
        
        this.$main.on('click', '[data-action="delete-leave"]', (e) => {
            const leaveId = $(e.currentTarget).data('leave-id');
            this.deleteLeave(leaveId);
        });
        
        this.$main.on('click', '[data-action="new-schedule"]', () => this.openCreateScheduleDialog());

        this.$main.on('click', '[data-action="start"]', (e) => {
            const project = $(e.currentTarget).data('project');
            this.updateStatus(project, 'In Process');
        });

        this.$main.on('click', '[data-action="complete"]', (e) => {
            const project = $(e.currentTarget).data('project');
            this.updateStatus(project, 'Completed');
        });

        this.$main.on('click', '[data-action="reopen"]', (e) => {
            const project = $(e.currentTarget).data('project');
            this.reopenProject(project);
        });

        this.$main.on('click', '[data-action="edit"]', (e) => {
            const project = $(e.currentTarget).data('project');
            this.editProject(project);
        });

        this.$main.on('click', '[data-action="delete"]', (e) => {
            const project = $(e.currentTarget).data('project');
            this.deleteProject(project);
        });

        this.$bulkForm.on('submit', (e) => {
            e.preventDefault();
            this.bulkSubmit();
        });

        this.$main.on('click', '[data-action="load-more"]', (e) => {
            const section = $(e.currentTarget).data('section');
            this.loadMore(section);
        });

        this.$main.on('click', '.view-btn', (e) => {
            const view = $(e.currentTarget).data('view');
            this.switchView(view);
        });

        this.$searchInput.on('input', frappe.utils.debounce(() => {
            this.state.displayCount = 10; // Reset display count on search
            this.filterTable();
        }, 300));

        this.$main.on('click', '[data-action="load-more-table"]', (e) => {
            e.preventDefault();
            this.loadMoreTableItems();
        });
    }

    load() {
        frappe.call({
            method: 'hkm.erpnext___custom.page.rtl_project_dashboard.rtl_project_dashboard.get_context',
            args: { assignee: this.state.selectedAssignee || null },
            freeze: true,
            callback: ({ message }) => {
                if (!message) {
                    this.renderEmpty();
                    return;
                }
                this.state.context = message;
                this.isAdmin = !!message.is_admin;
                
                // For normal users (not admin/HOD), set default filter to their own ID
                if (!message.is_rtl_admin && !message.is_hod && !this.state.selectedAssignee) {
                    this.state.selectedAssignee = frappe.session.user;
                    this.state.context.assignee = frappe.session.user;
                }
                
                this.render();
            },
        });
    }

    render() {
        const ctx = this.state.context;
        
        // Null safety check
        if (!ctx || !ctx.projects) {
            this.renderEmpty();
            return;
        }
        
        this.toggleAdminControls();
        this.renderAssigneeFilter();
        this.renderBulkTable();
        
        // Use switchView to render the current view mode
        // This ensures consistent rendering logic
        this.switchView(this.state.viewMode);
    }

    loadStatusMatrix() {
        frappe.call({
            method: 'hkm.erpnext___custom.page.rtl_project_dashboard.rtl_project_dashboard.get_matrix_data',
            args: { assignee: null },
            callback: ({ message }) => {
                if (message) {
                    this.renderStatusMatrix(message);
                }
            },
        });
    }

    renderStatusMatrix(data) {
        if (!data.rows || !data.rows.length) {
            this.$statusMatrix.html(`<p class="text-muted text-center" style="padding: 1rem;">${__('No in-process projects found.')}</p>`);
            return;
        }

        const escape = frappe.utils.escape_html;
        let html = `
            <div class="matrix-table-wrapper">
                <table class="matrix-table">
                    <thead>
                        <tr>
                            <th class="assignee-col">${__('Assignee')}</th>
                            <th class="project-count-col">${__('Projects')}</th>
                            <th class="missed-updates-col">${__('Missed Updates')}</th>
        `;

        for (let i = 1; i <= data.max_projects; i++) {
            html += `<th class="project-slot-col">${__('Project')} ${i}</th>`;
        }

        html += `</tr></thead><tbody>`;

        data.rows.forEach((row) => {
            html += `<tr>`;
            html += `<td class="assignee-col">${escape(row.assignee)}</td>`;
            html += `<td class="project-count-col">${row.projects.length}</td>`;
            
            // Add missed updates column with conditional styling
            const missedClass = row.missed_updates > 0 ? 'has-missed' : '';
            html += `<td class="missed-updates-col ${missedClass}">${row.missed_updates}</td>`;

            for (let i = 0; i < data.max_projects; i++) {
                if (i < row.projects.length) {
                    const project = row.projects[i];
                    const color = project.status ? data.colors[project.status] || '#94a3b8' : '#e2e8f0';
                    const statusText = project.status || 'No Status';
                    const tooltip = `${escape(project.id)}\n${escape(project.name)}\n${statusText}`;
                    
                    html += `<td class="project-cell" style="background-color: ${color}" title="${tooltip}">
                        <div class="project-id">${escape(project.id)}</div>
                    </td>`;
                } else {
                    html += `<td class="project-cell empty"></td>`;
                }
            }

            html += `</tr>`;
        });

        html += `</tbody></table></div>`;
        this.$statusMatrix.html(html);
    }

    switchView(view) {
        // Update state and button visual state
        this.state.viewMode = view;
        this.$main.find('.view-btn').removeClass('active');
        this.$main.find(`[data-view="${view}"]`).addClass('active');
        
        const $statusMatrixSection = this.$main.find('.status-matrix-section');
        const $projectsSection = this.$main.find('.projects-section');
        const $schedulesSection = this.$main.find('.schedules-section');
        const $calendarContainer = $projectsSection.find('.calendar-view-container');
        
        // Hide all content sections first
        $statusMatrixSection.hide();
        $projectsSection.hide();
        $schedulesSection.hide();
        
        // Hide all containers within projects section
        if (this.$tableContainer) this.$tableContainer.hide();
        if (this.$panelsContainer) this.$panelsContainer.hide();
        if ($calendarContainer.length) $calendarContainer.hide();
        
        // Handle each view type
        if (view === 'calendar') {
            // Calendar view - render inside projects section
            $projectsSection.show();
            this.loadCalendarView();
        } else if (view === 'schedules') {
            // Schedules view
            $schedulesSection.show();
            this.loadSchedulesView();
        } else if (view === 'matrix') {
            // Matrix view
            $statusMatrixSection.show();
            this.loadStatusMatrix();
        } else if (view === 'table') {
            // Table view - show projects in table format
            $projectsSection.show();
            this.$tableContainer.show();
            this.renderTableView();
        } else if (view === 'card') {
            // Card view - show three panels (Not Started, In Process, Completed)
            $projectsSection.show();
            this.$panelsContainer.show();
            
            const ctx = this.state.context;
            if (ctx && ctx.projects) {
                this.renderSection('not_started', ctx.projects.not_started || []);
                this.renderSection('in_process', ctx.projects.in_process || []);
                this.renderSection('completed', ctx.projects.completed || []);
            }
        } else {
            // Default to table view
            $projectsSection.show();
            this.$tableContainer.show();
            this.renderTableView();
        }
    }

    renderTableView() {
        const ctx = this.state.context;
        
        // Null safety check
        if (!ctx || !ctx.projects) {
            this.$tableWrapper.html(`<p class="text-muted text-center" style="padding: 2rem;">${__('No projects found.')}</p>`);
            return;
        }
        
        const allProjects = [
            ...(ctx.projects.not_started || []),
            ...(ctx.projects.in_process || []),
            ...(ctx.projects.completed || [])
        ];

        if (!allProjects.length) {
            this.$tableWrapper.html(`<p class="text-muted text-center" style="padding: 2rem;">${__('No projects found.')}</p>`);
            return;
        }

        this.allProjectsData = allProjects;
        this.renderTable(allProjects);
    }

    renderTable(projects) {
        // Show projects up to displayCount
        const totalProjects = projects.length;
        const displayedProjects = projects.slice(0, this.state.displayCount);
        const hasMore = totalProjects > this.state.displayCount;

        const escape = frappe.utils.escape_html;
        let html = `
            <table class="table table-bordered project-table">
                <thead>
                    <tr>
                        <th data-sort="project_name" style="cursor: pointer;">${__('Project Name')} <span class="sort-icon">⇅</span></th>
                        <th data-sort="assigned_to_name" style="cursor: pointer;">${__('Assigned To')} <span class="sort-icon">⇅</span></th>
                        <th data-sort="status" style="cursor: pointer;">${__('Status')} <span class="sort-icon">⇅</span></th>
                        <th data-sort="end_date" style="cursor: pointer;">${__('Due Date')} <span class="sort-icon">⇅</span></th>
                        <th>${__('Latest Progress')}</th>
                        <th>${__('Actions')}</th>
                    </tr>
                </thead>
                <tbody>
        `;

        displayedProjects.forEach((project) => {
            const statusClass = this.slug(project.status);
            const statusBadge = `<span class="badge badge-${statusClass}">${escape(project.status)}</span>`;
            const assigneeName = project.assigned_to_name || project.assigned_to;
            const dueDate = project.end_date ? frappe.datetime.str_to_user(project.end_date) : '-';
            
            let progressHtml = '-';
            if (project.latest_status) {
                const color = this.state.context.progress_colors?.[project.latest_status.progress_status] || '#94a3b8';
                progressHtml = `<span class="progress-badge" style="background: ${color}; color: #fff; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">${escape(project.latest_status.progress_status)}</span>`;
            }

            const actions = this.getCardActions(project);
            
            // Format project name with description
            let projectNameHtml = `<strong>${escape(project.project_name)}</strong>`;
            if (project.description) {
                projectNameHtml += `<div class="text-muted small" style="margin-top: 0.25rem; font-weight: normal;">${escape(project.description)}</div>`;
            }

            html += `
                <tr data-project="${escape(project.name)}">
                    <td>${projectNameHtml}</td>
                    <td>${escape(assigneeName)}</td>
                    <td>${statusBadge}</td>
                    <td>${escape(dueDate)}</td>
                    <td>${progressHtml}</td>
                    <td>${actions}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        this.$tableWrapper.html(html);

        // Update info and render Load More button
        const showingCount = Math.min(this.state.displayCount, totalProjects);
        this.$paginationInfo.html(`${__('Showing')} ${showingCount} ${__('of')} ${totalProjects} ${__('projects')}`);

        // Render Load More button
        this.renderLoadMoreButton(hasMore);

        // Bind sort events
        this.$tableWrapper.find('th[data-sort]').on('click', (e) => {
            const field = $(e.currentTarget).data('sort');
            this.sortTable(field);
        });
    }

    renderLoadMoreButton(hasMore) {
        if (!hasMore) {
            this.$paginationControls.empty();
            return;
        }

        const html = `
            <div class="text-center" style="padding: 1rem 0;">
                <button class="btn btn-secondary" data-action="load-more-table">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px;">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                    ${__('Load More')}
                </button>
            </div>
        `;
        this.$paginationControls.html(html);
    }

    loadMoreTableItems() {
        this.state.displayCount += this.state.loadMoreIncrement;
        const query = this.$searchInput.val().toLowerCase().trim();
        
        if (query) {
            this.filterTable();
        } else {
            this.renderTable(this.allProjectsData);
        }
    }

    sortTable(field) {
        if (!this.allProjectsData) return;

        if (this.state.sortField === field) {
            this.state.sortOrder = this.state.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.state.sortField = field;
            this.state.sortOrder = 'asc';
        }

        const sorted = [...this.allProjectsData].sort((a, b) => {
            let aVal = a[field] || '';
            let bVal = b[field] || '';

            if (field === 'end_date') {
                aVal = a.end_date ? new Date(a.end_date) : new Date(0);
                bVal = b.end_date ? new Date(b.end_date) : new Date(0);
            }

            if (aVal < bVal) return this.state.sortOrder === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.state.sortOrder === 'asc' ? 1 : -1;
            return 0;
        });

        this.renderTable(sorted);
    }

    filterTable() {
        if (!this.allProjectsData) return;

        const query = this.$searchInput.val().toLowerCase().trim();
        
        if (!query) {
            this.renderTable(this.allProjectsData);
            return;
        }

        const filtered = this.allProjectsData.filter((project) => {
            return (
                (project.project_name || '').toLowerCase().includes(query) ||
                (project.assigned_to_name || '').toLowerCase().includes(query) ||
                (project.assigned_to || '').toLowerCase().includes(query) ||
                (project.status || '').toLowerCase().includes(query)
            );
        });

        this.renderTable(filtered);
    }

    renderEmpty() {
        this.$main.find('[data-role="list"]').empty().append(`<p class="text-muted">${__('No projects found.')}</p>`);
        this.$bulkRows.empty();
    }

    toggleAdminControls() {
        const ctx = this.state.context;
        const $createBtn = this.$main.find('[data-role="create-project-btn"]');
        const $createScheduleBtn = this.$main.find('[data-role="create-schedule-btn"]');
        const $dailyUpdateBtn = this.$main.find('[data-role="daily-update-btn"]');
        const $schedulesViewBtn = this.$main.find('[data-role="schedules-view-btn"]');
        
        // Always show the filter section (contains view toggle and assignee filter)
        this.$adminActions.show();
        
        // Show Daily Update button for all users
        $dailyUpdateBtn.show();
        
        // Only show Create Project, Create Schedule, and Schedules View buttons for RTL Admin or HOD
        if (ctx && (ctx.is_rtl_admin || ctx.is_hod)) {
            $createBtn.show();
            $createScheduleBtn.show();
            $schedulesViewBtn.show();
        } else {
            $createBtn.hide();
            $createScheduleBtn.hide();
            $schedulesViewBtn.hide();
        }
    }

    renderAssigneeFilter() {
        const ctx = this.state.context;
        if (!ctx) {
            return;
        }

        // Show filter for all users (admins, HODs, and normal users)
        this.populateAssigneeFilter();
    }

    populateAssigneeFilter() {
        if (this.assigneeControl) {
            const selected = this.state.context.assignee || '';
            if (selected !== this.assigneeControl.get_value()) {
                this.suspendAssigneeOnChange = true;
                this.assigneeControl.set_value(selected);
                this.suspendAssigneeOnChange = false;
            }
        }
    }

    renderSection(section, projects) {
        const $container = this.$main.find(`.panel[data-section="${section}"] [data-role="list"]`);
        $container.empty();

        if (!projects.length) {
            $container.append(`<p class="text-muted small">${__('Nothing here yet.')}</p>`);
            return;
        }

        const limit = this.state.sectionLimits[section] || 5;
        const visible = projects.slice(0, limit);
        const remaining = projects.length - limit;

        visible.forEach((project) => {
            $container.append(this.getProjectCard(project, true));
        });

        if (remaining > 0) {
            const $loadMore = $(`
                <div class="load-more-wrapper">
                    <button class="btn btn-sm btn-default" data-action="load-more" data-section="${section}">
                        ${__('Load More')} (${remaining} ${__('remaining')})
                    </button>
                </div>
            `);
            $container.append($loadMore);
        }
    }

    getProjectCard(project, condensed = false) {
        const escape = frappe.utils.escape_html;
        const statusBadge = `<span class="status-badge status-${this.slug(project.status)}">${escape(project.status)}</span>`;
        
        if (condensed) {
            const endInfo = project.end_date ? frappe.datetime.str_to_user(project.end_date) : '';
            const latest = project.latest_status;
            let statusDot = '';
            if (latest) {
                const color = this.state.context.progress_colors?.[latest.progress_status] || '#64748b';
                statusDot = `<span class="status-dot" style="background:${color}" title="${escape(latest.progress_status)}"></span>`;
            }

            const actions = this.getCardActions(project);
            const assigneeName = project.assigned_to_name || project.assigned_to;

            return $(`
                <div class="project-card condensed" data-project="${escape(project.name)}">
                    <div class="card-header">
                        <div class="title-group">
                            ${statusDot}
                            <div class="title" title="${escape(project.project_name)}">${escape(project.project_name)}</div>
                        </div>
                    </div>
                    ${project.description ? `<div class="card-description text-muted small" style="padding: 0.5rem 1rem 0; font-size: 0.8rem;">${escape(project.description)}</div>` : ''}
                    <div class="card-body">
                        <div class="field-row compact">
                            <svg class="icon-user" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                            <span class="assignee-name">${escape(assigneeName)}</span>
                            ${endInfo ? `<span class="separator">•</span><svg class="icon-calendar" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg><span class="due-date">${endInfo}</span>` : ''}
                        </div>
                    </div>
                    <div class="card-actions">${actions}</div>
                </div>
            `);
        }

        const startInfo = project.start_date ? `${__('Started')}: ${frappe.datetime.str_to_user(project.start_date)}` : '';
        const endInfo = project.end_date ? `${__('End Date')}: ${frappe.datetime.str_to_user(project.end_date)}` : '';
        const finishInfo = project.finish_date ? `${__('Completed On')}: ${frappe.datetime.str_to_user(project.finish_date)}` : '';
        const latest = project.latest_status;
        let latestHtml = '';
        if (latest) {
            const color = this.state.context.progress_colors?.[latest.progress_status] || '#64748b';
            latestHtml = `
                <div class="latest-status">
                    <span class="status-dot" style="background:${color}"></span>
                    <span class="status-text">${escape(latest.progress_status)}</span>
                    <span class="status-date">${frappe.datetime.str_to_user(latest.log_date)}</span>
                </div>`;
        }

        const actions = this.getCardActions(project);

        return $(`
            <div class="project-card" data-project="${escape(project.name)}">
                <div class="card-header">
                    <div class="title">${escape(project.project_name)}</div>
                    ${statusBadge}
                </div>
                <div class="card-body">
                    <div class="field-row"><span class="label">${__('Assigned To')}:</span> ${escape(project.assigned_to)}</div>
                    ${project.description ? `<div class="field-row"><span class="label">${__('Description')}:</span> ${escape(project.description)}</div>` : ''}
                    <div class="field-row meta">${[startInfo, endInfo, finishInfo].filter(Boolean).join(' &middot; ')}</div>
                    ${latestHtml}
                </div>
                <div class="card-actions">${actions}</div>
            </div>
        `);
    }

    getCardActions(project) {
        const escape = frappe.utils.escape_html;
        const isAssignedUser = project.assigned_to === frappe.session.user;
        const ctx = this.state.context;
        const isAdminOrHOD = ctx && (ctx.is_rtl_admin || ctx.is_hod);
        const buttons = [];

        // Status change actions
        if (project.status === 'Not Started' && (isAssignedUser || this.isAdmin)) {
            buttons.push(`<button class="btn btn-xs btn-secondary" data-action="start" data-project="${escape(project.name)}">${__('Start')}</button>`);
        }

        if (project.status === 'In Process' && (isAssignedUser || this.isAdmin)) {
            buttons.push(`<button class="btn btn-xs btn-success" data-action="complete" data-project="${escape(project.name)}">${__('Complete')}</button>`);
        }

        if (project.status === 'Completed' && this.isAdmin) {
            buttons.push(`<button class="btn btn-xs btn-warning" data-action="reopen" data-project="${escape(project.name)}">${__('Reopen')}</button>`);
        }

        // Edit and Delete actions for Admin/HOD
        if (isAdminOrHOD) {
            buttons.push(`<button class="btn btn-xs btn-info" data-action="edit" data-project="${escape(project.name)}" title="${__('Edit Project')}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
            </button>`);
            buttons.push(`<button class="btn btn-xs btn-danger" data-action="delete" data-project="${escape(project.name)}" title="${__('Delete Project')}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>`);
        }

        if (!buttons.length) {
            return `<span class="text-muted small">${__('No actions available')}</span>`;
        }

        return buttons.join(' ');
    }

    renderBulkTable() {
        const ctx = this.state.context;
        const inProcess = ctx.projects.in_process || [];
        const targetAssignee = ctx.assignee || frappe.session.user;

        if (this.isAdmin && !ctx.assignee) {
            this.$bulkRows.html(`<tr><td colspan="3" class="text-muted">${__('Select an assignee to log daily status entries.')}</td></tr>`);
            return;
        }

        const rows = inProcess.filter((project) => project.assigned_to === targetAssignee);

        if (!rows.length) {
            this.$bulkRows.html(`<tr><td colspan="3" class="text-muted">${__('No in-process projects available for daily update.')}</td></tr>`);
            return;
        }

        this.$bulkRows.empty();
        rows.forEach((project) => {
            const escape = frappe.utils.escape_html;
            if (project.today_filed) {
                this.$bulkRows.append(`
                    <tr class="submitted" data-project="${escape(project.name)}">
                        <td>${escape(project.project_name)}<div class="small text-muted">${__('Already submitted for today')}</div></td>
                        <td colspan="2" class="text-muted">${__('No further action needed')}</td>
                    </tr>
                `);
                return;
            }

            const options = (ctx.progress_options || []).map((option) => `<option value="${escape(option)}">${escape(option)}</option>`).join('');

            this.$bulkRows.append(`
                <tr data-project="${escape(project.name)}">
                    <td>${escape(project.project_name)}</td>
                    <td>
                        <select class="form-control" data-role="progress-select">
                            <option value="">${__('Select')}</option>
                            ${options}
                        </select>
                    </td>
                    <td>
                        <input type="text" class="form-control" data-role="remarks" placeholder="${__('Remarks (optional)')}">
                    </td>
                </tr>
            `);
        });
    }

    bulkSubmit() {
        const entries = [];
        this.$bulkRows.find('tr').each((_, row) => {
            const $row = $(row);
            const project = $row.data('project');
            const progress = $row.find('[data-role="progress-select"]').val();
            if (!project || !progress) {
                return;
            }
            entries.push({
                project,
                progress_status: progress,
                remarks: $row.find('[data-role="remarks"]').val() || '',
            });
        });

        if (!entries.length) {
            frappe.msgprint(__('Select progress status for at least one project.'));
            return;
        }

        frappe.call({
            method: 'hkm.erpnext___custom.page.rtl_project_dashboard.rtl_project_dashboard.bulk_log_daily_status',
            args: { entries },
            freeze: true,
            callback: (response) => {
                const result = response.message;
                if (result.success) {
                    let message = `${__('Saved')} ${result.created_count} ${__('daily update(s) successfully.')}`;
                    if (result.errors && result.errors.length > 0) {
                        message += ` ${__('However,')} ${result.error_count} ${__('had errors.')}`;
                    }
                    frappe.show_alert({ message: message, indicator: result.error_count > 0 ? 'orange' : 'green' });
                    this.load();
                } else {
                    frappe.msgprint(__('Failed to save daily updates.'));
                }
            },
        });
    }

    createProject(values) {
        frappe.call({
            method: 'hkm.erpnext___custom.page.rtl_project_dashboard.rtl_project_dashboard.create_project',
            args: { data: values },
            freeze: true,
            callback: () => {
                frappe.show_alert({ message: __('Project created successfully.'), indicator: 'green' });
                this.projectDialog.hide();
                this.load();
            },
        });
    }

    updateStatus(project, status) {
        frappe.call({
            method: 'hkm.erpnext___custom.page.rtl_project_dashboard.rtl_project_dashboard.update_project_status',
            args: { project, status },
            freeze: true,
            callback: () => {
                frappe.show_alert({ message: __('Status updated.'), indicator: 'green' });
                this.load();
            },
        });
    }

    openProjectDialog() {
        const ctx = this.state.context;
        if (!ctx || (!ctx.is_rtl_admin && !ctx.is_hod)) {
            frappe.msgprint(__('Only RTL Admin or Department HOD can create projects.'));
            return;
        }

        if (!this.projectDialog) {
            // Get accessible users for assignment
            const assigneeOptions = (ctx.assignees || []).map(u => u.name);

            this.projectDialog = new frappe.ui.Dialog({
                title: __('Create RTL Project'),
                fields: [
                    { fieldname: 'project_name', fieldtype: 'Data', label: __('Project Name'), reqd: 1 },
                    { fieldname: 'description', fieldtype: 'Small Text', label: __('Description') },
                    {
                        fieldname: 'assigned_to',
                        fieldtype: 'Link',
                        label: __('Assign To'),
                        options: 'User',
                        reqd: 1,
                    },
                    { fieldname: 'end_date', fieldtype: 'Date', label: __('End Date'), reqd: 1 },
                ],
                primary_action_label: __('Create'),
                primary_action: (values) => {
                    this.createProject(values);
                },
            });

            // Restrict assignee selection to accessible users
            this.projectDialog.fields_dict.assigned_to.get_query = () => ({
                filters: {
                    enabled: 1,
                    user_type: 'System User',
                    name: ['in', assigneeOptions],
                },
                page_length: 20,
            });
        }

        const defaultAssignee = this.state.context.assignee || '';
        this.projectDialog.set_values({ assigned_to: defaultAssignee, end_date: null });
        this.projectDialog.show();
    }

    openDailyUpdateDialog() {
        const ctx = this.state.context;
        if (!ctx || !ctx.projects || !ctx.projects.in_process) {
            frappe.msgprint(__('No in-process projects available for daily update.'));
            return;
        }

        const inProcessProjects = ctx.projects.in_process || [];
        
        if (!this.dailyUpdateDialog) {
            this.dailyUpdateDialog = new frappe.ui.Dialog({
                title: __('Daily Progress Update'),
                size: 'large',
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'daily_update_html'
                    }
                ],
                primary_action_label: __('Save Daily Updates'),
                primary_action: () => {
                    this.bulkSubmitFromDialog();
                }
            });
        }

        // Build the table HTML
        const escape = frappe.utils.escape_html;
        const options = (ctx.progress_options || []).map((option) => `<option value="${escape(option)}">${escape(option)}</option>`).join('');
        
        let tableHTML = `
            <p class="text-muted mb-3">${__('Update daily progress for all in-process projects at once.')}</p>
            <div class="table-responsive">
                <table class="table table-bordered table-sm">
                    <thead>
                        <tr>
                            <th>${__('Project')}</th>
                            <th style="width: 220px;">${__('Forecast')}</th>
                            <th>${__('Remarks')}</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        inProcessProjects.forEach((project) => {
            if (project.today_filed) {
                tableHTML += `
                    <tr class="submitted" data-project="${escape(project.name)}">
                        <td>${escape(project.project_name)}<div class="small text-muted">${__('Already submitted for today')}</div></td>
                        <td colspan="2" class="text-muted">${__('No further action needed')}</td>
                    </tr>
                `;
            } else {
                tableHTML += `
                    <tr data-project="${escape(project.name)}">
                        <td>${escape(project.project_name)}</td>
                        <td>
                            <select class="form-control" data-role="progress-select">
                                <option value="">${__('Select')}</option>
                                ${options}
                            </select>
                        </td>
                        <td>
                            <input type="text" class="form-control" data-role="remarks" placeholder="${__('Remarks (optional)')}">
                        </td>
                    </tr>
                `;
            }
        });

        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;

        this.dailyUpdateDialog.fields_dict.daily_update_html.$wrapper.html(tableHTML);
        this.dailyUpdateDialog.show();
    }

    bulkSubmitFromDialog() {
        const entries = [];
        const $tbody = this.dailyUpdateDialog.fields_dict.daily_update_html.$wrapper.find('tbody');
        
        $tbody.find('tr').each((_, row) => {
            const $row = $(row);
            const project = $row.data('project');
            const progress = $row.find('[data-role="progress-select"]').val();
            if (!project || !progress) {
                return;
            }
            entries.push({
                project,
                progress_status: progress,
                remarks: $row.find('[data-role="remarks"]').val() || '',
            });
        });

        if (!entries.length) {
            frappe.msgprint(__('Please select forecast status for at least one project.'));
            return;
        }

        frappe.call({
            method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_project_api.bulk_daily_status',
            args: { entries },
            freeze: true,
            callback: ({ message }) => {
                if (message && message.success) {
                    let msg = `${__('Saved')} ${message.created_count || entries.length} ${__('daily update(s) successfully.')}`;
                    if (message.errors && message.errors.length > 0) {
                        msg += ` ${__('However,')} ${message.error_count} ${__('had errors.')}`;
                    }
                    frappe.show_alert({ message: msg, indicator: message.error_count > 0 ? 'orange' : 'green' });
                    this.dailyUpdateDialog.hide();
                    this.load();
                } else {
                    frappe.msgprint(__('Failed to save daily updates.'));
                }
            },
        });
    }

    reopenProject(project) {
        frappe.confirm(__('Reopen this project and move it back to In Process?'), () => {
            frappe.call({
                method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_project.reopen_project',
                args: { project_name: project },
                callback: () => {
                    frappe.show_alert({ message: __('Project reopened.'), indicator: 'orange' });
                    this.load();
                },
            });
        });
    }

    editProject(projectName) {
        // Fetch the project details using custom API that respects HOD permissions
        frappe.call({
            method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_project_api.get_project',
            args: {
                project_name: projectName
            },
            callback: ({ message }) => {
                if (!message) return;
                
                const project = message;
                const ctx = this.state.context;
                const assigneeOptions = ctx.assignee_options || [];

                if (!this.editProjectDialog) {
                    this.editProjectDialog = new frappe.ui.Dialog({
                        title: __('Edit Project'),
                        fields: [
                            {
                                fieldtype: 'Data',
                                fieldname: 'project_name',
                                label: __('Project Name'),
                                reqd: 1,
                            },
                            {
                                fieldtype: 'Small Text',
                                fieldname: 'description',
                                label: __('Description'),
                            },
                            {
                                fieldtype: 'Link',
                                fieldname: 'assigned_to',
                                label: __('Assigned To'),
                                options: 'User',
                                reqd: 1,
                            },
                            {
                                fieldtype: 'Date',
                                fieldname: 'end_date',
                                label: __('Due Date'),
                                reqd: 1,
                            },
                        ],
                        primary_action_label: __('Update'),
                        primary_action: (values) => {
                            this.updateProject(projectName, values);
                        },
                    });

                    // Restrict assignee selection
                    this.editProjectDialog.fields_dict.assigned_to.get_query = () => ({
                        filters: {
                            enabled: 1,
                            user_type: 'System User',
                            name: ['in', assigneeOptions],
                        },
                        page_length: 20,
                    });
                }

                // Set current values
                this.editProjectDialog.set_values({
                    project_name: project.project_name,
                    description: project.description || '',
                    assigned_to: project.assigned_to,
                    end_date: project.end_date
                });
                
                this.editProjectDialog.show();
            }
        });
    }

    updateProject(projectName, values) {
        frappe.call({
            method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_project_api.update_project',
            args: {
                project_name: projectName,
                values: values
            },
            freeze: true,
            callback: ({ message }) => {
                if (message) {
                    frappe.show_alert({ message: __('Project updated successfully.'), indicator: 'green' });
                    this.editProjectDialog.hide();
                    this.load();
                }
            },
        });
    }

    deleteProject(projectName) {
        frappe.confirm(
            __('Are you sure you want to delete this project? This action cannot be undone.'),
            () => {
                frappe.call({
                    method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_project_api.delete_project',
                    args: { project_name: projectName },
                    freeze: true,
                    callback: ({ message }) => {
                        if (message && message.success) {
                            frappe.show_alert({ message: __('Project deleted successfully.'), indicator: 'green' });
                            this.load();
                        }
                    },
                });
            }
        );
    }

    loadMore(section) {
        this.state.sectionLimits[section] = (this.state.sectionLimits[section] || 5) + 5;
        const projects = this.state.context.projects[section] || [];
        this.renderSection(section, projects);
    }

    slug(text) {
        return (text || '').toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'unknown';
    }

    initAssigneeControl() {
        if (this.assigneeControl || !this.$assigneeFilterWrapper.length) {
            return;
        }

        this.assigneeControl = frappe.ui.form.make_control({
            parent: this.$assigneeFilterWrapper[0],
            df: {
                fieldname: 'assignee_filter',
                fieldtype: 'Link',
                options: 'User',
                placeholder: __('Search Assignee...'),
                get_query: () => ({
                    filters: {
                        enabled: 1,
                        user_type: 'System User',
                    },
                    page_length: 20,
                }),
            },
            render_input: true,
            only_input: true,
        });

        this.assigneeControl.refresh();
        this.assigneeControl.$input.attr('placeholder', __('Search Assignee...'));
        
        // Hide the label
        if (this.assigneeControl.$wrapper) {
            this.assigneeControl.$wrapper.find('.control-label').hide();
        }

        this.assigneeControl.df.onchange = () => {
            if (this.suspendAssigneeOnChange) {
                return;
            }
            const value = this.assigneeControl.get_value();
            this.state.selectedAssignee = value || null;
            this.state.displayCount = 10; // Reset display count when filter changes
            this.load();
        };

        this.assigneeControl.refresh();
    }

    loadSchedulesView() {
        // Fetch schedules
        frappe.call({
            method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_project_api.get_project_schedules',
            callback: ({ message }) => {
                this.renderSchedulesView(message || []);
            }
        });
    }

    renderSchedulesView(schedules) {
        const escape = frappe.utils.escape_html;
        const $container = this.$main.find('[data-role="schedules-container"]');
        
        let tableHTML = `
            <div class="table-responsive">
                <table class="table table-bordered table-sm">
                    <thead>
                        <tr>
                            <th>${__('Schedule Name')}</th>
                            <th>${__('Template')}</th>
                            <th>${__('Frequency')}</th>
                            <th>${__('Duration')}</th>
                            <th>${__('Assignee')}</th>
                            <th>${__('First Run')}</th>
                            <th>${__('Next Run')}</th>
                            <th>${__('Status')}</th>
                            <th>${__('Actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        if (!schedules.length) {
            tableHTML += `<tr><td colspan="9" class="text-center text-muted py-4">${__('No schedules found. Click "Create Schedule" to add one.')}</td></tr>`;
        } else {
            schedules.forEach((schedule) => {
                const statusBadge = schedule.is_active 
                    ? `<span class="badge badge-success">${__('Active')}</span>`
                    : `<span class="badge badge-secondary">${__('Inactive')}</span>`;
                
                const firstRun = schedule.first_run_date 
                    ? frappe.datetime.str_to_user(schedule.first_run_date)
                    : '-';
                
                const nextRun = schedule.next_creation_date 
                    ? frappe.datetime.str_to_user(schedule.next_creation_date)
                    : '-';

                tableHTML += `
                    <tr>
                        <td><strong>${escape(schedule.schedule_name)}</strong></td>
                        <td>${escape(schedule.project_template)}</td>
                        <td>${escape(schedule.frequency)}</td>
                        <td>${schedule.duration_days} ${__('days')}</td>
                        <td>${escape(schedule.assigned_to)}</td>
                        <td>${firstRun}</td>
                        <td>${nextRun}</td>
                        <td>${statusBadge}</td>
                        <td>
                            <button class="btn btn-xs ${schedule.is_active ? 'btn-warning' : 'btn-success'}" 
                                    data-action="toggle-schedule" data-schedule="${escape(schedule.name)}" data-active="${schedule.is_active ? 0 : 1}">
                                ${schedule.is_active ? __('Deactivate') : __('Activate')}
                            </button>
                            <button class="btn btn-xs btn-danger" 
                                    data-action="delete-schedule" data-schedule="${escape(schedule.name)}">
                                ${__('Delete')}
                            </button>
                        </td>
                    </tr>
                `;
            });
        }

        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;

        $container.html(tableHTML);
        
        // Bind events for schedule actions
        $container.find('[data-action="toggle-schedule"]').on('click', (e) => {
            const scheduleName = $(e.currentTarget).data('schedule');
            const isActive = $(e.currentTarget).data('active');
            this.toggleSchedule(scheduleName, isActive);
        });
        
        $container.find('[data-action="delete-schedule"]').on('click', (e) => {
            const scheduleName = $(e.currentTarget).data('schedule');
            this.deleteSchedule(scheduleName);
        });
    }

    openCreateScheduleDialog() {
        const ctx = this.state.context;
        const assigneeOptions = ctx.assignee_options || [];

        if (!this.createScheduleDialog) {
            this.createScheduleDialog = new frappe.ui.Dialog({
                title: __('Create Project Schedule'),
                fields: [
                    {
                        fieldtype: 'Data',
                        fieldname: 'schedule_name',
                        label: __('Schedule Name'),
                        reqd: 1
                    },
                    {
                        fieldtype: 'Data',
                        fieldname: 'project_template',
                        label: __('Project Name Template'),
                        reqd: 1,
                        description: __('Use {month}, {year}, {date} as placeholders. Example: "Monthly Report - {month} {year}"')
                    },
                    {
                        fieldtype: 'Small Text',
                        fieldname: 'description',
                        label: __('Description')
                    },
                    {
                        fieldtype: 'Column Break'
                    },
                    {
                        fieldtype: 'Select',
                        fieldname: 'frequency',
                        label: __('Frequency'),
                        options: ['Daily', 'Weekly', 'Monthly', 'Quarterly'],
                        reqd: 1,
                        default: 'Monthly'
                    },
                    {
                        fieldtype: 'Int',
                        fieldname: 'start_day',
                        label: __('Day of Month'),
                        depends_on: 'eval:["Monthly", "Quarterly"].includes(doc.frequency)',
                        description: __('Day of month to create project (1-28)'),
                        default: 1
                    },
                    {
                        fieldtype: 'Int',
                        fieldname: 'duration_days',
                        label: __('Duration (Days)'),
                        reqd: 1,
                        default: 15,
                        description: __('Number of days from start to end date')
                    },
                    {
                        fieldtype: 'Link',
                        fieldname: 'assigned_to',
                        label: __('Assigned To'),
                        options: 'User',
                        reqd: 1
                    },
                    {
                        fieldtype: 'Date',
                        fieldname: 'first_run_date',
                        label: __('First Run Date'),
                        reqd: 1,
                        description: __('Date when this schedule should run for the first time')
                    }
                ],
                primary_action_label: __('Create Schedule'),
                primary_action: (values) => {
                    this.createSchedule(values);
                }
            });

            // Restrict assignee selection to accessible users (if available)
            this.createScheduleDialog.fields_dict.assigned_to.get_query = () => {
                const filters = {
                    enabled: 1,
                    user_type: 'System User'
                };
                
                // Only add name filter if assigneeOptions is not empty
                if (assigneeOptions && assigneeOptions.length > 0) {
                    filters.name = ['in', assigneeOptions];
                }
                
                return {
                    filters: filters,
                    page_length: 20
                };
            };
        }

        this.createScheduleDialog.clear();
        this.createScheduleDialog.show();
    }

    createSchedule(values) {
        frappe.call({
            method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_project_api.create_project_schedule',
            args: { values },
            freeze: true,
            callback: ({ message }) => {
                if (message) {
                    frappe.show_alert({ message: __('Schedule created successfully'), indicator: 'green' });
                    this.createScheduleDialog.hide();
                    this.loadSchedulesView(); // Refresh the schedules view
                }
            }
        });
    }

    toggleSchedule(scheduleName, isActive) {
        frappe.call({
            method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_project_api.toggle_schedule_status',
            args: { 
                schedule_name: scheduleName,
                is_active: isActive
            },
            callback: ({ message }) => {
                if (message && message.success) {
                    frappe.show_alert({ 
                        message: isActive ? __('Schedule activated') : __('Schedule deactivated'), 
                        indicator: 'green' 
                    });
                    this.loadSchedulesView(); // Refresh
                }
            }
        });
    }

    deleteSchedule(scheduleName) {
        frappe.confirm(
            __('Are you sure you want to delete this schedule?'),
            () => {
                frappe.call({
                    method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_project_api.delete_schedule',
                    args: { schedule_name: scheduleName },
                    callback: ({ message }) => {
                        if (message && message.success) {
                            frappe.show_alert({ message: __('Schedule deleted'), indicator: 'green' });
                            this.loadSchedulesView(); // Refresh
                        }
                    }
                });
            }
        );
    }

    openAddLeaveDialog() {
        this.openLeaveDialog();
    }

    openEditLeaveDialog(leaveId, fromDate, toDate, reason) {
        this.openLeaveDialog(leaveId, fromDate, toDate, reason);
    }

    openLeaveDialog(leaveId = null, fromDate = null, toDate = null, reason = null) {
        const isEdit = !!leaveId;
        const dialog = new frappe.ui.Dialog({
            title: isEdit ? __('Edit Leave') : __('Add Leave'),
            fields: [
                {
                    label: __('From Date'),
                    fieldname: 'from_date',
                    fieldtype: 'Date',
                    reqd: 1,
                    default: fromDate
                },
                {
                    label: __('To Date'),
                    fieldname: 'to_date',
                    fieldtype: 'Date',
                    reqd: 1,
                    default: toDate
                },
                {
                    label: __('Reason'),
                    fieldname: 'reason',
                    fieldtype: 'Small Text',
                    default: reason
                }
            ],
            primary_action_label: isEdit ? __('Update Leave') : __('Add Leave'),
            primary_action: (values) => {
                const method = isEdit ? 'update_leave' : 'create_leave';
                const args = isEdit ? { leave_id: leaveId, ...values } : values;
                
                frappe.call({
                    method: `hkm.erpnext___custom.doctype.rtl_project.rtl_leaves_calendar.${method}`,
                    args: args,
                    freeze: true,
                    callback: ({ message }) => {
                        if (message && message.success) {
                            frappe.show_alert({ 
                                message: isEdit ? __('Leave updated successfully') : __('Leave added successfully'), 
                                indicator: 'green' 
                            });
                            dialog.hide();
                            this.loadCalendarView();
                        }
                    }
                });
            }
        });
        dialog.show();
    }

    deleteLeave(leaveId) {
        frappe.confirm(__('Are you sure you want to delete this leave?'), () => {
            frappe.call({
                method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_leaves_calendar.delete_leave',
                args: { leave_id: leaveId },
                freeze: true,
                callback: ({ message }) => {
                    if (message && message.success) {
                        frappe.show_alert({ message: __('Leave deleted successfully'), indicator: 'green' });
                        this.loadCalendarView();
                    } else {
                        frappe.show_alert({ message: message.message || __('Error deleting leave'), indicator: 'red' });
                    }
                }
            });
        });
    }

    loadCalendarView() {
        frappe.call({
            method: 'hkm.erpnext___custom.doctype.rtl_project.rtl_leaves_calendar.get_leaves_and_holidays_calendar',
            args: { days: 30 },
            callback: ({ message }) => {
                if (message) {
                    this.renderCalendarView(message);
                }
            }
        });
    }

    renderCalendarView(data) {
        const $section = this.$main.find('.projects-section');
        
        // Hide table and panels containers
        this.$tableContainer.hide();
        this.$panelsContainer.hide();
        
        // Get or create calendar container
        let $calendarContainer = $section.find('.calendar-view-container');
        if (!$calendarContainer.length) {
            $section.append('<div class="calendar-view-container"></div>');
            $calendarContainer = $section.find('.calendar-view-container');
        }
        
        $calendarContainer.show();
        
        let html = `
            <div class="leaves-holidays-section">
                <div class="section-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h3>${__('Leaves & Holidays')}</h3>
                            <p class="subtitle">${__('Next 30 days - These dates are excluded from missed update count')}</p>
                        </div>
                        <button class="btn btn-primary btn-sm" data-action="add-leave">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px;">
                                <path d="M12 5v14M5 12h14"></path>
                            </svg>
                            ${__('Add Leave')}
                        </button>
                    </div>
                </div>
        `;
        
        if (data.events && data.events.length > 0) {
            html += `
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th style="width: 30%;">${__('Date')}</th>
                            <th style="width: 50%;">${__('Description')}</th>
                            <th style="width: 20%;">${__('Actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.events.forEach(event => {
                const badgeClass = event.type === 'leave' ? 'badge bg-info text-white' : 'badge bg-success text-white';
                const badge = `<span class="${badgeClass}">${event.type === 'leave' ? 'Leave' : 'Holiday'}</span>`;
                
                // Check if this is a future leave (not holiday) and can be edited
                const eventDate = new Date(event.date);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                const canEdit = event.type === 'leave' && event.leave_id && eventDate >= today;
                
                // Extract reason from description (remove "Leave - " prefix if present)
                const reason = event.description && event.description.startsWith('Leave - ') 
                    ? event.description.substring(8) 
                    : (event.description || '');
                
                const actions = canEdit ? `
                    <button class="btn btn-sm btn-outline-primary" data-action="edit-leave" data-leave-id="${frappe.utils.escape_html(event.leave_id)}" data-reason="${frappe.utils.escape_html(reason)}" title="${__('Edit Leave')}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                    </button>
                    <button class="btn btn-sm btn-outline-danger ms-1" data-action="delete-leave" data-leave-id="${frappe.utils.escape_html(event.leave_id)}" title="${__('Delete Leave')}">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3,6 5,6 21,6"></polyline>
                            <path d="M19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2"></path>
                        </svg>
                    </button>
                ` : '';
                
                html += `
                    <tr>
                        <td><strong>${event.date_formatted}</strong></td>
                        <td>${badge} ${frappe.utils.escape_html(event.description)}</td>
                        <td>${actions}</td>
                    </tr>
                `;
            });
            
            html += `
                    </tbody>
                </table>
            `;
        } else {
            html += `
                <div class="alert alert-info">
                    <p>${__('No leaves or holidays scheduled for the next 30 days')}</p>
                </div>
            `;
        }
        
        html += `</div>`;
        
        $calendarContainer.html(html).show();
    }

};
