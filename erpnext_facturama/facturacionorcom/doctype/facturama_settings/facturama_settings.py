# Copyright (c) 2026, Saul Romo and contributors
# For license information, please see license.txt

import frappe
import base64
import re
import xml.etree.ElementTree as ET
from frappe.model.document import Document

import erpnext_facturama.facturacionorcom.api.facturama_client


FACTURAMA_API_URLS = {
	False: "https://api.facturama.mx",
	True: "https://apisandbox.facturama.mx",
}


class FacturamaSettings(Document):
	def before_validate(self):
		# Settings is used only for API authentication and connectivity.
		return

	def before_save(self):
		frappe.logger("erpnext_facturama").info(
			"Guardando Facturama Settings: user=%s sandbox=%s has_password=%s",
			bool(self.api_user),
			bool(self.mode_sandbox),
			bool(self.get("api_password")),
		)

	def on_update(self):
		clear_facturama_settings_cache()
		frappe.logger("erpnext_facturama").info("Facturama Settings guardado correctamente")


_FACTURAMA_SETTINGS_CACHE = None


def get_facturama_settings():
	global _FACTURAMA_SETTINGS_CACHE

	if _FACTURAMA_SETTINGS_CACHE is not None:
		return _FACTURAMA_SETTINGS_CACHE

	try:
		settings = frappe.get_single("Facturama Settings")
		sandbox = bool(getattr(settings, "mode_sandbox", 0))
		_FACTURAMA_SETTINGS_CACHE = {
			"user": settings.api_user or "",
			"sandbox": sandbox,
			"url": FACTURAMA_API_URLS[sandbox],
		}
	except Exception:
		_FACTURAMA_SETTINGS_CACHE = {
			"user": "",
			"sandbox": False,
			"url": FACTURAMA_API_URLS[False],
		}

	return _FACTURAMA_SETTINGS_CACHE


def clear_facturama_settings_cache():
	global _FACTURAMA_SETTINGS_CACHE
	_FACTURAMA_SETTINGS_CACHE = None


def get_facturama_base_url(mode_sandbox):
	return FACTURAMA_API_URLS[bool(mode_sandbox)]


def _get_settings_doc():
	return frappe.get_single("Facturama Settings")


def get_facturama_auth():
	settings = _get_settings_doc()
	try:
		password = settings.get_password("api_password")
	except Exception:
		password = ""

	sandbox = bool(getattr(settings, "mode_sandbox", 0))
	return {
		"user": settings.api_user or "",
		"password": password or "",
		"url": get_facturama_base_url(sandbox),
		"sandbox": sandbox,
		"timeout": settings.timeout or 30,
	}


def get_facturama_client():
	auth = get_facturama_auth()

	if not auth["user"]:
		raise frappe.ValidationError("Falta configurar el usuario API de Facturama.")
	if not auth["password"]:
		raise frappe.ValidationError("Falta guardar la contraseña API de Facturama.")

	return erpnext_facturama.facturacionorcom.api.facturama_client.FacturamaClient(
		user=auth["user"],
		password=auth["password"],
		api_url=auth["url"],
		sandbox=auth["sandbox"],
		timeout=auth["timeout"],
	)


@frappe.whitelist()
def test_facturama_connection():
	"""Test the configured Facturama credentials against the CFDI endpoint."""
	try:
		frappe.logger("erpnext_facturama").info("Iniciando prueba de conexión Facturama")
		client = get_facturama_client()
		auth = get_facturama_auth()
		result = client.test_connection()
		if not result.get("ok") and result.get("status_code") == 401:
			environment = "Sandbox" if auth.get("sandbox") else "Producción"
			result["error"] = (
				f"Facturama rechazó la autenticación para {environment} (401 Unauthorized). "
				"Verifica usuario/contraseña y confirma que esas credenciales correspondan al ambiente seleccionado."
			)
		frappe.logger("erpnext_facturama").info(
			"Respuesta Facturama: ok=%s status=%s",
			result.get("ok"),
			result.get("status_code"),
		)
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Facturama connection test")
		return {"ok": False, "error": str(exc)}

	result["connection_status"] = "Conectado" if result.get("ok") else "Error"
	result["last_connection"] = frappe.utils.now_datetime()
	return result


