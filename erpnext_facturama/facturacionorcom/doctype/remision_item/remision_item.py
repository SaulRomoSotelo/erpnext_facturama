import frappe
from frappe.model.document import Document


class RemisionItem(Document):
    def validate(self):
        if self.item_code:
            item = frappe.get_doc("Item", self.item_code)
            self.item_name = item.item_name
            self.item_group = item.item_group
            self.stock_uom = item.stock_uom
            if not self.description:
                self.description = item.description or item.item_name

            # Auto-fill stock
            warehouse = self.parent_warehouse if hasattr(self, "parent_warehouse") else None
            if not warehouse:
                parent = frappe.get_doc(self.parenttype, self.parent)
                warehouse = parent.warehouse if hasattr(parent, "warehouse") else None
            if warehouse:
                stock = frappe.db.get_value(
                    "Bin",
                    {"item_code": self.item_code, "warehouse": warehouse},
                    "actual_qty",
                )
                self.warehouse_stock = stock or 0

        if self.qty and self.rate:
            self.amount = self.qty * self.rate
        else:
            self.amount = 0
