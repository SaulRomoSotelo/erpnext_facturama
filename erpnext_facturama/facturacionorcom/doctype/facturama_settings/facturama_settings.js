// Copyright (c) 2026, Saul Romo and contributors
// For license information, please see license.txt

frappe.ui.form.on("Facturama Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Conectar cuenta"), () => {
			frappe.show_alert({
				message: __("Iniciando conexión con Facturama..."),
				indicator: "blue",
			});

			const missing_fields = ["api_user", "api_password"].filter(
				(fieldname) => !frm.doc[fieldname]
			);
			if (missing_fields.length) {
				frappe.msgprint({
					title: __("Faltan datos de conexión"),
					message: __("Completa usuario y contraseña API para conectar la cuenta."),
					indicator: "orange",
				});
				return;
			}

			frappe.show_alert({
				message: __("Guardando datos de conexión..."),
				indicator: "blue",
			});

			const test_connection = () => {
				frappe.call({
						method: "erpnext_facturama.facturacionorcom.doctype.facturama_settings.facturama_settings.test_facturama_connection",
						heading: __("Conectando cuenta"),
						freeze: true,
						callback(response) {
							const result = response.message || {};
							if (result.connection_status) {
								frm.doc.connection_status = result.connection_status;
								frm.doc.last_connection = result.last_connection;
								frm.refresh_field("connection_status");
								frm.refresh_field("last_connection");
							}
							frappe.msgprint({
								title: result.ok ? __("Conexión exitosa") : __("No se pudo conectar"),
								message: result.ok
									? __("Facturama {0} respondió correctamente. Código HTTP: {1}", [frm.doc.mode_sandbox ? "Sandbox" : "Producción", result.status_code || 200])
									: result.error || __("No se recibió una respuesta válida."),
								indicator: result.ok ? "green" : "red",
							});
						},
						error(response) {
							frappe.msgprint({
								title: __("Error al probar la conexión"),
								message: response?.message || __("El servidor no pudo ejecutar la prueba."),
								indicator: "red",
							});
						},
					});
			};

			const save_result = frm.is_dirty() ? frm.save() : Promise.resolve();
			save_result
				.then(test_connection)
				.catch((error) => {
					frappe.msgprint({
						title: __("No se pudo guardar"),
						message: error?.message || __("Frappe rechazó el formulario. Revisa los campos obligatorios o el mensaje mostrado en Error Log."),
						indicator: "red",
					});
				});
		});
	},
});

function show_connection_result(title, message, indicator) {
	const dialog = new frappe.ui.Dialog({
		title: title,
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "result",
				options: `<p class="text-${indicator}">${frappe.utils.escape_html(message)}</p>`,
			},
		],
		primary_action_label: __("Cerrar"),
		primary_action() {
			dialog.hide();
		},
	});
	dialog.show();
}
