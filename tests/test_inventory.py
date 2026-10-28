import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from inventory.models import InventoryBook, InventoryValidationError
from inventory.persistence import FORMAT_NAME, FORMAT_VERSION, InventoryStore, load_inventory


def item_book():
    book = InventoryBook()
    item = book.create_item("FG-001", "Finished Widget", "Assembly", "pcs", 10, 3)
    return book, item


class InventoryModelTests(unittest.TestCase):
    def test_item_crud_validates_unique_sku_and_master_edit_preserves_balance(self):
        book, item = item_book()
        with self.assertRaisesRegex(InventoryValidationError, "item_code_duplicate"):
            book.create_item("fg-001", "Duplicate", "", "pcs", 5, 0)
        book.update_item(item.id, "FG-002", "Widget Rev B", "Assembly", "box", 4)
        self.assertEqual(book.balance(item.id), 10)
        self.assertEqual(book.item(item.id).code, "FG-002")
        book.set_active(item.id, False)
        with self.assertRaisesRegex(InventoryValidationError, "item_inactive"):
            book.transact(item.id, "in", 1)
        with self.assertRaisesRegex(InventoryValidationError, "item_has_history"):
            book.delete_item(item.id)

    def test_create_rejects_required_fields_and_out_of_range_quantities(self):
        book = InventoryBook()
        for args, code in [
            (("", "Widget", "", "pcs", 0, 0), "item_code_required"),
            (("FG-1", "", "", "pcs", 0, 0), "item_name_required"),
            (("FG-1", "Widget", "", "", 0, 0), "item_unit_required"),
            (("FG-1", "Widget", "", "pcs", float("nan"), 0), "opening_stock_invalid"),
            (("FG-1", "Widget", "", "pcs", 0, 1e20), "minimum_stock_invalid"),
        ]:
            with self.subTest(code=code), self.assertRaisesRegex(InventoryValidationError, code):
                book.create_item(*args)
        self.assertFalse(book.items)

    def test_stock_in_out_balances_and_rejects_invalid_or_insufficient_quantities(self):
        book, item = item_book()
        book.transact(item.id, "out", 6, "Order 51", "Shipment")
        book.transact(item.id, "in", 5, "Receipt 12")
        self.assertEqual(book.balance(item.id), 9)
        for quantity in (0, -1, float("nan"), float("inf"), 1e20):
            with self.subTest(quantity=quantity), self.assertRaises(InventoryValidationError):
                book.transact(item.id, "in", quantity)
        with self.assertRaisesRegex(InventoryValidationError, "insufficient_stock"):
            book.transact(item.id, "out", 10)
        self.assertEqual(book.balance(item.id), 9)
        self.assertEqual(len(book.transactions), 2)
        self.assertEqual(book.transactions[0].reference, "Order 51")

    def test_stocktaking_variance_adjustment_audit_and_stale_count_protection(self):
        book, item = item_book()
        row = book.stocktake(item.id, 7, "Two units damaged")
        self.assertEqual(row.system_stock, 10)
        self.assertEqual(row.variance, -3)
        self.assertEqual(book.balance(item.id), 10)
        with self.assertRaisesRegex(InventoryValidationError, "adjustment_reason_required"):
            book.adjust_to_stocktake(row.id, "  ")
        adjustment = book.adjust_to_stocktake(row.id, "Write off damaged items")
        self.assertEqual(adjustment.quantity, -3)
        self.assertEqual(book.balance(item.id), 7)
        with self.assertRaisesRegex(InventoryValidationError, "stocktake_already_adjusted"):
            book.adjust_to_stocktake(row.id, "Duplicate")

        second = book.stocktake(item.id, 6)
        book.transact(item.id, "in", 1)
        with self.assertRaisesRegex(InventoryValidationError, "stocktake_stale"):
            book.adjust_to_stocktake(second.id, "Old count")
        book.validate()

    def test_stocktake_is_stale_after_later_movements_even_if_net_balance_is_unchanged(self):
        book, item = item_book()
        row = book.stocktake(item.id, 8)
        book.transact(item.id, "out", 2)
        book.transact(item.id, "in", 2)
        self.assertEqual(book.balance(item.id), row.system_stock)
        with self.assertRaisesRegex(InventoryValidationError, "stocktake_stale"):
            book.adjust_to_stocktake(row.id, "Recount required")

    def test_adjustment_cannot_make_balance_negative_and_deletion_never_discards_stock(self):
        book, item = item_book()
        with self.assertRaisesRegex(InventoryValidationError, "item_has_history"):
            book.delete_item(item.id)
        row = book.stocktake(item.id, 0)
        book.adjust_to_stocktake(row.id, "Counted empty")
        self.assertEqual(book.balance(item.id), 0)


class InventoryPersistenceTests(unittest.TestCase):
    def test_ledger_round_trip_persists_balances_and_audit_history(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder:
            path = Path(folder) / "inventory.json"
            store = InventoryStore(path)
            item = store.perform(lambda book: book.create_item("FG-77", "Widget", "", "pcs", 8, 2))
            tx = store.perform(lambda book: book.transact(item.id, "out", 3, "SO-4", "Packed"))
            count = store.perform(lambda book: book.stocktake(item.id, 4, "Counted at rack A"))
            store.perform(lambda book: book.adjust_to_stocktake(count.id, "Damaged in storage"))
            reopened = InventoryStore(path)
            self.assertEqual(reopened.book.balance(item.id), 4)
            self.assertEqual(reopened.book.transactions[0].id, tx.id)
            self.assertEqual(reopened.book.adjustments[0].reason, "Damaged in storage")
            self.assertEqual(reopened.book.stocktakes[0].variance, -1)

    def test_failed_atomic_save_preserves_file_and_in_memory_inventory(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as folder:
            path = Path(folder) / "inventory.json"
            store = InventoryStore(path)
            previous = path.read_bytes()
            with patch("inventory.persistence.os.replace", side_effect=OSError("replace blocked")):
                with self.assertRaises(OSError):
                    store.perform(lambda book: book.create_item("FG-1", "Widget", "", "pcs", 5, 1))
            self.assertEqual(store.book.items, [])
            self.assertEqual(path.read_bytes(), previous)
            self.assertEqual(list(Path(folder).glob("*.tmp")), [])

    def test_malformed_or_unsupported_inventory_is_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "inventory.json"
            for contents, error in (("{broken", "inventory_file_unreadable"),
                                    (json.dumps({"format": FORMAT_NAME, "version": FORMAT_VERSION + 1,
                                                 "data": {}}), "inventory_version_unsupported"),
                                    (json.dumps({"format": FORMAT_NAME, "version": FORMAT_VERSION,
                                                 "data": {"items": [{"bad": "row"}]}}),
                                     "inventory_data_invalid")):
                path.write_text(contents, encoding="utf-8")
                before = path.read_text(encoding="utf-8")
                with self.subTest(error=error), self.assertRaisesRegex(InventoryValidationError, error):
                    load_inventory(path)
                self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_historical_negative_balance_is_rejected_even_if_later_receipt_recovers(self):
        book, item = item_book()
        outgoing = book.transact(item.id, "out", 6, occurred_at="2026-01-01T10:01:00+07:00")
        book.transact(item.id, "in", 5, occurred_at="2026-01-01T10:02:00+07:00")
        payload = {"format": FORMAT_NAME, "version": FORMAT_VERSION, "data": book.to_dict()}
        outgoing.quantity = 12
        payload["data"]["transactions"][0]["quantity"] = 12
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invalid.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(InventoryValidationError, "inventory_data_invalid"):
                load_inventory(path)


if __name__ == "__main__":
    unittest.main()
