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

        menubar=tk.Menu(root)

        file_menu=tk.Menu(menubar,tearoff=0)

        file_menu.add_command(
            label=self.main.t("save"),
            command=self.project_manager.save_project
        )

        file_menu.add_command(
            label=self.main.t("save_as"),
            command=self.project_manager.save_as_project
        )

        file_menu.add_command(
            label=self.main.t("load_project"),
            command=self.project_manager.load_project
        )

        file_menu.add_command(
            label=self.main.t("import_excel"),
            command=self.project_manager.import_excel
        )

        file_menu.add_command(
            label=self.main.t("export_pdf"),
            command=self.project_manager.generate_report
        )

        file_menu.add_command(
            label=self.main.t("new_project"),
            command=self.project_manager.new_project
        )
        menubar.add_cascade(label=self.main.t("file"),menu=file_menu)

        edit_menu=tk.Menu(menubar,tearoff=0)
        edit_menu.add_command(label=self.main.t("undo"))
        edit_menu.add_command(label=self.main.t("redo"))
        menubar.add_cascade(label=self.main.t("edit"),menu=edit_menu)

        menubar.add_command(
            label=self.main.t("histogram"),
            command=lambda:HistogramMenuPopup(
                self.main,
                self.main.sheet
            )
        )

        menubar.add_command(
            label=self.main.t("pareto"),
            command=lambda:ParetoConfigPopup(
            self.main,
            self.main.sheet
            )
        )
        
        menubar.add_command(
            label=self.main.t("scatter"),
            command=lambda:ScatterMenuPopup(
                self.main,
                self.main.sheet
            )
        )
        menubar.add_command(label=self.main.t("fishbone"))
        menubar.add_command(label=self.main.t("defect_concentration"))
        menubar.add_command(label=self.main.t("check_sheet"))

        control_chart_menu = tk.Menu(menubar, tearoff=0)

        variable_menu = tk.Menu(control_chart_menu, tearoff=0)

        individual_menu = tk.Menu(variable_menu, tearoff=0)

        individual_menu.add_command(
            label=self.main.t("i_mr"),
            command=lambda:IMRConfigPopup(
                self.main,
                self.main.sheet
            )
        )
        
        individual_menu.add_command(
            label=self.main.t("moving_range"),
            command=lambda:MovingRangeConfigPopup(
                self.main,
            )
        )
        
        individual_menu.add_command(
            label=self.main.t("i_chart"),
            command=lambda:IndividualConfigPopup(
                self.main,
            )
        )
        

        variable_menu.add_cascade(
            label=self.main.t("individual"),
            menu=individual_menu
        )

        subgroup_menu = tk.Menu(variable_menu, tearoff=0)
        subgroup_menu.add_command(label=self.main.t("xbar_r_chart"), command=lambda:XbarRConfigPopup (self.main, self.main.sheet))
        subgroup_menu.add_command(label=self.main.t("r_bar_chart"), command=lambda:RbarConfigPopup (self.main))
        subgroup_menu.add_command(label=self.main.t("xbar_s_chart"), command=lambda:XbarSConfigPopup (self.main, self.main.sheet))
        subgroup_menu.add_command(label=self.main.t("s_bar_chart"), command=lambda:SbarConfigPopup (self.main))

        variable_menu.add_cascade(
            label=self.main.t("subgroup"),
            menu=subgroup_menu
        )

        attribute_menu = tk.Menu(control_chart_menu, tearoff=0)

        attribute_menu.add_command(label=self.main.t("p_chart"), command=lambda:PChartConfigPopup(self.main, self.main.sheet))
        attribute_menu.add_command(label=self.main.t("np_chart"), command=lambda:NPChartConfigPopup(self.main, self.main.sheet))
        attribute_menu.add_command(label=self.main.t("c_chart"), command=lambda:CChartConfigPopup(self.main, self.main.sheet))
        attribute_menu.add_command(label=self.main.t("u_chart"), command=lambda:UChartModePopup(self.main, self.main.sheet))

        # MAIN CASCADE
        control_chart_menu.add_cascade(
            label=self.main.t("variable"),
            menu=variable_menu
        )

        control_chart_menu.add_cascade(
            label=self.main.t("attribute"),
            menu=attribute_menu
        )

        control_chart_menu.add_command(
            label=self.main.t("converter"),
            command=lambda:AttributeConverterPopup(
                self.main,
                self.main.sheet
            )
        )

        menubar.add_cascade(
            label=self.main.t("control_chart"),
            menu=control_chart_menu
        )

        lang_menu=tk.Menu(menubar,tearoff=0)

        lang_menu.add_command(
            label="English",
            command=lambda:self.main.set_lang("en")
        )

        lang_menu.add_command(
            label="Indonesia",
            command=lambda:self.main.set_lang("id")
        )

        menubar.add_cascade(
            label=self.main.t("language"),
            menu=lang_menu
        )

        root.config(menu=menubar)

        toolbar=tk.Frame(root,height=40)
        toolbar.pack(fill="x")

        tk.Button(
            toolbar,
            text="➕ "+self.main.t("column"),
            relief="flat"
        ).pack(side="left",padx=5)

        tk.Label(toolbar,text="|").pack(side="left")

        tk.Button(
            toolbar,
            text="💾 "+self.main.t("save"),
            relief="flat",
            command=self.project_manager.save_project
        ).pack(side="left", padx=5)

        tk.Label(toolbar,text="|").pack(side="left")

        tk.Button(
            toolbar,
            text="↩ "+self.main.t("undo"),
            relief="flat",
        ).pack(side="left",padx=5)

        tk.Label(toolbar,text="|").pack(side="left")

        tk.Button(
            toolbar,
            text="↪ "+self.main.t("redo"),
            relief="flat",
        ).pack(side="left",padx=5)

        sep_top=tk.Frame(root,height=1,bg="#d1d5db")
        sep_top.pack(fill="x")

        container=tk.Frame(root)
        container.pack(fill="both",expand=True)

        left=tk.Frame(container,bg="white")

        left.pack(
            side="left",
            fill="both",
            expand=True
        )

        tk.Label(
            left,
            text=self.main.t("data_input"),
            font=("Arial",14)
        ).pack(anchor="w",padx=10,pady=(10,5))

        tk.Frame(
            left,
            height=1,
            bg="#bdcadd"
        ).pack(fill="x",padx=10,pady=(0,10))

        table_container=tk.Frame(left,bg="white")

        table_container.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.main.sheet.build(table_container)

        sep_mid=tk.Frame(
            container,
            width=1,
            bg="#d1d5db"
        )

        sep_mid.pack(side="left",fill="y")

        right=tk.Frame(
            container,
            width=300,
            bg="#f8fafc"
        )

        right.pack(side="left",fill="y")
        right.pack_propagate(False)


        self.main.navigator=self

        tk.Label(
            right,
            text="Navigator",
            font=("Arial",12,"bold"),
            bg="#f8fafc"
        ).pack(anchor="w",padx=10,pady=(10,5))

        self.navigator_box=tk.Listbox(
            right,
            borderwidth=1,
            relief="solid",
            height=8
        )

        self.navigator_box.pack(
            fill="x",
            padx=10,
            pady=(0,15)
        )

        self.navigator_box.bind(
            "<Double-Button-1>",
            self.open_analysis
        )

        self.help_container = tk.Frame(
            right,
            bg="#f8fafc",
            bd=1,
            relief="solid"
        )

        self.help_container.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0,10)
        )

        tk.Label(
            self.help_container,
            text="Help",
            font=("Arial",12,"bold"),
            bg="#e2e8f0"
        ).pack(
            fill="x",
            ipady=5
        )

        canvas_container = tk.Frame(
            self.help_container,
            bg="white"
        )

        canvas_container.pack(
            fill="both",
            expand=True
        )

        self.help_canvas = tk.Canvas(
            canvas_container,
            bg="white",
            highlightthickness=0
        )

        self.help_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            canvas_container,
            orient="vertical",
            command=self.help_canvas.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.help_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.help_frame = tk.Frame(
            self.help_canvas,
            bg="white"
        )

        self.canvas_window = self.help_canvas.create_window(
            (0,0),
            window=self.help_frame,
            anchor="nw"
        )

        def on_frame_configure(event):

            self.help_canvas.configure(
                scrollregion=self.help_canvas.bbox("all")
            )

        self.help_frame.bind(
            "<Configure>",
            on_frame_configure
        )

        def resize_frame(event):

            self.help_canvas.itemconfig(
                self.canvas_window,
                width=event.width
            )

        self.help_canvas.bind(
            "<Configure>",
            resize_frame
        )

        def _on_mousewheel(event):

            self.help_canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )

        self.help_canvas.bind(
            "<MouseWheel>",
            _on_mousewheel
        )

        self.build_help_dropdown(
            self.help_frame,
            HELP_DATA[self.main.current_lang]
        )

        self.main.root.bind("<Control-s>", lambda e: self.project_manager.save_project())
        self.main.root.bind("<Control-Shift-s>", lambda e: self.project_manager.save_as_project())
        self.main.root.bind("<Control-z>", lambda e: self.undo_action())
        self.main.root.bind("<Control-y>", lambda e: self.redo_action())
        self.main.root.bind("<Control-o>", lambda e: self.project_manager.load_project())
        self.main.root.bind("<Control-n>", lambda e: self.project_manager.new_project())
        self.main.root.bind("<Control-i>", lambda e: self.project_manager.import_excel())
        self.main.root.bind("Control-p>", lambda e: self.project_manager.generate_report())

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

            self.navigator_box.insert(
                tk.END,
                analysis.navigator_name
            )

            self.main.analysis_objects.append(
                analysis
            )

    def open_analysis(self, event):

  

        index = self.navigator_box.nearest(event.y)

  

        if index < 0:
            return

        analysis = self.main.analysis_objects[index]



        if analysis.analysis_type == "Histogram":


            from logic.histogram import HistogramChartPopup

            HistogramChartPopup(
                self.main,
                None,
                analysis.data,
                analysis.settings["mode"],
                analysis.settings["bins"],
                analysis.settings["title"],
                analysis.settings["column_name"],
                save_to_history=False
            )

        elif analysis.analysis_type == "Scatterplot":


            from logic.scatter import ScatterChartPopup

            ScatterChartPopup(
                self.main,
                None,
                self.main.sheet,
                analysis.settings["mode"],
                analysis.settings["x_col"],
                analysis.settings["y_cols"],
                analysis.settings["group_col"],
                save_to_history=False
            )

        elif analysis.analysis_type == "Pareto":


            from logic.pareto import ParetoChartPopup

            ParetoChartPopup(
                self.main,
                None,
                self.main.sheet,
                analysis.settings["defect_col"],
                analysis.settings["freq_col"],
                analysis.settings["by_col"],
                save_to_history=False
            )

        elif analysis.analysis_type == "I-MR":


            from logic.imr_chart import IMRChartPopup

            IMRChartPopup(
                self.main,
                None,
                analysis.data["values"],
                analysis.settings["column"],
                analysis.data["violations"],
                save_to_history=False
            )

        elif analysis.analysis_type == "XBAR-S":


            from logic.xbar_s import XbarSChartPopup

            XbarSChartPopup(
                self.main,
                {
                    "column": analysis.settings["column"],
                    "xbars": analysis.data["xbars"],
                    "stds": analysis.data["stds"],
                    "xbar_bar": analysis.stats["xbar_bar"],
                    "s_bar": analysis.stats["s_bar"],
                    "xbar_ucl": analysis.stats["xbar_ucl"],
                    "xbar_lcl": analysis.stats["xbar_lcl"],
                    "s_ucl": analysis.stats["s_ucl"],
                    "s_lcl": analysis.stats["s_lcl"]
                },
                save_to_history=False
            )

        elif analysis.analysis_type == "XBAR-R":

            print("OPEN XBAR-R")

            from logic.xbar_r import XbarRChartPopup

            XbarRChartPopup(
                self.main,
                {
                    "column": analysis.settings["column"],
                    "xbars": analysis.data["xbars"],
                    "ranges": analysis.data["ranges"],
                    "xbar_bar": analysis.stats["xbar_bar"],
                    "r_bar": analysis.stats["r_bar"],
                    "xbar_ucl": analysis.stats["xbar_ucl"],
                    "xbar_lcl": analysis.stats["xbar_lcl"],
                    "r_ucl": analysis.stats["r_ucl"],
                    "r_lcl": analysis.stats["r_lcl"]
                },
                save_to_history=False
            )

        elif analysis.analysis_type == "P-CHART":

            print("OPEN P")

            from logic.p_chart import PChartPopup

            PChartPopup(
                self.main,
                {
                    "column": analysis.settings["column"],
                    "proportions": analysis.data["proportions"],
                    "p_bar": analysis.stats["p_bar"]
                },
                save_to_history=False
            )

        elif analysis.analysis_type == "NP-CHART":

            print("OPEN NP")

            from logic.np_chart import NPChartPopup

            NPChartPopup(
                self.main,
                {
                    "column": analysis.settings["column"],
                    "defect_counts": analysis.data["defect_counts"],
                    "np_bar": analysis.stats["np_bar"],
                    "ucl": analysis.stats["ucl"],
                    "lcl": analysis.stats["lcl"]
                },
                save_to_history=False
            )

        elif analysis.analysis_type == "C-CHART":

            print("OPEN C")

            from logic.c_chart import CChartPopup

            CChartPopup(
                self.main,
                {
                    "column": analysis.settings["column"],
                    "counts": analysis.data["counts"],
                    "c_bar": analysis.stats["c_bar"],
                    "ucl": analysis.stats["ucl"],
                    "lcl": analysis.stats["lcl"]
                },
                save_to_history=False
            )

        elif analysis.analysis_type == "U-CHART":

            from logic.u_chart import UChartPopup

            UChartPopup(
                self.main,
                {
                    "column": analysis.settings["column"],
                    "u_values": analysis.data["u_values"],
                    "u_bar": analysis.stats["u_bar"]
                },
                save_to_history=False
            )

        else:

            print("UNKNOWN ANALYSIS TYPE")

    def render(self):
        self.popup=tk.Toplevel(self.main.root)
        self.build_chart()