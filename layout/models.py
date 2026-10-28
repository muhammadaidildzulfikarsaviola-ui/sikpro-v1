"""Serializable domain models for facility layout planning."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any


RATINGS = ("A", "E", "I", "O", "U", "X")
DEFAULT_WEIGHTS = {"A": 6.0, "E": 5.0, "I": 4.0, "O": 3.0, "U": 2.0, "X": 0.0}
DEFAULT_X_PENALTY = 20.0


class LayoutInputError(ValueError):
    """Validation failure with stable localization keys."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(", ".join(errors))


def relation_key(first: str, second: str) -> tuple[str, str]:
    return tuple(sorted((first, second)))


@dataclass
class Department:
    id: str
    name: str
    required_area: float
    preferred_width: float | None = None
    preferred_height: float | None = None

    @property
    def preferred_aspect_ratio(self) -> float | None:
        if self.preferred_width and self.preferred_height:
            return self.preferred_width / self.preferred_height
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "required_area": self.required_area,
            "preferred_width": self.preferred_width,
            "preferred_height": self.preferred_height,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Department":
        if not isinstance(value, dict) or not isinstance(value.get("id"), str) or not isinstance(value.get("name"), str):
            raise ValueError("department ID and name must be strings")
        return cls(
            id=value["id"],
            name=value["name"],
            required_area=value["required_area"],
            preferred_width=value.get("preferred_width"),
            preferred_height=value.get("preferred_height"),
        )


@dataclass
class Relationship:
    rating: str | None = None
    reason: str = ""

    def to_dict(self, first: str, second: str) -> dict[str, Any]:
        return {"first": first, "second": second, "rating": self.rating, "reason": self.reason}


@dataclass
class Rectangle:
    x: float
    y: float
    width: float
    height: float

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Rectangle":
        return cls(value["x"], value["y"], value["width"], value["height"])


@dataclass
class LayoutAlternative:
    id: str
    name: str
    rectangles: dict[str, Rectangle]
    score: float
    violated_x: list[tuple[str, str]] = field(default_factory=list)
    flow_distance: float | None = None
    geometry_errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.geometry_errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "rectangles": {key: value.to_dict() for key, value in self.rectangles.items()},
            "score": self.score,
            "violated_x": [list(pair) for pair in self.violated_x],
            "flow_distance": self.flow_distance,
            "geometry_errors": list(self.geometry_errors),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "LayoutAlternative":
        flow = value.get("flow_distance")
        return cls(
            id=value["id"],
            name=value["name"],
            rectangles={key: Rectangle.from_dict(rect) for key, rect in value["rectangles"].items()},
            score=value["score"],
            violated_x=[tuple(pair) for pair in value.get("violated_x", [])],
            flow_distance=flow,
            geometry_errors=list(value.get("geometry_errors", [])),
        )


