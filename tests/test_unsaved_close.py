import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from models.quality_tools import default_tool_models
from project_managers.project_manager import ProjectManager
from ui.main_page import MainPage


class SnapshotSheet:
    def __init__(self):
        self.data = [[""]]
        self.headers = ["C1"]

    def get_sheet_data(self):
        return copy.deepcopy(self.data)

    def get_column_names(self):
        return list(self.headers)

    def clear(self):
        self.data = [[""]]
        self.headers = ["C1"]


class DirtyProjectManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.main = SimpleNamespace(
            root=object(),
            current_lang="en",
            sheet=SnapshotSheet(),
            analysis_objects=[],
            tool_models=default_tool_models("en"),
            navigator=SimpleNamespace(navigator_box=SimpleNamespace(delete=Mock())),
            t=lambda key: key,
        )
        self.manager = ProjectManager(self.main)
        self.manager.mark_saved()

    def test_sheet_analyses_and_each_quality_tool_contribute_to_dirty_state(self):
        mutations = (
            lambda: self.main.sheet.data[0].__setitem__(0, "changed"),
            lambda: self.main.analysis_objects.append(
                SimpleNamespace(to_dict=lambda: {"title": "New analysis"})
            ),
            lambda: setattr(self.main.tool_models["fishbone"], "effect", "Seal leak"),
            lambda: self.main.tool_models["check_sheet"].add_category("Scratch"),
            lambda: self.main.tool_models["defect_concentration"].add_mark(
                self.main.tool_models["defect_concentration"].default_category_id,
                0.3, 0.7, "edge",
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.manager.mark_saved()
                mutation()
                self.assertTrue(self.manager.has_unsaved_changes())

    def test_language_only_translation_of_builtin_categories_is_not_dirty(self):
        self.manager.mark_saved()
        self.main.current_lang = "id"
        self.main.tool_models["fishbone"].set_language("id")
        self.main.tool_models["defect_concentration"].set_language("id")
        self.assertFalse(self.manager.has_unsaved_changes())

    def test_successful_save_clears_dirty_state_and_failed_save_does_not(self):
        self.main.sheet.data[0][0] = "edited"
        self.manager.current_project_path = str(Path(self.temp.name) / "sample.spcproj")
        with patch.object(self.manager, "_write_project"):
            self.assertTrue(self.manager.save_project())
        self.assertFalse(self.manager.has_unsaved_changes())

        self.main.sheet.data[0][0] = "later edit"
        with patch.object(self.manager, "_write_project", side_effect=OSError("disk full")), \
                patch("project_managers.project_manager.messagebox.showerror"):
            self.assertFalse(self.manager.save_project())
        self.assertTrue(self.manager.has_unsaved_changes())

    def test_new_project_requires_confirmation_and_resets_dirty_baseline_only_on_confirm(self):
        self.main.sheet.data[0][0] = "unsaved"
        with patch("project_managers.project_manager.messagebox.askyesno", return_value=False):
            self.assertFalse(self.manager.new_project())
        self.assertTrue(self.manager.has_unsaved_changes())

        with patch("project_managers.project_manager.messagebox.askyesno", return_value=True):
            self.assertTrue(self.manager.new_project())
        self.assertFalse(self.manager.has_unsaved_changes())


class CloseDecisionTests(unittest.TestCase):
    def make_main(self, dirty, save_result=True):
        manager = SimpleNamespace(
            has_unsaved_changes=Mock(return_value=dirty),
            save_project=Mock(return_value=save_result),
        )
        main = MainPage.__new__(MainPage)
        main.ui = SimpleNamespace(project_manager=manager)
        main.root = object()
        main.t = lambda key: key
        return main, manager

    def test_clean_project_closes_without_confirmation(self):
        main, manager = self.make_main(False)
        with patch("ui.main_page.messagebox.askyesnocancel") as ask:
            self.assertTrue(main.confirm_close())
        ask.assert_not_called()
        manager.save_project.assert_not_called()

    def test_cancel_and_dont_save_choices_are_distinct_and_preserve_live_data(self):
        for answer, expected in ((None, False), (False, True)):
            main, manager = self.make_main(True)
            with self.subTest(answer=answer), patch(
                "ui.main_page.messagebox.askyesnocancel", return_value=answer
            ) as ask:
                self.assertEqual(main.confirm_close(), expected)
                ask.assert_called_once()
                manager.save_project.assert_not_called()

    def test_save_choice_closes_only_after_successful_save(self):
        for save_result in (True, False):
            main, manager = self.make_main(True, save_result)
            with self.subTest(save_result=save_result), patch(
                "ui.main_page.messagebox.askyesnocancel", return_value=True
            ):
                self.assertEqual(main.confirm_close(), save_result)
                manager.save_project.assert_called_once()


if __name__ == "__main__":
    unittest.main()
