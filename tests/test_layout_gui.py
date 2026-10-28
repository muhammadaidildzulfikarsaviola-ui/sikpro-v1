import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
import tempfile
from unittest.mock import patch

from layout.models import LayoutProject
from ui.launcher import ApplicationLauncher
from ui.layout_view import LayoutApplication
from ui.theme import ThemeManager


class LayoutWorkspaceGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.geometry("1100x760+35+35")
            self.root.update()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.temp_dir = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.settings_path = Path(self.temp_dir.name) / "settings.json"
        self.app = None

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

    def make_app(self, language="en", mode="light"):
        manager = ThemeManager(SimpleNamespace(root=self.root), settings_path=self.settings_path)
        manager.set_language(language, persist=False)
        manager.set_theme(mode, persist=False)
        self.app = LayoutApplication(self.root, theme_manager=manager)
        self.root.update()
        return self.app

    def test_launcher_opens_layout_in_same_root_and_preserves_preferences(self):
        created = []

        def open_layout(manager):
            created.append(LayoutApplication(self.root, theme_manager=manager))

        launcher = ApplicationLauncher(self.root, lambda _manager: None, self.settings_path,
                                       open_layout=open_layout)
        launcher.set_language("id")
        launcher.set_theme("dark")
        launcher.layout_button.invoke()
        self.root.update()
        self.assertEqual(len(created), 1)
        self.assertIs(created[0].root, self.root)
        self.assertEqual(created[0].current_lang, "id")
        self.assertEqual(created[0].theme_manager.mode, "dark")
        self.assertEqual(self.root.resizable(), (1, 1))
        self.assertIn("Tata Letak", self.root.title())

    def test_language_and_theme_switch_keep_current_input_and_models(self):
        app = self.make_app()
        department = app.project.add_department("Machining", 30)
        app._sync_project_fields()
        app.project_name_var.set("Draft Project")
        app.floor_width_var.set("36")
        app.set_theme("dark")
        self.assertEqual(app.project_name_var.get(), "Draft Project")
        self.assertEqual(app.floor_width_var.get(), "36")
        app.set_language("id")
        self.root.update()
        self.assertEqual(app.project.get_department(department.id).name, "Machining")
        self.assertEqual(app.project_name_var.get(), "Draft Project")
        self.assertEqual(app.title_label.cget("text"), "Perencanaan Tata Letak Fasilitas")
        self.assertEqual(app.canvas.cget("background"), app.palette["panel"])
        self.assertEqual(app.project_path_label.cget("text"), "Untitled Layout")
        self.assertEqual(app.theme_manager.language, "id")
        self.assertEqual(app.theme_manager.mode, "dark")

    def test_relationship_chart_generation_and_invalid_drag_are_visible(self):
        app = self.make_app()
        first = app.project.add_department("Cutting", 40)
        second = app.project.add_department("Assembly", 35)
        app.project.set_relationship(first.id, second.id, "A", "Near in process")
        app._sync_project_fields()
        app.refresh_all()
        self.assertEqual(len(app.relationship_tree.get_children()), 1)
        app.generate()
        self.root.update()
        self.assertGreater(len(app.project.alternatives), 1)
        self.assertEqual(len(app.alternative_tree.get_children()), len(app.project.alternatives))
        alternative = app.selected_alternative()
        self.assertTrue(alternative.is_valid)

        # Move the first block's center onto the second one through the same
        # press/drag/release handlers used by canvas pointer events.
        rectangle = alternative.rectangles[first.id]
        target = alternative.rectangles[second.id]
        width, height = app.canvas.winfo_width(), app.canvas.winfo_height()
        padding = 34
        scale = min((width - 2 * padding) / app.project.floor_width,
                    (height - 2 * padding) / app.project.floor_height)
        ox = (width - app.project.floor_width * scale) / 2
        oy = (height - app.project.floor_height * scale) / 2
        press = SimpleNamespace(
            x=ox + (rectangle.x + rectangle.width / 2) * scale,
            y=oy + (app.project.floor_height - rectangle.y - rectangle.height / 2) * scale,
        )
        drag = SimpleNamespace(
            x=ox + (target.x + target.width / 2) * scale,
            y=oy + (app.project.floor_height - target.y - target.height / 2) * scale,
        )
        app._canvas_press(press)
        old_score = alternative.score
        app._canvas_drag(drag)
        app._canvas_release(drag)
        self.assertFalse(alternative.is_valid)
        self.assertTrue(any(error.startswith("geometry_overlap") for error in alternative.geometry_errors))
        self.assertNotEqual(alternative.score, old_score)
        self.assertIn("Tidak valid" if app.current_lang == "id" else "Invalid", app.status_value.cget("text"))

    def test_canvas_fits_resizes_and_keeps_labels_inside_department_blocks(self):
        app = self.make_app()
        departments = [app.project.add_department(name, area) for name, area in
                       (("Cutting", 40), ("Assembly", 35), ("Inspection", 25))]
        for first, second, rating in ((0, 1, "A"), (0, 2, "X"), (1, 2, "E")):
            app.project.set_relationship(departments[first].id, departments[second].id, rating)
        app._sync_project_fields()
        app.generate()
        self.root.update()
        canvas = app.canvas
        floor_item = canvas.find_withtag("floor")[0]
        initial_floor_box = canvas.bbox(floor_item)
        self.assertIsNotNone(initial_floor_box)
        initial_department_boxes = {}
        for department in departments:
            items = canvas.find_withtag(f"department:{department.id}")
            rectangle_item = next(item for item in items if "rectangle" == canvas.type(item))
            initial_department_boxes[department.id] = canvas.bbox(rectangle_item)
            text_items = [item for item in items if canvas.type(item) == "text"]
            self.assertTrue(text_items)
            block_box = canvas.bbox(rectangle_item)
            for text_item in text_items:
                text_box = canvas.bbox(text_item)
                self.assertGreaterEqual(text_box[0], block_box[0])
                self.assertGreaterEqual(text_box[1], block_box[1])
                self.assertLessEqual(text_box[2], block_box[2])
                self.assertLessEqual(text_box[3], block_box[3])
        if len(app.project.alternatives) > 1:
            first_geometry = app.selected_alternative().to_dict()
            next_id = next(item.id for item in app.project.alternatives
                           if item.id != app.selected_alternative_id)
            app.alternative_tree.selection_set(next_id)
            app._alternative_selected()
            alternate_box = canvas.bbox(next(
                item for item in canvas.find_withtag(f"department:{departments[0].id}")
                if canvas.type(item) == "rectangle"
            ))
            self.assertNotEqual(alternate_box, initial_department_boxes[departments[0].id])
            self.root.geometry("1200x820+35+35")
            self.root.update()
            app.fit_button.invoke()
            self.root.update()
            resized_floor_box = canvas.bbox(canvas.find_withtag("floor")[0])
            self.assertGreaterEqual(resized_floor_box[0], 0)
            self.assertGreaterEqual(resized_floor_box[1], 0)
            self.assertLessEqual(resized_floor_box[2], canvas.winfo_width())
            self.assertLessEqual(resized_floor_box[3], canvas.winfo_height())
            self.assertNotEqual(resized_floor_box, initial_floor_box)
            self.assertNotEqual(app.selected_alternative().to_dict(), first_geometry)

    def test_project_roundtrip_and_failed_load_keep_active_state(self):
        app = self.make_app()
        first = app.project.add_department("Mixing", 30)
        second = app.project.add_department("Packing", 20)
        app.project.set_relationship(first.id, second.id, "E")
        app._sync_project_fields()
        app.generate()
        path = Path(self.temp_dir.name) / "saved.layoutproj"
        app.current_path = str(path)
        self.assertTrue(app.save_project())
        active = app.project
        bad_path = Path(self.temp_dir.name) / "unsupported.layoutproj"
        bad_path.write_text('{"format":"sikpro-layout","version":88,"project":{}}', encoding="utf-8")
        with patch("ui.layout_view.messagebox.showerror"):
            self.assertFalse(app._load_path(bad_path))
        self.assertIs(app.project, active)
        self.assertEqual(app.current_path, str(path))
        app.project = LayoutProject()
        self.assertTrue(app._load_path(path))
        self.assertEqual([item.name for item in app.project.departments], ["Mixing", "Packing"])
        self.assertTrue(app.project.alternatives)

    def test_help_is_localized_and_exports_can_be_triggered(self):
        app = self.make_app("id", "light")
        app.project.add_department("Lathe", 20)
        app._sync_project_fields()
        app.generate()
        before_help = app._snapshot()
        app.open_help()
        self.root.update()
        help_windows = [widget for widget in self.root.winfo_children()
                        if isinstance(widget, tk.Toplevel)]
        self.assertEqual(len(help_windows), 1)
        help_window = help_windows[0]
        help_text = next(widget for widget in help_window.winfo_children()[0].winfo_children()
                         if isinstance(widget, tk.Text))
        self.assertIn("memotong area tata letak", help_text.get("1.0", "end"))
        self.assertEqual(help_text.cget("state"), "disabled")
        self.assertEqual(help_window.cget("bg"), app.palette["window"])
        self.assertEqual(app._snapshot(), before_help)
        help_window.destroy()
        output_png = Path(self.temp_dir.name) / "selected.png"
        output_pdf = Path(self.temp_dir.name) / "report.pdf"
        with patch("ui.layout_view.filedialog.asksaveasfilename", side_effect=[str(output_png), str(output_pdf)]), \
                patch("ui.layout_view.messagebox.showinfo"):
            app.export_selected_png()
            app.export_report_pdf()
        self.assertEqual(output_png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(output_pdf.read_bytes()[:5], b"%PDF-")
        self.assertEqual(app.t("layout_help_title"), "Perencanaan tata letak: cara penggunaan")

    def test_close_cancel_preserves_workspace_and_unsaved_changes(self):
        app = self.make_app()
        app.project.add_department("Draft", 20)
        with patch("ui.layout_view.messagebox.askyesnocancel", return_value=None), \
                patch.object(self.root, "destroy") as destroy:
            app.request_close()
        destroy.assert_not_called()
        self.assertEqual([department.name for department in app.project.departments], ["Draft"])
        self.assertTrue(app.has_unsaved_changes())


if __name__ == "__main__":
    unittest.main()
