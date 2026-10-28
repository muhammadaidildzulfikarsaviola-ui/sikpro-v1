"""Deterministic area-preserving guillotine layout alternatives.

The documented heuristic recursively cuts a compact rectangle whose aspect
ratio matches the floor. Each cut allocates sub-rectangle area in proportion
to the required department area, so every leaf preserves area exactly. It is
not BLOCPLAN and does not claim global optimality.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import islice
import math

from .models import LayoutAlternative, LayoutProject, Rectangle, relation_key


def generate_alternatives(project: LayoutProject, limit: int = 6) -> list[LayoutAlternative]:
    """Generate up to ``limit`` distinct layouts reproducibly for fixed inputs."""
    project.require_valid_inputs(require_complete_relationships=True)
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    departments = list(project.departments)
    orders = _candidate_orders(project, departments)
    candidates = []
    seen = set()
    serial = 1
    for order in orders:
        for vertical_first in (True, False):
            rectangles = _pack_sliced_layout(project, order, vertical_first)
            signature = tuple((key, round(rect.x, 8), round(rect.y, 8),
                               round(rect.width, 8), round(rect.height, 8))
                              for key, rect in sorted(rectangles.items()))
            if signature in seen:
                continue
            seen.add(signature)
            score = closeness_score(project, rectangles)
            violations = violated_x_relationships(project, rectangles)
            flow = material_flow_distance(project, rectangles)
            alternative = LayoutAlternative(
                id=f"ALT{serial:02d}",
                name=f"Alternative {serial}",
                rectangles=rectangles,
                score=score,
                violated_x=violations,
                flow_distance=flow,
            )
            alternative.geometry_errors = validate_geometry(project, alternative)
            candidates.append((alternative, serial))
            serial += 1
    candidates.sort(key=lambda item: (-item[0].score, item[1]))
    result = [item[0] for item in islice(candidates, limit)]
    for index, alternative in enumerate(result, 1):
        alternative.id = f"ALT{index:02d}"
        alternative.name = f"Alternative {index}"
    project.alternatives = result
    return result


def _candidate_orders(project, departments):
    original = [department.id for department in departments]
    degree = {}
    for department_id in original:
        degree[department_id] = sum(
            project.scoring_weights.get(project.relationships[relation_key(department_id, other)].rating, 0.0)
            - (project.x_penalty if project.relationships[relation_key(department_id, other)].rating == "X" else 0.0)
            for other in original if other != department_id
        )
    flow = defaultdict(float)
    for (source, target), quantity in project.material_flows.items():
        flow[source] += quantity
        flow[target] += quantity
    lookup = {department.id: department for department in departments}
    proposed = [
        original,
        sorted(original, key=lambda item: (-degree[item], item)),
        sorted(original, key=lambda item: (-flow[item], -degree[item], item)),
        sorted(original, key=lambda item: (degree[item], item)),
    ]
    if len(original) > 2:
        proposed.extend(original[offset:] + original[:offset] for offset in range(1, len(original)))
    unique = []
    known = set()
    for order in proposed:
        marker = tuple(order)
        if marker not in known:
            known.add(marker)
            unique.append([lookup[key] for key in order])
    return unique


def _pack_sliced_layout(project, order, vertical_first=True):
    """Tile a centered, floor-proportional rectangle using recursive cuts.

    Subtree widths or heights are allocated by their required-area fraction.
    Thus each department has exact area without scaling its geometry after
    placement. The two root-cut orientations create genuinely different
    layouts even for a two-department project.
    """
    total_area = sum(department.required_area for department in order)
    floor_aspect = project.floor_width / project.floor_height
    plan_width = min(project.floor_width, math.sqrt(total_area * floor_aspect))
    plan_height = total_area / plan_width
    origin_x = (project.floor_width - plan_width) / 2
    origin_y = (project.floor_height - plan_height) / 2
    rectangles = {}

    def split(items, x, y, width, height, depth=0):
        if len(items) == 1:
            rectangles[items[0].id] = Rectangle(x, y, width, height)
            return
        total = sum(item.required_area for item in items)
        target = total / 2
        split_at = min(
            range(1, len(items)),
            key=lambda index: (abs(sum(item.required_area for item in items[:index]) - target), index),
        )
        first, second = items[:split_at], items[split_at:]
        first_area = sum(item.required_area for item in first)
        ratio = first_area / total
        cut_vertical = vertical_first if depth == 0 else width >= height
        if cut_vertical:
            first_width = width * ratio
            split(first, x, y, first_width, height, depth + 1)
            split(second, x + first_width, y, width - first_width, height, depth + 1)
        else:
            first_height = height * ratio
            split(first, x, y, width, first_height, depth + 1)
            split(second, x, y + first_height, width, height - first_height, depth + 1)

    split(order, origin_x, origin_y, plan_width, plan_height)
    return rectangles


def shared_boundary(first: Rectangle, second: Rectangle, tolerance=1e-8) -> float:
    vertical = 0.0
    if abs(first.x + first.width - second.x) <= tolerance or abs(second.x + second.width - first.x) <= tolerance:
        vertical = max(0.0, min(first.y + first.height, second.y + second.height)
                       - max(first.y, second.y))
    horizontal = 0.0
    if abs(first.y + first.height - second.y) <= tolerance or abs(second.y + second.height - first.y) <= tolerance:
        horizontal = max(0.0, min(first.x + first.width, second.x + second.width)
                         - max(first.x, second.x))
    return vertical + horizontal


def closeness_score(project: LayoutProject, rectangles: dict[str, Rectangle]) -> float:
    """Return Σ(weight × shared edge) − X penalty × shared edge (rating-points·m)."""
    score = 0.0
    for pair, relationship in project.relationships.items():
        if relationship.rating is None or not all(item in rectangles for item in pair):
            continue
        edge = shared_boundary(rectangles[pair[0]], rectangles[pair[1]])
        if relationship.rating == "X":
            score -= project.x_penalty * edge
        else:
            score += project.scoring_weights[relationship.rating] * edge
    return score


def violated_x_relationships(project: LayoutProject, rectangles: dict[str, Rectangle]) -> list[tuple[str, str]]:
    return sorted(
        pair for pair, relationship in project.relationships.items()
        if relationship.rating == "X" and pair[0] in rectangles and pair[1] in rectangles
        and shared_boundary(rectangles[pair[0]], rectangles[pair[1]]) > 1e-8
    )


def material_flow_distance(project: LayoutProject, rectangles: dict[str, Rectangle]) -> float | None:
    if not any(quantity > 0 for quantity in project.material_flows.values()):
        return None
    centers = {
        key: (rectangle.x + rectangle.width / 2, rectangle.y + rectangle.height / 2)
        for key, rectangle in rectangles.items()
    }
    return sum(
        quantity * (abs(centers[source][0] - centers[target][0])
                    + abs(centers[source][1] - centers[target][1]))
        for (source, target), quantity in project.material_flows.items()
    )


def validate_geometry(project: LayoutProject, alternative: LayoutAlternative, tolerance=1e-7) -> list[str]:
    errors = []
    department_ids = {department.id for department in project.departments}
    if set(alternative.rectangles) != department_ids:
        return ["geometry_department_set"]
    departments = {department.id: department for department in project.departments}
    rectangles = alternative.rectangles
    for department_id, rectangle in rectangles.items():
        if rectangle.width <= 0 or rectangle.height <= 0 or not all(
            math.isfinite(value) for value in (rectangle.x, rectangle.y, rectangle.width, rectangle.height)
        ):
            errors.append(f"geometry_dimensions:{department_id}")
            continue
        if (rectangle.x < -tolerance or rectangle.y < -tolerance
                or rectangle.x + rectangle.width > project.floor_width + tolerance
                or rectangle.y + rectangle.height > project.floor_height + tolerance):
            errors.append(f"geometry_bounds:{department_id}")
        expected_area = departments[department_id].required_area
        if abs(rectangle.area - expected_area) > max(tolerance, expected_area * 1e-7):
            errors.append(f"geometry_area:{department_id}")
    ids = sorted(rectangles)
    for index, first_id in enumerate(ids):
        first = rectangles[first_id]
        for second_id in ids[index + 1:]:
            second = rectangles[second_id]
            overlap_width = min(first.x + first.width, second.x + second.width) - max(first.x, second.x)
            overlap_height = min(first.y + first.height, second.y + second.height) - max(first.y, second.y)
            if overlap_width > tolerance and overlap_height > tolerance:
                errors.append(f"geometry_overlap:{first_id}:{second_id}")
    return errors
