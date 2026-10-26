import math
import os
import tempfile
import unittest

from logic.c_chart import calculate_c_chart
from logic.imr_chart import control_limits
from logic.imr_chart import check_nelson_rules as check_imr_rules
from logic.nelson_rules import check_nelson_rules, localize_chart_results, localize_violations, rule_details
from logic.np_chart import calculate_np_chart
from logic.np_chart import check_nelson_rules as check_np_rules
from logic.np_chart import build_horizontal_groups as build_np_groups
from logic.p_chart import calculate_p_chart
from logic.p_chart import check_nelson_rules as check_p_rules
from logic.p_chart import build_horizontal_groups as build_p_groups
from logic.u_chart import calculate_u_chart
from logic.u_chart import check_nelson_rules as check_u_rules
from logic.validation import numeric_values
from logic.xbar_r import (
    build_horizontal_subgroups as build_r_groups,
    build_vertical_subgroups as build_r_vertical,
    calculate_xbar_r,
    generate_recommendation as recommend_r,
)
from logic.xbar_s import (
    build_horizontal_subgroups as build_s_groups,
    build_vertical_subgroups as build_s_vertical,
    calculate_xbar_s,
    generate_recommendation as recommend_s,
)
from logic.c_chart import check_nelson_rules as check_c_rules
from logic.xbar_r import check_nelson_rules as check_xbar_r_rules
from logic.xbar_s import check_nelson_rules as check_xbar_s_rules
from models.analysis import Analysis
from project_managers.project_manager import ProjectManager
from ui.sheet import Sheet


class FakeSheet:
    def __init__(self, rows):
        self.rows = rows

    def get_sheet_data(self):
        return self.rows


def rule_ids(data, *, mean=0.0, sigma=1.0):
    found = check_nelson_rules(data, mean, mean + 3 * sigma, mean - 3 * sigma)
    return {item[0] for item in found}


class UChartTests(unittest.TestCase):
    def test_poisson_limits_vary_with_each_sample_size(self):
        result = calculate_u_chart([2, 4], [10, 20])
        self.assertEqual(result["u_values"], [0.2, 0.2])
        self.assertTrue(math.isclose(result["u_bar"], 0.2, abs_tol=1e-12))
        self.assertEqual(len(result["ucls"]), 2)
        self.assertTrue(math.isclose(result["ucls"][0], 0.6242640687119285, rel_tol=1e-12))
        self.assertTrue(math.isclose(result["ucls"][1], 0.5, rel_tol=1e-12))
        self.assertEqual(result["lcls"], [0.0, 0.0])

    def test_equal_sample_sizes_have_equal_limits(self):
        result = calculate_u_chart([2, 4], [10, 10])
        self.assertEqual(result["ucls"][0], result["ucls"][1])
        self.assertEqual(result["lcls"][0], result["lcls"][1])

    def test_rejects_empty_mismatched_negative_zero_and_nonfinite_inputs(self):
        invalid = [
            ([], [], "required"),
            ([1], [1, 2], "equal lengths"),
            ([-1], [2], "nonnegative"),
            ([1], [0], "positive"),
            ([float("nan")], [1], "non-finite"),
            ([1], [float("inf")], "non-finite"),
        ]
        for defects, sizes, expected in invalid:
            with self.subTest(defects=defects, sizes=sizes):
                with self.assertRaisesRegex(ValueError, expected):
                    calculate_u_chart(defects, sizes)

    def test_other_modes_keep_explicit_legacy_assumptions(self):
        normal = calculate_u_chart([2, 4], [10, 20], "Normal")
        self.assertEqual(normal["ucls"][0], normal["ucls"][1])
        binomial = calculate_u_chart([2, 4], [10, 20], "Binomial")
        self.assertEqual(len(binomial["ucls"]), 2)
        self.assertNotEqual(binomial["ucls"][0], binomial["ucls"][1])
        with self.assertRaisesRegex(ValueError, "not to exceed"):
            calculate_u_chart([3], [2], "Binomial")
        with self.assertRaisesRegex(ValueError, "at least two"):
            calculate_u_chart([2], [10], "Normal")
        with self.assertRaisesRegex(ValueError, "Distribution"):
            calculate_u_chart([1], [10], "unknown")


