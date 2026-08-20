import frappe


ARROSA_QUOTATION_HTML = """
{% set company = frappe.get_doc("Company", doc.company) if doc.company else None %}
{% set logo_url = frappe.utils.get_url(company.company_logo) if company and company.company_logo else "" %}
<div class="arrosa-quote">
  <div class="header">
    <div class="left">
      {% if logo_url %}
      <img src="{{ logo_url }}" class="logo" alt="Arrosa Medical" />
      {% else %}
      <div class="logo-fallback">ARROSA MEDICAL</div>
      {% endif %}
    </div>
    <div class="right">
      <div class="company">{{ (company.company_name if company else doc.company) or "" }}</div>
      <div class="line"><strong>RFC:</strong> {{ (company.tax_id if company else "") or "" }}</div>
      <div class="line"><strong>Folio:</strong> {{ doc.name }}</div>
      <div class="line"><strong>Fecha:</strong> {{ frappe.utils.formatdate(doc.transaction_date) }}</div>
    </div>
  </div>

  <div class="meta-grid">
    <div><span class="k">Hospital:</span> {{ doc.customer_hospital or "" }}</div>
    <div><span class="k">Cirujano:</span> {{ doc.customer_cirujano or "" }}</div>
    <div><span class="k">Hora:</span> {{ doc.customer_hora or "" }}</div>
    <div><span class="k">Paciente:</span> {{ doc.customer_paciente or "" }}</div>
    <div><span class="k">Edad:</span> {{ doc.customer_edad or "" }}</div>
    <div><span class="k">Procedimiento:</span> {{ doc.customer_procedimiento or "" }}</div>
  </div>

  <div class="title">COTIZACION</div>

  <table class="items">
    <thead>
      <tr>
        <th class="ref">Referencia</th>
        <th>Descripcion</th>
        <th class="num">Precio Unitario</th>
        <th class="num">Cantidad</th>
        <th class="num">Total</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      <tr>
        <td class="ref">{{ row.item_code or "" }}</td>
        <td>{{ row.description or row.item_name or "" }}</td>
        <td class="num">{{ frappe.utils.fmt_money((row.rate if row.rate else ((row.amount / row.qty) if row.qty else 0)), currency=doc.currency) }}</td>
        <td class="num">{{ row.qty }}</td>
        <td class="num">{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <table class="totals">
    <tr>
      <td>SUBTOTAL</td>
      <td class="num">{{ frappe.utils.fmt_money(doc.net_total, currency=doc.currency) }}</td>
    </tr>
    <tr>
      <td>IVA</td>
      <td class="num">{{ frappe.utils.fmt_money(doc.total_taxes_and_charges, currency=doc.currency) }}</td>
    </tr>
    <tr class="grand">
      <td>TOTAL</td>
      <td class="num">{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</td>
    </tr>
  </table>

  <div class="note">PRECIOS + IVA</div>
</div>
""".strip()


ARROSA_QUOTATION_CSS = """
.arrosa-quote {
  font-family: "Helvetica Neue", Arial, sans-serif;
  color: #222;
  font-size: 12px;
}
.arrosa-quote .header {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 18px;
  align-items: start;
  margin-bottom: 14px;
}
.arrosa-quote .logo {
  max-width: 220px;
  max-height: 120px;
  object-fit: contain;
}
.arrosa-quote .logo-fallback {
  font-weight: 700;
  letter-spacing: 1px;
}
.arrosa-quote .company {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 4px;
}
.arrosa-quote .line {
  margin: 2px 0;
}
.arrosa-quote .meta-grid {
  border: 1px solid #ddd;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
  padding: 10px;
  margin-bottom: 12px;
}
.arrosa-quote .k {
  font-weight: 700;
}
.arrosa-quote .title {
  border: 1px solid #333;
  font-weight: 700;
  text-align: center;
  padding: 6px;
  margin-bottom: 10px;
}
.arrosa-quote .items {
  width: 100%;
  border-collapse: collapse;
}
.arrosa-quote .items th,
.arrosa-quote .items td {
  border-bottom: 1px solid #e4e4e4;
  padding: 6px;
  vertical-align: top;
}
.arrosa-quote .items thead th {
  border-top: 1px solid #999;
  border-bottom: 1px solid #999;
  text-transform: uppercase;
  font-size: 11px;
}
.arrosa-quote .items .ref {
  width: 16%;
}
.arrosa-quote .num {
  text-align: right;
  white-space: nowrap;
}
.arrosa-quote .totals {
  width: 280px;
  margin-left: auto;
  margin-top: 12px;
  border-collapse: collapse;
}
.arrosa-quote .totals td {
  border: 1px solid #bdbdbd;
  padding: 6px 8px;
  font-weight: 600;
}
.arrosa-quote .totals .grand td {
  font-weight: 800;
}
.arrosa-quote .note {
  margin-top: 18px;
  font-size: 11px;
  font-weight: 700;
}
""".strip()


