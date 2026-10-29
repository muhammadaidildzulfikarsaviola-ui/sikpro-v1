import tkinter as tk
import tempfile
import unittest
from pathlib import Path

from ui.inventory_view import InventoryApplication
from ui.launcher import ApplicationLauncher
from ui.layout_view import LayoutApplication


class ModuleBackNavigationTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.update()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.settings = Path(self.temp.name) / "settings.json"
        self.module = None
        self.launcher = None
        self.show_launcher()

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.temp.cleanup()

    def show_launcher(self, manager=None):
        for child in self.root.winfo_children():
            child.destroy()
        self.launcher = ApplicationLauncher(
            self.root, lambda _manager: None, self.settings,
            open_layout=self.open_layout, open_inventory=self.open_inventory)
        if manager:
            self.launcher.theme_manager = manager
            manager.main = self.launcher
            self.launcher.current_lang = manager.language
            from core.lang import LANG
            self.launcher.lang_data = LANG[manager.language]
            self.launcher.build()

    def back(self):
        manager = self.module.theme_manager
        self.show_launcher(manager)

    def open_layout(self, manager):
        self.module = LayoutApplication(self.root, theme_manager=manager)
        self.module.set_on_back(self.back)

    def open_inventory(self, manager):
        self.module = InventoryApplication(self.root, theme_manager=manager)
        self.module.set_on_back(self.back)

    def _cycle(self, kind):
        self.launcher.set_language("id")
        self.launcher.set_theme("dark")
        for _ in range(3):
            button = self.launcher.layout_button if kind == "layout" else self.launcher.inventory_button
            button.invoke()
            self.root.update()
            back = self.module.back_button
            back.invoke()
            self.root.update()
            self.assertTrue(self.launcher.frame.winfo_exists())
            self.assertTrue(self.launcher.frame.winfo_ismapped())
            self.assertEqual(self.root.winfo_children().__len__(), 1)
            self.assertEqual(self.launcher.theme_manager.mode, "dark")
            self.assertEqual(self.launcher.theme_manager.language, "id")

    def test_layout_back_reopen_cycles(self):
        self._cycle("layout")

    def test_inventory_back_reopen_cycles(self):
        self._cycle("inventory")


if __name__ == "__main__":
    unittest.main()
