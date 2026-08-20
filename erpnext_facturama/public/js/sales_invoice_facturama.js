const BUNDLE_CUSTOMER = "INTERNATIONAL ORTHOPEDIC AND ARTROSCOPIC SUPLY";
const BUNDLE_FREE_ITEM = "TS.C100";
const BUNDLE_SAT_KEY = "42294209";
const BUNDLE_ITEMS = [
	"NBS105.55.30", "NBS105.55.35", "NBS105.55.40", "NBS105.55.45", "NBS105.55.50",
	"NBS106.65.30", "NBS106.65.35", "NBS106.65.40", "NBS106.65.45", "NBS106.65.50",
	"NBS106.65.55", "NBS134.70.35", "NBS134.70.40", "NBS134.70.45", "NBS134.70.50",
	"NBS134.70.55", "NBS111.55.50", "NBS111.55.60", "NBS111.55.70", "NBS111.55.80",
	"NBS111.55.90", "NBS111.55.100", "NBS111.55.110", "NBS111.55.120", "NBS111.55.130",
	"NBS111.55.140", "NBS111.55.150", "NBS111.55.200", "NBS111.55.250", "NBS111.55.300",
];

function sync_free_tuerca(frm) {
	if (frm.doc.customer !== BUNDLE_CUSTOMER) return;
	if (!frm.doc.items || !frm.doc.items.length) return;

	const bundle_count = frm.doc.items.filter(
		(row) => BUNDLE_ITEMS.includes(row.item_code) && row.item_code !== BUNDLE_FREE_ITEM
	).length;

	const existing = frm.doc.items.filter((row) => row.item_code === BUNDLE_FREE_ITEM);

	if (bundle_count === 0 && existing.length > 0) {
		existing.forEach((row) => {
			frm.get_field("items").grid.remove(row.name);
		});
		frm.refresh_field("items");
		return;
	}

	if (bundle_count > 0) {
		const current_qty = existing.length > 0 ? existing.reduce((s, r) => s + (r.qty || 0), 0) : 0;
		if (current_qty !== bundle_count) {
			if (existing.length > 0) {
				frappe.model.set_value(existing[0].doctype, existing[0].name, "qty", bundle_count);
				frappe.model.set_value(existing[0].doctype, existing[0].name, "rate", 0);
				frappe.model.set_value(existing[0].doctype, existing[0].name, "amount", 0);
				frappe.model.set_value(existing[0].doctype, existing[0].name, "mx_product_service_key", BUNDLE_SAT_KEY);
				for (let i = 1; i < existing.length; i++) {
					frm.get_field("items").grid.remove(existing[i].name);
				}
			} else {
				const row = frm.add_child("items");
				row.item_code = BUNDLE_FREE_ITEM;
				row.qty = bundle_count;
				row.rate = 0;
				row.amount = 0;
				row.mx_product_service_key = BUNDLE_SAT_KEY;
			}
			frm.refresh_field("items");
		}
	}
}

frappe.ui.form.on("Sales Invoice Item", {
	item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.item_code || row.mx_product_service_key) return;
		frappe.db.get_value("Item", row.item_code, "mx_product_service_key", (r) => {
			if (r && r.mx_product_service_key) {
				frappe.model.set_value(cdt, cdn, "mx_product_service_key", r.mx_product_service_key);
			}
		});
	},
});

frappe.ui.form.on("Quotation Item", {
	item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.item_code || row.mx_product_service_key) return;
		frappe.db.get_value("Item", row.item_code, "mx_product_service_key", (r) => {
			if (r && r.mx_product_service_key) {
				frappe.model.set_value(cdt, cdn, "mx_product_service_key", r.mx_product_service_key);
			}
		});
	},
});

