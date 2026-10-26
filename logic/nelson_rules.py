import math
from collections import Counter

from logic.validation import numeric_values


RULE_TEXT = {
    "Rule 1": {
        "id": ("Titik di luar batas kendali", "Titik melewati batas kendali", "Kemungkinan penyebab khusus", "Penyebab khusus mungkin telah memengaruhi proses."),
        "en": ("Point beyond control limits", "Point beyond control limits", "Possible special cause", "A special cause may have affected the process."),
    },
    "Rule 2": {
        "id": ("9 titik berturut-turut di satu sisi mean", "Pergeseran proses", "Pergeseran rata-rata proses", "Periksa perubahan sistematis pada mesin, operator, atau bahan baku."),
        "en": ("9 consecutive points on one side of the mean", "Process shift", "Process average shift", "Check for systematic changes in equipment, operators, or materials."),
    },
    "Rule 3": {
        "id": ("6 titik terus meningkat atau menurun", "Tren", "Tren sistematis", "Periksa keausan alat, drift proses, atau perubahan lingkungan bertahap."),
        "en": ("6 consecutive points increasing or decreasing", "Trend", "Systematic trend", "Check for tool wear, process drift, or gradual environmental changes."),
    },
    "Rule 4": {
        "id": ("14 titik bergerak naik-turun bergantian", "Osilasi", "Pola naik-turun bergantian", "Periksa penyesuaian berlebihan atau ketidakkonsistenan pengendalian."),
        "en": ("14 points alternating up and down", "Oscillation", "Alternating pattern", "Check for over-adjustment or inconsistent process control."),
    },
    "Rule 5": {
        "id": ("2 dari 3 titik lebih dari 2 sigma pada sisi yang sama", "Pola zona 2 sigma", "Sedikitnya 2 dari 3 titik melewati 2 sigma pada sisi yang sama", "Periksa peningkatan variasi atau perubahan proses baru-baru ini."),
        "en": ("2 of 3 points more than 2 sigma on the same side", "2-sigma zone pattern", "At least 2 of 3 points exceed 2 sigma on the same side", "Check for increased variation or a recent process change."),
    },
    "Rule 6": {
        "id": ("4 dari 5 titik lebih dari 1 sigma pada sisi yang sama", "Pola zona 1 sigma", "Sedikitnya 4 dari 5 titik melewati 1 sigma pada sisi yang sama", "Periksa penyebab variasi yang bergeser ke satu sisi."),
        "en": ("4 of 5 points more than 1 sigma on the same side", "1-sigma zone pattern", "At least 4 of 5 points exceed 1 sigma on the same side", "Check for a source of variation shifting to one side."),
    },
    "Rule 7": {
        "id": ("15 titik berada dalam zona satu sigma", "Stratifikasi", "Titik terlalu rapat di sekitar garis tengah", "Periksa pengelompokan data atau pencampuran beberapa sumber proses."),
        "en": ("15 points within one sigma", "Stratification", "Points are unusually close to the center line", "Check for data grouping or a mixture of process sources."),
    },
    "Rule 8": {
        "id": ("8 titik berturut-turut di luar zona satu sigma", "Pola zona 3 sigma", "Titik menghindari zona satu sigma", "Periksa campuran populasi atau pola dua proses yang berbeda."),
        "en": ("8 consecutive points outside one sigma", "3-sigma zone pattern", "Points avoid the one-sigma zone", "Check for mixed populations or two distinct process patterns."),
    },
}


def rule_details(rule, language="id"):
    text = RULE_TEXT.get(rule, {}).get("en" if language == "en" else "id")
    if not text:
        return {"description": "Unknown rule", "name": "Unknown", "interpretation": "No explanation", "recommendation": ""}
    return dict(zip(("description", "name", "interpretation", "recommendation"), text))


def localize_violations(violations, language="id"):
    """Return violations with descriptions and causes for the active language."""
    localized = []
    for violation in violations:
        if isinstance(violation, tuple) and len(violation) >= 3:
            rule_details_value = rule_details(violation[0], language)
            localized.append((violation[0], violation[1], rule_details_value["description"], *violation[3:]))
            continue
        item = dict(violation)
        details = rule_details(item.get("rule"), language)
        item["description"] = details["description"]
        item["cause"] = details["interpretation"]
        localized.append(item)
    return localized


def localize_chart_results(results, language="id"):
    """Refresh stored violation wording when an analysis is reopened."""
    for result in results:
        if not isinstance(result, dict):
            continue
        for key in ("violations", "xbar_violations", "s_violations"):
            if key in result:
                result[key] = localize_violations(result[key], language)
        if "xbar_violations" in result or "s_violations" in result:
            xbar = result.get("xbar_violations", [])
            variation = result.get("s_violations", [])
            total = len(xbar) + len(variation)
            english = language == "en"
            if total:
                summary = [f"Total violations detected: {total}" if english else f"Total pelanggaran terdeteksi: {total}"]
                if xbar:
                    summary.append("Xbar chart indicates instability in process mean." if english else "Grafik Xbar menunjukkan ketidakstabilan rata-rata proses.")
                if variation:
                    summary.append(("S chart" if "stds" in result.get("result", {}) else "R chart") + (" indicates instability in process variation." if english else " menunjukkan ketidakstabilan variasi proses."))
                counts = Counter(v["rule"] for v in xbar + variation)
                dominant = counts.most_common(1)[0]
                summary.append((f"Dominant violation: {dominant[0]} ({dominant[1]} times)" if english else f"Pelanggaran dominan: {dominant[0]} ({dominant[1]} kali)"))
                result["interpretation"] = "\n".join(summary)
                rules = dict.fromkeys(v["rule"] for v in xbar + variation)
                result["recommendation"] = "\n".join(
                    f"- {rule_details(rule, language)['recommendation']}" for rule in rules
                )
            else:
                result["interpretation"] = ("Process appears statistically controlled. No Nelson Rule violations detected."
                                             if english else "Proses tampak terkendali secara statistik. Tidak ditemukan pelanggaran Nelson Rules.")
                result["recommendation"] = ("Continue monitoring the process." if english else "Lanjutkan pemantauan proses.")
    return results