ARROSA_SALES_ORDER_HTML = """
{% set company = frappe.get_doc("Company", doc.company) if doc.company else None %}
{% set logo_url = frappe.utils.get_url(company.company_logo) if company and company.company_logo else "" %}
{% set customer = frappe.get_doc("Customer", doc.customer) if doc.customer else None %}
<div class="arrosa-quote">
  <div class="header">
    <div class="left">
      {% if logo_url %}
      <img src="{{ logo_url }}" class="logo" alt="Arrosa Medical" />
      {% else %}
      <div class="logo-fallback">ARROSA MEDICAL</div>
      {% endif %}
    </div>
    <div class="right">
      <div class="company">{{ (company.company_name if company else doc.company) or "" }}</div>
      <div class="line"><strong>RFC:</strong> {{ (company.tax_id if company else "") or "" }}</div>
      <div class="line"><strong>Folio:</strong> {{ doc.name }}</div>
      <div class="line"><strong>Fecha:</strong> {{ frappe.utils.formatdate(doc.transaction_date) }}</div>
    </div>
  </div>

  <div class="meta-grid">
    <div><span class="k">Hospital:</span> {{ doc.customer_hospital or "" }}</div>
    <div><span class="k">Cirujano:</span> {{ doc.customer_cirujano or "" }}</div>
    <div><span class="k">Hora:</span> {{ doc.customer_hora or "" }}</div>
    <div><span class="k">Paciente:</span> {{ doc.customer_paciente or "" }}</div>
    <div><span class="k">Edad:</span> {{ doc.customer_edad or "" }}</div>
    <div><span class="k">Procedimiento:</span> {{ doc.customer_procedimiento or "" }}</div>
  </div>

  <div class="title">ORDEN DE VENTA {{ (doc.customer_hospital or "").upper() }}</div>

  <table class="items">
    <thead>
      <tr>
        <th class="ref">Referencia</th>
        <th>Descripcion</th>
        <th class="num">Precio Unitario</th>
        <th class="num">Cantidad</th>
        <th class="num">Total</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      <tr>
        <td class="ref">{{ row.item_code or "" }}</td>
        <td>{{ row.description or row.item_name or "" }}</td>
        <td class="num">{{ frappe.utils.fmt_money((row.rate if row.rate else ((row.amount / row.qty) if row.qty else 0)), currency=doc.currency) }}</td>
        <td class="num">{{ row.qty }}</td>
        <td class="num">{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <table class="totals">
    <tr>
      <td>SUBTOTAL</td>
      <td class="num">{{ frappe.utils.fmt_money(doc.net_total, currency=doc.currency) }}</td>
    </tr>
    <tr>
      <td>IVA</td>
      <td class="num">{{ frappe.utils.fmt_money(doc.total_taxes_and_charges, currency=doc.currency) }}</td>
    </tr>
    <tr class="grand">
      <td>TOTAL</td>
      <td class="num">{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</td>
    </tr>
  </table>

  <div class="note">PRECIOS + IVA</div>
</div>
""".strip()

ARROSA_SALES_ORDER_CSS = ARROSA_QUOTATION_CSS



