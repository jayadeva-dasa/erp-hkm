// Copyright (c) 2025, HKM and contributors
// For license information, please see license.txt

/**
 * Simple check: if user has Auditor role, hide accounting dimensions
 */
function is_auditor() {
    try {
        return frappe && frappe.user && frappe.user.has_role && frappe.user.has_role('Auditor');
    } catch (e) {
        return false;
    }
}

// Fallback: common accounting dimension fieldnames (in case meta chain fails)
var COMMON_ACCOUNTING_DIMENSION_FIELDS = [
    'cost_center', 'project', 'cost_head', 'branch', 'department',
    'division', 'location', 'product_line', 'territory',
    'festival_event', 'volunteer', 'folk_residency', 'volunteer_head',
    'execution_department', 'if_income_or_expense', 'dimension_col_break'
];

/**
 * Get list of fieldnames that belong to "Accounting Dimensions" section for a doctype.
 * Uses insert_after chain; falls back to common list if meta has no section.
 */
function get_accounting_dimension_fieldnames(doctype) {
    var list = [];
    try {
        var meta = frappe.get_meta(doctype);
        if (!meta || !meta.docfields || !meta.docfields.length) {
            return COMMON_ACCOUNTING_DIMENSION_FIELDS.slice();
        }
        var in_section = {};
        in_section['accounting_dimensions_section'] = true;
        var changed = true;
        while (changed) {
            changed = false;
            meta.docfields.forEach(function(df) {
                if (df.fieldtype === 'Section Break' && df.fieldname === 'accounting_dimensions_section') return;
                if (in_section[df.fieldname]) return;
                if (in_section[df.insert_after]) {
                    in_section[df.fieldname] = true;
                    changed = true;
                }
            });
        }
        list = Object.keys(in_section).filter(function(k) { return k !== 'accounting_dimensions_section'; });
        if (list.length > 0) return list;
    } catch (e) {}
    // Fallback: return common fields that exist on this doctype
    var meta = frappe.get_meta(doctype);
    if (meta && meta.docfields) {
        var fieldnames = meta.docfields.map(function(df) { return df.fieldname; });
        return COMMON_ACCOUNTING_DIMENSION_FIELDS.filter(function(f) {
            return fieldnames.indexOf(f) !== -1;
        });
    }
    return COMMON_ACCOUNTING_DIMENSION_FIELDS.slice();
}

/**
 * Apply patches to Grid/GridRow so Auditor never sees accounting dimension columns.
 * Call with frm when form has grids (so Grid/GridRow are loaded).
 */
