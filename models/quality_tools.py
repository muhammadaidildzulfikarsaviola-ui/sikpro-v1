"""Small independent data models for the quality tools."""
from dataclasses import dataclass
import math
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

    def to_dict(self):
        return {
            "effect": self.effect,
            "categories": [dict(category) for category in self.categories],
            "causes": [
                {"id": cause.id, "category_id": cause.category_id, "text": cause.text}
                for cause in self.causes
            ],
        }

    @classmethod
    def from_dict(cls, data, language="en"):
        if not isinstance(data, dict):
            raise ValueError("Fishbone project data must be an object")
        effect = data.get("effect", "")
        categories = data.get("categories")
        causes = data.get("causes")
        if not isinstance(effect, str) or not isinstance(categories, list) or not isinstance(causes, list):
            raise ValueError("Fishbone project data is incomplete")
        category_ids = set()
        parsed_categories = []
        for category in categories:
            if not isinstance(category, dict):
                raise ValueError("Fishbone category must be an object")
            category_id, name = category.get("id"), category.get("name")
            if not isinstance(category_id, str) or not category_id or category_id in category_ids:
                raise ValueError("Fishbone category IDs must be unique nonempty strings")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Fishbone category names must be nonempty strings")
            if not isinstance(category.get("default", False), bool):
                raise ValueError("Fishbone category default flag must be a boolean")
            if "renamed" in category and not isinstance(category["renamed"], bool):
                raise ValueError("Fishbone category renamed flag must be a boolean")
            category_ids.add(category_id)
            parsed_categories.append(dict(category))
        parsed_causes = []
        cause_ids = set()
        for cause in causes:
            if not isinstance(cause, dict):
                raise ValueError("Fishbone cause must be an object")
            cause_id, category_id, text = cause.get("id"), cause.get("category_id"), cause.get("text")
            if not isinstance(cause_id, str) or not cause_id or cause_id in cause_ids:
                raise ValueError("Fishbone cause IDs must be unique nonempty strings")
            if category_id not in category_ids or not isinstance(text, str) or not text.strip():
                raise ValueError("Fishbone cause has invalid category or text")
            cause_ids.add(cause_id)
            parsed_causes.append(Cause(cause_id, category_id, text))
        model = cls(language)
        model.effect = effect
        model.categories = parsed_categories
        model.causes = parsed_causes
        model.set_language(language)
        return model

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

    def to_dict(self):
        return {
            "categories": [dict(category) for category in self.categories],
            "records": [dict(record) for record in self.records],
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Check Sheet project data must be an object")
        categories, records = data.get("categories"), data.get("records")
        if not isinstance(categories, list) or not isinstance(records, list):
            raise ValueError("Check Sheet project data is incomplete")
        model = cls()
        category_ids = set()
        for category in categories:
            if not isinstance(category, dict):
                raise ValueError("Check Sheet category must be an object")
            category_id, name = category.get("id"), category.get("name")
            if not isinstance(category_id, str) or not category_id or category_id in category_ids:
                raise ValueError("Check Sheet category IDs must be unique nonempty strings")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Check Sheet category names must be nonempty strings")
            category_ids.add(category_id)
            model.categories.append(dict(category))
        record_ids = set()
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Check Sheet record must be an object")
            record_id, category_id = record.get("id"), record.get("category_id")
            if not isinstance(record_id, str) or not record_id or record_id in record_ids:
                raise ValueError("Check Sheet record IDs must be unique nonempty strings")
            if category_id not in category_ids:
                raise ValueError("Check Sheet record references an unknown category")
            count = record.get("count")
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise ValueError("Check Sheet record count must be a nonnegative integer")
            if any(not isinstance(record.get(key, ""), str) for key in ("date", "item", "notes")):
                raise ValueError("Check Sheet record text fields must be strings")
            record_ids.add(record_id)
            model.records.append({
                "id": record_id,
                "category_id": category_id,
                "count": count,
                "date": record.get("date", ""),
                "item": record.get("item", ""),
                "notes": record.get("notes", ""),
            })
        return model

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

    def to_dict(self):
        return {
            "default_category_id": self.default_category_id,
            "categories": [dict(category) for category in self.categories],
            "marks": [dict(mark) for mark in self.marks],
        }

    @classmethod
    def from_dict(cls, data, language="en"):
        if not isinstance(data, dict):
            raise ValueError("Defect Concentration project data must be an object")
        default_category_id = data.get("default_category_id")
        categories, marks = data.get("categories"), data.get("marks")
        if (not isinstance(default_category_id, str) or not default_category_id
                or not isinstance(categories, list) or not isinstance(marks, list)):
            raise ValueError("Defect Concentration project data is incomplete")
        model = cls(language)
        model.categories = []
        category_ids = set()
        for category in categories:
            if not isinstance(category, dict):
                raise ValueError("Defect Concentration category must be an object")
            category_id, name = category.get("id"), category.get("name")
            if not isinstance(category_id, str) or not category_id or category_id in category_ids:
                raise ValueError("Defect Concentration category IDs must be unique nonempty strings")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Defect Concentration category names must be nonempty strings")
            if not isinstance(category.get("default", False), bool):
                raise ValueError("Defect Concentration category default flag must be a boolean")
            if "renamed" in category and not isinstance(category["renamed"], bool):
                raise ValueError("Defect Concentration renamed flag must be a boolean")
            category_ids.add(category_id)
            model.categories.append(dict(category))
        defaults = [category for category in model.categories if category.get("default")]
        if (default_category_id not in category_ids or len(defaults) != 1
                or defaults[0]["id"] != default_category_id):
            raise ValueError("Defect Concentration default category is invalid")
        model.default_category_id = default_category_id
        model.language = language
        model.set_language(language)
        mark_ids = set()
        for mark in marks:
            if not isinstance(mark, dict):
                raise ValueError("Defect Concentration mark must be an object")
            mark_id, category_id = mark.get("id"), mark.get("category_id")
            x, y, note = mark.get("x"), mark.get("y"), mark.get("note", "")
            if not isinstance(mark_id, str) or not mark_id or mark_id in mark_ids:
                raise ValueError("Defect Concentration mark IDs must be unique nonempty strings")
            if category_id not in category_ids:
                raise ValueError("Defect Concentration mark references an unknown category")
            if (isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, (int, float))
                    or not isinstance(y, (int, float)) or not math.isfinite(x) or not math.isfinite(y)
                    or not 0 <= x <= 1 or not 0 <= y <= 1):
                raise ValueError("Defect Concentration mark coordinates must be finite values from 0 to 1")
            if not isinstance(note, str):
                raise ValueError("Defect Concentration mark note must be a string")
            mark_ids.add(mark_id)
            model.marks.append({"id": mark_id, "category_id": category_id,
                                "x": float(x), "y": float(y), "note": note})
        return model

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


def default_tool_models(language="en"):
    """Create fresh editable models for a new application project."""
    return {
        "fishbone": FishboneModel(language),
        "check_sheet": CheckSheetModel(),
        "defect_concentration": DefectConcentrationModel(language),
    }
