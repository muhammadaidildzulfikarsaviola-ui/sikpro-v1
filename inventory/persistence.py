"""Atomic JSON persistence for the finished-goods inventory ledger."""
import copy
import json
import os
from pathlib import Path
import tempfile

from .models import InventoryBook, InventoryValidationError


FORMAT_NAME = "sikpro-inventory"
FORMAT_VERSION = 1


def default_inventory_path():
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / "SIKPRO" / "inventory.json"


class InventoryStore:
    """Commit copy-on-write inventory operations only after durable save."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_inventory_path()
        if self.path.exists():
            self.book = load_inventory(self.path)
        else:
            self.book = InventoryBook()
            self._write(self.book)

    def perform(self, operation):
        draft = copy.deepcopy(self.book)
        result = operation(draft)
        draft.validate()
        self._write(draft)
        self.book = draft
        return result

    def _write(self, book):
        payload = json.dumps({
            "format": FORMAT_NAME,
            "version": FORMAT_VERSION,
            "data": book.to_dict(),
        }, ensure_ascii=False, indent=2, allow_nan=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp",
                                         dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def load_inventory(path):
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InventoryValidationError("inventory_file_unreadable") from exc
    if not isinstance(payload, dict) or payload.get("format") != FORMAT_NAME:
        raise InventoryValidationError("inventory_file_invalid")
    if payload.get("version") != FORMAT_VERSION:
        raise InventoryValidationError("inventory_version_unsupported")
    try:
        return InventoryBook.from_dict(payload.get("data"))
    except InventoryValidationError:
        raise
    except (TypeError, ValueError) as exc:
        raise InventoryValidationError("inventory_file_invalid") from exc
