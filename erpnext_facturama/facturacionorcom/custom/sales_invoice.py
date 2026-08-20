import frappe


class SalesInvoiceFacturamaMixin:
	"""Custom naming for Sales Invoice: name = CFDI folio number (861, 862, ...)."""

	def autoname(self):
		from erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings import (
			get_next_sales_invoice_folio,
		)

		folio = str(get_next_sales_invoice_folio())
		self.name = folio
		self.facturama_folio = folio
		return self.name