frappe.pages["vista-almacen"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Vista Almacén",
		single_column: true,
	});

	// Filtro de almacén
	const warehouse_field = page.add_field({
		fieldtype: "Link",
		fieldname: "warehouse",
		options: "Warehouse",
		label: "Almacén",
		change() {
			load_data();
		},
	});

	// Filtro de grupo de producto
	const item_group_field = page.add_field({
		fieldtype: "Link",
		fieldname: "item_group",
		options: "Item Group",
		label: "Grupo de Producto",
		change() {
			load_data();
		},
	});

	// Buscador
	const search_field = page.add_field({
		fieldtype: "Data",
		fieldname: "search",
		label: "Buscar",
		change() {
			load_data();
		},
	});

	page.add_button(__("Actualizar"), () => load_data(), { icon: "refresh" });

	// Contenedor de la tabla
	const $body = $(`
		<div class="vista-almacen-wrapper" style="padding: 15px;">
			<div class="table-responsive">
				<table class="table table-bordered table-hover">
					<thead class="thead-dark">
						<tr>
							<th>Identificador</th>
							<th>Nombre</th>
							<th>Grupo</th>
							<th>Descripción</th>
							<th style="text-align:right;">Stock</th>
							<th>Almacén</th>
						</tr>
					</thead>
					<tbody id="almacen-tbody">
						<tr><td colspan="6" class="text-center text-muted">Cargando...</td></tr>
					</tbody>
				</table>
			</div>
		</div>
	`).appendTo(page.main);

	function load_data() {
		const warehouse = warehouse_field.get_value();
		const search = search_field.get_value();
		const item_group = item_group_field.get_value();

		frappe.call({
			method: "erpnext_facturama.facturacionorcom.page.vista_almacen.vista_almacen.get_stock_items",
			args: { warehouse, search, item_group },
			callback(r) {
				const rows = r.message || [];
				const $tbody = $("#almacen-tbody");
				$tbody.empty();

				if (!rows.length) {
					$tbody.html(
						'<tr><td colspan="6" class="text-center text-muted">Sin resultados</td></tr>'
					);
					return;
				}

				rows.forEach((row) => {
					$tbody.append(`
						<tr>
							<td><a href="/app/item/${row.identificador}">${row.identificador}</a></td>
							<td>${row.nombre}</td>
							<td>${row.grupo || ""}</td>
							<td>${(row.descripcion || "").replace(/<[^>]*>/g, "").trim()}</td>
							<td style="text-align:right;">${frappe.format(row.stock, { fieldtype: "Float" })}</td>
							<td>${row.almacen}</td>
						</tr>
					`);
				});
			},
		});
	}

	load_data();
};
