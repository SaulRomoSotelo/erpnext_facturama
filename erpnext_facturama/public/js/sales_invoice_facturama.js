frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
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
							message: `<pre style=\"white-space:pre-wrap;margin:0;\">${lines.join("\n")}</pre>`,
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
