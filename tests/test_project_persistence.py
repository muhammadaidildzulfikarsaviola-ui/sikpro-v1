import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd

from models.analysis import Analysis
from models.quality_tools import (
    Cause,
    CheckSheetModel,
    DefectConcentrationModel,
    FishboneModel,
    default_tool_models,
)
from project_managers.project_manager import ProjectManager


class FakeSheet:
    def __init__(self, data=None):
        self.data = copy.deepcopy(data if data is not None else [["old"]])
        self.fail_next_set = False
        self.headers = [f"C{i + 1}" for i in range(max((len(row) for row in self.data), default=0))]

    def get_sheet_data(self):
        return copy.deepcopy(self.data)

    def set_sheet_data(self, data):
        if self.fail_next_set:
            self.fail_next_set = False
            raise RuntimeError("simulated sheet restore failure")
        self.data = copy.deepcopy(data)
        self.headers = [f"C{i + 1}" for i in range(max((len(row) for row in data), default=0))]

    def set_sheet_data_with_headers(self, data, headers):
        self.set_sheet_data(data)
        self.headers = list(headers)

    def get_column_names(self):
        return list(self.headers)

    def clear(self):
        self.data = [[""]]
        self.headers = ["C1"]


class FakeListbox:
    def __init__(self):
        self.items = []

    def delete(self, _first, _last=None):
        self.items.clear()

    def insert(self, _index, value):
        self.items.append(value)


class FakeNavigator:
    def __init__(self, main):
        self.main = main
        self.navigator_box = FakeListbox()
        self.fail_on_title = None

    def add_analysis(self, analysis, save=True):
        if analysis.title == self.fail_on_title:
            self.fail_on_title = None
            raise RuntimeError("simulated navigator failure")
        if save:
            self.main.analysis_objects.append(analysis)
        self.navigator_box.insert("end", analysis.navigator_name or analysis.title)


class FakeMain:
    def __init__(self, language="en"):
        self.root = object()
        self.current_lang = language
        self.sheet = FakeSheet()
        self.analysis_objects = []
        self.tool_models = default_tool_models(language)
        self.navigator = FakeNavigator(self)

    def t(self, key):
        return key


