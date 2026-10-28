"""PNG layouts and multipage PDF reports using the application's Matplotlib dependency."""
from pathlib import Path
import textwrap
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle as PatchRectangle


def _colors(palette=None):
    p = palette or {
        "plot": "#ffffff", "text": "#1e293b", "muted": "#64748b",
        "border": "#94a3b8", "accent": "#2563eb", "panel": "#f8fafc",
        "danger": "#b91c1c",
    }
    return p


_REPORT_TEXT = {
    "en": {"width": "Floor width (m)", "height": "Floor height (m)", "invalid": "INVALID LAYOUT",
            "alternative": "Alternative", "area": "Required area", "departments": "Departments",
            "relationships": "Relationships", "flows": "Material flows", "scoring": "Scoring assumptions",
            "floor": "Factory floor", "required": "Total required area", "weights": "Weights",
            "penalty": "X penalty", "formula": "Score = sum(rating weight × shared edge length) minus X penalty × shared edge length.",
            "algorithm": "Layouts use deterministic recursive rectangular cuts proportional to department areas; required areas are preserved exactly.",
            "not_blocplan": "This documented heuristic is not BLOCPLAN and does not guarantee a global optimum.",
            "valid": "Valid geometry", "invalid_status": "INVALID", "adjacent_x": "Adjacent X relationships",
            "none": "None", "load_distance": "Load-distance", "no_flows": "Not calculated (no flow data)",
            "quantity_m": "quantity·m", "preferred": "preferred", "width_axis": "Width (m)", "height_axis": "Height (m)"},
    "id": {"width": "Lebar area (m)", "height": "Panjang area (m)", "invalid": "TATA LETAK TIDAK VALID",
           "alternative": "Alternatif", "area": "Luas yang dibutuhkan", "departments": "Departemen",
           "relationships": "Hubungan kedekatan", "flows": "Aliran material", "scoring": "Asumsi skor",
           "floor": "Area pabrik", "required": "Total luas yang dibutuhkan", "weights": "Bobot",
           "penalty": "Penalti X", "formula": "Skor = jumlah (bobot nilai × panjang sisi bersama) dikurangi penalti X × panjang sisi bersama.",
           "algorithm": "Tata letak memakai potongan persegi panjang berulang dengan proporsi sesuai luas departemen; luas yang dibutuhkan dipertahankan tepat.",
           "not_blocplan": "Heuristik ini terdokumentasi, bukan BLOCPLAN, dan tidak menjamin solusi global terbaik.",
           "valid": "Geometri valid", "invalid_status": "TIDAK VALID", "adjacent_x": "Hubungan X yang bersebelahan",
           "none": "Tidak ada", "load_distance": "Beban-jarak", "no_flows": "Tidak dihitung (belum ada data aliran)",
           "quantity_m": "jumlah·m", "preferred": "pilihan", "width_axis": "Lebar (m)", "height_axis": "Panjang (m)"},
}


def _draw_layout(axis, project, alternative, palette, language="en"):
    words = _REPORT_TEXT.get(language, _REPORT_TEXT["en"])
    axis.clear()
    axis.set_facecolor(palette["plot"])
    axis.add_patch(PatchRectangle((0, 0), project.floor_width, project.floor_height,
                                  fill=False, linewidth=1.5, edgecolor=palette["text"]))
    colors = ("#dbeafe", "#dcfce7", "#fef3c7", "#fce7f3", "#e0e7ff", "#cffafe", "#ffedd5")
    for index, department in enumerate(project.departments):
        rect = alternative.rectangles.get(department.id)
        if rect is None:
            continue
        axis.add_patch(PatchRectangle((rect.x, rect.y), rect.width, rect.height,
                                      facecolor=colors[index % len(colors)],
                                      edgecolor=palette["accent"], linewidth=1.2))
        label = f"{department.name}\n{department.required_area:g} m²"
        axis.text(rect.x + rect.width / 2, rect.y + rect.height / 2, label,
                  ha="center", va="center", fontsize=8, color=palette["text"], wrap=True)
    axis.set_xlim(0, project.floor_width)
    axis.set_ylim(0, project.floor_height)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel(words["width_axis"], color=palette["text"])
    axis.set_ylabel(words["height_axis"], color=palette["text"])
    axis.tick_params(colors=palette["muted"])
    axis.set_title(f"{words['alternative']} {alternative.id[-2:]}", color=palette["text"])
    if not alternative.is_valid:
        axis.text(0.5, 0.98, words["invalid"], transform=axis.transAxes,
                  ha="center", va="top", color=palette["danger"], fontweight="bold")
    for spine in axis.spines.values():
        spine.set_color(palette["border"])


