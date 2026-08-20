import frappe
from erpnext_facturama.facturacionorcom.utils.remision_print import REMISION_HTML, REMISION_CSS


@frappe.whitelist()
def upsert_remision_print_format():
    name = "remision_arrosa"
    existing_name = frappe.db.exists("Print Format", name)

    values = {
        "doc_type": "Remision",
        "print_format_type": "Jinja",
        "custom_format": 1,
        "raw_printing": 0,
        "disabled": 0,
        "html": REMISION_HTML,
        "css": REMISION_CSS,
    }

    if existing_name:
        frappe.db.set_value("Print Format", name, values)
    else:
        doc = frappe.get_doc({
            "doctype": "Print Format",
            "name": name,
            "module": "FacturacionORCom",
            **values,
        })
        doc.insert(ignore_permissions=True)

    frappe.db.commit()
    return {"ok": True, "name": name}