var auditor_grid_patches_applied = false;
function apply_auditor_grid_patches(frm) {
    if (auditor_grid_patches_applied || !is_auditor()) return;
    var Grid, GridRow;
    if (frm && frm.fields_dict) {
        for (var k in frm.fields_dict) {
            var control = frm.fields_dict[k];
            if (control && control.grid) {
                Grid = control.grid.constructor;
                if (control.grid.grid_rows && control.grid.grid_rows[0]) {
                    GridRow = control.grid.grid_rows[0].constructor;
                }
                break;
            }
        }
    }
    if (!Grid) Grid = frappe.ui.form.Grid || (window.Grid);
    if (!GridRow) GridRow = frappe.ui.form.GridRow || (window.GridRow);
    if (!Grid || !GridRow) return;
    try {

        // Patch Grid.setup_visible_columns: exclude accounting dimension columns
        if (!Grid.prototype._hkm_original_setup_visible_columns) {
            Grid.prototype._hkm_original_setup_visible_columns = Grid.prototype.setup_visible_columns;
            Grid.prototype.setup_visible_columns = function() {
                this._hkm_original_setup_visible_columns.call(this);
                if (!is_auditor()) return;
                var dim_fields = get_accounting_dimension_fieldnames(this.doctype);
                if (!this.visible_columns || dim_fields.length === 0) return;
                this.visible_columns = this.visible_columns.filter(function(col) {
                    var df = col[0];
                    return df && dim_fields.indexOf(df.fieldname) === -1;
                });
            };
        }

        // Patch Grid.setup_user_defined_columns: filter saved user settings for Auditor
        if (!Grid.prototype._hkm_original_setup_user_defined_columns) {
            Grid.prototype._hkm_original_setup_user_defined_columns = Grid.prototype.setup_user_defined_columns;
            Grid.prototype.setup_user_defined_columns = function() {
                this._hkm_original_setup_user_defined_columns.call(this);
                if (!this.user_defined_columns || !this.user_defined_columns.length) return;
                var dim_fields = get_accounting_dimension_fieldnames(this.doctype);
                if (dim_fields.length === 0) return;
                this.user_defined_columns = this.user_defined_columns.filter(function(df) {
                    return df && dim_fields.indexOf(df.fieldname) === -1;
                });
            };
        }

        // Patch GridRow.prepare_columns_for_dialog: don't show accounting dimension fields in Add/Remove Columns
        if (!GridRow.prototype._hkm_original_prepare_columns_for_dialog) {
            GridRow.prototype._hkm_original_prepare_columns_for_dialog = GridRow.prototype.prepare_columns_for_dialog;
            GridRow.prototype.prepare_columns_for_dialog = function(selected_fields) {
                var fields = this._hkm_original_prepare_columns_for_dialog.call(this, selected_fields);
                if (!is_auditor() || !this.grid || !this.grid.doctype) return fields;
                var dim_fields = get_accounting_dimension_fieldnames(this.grid.doctype);
                if (dim_fields.length === 0) return fields;
                return fields.filter(function(f) {
                    return f && dim_fields.indexOf(f.value) === -1;
                });
            };
        }

        // Patch GridRow.setup_columns_for_dialog: remove accounting dimension columns from selected when opening Configure Columns
        if (!GridRow.prototype._hkm_original_setup_columns_for_dialog) {
            GridRow.prototype._hkm_original_setup_columns_for_dialog = GridRow.prototype.setup_columns_for_dialog;
            GridRow.prototype.setup_columns_for_dialog = function() {
                this._hkm_original_setup_columns_for_dialog.call(this);
                if (!is_auditor() || !this.grid) return;
                var dim_fields = get_accounting_dimension_fieldnames(this.grid.doctype);
                if (dim_fields.length === 0) return;
                this.selected_columns_for_grid = (this.selected_columns_for_grid || []).filter(function(d) {
                    return dim_fields.indexOf(d.fieldname) === -1;
                });
            };
        }

        // Patch GridRow: when saving column settings, don't save accounting dimension columns
        if (!GridRow.prototype._hkm_original_update_user_settings_for_grid) {
            GridRow.prototype._hkm_original_update_user_settings_for_grid = GridRow.prototype.update_user_settings_for_grid;
            GridRow.prototype.update_user_settings_for_grid = function() {
                if (is_auditor() && this.grid && this.grid.doctype) {
                    var dim_fields = get_accounting_dimension_fieldnames(this.grid.doctype);
                    if (dim_fields.length > 0 && this.selected_columns_for_grid) {
                        this.selected_columns_for_grid = this.selected_columns_for_grid.filter(function(d) {
                            return dim_fields.indexOf(d.fieldname) === -1;
                        });
                    }
                }
                this._hkm_original_update_user_settings_for_grid.call(this);
            };
        }

        auditor_grid_patches_applied = true;
    } catch (e) {
        // Patches may run before Grid is loaded; will retry on form load
    }
}

/**
 * Hide accounting dimension columns in child table grids (DOM fallback).
 * Run with frm to use grid.doctype; otherwise hides by common field list.
 */
function hide_child_grid_dimension_columns(frm) {
    if (!is_auditor() || typeof $ === 'undefined') return;
    var fields_to_hide = [];
    if (frm && frm.grids && frm.grids.length) {
        frm.grids.forEach(function(grid_obj) {
            if (grid_obj.grid && grid_obj.grid.doctype) {
                var dims = get_accounting_dimension_fieldnames(grid_obj.grid.doctype);
                dims.forEach(function(f) {
                    if (fields_to_hide.indexOf(f) === -1) fields_to_hide.push(f);
                });
            }
        });
    }
    if (fields_to_hide.length === 0) {
        fields_to_hide = COMMON_ACCOUNTING_DIMENSION_FIELDS.slice();
    }
    fields_to_hide.forEach(function(fieldname) {
        $('.form-grid [data-fieldname="' + fieldname + '"]').addClass('hidden').hide().css({
            'display': 'none',
            'visibility': 'hidden',
            'width': '0',
            'min-width': '0',
            'overflow': 'hidden',
            'margin': '0',
            'padding': '0',
            'border': 'none'
        });
    });
}

/**
 * Inject CSS so accounting dimensions section is hidden immediately when rendered
 */
function inject_auditor_hide_css() {
    if (!is_auditor()) return;
    var styleId = 'hkm-hide-accounting-dimensions-auditor';
    if (document.getElementById(styleId)) return;
    var style = document.createElement('style');
    style.id = styleId;
    var gridSelectors = COMMON_ACCOUNTING_DIMENSION_FIELDS.map(function(f) {
        return '.form-grid [data-fieldname="' + f + '"]';
    }).join(',\n');
    style.textContent = [
        '.form-section[data-fieldname="accounting_dimensions_section"],',
        '[data-fieldname="accounting_dimensions_section"] {',
        '  display: none !important;',
        '  visibility: hidden !important;',
        '  height: 0 !important;',
        '  overflow: hidden !important;',
        '  margin: 0 !important;',
        '  padding: 0 !important;',
        '  border: none !important;',
        '}',
        '/* Hide accounting dimension columns in child table grids */',
        'body.user-is-auditor ' + gridSelectors + ' {',
        '  display: none !important;',
        '  width: 0 !important;',
        '  min-width: 0 !important;',
        '  overflow: hidden !important;',
        '  margin: 0 !important;',
        '  padding: 0 !important;',
        '  visibility: hidden !important;',
        '}'
    ].join('\n');
    (document.head || document.documentElement).appendChild(style);
    if (document.body) {
        document.body.classList.add('user-is-auditor');
    }
}

