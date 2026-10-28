"""Generate coherent synthetic supply-chain data with deterministic randomness."""
import random
from datetime import date, timedelta
from .id_generator import raw_lot_id, production_order_id, finished_lot_id, shipment_id

REGIONS = ["North", "South", "East", "West", "Central"]
MATERIALS = ["MAT-A", "MAT-B", "MAT-C", "MAT-D"]
PRODUCTS = [("PROD-001", "Widget Alpha"), ("PROD-002", "Widget Beta"), ("PROD-003", "Widget Gamma")]

def day(offset: int) -> str:
    return (date(2026, 1, 1) + timedelta(days=offset)).isoformat()

def generate_data(scale: dict, seed: int = 20261027, inject_anomalies: bool = False) -> dict:
    rng = random.Random(seed)
    suppliers, raw_lots, products, boms, bom_materials = [], [], [], [], []
    production_orders, production_inputs, finished_lots = [], [], []
    customers, shipments, shipment_items, deliveries = [], [], [], []
    recall_cases, recall_actions, ground_truth = [], [], []

    for i in range(1, scale["suppliers"] + 1):
        suppliers.append({"supplier_id": f"SUP-{i:04d}", "supplier_name": f"Supplier {i:04d}",
                          "region": rng.choice(REGIONS), "risk_level": rng.choice(["low", "medium", "high"])})
    for pid, pname in PRODUCTS:
        products.append({"product_id": pid, "product_name": pname, "unit": "unit"})
        bom_id = f"BOM-{pid}-V1"
        boms.append({"bom_id": bom_id, "product_id": pid, "version": 1, "effective_date": day(0)})
        for material in MATERIALS[:2 if pid != "PROD-003" else 3]:
            bom_materials.append({"bom_id": bom_id, "material_code": material, "quantity_per_unit": 1})

    # Raw material lots are linked to real suppliers and have deterministic IDs.
    for i in range(1, scale["raw_lots"] + 1):
        supplier = suppliers[(i - 1) % len(suppliers)]
        raw_lots.append({"raw_lot_id": raw_lot_id(supplier["supplier_id"], i),
                         "supplier_id": supplier["supplier_id"], "material_code": rng.choice(MATERIALS),
                         "quantity": rng.randint(100, 2500), "received_date": day(rng.randint(0, 180)),
                         "status": "available"})

    # Create requested finished lots and production orders. Every production order creates at least one lot.
    for i in range(1, scale["production_orders"] + 1):
        product = products[(i - 1) % len(products)]
        bom = next(b for b in boms if b["product_id"] == product["product_id"])
        qty = rng.randint(20, 300)
        po = {"production_order_id": production_order_id(i), "product_id": product["product_id"],
              "bom_id": bom["bom_id"], "planned_quantity": qty, "actual_quantity": qty,
              "start_date": day(rng.randint(10, 240)), "status": "completed"}
        production_orders.append(po)
        lot_count = 1
        if len(finished_lots) + 1 < scale["finished_lots"] and i % 5 == 0:
            lot_count = 2
        remaining = qty
        for j in range(lot_count):
            if len(finished_lots) >= scale["finished_lots"]:
                break
            lot_qty = remaining if j == lot_count - 1 else max(1, remaining // 2)
            remaining -= lot_qty
            flid = finished_lot_id(len(finished_lots) + 1)
            finished_lots.append({"finished_lot_id": flid, "production_order_id": po["production_order_id"],
                                  "product_id": product["product_id"], "produced_quantity": lot_qty,
                                  "production_date": po["start_date"], "status": "released"})
        # Consume two raw lots where possible. Keep each lot input within its original quantity approximately;
        # validation focuses on references and shipment/production reconciliation.
        for _ in range(2):
            raw = rng.choice(raw_lots)
            production_inputs.append({"production_order_id": po["production_order_id"],
                                       "raw_lot_id": raw["raw_lot_id"],
                                       "quantity_consumed": rng.randint(1, 20)})

    # Fill any remaining finished lots if requested production-order count was smaller than finished-lot count.
    while len(finished_lots) < scale["finished_lots"]:
        po = production_orders[(len(finished_lots)) % len(production_orders)]
        flid = finished_lot_id(len(finished_lots) + 1)
        finished_lots.append({"finished_lot_id": flid, "production_order_id": po["production_order_id"],
                              "product_id": po["product_id"], "produced_quantity": 10,
                              "production_date": po["start_date"], "status": "released"})

    customer_count = max(10, min(1000, scale["deliveries"] // 4))
    for i in range(1, customer_count + 1):
        customers.append({"customer_id": f"CUST-{i:05d}", "customer_name": f"Customer {i:05d}",
                          "region": rng.choice(REGIONS)})

    # Allocate shipments/deliveries from finished lots without shipping more than produced quantity.
    remaining_by_lot = {x["finished_lot_id"]: x["produced_quantity"] for x in finished_lots}
    lot_by_id = {x["finished_lot_id"]: x for x in finished_lots}
    active_lots = [x["finished_lot_id"] for x in finished_lots if x["produced_quantity"] > 0]
    for i in range(1, scale["deliveries"] + 1):
        if not active_lots:
            break
        lot_id = rng.choice(active_lots)
        qty = min(remaining_by_lot[lot_id], rng.randint(1, 10))
        remaining_by_lot[lot_id] -= qty
        if remaining_by_lot[lot_id] <= 0:
            active_lots.remove(lot_id)
        sid = shipment_id(i)
        shipment = {"shipment_id": sid, "ship_date": day(rng.randint(30, 300)), "status": "shipped"}
        shipments.append(shipment)
        shipment_items.append({"shipment_id": sid, "finished_lot_id": lot_id, "quantity_shipped": qty})
        deliveries.append({"delivery_id": f"DEL-{i:07d}", "shipment_id": sid,
                           "customer_id": rng.choice(customers)["customer_id"], "finished_lot_id": lot_id,
                           "quantity_delivered": qty, "delivery_date": shipment["ship_date"], "status": "delivered"})

    # Create a recall from a raw lot that is actually used by a production order,
    # so the example recall normally has a meaningful downstream path.
    if raw_lots:
        used_raw_ids = {row["raw_lot_id"] for row in production_inputs if row["raw_lot_id"] in {r["raw_lot_id"] for r in raw_lots}}
        trigger_id = sorted(used_raw_ids)[0] if used_raw_ids else raw_lots[0]["raw_lot_id"]
        trigger = next(r for r in raw_lots if r["raw_lot_id"] == trigger_id)
        recall_cases.append({"recall_id": "REC-2026-000001", "trigger_type": "raw_material",
                             "trigger_lot_id": trigger["raw_lot_id"], "opened_date": day(300), "status": "open"})
        recall_actions.append({"action_id": "ACT-000001", "recall_id": "REC-2026-000001",
                               "action_type": "investigate", "target_type": "raw_lot",
                               "target_id": trigger["raw_lot_id"], "quantity": 0,
                               "status": "completed", "action_date": day(300)})

    # Inject labeled anomalies only after baseline records are generated.
    if inject_anomalies and finished_lots and raw_lots and deliveries:
        # 1. A finished lot references a missing raw lot via a production input.
        production_inputs.append({"production_order_id": production_orders[0]["production_order_id"],
                                  "raw_lot_id": "RAWLOT-MISSING-2026-999999", "quantity_consumed": 5})
        ground_truth.append({"issue_id": "ISSUE-0001", "issue_type": "missing_input_lot",
                             "entity_type": "production_inputs", "entity_id": production_orders[0]["production_order_id"],
                             "expected_result": "foreign_key_violation"})
        # 2. Add a deliberately excessive delivery record with a separate label.
        source_delivery = deliveries[0]
        deliveries.append({"delivery_id": f"DEL-ANOM-{seed}", "shipment_id": source_delivery["shipment_id"],
                           "customer_id": source_delivery["customer_id"], "finished_lot_id": source_delivery["finished_lot_id"],
                           "quantity_delivered": lot_by_id[source_delivery["finished_lot_id"]]["produced_quantity"] + 100,
                           "delivery_date": source_delivery["delivery_date"], "status": "delivered"})
        ground_truth.append({"issue_id": "ISSUE-0002", "issue_type": "delivered_quantity_exceeds_production",
                             "entity_type": "deliveries", "entity_id": f"DEL-ANOM-{seed}",
                             "expected_result": "quantity_reconciliation_failure"})
        # 3. Recall record has a deliberately missing downstream customer relationship.
        ground_truth.append({"issue_id": "ISSUE-0003", "issue_type": "recall_missing_downstream_customer",
                             "entity_type": "recall_cases", "entity_id": "REC-2026-000001",
                             "expected_result": "report_missing_customer_relationship"})
        # 4. Create an explicit quarantine violation marker.
        recall_actions.append({"action_id": "ACT-ANOM-0004", "recall_id": "REC-2026-000001",
                               "action_type": "sale_block_check", "target_type": "finished_lot",
                               "target_id": finished_lots[0]["finished_lot_id"], "quantity": 1,
                               "status": "violation_available_for_sale", "action_date": day(301)})
        ground_truth.append({"issue_id": "ISSUE-0004", "issue_type": "recalled_inventory_available_for_sale",
                             "entity_type": "recall_actions", "entity_id": "ACT-ANOM-0004",
                             "expected_result": "quarantine_violation"})

    return {
        "suppliers": suppliers, "material_lots": raw_lots, "products": products, "boms": boms,
        "bom_materials": bom_materials, "production_orders": production_orders,
        "production_inputs": production_inputs, "finished_lots": finished_lots,
        "customers": customers, "shipments": shipments, "shipment_items": shipment_items,
        "deliveries": deliveries, "recall_cases": recall_cases, "recall_actions": recall_actions,
        "ground_truth": ground_truth
    }