@frappe.whitelist(allow_guest=True)
def get_cfdi_seals(doc):
    """Extract CFDI seal data from stamped XML."""
    import base64
    import xml.etree.ElementTree as ET
    result = {"sello_emisor": "", "no_cert_emisor": "", "sello_sat": "", "no_cert_sat": "", "uuid": "", "qr_url": "", "cadena_original": "", "rfc_prov_certif": "", "fecha_timbrado": ""}
    if not doc.mx_stamped_xml:
        return result
    try:
        xml_str = base64.b64decode(doc.mx_stamped_xml).decode("utf-8")
    except Exception:
        try:
            xml_str = doc.mx_stamped_xml
        except Exception:
            return result
    try:
        root = ET.fromstring(xml_str)
    except Exception:
        return result
    result["sello_emisor"] = root.get("Sello", "")
    result["no_cert_emisor"] = root.get("NoCertificado", "")
    ns_tfd = "http://www.sat.gob.mx/TimbreFiscalDigital"
    for elem in root.iter("{" + ns_tfd + "}TimbreFiscalDigital"):
        result["no_cert_sat"] = elem.get("NoCertificadoSAT", "")
        result["sello_sat"] = elem.get("SelloSAT", "")
        result["uuid"] = elem.get("UUID", "")
        fecha_timbrado = elem.get("FechaTimbrado", "")
        rfc_prov = elem.get("RfcProvCertif", "")
        result["rfc_prov_certif"] = rfc_prov
        result["fecha_timbrado"] = fecha_timbrado
        sello_cfd = elem.get("SelloCFD", "")
        result["cadena_original"] = (
            f"||1.1|{result['uuid']}|{fecha_timbrado}|{rfc_prov}|{sello_cfd}|"
            f"{result['no_cert_sat']}|{result['sello_sat']}||"
        )
    # Build QR URL
    company = frappe.get_doc("Company", doc.company) if doc.company else None
    customer = frappe.get_doc("Customer", doc.customer) if doc.customer else None
    rfc_emisor = company.tax_id if company else ""
    rfc_receptor = customer.tax_id if customer else ""
    total_str = str(doc.grand_total)
    sello_last8 = result["sello_emisor"][-8:] if result["sello_emisor"] else ""
    uuid_val = result["uuid"] or doc.mx_uuid or ""
    result["qr_url"] = f"https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?id={uuid_val}&re={rfc_emisor}&rr={rfc_receptor}&tt={total_str}&fe={sello_last8}"
    return result

