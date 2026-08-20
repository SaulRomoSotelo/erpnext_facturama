import frappe

@frappe.whitelist()
def get_stock_items(warehouse=None, search=None, item_group=None):
    filters = {}
    if warehouse:
        filters["warehouse"] = warehouse

    conditions = ""
    if search:
        conditions += " AND (i.name LIKE %(search)s OR i.item_name LIKE %(search)s)"
    if item_group:
        conditions += " AND i.item_group = %(item_group)s"

    data = frappe.db.sql(
        f"""
        SELECT
            i.name AS identificador,
            i.item_name AS nombre,
            COALESCE(i.description, '') AS descripcion,
            COALESCE(i.item_group, '') AS grupo,
            COALESCE(SUM(b.actual_qty), 0) AS stock,
            COALESCE(b.warehouse, '') AS almacen
        FROM `tabItem` i
        LEFT JOIN `tabBin` b ON b.item_code = i.name
            {("AND b.warehouse = %(warehouse)s" if warehouse else "")}
        WHERE i.disabled = 0
            {conditions}
        GROUP BY i.name, b.warehouse
        ORDER BY i.item_group, i.item_name
        """,
        {
            "warehouse": warehouse,
            "search": f"%{search}%" if search else None,
            "item_group": item_group,
        },
        as_dict=True,
    )
    return data


@frappe.whitelist()
def get_warehouses():
    return frappe.get_all("Warehouse", filters={"is_group": 0}, fields=["name"], order_by="name")
