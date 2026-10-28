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

    def test_help_covers_beginner_requirements_in_both_languages(self):
        required = {
            "en": {
                "check_sheet": ("Add category", "Add record", "grand total"),
                "fishbone": ("problem", "Add cause", "Delete cause", "hypotheses"),
                "defect_concentration": (
                    "inspection area", "Click inside", "Delete selected mark",
                    "same orientation",
                ),
            },
            "id": {
                "check_sheet": ("Tambah kategori", "Tambah catatan", "jumlah total"),
                "fishbone": ("masalah", "Tambah penyebab", "Hapus penyebab", "hipotesis"),
                "defect_concentration": (
                    "area pemeriksaan", "Klik di dalam", "Hapus penanda terpilih",
                    "orientasi yang sama",
                ),
            },
        }
        for language, tools in required.items():
            for tool_key, phrases in tools.items():
                content = QUALITY_TOOL_HELP[language][tool_key]
                searchable = " ".join((content["purpose"], *content["steps"], content["next"]))
                with self.subTest(language=language, tool=tool_key):
                    for phrase in phrases:
                        self.assertIn(phrase.casefold(), searchable.casefold())


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
        self.host.chart_canvas.pack(fill="both", expand=True)
        self.host.workspace_toolbar = tk.Frame(self.root)
        self.host.workspace_toolbar.pack(fill="x")
        self.host.workspace_title = ttk.Label(self.host.workspace_toolbar, text="Workspace")
        self.host.workspace_title.pack(side="left")
        self.host.context_title = ttk.Label(self.root)
        self.host.context_help = ttk.Label(self.root)
        self.host.workspace_tool_help_button = ttk.Button(self.host.workspace_toolbar)
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
        for language, purpose_label, steps_label in (
            ("en", "Purpose", "Steps"),
            ("id", "Tujuan", "Langkah penggunaan"),
        ):
            self.main.current_lang = language
            self.labels.update({
                "quality_help_purpose": purpose_label,
                "quality_help_steps": steps_label,
                "quality_help_next": "Example and next step" if language == "en" else "Contoh dan langkah berikutnya",
                "quality_help_close": "Close" if language == "en" else "Tutup",
            })
            for key in ("fishbone", "check_sheet", "defect_concentration"):
                with self.subTest(language=language, tool=key):
                    dialog = QualityToolHelpDialog(self.main, key)
                    self.root.update()
                    rendered = dialog.content.get("1.0", "end-1c")
                    self.assertIn(purpose_label, rendered)
                    self.assertIn(steps_label, rendered)
                    self.assertIn(QUALITY_TOOL_HELP[language][key]["purpose"], rendered)
                    dialog.destroy()
                    self.root.update()
                    self.assertEqual(
                        {model_key: model.to_dict() for model_key, model in self.models.items()},
                        self.before,
                    )

    def test_each_tool_workspace_help_button_opens_without_changing_models(self):
        class HelpHarness(ToolView):
            def __init__(self, main, key):
                super().__init__(main, key, key, f"{key}_help")

        for language, button_text in (("en", "How to use"), ("id", "Cara menggunakan")):
            self.main.current_lang = language
            self.labels["quality_tool_help"] = button_text
            for key in ("check_sheet", "fishbone", "defect_concentration"):
                with self.subTest(language=language, tool=key):
                    view = HelpHarness(self.main, key)
                    self.root.update()
                    button = self.host.workspace_tool_help_button
                    self.assertTrue(button.winfo_ismapped())
                    self.assertIs(button.master, self.host.workspace_title.master)
                    self.assertEqual(button.cget("text"), button_text)
                    self.assertEqual(button.winfo_manager(), "pack")
                    button.invoke()
                    self.root.update()
                    dialog = view._help_dialog
                    self.assertTrue(dialog.winfo_exists())
                    self.assertEqual(dialog.tool_key, key)
                    self.assertIn(
                        QUALITY_TOOL_HELP[language][key]["purpose"],
                        dialog.content.get("1.0", "end-1c"),
                    )
                    dialog.close_button.invoke()
                    self.root.update()
                    self.assertFalse(dialog.winfo_exists())
                    self.assertEqual(
                        {model_key: model.to_dict() for model_key, model in self.models.items()},
                        self.before,
                    )
                    view.destroy()
                    self.root.update()


if __name__ == "__main__":
    unittest.main()
