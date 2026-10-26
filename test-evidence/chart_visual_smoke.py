"""Live Tk chart-family theme smoke test; exports actual embedded figures."""
import os
from pathlib import Path
import sys
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
from PIL import Image
from logic.chart_canvas import FigureCanvasTkAgg

from ui.main_page import MainPage
from logic.histogram import HistogramChartPopup
from logic.pareto import ParetoChartPopup
from logic.scatter import ScatterChartPopup
from logic.xbar_r import XbarRChartPopup
from logic.xbar_s import XbarSChartPopup
from logic.p_chart import PChartPopup
from logic.np_chart import NPChartPopup
from logic.c_chart import CChartPopup
from logic.u_chart import UChartPopup

OUT = Path(__file__).resolve().parent / "chart-visual"
OUT.mkdir(exist_ok=True)
BG = {"light": "#ffffff", "dark": "#202833"}

root = tk.Tk()
main = MainPage(root)
root.state("normal")
root.geometry("1180x790+70+40")
root.update()
main.sheet.set_sheet_data([
    ["Scratch", 9, 1, 2.0, 3, 100],
    ["Dent", 6, 2, 2.4, 4, 100],
    ["Chip", 4, 3, 2.1, 2, 100],
    ["", "", 4, 2.8, 5, 100],
    ["", "", 5, 2.7, 3, 100],
    ["", "", 6, 3.0, 4, 100],
])

items = [
    ("Histogram", lambda: HistogramChartPopup(main, None, [2.0, 2.4, 2.1, 2.8, 2.7, 3.0], "simple", 5, "Histogram visual QA", "Y", save_to_history=False)),
    ("Pareto", lambda: ParetoChartPopup(main, None, main.sheet, "C1", "C2", "", save_to_history=False)),
    ("Scatter", lambda: ScatterChartPopup(main, None, main.sheet, "simple", "C3", ["C4"], save_to_history=False)),
    ("Xbar-R", lambda: XbarRChartPopup(main, [{"column":"Measurement", "result":{"xbars":[10.1,10.4,9.9,10.2,10.0], "ranges":[0.4,0.5,0.3,0.6,0.4], "xbar_bar":10.12, "xbar_ucl":10.8, "xbar_lcl":9.4, "r_bar":0.44, "r_ucl":0.94, "r_lcl":0.0}, "xbar_violations":[], "s_violations":[]}], save_to_history=False)),
    ("Xbar-S", lambda: XbarSChartPopup(main, [{"column":"Measurement", "result":{"xbars":[10.1,10.4,9.9,10.2,10.0], "stds":[0.12,0.15,0.09,0.18,0.13], "xbar_bar":10.12, "xbar_ucl":10.8, "xbar_lcl":9.4, "s_bar":0.134, "s_ucl":0.29, "s_lcl":0.0}, "xbar_violations":[], "s_violations":[]}], save_to_history=False)),
    ("p", lambda: PChartPopup(main, [{"column":"Defective proportion", "result":{"proportions":[.03,.04,.02,.05,.03], "ucls":[.12]*5, "lcls":[0]*5, "p_bar":.034}, "violations":[]}], save_to_history=False)),
    ("np", lambda: NPChartPopup(main, [{"column":"Defective count", "result":{"defect_counts":[3,4,2,5,3], "np_bar":3.4, "ucl":8.8, "lcl":0}, "violations":[]}], save_to_history=False)),
    ("c", lambda: CChartPopup(main, [{"column":"Defect count", "result":{"counts":[3,4,2,5,3], "c_bar":3.4, "ucl":8.93, "lcl":0}, "violations":[]}], save_to_history=False)),
    ("u", lambda: UChartPopup(main, {"u_values":[.03,.04,.02,.05,.03], "u_bar":.034, "ucls":[.087]*5, "lcls":[0]*5}, [], "Defects per unit", save_to_history=False)),
]

def close_active():
    active = main.ui.active_chart_view
    if active is not None:
        active.destroy()
        root.update()