def get_facturama_mapping_defaults():
	"""Return the default values that will be used when mapping ERPNext data to Facturama."""
	settings = get_facturama_settings()
	return {
		"user": settings.get("user", ""),
		"url": settings.get("url", ""),
		"sandbox": settings.get("sandbox", False),
		"default_currency": "MXN",
		"default_payment_form": "01",
		"default_payment_method": "PUE",
		"default_cfdi_use": "G03",
		"series": None,
		"save_xml": 0,
		"save_pdf": 0,
	}


def _get_address_pincode(address_name):
	if not address_name:
		return ""

	return frappe.db.get_value("Address", address_name, "pincode") or ""


def _get_primary_company_pincode(company_name):
	if not company_name:
		return ""

	emisor_pincode = frappe.db.get_value(
		"Facturama Emisor",
		{"company": company_name, "active": 1},
		"expedition_place",
	)
	if emisor_pincode:
		return emisor_pincode.strip()

	links = frappe.get_all(
		"Dynamic Link",
		filters={
			"parenttype": "Address",
			"link_doctype": "Company",
			"link_name": company_name,
		},
		pluck="parent",
	)
	if not links:
		return ""

	addresses = frappe.get_all(
		"Address",
		filters={"name": ["in", links], "disabled": 0},
		fields=["name", "pincode", "address_type", "is_primary_address"],
	)
	addresses.sort(
		key=lambda address: (
			address.is_primary_address != 1,
			address.address_type != "Billing",
		)
	)

	return addresses[0].pincode.strip() if addresses and addresses[0].pincode else ""


def _get_issuer_name(company_name, sandbox=False):
	name = frappe.db.get_value("Company", company_name, "company_name") or ""
	name = name.strip().upper()
	if sandbox:
		return re.sub(r"\s+(?:S\.?\s*A\.?\s+DE\s+C\.?\s*V\.?|SA\s+DE\s+CV)$", "", name)
	return name


def _ensure_sales_invoice_facturama_field():
	if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "facturama_cfdi_id"}):
		return

	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Sales Invoice",
		"fieldname": "facturama_cfdi_id",
		"label": "Facturama CFDI ID",
		"fieldtype": "Data",
		"insert_after": "customer_name",
		"hidden": 1,
		"translatable": 0,
	}).insert(ignore_permissions=True)


FOLIO_SERIES_NAME = "SALES-INVOICE-FOLIO"
FOLIO_START = 861


def _ensure_sales_invoice_folio_field():
	"""Ensure the custom field that stores the Facturama CFDI folio on Sales Invoice."""
	exists = frappe.db.exists(
		"Custom Field", {"dt": "Sales Invoice", "fieldname": "facturama_folio"}
	)
	if exists:
		return

	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Sales Invoice",
		"fieldname": "facturama_folio",
		"label": "Facturama Folio",
		"fieldtype": "Data",
		"insert_after": "facturama_cfdi_id",
		"hidden": 1,
		"translatable": 0,
	}).insert(ignore_permissions=True)


def _initialize_folio_series():
	"""Create the folio counter row if it does not exist yet."""
	if frappe.db.exists("Series", FOLIO_SERIES_NAME):
		return
	frappe.db.sql(
		"INSERT INTO `tabSeries` (name, current) VALUES (%s, %s)",
		(FOLIO_SERIES_NAME, FOLIO_START - 1),
	)
	frappe.db.commit()