@dataclass
class LayoutProject:
    project_name: str = "Untitled Layout"
    floor_width: float = 40.0
    floor_height: float = 30.0
    departments: list[Department] = field(default_factory=list)
    relationships: dict[tuple[str, str], Relationship] = field(default_factory=dict)
    material_flows: dict[tuple[str, str], float] = field(default_factory=dict)
    alternatives: list[LayoutAlternative] = field(default_factory=list)
    scoring_weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    x_penalty: float = DEFAULT_X_PENALTY

    def add_department(self, name: str, area: float, preferred_width=None, preferred_height=None) -> Department:
        used = {department.id for department in self.departments}
        number = 1
        while f"D{number:02d}" in used:
            number += 1
        department = Department(f"D{number:02d}", name.strip(), float(area), preferred_width, preferred_height)
        self.departments.append(department)
        for other in self.departments[:-1]:
            self.relationships[relation_key(department.id, other.id)] = Relationship()
        self.invalidate_alternatives()
        return department

    def update_department(self, department_id: str, name: str, area: float,
                          preferred_width=None, preferred_height=None) -> None:
        department = self.get_department(department_id)
        layout_inputs_changed = (department.required_area != float(area)
                                 or department.preferred_width != preferred_width
                                 or department.preferred_height != preferred_height)
        department.name = name.strip()
        department.required_area = float(area)
        department.preferred_width = preferred_width
        department.preferred_height = preferred_height
        if layout_inputs_changed:
            self.invalidate_alternatives()

    def remove_department(self, department_id: str) -> None:
        self.departments = [d for d in self.departments if d.id != department_id]
        self.relationships = {key: value for key, value in self.relationships.items()
                              if department_id not in key}
        self.material_flows = {key: value for key, value in self.material_flows.items()
                               if department_id not in key}
        self.invalidate_alternatives()

    def get_department(self, department_id: str) -> Department:
        for department in self.departments:
            if department.id == department_id:
                return department
        raise KeyError(department_id)

    def set_relationship(self, first: str, second: str, rating: str, reason: str = "") -> None:
        if first == second or first not in {d.id for d in self.departments} or second not in {d.id for d in self.departments}:
            raise ValueError("relationship departments must be distinct members of this project")
        rating = rating.upper()
        if rating not in RATINGS:
            raise ValueError(f"rating must be one of {', '.join(RATINGS)}")
        self.relationships[relation_key(first, second)] = Relationship(rating, reason.strip())
        self.invalidate_alternatives()

    def remove_relationship(self, first: str, second: str) -> None:
        self.relationships.pop(relation_key(first, second), None)
        self.invalidate_alternatives()

    def set_material_flow(self, source: str, target: str, quantity: float | None) -> None:
        ids = {d.id for d in self.departments}
        if source not in ids or target not in ids or source == target:
            raise ValueError("flow departments must be distinct members of this project")
        key = (source, target)
        if quantity is None:
            self.material_flows.pop(key, None)
        else:
            self.material_flows[key] = float(quantity)
        self.invalidate_alternatives()

    def set_floor(self, project_name: str, width: float, height: float) -> None:
        dimensions_changed = self.floor_width != float(width) or self.floor_height != float(height)
        self.project_name = project_name.strip()
        self.floor_width = float(width)
        self.floor_height = float(height)
        if dimensions_changed:
            self.invalidate_alternatives()

    def invalidate_alternatives(self) -> None:
        self.alternatives = []

    def input_errors(self, require_complete_relationships: bool = True) -> list[str]:
        errors = []
        if not isinstance(self.project_name, str) or not self.project_name.strip():
            errors.append("project_name_required")
        if not _positive_finite(self.floor_width):
            errors.append("floor_width_positive")
        if not _positive_finite(self.floor_height):
            errors.append("floor_height_positive")
        if require_complete_relationships and not self.departments:
            errors.append("department_required")
        ids = [department.id for department in self.departments]
        names = [department.name.strip().casefold() if isinstance(department.name, str) else ""
                 for department in self.departments]
        try:
            unique_ids = len(set(ids)) == len(ids)
        except TypeError:
            unique_ids = False
        if not unique_ids:
            errors.append("department_ids_unique")
        if len(set(names)) != len(names):
            errors.append("department_names_unique")
        if any(not isinstance(value, str) or not value.strip() or "::" in value for value in ids):
            errors.append("department_id_invalid")
        if any(not name for name in names):
            errors.append("department_name_required")
        total_area = 0.0
        for department in self.departments:
            if not _positive_finite(department.required_area):
                errors.append(f"department_area_positive:{department.id}")
            else:
                total_area += department.required_area
            if (department.preferred_width is None) != (department.preferred_height is None):
                errors.append(f"department_dimensions_pair:{department.id}")
            elif department.preferred_width is not None and (
                not _positive_finite(department.preferred_width)
                or not _positive_finite(department.preferred_height)
            ):
                errors.append(f"department_dimensions_positive:{department.id}")
        if _positive_finite(self.floor_width) and _positive_finite(self.floor_height):
            if total_area > self.floor_width * self.floor_height + 1e-8:
                errors.append("required_area_exceeds_floor")
        expected_pairs = {
            relation_key(a.id, b.id)
            for index, a in enumerate(self.departments)
            for b in self.departments[index + 1:]
        }
        actual_pairs = set(self.relationships)
        if len(actual_pairs) != len(self.relationships):
            errors.append("relationship_duplicate_pair")
        if actual_pairs - expected_pairs:
            errors.append("relationship_unknown_department")
        if require_complete_relationships:
            for pair in expected_pairs - actual_pairs:
                errors.append(f"relationship_missing:{pair[0]}:{pair[1]}")
            for pair in expected_pairs & actual_pairs:
                relationship = self.relationships[pair]
                if relationship.rating not in RATINGS:
                    errors.append(f"relationship_rating_required:{pair[0]}:{pair[1]}")
        for pair, relationship in self.relationships.items():
            if relationship.rating is not None and relationship.rating not in RATINGS:
                errors.append(f"relationship_rating_invalid:{pair[0]}:{pair[1]}")
            if not isinstance(relationship.reason, str):
                errors.append(f"relationship_reason_invalid:{pair[0]}:{pair[1]}")
        known_ids = set(ids)
        for pair, quantity in self.material_flows.items():
            if len(pair) != 2 or pair[0] not in known_ids or pair[1] not in known_ids or pair[0] == pair[1]:
                errors.append("material_flow_departments_invalid")
            if not _positive_finite(quantity, allow_zero=True):
                errors.append("material_flow_quantity_invalid")
        if set(self.scoring_weights) != set(RATINGS) or any(not _finite(value) for value in self.scoring_weights.values()):
            errors.append("scoring_weights_invalid")
        if not _positive_finite(self.x_penalty, allow_zero=True):
            errors.append("x_penalty_invalid")
        return errors

    def require_valid_inputs(self, require_complete_relationships: bool = True) -> None:
        errors = self.input_errors(require_complete_relationships)
        if errors:
            raise LayoutInputError(errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "floor": {"width": self.floor_width, "height": self.floor_height},
            "departments": [department.to_dict() for department in self.departments],
            "relationships": [self.relationships[pair].to_dict(*pair) for pair in sorted(self.relationships)],
            "material_flows": [
                {"source": pair[0], "target": pair[1], "quantity": quantity}
                for pair, quantity in sorted(self.material_flows.items())
            ],
            "alternatives": [alternative.to_dict() for alternative in self.alternatives],
            "scoring": {"weights": dict(self.scoring_weights), "x_penalty": self.x_penalty},
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "LayoutProject":
        if not isinstance(value, dict):
            raise ValueError("project must be an object")
        floor = value.get("floor")
        if not isinstance(floor, dict):
            raise ValueError("floor dimensions are missing")
        project = cls(
            project_name=value.get("project_name", ""),
            floor_width=floor.get("width"),
            floor_height=floor.get("height"),
            departments=[Department.from_dict(item) for item in value.get("departments", [])],
            scoring_weights=dict(value.get("scoring", {}).get("weights", DEFAULT_WEIGHTS)),
            x_penalty=value.get("scoring", {}).get("x_penalty", DEFAULT_X_PENALTY),
        )
        for item in value.get("relationships", []):
            first, second = item["first"], item["second"]
            pair = relation_key(first, second)
            if first == second or pair in project.relationships:
                raise ValueError("relationship pairs must be unique and non-reflexive")
            project.relationships[pair] = Relationship(item.get("rating"), item.get("reason", ""))
        for item in value.get("material_flows", []):
            pair = (item["source"], item["target"])
            if pair in project.material_flows:
                raise ValueError("material flow pairs must be unique")
            project.material_flows[pair] = item["quantity"]
        project.alternatives = [LayoutAlternative.from_dict(item) for item in value.get("alternatives", [])]
        errors = project.input_errors(require_complete_relationships=False)
        if errors:
            raise LayoutInputError(errors)
        department_ids = set(item.id for item in project.departments)
        for alternative in project.alternatives:
            if (not isinstance(alternative.name, str) or not alternative.name
                    or set(alternative.rectangles) != department_ids):
                raise ValueError("alternative must contain a rectangle for every department")
            if not _finite(alternative.score):
                raise ValueError("alternative score must be finite")
            if alternative.flow_distance is not None and not _positive_finite(alternative.flow_distance, allow_zero=True):
                raise ValueError("alternative flow distance must be finite and nonnegative")
            if any(pair[0] not in department_ids or pair[1] not in department_ids for pair in alternative.violated_x):
                raise ValueError("alternative contains an unknown X relationship")
            for rectangle in alternative.rectangles.values():
                if not all(_finite(number) for number in (rectangle.x, rectangle.y, rectangle.width, rectangle.height)):
                    raise ValueError("alternative geometry must be finite")
                if rectangle.width <= 0 or rectangle.height <= 0:
                    raise ValueError("alternative rectangle dimensions must be positive")
        if project.alternatives:
            from .algorithm import closeness_score, material_flow_distance, validate_geometry, violated_x_relationships
            for alternative in project.alternatives:
                alternative.score = closeness_score(project, alternative.rectangles)
                alternative.violated_x = violated_x_relationships(project, alternative.rectangles)
                alternative.flow_distance = material_flow_distance(project, alternative.rectangles)
                alternative.geometry_errors = validate_geometry(project, alternative)
        return project


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive_finite(value: Any, allow_zero: bool = False) -> bool:
    return _finite(value) and (value >= 0 if allow_zero else value > 0)
