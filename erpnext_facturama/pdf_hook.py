import frappe
import base64
import xml.etree.ElementTree as ET


def inject_cfdi_seals(jenv, template, print_format, args):
    """Hook: injects parsed CFDI seal data into print format context, then renders HTML."""
    default_seals = {"sello_emisor": "", "no_cert_emisor": "", "sello_sat": "", "no_cert_sat": "", "uuid": "", "qr_url": ""}
    doc = args.get("doc")
    seals = dict(default_seals)

    if doc and getattr(doc, "mx_stamped_xml", None):
        xml_str = None
        try:
            xml_str = base64.b64decode(doc.mx_stamped_xml).decode("utf-8")
        except Exception:
            xml_str = getattr(doc, "mx_stamped_xml", None)

        if xml_str:
            try:
                root = ET.fromstring(xml_str)
                seals["sello_emisor"] = root.get("Sello", "")
                seals["no_cert_emisor"] = root.get("NoCertificado", "")

                ns_tfd = "http://www.sat.gob.mx/TimbreFiscalDigital"
                for elem in root.iter("{" + ns_tfd + "}TimbreFiscalDigital"):
                    seals["no_cert_sat"] = elem.get("NoCertificadoSAT", "")
                    seals["sello_sat"] = elem.get("SelloSAT", "")
                    seals["uuid"] = elem.get("UUID", "")

                company = frappe.db.get_value("Company", doc.company, "tax_id") if doc.company else ""
                customer_rfc = frappe.db.get_value("Customer", doc.customer, "tax_id") if doc.customer else ""
                rfc_emisor = company or ""
                rfc_receptor = customer_rfc or ""
                total_str = str(doc.grand_total)
                sello_last8 = seals["sello_emisor"][-8:] if seals["sello_emisor"] else ""
                uuid_val = seals["uuid"] or doc.mx_uuid or ""
                seals["qr_url"] = f"https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?id={uuid_val}&re={rfc_emisor}&rr={rfc_receptor}&tt={total_str}&fe={sello_last8}"
            except Exception as e:
                frappe.log_error(f"[pdf_hook] Error parsing CFDI XML for {doc.name}: {e}", "pdf_hook")

    args["seals"] = seals
    return template.render(args, filters={"len": len})