def get_next_sales_invoice_folio(commit=True):
	"""Return the next CFDI folio number (atomic increment, no zero padding).

	``commit=False`` is used from the autoname mixin so the counter is saved
	together with the document transaction.
	"""
	_initialize_folio_series()
	next_value = frappe.db.sql(
		"SELECT current FROM `tabSeries` WHERE name = %s FOR UPDATE",
		FOLIO_SERIES_NAME,
	)[0][0]
	frappe.db.sql(
		"UPDATE `tabSeries` SET current = %s WHERE name = %s",
		(next_value + 1, FOLIO_SERIES_NAME),
	)
	if commit:
		frappe.db.commit()
	return int(next_value + 1)


def build_cancel_params(cfdi_id, motive="02", uuid_replacement=None):
	params = {"motive": motive}
	if uuid_replacement:
		params["uuidReplacement"] = uuid_replacement
	return params


@frappe.whitelist()
def stamp_sales_invoice_with_facturama(sales_invoice):
	"""Stamp a Sales Invoice through Facturama and persist the CFDI ID."""
	if not frappe.db.exists("Sales Invoice", sales_invoice):
		return {
			"ok": False,
			"errors": ["Guarda la factura antes de timbrarla."],
			"warnings": [],
		}

	try:
		validation = validate_sales_invoice_for_facturama(sales_invoice)
		if not validation.get("ok"):
			return {
				"ok": False,
				"errors": validation.get("errors", []),
				"warnings": validation.get("warnings", []),
				"message": "La factura no cumple con los requisitos previos para timbrar.",
			}

		invoice = frappe.get_doc("Sales Invoice", sales_invoice)
		_ensure_sales_invoice_facturama_field()
		_ensure_sales_invoice_folio_field()

		if not getattr(invoice, "facturama_folio", None):
			facturama_folio = str(get_next_sales_invoice_folio())
			invoice.db_set("facturama_folio", facturama_folio)
			frappe.db.commit()

		client = get_facturama_client()
		payload = client.build_multiemisor_payload(
			invoice,
			settings={
				"default_currency": "MXN",
				"default_payment_form": "01",
				"default_payment_method": "PUE",
				"default_cfdi_use": "G03",
				"series": None,
				"serie": "A",
				"folio": getattr(invoice, "facturama_folio", None) or None,
				"issuer_name": _get_issuer_name(invoice.company, client.sandbox),
				"zip_code_company": _get_primary_company_pincode(invoice.company),
				"save_xml": 0,
				"save_pdf": 0,
			},
		)
		response = client.create_multiemisor_cfdi(payload)
		cfdi_id = erpnext_facturama.facturacionorcom.api.facturama_client.extract_cfdi_id(response)
		if cfdi_id:
			invoice.db_set("facturama_cfdi_id", cfdi_id)
			try:
				xml_text = client.download_multiemisor_cfdi_xml(cfdi_id)
				invoice.db_set("mx_stamped_xml", xml_text)
				invoice.db_set("mx_uuid", _extract_uuid_from_xml(xml_text))
				invoice.db_set("mx_cfdi_status", "Valido")
			except Exception as exc:
				frappe.log_error(
					frappe.get_traceback(),
					f"Facturama stamping - XML guardado falló para {invoice.name}: {exc}",
				)
			frappe.db.commit()
		return {
			"ok": True,
			"message": "CFDI timbrado correctamente.",
			"response": response,
			"cfdi_id": cfdi_id,
		}
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Facturama stamping")
		return {"ok": False, "error": str(exc)}


def _extract_uuid_from_xml(xml_text):
	"""Extract the fiscal folio (UUID) from a stamped CFDI XML string."""
	if not xml_text:
		return ""
	try:
		root = ET.fromstring(xml_text)
		ns_tfd = "http://www.sat.gob.mx/TimbreFiscalDigital"
		for elem in root.iter("{" + ns_tfd + "}TimbreFiscalDigital"):
			return elem.get("UUID", "")
	except Exception:
		pass
	return ""


