// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on("HKM Budget", {
  refresh(frm) {
    if (!frm.is_new()) {
      // Add Refresh Connections button
      frm.add_custom_button(__("Refresh Connections"), () => {
        frm.trigger("load_budget_connections");
      });
      
      // Load connections
      frm.trigger("load_budget_connections");
    }
  },

  load_budget_connections(frm) {
    // Get the HTML field wrapper
    if (!frm.fields_dict.connections_html) {
      console.error("connections_html field not found");
      return;
    }

    const wrapper = frm.fields_dict.connections_html.$wrapper;
    
    // Show loading message
    wrapper.html(`
      <div style="padding: 15px; text-align: center;">
        <i class="fa fa-spinner fa-spin"></i> Loading connections...
      </div>
    `);

    // Fetch connections
    frappe.call({
      method: "hkm.erpnext___custom.doctype.hkm_budget.hkm_budget_connections.get_budget_connections",
      args: {
        budget_name: frm.doc.name
      },
      callback: function(r) {
        if (r.message) {
          render_connections(frm, r.message);
        } else {
          wrapper.html(`
            <div style="padding: 15px;">
              <p style="color: #888;">No connections data returned</p>
            </div>
          `);
        }
      },
      error: function(r) {
        wrapper.html(`
          <div style="padding: 15px;">
            <p style="color: #ef4444;">Error loading connections. Check console for details.</p>
          </div>
        `);
        console.error("Error loading connections:", r);
      }
    });
  },

});

function render_connections(frm, data) {
  const wrapper = frm.fields_dict.connections_html.$wrapper;
  
  if (!data || !data.connections) {
    wrapper.html(`
      <div style="padding: 15px;">
        <p style="color: #888;">No connections found</p>
      </div>
    `);
    return;
  }

    let html = `
      <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; margin-top: 15px;">
        <h4 style="margin-top: 0; color: #2563eb; display: flex; align-items: center;">
          <i class="fa fa-link" style="margin-right: 8px;"></i>
          Budget Connections
        </h4>
        
        ${data.dimensions && data.dimensions.length > 0 ? `
          <div style="margin-bottom: 15px; padding: 10px; background: white; border-radius: 4px;">
            <strong>Dimensions:</strong> 
            ${data.dimensions.map(d => `<span style="margin-left: 10px;">${d[0]}: <strong>${d[1]}</strong></span>`).join(', ')}
          </div>
        ` : ''}
        
        <div style="margin-bottom: 10px; color: #666;">
          <strong>Fiscal Year:</strong> ${data.fiscal_year} 
          <span style="margin-left: 15px;">(${data.date_range})</span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
    `;

    // Add connection cards
    const docTypes = [
      { key: "Payment Entry", icon: "fa-money", color: "#22c55e" },
      { key: "Purchase Invoice", icon: "fa-file-text", color: "#3b82f6" },
      { key: "Purchase Order", icon: "fa-shopping-cart", color: "#f97316" },
      { key: "Journal Entry", icon: "fa-book", color: "#9333ea" },
      { key: "Stock Entry", icon: "fa-cubes", color: "#ef4444" }
    ];

    docTypes.forEach(dt => {
      const conn = data.connections[dt.key];
      if (conn && conn.count > 0) {
        html += `
          <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid ${dt.color}; cursor: pointer;"
               onclick="frappe.set_route('List', '${dt.key}', {'${get_filter_field(dt.key)}': ['in', [${conn.items.map(i => `'${i.name}'`).join(',')}]]})">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
              <i class="fa ${dt.icon}" style="font-size: 24px; color: ${dt.color}; margin-right: 10px;"></i>
              <div>
                <div style="font-weight: 600; font-size: 14px;">${dt.key}</div>
                <div style="font-size: 24px; font-weight: bold; color: ${dt.color};">${conn.count}</div>
              </div>
            </div>
            ${conn.count > 10 ? `<div style="font-size: 12px; color: #666;">Showing 10 of ${conn.total_count}</div>` : ''}
            <div style="margin-top: 10px; font-size: 12px; color: #666;">
              Click to view all →
            </div>
          </div>
        `;
      } else {
        html += `
          <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; opacity: 0.5;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
              <i class="fa ${dt.icon}" style="font-size: 24px; color: #ccc; margin-right: 10px;"></i>
              <div>
                <div style="font-weight: 600; font-size: 14px; color: #999;">${dt.key}</div>
                <div style="font-size: 24px; font-weight: bold; color: #ccc;">0</div>
              </div>
            </div>
          </div>
        `;
      }
    });

    html += `
        </div>
      </div>
    `;

  wrapper.html(html);
}

function get_filter_field(doctype) {
  return "name";
}
