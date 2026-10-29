import math
import unittest

from inventory.calculators import calculate_eoq, calculate_mrp, calculate_rop


class EOQTests(unittest.TestCase):
    def test_known_result_and_cost_components(self):
        result = calculate_eoq(1000, 50, 2, 250)
        self.assertAlmostEqual(result["eoq"], math.sqrt(50000))
        self.assertAlmostEqual(result["orders_per_year"], 1000 / math.sqrt(50000))
        self.assertAlmostEqual(result["order_interval_days"], 250 / result["orders_per_year"])
        self.assertAlmostEqual(result["annual_ordering_cost"], result["annual_holding_cost"])
        self.assertAlmostEqual(result["relevant_annual_cost"], result["annual_ordering_cost"] * 2)

    def test_rejects_zero_negative_and_nonfinite_inputs(self):
        for args in ((0, 1, 1), (-1, 1, 1), (1, 0, 1), (1, 1, 0), (float("nan"), 1, 1), (1, float("inf"), 1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                calculate_eoq(*args)

    def test_purchase_price_is_optional_and_does_not_change_eoq(self):
        base = calculate_eoq(1000, 50, 2, 250)
        with_price = calculate_eoq(1000, 50, 2, 250, 4)
        self.assertAlmostEqual(base["eoq"], with_price["eoq"])
        self.assertAlmostEqual(with_price["annual_purchase_cost"], 4000)
        self.assertAlmostEqual(with_price["total_annual_cost"], with_price["relevant_annual_cost"] + 4000)
        self.assertEqual(calculate_eoq(1000, 50, 2, unit_purchase_price=0)["annual_purchase_cost"], 0)

    def test_operating_days_integer_and_extreme_values_are_validated(self):
        with self.assertRaisesRegex(ValueError, "whole number"):
            calculate_eoq(100, 10, 2, 250.5)
        with self.assertRaises(ValueError):
            calculate_eoq(1e308, 1e308, 1e-308)


class ROPTests(unittest.TestCase):
    def test_without_and_with_safety_stock(self):
        self.assertEqual(calculate_rop(4, 3), {"rop": 12, "lead_time_demand": 12, "safety_stock": 0})
        self.assertEqual(calculate_rop(4, 3, 5), {"rop": 17, "lead_time_demand": 12, "safety_stock": 5})

    def test_accepts_zero_and_rejects_invalid_values(self):
        self.assertEqual(calculate_rop(0, 2, 0)["rop"], 0)
        for args in ((-1, 1), (1, -1), (1, 1, -1), (float("nan"), 1), (1, float("inf"))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                calculate_rop(*args)


class MRPTests(unittest.TestCase):
    def test_lfl_scheduled_receipts_initial_inventory_and_zero_lead(self):
        result = calculate_mrp([5, 8, 2], 3, [0, 4, 0], 0, "LFL")
        self.assertEqual([r.net_requirements for r in result.rows], [2, 4, 2])
        self.assertEqual([r.planned_order_receipts for r in result.rows], [2, 4, 2])
        self.assertEqual([r.projected_available for r in result.rows], [0, 0, 0])
        self.assertEqual([r.planned_order_releases for r in result.rows], [2, 4, 2])

    def test_foq_and_poq(self):
        foq = calculate_mrp([5, 8, 2], 0, lead_time=0, lot_sizing="FOQ", fixed_order_quantity=6)
        self.assertEqual([r.planned_order_receipts for r in foq.rows], [6, 12, 0])
        self.assertEqual([r.projected_available for r in foq.rows], [1, 5, 3])
        poq = calculate_mrp([2, 3, 4, 1], 0, lot_sizing="POQ", poq_interval=2)
        self.assertEqual([r.planned_order_receipts for r in poq.rows], [5, 0, 5, 0])
        self.assertEqual([r.projected_available for r in poq.rows], [3, 0, 1, 0])

    def test_positive_lead_time_shifts_release_and_warns_before_horizon(self):
        result = calculate_mrp([4, 3], 0, lead_time=1, lot_sizing="LFL")
        self.assertEqual([r.planned_order_releases for r in result.rows], [3, 0])
        self.assertEqual(result.releases_before_horizon, ((0, 4),))

    def test_invalid_shapes_and_parameters(self):
        for args, kwargs in [(([], 0), {}), (([1], 0, [0, 0]), {}), (([1], 0), {"lead_time": 0.5}),
                             (([1], 0), {"lot_sizing": "FOQ"}), (([1], 0), {"lot_sizing": "POQ", "poq_interval": 0})]:
            with self.subTest(args=args, kwargs=kwargs), self.assertRaises(ValueError):
                calculate_mrp(*args, **kwargs)


if __name__ == "__main__":
    unittest.main()
