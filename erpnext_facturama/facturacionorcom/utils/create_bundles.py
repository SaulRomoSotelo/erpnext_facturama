import frappe

def main():
    items = [
        "NBS105.55.30", "NBS105.55.35", "NBS105.55.40", "NBS105.55.45", "NBS105.55.50",
        "NBS106.65.30", "NBS106.65.35", "NBS106.65.40", "NBS106.65.45", "NBS106.65.50",
        "NBS106.65.55", "NBS134.70.35", "NBS134.70.40", "NBS134.70.45", "NBS134.70.50",
        "NBS134.70.55", "NBS111.55.50", "NBS111.55.60", "NBS111.55.70", "NBS111.55.80",
        "NBS111.55.90", "NBS111.55.100", "NBS111.55.110", "NBS111.55.120", "NBS111.55.130",
        "NBS111.55.140", "NBS111.55.150", "NBS111.55.200", "NBS111.55.250", "NBS111.55.300",
    ]

    created = 0
    skipped = 0

    for item_code in items:
        existing = frappe.db.exists("Product Bundle", {"new_item_code": item_code})
        if existing:
            print(f"SKIP {item_code} (already exists: {existing})")
            skipped += 1
            continue

        bundle = frappe.get_doc({
            "doctype": "Product Bundle",
            "new_item_code": item_code,
            "description": f"{item_code} + TS.C100",
            "items": [{
                "item_code": "TS.C100",
                "qty": 1,
            }]
        })
        bundle.insert(ignore_permissions=True)
        print(f"CREATED {item_code}")
        created += 1

    frappe.db.commit()
    print(f"\nDone: {created} created, {skipped} skipped")
