import tkinter as tk
from tkinter import ttk
from logic.histogram import HistogramMenuPopup
from help.help import HELP_DATA
from models.analysis import Analysis
from ui.sheet import Sheet
from logic.histogram import (HistogramMenuPopup, HistogramChartPopup)
from logic.pareto import (ParetoConfigPopup, ParetoChartPopup)
from logic.scatter import (ScatterMenuPopup, ScatterChartPopup)
from project_managers.project_manager import ProjectManager
from logic.i_chart import (IndividualChartPopup, IndividualConfigPopup)
from logic.mr_chart import (MovingRangeConfigPopup, MovingRangeChartPopup)
from logic.imr_chart import (IMRChartPopup, IMRConfigPopup)
from core.lang import LANG
from logic.xbar_r import XbarRConfigPopup, XbarRChartPopup
from logic.xbar_s import XbarSConfigPopup, XbarSChartPopup
from logic.rbar import RbarConfigPopup, RbarChartPopup
from logic.sbar import SbarConfigPopup, SbarChartPopup
from logic.converter import AttributeConversionEngine, AttributeConverterPopup, AttributePreviewPopup
from logic.p_chart import PChartConfigPopup, PChartPopup
from logic.np_chart import NPChartConfigPopup, NPChartPopup
from logic.c_chart import CChartConfigPopup, CChartPopup
from logic.u_chart import UChartConfigPopup, UChartPopup, UChartModePopup, UChartConvertedPopup
from ui.quality_tools import FishboneView, CheckSheetView, DefectConcentrationView
from ui.help_view import HelpView
from ui.nav_icons import add_nav_button
from ui.dialogs import install_dialog_services
from ui.control_chart_guide import ControlChartGuide


