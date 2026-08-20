frappe.ui.form.on("Payment Entry", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		if (frm.doc.payment_type !== "Receive") {
			return;
		}

		const has_references = (frm.doc.references || []).some(
			(row) => row.reference_doctype === "Sales Invoice"
		);

		if (!has_references) {
			return;
		}

		const has_complement = Boolean(frm.doc.facturama_complement_cfdi_id);

		if (has_complement) {
			frm.add_custom_button("Estatus Complemento", () => {
				frappe.call({
					method: "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings.check_payment_complement_status",
					args: { payment_entry: frm.doc.name },
					freeze: true,
					freeze_message: "Consultando estatus del complemento...",
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
						const statusInfo =
							statusMap[result.status] || {
								text: result.status,
								indicator: "orange",
							};

						frappe.msgprint({
							title: "Estatus del Complemento de Pago",
							message: [
								`<b>Estatus:</b> ${frappe.utils.escape_html(statusInfo.text)}`,
								`<b>UUID:</b> ${frappe.utils.escape_html(result.uuid || "N/D")}`,
								`<b>Folio:</b> ${frappe.utils.escape_html(result.cfdi_id || "N/D")}`,
								`<b>Fecha:</b> ${frappe.utils.escape_html(result.date || "N/D")}`,
								`<b>Total:</b> ${frappe.utils.escape_html(result.total || 0)} ${frappe.utils.escape_html(result.currency || "")}`,
								`<b>Receptor:</b> ${frappe.utils.escape_html(result.receiver_name || "")} (${frappe.utils.escape_html(result.receiver_rfc || "")})`,
							].join("<br>"),
							indicator: statusInfo.indicator,
						});
					},
				});
			}, "Complemento de Pago");

			frm.add_custom_button("Descargar XML", () => {
				frappe.call({
					method: "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings.download_payment_complement_xml",
					args: { payment_entry: frm.doc.name },
					freeze: true,
					freeze_message: "Descargando XML del complemento...",
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
			}, "Complemento de Pago");

			frm.add_custom_button("Cancelar Complemento", () => {
				frappe.confirm(
					"¿Seguro que deseas cancelar el complemento de pago en Facturama?",
					() => {
						frappe.call({
							method: "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings.cancel_payment_complement",
							args: { payment_entry: frm.doc.name, motive: "02" },
							freeze: true,
							freeze_message: "Cancelando complemento en Facturama...",
							callback(response) {
								const result = response.message || {};
								if (result.ok) {
									frappe.msgprint({
										title: "Cancelación enviada",
										message:
											(result.result && result.result.Status)
												? `Estado: ${frappe.utils.escape_html(result.result.Status)}`
												: "La solicitud de cancelación fue enviada a Facturama.",
										indicator: "green",
									});
									frm.reload_doc();
								} else {
									frappe.msgprint({
										title: "No se pudo cancelar",
										message: result.error || "Ocurrió un error al cancelar.",
										indicator: "orange",
									});
								}
							},
						});
					}
				);
			}, "Complemento de Pago");
		} else {
			frm.add_custom_button("Timbrar Complemento de Pago", () => {
				frappe.call({
					method: "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings.stamp_payment_complement",
					args: { payment_entry: frm.doc.name },
					freeze: true,
					freeze_message: "Timbrando complemento de pago en Facturama...",
					callback(response) {
						const result = response.message || {};
						if (result.ok) {
							frappe.msgprint({
								title: "Complemento timbrado",
								message: `El complemento de pago fue timbrado correctamente.\nCFDI ID: ${frappe.utils.escape_html(result.cfdi_id || "N/D")}`,
								indicator: "green",
							});
							frm.reload_doc();
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
								lines.push(result.error || "No se pudo timbrar el complemento.");
							}

							frappe.msgprint({
								title: "No se pudo timbrar",
								indicator: "orange",
								message: `<pre style="white-space:pre-wrap;margin:0;">${lines.join("\n")}</pre>`,
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
			}, "Complemento de Pago");
		}
	},
});