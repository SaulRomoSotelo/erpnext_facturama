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

  <div class="title">COTIZACION {{ (doc.customer_hospital or "").upper() }}</div>

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

ARROSA_SALES_INVOICE_HTML = """
{% set company = frappe.get_doc("Company", doc.company) if doc.company else None %}
{% set logo_url = frappe.utils.get_url(company.company_logo) if company and company.company_logo else "" %}
{% set customer = frappe.get_doc("Customer", doc.customer) if doc.customer else None %}
{% set invoice_uuid = doc.mx_uuid or "" %}
<div class="arrosa-invoice">
  <div class="inv-header">
    <div class="logo-box">
      {% if logo_url %}
      <img src="{{ logo_url }}" class="logo" alt="Arrosa Medical" />
      {% else %}
      <div class="logo-fallback">ARROSA MEDICAL</div>
      {% endif %}
    </div>
    <div class="title-box">ARROSA MEDICAL</div>
  </div>

  <div class="meta-grid">
    <div>
      <div><span class="k">RFC emisor:</span> {{ (company.tax_id if company else "") or "" }}</div>
      <div><span class="k">Nombre emisor:</span> {{ (company.company_name if company else doc.company) or "" }}</div>
      <div><span class="k">Folio:</span> {{ doc.name }}</div>
      <div><span class="k">RFC receptor:</span> {{ (customer.tax_id if customer else "") or "" }}</div>
      <div><span class="k">Nombre receptor:</span> {{ doc.customer_name or doc.customer or "" }}</div>
      <div><span class="k">Codigo postal receptor:</span> {{ doc.customer_address or "" }}</div>
      <div><span class="k">Uso CFDI:</span> {{ doc.mx_cfdi_use or "" }}</div>
    </div>
    <div>
      <div><span class="k">UUID fiscal:</span> {{ invoice_uuid }}</div>
      <div><span class="k">Serie:</span> {{ doc.naming_series or "" }}</div>
      <div><span class="k">Codigo postal, fecha y hora emision:</span> {{ frappe.utils.format_datetime(doc.posting_date ~ " " ~ (doc.posting_time or "00:00:00")) }}</div>
      <div><span class="k">Efecto de comprobante:</span> Ingreso</div>
      <div><span class="k">Regimen fiscal:</span> {{ (company.mx_tax_regime if company and company.mx_tax_regime else (company.sat_tax_regime if company else "")) or "" }}</div>
      <div><span class="k">Exportacion:</span> No aplica</div>
    </div>
  </div>

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

  {% if invoice_uuid %}
  <div class="seal-block">
    <div><span class="k">UUID:</span> {{ invoice_uuid }}</div>
    <div><span class="k">Estado CFDI:</span> {{ doc.mx_cfdi_status or "" }}</div>
  </div>
  {% endif %}

  <div class="footer-note">Este documento es una representacion impresa de un CFDI.</div>
</div>
""".strip()


ARROSA_SALES_INVOICE_CSS = """
.arrosa-invoice {
  font-family: "Helvetica Neue", Arial, sans-serif;
  color: #2a2a2a;
  font-size: 11px;
}
.arrosa-invoice .inv-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-items: center;
  margin-bottom: 10px;
}
.arrosa-invoice .logo {
  max-width: 120px;
  max-height: 90px;
  object-fit: contain;
}
.arrosa-invoice .title-box {
  font-size: 33px;
  font-weight: 700;
  text-align: center;
  letter-spacing: 0.4px;
}
.arrosa-invoice .logo-fallback {
  font-size: 18px;
  font-weight: 700;
}
.arrosa-invoice .meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 18px;
  margin-bottom: 10px;
}
.arrosa-invoice .meta-grid > div > div {
  margin: 2px 0;
}
.arrosa-invoice .k {
  font-weight: 700;
}
.arrosa-invoice .section-title {
  font-size: 17px;
  font-weight: 700;
  margin: 8px 0;
}
.arrosa-invoice .items {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}
.arrosa-invoice .items th,
.arrosa-invoice .items td {
  border: 1px solid #8d8d8d;
  padding: 4px 5px;
  vertical-align: top;
  font-size: 10px;
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