class UI:
    def __init__(self,main):
        self.main=main
        self.help_sections={}
        self.project_manager = ProjectManager(self.main)

    def undo_action(self):

        self.main.sheet.sheet.undo()

    def redo_action(self):
        self.main.sheet.sheet.redo()

    def build(self):
        root=self.main.root
        install_dialog_services(root)
        bg = "#f3f6fa"
        panel_bg = "#ffffff"
        text_color = "#1e293b"
        muted = "#64748b"
        accent = "#2563eb"
        border = "#dbe3ec"
        root.configure(bg=bg)

        style = ttk.Style(root)
        style.configure("TButton", padding=(9, 5), font=("Segoe UI", 9))
        style.configure("TLabel", background=panel_bg, foreground=text_color, font=("Segoe UI", 9))

        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        for key, command in (
            ("new_project", self.new_project),
            ("load_project", self.load_project),
            ("save", self.save_project),
            ("save_as", self.save_as_project),
            ("import_excel", self.import_excel),
            ("export_pdf", self.project_manager.generate_report),
        ):
            file_menu.add_command(label=self.main.t(key), command=command)
        menubar.add_cascade(label=self.main.t("file"), menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label=self.main.t("undo"), command=self.undo_action, accelerator="Ctrl+Z")
        edit_menu.add_command(label=self.main.t("redo"), command=self.redo_action, accelerator="Ctrl+Y")
        menubar.add_cascade(label=self.main.t("edit"), menu=edit_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label=self.main.t("histogram"), command=self.open_histogram)
        tools_menu.add_command(label=self.main.t("pareto"), command=self.open_pareto)
        tools_menu.add_command(label=self.main.t("scatter"), command=self.open_scatter)
        tools_menu.add_command(label=self.main.t("control_chart"), command=self.open_chart_menu)
        tools_menu.add_command(label=self.main.t("check_sheet"), command=self.open_check_sheet)
        tools_menu.add_command(label=self.main.t("fishbone"), command=self.open_fishbone)
        tools_menu.add_command(label=self.main.t("defect_concentration"), command=self.open_defect_concentration)
        menubar.add_cascade(label=self.main.t("analysis_tools"), menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=self.main.t("help"), command=self.open_help)
        menubar.add_cascade(label=self.main.t("help"), menu=help_menu)

        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="English", command=lambda: self.main.set_lang("en"))
        lang_menu.add_command(label="Indonesia", command=lambda: self.main.set_lang("id"))
        menubar.add_cascade(label=self.main.t("language"), menu=lang_menu)

        theme_menu = tk.Menu(menubar, tearoff=0)
        self.theme_var = tk.StringVar(root, value=self.main.theme_manager.mode)
        theme_menu.add_radiobutton(label=self.main.t("light"), variable=self.theme_var,
                                   value="light", command=lambda: self.main.set_theme("light"))
        theme_menu.add_radiobutton(label=self.main.t("dark"), variable=self.theme_var,
                                   value="dark", command=lambda: self.main.set_theme("dark"))
        menubar.add_cascade(label=self.main.t("theme"), menu=theme_menu)
        root.config(menu=menubar)

        # Compact app identity and current project status.
        header = tk.Frame(root, bg=panel_bg, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="SIKPRO", bg=panel_bg, fg=accent,
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=(18, 12))
        tk.Frame(header, width=1, bg=border).pack(side="left", fill="y", pady=10)
        project = self.project_manager.current_project_path or getattr(self.main, "current_file", None)
        project_text = self.main.t("unsaved_project") if not project else str(project).replace("\\", "/").rsplit("/", 1)[-1]
        self.project_label = tk.Label(header, text=project_text, bg=panel_bg, fg=muted,
                 font=("Segoe UI", 9))
        self.project_label.pack(side="left", padx=12)
        tk.Frame(root, height=1, bg=border).pack(fill="x")

        body = tk.Frame(root, bg=bg)
        body.pack(fill="both", expand=True)

        # Permanent navigation. Available analysis commands reuse their existing dialogs.
        sidebar = tk.Frame(body, bg="#f8fafc", width=205)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text=self.main.t("workspace_group"), bg="#f8fafc", fg=muted,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(18, 7))
        self.nav_buttons = {}
        self.nav_buttons["data_input"] = self._add_nav_button(sidebar, "grid", self.main.t("data_input"), self.select_data_input, selected=True)
        self.nav_buttons["control_chart"] = self._add_nav_button(sidebar, "line_chart", self.main.t("control_chart"), self.open_chart_menu)

        tk.Label(sidebar, text=self.main.t("analysis_tools"), bg="#f8fafc", fg=muted,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(22, 7))
        self.nav_buttons["histogram"] = self._add_nav_button(sidebar, "bars", self.main.t("histogram"), self.open_histogram)
        self.nav_buttons["pareto"] = self._add_nav_button(sidebar, "pareto", self.main.t("pareto"), self.open_pareto)
        self.nav_buttons["scatter"] = self._add_nav_button(sidebar, "scatter", self.main.t("scatter"), self.open_scatter)
        self.nav_buttons["check_sheet"] = self._add_nav_button(sidebar, "checklist", self.main.t("check_sheet"), self.open_check_sheet)
        self.nav_buttons["fishbone"] = self._add_nav_button(sidebar, "fishbone", self.main.t("fishbone"), self.open_fishbone)
        self.nav_buttons["defect_concentration"] = self._add_nav_button(sidebar, "target", self.main.t("defect_concentration"), self.open_defect_concentration)
        tk.Label(sidebar, text=self.main.t("application_group"), bg="#f8fafc", fg=muted,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(22, 7))
        self._add_nav_button(sidebar, "new", self.main.t("new_project"), self.new_project)
        self._add_nav_button(sidebar, "folder", self.main.t("load_project"), self.load_project)
        self._add_nav_button(sidebar, "export", self.main.t("export_pdf"), self.project_manager.generate_report)
        self._add_nav_button(sidebar, "globe", self.main.t("language"), self.open_language_menu)
        self.nav_buttons["help"] = self._add_nav_button(sidebar, "help", self.main.t("help"), self.open_help)

        tk.Frame(body, width=1, bg=border).pack(side="left", fill="y")
        center = tk.Frame(body, bg=panel_bg)
        center.pack(side="left", fill="both", expand=True)

        toolbar = tk.Frame(center, bg=panel_bg, height=42)
        self.workspace_toolbar = toolbar
        toolbar.pack(fill="x", padx=18, pady=(10, 0))
        toolbar.pack_propagate(False)
        self.workspace_title = tk.Label(toolbar, text=self.main.t("data_input"), bg=panel_bg, fg=text_color,
                 font=("Segoe UI", 14, "bold"))
        self.workspace_title.pack(side="left", anchor="w")
        self.workspace_tool_help_button = ttk.Button(
            toolbar, text=self.main.t("quality_tool_help")
        )
        self.chart_return_button = ttk.Button(toolbar, text=self.main.t("data_input"),
                                               command=self.select_data_input)
        self.context_toggle_button = ttk.Button(toolbar, text=self.main.t("hide_context"), command=self.toggle_context_panel)
        self.context_toggle_button.pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text=self.main.t("column"), command=self.add_column).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text=self.main.t("redo"), command=self.redo_action).pack(side="right", padx=4)
        ttk.Button(toolbar, text=self.main.t("undo"), command=self.undo_action).pack(side="right", padx=4)
        ttk.Button(toolbar, text=self.main.t("import_excel"), command=self.import_excel).pack(side="right", padx=4)
        ttk.Button(toolbar, text=self.main.t("save"), command=self.save_project).pack(side="right", padx=4)

        self.data_workspace = tk.Frame(center, bg=panel_bg)
        self.data_workspace.pack(fill="both", expand=True)
        tk.Label(self.data_workspace, text=self.main.t("data_input_guidance"), bg=panel_bg, fg=muted,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(3, 8))
        tk.Frame(self.data_workspace, height=1, bg=border).pack(fill="x", padx=18)
        table_container = tk.Frame(self.data_workspace, bg=panel_bg)
        table_container.pack(fill="both", expand=True, padx=18, pady=14)
        self.main.sheet.build(table_container)
        self.chart_workspace = tk.Frame(center, bg=panel_bg)
        self.chart_canvas = tk.Frame(self.chart_workspace, bg=panel_bg)
        self.chart_canvas.pack(fill="both", expand=True)
        self.active_chart_view = None
        self.main.root._sikpro_chart_host = self

        tk.Frame(body, width=1, bg=border).pack(side="left", fill="y")
        self.context_panel = tk.Frame(body, bg="#f8fafc", width=265)
        self.context_panel.pack(side="right", fill="y")
        self.context_panel.pack_propagate(False)
        context_header = tk.Frame(self.context_panel, bg="#f8fafc")
        context_header.pack(fill="x", padx=14, pady=(13, 8))
        tk.Label(context_header, text=self.main.t("context_panel"), bg="#f8fafc", fg=text_color,
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        self.context_title = tk.Label(self.context_panel, text=self.main.t("input_guidance"), bg="#f8fafc", fg=muted,
                 font=("Segoe UI", 9, "bold"))
        self.context_title.pack(anchor="w", padx=14, pady=(4, 2))
        self.context_help = tk.Label(self.context_panel, text=self.main.t("context_data_help"), bg="#f8fafc", fg=text_color,
                 font=("Segoe UI", 9), justify="left", wraplength=230)
        self.context_help.pack(anchor="w", padx=14, pady=(0, 14))
        tk.Frame(self.context_panel, height=1, bg=border).pack(fill="x", padx=14)
        tk.Label(self.context_panel, text=self.main.t("analysis_history"), bg="#f8fafc", fg=text_color,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 5))
        self.navigator_box = tk.Listbox(self.context_panel, height=9, relief="flat", bd=0,
            bg="#ffffff", fg=text_color, selectbackground="#dbeafe", selectforeground=text_color,
            highlightthickness=1, highlightbackground=border, font=("Segoe UI", 9), activestyle="none")
        self.navigator_box.pack(fill="x", padx=14)
        self.navigator_box.bind("<Double-Button-1>", self.open_analysis)
        self.navigator_box.bind("<<ListboxSelect>>", self.show_analysis_context)
        self.context_detail = tk.Label(self.context_panel, text=self.main.t("context_empty"),
            bg="#f8fafc", fg=muted, font=("Segoe UI", 9), justify="left", wraplength=230)
        self.context_detail.pack(anchor="w", padx=14, pady=12)
        self.context_visible = True
        self.main.navigator = self

        self.main.root.bind("<Control-s>", lambda e: self.save_project())
        self.main.root.bind("<Control-Shift-s>", lambda e: self.save_as_project())
        self.main.root.bind("<Control-z>", lambda e: self.undo_action())
        self.main.root.bind("<Control-y>", lambda e: self.redo_action())
        self.main.root.bind("<Control-o>", lambda e: self.load_project())
        self.main.root.bind("<Control-n>", lambda e: self.new_project())
        self.main.root.bind("<Control-i>", lambda e: self.import_excel())
        self.main.root.bind("<Control-p>", lambda e: self.project_manager.generate_report())
        self.main.root.bind("<F1>", lambda e: self.open_help())
        self.main.theme_manager.install(root)

    def _add_nav_button(self, parent, icon, label, command, selected=False, enabled=True):
        return add_nav_button(parent, icon, label, command, selected, enabled)

    def select_data_input(self):
        previous = self.active_chart_view
        self.active_chart_view = None
        if previous is not None:
            close_handler = getattr(previous, "close_all", None)
            if close_handler:
                close_handler()
            else:
                previous.destroy()
        self.chart_workspace.pack_forget()
        self.data_workspace.pack(fill="both", expand=True)
        self.workspace_title.configure(text=self.main.t("data_input"))
        self.chart_return_button.pack_forget()
        self.context_title.configure(text=self.main.t("input_guidance"))
        self.context_help.configure(text=self.main.t("context_data_help"))
        self.workspace_tool_help_button.pack_forget()
        self.set_active_navigation("data_input")

    def prepare_chart_view(self):
        previous = self.active_chart_view
        self.active_chart_view = None
        if previous is not None:
            close_handler = getattr(previous, "close_all", None)
            if close_handler:
                close_handler()
            else:
                previous.destroy()
        self.data_workspace.pack_forget()
        self.chart_workspace.pack(fill="both", expand=True)
        self.context_title.configure(text=self.main.t("chart_context"))
        self.context_help.configure(text=self.main.t("chart_context_guidance"))
        self.workspace_tool_help_button.pack_forget()

    def activate_chart_view(self, chart):
        self.active_chart_view = chart
        class_name = type(chart).__name__
        nav_key = {
            "HistogramChartPopup": "histogram",
            "ParetoChartPopup": "pareto",
            "ScatterChartPopup": "scatter",
        }.get(class_name, "control_chart")
        self.set_active_navigation(nav_key)
        self.workspace_title.configure(text=self.main.t("chart_view"))
        self.chart_return_button.pack(side="left", padx=(14, 0))

    def set_chart_title(self, title):
        self.workspace_title.configure(text=title)

    def chart_view_destroyed(self, chart):
        if getattr(self, "active_chart_view", None) is chart:
            self.active_chart_view = None

    def set_active_navigation(self, selected_key):
        for key, button in self.nav_buttons.items():
            is_selected = key == selected_key
            button.selected = is_selected
            button.set_theme(self.main.theme_manager.palette)

    def refresh_project_label(self):
        path = self.project_manager.current_project_path or getattr(self.main, "current_file", None)
        label = self.main.t("unsaved_project") if not path else str(path).replace("\\", "/").rsplit("/", 1)[-1]
        self.project_label.configure(text=label)

    def save_project(self):
        self.project_manager.save_project()
        self.refresh_project_label()

    def save_as_project(self):
        self.project_manager.save_as_project()
        self.refresh_project_label()

    def load_project(self):
        if self.project_manager.load_project():
            self.select_data_input()
        self.refresh_project_label()

    def new_project(self):
        if self.project_manager.new_project():
            self.select_data_input()
        self.refresh_project_label()

    def import_excel(self):
        previous_data = self.main.sheet.get_sheet_data()
        self.project_manager.import_excel()
        if self.main.sheet.get_sheet_data() != previous_data:
            self.select_data_input()

    def add_column(self):
        sheet = self.main.sheet.sheet
        sheet.insert_column(idx=sheet.total_columns(), width=120, header=False)
        self.main.sheet.update_headers()

    def open_language_menu(self):
        menu = tk.Menu(self.main.root, tearoff=0)
        menu.add_command(label="English", command=lambda: self.main.set_lang("en"))
        menu.add_command(label="Indonesia", command=lambda: self.main.set_lang("id"))
        menu.tk_popup(self.main.root.winfo_pointerx(), self.main.root.winfo_pointery())

    def toggle_context_panel(self):
        if self.context_visible:
            self.context_panel.pack_forget()
            self.context_toggle_button.configure(text=self.main.t("show_context"))
        else:
            self.context_panel.pack(side="right", fill="y")
            self.context_toggle_button.configure(text=self.main.t("hide_context"))
        self.context_visible = not self.context_visible

    def show_analysis_context(self, event=None):
        selected = self.navigator_box.curselection()
        if not selected or selected[0] >= len(self.main.analysis_objects):
            return
        analysis = self.main.analysis_objects[selected[0]]
        lines = [analysis.title or analysis.analysis_type]
        stats = analysis.stats if isinstance(analysis.stats, dict) else {}
        lines.extend(f"{key.replace('_', ' ').title()}: {value}" for key, value in stats.items()
                     if isinstance(value, (int, float, str)))
        data = analysis.data if isinstance(analysis.data, dict) else {}
        signals = []
        for key in ("violations", "xbar_violations", "s_violations"):
            values = data.get(key, [])
            if isinstance(values, (list, tuple)):
                signals.extend(values)
        if signals:
            lines.append(f'{self.main.t("detected_violations")}: {len(signals)}')
            for signal in signals[:5]:
                if isinstance(signal, dict):
                    rule = signal.get("rule", "")
                    point = signal.get("point")
                elif isinstance(signal, (list, tuple)) and len(signal) >= 2:
                    rule, point = signal[0], signal[1]
                else:
                    continue
                lines.append(f"{rule} · {self.main.t('point')} {point}" if point is not None else str(rule))
        kind = str(analysis.analysis_type).casefold()
        if kind == "p-chart" and not {"ucls", "lcls"}.issubset(data):
            lines.append(self.main.t("saved_limits_unavailable"))
        if kind == "u-chart" and not {"ucls", "lcls"}.issubset(data):
            lines.append(self.main.t("saved_limits_unavailable"))
        self.context_detail.configure(text="\n".join(lines))

    def open_histogram(self):
        HistogramMenuPopup(self.main, self.main.sheet)

    def open_pareto(self):
        ParetoConfigPopup(self.main, self.main.sheet)

    def open_scatter(self):
        ScatterMenuPopup(self.main, self.main.sheet)

    def open_fishbone(self):
        FishboneView(self.main)

    def open_check_sheet(self):
        CheckSheetView(self.main)

    def open_defect_concentration(self):
        DefectConcentrationView(self.main)

    def open_help(self):
        HelpView(self.main)

    def open_chart_menu(self):
        return ControlChartGuide(self.main, self.main.sheet)

    def build_help_dropdown(self,parent,data,level=0):
        
        for key,value in data.items():

            container=tk.Frame(
                parent,
                bg="white"
            )

            container.pack(
                fill="x",
                anchor="w"
            )

            if isinstance(value,dict):

                state={"open":False}

                header=tk.Frame(
                    container,
                    bg="white",
                    cursor="hand2"
                )

                header.pack(fill="x")

                icon=tk.Label(
                    header,
                    text="▶",
                    bg="white"
                )

                icon.pack(
                    side="left",
                    padx=(10+(level*15),5)
                )

                tk.Label(
                    header,
                    text=key,
                    bg="white",
                    font=("Arial",10,"bold")
                ).pack(
                    side="left",
                    pady=4
                )

                body=tk.Frame(
                    container,
                    bg="white"
                )

                def toggle(
                    body=body,
                    icon=icon,
                    state=state
                ):

                    if state["open"]:

                        body.pack_forget()

                        icon.config(
                            text="▶"
                        )

                        state["open"]=False

                    else:

                        body.pack(
                            fill="x"
                        )

                        icon.config(
                            text="▼"
                        )

                        state["open"]=True

                header.bind(
                    "<Button-1>",
                    lambda e,toggle=toggle:toggle()
                )

                icon.bind(
                    "<Button-1>",
                    lambda e,toggle=toggle:toggle()
                )

                self.build_help_dropdown(
                    body,
                    value,
                    level+1
                )

            else:

                state={"open":False}

                header=tk.Frame(
                    container,
                    bg="white",
                    cursor="hand2"
                )

                header.pack(fill="x")

                icon=tk.Label(
                    header,
                    text="▶",
                    bg="white"
                )

                icon.pack(
                    side="left",
                    padx=(10+(level*15),5)
                )

                tk.Label(
                    header,
                    text=key,
                    bg="white"
                ).pack(
                    side="left",
                    pady=4
                )

                body=tk.Label(
                    container,
                    text=value.strip(),
                    justify="left",
                    anchor="w",
                    bg="#f8fafc",
                    wraplength=220,
                    padx=10,
                    pady=8
                )

                def toggle_text(
                    body=body,
                    icon=icon,
                    state=state
                ):

                    if state["open"]:

                        body.pack_forget()

                        icon.config(
                            text="▶"
                        )

                        state["open"]=False

                    else:

                        body.pack(
                            fill="x",
                            padx=10,
                            pady=(0,5)
                        )

                        icon.config(
                            text="▼"
                        )

                        state["open"]=True

                header.bind(
                    "<Button-1>",
                    lambda e,toggle_text=toggle_text:toggle_text()
                )

                icon.bind(
                    "<Button-1>",
                    lambda e,toggle_text=toggle_text:toggle_text()
                )
    
    def add_analysis(self, analysis, save=True):
        if save:
            self.main.analysis_objects.append(analysis)
        self.navigator_box.insert(tk.END, analysis.navigator_name or analysis.title or analysis.analysis_type)
        if save:
            last = self.navigator_box.size() - 1
            self.navigator_box.selection_clear(0, tk.END)
            self.navigator_box.selection_set(last)
            self.navigator_box.see(last)
            self.show_analysis_context()

    def open_analysis(self, event):
        selected = self.navigator_box.curselection()
        index = selected[0] if selected else self.navigator_box.nearest(event.y)
        if index < 0 or index >= len(self.main.analysis_objects):
            return

        analysis = self.main.analysis_objects[index]
        kind = str(analysis.analysis_type).casefold()
        data = analysis.data if isinstance(analysis.data, dict) else {}
        stats = analysis.stats if isinstance(analysis.stats, dict) else {}
        settings = analysis.settings if isinstance(analysis.settings, dict) else {}
        column = settings.get("column", "")

        if kind == "histogram":
            HistogramChartPopup(
                self.main, None, analysis.data, settings["mode"], settings["bins"],
                settings["title"], settings["column_name"], save_to_history=False,
            )
        elif kind == "scatterplot":
            ScatterChartPopup(
                self.main, None, self.main.sheet, settings["mode"], settings["x_col"],
                settings["y_cols"], settings.get("group_col", ""), save_to_history=False,
            )
        elif kind == "pareto":
            ParetoChartPopup(
                self.main, None, self.main.sheet, settings["defect_col"],
                settings.get("freq_col", ""), settings.get("by_col", ""),
                analysis=analysis, save_to_history=False,
            )
        elif kind == "i-mr":
            IMRChartPopup(
                self.main, None, data["values"], column, data.get("violations", []),
                save_to_history=False,
            )
        elif kind == "xbar-r":
            result = {key: stats[key] for key in (
                "xbar_bar", "r_bar", "xbar_ucl", "xbar_lcl", "r_ucl", "r_lcl",
            )}
            result.update({"xbars": data["xbars"], "ranges": data["ranges"]})
            XbarRChartPopup(self.main, [{
                "column": column, "result": result,
                "xbar_violations": data.get("xbar_violations", []),
                "s_violations": data.get("s_violations", []),
            }], save_to_history=False)
        elif kind == "xbar-s":
            result = {key: stats[key] for key in (
                "xbar_bar", "s_bar", "xbar_ucl", "xbar_lcl", "s_ucl", "s_lcl",
            )}
            result.update({"xbars": data["xbars"], "stds": data["stds"]})
            XbarSChartPopup(self.main, [{
                "column": column, "result": result,
                "xbar_violations": data.get("xbar_violations", []),
                "s_violations": data.get("s_violations", []),
            }], save_to_history=False)
        elif kind == "p-chart":
            result = {"proportions": data["proportions"], "p_bar": stats["p_bar"]}
            for key in ("ucls", "lcls"):
                if key in data:
                    result[key] = data[key]
            PChartPopup(self.main, [{
                "column": column, "result": result,
                "violations": data.get("violations", []),
            }], save_to_history=False)
        elif kind == "np-chart":
            result = {"defect_counts": data["defect_counts"], **{
                key: stats[key] for key in ("np_bar", "ucl", "lcl")
            }}
            NPChartPopup(self.main, [{
                "column": column, "result": result,
                "violations": data.get("violations", []),
            }], save_to_history=False)
        elif kind == "c-chart":
            result = {"counts": data["counts"], **{
                key: stats[key] for key in ("c_bar", "ucl", "lcl")
            }}
            CChartPopup(self.main, [{
                "column": column, "result": result,
                "violations": data.get("violations", []),
            }], save_to_history=False)
        elif kind == "u-chart":
            result = {"u_values": data["u_values"], "u_bar": stats["u_bar"]}
            for key in ("ucls", "lcls"):
                if key in data:
                    result[key] = data[key]
            if "ucls" not in result or "lcls" not in result:
                result["_limits_unavailable"] = True
            UChartPopup(
                self.main, result, data.get("violations", []), column or "U-CHART",
                settings.get("distribution", "Poisson"), save_to_history=False,
                calculation_method_key=settings.get("calculation_method"),
            )

    def render(self):
        self.popup=tk.Toplevel(self.main.root)
        self.build_chart()
