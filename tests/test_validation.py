
import unittest
from src.data_generator import generate_data
from src.validators import validate


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.scale = {
            "suppliers": 4,
            "raw_lots": 12,
            "production_orders": 6,
            "finished_lots": 8,
            "deliveries": 10,
        }

    def test_anomalies_are_detected(self):
        data = generate_data(
            self.scale,
            seed=123,
            inject_anomalies=True,
        )

        report = validate(data)
        types = {
            issue["type"]
            for issue in report["errors"] + report["warnings"]
        }

        self.assertIn("missing_input_lot", types)
        self.assertIn("delivered_quantity_exceeds_production", types)
        self.assertIn("quarantine_violation", types)
        self.assertIn("report_missing_customer_relationship", types)

    def test_all_ground_truth_anomalies_are_detected(self):
        data = generate_data(
            self.scale,
            seed=20261027,
            inject_anomalies=True,
        )

        report = validate(data)

        detected_types = {
            issue["type"]
            for issue in report["errors"] + report["warnings"]
        }

        expected_types = {
            "missing_input_lot",
            "delivered_quantity_exceeds_production",
            "quarantine_violation",
            "report_missing_customer_relationship",
        }

        self.assertTrue(
            expected_types.issubset(detected_types),
            msg=f"Missing anomaly detections: {expected_types - detected_types}",
        )

        self.assertEqual(len(data["ground_truth"]), 4)

    def test_clean_data_is_valid(self):
        data = generate_data(
            self.scale,
            seed=123,
            inject_anomalies=False,
        )

        report = validate(data)

        self.assertTrue(report["valid"])
        self.assertEqual(report["error_count"], 0)
        self.assertEqual(len(report["errors"]), 0)

    def test_negative_quantity_detection(self):
        data = generate_data(
            self.scale,
            seed=123,
            inject_anomalies=False,
        )

        data["finished_lots"][0]["produced_quantity"] = -10
        data["deliveries"][0]["quantity_delivered"] = -5

        report = validate(data)

        self.assertFalse(report["valid"])

        negative_errors = [
            issue for issue in report["errors"]
            if issue["type"] == "negative_quantity"
        ]

        self.assertGreaterEqual(len(negative_errors), 2)

    def test_invalid_foreign_key_detection(self):
        data = generate_data(
            self.scale,
            seed=123,
            inject_anomalies=False,
        )

        data["material_lots"][0]["supplier_id"] = "SUP-NONEXISTENT"

        report = validate(data)

        self.assertFalse(report["valid"])

        fk_errors = [
            issue for issue in report["errors"]
            if issue["type"] == "invalid_supplier_fk"
        ]

        self.assertEqual(len(fk_errors), 1)


if __name__ == "__main__":
    unittest.main()
