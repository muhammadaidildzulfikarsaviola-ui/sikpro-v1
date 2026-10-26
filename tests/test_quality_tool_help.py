import tkinter as tk
import unittest
from types import SimpleNamespace
from tkinter import ttk

from help.quality_tool_help import QUALITY_TOOL_HELP
from models.quality_tools import default_tool_models
from ui.quality_tools import QualityToolHelpDialog, ToolView
from ui.theme import PALETTES


class QualityToolHelpContentTests(unittest.TestCase):
    def test_help_exists_in_both_languages_for_each_tool(self):
        expected_tools = {"fishbone", "check_sheet", "defect_concentration"}
        self.assertEqual(set(QUALITY_TOOL_HELP), {"en", "id"})
        for language in QUALITY_TOOL_HELP.values():
            self.assertEqual(set(language), expected_tools)
            for content in language.values():
                self.assertTrue(content["purpose"].strip())
                self.assertGreaterEqual(len(content["steps"]), 4)
                self.assertTrue(all(step.strip() for step in content["steps"]))
                self.assertTrue(content["next"].strip())

    def test_help_describes_actual_exports_persistence_and_mark_deletion(self):
        check_sheet = QUALITY_TOOL_HELP["en"]["check_sheet"]
        self.assertIn("no PNG, PDF", check_sheet["next"])
        concentration = " ".join(QUALITY_TOOL_HELP["en"]["defect_concentration"]["steps"])
        self.assertIn("Delete selected mark", concentration)
        self.assertIn("File → Save", concentration)
        fishbone = " ".join(QUALITY_TOOL_HELP["en"]["fishbone"]["steps"])
        self.assertIn("hypotheses", QUALITY_TOOL_HELP["en"]["fishbone"]["purpose"])
        self.assertIn("PNG or PDF", fishbone)


class QualityToolHelpGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.geometry("760x540+80+70")
            self.root.update()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.models = default_tool_models("en")
        self.models["fishbone"].effect = "Seal leakage"
        category = self.models["fishbone"].categories[0]["id"]
        self.models["fishbone"].add_cause(category, "Worn seal")
        check_category = self.models["check_sheet"].add_category("Scratch")
        self.models["check_sheet"].add_record(check_category, 3, "2026-10-27", "Batch 8", "Left edge")
        defect_category = self.models["defect_concentration"].default_category_id
        self.models["defect_concentration"].add_mark(defect_category, .27, .64, "Upper edge")
        self.before = {key: model.to_dict() for key, model in self.models.items()}
        self.labels = {
            "fishbone": "Fishbone", "check_sheet": "Check Sheet",
            "defect_concentration": "Defect Concentration",
            "quality_tool_help": "How to use", "quality_help_purpose": "Purpose",
            "quality_help_steps": "Steps", "quality_help_next": "Example and next step",
            "quality_help_close": "Close",
        }
        self.main = SimpleNamespace(
            root=self.root, current_lang="en", tool_models=self.models,
            theme_manager=SimpleNamespace(palette=PALETTES["light"]),
            t=lambda key: self.labels.get(key, key),
        )
        self.host = SimpleNamespace()
        self.host.chart_canvas = tk.Frame(self.root)
        self.host.workspace_title = ttk.Label(self.root)
        self.host.context_title = ttk.Label(self.root)
        self.host.context_help = ttk.Label(self.root)
        self.host.context_tool_help_button = ttk.Button(self.root)
        self.host.prepare_chart_view = lambda: None
        self.host.activate_chart_view = lambda _view: None
        self.host.set_active_navigation = lambda _key: None
        self.root._sikpro_chart_host = self.host

    def tearDown(self):
        try:
            self.root.destroy()
        except (AttributeError, tk.TclError):
            pass

    def test_opening_and_closing_help_preserves_tool_data(self):
        for key in ("fishbone", "check_sheet", "defect_concentration"):
            with self.subTest(tool=key):
                dialog = QualityToolHelpDialog(self.main, key)
                self.root.update()
                rendered = dialog.content.get("1.0", "end-1c")
                self.assertIn("Purpose", rendered)
                self.assertIn("Steps", rendered)
                dialog.destroy()
                self.root.update()
                self.assertEqual(
                    {model_key: model.to_dict() for model_key, model in self.models.items()},
                    self.before,
                )

    def test_in_tool_context_help_button_opens_and_closes_without_changing_models(self):
        class CheckSheetHelpHarness(ToolView):
            def __init__(self, main):
                super().__init__(main, "check_sheet", "check_sheet", "check_sheet_help")

        view = CheckSheetHelpHarness(self.main)
        self.root.update()
        self.host.context_tool_help_button.invoke()
        self.root.update()
        dialog = view._help_dialog
        self.assertTrue(dialog.winfo_exists())
        self.assertIn("Check Sheet", dialog.content.get("1.0", "end-1c"))
        dialog.close_button.invoke()
        self.root.update()
        self.assertFalse(dialog.winfo_exists())
        self.assertEqual(
            {key: model.to_dict() for key, model in self.models.items()}, self.before
        )
        view.destroy()


if __name__ == "__main__":
    unittest.main()
