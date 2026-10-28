import tkinter as tk
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ui.main_page import MainPage


class SheetNumberingGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.geometry("900x600+30+30")
            self.root.update()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.main = MainPage(self.root)
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

    def test_insert_delete_and_undo_redo_keep_row_numbers_sequential(self):
        sheet = self.main.sheet.sheet
        original_rows = sheet.total_rows()
        sheet.set_cell_data(0, 0, "preserve-top")
        sheet.set_cell_data(2, 0, "preserve-third")
        sheet.insert_row(idx=2)
        self.root.update()
        self.assertEqual(sheet.row_index()[:7], [str(i) for i in range(1, 8)])
        self.assertEqual(sheet.total_rows(), original_rows + 1)
        self.assertEqual(sheet.get_cell_data(0, 0), "preserve-top")
        self.assertEqual(sheet.get_cell_data(3, 0), "preserve-third")

        sheet.del_rows(2)
        self.root.update()
        self.assertEqual(sheet.row_index()[:7], [str(i) for i in range(1, 8)])
        self.assertEqual(sheet.get_cell_data(2, 0), "preserve-third")
        sheet.undo()
        self.root.update()
        self.assertEqual(sheet.row_index()[:7], [str(i) for i in range(1, 8)])
        self.assertEqual(sheet.get_cell_data(3, 0), "preserve-third")
        sheet.redo()
        self.root.update()
        self.assertEqual(sheet.row_index()[:7], [str(i) for i in range(1, 8)])
        self.assertEqual(sheet.get_cell_data(2, 0), "preserve-third")

    def test_generated_headers_resequence_without_losing_imported_headers(self):
        sheet_view = self.main.sheet
        sheet_view.set_sheet_data_with_headers(
            [["batch-1", 12.5, 4], ["batch-2", 13.0, 5]],
            ["Batch ID", "Diameter", "C3"],
            [False, False, False],
        )
        sheet = sheet_view.sheet
        self.assertEqual(sheet_view.get_column_names()[:3], ["Batch ID", "Diameter", "C3"])

        sheet.insert_column(idx=1)
        self.root.update()
        self.assertEqual(sheet_view.get_column_names()[:5], ["Batch ID", "C2", "Diameter", "C3", "C5"])
        self.assertEqual(sheet.get_sheet_data()[0][:4], ["batch-1", "", 12.5, 4])
        self.assertEqual(sheet.get_sheet_data()[1][:4], ["batch-2", "", 13.0, 5])

        sheet.del_columns(1)
        self.root.update()
        self.assertEqual(sheet_view.get_column_names()[:5], ["Batch ID", "Diameter", "C3", "C4", "C5"])
        sheet.undo()
        self.root.update()
        self.assertEqual(sheet_view.get_column_names()[:5], ["Batch ID", "C2", "Diameter", "C3", "C5"])
        sheet.redo()
        self.root.update()
        self.assertEqual(sheet_view.get_column_names()[:5], ["Batch ID", "Diameter", "C3", "C4", "C5"])
        self.assertEqual(sheet.get_sheet_data()[0][:3], ["batch-1", 12.5, 4])

        manager = self.main.ui.project_manager
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder, \
                patch("project_managers.project_manager.messagebox.showinfo"):
            path = Path(folder) / "headers.spcproj"
            manager._write_project(path)
            sheet_view.set_sheet_data([["changed"]])
            self.assertTrue(manager.load_project(path))
        self.assertEqual(sheet_view.get_column_names()[:5], ["Batch ID", "Diameter", "C3", "C4", "C5"])
        self.assertEqual(sheet_view.get_generated_header_flags()[:5], [False, False, False, True, True])


if __name__ == "__main__":
    unittest.main()