ARROSA_SALES_INVOICE_HTML = """
{% set company = frappe.get_doc("Company", doc.company) if doc.company else None %}
{% set logo_url = frappe.utils.get_url(company.company_logo) if company and company.company_logo else "" %}
{% set customer = frappe.get_doc("Customer", doc.customer) if doc.customer else None %}
{% set customer_zip = frappe.db.get_value("Address", doc.customer_address, "pincode") if doc.customer_address else "" %}
{% set company_zip = (frappe.db.get_value("Facturama Emisor", {"company": doc.company, "active": 1}, "expedition_place") if doc.company else "") or "" %}
{% set invoice_uuid = doc.mx_uuid or "" %}
<div class="arrosa-invoice">
  <table class="inv-header">
    <tr>
      <td class="logo-cell">
        {% if logo_url %}
        <img src="{{ logo_url }}" class="logo" alt="Arrosa Medical" />
        {% else %}
        <div class="logo-fallback">ARROSA MEDICAL</div>
        {% endif %}
      </td>
      <td class="title-cell">ARROSA MEDICAL</td>
    </tr>
  </table>

  <table class="meta-grid">
    <tr>
      <td class="meta-col">
        <div><span class="k">RFC emisor:</span> {{ (company.tax_id if company else "") or "" }}</div>
        <div><span class="k">Nombre emisor:</span> {{ (company.company_name if company else doc.company) or "" }}</div>
        <div><span class="k">Folio:</span> {{ doc.name }}</div>
        <div><span class="k">RFC receptor:</span> {{ (customer.tax_id if customer else "") or "" }}</div>
        <div><span class="k">Nombre receptor:</span> {{ doc.customer_name or doc.customer or "" }}</div>
        <div><span class="k">Codigo postal receptor:</span> {{ customer_zip or "" }}</div>
        <div><span class="k">Uso CFDI:</span> {{ doc.mx_cfdi_use or "" }}</div>
      </td>
      <td class="meta-col">
        <div><span class="k">Folio fiscal:</span> {{ invoice_uuid }}</div>
        <div><span class="k">No. serie del CSD:</span> {{ (seals|default({})).get('no_cert_emisor', '') }}</div>
        <div><span class="k">Serie:</span> {{ doc.naming_series or "" }}</div>
        <div><span class="k">Codigo postal, fecha y hora emision:</span> {{ (company_zip or "") }} {{ frappe.utils.format_datetime(doc.posting_date ~ " " ~ (doc.posting_time or "00:00:00")) }}</div>
        <div><span class="k">Efecto de comprobante:</span> Ingreso</div>
        <div><span class="k">Regimen fiscal:</span> {{ (company.mx_tax_regime if company and company.mx_tax_regime else (company.sat_tax_regime if company else "")) or "" }}</div>
        <div><span class="k">Exportacion:</span> No aplica</div>
      </td>
    </tr>
  </table>

  <div class="section-title">Conceptos</div>
  <table class="items">
    <thead>
      <tr>
        <th>Clave del producto y/o servicio</th>
        <th>No. identificacion</th>
        <th class="num">Cantidad</th>
        <th>Clave de unidad</th>
        <th>Unidad</th>
        <th class="num">Valor unitario</th>
        <th class="num">Importe</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      {% set item_doc = frappe.get_cached_doc("Item", row.item_code) if row.item_code else None %}
      {% set sat_product = (item_doc.sat_product_key if item_doc and item_doc.sat_product_key else (item_doc.sat_item_key if item_doc and item_doc.sat_item_key else (item_doc.sat_clave_producto if item_doc and item_doc.sat_clave_producto else "01010101"))) %}
      {% set sat_unit = (item_doc.sat_uom if item_doc and item_doc.sat_uom else (item_doc.sat_unit_code if item_doc and item_doc.sat_unit_code else (item_doc.sat_clave_unidad if item_doc and item_doc.sat_clave_unidad else "E48"))) %}
      <tr>
        <td>{{ sat_product }}</td>
        <td>{{ row.item_code or "" }}</td>
        <td class="num">{{ row.qty }}</td>
        <td>{{ sat_unit }}</td>
        <td>{{ row.uom or "" }}</td>
        <td class="num">{{ frappe.utils.fmt_money((row.rate if row.rate else ((row.amount / row.qty) if row.qty else 0)), currency=doc.currency) }}</td>
        <td class="num">{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
      </tr>
      <tr class="desc-row">
        <td colspan="7"><strong>Descripcion:</strong> {{ row.description or row.item_name or "" }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="totals-wrap">
    <table class="totals">
      <tr>
        <td>Moneda:</td>
        <td>{{ doc.currency or "MXN" }}</td>
      </tr>
      <tr>
        <td>Forma de pago:</td>
        <td>{{ doc.mx_payment_mode or doc.mode_of_payment or "" }}</td>
      </tr>
      <tr>
        <td>Metodo de pago:</td>
        <td>{{ doc.mx_payment_option or "" }}</td>
      </tr>
      <tr>
        <td>Subtotal</td>
        <td class="num">{{ frappe.utils.fmt_money(doc.net_total, currency=doc.currency) }}</td>
      </tr>
      <tr>
        <td>Impuestos trasladados</td>
        <td class="num">{{ frappe.utils.fmt_money(doc.total_taxes_and_charges, currency=doc.currency) }}</td>
      </tr>
      <tr class="grand">
        <td>Total</td>
        <td class="num">{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</td>
      </tr>
    </table>
  </div>

  {% set seals = seals|default({}) %}

  {% if invoice_uuid or seals.get('uuid') %}
  <div class="seal-section">
    <div class="seal-title">Sellos Digitales</div>

    <div class="seal-row">
      <span class="k">Sello Digital del Emisor:</span>
      <div class="seal-text">{{ seals.sello_emisor }}</div>
    </div>

    <div class="seal-row">
      <span class="k">No. Certificado del Emisor:</span> {{ seals.no_cert_emisor }}
    </div>

    <div class="seal-row">
      <span class="k">Sello del SAT:</span>
      <div class="seal-text">{{ seals.sello_sat }}</div>
    </div>

    <div class="seal-row">
      <span class="k">No. Certificado SAT:</span> {{ seals.no_cert_sat }}
    </div>

    <div class="seal-row">
      <span class="k">UUID:</span> {{ invoice_uuid or seals.get('uuid') or "" }}
    </div>

    {% if seals.qr_url %}
    <table class="qr-cadena">
      <tr>
        <td class="qr-cell">
          <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={{ seals.qr_url|urlencode }}" alt="CFDI QR" />
        </td>
        <td class="cadena-cell">
          <div class="k">Cadena Original del complemento de certificacion digital del SAT:</div>
          <div class="cadena-text">{{ seals.cadena_original }}</div>
          <div class="cert-meta">
            <div><span class="k">RFC del proveedor de certificacion:</span> {{ seals.rfc_prov_certif }}</div>
            <div><span class="k">Fecha y hora de certificacion:</span> {{ seals.fecha_timbrado }}</div>
            <div><span class="k">No. de serie del certificado:</span> {{ seals.no_cert_sat }}</div>
          </div>
        </td>
      </tr>
    </table>
    {% endif %}
  </div>
  {% endif %}
</div>
""".strip()


