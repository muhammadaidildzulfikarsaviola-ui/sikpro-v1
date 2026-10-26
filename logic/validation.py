import math
import re
from functools import wraps


def numeric_values(values, name="data"):
    """Convert a column to finite floats, allowing only trailing blank cells."""
    values = list(values)
    while values and (values[-1] is None or str(values[-1]).strip() == ""):
        values.pop()

    result = []
    for index, value in enumerate(values, start=1):
        if value is None or str(value).strip() == "":
            raise ValueError(f"{name}: blank value at row {index}")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name}: invalid number at row {index}: {value!r}") from exc
        if not math.isfinite(number):
            raise ValueError(f"{name}: non-finite number at row {index}")
        result.append(number)
    return result


def numeric_subgroups(subgroups, name="subgroups", min_size=2, max_size=10):
    if subgroups is None:
        raise ValueError(f"{name} are required")
    groups = list(subgroups)
    if not groups:
        raise ValueError(f"At least one {name[:-1]} is required")

    parsed = []
    expected_size = None
    for group_index, group in enumerate(groups, start=1):
        values = numeric_values(group, f"{name} {group_index}")
        if expected_size is None:
            expected_size = len(values)
            if not min_size <= expected_size <= max_size:
                raise ValueError(
                    f"Subgroup size must be between {min_size} and {max_size}"
                )
        elif len(values) != expected_size:
            raise ValueError(
                f"{name} {group_index} has {len(values)} values; expected {expected_size}"
            )
        parsed.append(values)
    return parsed


def handle_validation_errors(function):
    """Keep configuration dialogs open and report generation failures clearly."""
    @wraps(function)
    def wrapped(self, *args, **kwargs):
        try:
            return function(self, *args, **kwargs)
        except Exception as exc:
            from tkinter import messagebox
            main = getattr(self, "main", None)
            language = getattr(main, "current_lang", "id")
            is_english = language == "en"
            title = ("Could not generate chart" if is_english else "Gagal membuat grafik")
            detail = str(exc)
            match = re.match(r"(.+): blank value at row (\d+)$", detail)
            if match:
                detail = ((f"{match.group(1)} has a blank value in row {match.group(2)}. Fill it in or remove the row."
                           if is_english else f"{match.group(1)} memiliki nilai kosong pada baris {match.group(2)}. Isi atau hapus baris tersebut."))
            match = re.match(r"(.+): invalid number at row (\d+): (.+)$", detail)
            if match:
                detail = ((f"{match.group(1)} row {match.group(2)} must contain a number; found {match.group(3)}."
                           if is_english else f"{match.group(1)} baris {match.group(2)} harus berisi angka; ditemukan {match.group(3)}."))
            match = re.match(r"(.+): non-finite number at row (\d+)$", detail)
            if match:
                detail = ((f"{match.group(1)} row {match.group(2)} must contain a finite number."
                           if is_english else f"{match.group(1)} baris {match.group(2)} harus berisi angka yang valid."))
            translations = {
                "At least one observation is required": ("Enter at least one observation.", "Masukkan setidaknya satu pengamatan."),
                "At least one defect observation is required": ("Enter at least one defect observation.", "Masukkan setidaknya satu data cacat."),
                "At least one subgroup is required": ("Enter at least one subgroup.", "Masukkan setidaknya satu subgrup."),
                "At least one np-chart subgroup is required": ("Enter at least one np-chart subgroup.", "Masukkan setidaknya satu subgrup grafik np."),
                "I-MR chart requires at least two observations": ("Enter at least two observations for an I-MR chart.", "Masukkan setidaknya dua pengamatan untuk grafik I-MR."),
                "Center line must be finite": ("Check the center line value.", "Periksa nilai garis tengah."),
            }
            for source, localized in translations.items():
                if source in detail:
                    detail = localized[0 if is_english else 1]
                    break
            messagebox.showerror(
                title,
                detail if isinstance(exc, (ValueError, OverflowError, ZeroDivisionError)) else (
                    (f"The chart could not be created: {detail}" if is_english else f"Grafik tidak dapat dibuat: {detail}")
                ),
                parent=getattr(main, "root", self),
            )
            return None
    return wrapped