@frappe.whitelist()
def cancel_sales_invoice_timbre(sales_invoice, motive="02", uuid_replacement=None):
	"""Request cancellation of a Facturama CFDI for a Sales Invoice."""
	invoice = frappe.get_doc("Sales Invoice", sales_invoice)

	cfdi_id = getattr(invoice, "facturama_cfdi_id", None) or getattr(invoice, "cfdi_id", None)
	if not cfdi_id:
		raise frappe.ValidationError(
			"La factura no tiene un identificador de CFDI/Timbrado asociado."
		)

	client = get_facturama_client()
	result = client.cancel_multiemisor_cfdi(
		cfdi_id,
		motive=motive,
		uuid_replacement=uuid_replacement,
	)

	return {
		"ok": True,
		"result": result,
		"invoice": invoice.name,
		"cfdi_id": cfdi_id,
	}


@frappe.whitelist()
def download_sales_invoice_xml(sales_invoice):
	"""Download XML from Facturama for a stamped Sales Invoice."""
	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	cfdi_id = getattr(invoice, "facturama_cfdi_id", None) or getattr(invoice, "cfdi_id", None)
	if not cfdi_id:
		raise frappe.ValidationError(
			"La factura no tiene un identificador de CFDI/Timbrado asociado."
		)

	client = get_facturama_client()
	xml_text = client.download_multiemisor_cfdi_xml(cfdi_id)
	filename = f"{invoice.name}-{cfdi_id}.xml"

	return {
		"ok": True,
		"filename": filename,
		"cfdi_id": cfdi_id,
		"xml_base64": base64.b64encode(xml_text.encode("utf-8")).decode("ascii"),
	}


@frappe.whitelist()
def validate_sales_invoice_for_facturama(sales_invoice):
	"""Validate required fiscal data before attempting CFDI stamping."""
	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	settings = frappe.get_single("Facturama Settings")
	errors = []
	warnings = []

	if not getattr(settings, "api_user", None):
		errors.append("Falta configurar el usuario API de Facturama.")
	if not settings.get_password("api_password"):
		errors.append("Falta guardar la contraseña API de Facturama.")

	company = frappe.get_doc("Company", invoice.company)
	company_rfc = getattr(company, "tax_id", None)
	company_regime = getattr(company, "mx_tax_regime", None) or getattr(company, "sat_tax_regime", None)
	company_zip = _get_primary_company_pincode(invoice.company)

	if not company_rfc:
		errors.append("La empresa no tiene RFC (tax_id).")
	if not company_regime:
		errors.append("La empresa no tiene régimen fiscal (mx_tax_regime).")
	if not company_zip or not str(company_zip).isdigit() or len(str(company_zip)) != 5:
		errors.append("La empresa no tiene código postal válido de 5 dígitos para expedición.")

	if not invoice.customer:
		errors.append("La factura no tiene cliente.")
		customer = None
	else:
		customer = frappe.get_doc("Customer", invoice.customer)

	if customer:
		customer_rfc = getattr(customer, "tax_id", None)
		if not customer_rfc:
			errors.append("El cliente no tiene RFC (tax_id).")
		customer_regime = getattr(customer, "mx_tax_regime", None) or getattr(customer, "sat_tax_regime", None)
		if not customer_regime:
			errors.append("El cliente no tiene régimen fiscal SAT (mx_tax_regime).")

	customer_zip = _get_address_pincode(invoice.customer_address)
	if not customer_zip or not str(customer_zip).isdigit() or len(str(customer_zip)) != 5:
		errors.append("El cliente no tiene código postal válido de 5 dígitos en su dirección.")

	if not invoice.items:
		errors.append("La factura no tiene partidas.")
	else:
		for idx, row in enumerate(invoice.items, start=1):
			if not row.item_code:
				errors.append(f"Partida {idx}: falta el Item Code.")
			if not row.item_name and not row.description:
				errors.append(f"Partida {idx}: falta descripción del producto.")
			if (row.qty or 0) <= 0:
				errors.append(f"Partida {idx}: la cantidad debe ser mayor a 0.")
			if (row.rate or 0) < 0:
				errors.append(f"Partida {idx}: el precio no puede ser negativo.")

			item_doc = frappe.get_cached_doc("Item", row.item_code) if row.item_code else None
			if item_doc:
				has_sat_product = any(
					bool(getattr(item_doc, field, None))
					for field in (
						"mx_product_service_key",
						"sat_product_key",
						"sat_item_key",
						"sat_clave_producto",
					)
				)
				uom_name = row.uom or row.stock_uom or item_doc.stock_uom
				has_sat_unit = bool(
					uom_name and frappe.db.get_value("UOM", uom_name, "mx_uom_key")
				) or any(
					bool(getattr(item_doc, field, None))
					for field in ("sat_uom", "sat_unit_code", "sat_clave_unidad")
				)

				if not has_sat_product:
					warnings.append(
						f"Partida {idx}: sin clave SAT de producto, se usará 01010101 por defecto."
					)
				if not has_sat_unit:
					warnings.append(
						f"Partida {idx}: sin clave SAT de unidad, se usará E48 por defecto."
					)

	if not invoice.currency:
		errors.append("La factura no tiene moneda.")
	elif invoice.currency != "MXN":
		warnings.append("Moneda distinta de MXN: confirma tipo de cambio y configuración CFDI.")

	return {
		"ok": not errors,
		"errors": errors,
		"warnings": warnings,
		"invoice": invoice.name,
	}


