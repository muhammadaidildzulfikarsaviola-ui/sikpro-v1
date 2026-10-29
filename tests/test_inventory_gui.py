import tkinter as tk
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from ui.inventory_view import InventoryApplication
from ui.launcher import ApplicationLauncher
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
        settings = Path(self.temp_dir.name) / "settings.json"
        manager = ThemeManager(SimpleNamespace(root=self.root), settings_path=settings)
        manager.set_language("en", persist=False)
        manager.set_theme("light", persist=False)
        self.app = InventoryApplication(self.root, theme_manager=manager)
        self.root.update()

    def tearDown(self):
        try:
            for after_id in self.root.tk.call("after", "info"):
                try:
                    self.root.after_cancel(after_id)
                except tk.TclError:
                    pass
            self.root.update_idletasks()
            self.root.destroy()
        except (AttributeError, tk.TclError):
            pass
        self.temp_dir.cleanup()

    def test_workspace_has_three_planning_tools_and_theme_language_switch(self):
        self.assertEqual(len(self.app.tabs.tabs()), 3)
        self.app.set_theme("dark")
        self.app.set_language("id")
        self.assertEqual(self.root.title(), "Kalkulator Perencanaan Persediaan")
        self.assertEqual(self.app.theme_manager.mode, "dark")

    def test_eoq_modes_localize_switch_and_calculate_shared_model(self):
        self.app.eoq_vars["inv_annual_demand"].set("1000")
        self.app.eoq_vars["inv_ordering_cost"].set("50")
        self.app.eoq_vars["inv_holding_cost"].set("2")
        self.app.calculate_eoq()
        unit_text = self.app.eoq_result.cget("text")
        self.assertIn("operating days", unit_text)
        self.app.eoq_mode_selector.current(1)
        self.app._show_eoq_mode()
        self.root.update_idletasks()
        self.assertEqual(self.app.eoq_vars["inv_operating_days__widget"].winfo_manager(), "")
        self.assertEqual(self.app.eoq_vars["inv_unit_price__widget"].winfo_manager(), "grid")
        self.app.eoq_vars["inv_unit_price"].set("4")
        self.app.calculate_eoq()
        cost_text = self.app.eoq_result.cget("text")
        self.assertIn("Total annual cost including purchases", cost_text)
        self.app.set_language("id")
        self.assertEqual(tuple(self.app.eoq_mode_selector.cget("values")), ("EOQ Kuantitas (Unit)", "EOQ Analisis Biaya"))
        self.assertEqual(self.app.eoq_mode_selector.current(), 1)

    def test_theme_dropdown_uses_localized_labels_and_preserves_mode(self):
        self.app.set_language("id")
        self.assertEqual(tuple(self.app.theme_box.cget("values")), ("Terang", "Gelap"))
        self.app.theme_box.current(1)
        self.app.theme_box.event_generate("<<ComboboxSelected>>")
        self.root.update()
        self.assertEqual(self.app.theme_manager.mode, "dark")
        self.app.set_language("en")
        self.assertEqual(tuple(self.app.theme_box.cget("values")), ("Light", "Dark"))
        self.assertEqual(self.app.theme_var.get(), "Dark")

    def test_inventory_forms_actions_help_and_results_do_not_overlap(self):
        self.root.geometry("920x640+20+20")
        self.root.update_idletasks()

        def bottom(widget):
            return widget.winfo_rooty() + widget.winfo_height()

        def top(widget):
            return widget.winfo_rooty()

        def verify_eoq(mode_index):
            self.app.eoq_mode_selector.current(mode_index)
            self.app._show_eoq_mode()
            self.root.update_idletasks()
            inputs = [self.app.eoq_vars[key + "__widget"] for key in
                      ("inv_annual_demand", "inv_ordering_cost", "inv_holding_cost",
                       "inv_operating_days" if mode_index == 0 else "inv_unit_price")]
            actions = self.app.eoq_result.master.master.grid_slaves(row=2, column=0)[0]
            self.assertGreaterEqual(top(actions), max(bottom(widget) for widget in inputs))
            self.assertGreaterEqual(top(self.app.eoq_result.master), bottom(actions))

        verify_eoq(0)
        verify_eoq(1)
        self.app.tabs.select(1)
        self.root.update_idletasks()
        rop_inputs = [self.app.rop_vars[key + "__widget"] for key in
                      ("inv_average_demand", "inv_lead_time", "inv_safety_stock")]
        rop_actions = self.app.rop_result.master.master.grid_slaves(row=1, column=0)[0]
        self.assertGreaterEqual(top(rop_actions), max(bottom(widget) for widget in rop_inputs))
        self.assertGreaterEqual(top(self.app.rop_result.master), bottom(rop_actions))
        self.app.tabs.select(2)
        self.root.update_idletasks()
        mrp_inputs = [self.app.mrp_vars[key + "__widget"] for key in
                      ("inv_periods", "inv_gross_requirements", "inv_initial_on_hand",
                       "inv_scheduled_receipts", "inv_lead_time", "inv_lot_method",
                       "inv_fixed_quantity", "inv_poq_interval")]
        mrp_actions = self.app.mrp_output.master.grid_slaves(row=1, column=0)[0]
        self.assertGreaterEqual(top(mrp_actions), max(bottom(widget) for widget in mrp_inputs))
        self.assertGreaterEqual(top(self.app.mrp_help), bottom(mrp_actions))
        self.assertGreaterEqual(top(self.app.mrp_output), bottom(self.app.mrp_help))
        for width, height in ((1100, 760), (1000, 700)):
            self.root.geometry(f"{width}x{height}+20+20")
            self.root.update_idletasks()
            self.assertGreaterEqual(top(mrp_actions), max(bottom(widget) for widget in mrp_inputs))
            self.assertGreaterEqual(top(self.app.mrp_output), bottom(self.app.mrp_help))
        self.app.set_theme("dark")
        self.app.set_language("id")
        self.root.update_idletasks()
        self.assertEqual(len(self.app.tabs.tabs()), 3)
        verify_eoq(0)
        verify_eoq(1)

    def test_spc_header_back_action_is_connected(self):
        from ui.main_page import MainPage
        calls = []
        app = MainPage(self.root, theme_manager=self.app.theme_manager)
        app.set_on_back(lambda: calls.append(True))
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        back = next(widget for widget in descendants(app.root)
                    if isinstance(widget, tk.Button) and widget.cget("text") == "Back to Apps")
        back.invoke()
        self.assertEqual(calls, [True])

    def test_launcher_opens_calculator_on_shared_root(self):
        self.app.outer.destroy()
        opened = []
        launcher = ApplicationLauncher(self.root, lambda _manager: None,
            open_inventory=lambda manager: opened.append(InventoryApplication(self.root, theme_manager=manager)))
        launcher.inventory_button.invoke()
        self.root.update()
        self.app = opened[0]
        self.assertIs(self.app.root, self.root)
        self.assertEqual(len(self.app.tabs.tabs()), 3)


if __name__ == "__main__":
    unittest.main()
