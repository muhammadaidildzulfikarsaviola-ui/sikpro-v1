import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import logic.xbar_r as xbar_r
from logic.xbar_r import XbarRChartPopup, XbarRConfigPopup
from logic.u_chart import UChartConfigPopup, UChartConvertedPopup, UChartPopup
from ui.control_chart_guide import ControlChartGuide, GUIDANCE, ROUTES
from logic.imr_chart import IMRConfigPopup
from logic.xbar_s import XbarSConfigPopup
from logic.p_chart import PChartConfigPopup
from logic.np_chart import NPChartConfigPopup
from logic.c_chart import CChartConfigPopup


class ChartHost:
    def __init__(self, root):
        self.root = root
        self.chart_canvas = tk.Frame(root)
        self.active_chart = None

    def prepare_chart_view(self):
        if self.active_chart is not None:
            self.active_chart.destroy()
            self.active_chart = None

    def activate_chart_view(self, chart):
        self.active_chart = chart

    def set_chart_title(self, _title):
        pass

    def chart_view_destroyed(self, chart):
        if self.active_chart is chart:
            self.active_chart = None


class ChartSheet:
    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows

    def get_column_names(self):
        return self.columns

    def get_column_data(self, column):
        return [row[column] for row in self.rows]

    def get_sheet_data(self):
        return self.rows


class XbarRWorkflowGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.geometry("1000x700+40+40")
            self.root.update()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.host = ChartHost(self.root)
        self.root._sikpro_chart_host = self.host
        self.main = SimpleNamespace(
            root=self.root,
            current_lang="en",
            t=lambda key: key,
            navigator=SimpleNamespace(add_analysis=lambda _analysis, **_kwargs: None),
        )

    def tearDown(self):
        try:
            self.root.destroy()
        except (AttributeError, tk.TclError):
            pass

    def _run_generation(self, sheet, mode):
        config = XbarRConfigPopup(self.main, sheet)
        self.root.update()
        if mode == "horizontal":
            config.column_listbox.selection_set(0)
            config.select_column()
            config.subgroup_size_var.set("5")
        else:
            for index in range(len(sheet.columns)):
                config.column_listbox.selection_set(index)
            config.select_column()
            config.mode_var.set("vertical")
        calls = []
        real_check = xbar_r.check_nelson_rules

        def record_check(*args, **kwargs):
            calls.append(args)
            return real_check(*args, **kwargs)

        with patch("logic.xbar_r.check_nelson_rules", side_effect=record_check), \
                patch("tkinter.messagebox.showerror") as showerror:
            config.generate()
            self.assertFalse(showerror.called, "valid chart generation showed an error")
        self.root.update()
        return config, calls

    def test_horizontal_and_vertical_generate_use_correct_r_chart_limits(self):
        one_column = ChartSheet(
            ["Measurements"],
            [[value] for value in (
                10, 12, 11, 9, 10,
                11, 13, 12, 10, 11,
                12, 14, 13, 11, 12,
                13, 15, 14, 12, 13,
            )],
        )
        horizontal_config, horizontal_checks = self._run_generation(one_column, "horizontal")
        self.assertFalse(horizontal_config.winfo_exists())
        self.assertIsInstance(self.host.active_chart, XbarRChartPopup)
        horizontal_result = self.host.active_chart.results[0]["result"]
        self.assertEqual(horizontal_checks[1][2], horizontal_result["r_ucl"])
        self.assertEqual(horizontal_checks[1][3], horizontal_result["r_lcl"])
        self.host.active_chart.destroy()

        across_columns = ChartSheet(
            ["M1", "M2", "M3", "M4", "M5"],
            [
                [10, 12, 11, 9, 10],
                [11, 13, 12, 10, 11],
                [12, 14, 13, 11, 12],
                [13, 15, 14, 12, 13],
            ],
        )
        vertical_config, vertical_checks = self._run_generation(across_columns, "vertical")
        self.assertFalse(vertical_config.winfo_exists())
        self.assertIsInstance(self.host.active_chart, XbarRChartPopup)
        vertical_result = self.host.active_chart.results[0]["result"]
        self.assertEqual(vertical_checks[1][2], vertical_result["r_ucl"])
        self.assertEqual(vertical_checks[1][3], vertical_result["r_lcl"])

    def test_guide_localizes_all_supported_routes_and_routes_to_existing_dialogs(self):
        expected = {
            "imr": IMRConfigPopup,
            "xbar_r": XbarRConfigPopup,
            "xbar_s": XbarSConfigPopup,
            "p": PChartConfigPopup,
            "np": NPChartConfigPopup,
            "c": CChartConfigPopup,
            "u_raw": UChartConfigPopup,
            "u_converted": UChartConvertedPopup,
        }
        self.assertEqual(ROUTES, expected)
        self.assertEqual(set(GUIDANCE["en"]), set(GUIDANCE["id"]))
        self.assertEqual(len(GUIDANCE["en"]), 8)
        guide = ControlChartGuide(self.main, ChartSheet(["Value"], [[1], [2]]))
        self.assertEqual(guide.language, "en")
        guide.choices.selection_clear(0, "end")
        guide.choices.selection_set(7)
        guide._show_selected()
        self.assertIn("sample standard deviations", guide.details.get("1.0", "end"))
        guide.destroy()
        self.main.current_lang = "id"
        guide = ControlChartGuide(self.main, ChartSheet(["Nilai"], [[1], [2]]))
        self.assertEqual(guide.language, "id")
        self.assertIn("Pilih", guide.title())
        guide.choices.selection_clear(0, "end")
        guide.choices.selection_set(7)
        guide._show_selected()
        self.assertIn("simpangan baku sampel", guide.details.get("1.0", "end"))
        guide.destroy()

    def test_each_guide_selection_invokes_its_selected_chart_route(self):
        sheet = ChartSheet(["Value"], [[1], [2]])
        for index, key in enumerate(tuple(ROUTES)):
            guide = ControlChartGuide(self.main, sheet)
            self.root.update()
            guide.choices.selection_clear(0, "end")
            guide.choices.selection_set(index)
            opened = []

            def route(main, selected_sheet):
                opened.append((main, selected_sheet))
                return tk.Toplevel(self.root)

            with patch.dict(ROUTES, {key: route}):
                result = guide.open_selected()
            self.assertEqual(opened, [(self.main, sheet)], key)
            self.assertFalse(guide.winfo_exists(), key)
            result.destroy()
        self.assertEqual(sheet.rows, [[1], [2]])

    def test_converted_u_dialog_has_no_distribution_selector_and_sends_method_metadata(self):
        sheet = ChartSheet(["U rate"], [[0.04], [0.05], [0.03]])
        popup = UChartConvertedPopup(self.main, sheet)
        self.root.update()
        self.assertFalse(hasattr(popup, "distribution_var"))
        popup.column_listbox.selection_set(0)
        popup.set_converted_column()

        with patch("logic.u_chart.UChartPopup", return_value=object()) as chart_popup:
            popup.generate()
        self.assertFalse(popup.winfo_exists())
        args, kwargs = chart_popup.call_args
        self.assertIsNone(kwargs["distribution"])
        self.assertEqual(kwargs["calculation_method_key"], "converted_sample_sd")
        self.assertEqual(args[1]["calculation_method"], "converted_sample_sd")
        self.assertAlmostEqual(args[1]["u_bar"], 0.04)
        self.assertAlmostEqual(args[1]["ucls"][0], 0.07)
        self.assertAlmostEqual(args[1]["lcls"][0], 0.01)

    def test_converted_u_result_labels_and_saves_actual_limit_method(self):
        result = {
            "u_values": [0.04, 0.05, 0.03],
            "u_bar": 0.04,
            "ucls": [0.0645] * 3,
            "lcls": [0.0155] * 3,
        }
        added = []
        self.main.navigator.add_analysis = lambda analysis: added.append(analysis)
        popup = UChartPopup(
            self.main, result, [], "U rate", distribution=None,
            calculation_method_key="converted_sample_sd",
        )
        self.root.update()
        self.assertEqual(added[0].settings["calculation_method"], "converted_sample_sd")
        self.assertIsNone(added[0].settings["distribution"])
        popup.destroy()

    def test_raw_u_chart_keeps_distribution_selector_and_saved_setting(self):
        added = []
        self.main.navigator.add_analysis = lambda analysis: added.append(analysis)
        sheet = ChartSheet(
            ["Defects", "Units"],
            [[4, 100], [6, 150], [3, 80]],
        )
        config = UChartConfigPopup(self.main, sheet)
        self.root.update()
        self.assertTrue(hasattr(config, "distribution_var"))
        config.column_listbox.selection_set(0)
        config.set_defect_column()
        config.column_listbox.selection_clear(0, "end")
        config.column_listbox.selection_set(1)
        config.set_sample_column()
        with patch("tkinter.messagebox.showerror") as showerror:
            config.generate()
        self.assertFalse(showerror.called)
        self.assertFalse(config.winfo_exists())
        self.assertEqual(self.host.active_chart.distribution, "Poisson")
        self.assertEqual(added[0].settings["distribution"], "Poisson")
        self.assertIsNone(added[0].settings["calculation_method"])
        self.host.active_chart.destroy()

    def test_invalid_attribute_size_keeps_both_configurations_usable(self):
        for config_type in (PChartConfigPopup, NPChartConfigPopup):
            popup = config_type(self.main, ChartSheet(["Defective"], [[0], [1], [0], [0]]))
            self.root.update()
            popup.column_listbox.selection_set(0)
            popup.select_column()
            popup.subgroup_var.set("not a size")
            with patch("tkinter.messagebox.showerror") as showerror:
                popup.generate()
            self.assertTrue(showerror.called)
            self.assertTrue(popup.winfo_exists())
            self.assertEqual(popup.selected_columns, ["Defective"])
            self.assertEqual(popup.subgroup_var.get(), "not a size")
            popup.destroy()

    def test_closing_guide_does_not_change_sheet_data(self):
        sheet = ChartSheet(["Measurement"], [[1.2], [1.3], [1.1]])
        before = [row[:] for row in sheet.rows]
        guide = ControlChartGuide(self.main, sheet)
        self.root.update()
        guide.destroy()
        self.assertEqual(sheet.rows, before)


if __name__ == "__main__":
    unittest.main()
