"""Small independent data models for the quality tools."""
from dataclasses import dataclass
from uuid import uuid4


def _required(value, label):
    value = str(value or "").strip()
    if not value:
        raise ValueError(f"{label} is required")
    return value


@dataclass
class Cause:
    id: str
    category_id: str
    text: str


class FishboneModel:
    DEFAULTS = (("Man", "Manusia"), ("Machine", "Mesin"), ("Method", "Metode"),
                ("Material", "Material"), ("Measurement", "Pengukuran"),
                ("Mother Nature", "Lingkungan"))

    def __init__(self, language="en"):
        self.language = language
        self.effect = ""
        self.categories = [{"id": uuid4().hex, "name": names[0 if language == "en" else 1], "default": True}
                           for names in self.DEFAULTS]
        self.causes = []

    def set_language(self, language):
        self.language = language
        defaults = [c for c in self.categories if c["default"]]
        for category, names in zip(defaults, self.DEFAULTS):
            if not category.get("renamed", False):
                category["name"] = names[0 if language == "en" else 1]

    def add_category(self, name):
        name = _required(name, "Category")
        if any(c["name"].strip().casefold() == name.casefold() for c in self.categories):
            raise ValueError("Category already exists")
        item = {"id": uuid4().hex, "name": name, "default": False}
        self.categories.append(item)
        return item["id"]

    def rename_category(self, category_id, name):
        name = _required(name, "Category")
        if any(c["id"] != category_id and c["name"].strip().casefold() == name.casefold() for c in self.categories):
            raise ValueError("Category already exists")
        category = self._category(category_id)
        category["name"] = name
        if category["default"]:
            category["renamed"] = True

    def delete_category(self, category_id, reassign_to=None):
        category = self._category(category_id)
        if category["default"]:
            raise ValueError("Default categories cannot be deleted")
        dependent = [cause for cause in self.causes if cause.category_id == category_id]
        if dependent and not reassign_to:
            raise ValueError("Reassign causes before deleting this category")
        if reassign_to:
            if reassign_to == category_id:
                raise ValueError("Choose a different category")
            self._category(reassign_to)
            for cause in dependent:
                cause.category_id = reassign_to
        self.categories.remove(category)

    def add_cause(self, category_id, text):
        self._category(category_id)
        cause = Cause(uuid4().hex, category_id, _required(text, "Cause"))
        self.causes.append(cause)
        return cause.id

    def edit_cause(self, cause_id, text, category_id=None):
        cause = self._cause(cause_id)
        cause.text = _required(text, "Cause")
        if category_id:
            self._category(category_id)
            cause.category_id = category_id

    def delete_cause(self, cause_id):
        self.causes.remove(self._cause(cause_id))

    def move_cause_order(self, cause_id, offset):
        cause = self._cause(cause_id)
        peers = [item for item in self.causes if item.category_id == cause.category_id]
        index = peers.index(cause)
        target = max(0, min(len(peers) - 1, index + int(offset)))
        if target == index:
            return
        self.causes.remove(cause)
        peers = [item for item in self.causes if item.category_id == cause.category_id]
        if target >= len(peers):
            insert_at = max((i for i, item in enumerate(self.causes) if item.category_id == cause.category_id), default=len(self.causes)-1) + 1
        else:
            insert_at = self.causes.index(peers[target])
        self.causes.insert(insert_at, cause)

    def _category(self, category_id):
        for item in self.categories:
            if item["id"] == category_id:
                return item
        raise ValueError("Unknown category")

    def _cause(self, cause_id):
        for item in self.causes:
            if item.id == cause_id:
                return item
        raise ValueError("Unknown cause")


