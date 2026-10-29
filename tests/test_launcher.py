import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from ui.launcher import ApplicationLauncher
from ui.main_page import MainPage


class ApplicationLauncherTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.geometry("900x640+40+40")
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings_path = Path(self.temp_dir.name) / "settings.json"

    def tearDown(self):
        try:
            self.root.destroy()
        except (AttributeError, tk.TclError):
            pass
        if hasattr(self, "temp_dir"):
            self.temp_dir.cleanup()

    def make_launcher(self, callback=None):
        return ApplicationLauncher(
            self.root, callback or (lambda _theme_manager: None), self.settings_path,
            open_layout=lambda _theme_manager: None,
            open_inventory=lambda _theme_manager: None,
        )

    def test_seven_cards_use_three_column_grid_and_only_spc_is_available(self):
        launcher = self.make_launcher()
        self.root.update()
        self.assertEqual(self.root.winfo_width(), launcher.WINDOW_WIDTH)
        self.assertEqual(self.root.winfo_height(), launcher.WINDOW_HEIGHT)
        self.assertEqual(self.root.resizable(), (0, 0))
        self.assertEqual(
            self.root.winfo_x(), (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        )
        self.assertEqual(
            self.root.winfo_y(), (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        )
        self.assertEqual(launcher.current_lang, "en")
        self.assertEqual(launcher.spc_button.cget("text"), "Open SPC")
        self.assertEqual(launcher.layout_button.cget("text"), "Open Layout")
        self.assertNotIn("disabled", launcher.layout_button.state())
        self.assertEqual(launcher.inventory_button.cget("text"), "Open Calculator")
        self.assertNotIn("disabled", launcher.inventory_button.state())
        self.assertEqual(len(launcher.cards_by_key), 7)
        self.assertEqual(
            [(key, int(card["frame"].grid_info()["row"]), int(card["frame"].grid_info()["column"]))
             for key, card in launcher.cards_by_key.items()],
            [("spc", 0, 0), ("layout", 0, 1), ("inventory", 0, 2),
             ("forecasting", 1, 0), ("mrp", 1, 1), ("work_measurement", 1, 2),
             ("optimization", 2, 0)],
        )
        launcher.cards.update_idletasks()
        self.assertLessEqual(launcher.cards.winfo_y() + launcher.cards.winfo_height(),
                             launcher.frame.winfo_height())
        self.assertEqual(launcher.cards_by_key["spc"]["status"].cget("text"), "Available")
        self.assertEqual(launcher.cards_by_key["layout"]["status"].cget("text"), "Available")
        self.assertEqual(launcher.cards_by_key["inventory"]["status"].cget("text"), "Available")
        for key in ("forecasting", "mrp", "work_measurement", "optimization"):
            self.assertEqual(launcher.cards_by_key[key]["status"].cget("text"), "Planned")
        for key, card_data in launcher.cards_by_key.items():
            card = card_data["frame"]
            self.assertTrue(card_data["button"].winfo_ismapped())
            card.update_idletasks()
            self.assertLessEqual(card.winfo_y() + card.winfo_height(), launcher.cards.winfo_height())
            for child in card.winfo_children():
                self.assertLessEqual(child.winfo_y() + child.winfo_height(), card.winfo_height())
            if key not in ("spc", "layout", "inventory"):
                self.assertIn("disabled", card_data["button"].state())

    def test_translations_and_theme_are_applied_to_all_cards(self):
        launcher = self.make_launcher()
        expected = {
            "en": {
                "titles": ["SPC", "Layout", "Inventory", "Forecasting", "MRP", "Work Measurement", "Optimization"],
                "statuses": ["Available", "Available", "Available"] + ["Planned"] * 4,
                "descriptions": [
                    "Analyze process variation", "Design factory layouts", "Plan EOQ, reorder points",
                    "Estimate future demand", "Plan the materials", "Study work methods",
                    "Compare choices",
                ],
                "button": "Not Available Yet",
                "layout_button": "Open Layout",
                "inventory_button": "Open Calculator",
            },
            "id": {
                "titles": ["SPC", "Tata Letak", "Persediaan", "Peramalan", "MRP", "Pengukuran Kerja", "Optimasi"],
                "statuses": ["Tersedia", "Tersedia", "Tersedia"] + ["Direncanakan"] * 4,
                "descriptions": [
                    "Analisis variasi proses", "Rancang tata letak", "Rencanakan EOQ",
                    "Perkirakan permintaan", "Rencanakan bahan", "Pelajari metode",
                    "Bandingkan pilihan",
                ],
                "button": "Belum Tersedia",
                "layout_button": "Buka Tata Letak",
                "inventory_button": "Buka Kalkulator",
            },
        }
        for language, mode in (
            ("en", "light"),
            ("id", "dark"),
            ("en", "dark"),
            ("id", "light"),
        ):
            launcher.set_language(language)
            launcher.set_theme(mode)
            self.root.update()
            self.assertEqual(self.root.winfo_width(), launcher.WINDOW_WIDTH)
            self.assertEqual(self.root.winfo_height(), launcher.WINDOW_HEIGHT)
            palette = launcher.theme_manager.palette
            for index, (key, card_data) in enumerate(launcher.cards_by_key.items()):
                self.assertEqual(card_data["title"].cget("text"), expected[language]["titles"][index])
                self.assertEqual(card_data["status"].cget("text"), expected[language]["statuses"][index])
                self.assertIn(expected[language]["descriptions"][index],
                              card_data["description"].cget("text"))
                self.assertEqual(card_data["frame"].cget("background"), palette["surface"])
                self.assertEqual(card_data["description"].cget("foreground"), palette["text_soft"])
                self.assertTrue(card_data["button"].winfo_ismapped())
                card_data["frame"].update_idletasks()
                self.assertLessEqual(card_data["button"].winfo_y() + card_data["button"].winfo_height(),
                                     card_data["frame"].winfo_height())
            self.assertEqual(launcher.spc_button.cget("text"), "Open SPC" if language == "en" else "Buka SPC")
            self.assertEqual(launcher.layout_button.cget("text"), expected[language]["layout_button"])
            self.assertEqual(launcher.inventory_button.cget("text"), expected[language]["inventory_button"])
            self.assertEqual(launcher.cards_by_key["inventory"]["button"].cget("text"),
                             expected[language]["inventory_button"])

    def test_unavailable_cards_cannot_launch_any_module(self):
        calls = []
        launcher = self.make_launcher(lambda manager: calls.append(manager))
        for key in ("forecasting", "mrp", "work_measurement", "optimization"):
            launcher.cards_by_key[key]["button"].invoke()
        self.assertEqual(calls, [])

    def test_layout_card_routes_to_layout_callback(self):
        calls = []
        launcher = ApplicationLauncher(
            self.root, lambda manager: None, self.settings_path,
            open_layout=lambda manager: calls.append(manager),
        )
        self.root.update()
        launcher.layout_button.invoke()
        self.root.update()
        self.assertEqual(calls, [launcher.theme_manager])
        self.assertFalse(launcher.frame.winfo_exists())

    def test_inventory_card_routes_to_inventory_callback(self):
        calls = []
        launcher = ApplicationLauncher(
            self.root, lambda manager: None, self.settings_path,
            open_layout=lambda manager: None,
            open_inventory=lambda manager: calls.append(manager),
        )
        self.root.update()
        launcher.inventory_button.invoke()
        self.root.update()
        self.assertEqual(calls, [launcher.theme_manager])
        self.assertFalse(launcher.frame.winfo_exists())

    def test_spc_button_invokes_existing_application_callback_once(self):
        calls = []
        launcher = self.make_launcher(lambda manager: calls.append(manager))
        self.root.update()
        launcher.spc_button.invoke()
        self.root.update()
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0], launcher.theme_manager)
        self.assertFalse(launcher.frame.winfo_exists())

    def test_spc_workspace_starts_maximized_on_existing_launcher_root(self):
        launcher = self.make_launcher()
        app = MainPage(self.root, theme_manager=launcher.theme_manager)
        self.root.update()
        self.assertIs(app.root, self.root)
        self.assertEqual(self.root.state(), "zoomed")
        self.assertEqual(len([child for child in self.root.winfo_children()
                              if isinstance(child, tk.Toplevel)]), 0)

    def test_language_and_theme_persist_and_pass_to_spc(self):
        launcher = self.make_launcher()
        launcher.set_language("id")
        launcher.set_theme("dark")
        self.root.update()
        self.assertEqual(launcher.current_lang, "id")
        self.assertEqual(launcher.spc_button.cget("text"), "Buka SPC")
        self.assertEqual(launcher.theme_manager.palette["window"], "#171c24")

        app_state = {}
        launcher.open_spc_callback = lambda manager: app_state.setdefault(
            "app", MainPage(self.root, theme_manager=manager)
        )
        launcher.spc_button.invoke()
        self.root.update()
        app = app_state["app"]
        self.assertIs(app.theme_manager, launcher.theme_manager)
        self.assertEqual(app.current_lang, "id")
        self.assertEqual(app.theme_manager.mode, "dark")
        self.assertEqual(app.lang_data["file"], "Berkas")
        self.assertEqual(self.root.resizable(), (1, 1))
        project_manager = app.ui.project_manager
        project_manager.current_project_path = str(Path(self.temp_dir.name) / "active.spcproj")
        app.tool_models["fishbone"].effect = "Unsaved effect"
        self.assertTrue(project_manager.has_unsaved_changes())
        app.set_lang("en")
        self.assertEqual(app.ui.project_manager.current_project_path, project_manager.current_project_path)
        self.assertTrue(app.ui.project_manager.has_unsaved_changes())
        self.assertEqual(app.tool_models["fishbone"].effect, "Unsaved effect")
        app.set_lang("id")

        for child in self.root.winfo_children():
            child.destroy()
        restarted = ApplicationLauncher(self.root, lambda _manager: None, self.settings_path,
                                        open_layout=lambda _manager: None,
                                        open_inventory=lambda _manager: None)
        self.root.update()
        self.assertEqual(restarted.current_lang, "id")
        self.assertEqual(restarted.theme_manager.mode, "dark")
        self.assertEqual(restarted.layout_button.cget("text"), "Buka Tata Letak")
        self.assertEqual(restarted.inventory_button.cget("text"), "Buka Kalkulator")
        self.assertEqual(len(restarted.cards_by_key), 7)


if __name__ == "__main__":
    unittest.main()
