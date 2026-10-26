"""Open/reopen reachable configuration dialogs in a live Tk session."""
from pathlib import Path
import sys
import tkinter as tk
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.main_page import MainPage
from ui.dialogs import _windows_window_rect, _work_area
from logic.histogram import HistogramMenuPopup
from logic.pareto import ParetoConfigPopup
from logic.scatter import ScatterMenuPopup
from logic.imr_chart import IMRConfigPopup
from logic.xbar_r import XbarRConfigPopup
from logic.xbar_s import XbarSConfigPopup
from logic.p_chart import PChartConfigPopup
from logic.np_chart import NPChartConfigPopup
from logic.c_chart import CChartConfigPopup
from logic.u_chart import UChartModePopup
from logic.converter import AttributeConverterPopup
from ui.quality_tools import CauseEditorDialog

root=tk.Tk(); app=MainPage(root); root.state("normal"); root.geometry("1120x760+100+60"); root.update()
factories=[
    ("Histogram menu",lambda:HistogramMenuPopup(app,app.sheet)),
    ("Pareto config",lambda:ParetoConfigPopup(app,app.sheet)),
    ("Scatter menu",lambda:ScatterMenuPopup(app,app.sheet)),
    ("I-MR config",lambda:IMRConfigPopup(app,app.sheet)),
    ("Xbar-R config",lambda:XbarRConfigPopup(app,app.sheet)),
    ("Xbar-S config",lambda:XbarSConfigPopup(app,app.sheet)),
    ("p config",lambda:PChartConfigPopup(app,app.sheet)),
    ("np config",lambda:NPChartConfigPopup(app,app.sheet)),
    ("c config",lambda:CChartConfigPopup(app,app.sheet)),
    ("attribute chart mode",lambda:UChartModePopup(app,app.sheet)),
    ("attribute converter",lambda:AttributeConverterPopup(app,app.sheet)),
    ("cause editor",lambda:CauseEditorDialog(app,"Edit cause","Long cause text for popup QA",lambda text:None)),
]
try:
    for name,factory in factories:
        app.set_theme("light")
        dialog=factory(); root.update()
        assert dialog.winfo_exists() and dialog.winfo_width()>100 and dialog.winfo_height()>60, name
        size=(dialog.winfo_width(),dialog.winfo_height())
        work=_work_area(root,(0,0,root.winfo_screenwidth(),root.winfo_screenheight()))
        rect=_windows_window_rect(dialog.winfo_id())
        if rect:
            assert rect[0]>=work[0] and rect[1]>=work[1] and rect[2]<=work[2] and rect[3]<=work[3],(name,rect,work)
        app.set_theme("dark"); root.update()
        assert dialog.winfo_exists(), name
        palette=app.theme_manager.palette
        if isinstance(dialog,tk.Toplevel):
            assert dialog.cget("bg")==palette["window"],(name,dialog.cget("bg"),palette["window"])
        dialog.destroy(); root.update()
        reopened=factory(); root.update()
        assert reopened.winfo_exists(), name
        app.set_theme("light"); root.update()
        reopened.destroy(); root.update()
        print("PASS",name,"size",size,"rect",rect,"work",work,flush=True)
finally:
    root.destroy()
