import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.lang import LANG
from logic.c_chart import CChartConfigPopup
from logic.imr_chart import IMRConfigPopup
from logic.np_chart import NPChartConfigPopup
from logic.p_chart import PChartConfigPopup
from logic.u_chart import UChartConfigPopup, UChartConvertedPopup, UChartModePopup
from logic.xbar_r import XbarRConfigPopup
from logic.xbar_s import XbarSConfigPopup


class StubSheet:
    def get_column_names(self):
        return ["Measurement"]

    def get_column_data(self, _index):
        return [1, 2, 3]

    def get_sheet_data(self):
        return [[1], [2], [3]]


class SingleObservationSheet(StubSheet):
    def get_column_data(self, _index):
        return [1]


def widget_texts(widget):
    texts = []
    for child in widget.winfo_children():
        try:
            text = child.cget("text")
            if text:
                texts.append(str(text))
        except tk.TclError:
            pass
        texts.extend(widget_texts(child))
    return texts


class ControlChartDialogLocalizationTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.geometry("1000x700+30+30")
            self.root.update()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.sheet = StubSheet()

    def tearDown(self):
        try:
            self.root.destroy()
        except (AttributeError, tk.TclError):
            pass

    def make_main(self, language):
        return SimpleNamespace(
            root=self.root,
            current_lang=language,
            t=lambda key: LANG[language].get(key, key),
        )

    def test_control_chart_setup_titles_and_labels_follow_active_language(self):
        cases = (
            (PChartConfigPopup, "p_chart", ("available_columns", "chart_selected_columns", "chart_configuration", "chart_subgroup_size", "chart_generate_p")),
            (NPChartConfigPopup, "np_chart", ("available_columns", "chart_selected_columns", "chart_configuration", "chart_subgroup_size", "chart_generate_np")),
            (CChartConfigPopup, "c_chart", ("available_columns", "chart_selected_columns", "chart_generate_c")),
            (XbarRConfigPopup, "xbar_r_chart", ("available_columns", "chart_selected_columns", "chart_configuration", "chart_subgroup_mode", "chart_observations_one_column", "chart_observations_across_columns", "chart_generate_xbar_r")),
            (XbarSConfigPopup, "xbar_s_chart", ("available_columns", "chart_selected_columns", "chart_configuration", "chart_subgroup_mode", "chart_observations_one_column", "chart_observations_across_columns", "chart_generate_xbar_s")),
            (UChartModePopup, "chart_select_u_mode", ("chart_select_data_source", "chart_use_raw_data", "chart_use_converted_data")),
            (UChartConfigPopup, "u_chart", ("available_columns", "chart_distribution", "chart_set_defect_count", "chart_set_sample_size", "chart_generate_u")),
            (UChartConvertedPopup, "chart_converted_u_title", ("chart_using_converted_data", "available_columns", "chart_set_converted_column", "chart_generate_u")),
            (IMRConfigPopup, "imr_chart", ("variables", "select", "generate_imr_chart", "available_columns")),
        )
        for language in ("en", "id"):
            main = self.make_main(language)
            for dialog_class, title_key, label_keys in cases:
                with self.subTest(language=language, dialog=dialog_class.__name__):
                    dialog = dialog_class(main, self.sheet)
                    self.root.update()
                    self.assertEqual(dialog.title(), main.t(title_key))
                    displayed = " ".join(widget_texts(dialog))
                    for key in label_keys:
                        self.assertIn(main.t(key), displayed)
                    dialog.destroy()
                    self.root.update()

    def test_missing_column_validation_uses_active_language(self):
        for language in ("en", "id"):
            main = self.make_main(language)
            with self.subTest(language=language):
                dialog = PChartConfigPopup(main, self.sheet)
                with patch("logic.p_chart.messagebox.showerror") as showerror:
                    dialog.generate()
                self.assertEqual(showerror.call_args.args[0], main.t("error"))
                self.assertEqual(showerror.call_args.args[1], main.t("select_at_least_one_column"))
                dialog.destroy()

    def test_incomplete_subgroup_error_is_localized(self):
        for language in ("en", "id"):
            main = self.make_main(language)
            with self.subTest(language=language):
                dialog = PChartConfigPopup(main, self.sheet)
                dialog.selected_columns = ["Measurement"]
                dialog.numeric_columns = {"Measurement": 0}
                dialog.subgroup_var.set("2")
                with patch("logic.p_chart.messagebox.showerror") as showerror:
                    dialog.generate()
                self.assertEqual(showerror.call_args.args[0], main.t("chart_generate_failed"))
                expected = main.t("chart_validation_incomplete_subgroup").format(count="3", size="2")
                self.assertEqual(showerror.call_args.args[1], expected)
                dialog.destroy()

    def test_subgroup_range_error_is_localized(self):
        for language in ("en", "id"):
            main = self.make_main(language)
            with self.subTest(language=language):
                dialog = XbarRConfigPopup(main, self.sheet)
                dialog.selected_columns = ["Measurement"]
                dialog.numeric_columns = {"Measurement": 0}
                dialog.mode_var.set("horizontal")
                dialog.subgroup_size_var.set("11")
                with patch("logic.xbar_r.messagebox.showerror") as showerror:
                    dialog.generate()
                expected = main.t("chart_validation_subgroup_range").format(
                    minimum="2", maximum="10"
                )
                self.assertEqual(showerror.call_args.args[0], main.t("chart_generate_failed"))
                self.assertEqual(showerror.call_args.args[1], expected)
                dialog.destroy()

    def test_converted_chart_minimum_observations_error_is_localized(self):
        for language in ("en", "id"):
            main = self.make_main(language)
            with self.subTest(language=language):
                dialog = UChartConvertedPopup(main, SingleObservationSheet())
                dialog.converted_column = "Measurement"
                dialog.numeric_columns = {"Measurement": 0}
                with patch("logic.u_chart.messagebox.showerror") as showerror:
                    dialog.generate()
                self.assertEqual(showerror.call_args.args[0], main.t("chart_generate_failed"))
                self.assertEqual(
                    showerror.call_args.args[1],
                    main.t("chart_validation_converted_observations"),
                )
                dialog.destroy()


if __name__ == "__main__":
    unittest.main()
