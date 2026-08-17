# Copyright (c) 2026, Saul Romo and contributors
# For license information, please see license.txt

import base64
import os
import subprocess
import tempfile

import frappe
from frappe.model.document import Document

import erpnext_facturama.facturacionorcom.api.facturama_client
from erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings import (
	get_facturama_client,
)


class FacturamaEmisor(Document):
	def validate(self):
		if not self.rfc:
			frappe.throw("La empresa debe tener RFC configurado")
		if not self.fiscal_regime:
			frappe.throw("La empresa debe tener régimen fiscal configurado")
		if not self.expedition_place.isdigit() or len(self.expedition_place) != 5:
			frappe.throw("El código postal de expedición debe tener 5 dígitos")
		for fieldname, extension in (("certificate_file", ".cer"), ("private_key_file", ".key")):
			file_url = self.get(fieldname) or ""
			if not file_url.lower().endswith(extension):
				frappe.throw(f"{fieldname} debe ser un archivo {extension}")


def _read_private_file(file_url):
	file_doc = frappe.get_doc("File", {"file_url": file_url})
	if not file_doc.is_private:
		frappe.throw("Los archivos CSD deben almacenarse como privados")
	return file_doc.get_content()


def _write_temp_bytes(content, suffix):
	temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
	try:
		temp_file.write(content)
		temp_file.flush()
		return temp_file.name
	finally:
		temp_file.close()


def _run_openssl(args):
	return subprocess.run(args, capture_output=True, check=True, text=True)


def _validate_csd_files(certificate_bytes, private_key_bytes, private_key_password):
	certificate_path = _write_temp_bytes(certificate_bytes, ".cer")
	private_key_path = _write_temp_bytes(private_key_bytes, ".key")
	private_key_pub_path = private_key_path + ".pub"
	try:
		try:
			_run_openssl([
				"openssl",
				"x509",
				"-inform",
				"DER",
				"-noout",
				"-pubkey",
				"-in",
				certificate_path,
			])
		except subprocess.CalledProcessError:
			return {"error": "El archivo .cer no es válido o está dañado.", "stage": "certificate"}

		try:
			_run_openssl([
				"openssl",
				"pkey",
				"-inform",
				"DER",
				"-in",
				private_key_path,
				"-passin",
				f"pass:{private_key_password}",
				"-noout",
			])
		except subprocess.CalledProcessError as exc:
			stderr = (exc.stderr or "").lower()
			if "decrypt" in stderr or "bad decrypt" in stderr or "password" in stderr:
				return {
					"error": "La contraseña de la llave privada no es correcta.",
					"stage": "password",
				}
			return {"error": "La llave privada .key no es válida o está dañada.", "stage": "private_key"}

		_run_openssl([
			"openssl",
			"x509",
			"-inform",
			"DER",
			"-noout",
			"-pubkey",
			"-in",
			certificate_path,
			"-out",
			certificate_path + ".pub",
		])
		_run_openssl([
			"openssl",
			"pkey",
			"-inform",
			"DER",
			"-in",
			private_key_path,
			"-passin",
			f"pass:{private_key_password}",
			"-pubout",
			"-out",
			private_key_pub_path,
		])

		with open(certificate_path + ".pub", "r", encoding="utf-8") as certificate_pub_file:
			certificate_pubkey = certificate_pub_file.read().strip()
		with open(private_key_pub_path, "r", encoding="utf-8") as private_key_pub_file:
			private_key_pubkey = private_key_pub_file.read().strip()

		if certificate_pubkey != private_key_pubkey:
			return {
				"error": "El certificado .cer y la llave .key no corresponden al mismo CSD.",
				"stage": "mismatch",
			}

		return {"error": "", "stage": ""}
	finally:
		for path in (certificate_path, private_key_path, certificate_path + ".pub", private_key_pub_path):
			if os.path.exists(path):
				os.unlink(path)


@frappe.whitelist()
def upload_csd(name):
	emisor = frappe.get_doc("Facturama Emisor", name)
	emisor.check_permission("write")
	certificate_bytes = _read_private_file(emisor.certificate_file)
	private_key_bytes = _read_private_file(emisor.private_key_file)
	private_key_password = emisor.get_password("private_key_password")
	validation_error = _validate_csd_files(certificate_bytes, private_key_bytes, private_key_password)
	if validation_error.get("error"):
		emisor.db_set({"csd_status": "Error"})
		return {
			"ok": False,
			"error": validation_error["error"],
			"stage": validation_error.get("stage", "validation"),
			"title": "Error al validar CSD",
		}

	certificate = base64.b64encode(certificate_bytes).decode()
	private_key = base64.b64encode(private_key_bytes).decode()
	client = get_facturama_client()

	try:
		result = client.upload_csd(emisor.rfc, certificate, private_key, private_key_password)
	except Exception as exc:
		emisor.db_set({"csd_status": "Error"})
		frappe.log_error(frappe.get_traceback(), "Facturama CSD upload")
		detail = str(exc).strip()
		if detail == "La solicitud no es válida.":
			detail = (
				"Facturama rechazó el CSD: la solicitud no es válida. "
				"Revisa que el .cer y la .key correspondan al mismo certificado y que la contraseña sea correcta."
			)
		return {
			"ok": False,
			"error": detail or "No fue posible cargar el CSD en Facturama.",
			"stage": "facturama",
			"title": "Error al cargar en Facturama",
		}

	emisor.db_set({"csd_status": "Cargado", "csd_uploaded_at": frappe.utils.now_datetime()})
	return {"ok": True, "result": result}