class NelsonRuleTests(unittest.TestCase):
    def test_rule_messages_and_explanations_follow_active_language(self):
        english = check_nelson_rules([4], 0, 3, -3, language="en")
        indonesian = check_nelson_rules([4], 0, 3, -3, language="id")
        self.assertIn("Point", english[0][2])
        self.assertIn("Titik", indonesian[0][2])
        self.assertIn("special cause", rule_details("Rule 1", "en")["recommendation"])
        self.assertIn("penyebab", rule_details("Rule 1", "id")["recommendation"].lower())
        # Saved analysis records are refreshed when reopened in another language.
        saved = [{"rule": "Rule 1", "point": 1, "description": indonesian[0][2], "cause": "old"}]
        self.assertIn("Point", localize_violations(saved, "en")[0]["description"])

    def test_saved_analysis_summary_and_recommendation_refresh_in_active_language(self):
        saved = [{"result": {"ranges": [1]}, "xbar_violations": [
            {"rule": "Rule 1", "point": 1, "description": "old", "cause": "old"}],
            "s_violations": [], "interpretation": "old", "recommendation": "old"}]
        localize_chart_results(saved, "en")
        self.assertIn("Total violations", saved[0]["interpretation"])
        self.assertIn("special cause", saved[0]["recommendation"])
        localize_chart_results(saved, "id")
        self.assertIn("Total pelanggaran", saved[0]["interpretation"])
        self.assertIn("Penyebab", saved[0]["recommendation"])

    def test_rule_1_positive_and_exact_limit_negative(self):
        self.assertIn("Rule 1", rule_ids([3.01]))
        self.assertNotIn("Rule 1", rule_ids([3.0, -3.0]))

    def test_rule_2_nine_points_and_center_line_break(self):
        result = check_nelson_rules([1] * 9, 0, 3, -3)
        self.assertEqual([item[1] for item in result if item[0] == "Rule 2"], [9])
        self.assertNotIn("Rule 2", rule_ids([1] * 8 + [0, 1]))

    def test_rule_3_six_monotonic_points_and_ties_break(self):
        self.assertIn("Rule 3", rule_ids([0.1, 0.2, 0.3, 0.4, 0.5, 0.6]))
        self.assertNotIn("Rule 3", rule_ids([0, 1, 2, 2, 3, 4, 5]))

    def test_rule_4_requires_fourteen_points_and_marks_overlaps(self):
        self.assertNotIn("Rule 4", rule_ids([0, 1] * 6 + [0]))
        found = [item[1] for item in check_nelson_rules([0, 1] * 8, 0.5, 100, -100)
                 if item[0] == "Rule 4"]
        self.assertEqual(found, [14, 15, 16])

    def test_rule_5_requires_same_side_and_overlapping_windows(self):
        self.assertNotIn("Rule 5", rule_ids([2.1, -2.1, 0]))
        found = [item[1] for item in check_nelson_rules([2.1, 2.2, 0, 2.3], 0, 3, -3)
                 if item[0] == "Rule 5"]
        self.assertEqual(found, [3, 4])
        self.assertNotIn("Rule 5", rule_ids([2.0, 2.1, 0]))

    def test_rule_6_requires_same_side_and_strictly_beyond_one_sigma(self):
        self.assertNotIn("Rule 6", rule_ids([1.1, -1.1, 1.1, -1.1, 0]))
        self.assertIn("Rule 6", rule_ids([1.1, 1.2, 1.3, 1.4, 0]))
        self.assertNotIn("Rule 6", rule_ids([1.0, 1.1, 1.2, 1.3, 0]))

    def test_rule_7_includes_one_sigma_boundary_and_excludes_outside(self):
        boundary_pattern = [1, 1, 0, -1, -1, 0, 1, 0, -1, 0, 1, -1, 0, 1, -1]
        inside_pattern = [value * 0.999 for value in boundary_pattern]
        outside_pattern = boundary_pattern.copy()
        outside_pattern[4] = -1.001
        self.assertEqual(rule_ids(boundary_pattern), {"Rule 7"})
        self.assertEqual(rule_ids(inside_pattern), {"Rule 7"})
        self.assertNotIn("Rule 7", rule_ids(outside_pattern))

    def test_rule_8_detects_both_sides_without_rule_6_false_positive(self):
        data = [1.1, 1.2, -1.1, -1.2] * 2
        self.assertEqual(rule_ids(data), {"Rule 8"})

    def test_variable_sigma_is_applied_per_observation(self):
        result = calculate_u_chart([2, 4], [10, 20])
        found = check_nelson_rules(result["u_values"], result["u_bar"],
                                   result["ucls"], result["lcls"])
        self.assertIsInstance(found, list)
        with self.assertRaisesRegex(ValueError, "length must match"):
            check_nelson_rules([0, 0], 0, [3], [-3, -3])
        with self.assertRaisesRegex(ValueError, "non-finite"):
            check_nelson_rules([float("inf")], 0, 3, -3)

    def test_chart_adapters_share_rule_results_and_keep_result_shapes(self):
        data = [1.1, -1.1, 1.1, -1.1, 0]
        checks = [
            (check_imr_rules, (data, 0, 3, -3), "tuple"),
            (check_xbar_r_rules, (data, 0, 3, -3), "dict"),
            (check_xbar_s_rules, (data, 0, 3, -3), "dict"),
            (check_p_rules, (data, 0, [3] * 5, [-3] * 5), "dict"),
            (check_np_rules, (data, 0, 3, -3), "dict"),
            (check_c_rules, (data, 0, 3, -3), "dict"),
            (check_u_rules, (data, 0, [3] * 5, [-3] * 5), "dict"),
        ]
        for function, args, output_type in checks:
            with self.subTest(function=function.__module__):
                result = function(*args)
                if output_type == "tuple":
                    rules = {item[0] for item in result}
                else:
                    self.assertTrue(all({"rule", "point", "description", "cause"} <= item.keys()
                                        for item in result))
                    rules = {item["rule"] for item in result}
                self.assertNotIn("Rule 6", rules)

    def test_xbar_interpretations_recommend_for_all_eight_rules(self):
        for recommend in (recommend_r, recommend_s):
            for rule in ("Rule 4", "Rule 7", "Rule 8"):
                with self.subTest(recommend=recommend.__module__, rule=rule):
                    result = recommend([{"rule": rule}], [])
                    self.assertIn("-", result)
                    self.assertNotIn("Continue monitoring", result)


