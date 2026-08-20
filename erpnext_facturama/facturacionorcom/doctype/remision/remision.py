import frappe
from frappe.model.document import Document


class Remision(Document):
    def validate(self):
        pass


@frappe.whitelist()
def get_groups_stock(warehouse):
    """Get all Item Groups with total stock in the warehouse."""
    data = frappe.db.sql(
        """
        SELECT
            i.item_group,
            COALESCE(SUM(b.actual_qty), 0) AS stock_qty
        FROM `tabItem` i
        INNER JOIN `tabBin` b ON b.item_code = i.name AND b.warehouse = %(warehouse)s
        WHERE i.disabled = 0
            AND i.item_group IS NOT NULL
            AND i.item_group != ''
        GROUP BY i.item_group
        HAVING stock_qty > 0
        ORDER BY i.item_group
        """,
        {"warehouse": warehouse},
        as_dict=True,
    )
    return data


@frappe.whitelist()
def get_items_by_group(item_group, warehouse):
    """Get all items in a group with stock in the warehouse."""
    data = frappe.db.sql(
        """
        SELECT
            i.name AS item_code,
            i.item_name,
            i.item_group,
            COALESCE(b.actual_qty, 0) AS stock_qty
        FROM `tabItem` i
        INNER JOIN `tabBin` b ON b.item_code = i.name AND b.warehouse = %(warehouse)s
        WHERE i.disabled = 0
            AND i.item_group = %(item_group)s
            AND b.actual_qty > 0
        ORDER BY i.item_code
        """,
        {"item_group": item_group, "warehouse": warehouse},
        as_dict=True,
    )
    return data


@frappe.whitelist()
def get_all_items_by_warehouse(warehouse):
    """Get all items with stock grouped by item_group."""
    data = frappe.db.sql(
        """
        SELECT
            i.name AS item_code,
            i.item_name,
            i.item_group,
            COALESCE(b.actual_qty, 0) AS stock_qty
        FROM `tabItem` i
        INNER JOIN `tabBin` b ON b.item_code = i.name AND b.warehouse = %(warehouse)s
        WHERE i.disabled = 0
            AND i.item_group IS NOT NULL
            AND i.item_group != ''
            AND b.actual_qty > 0
        ORDER BY i.item_group, i.item_code
        """,
        {"warehouse": warehouse},
        as_dict=True,
    )
    return data
