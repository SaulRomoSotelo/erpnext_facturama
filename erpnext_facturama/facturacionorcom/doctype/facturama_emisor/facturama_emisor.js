frappe.ui.form.on("Facturama Emisor", {
	refresh(frm) {
		frm.add_custom_button(__("Cargar CSD"), () => {
			if (frm.is_new()) {
				frappe.msgprint(__("Guarda primero el emisor antes de cargar el CSD."));
				return;
			}

			frappe.call({
				method: "erpnext_facturama.facturacionorcom.doctype.facturama_emisor.facturama_emisor.upload_csd",
				args: { name: frm.doc.name },
				heading: __("Cargando CSD"),
				freeze: true,
				callback(response) {
					const result = response.message || {};
					frappe.msgprint({
						title: result.ok ? __("CSD cargado") : __(result.title || "Error al cargar CSD"),
						message: result.ok
							? __("El CSD quedó registrado en Facturama.")
							: result.error || __("Facturama rechazó el CSD."),
						indicator: result.ok ? "green" : "red",
					});
					frm.reload_doc();
				},
			});
		});
	},
});
