frappe.ui.form.on("Remision", {
    customer(frm) {
        if (frm.doc.customer) {
            frappe.db.get_value("Customer", frm.doc.customer, "customer_name", (r) => {
                frm.set_value("customer_name", r.customer_name || frm.doc.customer);
            });
        }
    },

    item_group(frm) {
        if (!frm.doc.item_group) {
            return;
        }
        if (!frm.doc.warehouse) {
            frappe.msgprint(__("Selecciona un Almacen primero"));
            return;
        }

        frappe.dom.freeze(__("Cargando items del grupo..."));
        frappe.call({
            method: "erpnext_facturama.facturacionorcom.doctype.remision.remision.get_items_by_group",
            args: { item_group: frm.doc.item_group, warehouse: frm.doc.warehouse },
            callback(r) {
                frappe.dom.unfreeze();
                const items = r.message || [];
                if (!items.length) {
                    frappe.msgprint(__("No se encontraron items con stock en este grupo"));
                    return;
                }
                frm.clear_table("items");
                items.forEach((item) => {
                    const row = frm.add_child("items");
                    row.item_group = item.item_group;
                    row.item_code = item.item_code;
                    row.item_name = item.item_name;
                    row.qty = 0;
                    row.stock_qty = item.stock_qty;
                });
                frm.refresh_field("items");
                frappe.show_alert({
                    message: __("Se cargaron {0} items del grupo {1}", [items.length, frm.doc.item_group]),
                    indicator: "green",
                });
            },
        });
    },

    refresh(frm) {
        frm.add_custom_button(__("Limpiar"), () => {
            frm.clear_table("items");
            frm.refresh_field("items");
        }, __("Acciones"));
    },
});