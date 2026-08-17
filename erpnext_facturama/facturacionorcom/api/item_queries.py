import json

import frappe
from frappe.utils import cint
from frappe.utils.nestedset import get_descendants_of

from erpnext.controllers.queries import item_query


@frappe.whitelist()
def item_query_by_subrentados(doctype, txt, searchfield, start, page_len, filters):
	"""Return items inside or outside Sub Rentados for the current transaction flow."""
	if isinstance(filters, str):
		filters = json.loads(filters)
	else:
		filters = dict(filters or {})

	is_subcontracted = cint(filters.pop("is_subcontracted", 0))
	groups = ["Sub Rentados", *get_descendants_of("Item Group", "Sub Rentados")]
	filters["item_group"] = ["in" if is_subcontracted else "not in", groups]

	if doctype == "Purchase Order":
		filters["is_purchase_item"] = 1
	else:
		filters["is_sales_item"] = 1

	return item_query(doctype, txt, searchfield, start, page_len, filters)


@frappe.whitelist()
def configure_subrentados_client_scripts():
	"""Install the item filters for normal and subcontracted transaction flows."""
	scripts = {
		"Purchase Order": """frappe.ui.form.on(\"Purchase Order\", {
	setup(frm) { configure_subrentados_query(frm); },
	refresh(frm) { configure_subrentados_query(frm); },
	is_subcontracted(frm) { configure_subrentados_query(frm); }
});

function configure_subrentados_query(frm) {
	frm.set_query(\"item_code\", \"items\", () => ({
		query: \"erpnext_facturama.facturacionorcom.api.item_queries.item_query_by_subrentados\",
		filters: {
			is_subcontracted: frm.doc.is_subcontracted || 0,
			supplier: frm.doc.supplier || \"\",
			has_variants: 0
		}
	}));
}""",
		"Sales Order": """frappe.ui.form.on(\"Sales Order\", {
	setup(frm) { configure_subrentados_query(frm); },
	refresh(frm) { configure_subrentados_query(frm); },
	is_subcontracted(frm) { configure_subrentados_query(frm); }
});

function configure_subrentados_query(frm) {
	frm.set_query(\"item_code\", \"items\", () => ({
		query: \"erpnext_facturama.facturacionorcom.api.item_queries.item_query_by_subrentados\",
		filters: {
			is_subcontracted: frm.doc.is_subcontracted || 0,
			customer: frm.doc.customer || \"\",
			has_variants: 0
		}
	}));
}""",
		"Sales Invoice": """frappe.ui.form.on(\"Sales Invoice\", {
	setup(frm) { configure_subrentados_query(frm); },
	refresh(frm) { configure_subrentados_query(frm); }
});

function configure_subrentados_query(frm) {
	frm.set_query(\"item_code\", \"items\", () => ({
		query: \"erpnext_facturama.facturacionorcom.api.item_queries.item_query_by_subrentados\",
		filters: {
			is_subcontracted: 0,
			customer: frm.doc.customer || \"\",
			has_variants: 0
		}
	}));
}""",
	}

	for doctype, script in scripts.items():
		name = f"Filtro Sub Rentados - {doctype}"
		if frappe.db.exists("Client Script", name):
			frappe.db.set_value("Client Script", name, {"script": script, "enabled": 1})
		else:
			frappe.get_doc(
				{
					"doctype": "Client Script",
					"name": name,
					"dt": doctype,
					"script": script,
					"enabled": 1,
				}
			).insert(ignore_permissions=True)

	for name in (
		"orden de compra",
		"Orden de subcontratación",
		"Filtro Sub Rentados - Orden de Compra",
	):
		if frappe.db.exists("Client Script", name):
			frappe.db.set_value("Client Script", name, "enabled", 0)

	frappe.clear_cache(doctype="Client Script")
	return {"configured": list(scripts)}
