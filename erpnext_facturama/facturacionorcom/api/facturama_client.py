import frappe
import requests
import base64
import binascii


def _response_error_message(response):
    if response is None:
        return ""

    try:
        payload = response.json()
    except ValueError:
        return (response.text or "")[:500]

    if isinstance(payload, dict):
        details = payload.get("Errors") or payload.get("errors") or payload.get("ModelState")
        if isinstance(details, dict):
            messages = [
                str(message)
                for value in details.values()
                for message in (value if isinstance(value, list) else [value])
                if message
            ]
            if messages:
                return " ".join(messages)
        if isinstance(details, list):
            messages = [str(message) for message in details if message]
            if messages:
                return " ".join(messages)
        return (
            payload.get("Message")
            or payload.get("message")
            or payload.get("Detail")
            or payload.get("detail")
            or response.text[:500]
        )

    return str(payload)[:500]


def extract_cfdi_id(response):
    if not isinstance(response, dict):
        return None

    for key in ("Id", "id", "cfdiId", "CfdiId", "uuid", "UUID"):
        value = response.get(key)
        if value:
            return value

    data = response.get("Data")
    if isinstance(data, dict):
        for key in ("Id", "id", "cfdiId", "CfdiId", "uuid", "UUID"):
            value = data.get(key)
            if value:
                return value

    return None


def extract_uuid(response):
    """Extract the fiscal folio (UUID) from a Facturama CFDI detail response."""
    if not isinstance(response, dict):
        return ""

    for key in ("Uuid", "UUID", "uuid"):
        value = response.get(key)
        if value:
            return value

    complement = response.get("Complement") or {}
    tax_stamp = complement.get("TaxStamp") or {}
    return tax_stamp.get("Uuid", "") or tax_stamp.get("UUID", "") or ""


def _extract_xml_text(payload):
    if isinstance(payload, str):
        candidate = payload.strip()
        if candidate.startswith("<"):
            return candidate
        try:
            decoded = base64.b64decode(candidate, validate=True).decode("utf-8", errors="replace")
            if decoded.strip().startswith("<"):
                return decoded
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return None
        return None

    if not isinstance(payload, dict):
        return None

    for key in ("Xml", "xml", "Content", "content", "Cfdi", "cfdi"):
        if payload.get(key):
            xml = _extract_xml_text(payload.get(key))
            if xml:
                return xml

    data = payload.get("Data")
    if isinstance(data, dict):
        return _extract_xml_text(data)

    return None


