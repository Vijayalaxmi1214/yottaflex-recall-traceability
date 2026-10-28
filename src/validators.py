"""Integrity checks and measurable validation output."""
from collections import defaultdict

def validate(data: dict) -> dict:
    errors, warnings = [], []
    def ids(table, key):
        return {row[key] for row in data.get(table, []) if key in row}
    # Primary-key uniqueness
    key_fields = {
        "suppliers":"supplier_id", "material_lots":"raw_lot_id", "products":"product_id",
        "boms":"bom_id", "production_orders":"production_order_id", "finished_lots":"finished_lot_id",
        "customers":"customer_id", "shipments":"shipment_id", "deliveries":"delivery_id",
        "recall_cases":"recall_id", "recall_actions":"action_id"
    }
    for table, key in key_fields.items():
        values = [r[key] for r in data.get(table, []) if key in r]
        if len(values) != len(set(values)):
            errors.append({"type":"duplicate_primary_key", "table":table, "field":key})
    supplier_ids, raw_ids = ids("suppliers","supplier_id"), ids("material_lots","raw_lot_id")
    product_ids, bom_ids = ids("products","product_id"), ids("boms","bom_id")
    po_ids, finished_ids = ids("production_orders","production_order_id"), ids("finished_lots","finished_lot_id")
    customer_ids, shipment_ids = ids("customers","customer_id"), ids("shipments","shipment_id")
    recall_ids = ids("recall_cases", "recall_id")

    # Foreign keys
    for row in data.get("material_lots", []):
        if row.get("supplier_id") not in supplier_ids:
            errors.append({"type":"invalid_supplier_fk", "id":row.get("raw_lot_id")})
    for row in data.get("boms", []):
        if row.get("product_id") not in product_ids:
            errors.append({"type":"invalid_product_fk", "id":row.get("bom_id")})
    for row in data.get("bom_materials", []):
        if row.get("bom_id") not in bom_ids:
            errors.append({"type":"invalid_bom_material_fk", "id":row.get("bom_id")})
    for row in data.get("production_orders", []):
        if row.get("product_id") not in product_ids or row.get("bom_id") not in bom_ids:
            errors.append({"type":"invalid_production_order_fk", "id":row.get("production_order_id")})
    for row in data.get("production_inputs", []):
        if row.get("production_order_id") not in po_ids:
            errors.append({"type":"invalid_production_input_order_fk", "id":row.get("production_order_id")})
        if row.get("raw_lot_id") not in raw_ids:
            errors.append({"type":"missing_input_lot", "id":row.get("raw_lot_id"), "production_order_id":row.get("production_order_id")})
    for row in data.get("finished_lots", []):
        if row.get("production_order_id") not in po_ids:
            errors.append({"type":"invalid_finished_lot_order_fk", "id":row.get("finished_lot_id")})
        if row.get("product_id") not in product_ids:
            errors.append({"type":"invalid_finished_lot_product_fk", "id":row.get("finished_lot_id")})
    for row in data.get("shipment_items", []):
        if row.get("shipment_id") not in shipment_ids or row.get("finished_lot_id") not in finished_ids:
            errors.append({"type":"invalid_shipment_item_fk", "id":row.get("shipment_id")})
    for row in data.get("deliveries", []):
        if row.get("shipment_id") not in shipment_ids or row.get("customer_id") not in customer_ids or row.get("finished_lot_id") not in finished_ids:
            errors.append({"type":"invalid_delivery_fk", "id":row.get("delivery_id")})
    for row in data.get("recall_actions", []):
        if row.get("recall_id") not in recall_ids:
            errors.append({"type":"invalid_recall_action_fk", "id":row.get("action_id")})
        if row.get("status") == "violation_available_for_sale":
            errors.append({"type":"quarantine_violation", "id":row.get("action_id"), "target_id":row.get("target_id")})

    # Check for recall cases missing downstream customer relationships / actions
    for case in data.get("recall_cases", []):
        case_actions = [a for a in data.get("recall_actions", []) if a.get("recall_id") == case.get("recall_id")]
        has_customer_action = any(a.get("target_type") == "customer" for a in case_actions)
        if not has_customer_action:
            warnings.append({"type":"report_missing_customer_relationship", "recall_id":case.get("recall_id")})

    # Quantity reconciliation based on source finished-lot quantities.
    produced = {r["finished_lot_id"]: int(r["produced_quantity"]) for r in data.get("finished_lots", []) if "finished_lot_id" in r and "produced_quantity" in r}
    delivered = defaultdict(int)
    for row in data.get("deliveries", []):
        if "finished_lot_id" in row and "quantity_delivered" in row:
            delivered[row["finished_lot_id"]] += int(row["quantity_delivered"])
    for lot_id, qty in delivered.items():
        if lot_id in produced and qty > produced[lot_id]:
            errors.append({"type":"delivered_quantity_exceeds_production", "finished_lot_id":lot_id,
                           "produced":produced[lot_id], "delivered":qty})

    # Lifecycle and quantity checks
    quantity_fields = {
        "material_lots": ["quantity"],
        "production_orders": ["planned_quantity", "actual_quantity"],
        "production_inputs": ["quantity_consumed"],
        "finished_lots": ["produced_quantity"],
        "shipment_items": ["quantity_shipped"],
        "deliveries": ["quantity_delivered"],
        "bom_materials": ["quantity_per_unit"],
        "recall_actions": ["quantity"],
    }
    for table, fields in quantity_fields.items():
        for row in data.get(table, []):
            for field in fields:
                val = row.get(field)
                if val is not None and int(val) < 0:
                    errors.append({"type":"negative_quantity", "table":table, "field":field, "id":row.get(key_fields.get(table, "id"))})

    return {"valid": len(errors) == 0, "error_count":len(errors), "warning_count":len(warnings),
            "errors":errors[:1000], "warnings":warnings}