@frappe.whitelist()
def check_cfdi_status(sales_invoice):
	"""Check the current status of a CFDI in Facturama."""
	invoice = frappe.get_doc("Sales Invoice", sales_invoice)
	cfdi_id = getattr(invoice, "facturama_cfdi_id", None) or getattr(invoice, "cfdi_id", None)
	if not cfdi_id:
		return {
			"ok": False,
			"error": "La factura no tiene un identificador de CFDI/Timbrado asociado.",
		}

	client = get_facturama_client()
	try:
		result = client.request("GET", "/api-lite/cfdis/" + cfdi_id)
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Facturama status check")
		return {"ok": False, "error": str(exc)}

	status = result.get("Status", "unknown")
	return {
		"ok": True,
		"cfdi_id": cfdi_id,
		"status": status,
		"uuid": ((result.get("Complement", {}) or {}).get("TaxStamp", {}) or {}).get("Uuid", ""),
		"date": result.get("Date", ""),
		"total": result.get("Total", 0),
		"currency": result.get("Currency", ""),
		"issuer_rfc": (result.get("Issuer", {}) or {}).get("Rfc", ""),
		"receiver_rfc": (result.get("Receiver", {}) or {}).get("Rfc", ""),
		"receiver_name": (result.get("Receiver", {}) or {}).get("Name", ""),
		"full_response": result,
	}


def _ensure_payment_entry_facturama_fields():
	"""Ensure custom fields used to track the payment complement on Payment Entry."""
	fields = [
		{
			"fieldname": "facturama_complement_cfdi_id",
			"label": "Facturama Complemento de Pago CFDI ID",
			"fieldtype": "Data",
			"insert_after": "mode_of_payment",
			"hidden": 1,
			"translatable": 0,
		},
		{
			"fieldname": "facturama_complement_uuid",
			"label": "UUID Complemento de Pago",
			"fieldtype": "Data",
			"insert_after": "facturama_complement_cfdi_id",
			"hidden": 1,
			"translatable": 0,
		},
	]

	for field in fields:
		exists = frappe.db.exists(
			"Custom Field", {"dt": "Payment Entry", "fieldname": field["fieldname"]}
		)
		if exists:
			continue
		frappe.get_doc({"doctype": "Custom Field", "dt": "Payment Entry", **field}).insert(
			ignore_permissions=True
		)


