"""Entity field conventions. Rows are dictionaries for easy CSV/JSON export."""
ENTITY_FIELDS = {
    "suppliers": ["supplier_id", "supplier_name", "region", "risk_level"],
    "material_lots": ["raw_lot_id", "supplier_id", "material_code", "quantity", "received_date", "status"],
    "products": ["product_id", "product_name", "unit"],
    "boms": ["bom_id", "product_id", "version", "effective_date"],
    "bom_materials": ["bom_id", "material_code", "quantity_per_unit"],
    "production_orders": ["production_order_id", "product_id", "bom_id", "planned_quantity", "actual_quantity", "start_date", "status"],
    "production_inputs": ["production_order_id", "raw_lot_id", "quantity_consumed"],
    "finished_lots": ["finished_lot_id", "production_order_id", "product_id", "produced_quantity", "production_date", "status"],
    "customers": ["customer_id", "customer_name", "region"],
    "shipments": ["shipment_id", "ship_date", "status"],
    "shipment_items": ["shipment_id", "finished_lot_id", "quantity_shipped"],
    "deliveries": ["delivery_id", "shipment_id", "customer_id", "finished_lot_id", "quantity_delivered", "delivery_date", "status"],
    "recall_cases": ["recall_id", "trigger_type", "trigger_lot_id", "opened_date", "status"],
    "recall_actions": ["action_id", "recall_id", "action_type", "target_type", "target_id", "quantity", "status", "action_date"],
    "ground_truth": ["issue_id", "issue_type", "entity_type", "entity_id", "expected_result"],
}
