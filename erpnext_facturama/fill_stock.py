"""
Uso:
  bench --site arrasamedical.tech execute erpnext_facturama.fill_stock.main

Edita la lista ITEMS abajo con tus items, almacenes y cantidades.
"""
import frappe

# ========== EDITA AQUI ==========
# Formato: (item_code, warehouse, qty, rate)
# Si rate es 0, usa el ultimmo precio de compra o 1
ITEMS = [
    # ("ITEM-001", "Almacen Principal - AM", 10, 0),
    # ("ITEM-002", "Almacen Principal - AM", 5, 150.00),
    # ("ITEM-003", "Farmacia - AM", 20, 0),
]

# Fecha del movimiento (cambia si necesitas)
POSTING_DATE = "2026-08-17"
# ==================================


def main():
    if not ITEMS:
        print("ERROR: Agrega items a la lista ITEMS en el script fill_stock.py")
        return

    created = []
    errors = []

    for item_code, warehouse, qty, rate in ITEMS:
        try:
            # Check item exists
            if not frappe.db.exists("Item", item_code):
                errors.append(f"Item '{item_code}' no existe")
                continue

            # Check warehouse exists
            if not frappe.db.exists("Warehouse", warehouse):
                errors.append(f"Warehouse '{warehouse}' no existe")
                continue

            # Get item details
            item_doc = frappe.get_doc("Item", item_code)
            uom = item_doc.stock_uom or "Nos."

            # If rate is 0, try to get from last purchase rate or item valuation
            if rate == 0:
                last_rate = frappe.db.get_value("Item Price", {
                    "item_code": item_code,
                    "buying": 1,
                    "price_list": frappe.db.get_value("Buying Settings", None, "buying_price_list") or "Standard Buying"
                }, "price_list_rate")
                rate = last_rate or 1

            # Create Stock Reconciliation
            sr = frappe.get_doc({
                "doctype": "Stock Reconciliation",
                "posting_date": POSTING_DATE,
                "posting_time": "00:00:00",
                "purpose": "Opening Stock",
                "items": [{
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "qty": qty,
                    "valuation_rate": rate,
                    "amount": qty * rate,
                }]
            })
            sr.insert(ignore_permissions=True)
            sr.submit()
            created.append(f"{item_code}: {qty} {uom} en {warehouse} @ ${rate}")
            print(f"  OK: {item_code} -> {qty} {uom}")

        except Exception as e:
            errors.append(f"{item_code}: {str(e)[:100]}")
            print(f"  ERROR: {item_code}: {str(e)[:100]}")

    frappe.db.commit()

    print(f"\n=== RESUMEN ===")
    print(f"Creados: {len(created)}")
    print(f"Errores: {len(errors)}")
    if errors:
        for e in errors:
            print(f"  - {e}")