@frappe.whitelist()
def validate_payment_entry_for_complement(payment_entry):
	"""Validate that a Payment Entry is suitable to stamp a payment complement."""
	payment = frappe.get_doc("Payment Entry", payment_entry)
	errors = []
	warnings = []

	if getattr(payment, "docstatus", 0) != 1:
		errors.append("El Payment Entry debe estar contabilizado (Submited).")

	if getattr(payment, "payment_type", "") != "Receive":
		errors.append("El complemento de pago solo aplica a Payment Entries tipo Receive (cobros).")

	if not getattr(payment, "party", None):
		errors.append("El Payment Entry no tiene cliente.")

	references = [r for r in getattr(payment, "references", []) or []]
	invoice_refs = [
		r
		for r in references
		if getattr(r, "reference_doctype", "") == "Sales Invoice"
	]
	if not invoice_refs:
		errors.append("El Payment Entry no referencia ninguna factura de venta (Sales Invoice).")

	settings = frappe.get_single("Facturama Settings")
	if not getattr(settings, "api_user", None):
		errors.append("Falta configurar el usuario API de Facturama.")
	if not settings.get_password("api_password"):
		errors.append("Falta guardar la contraseña API de Facturama.")

	company = frappe.get_doc("Company", payment.company)
	company_zip = _get_primary_company_pincode(payment.company)
	if not company_zip or not str(company_zip).isdigit() or len(str(company_zip)) != 5:
		errors.append("La empresa no tiene código postal válido de 5 dígitos para expedición.")

	for ref in invoice_refs:
		invoice_name = getattr(ref, "reference_name", None)
		if not frappe.db.exists("Sales Invoice", invoice_name):
			errors.append(f"La factura de referencia {invoice_name} no existe.")
			continue
		invoice = frappe.get_doc("Sales Invoice", invoice_name)
		if getattr(invoice, "docstatus", 0) != 1:
			errors.append(f"La factura {invoice_name} no está contabilizada.")
		cfdi_id = getattr(invoice, "facturama_cfdi_id", None) or getattr(invoice, "cfdi_id", None)
		if not cfdi_id:
			errors.append(
				f"La factura {invoice_name} no tiene un CFDI timbrado asociado (facturama_cfdi_id)."
			)
		if not getattr(ref, "allocated_amount", 0):
			warnings.append(f"La factura {invoice_name} no tiene monto asignado (allocated_amount).")

	return {
		"ok": not errors,
		"errors": errors,
		"warnings": warnings,
		"payment_entry": payment.name,
	}


@frappe.whitelist()
def stamp_payment_complement(payment_entry):
	"""Stamp a payment complement (CfdiType P) for a Receive Payment Entry."""
	if not frappe.db.exists("Payment Entry", payment_entry):
		return {
			"ok": False,
			"errors": ["Guarda el Payment Entry antes de timbrar el complemento."],
			"warnings": [],
		}

	try:
		_ensure_payment_entry_facturama_fields()
		validation = validate_payment_entry_for_complement(payment_entry)
		if not validation.get("ok"):
			return {
				"ok": False,
				"errors": validation.get("errors", []),
				"warnings": validation.get("warnings", []),
				"message": "El Payment Entry no cumple con los requisitos para emitir el complemento.",
			}

		payment = frappe.get_doc("Payment Entry", payment_entry)

		existing_cfdi = getattr(payment, "facturama_complement_cfdi_id", None)
		if existing_cfdi:
			return {
				"ok": False,
				"errors": [
					f"Este Payment Entry ya tiene un complemento de pago timbrado (CFDI ID: {existing_cfdi})."
				],
				"warnings": [],
			}

		client = get_facturama_client()
		payload = client.build_payment_complement_payload(
			payment,
			settings={
				"default_payment_form": "03",
				"zip_code_company": _get_primary_company_pincode(payment.company),
			},
		)

		response = client.create_multiemisor_cfdi(payload)
		cfdi_id = erpnext_facturama.facturacionorcom.api.facturama_client.extract_cfdi_id(response)
		uuid = erpnext_facturama.facturacionorcom.api.facturama_client.extract_uuid(response)

		if cfdi_id:
			payment.db_set("facturama_complement_cfdi_id", cfdi_id)
		if uuid:
			payment.db_set("facturama_complement_uuid", uuid)
		frappe.db.commit()

		return {
			"ok": True,
			"message": "Complemento de pago timbrado correctamente.",
			"response": response,
			"cfdi_id": cfdi_id,
			"uuid": uuid,
		}
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Facturama payment complement stamping")
		return {"ok": False, "error": str(exc)}


