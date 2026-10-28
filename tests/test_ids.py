import unittest
from src.id_generator import raw_lot_id, production_order_id, finished_lot_id, shipment_id, recall_id

class TestIDs(unittest.TestCase):
    def test_id_formats(self):
        self.assertEqual(raw_lot_id("SUP-0001", 1), "RAWLOT-SUP-0001-2026-000001")
        self.assertEqual(production_order_id(1), "WO-2026-000001")
        self.assertEqual(finished_lot_id(1), "FINLOT-2026-000001")
        self.assertEqual(shipment_id(1), "SHP-2026-000001")
        self.assertEqual(recall_id(1), "REC-2026-000001")

if __name__ == "__main__":
    unittest.main()
