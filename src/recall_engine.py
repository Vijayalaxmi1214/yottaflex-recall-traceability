"""Downstream genealogy traversal and recall scope calculation."""
from __future__ import annotations
from collections import defaultdict

def simulate_recall(data: dict, recall_id: str | None = None) -> dict:
    cases = data.get("recall_cases", [])
    if not cases:
        return {"error":"No recall case available"}
    case = next((c for c in cases if recall_id is None or c["recall_id"] == recall_id), None)
    if not case:
        return {"error":f"Recall case not found: {recall_id}"}

    trigger_type, trigger_id = case["trigger_type"], case["trigger_lot_id"]
    raw_to_orders = defaultdict(set)
    for row in data.get("production_inputs", []):
        raw_to_orders[row["raw_lot_id"]].add(row["production_order_id"])
    order_to_finished = defaultdict(set)
    for row in data.get("finished_lots", []):
        order_to_finished[row["production_order_id"]].add(row["finished_lot_id"])
    finished_to_deliveries = defaultdict(list)
    for row in data.get("deliveries", []):
        finished_to_deliveries[row["finished_lot_id"]].append(row)

    affected_finished = set()
    if trigger_type == "raw_material":
        for order_id in raw_to_orders.get(trigger_id, set()):
            affected_finished.update(order_to_finished.get(order_id, set()))
    elif trigger_type == "finished_lot":
        affected_finished.add(trigger_id)
    else:
        return {"error":f"Unsupported trigger_type: {trigger_type}"}

    affected_deliveries = [d for fid in sorted(affected_finished) for d in finished_to_deliveries.get(fid, [])]
    customers = sorted({d["customer_id"] for d in affected_deliveries})
    affected_quantity = sum(int(d["quantity_delivered"]) for d in affected_deliveries)
    actions = [a for a in data.get("recall_actions", []) if a["recall_id"] == case["recall_id"]]
    recovered_quantity = sum(int(a["quantity"]) for a in actions if a["action_type"] == "recover" and a["status"] == "completed")
    return {
        "recall_id":case["recall_id"], "trigger_type":trigger_type, "trigger_lot_id":trigger_id,
        "affected_finished_lots":sorted(affected_finished),
        "affected_deliveries":[d["delivery_id"] for d in affected_deliveries],
        "affected_customers":customers, "affected_customer_count":len(customers),
        "affected_delivery_count":len(affected_deliveries), "affected_delivered_quantity":affected_quantity,
        "recovered_quantity":recovered_quantity,
        "unrecovered_delivered_quantity":max(0, affected_quantity-recovered_quantity),
        "recall_actions":actions
    }