@frappe.whitelist()
def check_payment_complement_status(payment_entry):
	"""Check the status of a stamped payment complement from a Payment Entry."""
	payment = frappe.get_doc("Payment Entry", payment_entry)
	cfdi_id = getattr(payment, "facturama_complement_cfdi_id", None)
	if not cfdi_id:
		return {
			"ok": False,
			"error": "El Payment Entry no tiene un complemento de pago timbrado asociado.",
		}

	client = get_facturama_client()
	try:
		result = client.get_cfdi_detail(cfdi_id)
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "Facturama payment complement status")
		return {"ok": False, "error": str(exc)}

	return {
		"ok": True,
		"cfdi_id": cfdi_id,
		"uuid": ((result.get("Complement", {}) or {}).get("TaxStamp", {}) or {}).get("Uuid", "")
		or erpnext_facturama.facturacionorcom.api.facturama_client.extract_uuid(result),
		"status": result.get("Status", "unknown"),
		"date": result.get("Date", ""),
		"total": result.get("Total", 0),
		"currency": result.get("Currency", ""),
		"receiver_rfc": (result.get("Receiver", {}) or {}).get("Rfc", ""),
		"receiver_name": (result.get("Receiver", {}) or {}).get("Name", ""),
		"full_response": result,
	}


@frappe.whitelist()
def download_payment_complement_xml(payment_entry):
	"""Download XML of a stamped payment complement from a Payment Entry."""
	payment = frappe.get_doc("Payment Entry", payment_entry)
	cfdi_id = getattr(payment, "facturama_complement_cfdi_id", None)
	if not cfdi_id:
		raise frappe.ValidationError(
			"El Payment Entry no tiene un complemento de pago timbrado asociado."
		)

	client = get_facturama_client()
	xml_text = client.download_multiemisor_cfdi_xml(cfdi_id)
	filename = f"{payment.name}-{cfdi_id}.xml"

	return {
		"ok": True,
		"filename": filename,
		"cfdi_id": cfdi_id,
		"xml_base64": base64.b64encode(xml_text.encode("utf-8")).decode("ascii"),
	}


@frappe.whitelist()
def cancel_payment_complement(payment_entry, motive="02", uuid_replacement=None):
	"""Request cancellation of a stamped payment complement from a Payment Entry."""
	payment = frappe.get_doc("Payment Entry", payment_entry)
	cfdi_id = getattr(payment, "facturama_complement_cfdi_id", None)
	if not cfdi_id:
		raise frappe.ValidationError(
			"El Payment Entry no tiene un complemento de pago timbrado asociado."
		)

	client = get_facturama_client()
	result = client.cancel_multiemisor_cfdi(
		cfdi_id,
		motive=motive,
		uuid_replacement=uuid_replacement,
	)

	if result is not None:
		payment.db_set("facturama_complement_cfdi_id", None)
		payment.db_set("facturama_complement_uuid", None)
		frappe.db.commit()

	return {
		"ok": True,
		"result": result,
		"payment_entry": payment.name,
		"cfdi_id": cfdi_id,
	}