/**
 * Hide accounting dimensions section via JS (backup to CSS)
 */
function hide_accounting_dimensions() {
    if (!is_auditor()) return;
    if (typeof $ === 'undefined') return;

    // Section by data-fieldname
    $('[data-fieldname="accounting_dimensions_section"]').addClass('hidden').hide().css({
        'display': 'none',
        'visibility': 'hidden',
        'height': '0',
        'overflow': 'hidden',
        'margin': '0',
        'padding': '0'
    });

    // Section by label text (for any variant)
    $('.form-section .section-head').each(function() {
        var $head = $(this);
        if ($head.text().trim().indexOf('Accounting Dimension') !== -1) {
            $head.closest('.form-section').addClass('hidden').hide().css({
                'display': 'none',
                'visibility': 'hidden',
                'height': '0',
                'overflow': 'hidden'
            });
        }
    });
}

/**
 * Run hide repeatedly for a short period (catches late-rendered grid row form)
 */
function hide_accounting_dimensions_repeat(times, interval) {
    if (!is_auditor()) return;
    var count = 0;
    var t = setInterval(function() {
        hide_accounting_dimensions();
        count++;
        if (count >= times) clearInterval(t);
    }, interval);
}

// Run when Frappe is ready
function init_hide_for_auditor() {
    if (typeof frappe !== 'undefined' && frappe.ready) {
        frappe.ready(function() {
            setup_form_hooks();
            if (is_auditor()) {
                inject_auditor_hide_css();
                hide_accounting_dimensions();
                hide_accounting_dimensions_repeat(20, 100);
            }
        });
    }
    $(document).ready(function() {
        setup_form_hooks();
        if (is_auditor()) {
            inject_auditor_hide_css();
            hide_accounting_dimensions();
            setTimeout(hide_accounting_dimensions, 100);
            setTimeout(hide_accounting_dimensions, 300);
            setTimeout(hide_accounting_dimensions, 600);
        }
    });
}
init_hide_for_auditor();

// Form events (register only when Frappe is ready, once)
var form_hooks_setup = false;
function setup_form_hooks() {
    if (form_hooks_setup) return;
    if (typeof frappe === 'undefined' || !frappe.ui || !frappe.ui.form) return;
    form_hooks_setup = true;
    frappe.ui.form.on('*', {
        refresh: function(frm) {
            if (is_auditor()) {
                apply_auditor_grid_patches(frm);
                inject_auditor_hide_css();
                hide_accounting_dimensions();
                setTimeout(hide_accounting_dimensions, 50);
                setTimeout(hide_accounting_dimensions, 200);
                // Re-apply grid column visibility (reset so columns rebuild without accounting dimensions)
                if (frm.grids && frm.grids.length) {
                    frm.grids.forEach(function(grid_obj) {
                        if (grid_obj.grid) {
                            grid_obj.grid.visible_columns = null;
                            grid_obj.grid.setup_visible_columns();
                            grid_obj.grid.refresh();
                        }
                    });
                }
                // DOM fallback: hide dimension columns in child grids
                hide_child_grid_dimension_columns(frm);
                setTimeout(function() { hide_child_grid_dimension_columns(frm); }, 100);
                setTimeout(function() { hide_child_grid_dimension_columns(frm); }, 400);
            }
        },
        onload: function(frm) {
            if (is_auditor()) {
                apply_auditor_grid_patches(frm);
                inject_auditor_hide_css();
                hide_accounting_dimensions();
                setTimeout(hide_accounting_dimensions, 100);
                setTimeout(function() { hide_child_grid_dimension_columns(frm); }, 200);
            }
        }
    });
}

// Dialogs
$(document).ready(function() {
    $(document).on('frappe.ui.Dialog:shown', function() {
        if (is_auditor()) {
            hide_accounting_dimensions();
            hide_accounting_dimensions_repeat(15, 80);
        }
    });
});

// Mutation observer – delay slightly so child DOM is ready
var observer = new MutationObserver(function(mutations) {
    if (!is_auditor()) return;
    var hasNew = false;
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) hasNew = true;
    });
    if (hasNew) {
        setTimeout(hide_accounting_dimensions, 0);
        setTimeout(hide_accounting_dimensions, 50);
        setTimeout(hide_accounting_dimensions, 150);
        setTimeout(function() { hide_child_grid_dimension_columns(window.cur_frm || null); }, 50);
        setTimeout(function() { hide_child_grid_dimension_columns(window.cur_frm || null); }, 200);
    }
});

function start_observer() {
    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    }
}
if (document.body) {
    start_observer();
} else {
    $(document).ready(start_observer);
}