class ExportAndDependencyTests(unittest.TestCase):
    def test_application_ui_and_project_manager_import(self):
        import ui.ui
        import project_managers.project_manager

        self.assertIsNotNone(ui.ui.UI)
        self.assertIsNotNone(project_managers.project_manager.ProjectManager)

    def test_excel_engine_and_manifest_dependencies_are_available(self):
        import importlib.metadata
        import pandas as pd

        self.assertEqual(importlib.metadata.version("pandas"), "3.0.3")
        self.assertEqual(importlib.metadata.version("openpyxl"), "3.1.5")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "uji.xlsx")
            pd.DataFrame({"C1": [1, 2], "C2": [3, 4]}).to_excel(path, index=False)
            result = pd.read_excel(path, engine="openpyxl")
            self.assertEqual(result.values.tolist(), [[1, 3], [2, 4]])

    def test_pdf_exporter_creates_valid_pdf_for_saved_analysis(self):
        analysis = Analysis(
            analysis_type="c-chart",
            title="Uji — Cárt",
            data={"counts": [1, 2, 3]},
            stats={"c_bar": 2.0, "ucl": 6.2426, "lcl": 0.0},
            settings={"column": "C1"},
            navigator_name="Uji PDF",
        )
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "laporan.pdf")
            ProjectManager._write_report_pdf(path, [analysis])
            with open(path, "rb") as report_file:
                self.assertEqual(report_file.read(4), b"%PDF")
            self.assertGreater(os.path.getsize(path), 1000)