def _layout_figure(project, alternative, palette=None, language="en"):
    colors = _colors(palette)
    figure = Figure(figsize=(9, 6), facecolor=colors["plot"], constrained_layout=True)
    axis = figure.add_subplot(111)
    _draw_layout(axis, project, alternative, colors, language)
    return figure


def export_png(path, project, alternative, palette=None, language="en") -> Path:
    path = Path(path)
    figure = _layout_figure(project, alternative, palette, language)
    figure.savefig(path, format="png", dpi=160, facecolor=figure.get_facecolor())
    return path


def export_pdf(path, project, palette=None, language="en") -> Path:
    path = Path(path)
    colors = _colors(palette)
    words = _REPORT_TEXT.get(language, _REPORT_TEXT["en"])
    with PdfPages(path) as pdf:
        lines = [
            f"{words['floor']}: {project.floor_width:g} m × {project.floor_height:g} m",
            f"{words['required']}: {sum(d.required_area for d in project.departments):g} m²",
            "",
            words["departments"],
        ]
        for department in project.departments:
            dims = ""
            if department.preferred_width is not None:
                dims = f" ({words['preferred']} {department.preferred_width:g} × {department.preferred_height:g} m)"
            lines.append(f"{department.id}  {department.name} — {department.required_area:g} m²{dims}")
        lines.extend(("", words["relationships"]))
        for pair, relationship in sorted(project.relationships.items()):
            label = relationship.rating or "—"
            reason = f" — {relationship.reason}" if relationship.reason else ""
            lines.append(f"{pair[0]} ↔ {pair[1]}: {label}{reason}")
        lines.extend(("", words["flows"]))
        for (source, target), quantity in sorted(project.material_flows.items()):
            lines.append(f"{source} → {target}: {quantity:g}")
        lines.extend(("", words["scoring"]))
        lines.append(words["formula"])
        lines.append(f"{words['weights']}: {project.scoring_weights}; {words['penalty']}: {project.x_penalty:g}.")
        lines.append(words["algorithm"])
        lines.append(words["not_blocplan"])
        for index, alternative in enumerate(project.alternatives, 1):
            flow = (f"{words['load_distance']}: {alternative.flow_distance:.3f} {words['quantity_m']}"
                    if alternative.flow_distance is not None else f"{words['load_distance']}: {words['no_flows']}.")
            status = words["valid"] if alternative.is_valid else words["invalid_status"] + ": " + ", ".join(alternative.geometry_errors)
            x_text = ", ".join(f"{a}–{b}" for a, b in alternative.violated_x) or words["none"]
            lines.extend(("", f"{words['alternative']} {index}: score {alternative.score:.3f}; {status}",
                          f"{words['adjacent_x']}: {x_text}", flow))
        wrapped_lines = []
        for line in lines:
            wrapped_lines.extend(textwrap.wrap(line, width=96, break_long_words=True) if line else [""])
        # Keep each text page bounded so even projects with many departments remain readable.
        chunks = [wrapped_lines[index:index + 50] for index in range(0, len(wrapped_lines), 50)] or [[]]
        for page_index, chunk in enumerate(chunks):
            summary = Figure(figsize=(8.27, 11.69), facecolor=colors["plot"], constrained_layout=True)
            axis = summary.add_subplot(111)
            axis.axis("off")
            if page_index == 0:
                axis.text(0.03, 0.97, project.project_name, va="top", fontsize=19,
                          fontweight="bold", color=colors["text"], transform=axis.transAxes)
                text_y = 0.91
            else:
                text_y = 0.97
            axis.text(0.03, text_y, "\n".join(chunk), va="top", fontsize=9,
                      color=colors["text"], linespacing=1.35, transform=axis.transAxes)
            pdf.savefig(summary)
        for alternative in project.alternatives:
            figure = _layout_figure(project, alternative, colors, language)
            pdf.savefig(figure)
    return path
