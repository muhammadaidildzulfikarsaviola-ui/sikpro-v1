import tkinter as tk
import unittest
from types import SimpleNamespace

from ui.quality_tools import CauseEditorDialog


TEXTS = {
    "cause_editor_guidance": "Enter adds a line; Ctrl+Enter saves; Escape cancels.",
    "cancel": "Cancel", "save": "Save", "error": "Error",
    "validation_cause_required": "Enter a cause.",
}


class FishboneEditorKeyboardGuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.geometry("760x540+80+70")
            self.shortcut_calls = []
            self.root.bind("<Control-z>", lambda _event: self.shortcut_calls.append("app-undo"))
            self.root.bind("<Control-y>", lambda _event: self.shortcut_calls.append("app-redo"))
            self.root.update()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.main = SimpleNamespace(root=self.root, lang_data=TEXTS,
                                    t=lambda key: TEXTS.get(key, key))
        self.saved = []
        self.dialog = CauseEditorDialog(self.main, "Edit cause", "abcdef",
                                        lambda value: self.saved.append(value))
        self.root.update()
        self.dialog.editor.focus_force()
        self.root.update()

    def tearDown(self):
        try:
            self.root.destroy()
        except (AttributeError, tk.TclError):
            pass

    def _text(self):
        return self.dialog.editor.get("1.0", "end-1c")

    def test_fish_key_001_backspace_deletes_before_caret(self):
        editor = self.dialog.editor
        editor.mark_set("insert", "1.3")
        editor.event_generate("<KeyPress-BackSpace>")
        self.root.update()
        self.assertEqual(self._text(), "abdef")

    def test_fish_key_002_delete_deletes_after_caret(self):
        editor = self.dialog.editor
        editor.mark_set("insert", "1.3")
        editor.event_generate("<KeyPress-Delete>")
        self.root.update()
        self.assertEqual(self._text(), "abcef")

    def test_fish_key_003_cursor_movement_and_mid_string_editing(self):
        editor = self.dialog.editor
        editor.mark_set("insert", "1.2")
        editor.event_generate("<KeyPress-Right>")
        self.root.update()
        self.assertEqual(str(editor.index("insert")), "1.3")
        editor.event_generate("<KeyPress-Home>")
        editor.event_generate("<KeyPress-X>")
        self.root.update()
        self.assertEqual(self._text(), "Xabcdef")
        editor.mark_set("insert", "1.4")
        editor.event_generate("<KeyPress-End>")
        self.root.update()
        self.assertEqual(str(editor.index("insert")), "1.7")

    def test_fish_key_004_select_all_and_text_undo_redo(self):
        editor = self.dialog.editor
        editor.event_generate("<Control-a>")
        self.root.update()
        self.assertEqual(editor.get("sel.first", "sel.last"), "abcdef")
        editor.insert("insert", "replacement")
        editor.edit_separator()
        editor.event_generate("<Control-z>")
        self.root.update()
        self.assertNotIn("replacement", self._text())
        editor.event_generate("<Control-y>")
        self.root.update()
        self.assertIn("replacement", self._text())
        self.assertEqual(self.shortcut_calls, [])

    def test_fish_key_005_editing_keys_do_not_invoke_diagram_action(self):
        editor = self.dialog.editor
        editor.mark_set("insert", "1.2")
        editor.event_generate("<KeyPress-BackSpace>")
        editor.event_generate("<KeyPress-Delete>")
        self.root.update()
        self.assertTrue(self.dialog.winfo_exists())
        self.assertEqual(self.saved, [])

    def test_edit_existing_cause_saves_text_without_replacing_other_content(self):
        editor = self.dialog.editor
        editor.mark_set("insert", "1.3")
        editor.event_generate("<KeyPress-BackSpace>")
        self.root.update()
        self.dialog.save()
        self.assertEqual(self.saved, ["abdef"])
        self.assertFalse(self.dialog.winfo_exists())

    def test_enter_escape_focus_loss_and_ctrl_enter_confirmation(self):
        editor = self.dialog.editor
        editor.event_generate("<KeyPress-Return>")
        self.root.update()
        self.assertEqual(self._text(), "abcdef\n")
        self.root.focus_force()
        self.root.update()
        self.assertTrue(self.dialog.winfo_exists())
        self.assertEqual(self._text(), "abcdef\n")
        editor.focus_force()
        editor.event_generate("<Escape>")
        self.root.update()
        self.assertFalse(self.dialog.winfo_exists())
        self.assertEqual(self.saved, [])

        second = CauseEditorDialog(self.main, "Add cause", "new cause",
                                   lambda value: self.saved.append(value))
        self.root.update()
        second.editor.focus_force()
        second.editor.event_generate("<Control-Return>")
        self.root.update()
        self.assertEqual(self.saved, ["new cause"])
        self.assertFalse(second.winfo_exists())


if __name__ == "__main__":
    unittest.main()