def figure_for(view):
    canvases = [c for c in list(FigureCanvasTkAgg.instances) if c.get_tk_widget().winfo_exists() and c.get_tk_widget().winfo_toplevel() is root]
    # Fishbone/quality views may add no Matplotlib chart. Select a figure newly
    # attached under current embedded chart view when several canvases exist.
    descendants = set()
    def walk(widget):
        for child in widget.winfo_children():
            descendants.add(child)
            walk(child)
    walk(view)
    for canvas in canvases:
        if canvas.get_tk_widget() in descendants:
            return canvas.figure, canvas
    raise AssertionError("No live FigureCanvasTkAgg was found for " + view.__class__.__name__)

def inspect(name, mode, fig, canvas):
    expected = matplotlib.colors.to_rgba(BG[mode])
    assert all(abs(a-b) < .015 for a,b in zip(fig.get_facecolor(), expected)), (name, mode, fig.get_facecolor())
    assert fig.axes, (name, mode, "no axes")
    for ax in fig.axes:
        assert all(abs(a-b) < .015 for a,b in zip(ax.get_facecolor(), expected)), (name, mode, ax.get_facecolor())
        assert ax.get_title() or ax.get_xlabel() or ax.get_ylabel() or ax.lines or ax.collections or ax.patches, (name, mode, "empty axes")
        labels = [*ax.get_xticklabels(), *ax.get_yticklabels(), ax.title, ax.xaxis.label, ax.yaxis.label]
        visible = [label for label in labels if label.get_visible() and label.get_text()]
        assert visible, (name, mode, "no visible chart text")
    fig.canvas.draw()
    root.update()
    path = OUT / f"{name.lower().replace('-', '_')}-{mode}.png"
    fig.savefig(path, dpi=120, facecolor=fig.get_facecolor(), bbox_inches="tight")
    with Image.open(path) as image:
        assert image.width > 500 and image.height > 250
        pixel = image.convert("RGB").getpixel((0, 0))
        assert all(abs(pixel[i]-round(expected[i]*255)) < 5 for i in range(3)), (name, mode, pixel)
    assert canvas.get_tk_widget().winfo_width() > 200 and canvas.get_tk_widget().winfo_height() > 150
    return str(path), fig.get_facecolor(), [ax.get_title() for ax in fig.axes]

records = []
try:
    for index, (name, create) in enumerate(items):
        close_active()
        initial = "light" if index % 2 == 0 else "dark"
        main.set_theme(initial)
        view = create()
        root.update()
        fig, canvas = figure_for(view)
        if name == "Histogram":
            assert fig.axes[0].get_title() == "Simple Histogram", fig.axes[0].get_title()
        if name == "Xbar-R":
            range_ax = fig.axes[1]
            lines = {line.get_label(): float(line.get_ydata()[0]) for line in range_ax.lines}
            assert lines["LCL = 0.0"] == 0.0, lines
            assert lines["UCL = 0.94"] == 0.94, lines
        light_record = inspect(name, initial, fig, canvas)
        other = "dark" if initial == "light" else "light"
        main.set_theme(other)
        root.update()
        switched_record = inspect(name, other, fig, canvas)
        if name == "Xbar-R":
            lines = {line.get_label(): float(line.get_ydata()[0]) for line in fig.axes[1].lines}
            assert lines["LCL = 0.0"] == 0.0 and lines["UCL = 0.94"] == 0.94, lines
        # Exercise resize/redraw on the actual embedded figure.
        before = canvas.get_tk_widget().winfo_width(), canvas.get_tk_widget().winfo_height()
        root.geometry("1040x730+80+50" if index % 2 == 0 else "1180x790+70+40")
        root.update()
        canvas.draw()
        after = canvas.get_tk_widget().winfo_width(), canvas.get_tk_widget().winfo_height()
        assert min(after) > 100
        records.append((name, light_record, switched_record, before, after))
    for name, *_ in records:
        print("PASS", name)
    for record in records:
        print("RECORD", repr(record))
finally:
    root.destroy()
