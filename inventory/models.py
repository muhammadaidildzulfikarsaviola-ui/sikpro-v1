"""Inventory ledger models and validated stock workflows."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import math
from typing import Any
from uuid import uuid4


MAX_QUANTITY = 1_000_000_000_000


class InventoryValidationError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass
class InventoryItem:
    id: str
    code: str
    name: str
    category: str
    unit: str
    opening_stock: float
    minimum_stock: float
    active: bool = True


@dataclass
class StockTransaction:
    id: str
    item_id: str
    kind: str
    quantity: float
    occurred_at: str
    reference: str = ""
    notes: str = ""
    sequence: int = 0


@dataclass
class Stocktake:
    id: str
    item_id: str
    system_stock: float
    physical_count: float
    variance: float
    occurred_at: str
    notes: str = ""
    sequence: int = 0


@dataclass
class StockAdjustment:
    id: str
    stocktake_id: str
    item_id: str
    quantity: float
    system_before: float
    physical_count: float
    reason: str
    occurred_at: str
    sequence: int = 0


@dataclass
class InventoryBook:
    items: list[InventoryItem] = field(default_factory=list)
    transactions: list[StockTransaction] = field(default_factory=list)
    stocktakes: list[Stocktake] = field(default_factory=list)
    adjustments: list[StockAdjustment] = field(default_factory=list)

    def balance(self, item_id: str) -> float:
        item = self.item(item_id)
        incoming = sum(t.quantity for t in self.transactions if t.item_id == item_id and t.kind == "in")
        outgoing = sum(t.quantity for t in self.transactions if t.item_id == item_id and t.kind == "out")
        adjusted = sum(a.quantity for a in self.adjustments if a.item_id == item_id)
        return _clean_zero(item.opening_stock + incoming - outgoing + adjusted)

    def item(self, item_id: str) -> InventoryItem:
        for item in self.items:
            if item.id == item_id:
                return item
        raise InventoryValidationError("item_missing")

    def create_item(self, code, name, category, unit, opening_stock, minimum_stock) -> InventoryItem:
        normalized = _text(code, "item_code_required").upper()
        if any(item.code.casefold() == normalized.casefold() for item in self.items):
            raise InventoryValidationError("item_code_duplicate")
        item = InventoryItem(str(uuid4()), normalized, _text(name, "item_name_required"),
                             str(category or "").strip(), _text(unit, "item_unit_required"),
                             _quantity(opening_stock, "opening_stock_invalid"),
                             _quantity(minimum_stock, "minimum_stock_invalid"))
        self.items.append(item)
        return item

    def update_item(self, item_id, code, name, category, unit, minimum_stock):
        item = self.item(item_id)
        normalized = _text(code, "item_code_required").upper()
        if any(other.id != item_id and other.code.casefold() == normalized.casefold()
               for other in self.items):
            raise InventoryValidationError("item_code_duplicate")
        # Stock is intentionally absent from this edit path.
        item.code = normalized
        item.name = _text(name, "item_name_required")
        item.category = str(category or "").strip()
        item.unit = _text(unit, "item_unit_required")
        item.minimum_stock = _quantity(minimum_stock, "minimum_stock_invalid")
        return item

    def set_active(self, item_id, active):
        self.item(item_id).active = bool(active)

    def delete_item(self, item_id):
        self.item(item_id)
        if any(row.item_id == item_id for row in (*self.transactions, *self.stocktakes, *self.adjustments)):
            raise InventoryValidationError("item_has_history")
        if self.balance(item_id) != 0:
            raise InventoryValidationError("item_has_history")
        self.items = [item for item in self.items if item.id != item_id]

    def transact(self, item_id, kind, quantity, reference="", notes="", occurred_at=None):
        item = self.item(item_id)
        if not item.active:
            raise InventoryValidationError("item_inactive")
        if kind not in ("in", "out"):
            raise InventoryValidationError("transaction_kind_invalid")
        amount = _quantity(quantity, "transaction_quantity_invalid", allow_zero=False)
        if kind == "out" and amount > self.balance(item_id):
            raise InventoryValidationError("insufficient_stock")
        transaction = StockTransaction(
            str(uuid4()), item_id, kind, amount, _timestamp(occurred_at),
            str(reference or "").strip(), str(notes or "").strip(), self._next_sequence(),
        )
        self.transactions.append(transaction)
        return transaction

    def stocktake(self, item_id, physical_count, notes="", occurred_at=None):
        item = self.item(item_id)
        count = _quantity(physical_count, "physical_count_invalid")
        system = self.balance(item.id)
        row = Stocktake(str(uuid4()), item.id, system, count, _clean_zero(count - system),
                        _timestamp(occurred_at), str(notes or "").strip(), self._next_sequence())
        self.stocktakes.append(row)
        return row

    def adjust_to_stocktake(self, stocktake_id, reason, occurred_at=None):
        row = next((entry for entry in self.stocktakes if entry.id == stocktake_id), None)
        if row is None:
            raise InventoryValidationError("stocktake_missing")
        if any(adjustment.stocktake_id == stocktake_id for adjustment in self.adjustments):
            raise InventoryValidationError("stocktake_already_adjusted")
        explanation = _text(reason, "adjustment_reason_required")
        current = self.balance(row.item_id)
        later_changes = any(
            event.item_id == row.item_id and event.sequence > row.sequence
            for event in (*self.transactions, *self.adjustments)
        )
        if later_changes or not math.isclose(current, row.system_stock, rel_tol=1e-12, abs_tol=1e-9):
            raise InventoryValidationError("stocktake_stale")
        adjustment = StockAdjustment(
            str(uuid4()), row.id, row.item_id, row.variance, current,
            row.physical_count, explanation, _timestamp(occurred_at), self._next_sequence(),
        )
        self.adjustments.append(adjustment)
        return adjustment

    def validate(self):
        events = (*self.transactions, *self.stocktakes, *self.adjustments)
        sequences = [event.sequence for event in events]
        if (any(not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1
                for sequence in sequences)
                or len(set(sequences)) != len(sequences)
                or sorted(sequences) != list(range(1, len(sequences) + 1))):
            raise InventoryValidationError("inventory_data_invalid")
        ids = [item.id for item in self.items]
        codes = [item.code.casefold() for item in self.items]
        if len(set(ids)) != len(ids) or len(set(codes)) != len(codes):
            raise InventoryValidationError("inventory_data_invalid")
        item_ids = set(ids)
        for item in self.items:
            if not isinstance(item.id, str) or not item.id.strip():
                raise InventoryValidationError("inventory_data_invalid")
            _text(item.code, "inventory_data_invalid")
            if item.code != item.code.strip().upper():
                raise InventoryValidationError("inventory_data_invalid")
            _text(item.name, "inventory_data_invalid")
            _text(item.unit, "inventory_data_invalid")
            if not isinstance(item.category, str):
                raise InventoryValidationError("inventory_data_invalid")
            _quantity(item.opening_stock, "inventory_data_invalid")
            _quantity(item.minimum_stock, "inventory_data_invalid")
            if not isinstance(item.active, bool):
                raise InventoryValidationError("inventory_data_invalid")
        transaction_ids = set()
        for tx in self.transactions:
            if (not isinstance(tx.id, str) or not tx.id.strip() or tx.id in transaction_ids
                    or not isinstance(tx.item_id, str) or tx.item_id not in item_ids
                    or tx.kind not in ("in", "out") or not isinstance(tx.reference, str)
                    or not isinstance(tx.notes, str)):
                raise InventoryValidationError("inventory_data_invalid")
            transaction_ids.add(tx.id)
            _quantity(tx.quantity, "inventory_data_invalid", allow_zero=False)
            _timestamp(tx.occurred_at)
        stocktake_ids = set()
        for row in self.stocktakes:
            if (not isinstance(row.id, str) or not row.id.strip() or row.id in stocktake_ids
                    or not isinstance(row.item_id, str) or row.item_id not in item_ids
                    or not isinstance(row.notes, str)):
                raise InventoryValidationError("inventory_data_invalid")
            stocktake_ids.add(row.id)
            _quantity(row.system_stock, "inventory_data_invalid")
            _quantity(row.physical_count, "inventory_data_invalid")
            if not math.isclose(row.variance, row.physical_count - row.system_stock,
                                rel_tol=1e-12, abs_tol=1e-9):
                raise InventoryValidationError("inventory_data_invalid")
            _timestamp(row.occurred_at)
        adjusted_stocktakes = set()
        adjustment_ids = set()
        stocktakes_by_id = {row.id: row for row in self.stocktakes}
        for adjustment in self.adjustments:
            if (not isinstance(adjustment.id, str) or not adjustment.id.strip()
                    or adjustment.id in transaction_ids or adjustment.id in adjustment_ids
                    or not isinstance(adjustment.stocktake_id, str)
                    or adjustment.stocktake_id not in stocktake_ids
                    or adjustment.stocktake_id in adjusted_stocktakes
                    or not isinstance(adjustment.item_id, str) or adjustment.item_id not in item_ids):
                raise InventoryValidationError("inventory_data_invalid")
            adjustment_ids.add(adjustment.id)
            adjusted_stocktakes.add(adjustment.stocktake_id)
            _text(adjustment.reason, "inventory_data_invalid")
            _quantity(adjustment.system_before, "inventory_data_invalid")
            _quantity(adjustment.physical_count, "inventory_data_invalid")
            if not _finite_number(adjustment.quantity) or abs(adjustment.quantity) > MAX_QUANTITY:
                raise InventoryValidationError("inventory_data_invalid")
            stocktake = stocktakes_by_id[adjustment.stocktake_id]
            if (adjustment.item_id != stocktake.item_id
                    or not math.isclose(adjustment.quantity, stocktake.variance, rel_tol=1e-12, abs_tol=1e-9)
                    or not math.isclose(adjustment.system_before, stocktake.system_stock, rel_tol=1e-12, abs_tol=1e-9)
                    or not math.isclose(adjustment.physical_count, stocktake.physical_count,
                                        rel_tol=1e-12, abs_tol=1e-9)):
                raise InventoryValidationError("inventory_data_invalid")
            _timestamp(adjustment.occurred_at)
        balances = {item.id: item.opening_stock for item in self.items}
        stocktakes_by_id = {row.id: row for row in self.stocktakes}
        for event in sorted(events, key=lambda entry: entry.sequence):
            if isinstance(event, StockTransaction):
                change = event.quantity if event.kind == "in" else -event.quantity
                balances[event.item_id] += change
                if balances[event.item_id] < -1e-9:
                    raise InventoryValidationError("inventory_data_invalid")
            elif isinstance(event, Stocktake):
                if not math.isclose(balances[event.item_id], event.system_stock,
                                    rel_tol=1e-12, abs_tol=1e-9):
                    raise InventoryValidationError("inventory_data_invalid")
            else:
                stocktake = stocktakes_by_id[event.stocktake_id]
                if not math.isclose(balances[event.item_id], event.system_before,
                                    rel_tol=1e-12, abs_tol=1e-9):
                    raise InventoryValidationError("inventory_data_invalid")
                if event.sequence <= stocktake.sequence:
                    raise InventoryValidationError("inventory_data_invalid")
                balances[event.item_id] += event.quantity
                if balances[event.item_id] < -1e-9:
                    raise InventoryValidationError("inventory_data_invalid")
        for item in self.items:
            if not math.isclose(balances[item.id], self.balance(item.id), rel_tol=1e-12, abs_tol=1e-9):
                raise InventoryValidationError("inventory_data_invalid")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {"items": [asdict(row) for row in self.items],
                "transactions": [asdict(row) for row in self.transactions],
                "stocktakes": [asdict(row) for row in self.stocktakes],
                "adjustments": [asdict(row) for row in self.adjustments]}

    def _next_sequence(self):
        return max((event.sequence for event in
                    (*self.transactions, *self.stocktakes, *self.adjustments)), default=0) + 1

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict):
            raise InventoryValidationError("inventory_data_invalid")
        try:
            rows = cls(
                items=[InventoryItem(**row) for row in _rows(value, "items")],
                transactions=[StockTransaction(**row) for row in _rows(value, "transactions")],
                stocktakes=[Stocktake(**row) for row in _rows(value, "stocktakes")],
                adjustments=[StockAdjustment(**row) for row in _rows(value, "adjustments")],
            )
            rows.validate()
            return rows
        except (TypeError, KeyError, ValueError) as exc:
            if isinstance(exc, InventoryValidationError):
                raise
            raise InventoryValidationError("inventory_data_invalid") from exc


def _rows(value, key):
    rows = value.get(key, [])
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise InventoryValidationError("inventory_data_invalid")
    return rows


def _text(value, error):
    if not isinstance(value, str) or not value.strip():
        raise InventoryValidationError(error)
    return value.strip()


def _quantity(value, error, allow_zero=True):
    if not _finite_number(value):
        raise InventoryValidationError(error)
    if value < 0 if allow_zero else value <= 0:
        raise InventoryValidationError(error)
    if value > MAX_QUANTITY:
        raise InventoryValidationError(error)
    return float(value)


def _timestamp(value=None):
    if value is None:
        value = datetime.now().astimezone().isoformat(timespec="microseconds")
    if not isinstance(value, str):
        raise InventoryValidationError("timestamp_invalid")
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise InventoryValidationError("timestamp_invalid") from exc
    return value


def _clean_zero(value):
    return 0.0 if abs(value) < 1e-10 else float(value)


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