class CheckSheetModel:
    def __init__(self):
        self.categories = []
        self.records = []

    def add_category(self, name):
        name = _required(name, "Category")
        if any(c["name"].casefold() == name.casefold() for c in self.categories):
            raise ValueError("Category already exists")
        item = {"id": uuid4().hex, "name": name}
        self.categories.append(item)
        return item["id"]

    def rename_category(self, category_id, name):
        name = _required(name, "Category")
        if any(c["id"] != category_id and c["name"].casefold() == name.casefold() for c in self.categories):
            raise ValueError("Category already exists")
        self._category(category_id)["name"] = name

    def delete_category(self, category_id, reassign_to=None):
        cat = self._category(category_id)
        rows = [r for r in self.records if r["category_id"] == category_id]
        if rows and not reassign_to:
            raise ValueError("Reassign or delete records before deleting this category")
        if reassign_to:
            self._category(reassign_to)
            for row in rows:
                row["category_id"] = reassign_to
        self.categories.remove(cat)

    def add_record(self, category_id, count, date="", item="", notes=""):
        self._category(category_id)
        row = {"id": uuid4().hex, "category_id": category_id, "count": self._count(count),
               "date": str(date).strip(), "item": str(item).strip(), "notes": str(notes).strip()}
        self.records.append(row)
        return row["id"]

    def edit_record(self, record_id, **changes):
        row = self._record(record_id)
        if "category_id" in changes:
            self._category(changes["category_id"])
        if "count" in changes:
            changes["count"] = self._count(changes["count"])
        row.update({k: str(v).strip() if k in ("date", "item", "notes") else v for k, v in changes.items()})

    def delete_record(self, record_id):
        self.records.remove(self._record(record_id))

    def clear(self):
        self.records.clear()

    @property
    def totals(self):
        return {c["id"]: sum(r["count"] for r in self.records if r["category_id"] == c["id"])
                for c in self.categories}

    @property
    def grand_total(self):
        return sum(r["count"] for r in self.records)

    @staticmethod
    def _count(value):
        if value is None or str(value).strip() == "":
            raise ValueError("Count is required")
        try:
            number = int(str(value).strip())
        except (TypeError, ValueError):
            raise ValueError("Count must be a nonnegative integer")
        if number < 0:
            raise ValueError("Count must be a nonnegative integer")
        return number

    def _category(self, key):
        for item in self.categories:
            if item["id"] == key:
                return item
        raise ValueError("Unknown category")

    def _record(self, key):
        for item in self.records:
            if item["id"] == key:
                return item
        raise ValueError("Unknown record")


class DefectConcentrationModel:
    def __init__(self, language="en"):
        self.language = language
        self.default_category_id = uuid4().hex
        self.categories = [{"id": self.default_category_id,
                            "name": "Defect" if language == "en" else "Cacat",
                            "default": True}]
        self.marks = []

    def set_language(self, language):
        self.language = language
        default = next((c for c in self.categories if c["id"] == self.default_category_id), None)
        if default is not None and not default.get("renamed", False):
            default["name"] = "Defect" if language == "en" else "Cacat"

    def add_category(self, name):
        name = _required(name, "Category")
        if any(c["name"].casefold() == name.casefold() for c in self.categories):
            raise ValueError("Category already exists")
        item = {"id": uuid4().hex, "name": name}
        self.categories.append(item)
        return item["id"]

    def rename_category(self, category_id, name):
        name = _required(name, "Category")
        if any(c["id"] != category_id and c["name"].casefold() == name.casefold() for c in self.categories):
            raise ValueError("Category already exists")
        category = self._category(category_id)
        category["name"] = name
        if category.get("default"):
            category["renamed"] = True

    def delete_category(self, category_id, reassign_to=None):
        cat = self._category(category_id)
        dependent = [mark for mark in self.marks if mark["category_id"] == category_id]
        if dependent and not reassign_to:
            raise ValueError("Reassign or delete marks before deleting this category")
        if reassign_to:
            self._category(reassign_to)
            for mark in dependent:
                mark["category_id"] = reassign_to
        self.categories.remove(cat)

    def add_mark(self, category_id, x, y, note=""):
        self._category(category_id)
        x, y = float(x), float(y)
        if not (0 <= x <= 1 and 0 <= y <= 1):
            raise ValueError("Defect position must be inside the inspection area")
        item = {"id": uuid4().hex, "category_id": category_id, "x": x, "y": y, "note": str(note).strip()}
        self.marks.append(item)
        return item["id"]

    def edit_mark(self, mark_id, category_id=None, x=None, y=None, note=None):
        mark = self._mark(mark_id)
        nx = mark["x"] if x is None else float(x)
        ny = mark["y"] if y is None else float(y)
        if not (0 <= nx <= 1 and 0 <= ny <= 1):
            raise ValueError("Defect position must be inside the inspection area")
        if category_id is not None:
            self._category(category_id)
            mark["category_id"] = category_id
        mark.update(x=nx, y=ny)
        if note is not None:
            mark["note"] = str(note).strip()

    def delete_mark(self, mark_id):
        self.marks.remove(self._mark(mark_id))

    @property
    def counts(self):
        return {c["id"]: sum(m["category_id"] == c["id"] for m in self.marks) for c in self.categories}

    @property
    def total(self):
        return len(self.marks)

    def _category(self, key):
        for item in self.categories:
            if item["id"] == key:
                return item
        raise ValueError("Unknown category")

    def _mark(self, key):
        for item in self.marks:
            if item["id"] == key:
                return item
        raise ValueError("Unknown mark")
