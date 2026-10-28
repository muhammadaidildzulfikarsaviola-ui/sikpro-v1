"""Coordinate fitting and compact label helpers for the Layout canvas."""
import math


def fit_floor_view(canvas_width, canvas_height, floor_width, floor_height, padding=34):
    """Return a centered, aspect-preserving floor-to-canvas transform."""
    values = (canvas_width, canvas_height, floor_width, floor_height, padding)
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values):
        raise ValueError("view dimensions must be finite numbers")
    if canvas_width <= 2 * padding or canvas_height <= 2 * padding:
        raise ValueError("canvas is too small for the requested padding")
    if floor_width <= 0 or floor_height <= 0:
        raise ValueError("floor dimensions must be positive")
    scale = min((canvas_width - 2 * padding) / floor_width,
                (canvas_height - 2 * padding) / floor_height)
    drawn_width, drawn_height = floor_width * scale, floor_height * scale
    return {
        "scale": scale,
        "origin_x": (canvas_width - drawn_width) / 2,
        "origin_y": (canvas_height - drawn_height) / 2,
        "width": drawn_width,
        "height": drawn_height,
    }


def canvas_to_world(x, y, floor_height, view):
    """Map a canvas point into floor coordinates, with the floor origin below."""
    scale = view["scale"]
    return ((x - view["origin_x"]) / scale,
            floor_height - ((y - view["origin_y"]) / scale))


def fit_department_label(department_id, name, required_area, pixel_width, pixel_height):
    """Choose a label that fits inside its block, or omit it when too small.

    Full labels are preferred. The ID fallback stays unambiguous and the
    department table remains the readable source for full names and areas.
    """
    if pixel_width <= 0 or pixel_height <= 0:
        return None
    content_width = pixel_width - 8
    # Leave room for Tk's font metrics, whose rendered line height is slightly
    # taller than the nominal point size used by the estimate below.
    content_height = pixel_height - 12
    for size in (10, 9, 8, 7):
        max_chars = max(1, int(content_width / (size * 0.58)))
        name_lines = max(1, math.ceil(len(name) / max_chars))
        id_lines = max(1, math.ceil(len(department_id) / max_chars))
        area_text = f"{required_area:g} m²"
        area_lines = max(1, math.ceil(len(area_text) / max_chars))
        line_count = id_lines + name_lines + area_lines
        if line_count * size * 1.2 <= content_height:
            return f"{department_id}\n{name}\n{area_text}", size
    size = 8
    if (len(department_id) * size * 0.58 <= content_width
            and size * 1.2 <= content_height):
        return department_id, size
    return None
