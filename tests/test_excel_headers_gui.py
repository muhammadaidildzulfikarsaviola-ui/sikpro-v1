import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook

from logic.imr_chart import IMRConfigPopup
from ui.main_page import MainPage


class ExcelHeaderWorkflowGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.geometry("1000x700+50+40")
            self.root.update()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.main = MainPage(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except (AttributeError, tk.TclError):
            pass

    def test_excel_headers_reach_chart_setup_and_survive_save_load_and_language_change(self):
        folder = Path(self.temp.name)
        workbook_path = folder / "synthetic.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Batch ID", "Diameter"])
        sheet.append([1, 12.5])
        sheet.append([2, 13.0])
        workbook.save(workbook_path)

        manager = self.main.ui.project_manager
        with patch("project_managers.project_manager.filedialog.askopenfilename", return_value=str(workbook_path)), \
                patch("project_managers.project_manager.messagebox.showinfo"):
            manager.import_excel()

        headers = self.main.sheet.get_column_names()
        self.assertEqual(headers[:2], ["Batch ID", "Diameter"])
        self.assertEqual(headers[2:], [f"C{i}" for i in range(3, len(headers) + 1)])
        self.assertEqual(self.main.sheet.get_sheet_data(), [[1, 12.5], [2, 13.0]])
        config = IMRConfigPopup(self.main, self.main.sheet)
        self.root.update()
        values = tuple(config.column_listbox.get(0, "end"))
        self.assertEqual(values, ("Batch ID", "Diameter"))
        config.destroy()

        project_path = folder / "with-headers.spcproj"
        with patch("project_managers.project_manager.messagebox.showinfo"):
            manager._write_project(project_path)
            self.main.sheet.clear()
            self.assertEqual(self.main.sheet.get_column_names(), [f"C{i}" for i in range(1, len(headers) + 1)])
            self.assertTrue(manager.load_project(project_path))

        self.assertEqual(self.main.sheet.get_column_names(), headers)
        self.main.set_lang("id")
        self.root.update()
        self.assertEqual(self.main.sheet.get_column_names(), headers)


if __name__ == "__main__":
    unittest.main()