class FacturamaClient:
    def __init__(self, user=None, password=None, api_url=None, sandbox=False, timeout=30):
        self.user = user
        self.password = password
        self.api_url = api_url or ""
        self.sandbox = sandbox
        self.timeout = timeout

    def get_config(self):
        return {
            "user": self.user,
            "password": self.password,
            "url": self.api_url,
            "sandbox": self.sandbox,
            "timeout": self.timeout,
        }

    def test_connection(self):
        if not self.user or not self.password or not self.api_url:
            raise ValueError("Faltan credenciales o URL de Facturama")

        try:
            response = requests.get(
                self.api_url.rstrip("/") + "/cfdi",
                auth=(self.user, self.password),
                params={"type": "issued"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return {
                "ok": True,
                "status_code": response.status_code,
            }
        except requests.RequestException as exc:
            response = getattr(exc, "response", None)
            detail = _response_error_message(response)

            return {
                "ok": False,
                "status_code": response.status_code if response is not None else None,
                "error": detail or str(exc),
            }

    def request(self, method, path, **kwargs):
        if not self.api_url:
            raise ValueError("La URL de Facturama no está configurada")

        url = self.api_url.rstrip("/") + "/" + path.lstrip("/")
        headers = kwargs.pop("headers", {})
        headers.setdefault("Content-Type", "application/json")

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                auth=(self.user, self.password),
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            response = getattr(exc, "response", None)
            detail = _response_error_message(response)
            status_code = response.status_code if response is not None else None
            raise frappe.ValidationError(
                detail or f"Facturama respondió con error al llamar {path}"
            ) from exc

        return response.json() if response.content else {}

    def upload_csd(self, rfc, certificate, private_key, private_key_password):
        """Register or update a multi-emisor CSD using base64 values."""
        return self.request(
            "POST",
            "/api-lite/csds",
            json={
                "Rfc": rfc,
                "Certificate": certificate,
                "PrivateKey": private_key,
                "PrivateKeyPassword": private_key_password,
            },
        )

    def create_multiemisor_cfdi(self, payload):
        """Create a CFDI through the Facturama multi-emisor endpoint."""
        return self.request("POST", "/api-lite/3/cfdis", json=payload)

    def get_cfdi_detail(self, cfdi_id):
        """Get the detail of an issued CFDI to read its UUID / serie / folio."""
        return self.request("GET", "/api-lite/cfdis/" + cfdi_id)

    def build_payment_complement_payload(self, payment_entry, settings=None):
        """Build a Facturama 4.0 payment complement (CfdiType P) payload.

        The payment complement references the CFDI UUIDs of the Sales Invoices
        that were paid through the Payment Entry (references child table).
        """
        if settings is None:
            settings = {}

        if not payment_entry.references:
            raise frappe.ValidationError(
                "El Payment Entry no tiene documentos de referencia para emitir el complemento de pago."
            )

        paid_amount = float(getattr(payment_entry, "paid_amount", 0) or 0)
        if paid_amount <= 0:
            raise frappe.ValidationError("El monto pagado debe ser mayor a 0.")

        customer = frappe.get_doc("Customer", payment_entry.party)
        customer_zip = ""
        if getattr(payment_entry, "party_address", None):
            customer_zip = frappe.db.get_value(
                "Address", payment_entry.party_address, "pincode"
            ) or ""
        if not customer_zip:
            customer_zip = frappe.db.get_value(
                "Address",
                {"link_doctype": "Customer", "link_name": payment_entry.party},
                "pincode",
            ) or ""

        customer_tax_regime = (
            getattr(customer, "mx_tax_regime", None)
            or getattr(customer, "sat_tax_regime", None)
            or ""
        )
        customer_rfc = getattr(customer, "tax_id", None) or ""
        customer_name = getattr(customer, "customer_name", None) or ""

        if not customer_rfc:
            raise frappe.ValidationError("El cliente no tiene RFC (tax_id).")
        if not customer_tax_regime:
            raise frappe.ValidationError(
                "El cliente no tiene régimen fiscal SAT (mx_tax_regime)."
            )

        related_documents = []
        total_amount = 0.0
        for reference in payment_entry.references:
            if getattr(reference, "reference_doctype", None) != "Sales Invoice":
                continue
            if not getattr(reference, "reference_name", None):
                continue

            invoice = frappe.get_doc("Sales Invoice", reference.reference_name)
            if getattr(invoice, "docstatus", 0) != 1:
                raise frappe.ValidationError(
                    f"La factura {invoice.name} no está contabilizada (docstatus != 1)."
                )

            cfdi_id = getattr(invoice, "facturama_cfdi_id", None) or getattr(
                invoice, "cfdi_id", None
            )
            if not cfdi_id:
                raise frappe.ValidationError(
                    f"La factura {invoice.name} no tiene un CFDI timbrado asociado."
                )

            uuid = ""
            serie = ""
            folio = ""
            try:
                detail = self.get_cfdi_detail(cfdi_id)
                complement = detail.get("Complement", {}) or {}
                tax_stamp = complement.get("TaxStamp", {}) or {}
                uuid = (
                    tax_stamp.get("Uuid", "")
                    or tax_stamp.get("UUID", "")
                    or detail.get("Uuid", "")
                    or detail.get("UUID", "")
                )
                serie = detail.get("Serie", "") or ""
                folio = detail.get("Folio", "") or ""
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    "Facturama get_cfdi_detail for payment complement",
                )

            if not uuid:
                raise frappe.ValidationError(
                    f"No se pudo obtener el UUID del CFDI de la factura {invoice.name}."
                )

            invoice_grand_total = float(getattr(invoice, "grand_total", 0) or 0)
            amount_paid = float(getattr(reference, "allocated_amount", 0) or 0)
            if amount_paid <= 0:
                raise frappe.ValidationError(
                    f"El monto asignado de la factura {invoice.name} debe ser mayor a 0."
                )
            total_amount += amount_paid

            prior = self._get_prior_paid_for_invoice(
                invoice.name, exclude_payment=payment_entry.name
            )
            previous_balance = round(invoice_grand_total - prior, 2)
            remaining = round(previous_balance - amount_paid, 2)
            if previous_balance < 0:
                previous_balance = round(invoice_grand_total, 2)
                remaining = round(invoice_grand_total - amount_paid, 2)
            partiality = self._get_partiality_number(
                invoice.name, exclude_payment=payment_entry.name
            )

            taxes = self._get_prorated_taxes(invoice, amount_paid, invoice_grand_total)

            related = {
                "TaxObject": "02" if taxes else "01",
                "Uuid": uuid,
                "Serie": serie,
                "Folio": folio or invoice.name,
                "PaymentMethod": self._get_invoice_payment_method(invoice),
                "PartialityNumber": partiality,
                "PreviousBalanceAmount": previous_balance,
                "AmountPaid": amount_paid,
                "ImpSaldoInsoluto": remaining,
            }

            currency = getattr(invoice, "currency", None) or "MXN"
            if currency and currency != "MXN":
                related["Currency"] = currency
                related["EquivalenceDocRel"] = 1

            if taxes:
                related["Taxes"] = taxes

            related_documents.append(related)

        if not related_documents:
            raise frappe.ValidationError(
                "El Payment Entry no referencia ninguna factura de venta válida."
            )

        payment_date = getattr(payment_entry, "posting_date", None)
        if payment_date:
            payment_date = payment_date.isoformat()

        return {
            "CfdiType": "P",
            "NameId": "14",
            "Folio": getattr(payment_entry, "name", "") or "1",
            "ExpeditionPlace": settings.get("zip_code_company") or "",
            "Receiver": {
                "Rfc": customer_rfc,
                "CfdiUse": "CP01",
                "Name": customer_name,
                "FiscalRegime": customer_tax_regime,
                "TaxZipCode": customer_zip or "",
            },
            "Complemento": {
                "Payments": [
                    {
                        "Date": payment_date or frappe.utils.today(),
                        "PaymentForm": settings.get("default_payment_form") or "03",
                        "Amount": paid_amount,
                        "Currency": "MXN",
                        "RelatedDocuments": related_documents,
                    }
                ]
            },
        }

    def _get_invoice_payment_method(self, invoice):
        """Return PPD or PUE from the invoice, defaulting to PPD for complements."""
        value = getattr(invoice, "payment_method", None)
        if value in ("PPD", "PUE"):
            return value
        return "PPD"

    def _get_prior_paid_for_invoice(self, invoice_name, exclude_payment=None):
        """Sum of amounts already covered by prior issued payment complements."""
        query = """
            SELECT COALESCE(SUM(ref.allocated_amount), 0)
            FROM `tabPayment Entry Reference` ref
            INNER JOIN `tabPayment Entry` pe ON pe.name = ref.parent
            WHERE ref.reference_doctype = 'Sales Invoice'
              AND ref.reference_name = %s
              AND pe.docstatus = 1
              AND COALESCE(pe.facturama_complement_cfdi_id, '') <> ''
        """
        values = [invoice_name]
        if exclude_payment:
            query += " AND pe.name != %s"
            values.append(exclude_payment)
        return float(frappe.db.sql(query, values)[0][0] or 0)

    def _get_partiality_number(self, invoice_name, exclude_payment=None):
        """Number of the current partial payment (1 for the first one).

        Counts only submitted Payment Entries that already issued a complement.
        """
        query = """
            SELECT COUNT(*)
            FROM `tabPayment Entry Reference` ref
            INNER JOIN `tabPayment Entry` pe ON pe.name = ref.parent
            WHERE ref.reference_doctype = 'Sales Invoice'
              AND ref.reference_name = %s
              AND pe.docstatus = 1
              AND COALESCE(pe.facturama_complement_cfdi_id, '') <> ''
        """
        values = [invoice_name]
        if exclude_payment:
            query += " AND pe.name != %s"
            values.append(exclude_payment)
        count = frappe.db.sql(query, values)[0][0]
        return int(count or 0) + 1

    def _get_prorated_taxes(self, invoice, amount_paid, invoice_grand_total):
        """Allocate invoice taxes proportionally to the amount paid."""
        if invoice_grand_total <= 0 or amount_paid <= 0:
            return []

        taxes = []
        ratio = amount_paid / invoice_grand_total
        for tax in getattr(invoice, "taxes", []) or []:
            tax_amount = float(
                getattr(tax, "tax_amount_after_discount_amount", 0) or 0
            ) or float(getattr(tax, "tax_amount", 0) or 0)
            if not tax_amount:
                continue

            allocated = round(tax_amount * ratio, 2)
            if abs(allocated) < 0.01:
                continue

            rate = float(getattr(tax, "rate", 0) or 0) / 100
            base = round(allocated / rate, 2) if rate else round(amount_paid, 2)

            account_name = (getattr(tax, "account_head", "") or "").lower()
            description = (getattr(tax, "description", "") or "").lower()
            is_retention = allocated < 0 or "retenci" in account_name or "retenci" in description
            name = (
                "IVA"
                if "iva" in account_name or "iva" in description
                else getattr(tax, "description", "") or "Impuesto"
            )

            taxes.append({
                "Name": name,
                "Rate": rate,
                "Total": abs(allocated),
                "Base": base,
                "IsRetention": is_retention,
            })

        return taxes

    def list_multiemisor_cfdis(self, **filters):
        """List multi-emisor CFDIs without exposing them in the Facturama UI."""
        params = {"type": "issuedLite", **filters}
        return self.request("GET", "/cfdi", params=params)

    def cancel_multiemisor_cfdi(self, cfdi_id, motive="02", uuid_replacement=None):
        """Request cancellation of a multi-emisor CFDI."""
        params = {"motive": motive}
        if uuid_replacement:
            params["uuidReplacement"] = uuid_replacement
        return self.request("DELETE", f"/api-lite/cfdis/{cfdi_id}", params=params)

    def download_multiemisor_cfdi_xml(self, cfdi_id):
        """Download XML for a CFDI id, accepting Facturama XML or JSON-wrapped responses."""
        if not self.api_url:
            raise ValueError("La URL de Facturama no está configurada")

        candidates = [
            f"/cfdi/xml/issuedLite/{cfdi_id}",
            f"/api-lite/4/cfdis/xml/{cfdi_id}",
            f"/api-lite/cfdis/{cfdi_id}/xml",
        ]

        last_error = ""
        for path in candidates:
            url = self.api_url.rstrip("/") + path
            try:
                response = requests.get(
                    url,
                    auth=(self.user, self.password),
                    headers={"Accept": "application/xml, text/xml, application/json"},
                    timeout=self.timeout,
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                detail = _response_error_message(getattr(exc, "response", None))
                last_error = detail or str(exc)
                continue

            content_type = (response.headers.get("Content-Type") or "").lower()
            body_text = response.text or ""
            if "xml" in content_type and body_text.strip().startswith("<"):
                return body_text

            try:
                payload = response.json() if response.content else {}
            except ValueError:
                payload = body_text

            if isinstance(payload, dict):
                for key in ("Content", "content", "Xml", "xml"):
                    if payload.get(key):
                        xml = _extract_xml_text(payload[key])
                        if xml:
                            return xml

            xml = _extract_xml_text(payload)
            if xml:
                return xml

            last_error = "Facturama respondió, pero no devolvió un XML legible."

        raise frappe.ValidationError(last_error or "No fue posible descargar el XML desde Facturama.")

    def build_multiemisor_payload(self, invoice, settings=None):
        """Build the Facturama 4.0 multi-emisor envelope from an ERPNext invoice."""
        payload = self.build_invoice_payload(invoice, settings)
        issuer = payload.pop("issuer")
        receiver = payload.pop("receiver")
        items = payload.pop("items")

        return {
            "CfdiType": "I",
            "Folio": getattr(invoice, "name", "") or "1",
            "PaymentForm": payload.pop("payment_form"),
            "PaymentMethod": payload.pop("payment_method"),
            "Currency": payload.pop("currency"),
            "ExpeditionPlace": issuer.get("address", {}).get("zip_code", ""),
            "Issuer": {
                "Rfc": issuer.get("rfc", ""),
                "Name": issuer.get("name", ""),
                "FiscalRegime": issuer.get("tax_regime", ""),
            },
            "Receiver": {
                "Rfc": receiver.get("rfc", ""),
                "Name": receiver.get("name", ""),
                "CfdiUse": receiver.get("cfdi_use", "G03"),
                "FiscalRegime": receiver.get("tax_regime", ""),
                "TaxZipCode": receiver.get("address", {}).get("zip_code", ""),
            },
            "Items": [
                {
                    "Description": item.get("description", ""),
                    "Quantity": item.get("quantity", 0),
                    "UnitPrice": item.get("unit_price", 0),
                    "Subtotal": item.get("amount", 0),
                    "ProductCode": item.get("product_code", "01010101"),
                    "Unit": item.get("unit", "Pieza"),
                    "UnitCode": item.get("unit_code", "E48"),
                    "TaxObject": "02" if item.get("taxes") else "01",
                    "Taxes": [
                        {
                            "Name": tax.get("name", "IVA"),
                            "Rate": tax.get("rate", 0),
                            "Total": tax.get("amount", 0),
                            "Base": item.get("amount", 0),
                            "IsRetention": False,
                        }
                        for tax in item.get("taxes", [])
                        if tax.get("amount", 0)
                    ],
                    "Total": item.get("amount", 0) + sum(
                        tax.get("amount", 0) for tax in item.get("taxes", [])
                    ),
                }
                for item in items
            ],
        }

    def build_invoice_payload(self, invoice, settings=None):
        """Build a base payload from a Sales Invoice and Facturama settings."""
        if settings is None:
            settings = {}

        company_name = getattr(invoice, "company", None)
        customer_name = getattr(invoice, "customer", None)
        company = frappe.get_doc("Company", company_name) if company_name else None
        customer = frappe.get_doc("Customer", customer_name) if customer_name else None

        address_name = getattr(invoice, "customer_address", None)
        customer_zip = ""
        if address_name:
            customer_zip = frappe.db.get_value("Address", address_name, "pincode") or ""

        invoice_tax_rows = [
            tax
            for tax in getattr(invoice, "taxes", []) or []
            if getattr(tax, "tax_amount_after_discount_amount", 0) or getattr(tax, "tax_amount", 0)
        ]
        net_total = getattr(invoice, "net_total", 0) or 0
        items = []
        invoice_items = getattr(invoice, "items", []) or []
        for index, item in enumerate(invoice_items):
            item_doc = frappe.get_cached_doc("Item", item.item_code) if item.item_code else None
            uom_name = getattr(item, "uom", None) or getattr(item, "stock_uom", None)
            product_code = (
                getattr(item, "mx_product_service_key", None)
                or getattr(item_doc, "mx_product_service_key", None)
                or getattr(item_doc, "sat_product_key", None)
                or getattr(item_doc, "sat_item_key", None)
                or getattr(item_doc, "sat_clave_producto", None)
                or "01010101"
            )
            unit_code = (
                frappe.db.get_value("UOM", uom_name, "mx_uom_key") if uom_name else None
            ) or getattr(item_doc, "sat_uom", None) or getattr(item_doc, "sat_unit_code", None) or getattr(item_doc, "sat_clave_unidad", None) or "E48"
            item_amount = getattr(item, "amount", 0) or 0
            item_taxes = []
            for tax in invoice_tax_rows:
                total_tax_amount = getattr(tax, "tax_amount_after_discount_amount", 0) or getattr(tax, "tax_amount", 0)
                if index == len(invoice_items) - 1:
                    allocated_amount = total_tax_amount - sum(
                        round(total_tax_amount * ((previous.amount or 0) / net_total), 2)
                        for previous in invoice_items[:index]
                    ) if net_total else 0
                else:
                    allocated_amount = round(total_tax_amount * (item_amount / net_total), 2) if net_total else 0

                if not allocated_amount:
                    continue

                account_name = (getattr(tax, "account_head", "") or "").lower()
                description = (getattr(tax, "description", "") or "").lower()
                item_taxes.append({
                    "name": "IVA" if "iva" in account_name or "iva" in description else getattr(tax, "description", "") or "Impuesto",
                    "rate": (getattr(tax, "rate", 0) or 0) / 100,
                    "amount": allocated_amount,
                    "is_retention": allocated_amount < 0 or "retenci" in account_name or "retenci" in description,
                })

            items.append({
                "description": getattr(item, "item_name", "") or getattr(item, "description", ""),
                "quantity": getattr(item, "qty", 0) or 0,
                "unit_price": getattr(item, "rate", 0) or 0,
                "amount": item_amount,
                "product_code": product_code,
                "unit": uom_name or "Pieza",
                "unit_code": unit_code,
                "taxes": item_taxes,
            })

        return {
            "issuer": {
                "rfc": getattr(company, "tax_id", "") if company else "",
                "name": settings.get("issuer_name") or (
                    getattr(company, "company_name", "") or ""
                ).upper() if company else "",
                "tax_regime": (
                    getattr(company, "mx_tax_regime", None)
                    or getattr(company, "sat_tax_regime", "")
                ) if company else "",
                "address": {
                    "street": getattr(company, "address_line1", "") if company else "",
                    "zip_code": settings.get("zip_code_company") or "",
                },
            },
            "receiver": {
                "rfc": getattr(customer, "tax_id", "") if customer else "",
                "name": getattr(customer, "customer_name", "") if customer else "",
                "cfdi_use": getattr(customer, "mx_cfdi_use", None) or settings.get("default_cfdi_use") or "G03",
                "tax_regime": getattr(customer, "mx_tax_regime", None) or getattr(customer, "sat_tax_regime", None) or "",
                "address": {
                    "street": getattr(customer, "address_line1", "") if customer else "",
                    "zip_code": customer_zip,
                },
            },
            "currency": settings.get("default_currency") or "MXN",
            "payment_form": settings.get("default_payment_form") or "01",
            "payment_method": settings.get("default_payment_method") or "PUE",
            "series": settings.get("series") or "",
            "items": items,
            "totals": {
                "subtotal": getattr(invoice, "net_total", 0) or 0,
                "total": getattr(invoice, "grand_total", 0) or 0,
                "tax": getattr(invoice, "total_taxes_and_charges", 0) or 0,
            },
            "metadata": {
                "posting_date": getattr(invoice, "posting_date", None),
                "due_date": getattr(invoice, "due_date", None),
                "naming_series": getattr(invoice, "naming_series", None),
                "save_xml": bool(settings.get("save_xml", 0)),
                "save_pdf": bool(settings.get("save_pdf", 0)),
            },
        }
