"""Centralized deterministic ID helpers."""
def numbered(prefix: str, number: int, width: int = 6, year: int = 2026) -> str:
    return f"{prefix}-{year}-{number:0{width}d}"

def raw_lot_id(supplier_id: str, number: int, year: int = 2026) -> str:
    return f"RAWLOT-{supplier_id}-{year}-{number:06d}"

def production_order_id(number: int, year: int = 2026) -> str:
    return numbered("WO", number, year=year)

def finished_lot_id(number: int, year: int = 2026) -> str:
    return numbered("FINLOT", number, year=year)

def shipment_id(number: int, year: int = 2026) -> str:
    return numbered("SHP", number, year=year)

def recall_id(number: int, year: int = 2026) -> str:
    return numbered("REC", number, year=year)