def _expand_limits(values, count, name):
    if isinstance(values, (int, float)):
        result = [float(values)] * count
    else:
        result = numeric_values(values, name)
        if len(result) != count:
            raise ValueError(f"{name} length must match data length")
    if any(not math.isfinite(value) for value in result):
        raise ValueError(f"{name} must contain only finite values")
    return result


def check_nelson_rules(data, mean, ucl, lcl, language="id"):
    """Return (rule, 1-based ending point, description) signals for Nelson Rules 1–8.

    Rule 7 treats points exactly one sigma from the center line as within Zone C.
    For variable limits, each point's sigma is inferred from its UCL and center line.
    """
    values = numeric_values(data, "chart data")
    if not values:
        return []
    try:
        center = float(mean)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Center line must be finite") from exc
    if not math.isfinite(center):
        raise ValueError("Center line must be finite")

    uppers = _expand_limits(ucl, len(values), "UCL")
    lowers = _expand_limits(lcl, len(values), "LCL")
    sigmas = []
    for index, (upper, lower) in enumerate(zip(uppers, lowers), start=1):
        if lower > center or upper < center or lower > upper:
            raise ValueError(f"Invalid control limits at point {index}")
        sigma = (upper - center) / 3.0
        if not math.isfinite(sigma) or sigma < 0:
            raise ValueError(f"Invalid UCL sigma at point {index}")
        sigmas.append(sigma)

    violations = []

    def add(rule, end, description):
        violations.append((f"Rule {rule}", end + 1, description))

    # Rule 1: a point strictly beyond either 3-sigma control limit.
    for i, value in enumerate(values):
        if value > uppers[i] or value < lowers[i]:
            add(1, i, "Titik di luar batas kendali")

    # Rule 2: nine consecutive points strictly on one side; points on the line break a run.
    run_side = 0
    run_length = 0
    for i, value in enumerate(values):
        side = 1 if value > center else -1 if value < center else 0
        if side and side == run_side:
            run_length += 1
        elif side:
            run_side, run_length = side, 1
        else:
            run_side, run_length = 0, 0
        if run_length >= 9:
            add(2, i, "9 titik berturut-turut di satu sisi mean")

    # Rule 3: each six-point window must be strictly monotonic.
    for start in range(max(0, len(values) - 5)):
        window = values[start:start + 6]
        if len(window) == 6 and (all(a < b for a, b in zip(window, window[1:])) or
                                  all(a > b for a, b in zip(window, window[1:]))):
            add(3, start + 5, "6 titik terus meningkat atau menurun")

    # Rule 4: 14 observations (13 consecutive direction changes), checked in sliding windows.
    for start in range(max(0, len(values) - 13)):
        window = values[start:start + 14]
        directions = [1 if b > a else -1 if b < a else 0
                      for a, b in zip(window, window[1:])]
        if len(directions) == 13 and all(
            direction != 0 and directions[index] == -directions[index - 1]
            for index, direction in enumerate(directions[1:], start=1)
        ):
            add(4, start + 13, "14 titik bergerak naik-turun bergantian")

    # Rule 5: at least two of three points beyond 2 sigma on the same side.
    for start in range(max(0, len(values) - 2)):
        window = values[start:start + 3]
        upper_count = sum(value - center > 2 * sigmas[start + offset]
                          for offset, value in enumerate(window))
        lower_count = sum(center - value > 2 * sigmas[start + offset]
                          for offset, value in enumerate(window))
        if max(upper_count, lower_count) >= 2:
            add(5, start + 2, "2 dari 3 titik lebih dari 2 sigma pada sisi yang sama")

    # Rule 6: at least four of five points beyond 1 sigma on the same side.
    for start in range(max(0, len(values) - 4)):
        window = values[start:start + 5]
        upper_count = sum(value - center > sigmas[start + offset]
                          for offset, value in enumerate(window))
        lower_count = sum(center - value > sigmas[start + offset]
                          for offset, value in enumerate(window))
        if max(upper_count, lower_count) >= 4:
            add(6, start + 4, "4 dari 5 titik lebih dari 1 sigma pada sisi yang sama")

    # Rule 7: 15 points within or exactly on the one-sigma boundary.
    for start in range(max(0, len(values) - 14)):
        if all(abs(values[start + offset] - center) <= sigmas[start + offset]
               for offset in range(15)):
            add(7, start + 14, "15 titik berada dalam zona satu sigma")

    # Rule 8: each of eight points is outside Zone C; points may be on either side.
    for start in range(max(0, len(values) - 7)):
        if all(abs(values[start + offset] - center) > sigmas[start + offset]
               for offset in range(8)):
            add(8, start + 7, "8 titik berturut-turut di luar zona satu sigma")

    if language == "en":
        violations = [(rule, point, rule_details(rule, language)["description"])
                      for rule, point, _ in violations]
    return violations
