import tkinter as tk
from tkinter import ttk
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from inventory.persistence import InventoryStore
from ui.launcher import ApplicationLauncher
from ui.inventory_view import InventoryApplication
from ui.theme import ThemeManager


class InventoryWorkspaceGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.geometry("1100x760+35+35")
            self.root.update()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.temp_dir = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.path = Path(self.temp_dir.name) / "inventory.json"
        self.settings = Path(self.temp_dir.name) / "settings.json"
        manager = ThemeManager(SimpleNamespace(root=self.root), settings_path=self.settings)
        manager.set_language("en", persist=False)
        manager.set_theme("light", persist=False)
        self.app = InventoryApplication(self.root, theme_manager=manager, data_path=self.path)
        self.root.update()

    def tearDown(self):
        try:
            for after_id in self.root.tk.call("after", "info"):
                try:
                    self.root.after_cancel(after_id)
                except tk.TclError:
                    pass
            self.root.destroy()
        except (AttributeError, tk.TclError):
            pass
        self.temp_dir.cleanup()

    def _dialog(self):
        self.root.update()
        return next(widget for widget in self.root.winfo_children()
                    if isinstance(widget, tk.Toplevel))

    @staticmethod
    def _descendants(widget):
        result = []
        for child in widget.winfo_children():
            result.append(child)
            result.extend(InventoryWorkspaceGuiTests._descendants(child))
        return result

    def _enter_item(self, code="FG-1", name="Widget", minimum="3", opening="10"):
        self.app.add_item()
        dialog = self._dialog()
        entries = sorted((widget for widget in self._descendants(dialog) if isinstance(widget, ttk.Entry)),
                         key=lambda widget: int(widget.grid_info().get("row", 0)))
        for entry, value in zip(entries, (code, name, "Assembly", "pcs", minimum, opening)):
            entry.delete(0, "end")
            entry.insert(0, value)
        save = next(widget for widget in self._descendants(dialog)
                    if isinstance(widget, ttk.Button) and widget.cget("text") == "Save")
        save.invoke()
        self.root.update()

    def test_launcher_integration_uses_same_root_and_starts_maximized(self):
        self.app.outer.destroy()
        opened = []
        launcher = ApplicationLauncher(
            self.root, lambda _manager: None, self.settings,
            open_layout=lambda _manager: None,
            open_inventory=lambda manager: opened.append(
                InventoryApplication(self.root, theme_manager=manager, data_path=self.path)),
        )
        launcher.inventory_button.invoke()
        self.root.update()
        self.app = opened[0]
        self.assertIs(self.app.root, self.root)
        self.assertEqual(self.root.state(), "zoomed")
        self.assertTrue(self.app.item_tree.winfo_ismapped())
        self.assertTrue(self.app.recent_tree.winfo_ismapped())

    def test_item_dialog_transaction_stocktake_search_and_adjustment_workflow(self):
        self._enter_item()
        item = self.app.book.items[0]
        self.assertEqual(self.app.book.balance(item.id), 10)
        self.assertEqual(self.app.active_value.cget("text"), "1")
        self.assertEqual(self.app.item_tree.item(item.id, "values")[0], "FG-1")

        self.app.item_tree.selection_set(item.id)
        self.app._refresh_item_buttons()
        self.app.open_transaction("out")
        dialog = self._dialog()
        entries = sorted((widget for widget in self._descendants(dialog) if isinstance(widget, ttk.Entry)),
                         key=lambda widget: int(widget.grid_info().get("row", 0)))
        for entry, value in zip(entries, ("8", "SO-9", "Customer delivery")):
            entry.insert(0, value)
        next(widget for widget in self._descendants(dialog)
             if isinstance(widget, ttk.Button) and widget.cget("text") == "Save").invoke()
        self.root.update()
        self.assertEqual(self.app.book.balance(item.id), 2)
        self.assertEqual(self.app.low_value.cget("text"), "1")
        self.assertEqual(len(self.app.transaction_tree.get_children()), 1)

        self.app.search_var.set("does-not-match")
        self.app._refresh_items()
        self.assertEqual(self.app.item_tree.item("__empty__", "values")[0], self.app.t("inv_no_items"))
        self.app.search_var.set("")
        self.app._refresh_items()
        self.app.count_var.set("1")
        self.app.count_notes_var.set("One item missing")
        self.app.record_stocktake()
        stocktake = self.app.book.stocktakes[0]
        self.assertEqual(stocktake.system_stock, 2)
        self.assertEqual(stocktake.variance, -1)
        self.assertEqual(self.app.book.balance(item.id), 2)
        self.app.stocktake_tree.selection_set(stocktake.id)
        self.app._refresh_adjustment_state()
        self.app.adjustment_reason_var.set("Approved recount adjustment")
        self.app.adjust_stocktake()
        self.assertEqual(self.app.book.balance(item.id), 1)
        self.assertEqual(self.app.book.adjustments[0].reason, "Approved recount adjustment")
        self.assertIn("Approved recount adjustment",
                      self.app.stocktake_tree.item(stocktake.id, "values")[-1])

    def test_help_language_theme_and_saved_data_are_independent(self):
        self._enter_item(code="FG-ID")
        item_id = self.app.book.items[0].id
        before = self.app.book.to_dict()
        self.app.set_theme("dark")
        self.app.set_language("id")
        self.root.update()
        self.assertEqual(self.root.title(), "Persediaan Barang Jadi")
        self.assertEqual(self.app.book.to_dict(), before)
        self.assertEqual(self.app.theme_manager.mode, "dark")
        self.assertEqual(self.app.theme_manager.language, "id")
        self.app.open_help()
        dialog = self._dialog()
        content = next(widget for widget in self._descendants(dialog) if isinstance(widget, tk.Text))
        self.assertIn("stok sistem", content.get("1.0", "end").casefold())
        self.assertEqual(self.app.book.to_dict(), before)
        dialog.destroy()
        self.app.request_close()
        reopened = InventoryStore(self.path)
        self.assertEqual(reopened.book.balance(item_id), 10)

    def test_failed_ui_save_keeps_dialog_open_and_inventory_unchanged(self):
        self.app.add_item()
        dialog = self._dialog()
        entries = sorted((widget for widget in self._descendants(dialog) if isinstance(widget, ttk.Entry)),
                         key=lambda widget: int(widget.grid_info().get("row", 0)))
        for entry, value in zip(entries, ("FG-1", "Widget", "", "pcs", "0", "5")):
            entry.delete(0, "end")
            entry.insert(0, value)
        with patch("ui.inventory_view.messagebox.showerror") as error:
            with patch.object(self.app.store, "_write", side_effect=OSError("disk unavailable")):
                next(widget for widget in self._descendants(dialog)
                     if isinstance(widget, ttk.Button) and widget.cget("text") == "Save").invoke()
        self.root.update()
        self.assertTrue(dialog.winfo_exists())
        self.assertEqual(self.app.book.items, [])
        self.assertTrue(error.called)


if __name__ == "__main__":
    unittest.main()
