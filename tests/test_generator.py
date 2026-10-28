import unittest
from src.data_generator import generate_data

SCALE = {"suppliers":4, "raw_lots":12, "production_orders":6, "finished_lots":8, "deliveries":10}

class TestGenerator(unittest.TestCase):
    def test_expected_baseline_counts(self):
        data = generate_data(SCALE, seed=123)
        self.assertEqual(len(data["suppliers"]), 4)
        self.assertEqual(len(data["material_lots"]), 12)
        self.assertEqual(len(data["production_orders"]), 6)
        self.assertEqual(len(data["finished_lots"]), 8)

    def test_fixed_seed_reproducible(self):
        a = generate_data(SCALE, seed=123)
        b = generate_data(SCALE, seed=123)
        self.assertEqual(a, b)

if __name__ == "__main__":
    unittest.main()
