import unittest

from models.quality_tools import FishboneModel, CheckSheetModel, DefectConcentrationModel
from help.help import HELP_DATA
from ui.dialogs import clamp_dialog_geometry, deliver_result


class FishboneModelTests(unittest.TestCase):
    def setUp(self):
        self.model = FishboneModel()

    def test_defaults_and_cause_crud_move(self):
        self.assertEqual(len(self.model.categories), 6)
        a, b = (c["id"] for c in self.model.categories[:2])
        cause_id = self.model.add_cause(a, "Long " + "description " * 20)
        self.model.edit_cause(cause_id, "edited", b)
        self.assertEqual((self.model.causes[0].category_id, self.model.causes[0].text), (b, "edited"))
        self.model.delete_cause(cause_id)
        self.assertFalse(self.model.causes)

    def test_categories_validate_and_protect_data(self):
        with self.assertRaises(ValueError): self.model.add_cause(self.model.categories[0]["id"], "  ")
        with self.assertRaises(ValueError): self.model.add_category(" man ")
        custom = self.model.add_category("Custom")
        target = self.model.categories[0]["id"]
        cause = self.model.add_cause(custom, "Cause")
        with self.assertRaises(ValueError): self.model.delete_category(custom)
        self.model.delete_category(custom, target)
        self.assertEqual(self.model.causes[0].category_id, target)
        with self.assertRaises(ValueError): self.model.delete_category(target)
        self.assertEqual(self.model.causes[0].id, cause)

    def test_localized_default_categories_keep_identifiers(self):
        ids = [c["id"] for c in self.model.categories]
        self.model.set_language("id")
        self.assertEqual(self.model.categories[0]["name"], "Manusia")
        self.assertEqual(ids, [c["id"] for c in self.model.categories])

    def test_renamed_default_and_cause_order_survive_language_change(self):
        first = self.model.categories[0]["id"]
        self.model.rename_category(first, "Operators")
        a = self.model.add_cause(first, "A")
        b = self.model.add_cause(first, "B")
        self.model.move_cause_order(b, -1)
        self.assertEqual([c.text for c in self.model.causes], ["B", "A"])
        self.model.set_language("id")
        self.assertEqual(self.model.categories[0]["name"], "Operators")


class CheckSheetModelTests(unittest.TestCase):
    def setUp(self):
        self.model = CheckSheetModel()
        self.category = self.model.add_category("Scratch")

    def test_record_crud_totals_and_no_duplicate_counting(self):
        record = self.model.add_record(self.category, "0", item="Lot A")
        self.assertEqual((self.model.totals[self.category], self.model.grand_total), (0, 0))
        self.model.edit_record(record, count="4", notes="updated")
        self.assertEqual((self.model.totals[self.category], self.model.grand_total), (4, 4))
        self.model.edit_record(record, count="2")
        self.assertEqual(self.model.grand_total, 2)
        self.model.delete_record(record)
        self.assertEqual(self.model.grand_total, 0)

    def test_counts_and_categories_validate_safely(self):
        for invalid in ("", "1.2", "-1", "NaN"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError): self.model.add_record(self.category, invalid)
        row = self.model.add_record(self.category, 3)
        with self.assertRaises(ValueError): self.model.delete_category(self.category)
        self.model.rename_category(self.category, "Dent")
        self.assertEqual(self.model.records[0]["category_id"], self.category)
        with self.assertRaises(ValueError): self.model.add_category(" dent ")
        self.model.delete_category(self.category, reassign_to=self.model.add_category("Other"))
        self.assertEqual(self.model.records[0]["id"], row)
        self.assertEqual(self.model.grand_total, 3)


class DefectConcentrationModelTests(unittest.TestCase):
    def setUp(self):
        self.model = DefectConcentrationModel()
        self.category = self.model.add_category("Dent")

    def test_marks_counts_normalized_coordinates_and_crud(self):
        mark = self.model.add_mark(self.category, .25, .75, "note")
        self.assertEqual((self.model.total, self.model.counts[self.category]), (1, 1))
        self.model.edit_mark(mark, x=.8, y=.2, note="edited")
        self.assertEqual((self.model.marks[0]["x"], self.model.marks[0]["y"]), (.8, .2))
        self.model.edit_mark(mark, x=1, y=0)
        with self.assertRaises(ValueError): self.model.edit_mark(mark, x=1.01)
        self.model.delete_mark(mark)
        self.assertEqual(self.model.total, 0)

    def test_category_assignment_and_safe_reassignment(self):
        mark = self.model.add_mark(self.category, .5, .5)
        other = self.model.add_category("Crack")
        with self.assertRaises(ValueError): self.model.add_mark(self.category, -0.01, .5)
        with self.assertRaises(ValueError): self.model.delete_category(self.category)
        self.model.delete_category(self.category, reassign_to=other)
        self.assertEqual(self.model.marks[0]["category_id"], other)
        self.assertEqual(self.model.counts[other], 1)
        self.assertEqual(self.model.marks[0]["id"], mark)

    def test_builtin_category_localizes_without_changing_identity(self):
        category_id = self.model.categories[0]["id"]
        self.model.set_language("id")
        self.assertEqual(self.model.categories[0]["name"], "Cacat")
        self.assertEqual(self.model.categories[0]["id"], category_id)


class HelpContentTests(unittest.TestCase):
    def test_six_help_topics_have_nonempty_bilingual_content(self):
        expected = {
            "en": ("Project", "Data Input", "Analysis", "Control Chart", "Export", "System"),
            "id": ("Proyek", "Input Data", "Analisis", "Peta Kendali", "Ekspor", "Sistem"),
        }
        for language, topics in expected.items():
            self.assertEqual(set(topics), set(HELP_DATA[language]))
            for topic in topics:
                self.assertTrue(HELP_DATA[language][topic])
                self.assertTrue(all(any(text.strip() for text in article.values())
                                    for article in HELP_DATA[language][topic].values()))


class DialogGeometryTests(unittest.TestCase):
    def test_dialog_geometry_is_centered_then_clamped_to_work_area(self):
        self.assertEqual(
            clamp_dialog_geometry(500, 300, (1920, 0, 3200, 1040), (2400, 500)),
            (500, 300, 2150, 350),
        )
        self.assertEqual(
            clamp_dialog_geometry(1600, 1200, (-1280, 0, 0, 800), (-640, 400)),
            (1280, 800, -1280, 0),
        )

    def test_result_dialog_closes_only_after_result_creation_succeeds(self):
        class Dialog:
            destroyed = False
            def winfo_exists(self): return True
            def destroy(self): self.destroyed = True

        config = Dialog()
        with self.assertRaises(RuntimeError):
            deliver_result(config, lambda: (_ for _ in ()).throw(RuntimeError("chart failed")))
        self.assertFalse(config.destroyed)
        result = object()
        self.assertIs(deliver_result(config, lambda: result), result)
        self.assertTrue(config.destroyed)


if __name__ == "__main__":
    unittest.main()
