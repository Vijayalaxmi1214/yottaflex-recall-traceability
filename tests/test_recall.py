import unittest
from src.data_generator import generate_data
from src.recall_engine import simulate_recall

class TestRecall(unittest.TestCase):
    def test_recall_report_has_expected_fields(self):
        scale = {"suppliers":4, "raw_lots":12, "production_orders":6, "finished_lots":8, "deliveries":10}
        data = generate_data(scale, seed=123)
        report = simulate_recall(data)
        self.assertIn("affected_finished_lots", report)
        self.assertIn("affected_customers", report)
        self.assertIn("affected_delivered_quantity", report)

    def test_unrecovered_calculation(self):
        scale = {"suppliers":4, "raw_lots":12, "production_orders":6, "finished_lots":8, "deliveries":10}
        data = generate_data(scale, seed=123)
        report = simulate_recall(data)
        self.assertEqual(
            report["unrecovered_delivered_quantity"],
            max(0, report["affected_delivered_quantity"] - report["recovered_quantity"])
        )

if __name__ == "__main__":
    unittest.main()