frappe.ui.form.on("Sales Invoice", {
	customer(frm) {
		sync_free_tuerca(frm);
	},

	items_add(frm) {
		sync_free_tuerca(frm);
	},

	items_remove(frm) {
		sync_free_tuerca(frm);
	},

	refresh(frm) {
		sync_free_tuerca(frm);

		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button("Timbrar", () => {
			frappe.call({
				method: "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings.stamp_sales_invoice_with_facturama",
				args: { sales_invoice: frm.doc.name },
				freeze: true,
				freeze_message: "Timbrando CFDI en Facturama...",
				callback(response) {
					const result = response.message || {};
					if (result.ok) {
						frappe.msgprint({
							title: "CFDI timbrado",
							message: `El CFDI fue timbrado correctamente.\nID: ${frappe.utils.escape_html(result.cfdi_id || "N/D")}`,
							indicator: "green",
						});
					} else {
						const errors = result.errors || [];
						const warnings = result.warnings || [];
						const lines = [];
						if (errors.length) {
							lines.push("<b>Errores</b>");
							errors.forEach((msg) => lines.push(`- ${frappe.utils.escape_html(msg)}`));
						}
						if (warnings.length) {
							if (lines.length) {
								lines.push("");
							}
							lines.push("<b>Advertencias</b>");
							warnings.forEach((msg) => lines.push(`- ${frappe.utils.escape_html(msg)}`));
						}
						if (!lines.length) {
							lines.push(result.error || "No se pudo timbrar la factura.");
						}

						frappe.msgprint({
							title: "No se pudo timbrar",
							indicator: "orange",
							message: `<pre style="white-space:pre-wrap;margin:0;">${lines.join("\n")}</pre>`,
						});
					}
				},
			});
		}, "Factura Electrónica");

		frm.add_custom_button("Cancelar Timbre", () => {
			frappe.call({
				method: "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings.cancel_sales_invoice_timbre",
				args: {
					sales_invoice: frm.doc.name,
					motive: "02",
				},
				freeze: true,
				freeze_message: "Cancelando timbre en Facturama...",
				callback(response) {
					const result = response.message || {};
					if (result.ok) {
						const status = result.result && result.result.Status ? result.result.Status : "unknown";
						const message = result.result && result.result.Message ? result.result.Message : "La solicitud de cancelación fue enviada a Facturama.";
						frappe.msgprint({
							title: "Cancelación enviada",
							message: `Estado: ${frappe.utils.escape_html(status)}\n\n${frappe.utils.escape_html(message)}`,
							indicator: "green",
						});
					} else {
						frappe.msgprint({
							title: "No se pudo cancelar",
							message: result.error || "Ocurrió un error al cancelar el timbre.",
							indicator: "orange",
						});
					}
				},
				error(r) {
					frappe.msgprint({
						title: "Error de conexión",
						message: r.exception || r.message || "No se pudo conectar con el servidor.",
						indicator: "red",
					});
				},
			});
		}, "Factura Electrónica");

		frm.add_custom_button("Verificar Estatus", () => {
			frappe.call({
				method: "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings.check_cfdi_status",
				args: { sales_invoice: frm.doc.name },
				freeze: true,
				freeze_message: "Consultando estatus del CFDI en Facturama...",
				callback(response) {
					const result = response.message || {};
					if (!result.ok) {
						frappe.msgprint({
							title: "Error",
							message: result.error || "No se pudo consultar el estatus.",
							indicator: "orange",
						});
						return;
					}

					const statusMap = {
						active: { text: "Activo", indicator: "green" },
						cancelled: { text: "Cancelado", indicator: "red" },
						unknown: { text: "Desconocido", indicator: "orange" },
					};
					const statusInfo = statusMap[result.status] || { text: result.status, indicator: "orange" };

					const lines = [
						`<b>Estatus:</b> ${frappe.utils.escape_html(statusInfo.text)}`,
						`<b>UUID:</b> ${frappe.utils.escape_html(result.uuid || "N/D")}`,
						`<b>Folio:</b> ${frappe.utils.escape_html(result.cfdi_id || "N/D")}`,
						`<b>Fecha:</b> ${frappe.utils.escape_html(result.date || "N/D")}`,
						`<b>Total:</b> ${frappe.utils.escape_html(result.total || 0)} ${frappe.utils.escape_html(result.currency || "")}`,
						`<b>Receptor:</b> ${frappe.utils.escape_html(result.receiver_name || "")} (${frappe.utils.escape_html(result.receiver_rfc || "")})`,
					];

					frappe.msgprint({
						title: "Estatus del CFDI",
						message: lines.join("<br>"),
						indicator: statusInfo.indicator,
					});
				},
				error(r) {
					frappe.msgprint({
						title: "Error de conexión",
						message: r.exception || r.message || "No se pudo conectar con el servidor.",
						indicator: "red",
					});
				},
			});
		}, "Factura Electrónica");

		frm.add_custom_button("Descargar XML", () => {
			frappe.call({
				method: "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings.download_sales_invoice_xml",
				args: { sales_invoice: frm.doc.name },
				freeze: true,
				freeze_message: "Descargando XML desde Facturama...",
				callback(response) {
					const result = response.message || {};
					if (!result.ok || !result.xml_base64) {
						frappe.msgprint({
							title: "No se pudo descargar XML",
							message: result.error || "Facturama no devolvió un XML válido.",
							indicator: "orange",
						});
						return;
					}

					const xmlContent = atob(result.xml_base64);
					const blob = new Blob([xmlContent], { type: "application/xml;charset=utf-8" });
					const downloadUrl = URL.createObjectURL(blob);
					const link = document.createElement("a");
					link.href = downloadUrl;
					link.download = result.filename || `${frm.doc.name}.xml`;
					document.body.appendChild(link);
					link.click();
					document.body.removeChild(link);
					URL.revokeObjectURL(downloadUrl);

					frappe.show_alert({
						message: "XML descargado correctamente.",
						indicator: "green",
					});
				},
			});
		}, "Factura Electrónica");
	},
});

frappe.ui.form.on("Quotation", {
	customer(frm) {
		sync_free_tuerca(frm);
	},

	items_add(frm) {
		sync_free_tuerca(frm);
	},

	items_remove(frm) {
		sync_free_tuerca(frm);
	},

	refresh(frm) {
		sync_free_tuerca(frm);
	},
});
