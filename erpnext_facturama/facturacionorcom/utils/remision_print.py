REMISION_HTML = """
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
    <div><span class="k">Hospital:</span> {{ doc.hospital or "" }}</div>
    <div><span class="k">Cirujano:</span> {{ doc.cirujano or "" }}</div>
    <div><span class="k">Hora:</span> {{ doc.hora or "" }}</div>
    <div><span class="k">Tecnico:</span> {{ doc.tecnico or "" }}</div>
    <div><span class="k">Paciente:</span> {{ doc.paciente or "" }}</div>
    <div><span class="k">Edad:</span> {{ doc.edad or "" }}</div>
    <div><span class="k">Procedimiento:</span> {{ doc.procedimiento or "" }}</div>
    <div><span class="k">Cliente:</span> {{ doc.customer_name or doc.customer or "" }}</div>
    <div><span class="k">Almacen:</span> {{ doc.warehouse or "" }}</div>
  </div>

  <div class="title">REMISION</div>

  {% set ns = namespace(current_group="", total_qty=0) %}
  {% for row in doc.items %}
    {% if row.item_group != ns.current_group %}
      {% if ns.current_group != "" %}
      </tbody>
    </table>
      {% endif %}
      {% set ns.current_group = row.item_group %}
      <div class="group-title">{{ row.item_group or "" }}</div>
      <table class="items">
        <thead>
          <tr>
            <th class="num">Cantidad</th>
            <th>Codigo</th>
            <th>Descripcion</th>
            <th class="num">Existencia</th>
          </tr>
        </thead>
        <tbody>
    {% endif %}
      <tr>
        <td class="num">{{ row.qty or 0 }}</td>
        <td class="ref">{{ row.item_code or "" }}</td>
        <td>{{ row.item_name or "" }}</td>
        <td class="num">{{ row.stock_qty or 0 }}</td>
      </tr>
      {% set ns.total_qty = ns.total_qty + (row.qty or 0) %}
  {% endfor %}
  {% if doc.items %}
        </tbody>
      </table>
  {% endif %}

  <table class="totals">
    <tr>
      <td>CANTIDAD TOTAL</td>
      <td class="num">{{ ns.total_qty }}</td>
    </tr>
  </table>

  {% if doc.notes %}
  <div class="notes-section">
    <span class="k">Notas:</span>
    <div class="notes-text">{{ doc.notes }}</div>
  </div>
  {% endif %}
</div>
""".strip()

REMISION_CSS = """
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
  grid-template-columns: 1fr 1fr 1fr;
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
.arrosa-quote .group-title {
  font-weight: 700;
  font-size: 13px;
  background: #f0f0f0;
  padding: 5px 8px;
  margin-top: 12px;
  margin-bottom: 0;
  border: 1px solid #ccc;
}
.arrosa-quote .items {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 0;
}
.arrosa-quote .items th,
.arrosa-quote .items td {
  border-bottom: 1px solid #e4e4e4;
  padding: 5px 6px;
  vertical-align: top;
}
.arrosa-quote .items thead th {
  border-top: 1px solid #999;
  border-bottom: 1px solid #999;
  text-transform: uppercase;
  font-size: 10px;
  background: #f8f8f8;
}
.arrosa-quote .items .ref {
  font-family: monospace;
  font-size: 11px;
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
.arrosa-quote .notes-section {
  margin-top: 18px;
  border-top: 1px solid #ddd;
  padding-top: 8px;
}
.arrosa-quote .notes-text {
  margin-top: 4px;
  font-size: 11px;
}
""".strip()