ARROSA_SALES_INVOICE_CSS = """
.arrosa-invoice {
  font-family: "Helvetica Neue", Arial, sans-serif;
  color: #2a2a2a;
  font-size: 10px;
}
.arrosa-invoice .inv-header {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}
.arrosa-invoice .inv-header .logo-cell {
  width: 40%;
  vertical-align: middle;
}
.arrosa-invoice .inv-header .title-cell {
  width: 60%;
  vertical-align: middle;
  font-size: 27px;
  font-weight: 700;
  text-align: center;
  letter-spacing: 0.4px;
}
.arrosa-invoice .logo {
  max-width: 110px;
  max-height: 80px;
  object-fit: contain;
}
.arrosa-invoice .logo-fallback {
  font-size: 16px;
  font-weight: 700;
}
.arrosa-invoice .meta-grid {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}
.arrosa-invoice .meta-grid .meta-col {
  width: 50%;
  vertical-align: top;
  padding: 0;
}
.arrosa-invoice .meta-grid .meta-col > div {
  margin: 1px 0;
}
.arrosa-invoice .meta-grid .meta-col:first-child {
  padding-right: 12px;
}
.arrosa-invoice .k {
  font-weight: 700;
}
.arrosa-invoice .section-title {
  font-size: 14px;
  font-weight: 700;
  margin: 6px 0;
}
.arrosa-invoice .items {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}
.arrosa-invoice .items th,
.arrosa-invoice .items td {
  border: 1px solid #8d8d8d;
  padding: 3px 5px;
  vertical-align: top;
  font-size: 9px;
}
.arrosa-invoice .items th {
  background: #f4f4f4;
  font-weight: 700;
}
.arrosa-invoice .items .desc-row td {
  border-top: 0;
}
.arrosa-invoice .num {
  text-align: right;
  white-space: nowrap;
}
.arrosa-invoice .totals-wrap {
  display: flex;
  justify-content: flex-end;
}
.arrosa-invoice .totals {
  width: 360px;
  border-collapse: collapse;
}
.arrosa-invoice .totals td {
  border: 1px solid #8d8d8d;
  padding: 5px 7px;
}
.arrosa-invoice .totals .grand td {
  font-weight: 800;
}
.arrosa-invoice .seal-block {
  margin-top: 10px;
  border-top: 1px solid #ddd;
  padding-top: 6px;
}
.arrosa-invoice .footer-note {
  margin-top: 14px;
  text-align: center;
  font-size: 10px;
  font-weight: 700;
}
.arrosa-invoice .seal-section {
  margin-top: 18px;
  border-top: 2px solid #333;
  padding-top: 10px;
}
.arrosa-invoice .seal-title {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.arrosa-invoice .seal-row {
  margin: 4px 0;
  font-size: 9px;
  word-break: break-all;
}
.arrosa-invoice .seal-text {
  font-family: monospace;
  font-size: 8px;
  line-height: 1.3;
  background: #f8f8f8;
  padding: 4px 6px;
  border: 1px solid #ddd;
  max-height: 60px;
  overflow: hidden;
}
.arrosa-invoice .qr-cadena {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}
.arrosa-invoice .qr-cadena .qr-cell {
  width: 160px;
  vertical-align: middle;
  text-align: center;
}
.arrosa-invoice .qr-cadena .cadena-cell {
  vertical-align: middle;
  padding-left: 14px;
}
.arrosa-invoice .cadena-text {
  font-family: monospace;
  font-size: 8px;
  line-height: 1.3;
  background: #f8f8f8;
  padding: 4px 6px;
  border: 1px solid #ddd;
  word-break: break-all;
}
.arrosa-invoice .cert-meta {
  margin-top: 6px;
  font-size: 9px;
}
.arrosa-invoice .cert-meta > div {
  margin: 1px 0;
}
""".strip()


def upsert_arrosa_quotation_print_format():
    name = "cotizacion"
    existing_name = frappe.db.exists("Print Format", name)

    values = {
        "doc_type": "Quotation",
        "print_format_type": "Jinja",
        "custom_format": 1,
        "raw_printing": 0,
        "disabled": 0,
        "html": ARROSA_QUOTATION_HTML,
        "css": ARROSA_QUOTATION_CSS,
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


def upsert_arrosa_sales_order_print_format():
    name = "orden_venta_arrosa"
    existing_name = frappe.db.exists("Print Format", name)

    values = {
        "doc_type": "Sales Order",
        "print_format_type": "Jinja",
        "custom_format": 1,
        "raw_printing": 0,
        "disabled": 0,
        "html": ARROSA_SALES_ORDER_HTML,
        "css": ARROSA_SALES_ORDER_CSS,
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


def upsert_arrosa_sales_invoice_print_format():
    name = "factura_venta_arrosa"
    existing_name = frappe.db.exists("Print Format", name)

    values = {
        "doc_type": "Sales Invoice",
        "print_format_type": "Jinja",
        "custom_format": 1,
        "raw_printing": 0,
        "disabled": 0,
        "html": ARROSA_SALES_INVOICE_HTML,
        "css": ARROSA_SALES_INVOICE_CSS,
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