class InputValidationTests(unittest.TestCase):
    def test_numeric_values_rejects_internal_blank_text_nan_and_infinity(self):
        for values in ([1, "", 2], [1, "oops"], [float("nan")], [float("inf")]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    numeric_values(values)
        self.assertEqual(numeric_values([1, 2, "", None]), [1.0, 2.0])

    def test_vertical_subgroups_preserve_rows_and_reject_missing_cells(self):
        rows = [[1, 2], [3, 4]]
        self.assertEqual(build_r_vertical(FakeSheet(rows), [0, 1]), [[1, 2], [3, 4]])
        self.assertEqual(build_s_vertical(FakeSheet(rows), [0, 1]), [[1, 2], [3, 4]])
        for builder in (build_r_vertical, build_s_vertical):
            with self.subTest(builder=builder.__module__):
                with self.assertRaisesRegex(ValueError, "row 2, column C2"):
                    builder(FakeSheet([[1, 2], [3, ""], [4, 5]]), [0, 1])
                with self.assertRaisesRegex(ValueError, "row 2, column C2"):
                    builder(FakeSheet([[1, 2], [3, "bad"]]), [0, 1])
                with self.assertRaisesRegex(ValueError, "non-finite"):
                    builder(FakeSheet([[1, 2], [3, float("inf")]]), [0, 1])

    def test_horizontal_subgroups_reject_incomplete_and_invalid_values(self):
        self.assertEqual(build_r_groups([1, 2, 3, 4], 2), [[1, 2], [3, 4]])
        self.assertEqual(build_s_groups([1, 2, 3, 4], 2), [[1, 2], [3, 4]])
        for builder in (build_r_groups, build_s_groups):
            with self.assertRaisesRegex(ValueError, "Incomplete final subgroup"):
                builder([1, 2, 3], 2)
            with self.assertRaisesRegex(ValueError, "row 2"):
                builder([1, "bad", 3, 4], 2)

    def test_attribute_group_builders_reject_incomplete_subgroups(self):
        self.assertEqual(build_p_groups([0, 1, 1, 0], 2), [[0.0, 1.0], [1.0, 0.0]])
        self.assertEqual(build_np_groups([0, 1, 1, 0], 2), [[0.0, 1.0], [1.0, 0.0]])
        for builder in (build_p_groups, build_np_groups):
            with self.assertRaisesRegex(ValueError, "Incomplete final subgroup"):
                builder([0, 1, 0], 2)

    def test_sheet_column_read_keeps_internal_blank_rows(self):
        sheet = object.__new__(Sheet)
        sheet.sheet = FakeSheet([[1], [""], [3], [""], [""]])
        self.assertEqual(sheet.get_column_data(0), [1, "", 3])
        self.assertEqual(sheet.get_column_data_with_rows(0), [(1, 1), (2, ""), (3, 3)])

    def test_xbar_calculators_validate_empty_ragged_and_nonfinite_subgroups(self):
        for calculate in (calculate_xbar_r, calculate_xbar_s):
            with self.subTest(calculate=calculate.__name__):
                for data in ([], [[1, 2], [3]], [[1, float("nan")], [2, 3]]):
                    with self.assertRaises(ValueError):
                        calculate(data)

    def test_attribute_charts_validate_empty_domains_and_nonfinite_data(self):
        invalid_calls = [
            (calculate_p_chart, []),
            (calculate_p_chart, [[0, 2]]),
            (calculate_np_chart, []),
            (calculate_np_chart, [[0, 1], [0]]),
            (calculate_c_chart, []),
            (calculate_c_chart, [1, float("nan")]),
            (control_limits, []),
            (control_limits, [1]),
            (control_limits, [1, float("inf")]),
        ]
        for function, argument in invalid_calls:
            with self.subTest(function=function.__name__, argument=argument):
                with self.assertRaises(ValueError):
                    function(argument)

    def test_chart_output_keys_remain_compatible(self):
        r_result = calculate_xbar_r([[1, 2], [2, 3]])
        s_result = calculate_xbar_s([[1, 2], [2, 3]])
        p_result = calculate_p_chart([[0, 1], [1, 0]])
        np_result = calculate_np_chart([[0, 1], [1, 0]])
        c_result = calculate_c_chart([1, 2])
        u_result = calculate_u_chart([1, 2], [10, 10])
        self.assertTrue({"xbars", "ranges", "xbar_bar", "r_bar", "xbar_ucl", "xbar_lcl", "r_ucl", "r_lcl", "subgroup_size"} <= r_result.keys())
        self.assertTrue({"xbars", "stds", "xbar_bar", "s_bar", "xbar_ucl", "xbar_lcl", "s_ucl", "s_lcl", "subgroup_size"} <= s_result.keys())
        self.assertTrue({"proportions", "subgroup_sizes", "p_bar", "ucls", "lcls"} <= p_result.keys())
        self.assertTrue({"defect_counts", "np_bar", "ucl", "lcl", "subgroup_size", "p_bar"} <= np_result.keys())
        self.assertTrue({"counts", "c_bar", "ucl", "lcl"} <= c_result.keys())
        self.assertTrue({"u_values", "sample_sizes", "u_bar", "ucls", "lcls", "distribution"} <= u_result.keys())


if __name__ == "__main__":
    unittest.main()