class ProjectPersistenceTests(unittest.TestCase):
    def setUp(self):
        # Keep temporary files under the writable repository root. The host
        # sandbox may deny atomic replacement under the system temp directory.
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.main = FakeMain()
        self.manager = ProjectManager(self.main)
        self._quiet_messages()

    def _quiet_messages(self):
        info = patch("project_managers.project_manager.messagebox.showinfo")
        error = patch("project_managers.project_manager.messagebox.showerror")
        info.start()
        error.start()
        self.addCleanup(info.stop)
        self.addCleanup(error.stop)

    def _populate_models(self):
        fishbone = self.main.tool_models["fishbone"]
        fishbone.effect = "Seal leakage"
        first_category = fishbone.categories[0]["id"]
        custom_category = fishbone.add_category("Inspection")
        first = fishbone.add_cause(first_category, "Worn seal")
        second = fishbone.add_cause(first_category, "Incorrect torque")
        fishbone.move_cause_order(second, -1)
        fishbone.add_cause(custom_category, "Missed inspection")

        check_sheet = self.main.tool_models["check_sheet"]
        category = check_sheet.add_category("Scratch")
        check_sheet.add_record(category, 4, "2026-10-27", "Batch 17", "Left edge")
        check_sheet.add_record(category, 2, "2026-10-28", "Batch 18", "")

        concentration = self.main.tool_models["defect_concentration"]
        default_category = concentration.default_category_id
        renamed_category = concentration.add_category("Dent")
        concentration.rename_category(default_category, "Pinhole")
        concentration.add_mark(renamed_category, 0.125, 0.875, "Near upper corner")
        concentration.add_mark(default_category, 0.61, 0.42, "Center")

    def _save_and_reopen(self, models=None):
        if models is not None:
            self.main.tool_models = models
        path = Path(self.temp.name) / "project.spcproj"
        self.manager._write_project(path)
        restored_main = FakeMain()
        restored_manager = ProjectManager(restored_main)
        self.assertTrue(restored_manager.load_project(path))
        return restored_main, path

    def test_fishbone_round_trip_preserves_effect_categories_causes_and_order(self):
        self._populate_models()
        restored, _ = self._save_and_reopen()
        before = self.main.tool_models["fishbone"].to_dict()
        after = restored.tool_models["fishbone"].to_dict()
        self.assertEqual(after["effect"], before["effect"])
        self.assertEqual(after["categories"], before["categories"])
        self.assertEqual(after["causes"], before["causes"])

    def test_check_sheet_round_trip_preserves_categories_records_and_totals(self):
        self._populate_models()
        restored, _ = self._save_and_reopen()
        before = self.main.tool_models["check_sheet"]
        after = restored.tool_models["check_sheet"]
        self.assertEqual(after.to_dict(), before.to_dict())
        self.assertEqual(after.grand_total, before.grand_total)
        self.assertEqual(after.totals, before.totals)

    def test_defect_concentration_round_trip_preserves_mark_details(self):
        self._populate_models()
        restored, _ = self._save_and_reopen()
        before = self.main.tool_models["defect_concentration"]
        after = restored.tool_models["defect_concentration"]
        self.assertEqual(after.to_dict(), before.to_dict())
        self.assertEqual(after.default_category_id, before.default_category_id)
        self.assertEqual(after.total, before.total)

    def test_all_quality_models_restore_together_with_sheet_and_analysis(self):
        self._populate_models()
        self.main.sheet.set_sheet_data([["Measurement"], [12.5]])
        self.main.analysis_objects = [Analysis("i-mr", "Line 1", {"values": [12.5]},
                                               {"mean": 12.5}, {"column": "C1"}, "I-MR")]
        restored, _ = self._save_and_reopen()
        self.assertEqual(restored.sheet.get_sheet_data(), [["Measurement"], [12.5]])
        self.assertEqual(len(restored.analysis_objects), 1)
        self.assertEqual(restored.analysis_objects[0].title, "Line 1")
        for key in ("fishbone", "check_sheet", "defect_concentration"):
            self.assertEqual(restored.tool_models[key].to_dict(), self.main.tool_models[key].to_dict())

    def test_project_round_trip_preserves_spreadsheet_headers(self):
        self.main.sheet.set_sheet_data_with_headers(
            [[1, 12.5], [2, 13.0]], ["Batch ID", "Diameter"]
        )
        restored, _ = self._save_and_reopen()
        self.assertEqual(restored.sheet.get_column_names(), ["Batch ID", "Diameter"])

    def test_excel_import_preserves_workbook_column_names_and_values(self):
        workbook = pd.DataFrame({"Batch ID": [1, 2], "Diameter": [12.5, 13.0]})
        with patch("project_managers.project_manager.filedialog.askopenfilename", return_value="synthetic.xlsx"), \
                patch("project_managers.project_manager.pd.read_excel", return_value=workbook):
            self.manager.import_excel()
        self.assertEqual(self.main.sheet.get_column_names(), ["Batch ID", "Diameter"])
        self.assertEqual(self.main.sheet.get_sheet_data(), [[1, 12.5], [2, 13.0]])

    def test_new_project_resets_models_and_preserves_language_and_theme_preference(self):
        self._populate_models()
        self.main.current_lang = "id"
        self.main.theme = "dark"
        self.manager.current_project_path = "old.spcproj"
        with patch("project_managers.project_manager.messagebox.askyesno", return_value=True):
            self.assertTrue(self.manager.new_project())
        self.assertEqual(self.manager.current_project_path, None)
        self.assertEqual(self.main.current_lang, "id")
        self.assertEqual(self.main.theme, "dark")
        self.assertEqual(self.main.tool_models["fishbone"].effect, "")
        self.assertEqual(len(self.main.tool_models["fishbone"].categories), 6)
        self.assertEqual(self.main.tool_models["fishbone"].causes, [])
        self.assertEqual(self.main.tool_models["check_sheet"].to_dict(), {"categories": [], "records": []})
        self.assertEqual(self.main.tool_models["defect_concentration"].marks, [])
        self.assertEqual(len(self.main.tool_models["defect_concentration"].categories), 1)

    def test_legacy_project_without_tool_models_loads_safe_defaults(self):
        path = Path(self.temp.name) / "legacy.spcproj"
        path.write_text(json.dumps({"analyses": [], "sheet_data": [["legacy"]]}), encoding="utf-8")
        self.assertTrue(self.manager.load_project(path))
        self.assertEqual(self.main.sheet.get_sheet_data(), [["legacy"]])
        self.assertEqual(self.main.sheet.get_column_names(), ["C1"])
        self.assertEqual(len(self.main.tool_models["fishbone"].categories), 6)
        self.assertEqual(self.main.tool_models["check_sheet"].records, [])
        self.assertEqual(len(self.main.tool_models["defect_concentration"].categories), 1)
        self.assertEqual(self.main.tool_models["defect_concentration"].marks, [])

    def test_malformed_quality_data_is_rejected_without_mutating_session(self):
        self._populate_models()
        self.main.sheet.set_sheet_data([["active"]])
        self.main.analysis_objects = [Analysis("histogram", "Active", {}, {}, {})]
        old_models = self.main.tool_models
        old_path = "active.spcproj"
        self.manager.current_project_path = old_path
        malformed = {
            "analyses": [],
            "sheet_data": [["incoming"]],
            "tool_models": {
                "defect_concentration": {
                    "default_category_id": "missing",
                    "categories": [],
                    "marks": [{"id": "m", "category_id": "missing", "x": 0.2, "y": 0.4}],
                }
            },
        }
        path = Path(self.temp.name) / "malformed.spcproj"
        path.write_text(json.dumps(malformed), encoding="utf-8")
        self.assertFalse(self.manager.load_project(path))
        self.assertEqual(self.main.sheet.get_sheet_data(), [["active"]])
        self.assertEqual(self.main.analysis_objects[0].title, "Active")
        self.assertIs(self.main.tool_models, old_models)
        self.assertEqual(self.manager.current_project_path, old_path)

    def test_failed_load_during_commit_rolls_back_active_session(self):
        self._populate_models()
        self.main.sheet.set_sheet_data([["active"]])
        self.main.analysis_objects = [Analysis("histogram", "Active", {}, {}, {}, "Active item")]
        self.main.navigator.navigator_box.items = ["Active item"]
        self.manager.current_project_path = "active.spcproj"
        old_models = self.main.tool_models
        path = Path(self.temp.name) / "incoming.spcproj"
        path.write_text(json.dumps({
            "analyses": [Analysis("c-chart", "Incoming", {}, {}, {}, "Incoming item").to_dict()],
            "sheet_data": [["incoming"]],
        }), encoding="utf-8")
        self.main.sheet.fail_next_set = True
        self.assertFalse(self.manager.load_project(path))
        self.assertEqual(self.main.sheet.get_sheet_data(), [["active"]])
        self.assertEqual([a.title for a in self.main.analysis_objects], ["Active"])
        self.assertEqual(self.main.navigator.navigator_box.items, ["Active item"])
        self.assertIs(self.main.tool_models, old_models)
        self.assertEqual(self.manager.current_project_path, "active.spcproj")

    def test_failed_atomic_save_preserves_previous_project_file(self):
        path = Path(self.temp.name) / "existing.spcproj"
        original = '{"valid": "previous project"}'
        path.write_text(original, encoding="utf-8")
        with patch("project_managers.project_manager.os.replace", side_effect=OSError("replace denied")):
            with self.assertRaisesRegex(OSError, "replace denied"):
                self.manager._write_project(path)
        self.assertEqual(path.read_text(encoding="utf-8"), original)
        self.assertEqual(list(Path(self.temp.name).glob("*.tmp")), [])

    def test_invalid_serialized_model_is_rejected_before_file_is_touched(self):
        path = Path(self.temp.name) / "existing.spcproj"
        original = "previous valid contents"
        path.write_text(original, encoding="utf-8")
        self.main.tool_models["fishbone"].causes = [Cause("bad", "missing-category", "bad cause")]
        with self.assertRaisesRegex(ValueError, "invalid category"):
            self.manager._write_project(path)
        self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
