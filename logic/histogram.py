from logic.validation import handle_validation_errors
import tkinter as tk
from tkinter import ttk,messagebox
import numpy as np
import matplotlib.pyplot as plt
from logic.chart_canvas import FigureCanvasTkAgg
from ui.chart_view import EmbeddedChartFrame
from ui.dialogs import deliver_result
from scipy.stats import norm
from models.analysis import Analysis

class HistogramMenuPopup(tk.Toplevel):
    def __init__(self,main,sheet,analysis=None):
        super().__init__(main.root)
        if analysis:
            
            self.settings=analysis.settings

            self.column_var.set(
                self.settings["column_name"]
            )

            self.bin_var.set(
                self.settings["bins"]
            )

            self.generate()
        self.main=main
        self.sheet=sheet
        self.title(self.main.t("histogram_type"))
        self.geometry("320x230")
        self.center_window(320,230)

        ttk.Label(
            self,
            text=self.main.t("choose_histogram_type"),
            font=("Segoe UI",12,"bold")
        ).pack(pady=15)

        ttk.Button(
            self,
            text=self.main.t("simple_histogram"),
            command=lambda:self.open_config("simple")
        ).pack(fill="x",padx=20,pady=5)

        ttk.Button(
            self,
            text=self.main.t("histogram_with_fit"),
            command=lambda:self.open_config("fit")
        ).pack(fill="x",padx=20,pady=5)

        ttk.Button(
            self,
            text=self.main.t("grouped_histogram"),
            command=lambda:self.open_config("group")
        ).pack(fill="x",padx=20,pady=5)
            
    def center_window(self,width,height):
        screen_width=self.winfo_screenwidth()
        screen_height=self.winfo_screenheight()

        x=int((screen_width/2)-(width/2))
        y=int((screen_height/2)-(height/2))

        self.geometry(f"{width}x{height}+{x}+{y}")

    def open_config(self,mode):
        HistogramConfigPopup(
            self.main,
            self,
            self.sheet,
            mode
        )

class HistogramConfigPopup(tk.Toplevel):
    def __init__(self,main,menu_popup,sheet,mode):
        super().__init__(main.root)

        self.main=main
        self.menu_popup=menu_popup
        self.sheet=sheet
        self.mode=mode

        self.title(self.main.t("histogram_configuration"))
        self.geometry("640x600")
        self.center_window(320,300)

        ttk.Label(
            self,
            text=self.main.t("select_column")
        ).pack(pady=(15,5))

        self.column_var=tk.StringVar()

        self.column_combo=ttk.Combobox(
            self,
            values=self.sheet.get_column_names(),
            textvariable=self.column_var,
            state="readonly"
        )

        self.column_combo.pack(
            fill="x",
            padx=20
        )

        ttk.Label(
            self,
            text=self.main.t("bins_optional")
        ).pack(pady=(15,5))

        self.bin_entry=ttk.Entry(self)

        self.bin_entry.pack(
            fill="x",
            padx=20
        )

        ttk.Label(
            self,
            text=self.main.t("analysis_title")
        ).pack(pady=(15,5))

        self.title_entry=ttk.Entry(self)

        self.title_entry.pack(
            fill="x",
            padx=20
        )

        ttk.Button(
            self,
            text=self.main.t("generate_histogram"),
            command=self.generate
        ).pack(pady=20)

    def center_window(self,width,height):
        screen_width=self.winfo_screenwidth()
        screen_height=self.winfo_screenheight()

        x=int((screen_width/2)-(width/2))
        y=int((screen_height/2)-(height/2))

        self.geometry(f"{width}x{height}+{x}+{y}")

    def get_numeric_data(self,column_index):
        raw_data=self.sheet.get_column_data(column_index)
        numeric_data=[]

        for value in raw_data:
            try:
                numeric_data.append(float(value))
            except:
                pass

        return numeric_data

    @handle_validation_errors
    def generate(self):
        selected_column=self.column_combo.current()

        if selected_column==-1:
            messagebox.showerror(
                self.main.t("error"),
                self.main.t("please_select_column")
            )
            return

        data=self.get_numeric_data(selected_column)

        if len(data)==0:
            messagebox.showerror(
                self.main.t("error"),
                self.main.t("no_numeric_data")
            )
            return

        bins=self.bin_entry.get().strip()

        if bins=="":
            bins="auto"

        else:
            try:
                bins=int(bins)
            except:
                messagebox.showerror(
                    self.main.t("error"),
                    self.main.t("bins_must_be_number")
                )
                return

        title=self.title_entry.get().strip()

        if title=="":
            title=self.main.t("histogram")

        column_name=self.column_var.get()

        deliver_result(self, lambda: HistogramChartPopup(
            self.main, self, data, self.mode, bins, title, column_name
        ), self.menu_popup)

class HistogramChartPopup(EmbeddedChartFrame):
    def __init__(self, main, config_popup, data, mode, bins, title, column_name, analysis=None, save_to_history=True):
        super().__init__(main.root)

        self.main=main


        self.config_popup=config_popup
        if config_popup:
            self.menu_popup=config_popup.menu_popup
        else:
            self.menu_popup=None
        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_all
        )

        self.data=data
        self.mode=mode
        self.bins=bins
        self.analysis_title=title
        self.column_name=column_name

        self.title(title)
        self.state("zoomed")
        #self.center_window(320,300)

        self.mean=np.mean(data)

        self.stdev=np.std(
            data,
            ddof=1
        )

        self.n=len(data)

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_all
        )

        self.create_chart()
        if save_to_history:
            self.save_analysis()

    def center_window(self,width,height):
        screen_width=self.winfo_screenwidth()
        screen_height=self.winfo_screenheight()

        x=int((screen_width/2)-(width/2))
        y=int((screen_height/2)-(height/2))

        self.geometry(f"{width}x{height}+{x}+{y}")

    def save_analysis(self):
        analysis=Analysis(
            analysis_type="histogram",
            title=self.analysis_title,
            navigator_name=(
                f'Histogram Chart of '
                f'{self.column_name}'
            ),
            data=self.data,
            stats={
                self.main.t("mean"):self.mean,
                self.main.t("stdev"):self.stdev,
                "n":self.n
            },
            settings={
                "mode":self.mode,
                "bins":self.bins,
                "column_name":self.column_name,
                "title":self.analysis_title
            }
        )

        self.main.navigator.add_analysis(analysis)

    def close_all(self):
        try:
            self.config_popup.destroy()
        except:
            pass

        try:
            self.menu_popup.destroy()
        except:
            pass

        try:
            self.destroy()
        except:
            pass

    def create_chart(self):
        ttk.Label(
            self,
            text=f"Mean = {self.mean:.2f} | Std Dev = {self.stdev:.2f} | N = {self.n}",
            font=("Segoe UI",11)
        ).pack(pady=10)

        self.fig,self.ax=plt.subplots(figsize=(12,7))

        if self.mode=="simple":
            self.show_simple_histogram()

        elif self.mode=="fit":
            self.show_fit_histogram()

        elif self.mode=="group":
            self.show_group_histogram()

        self.ax.grid(
            True,
            alpha=0.25,
            linewidth=0.5
        )

        self.ax.set_axisbelow(True)

        canvas=FigureCanvasTkAgg(
            self.fig,
            master=self
        )

        canvas.draw_idle()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

    def show_simple_histogram(self):
        
        data=np.array(self.data)

        mean=np.mean(data)

        stdev=np.std(
            data,
            ddof=1
        )

        data_min=min(data)
        data_max=max(data)

        range_data=data_max-data_min

        if self.bins=="auto":

            bin_width=round(
                range_data/10,
                2
            )

        else:

            bin_width=range_data/self.bins

        left_edge=mean

        while left_edge>data_min:
            left_edge-=bin_width

        right_edge=mean

        while right_edge<data_max:
            right_edge+=bin_width

        bins=np.arange(
            left_edge,
            right_edge+bin_width,
            bin_width
        )

        self.ax.hist(
            data,
            bins=bins,
            color="#6baed6",
            edgecolor="#2b2b2b",
            linewidth=0.8,
            rwidth=0.97
        )

        tick_step=round(
            bin_width,
            2
        )

        ticks=np.arange(
            left_edge,
            right_edge+tick_step,
            tick_step
        )

        if len(ticks)>15:
            ticks=ticks[::2]

        self.ax.set_xticks(ticks)

        self.ax.set_xticklabels(
            [f"{x:.2f}" for x in ticks]
        )

        self.ax.axvline(
            mean,
            color="#444",
            linestyle="--",
            linewidth=1
        )

        self.ax.set_title(
            self.main.t("simpe_histogram"),
            fontsize=14,
            pad=15
        )

        self.ax.set_xlabel(
            self.main.t("value"),
            fontsize=11
        )

        self.ax.set_ylabel(
            self.main.t("frequency"),
            fontsize=11
        )

        self.ax.grid(
            True,
            alpha=0.18,
            linewidth=0.5
        )

        self.ax.set_axisbelow(True)

        self.fig.patch.set_facecolor(self.main.theme_manager.palette["plot"])

        self.ax.set_facecolor(self.main.theme_manager.palette["plot"])

        self.ax.margins(x=0.02)

        self.fig.tight_layout()

    def show_fit_histogram(self):
        
        data=np.array(self.data)

        mean=np.mean(data)

        stdev=np.std(
            data,
            ddof=1
        )

        data_min=min(data)
        data_max=max(data)

        range_data=data_max-data_min

        if self.bins=="auto":

            bin_width=round(
                range_data/10,
                2
            )

        else:

            bin_width=range_data/self.bins

        left_edge=mean

        while left_edge>data_min:
            left_edge-=bin_width

        right_edge=mean

        while right_edge<data_max:
            right_edge+=bin_width

        bins=np.arange(
            left_edge,
            right_edge+bin_width,
            bin_width
        )

        counts,bin_edges,_=self.ax.hist(
            data,
            bins=bins,
            color="#6baed6",
            edgecolor="#2b2b2b",
            linewidth=0.8,
            rwidth=0.97
        )

        x=np.linspace(
            left_edge,
            right_edge,
            400
        )

        y=norm.pdf(
            x,
            mean,
            stdev
        )*len(data)*bin_width

        self.ax.plot(
            x,
            y,
            color="#d95f02",
            linewidth=2.2
        )

        tick_step=round(
            bin_width,
            2
        )

        ticks=np.arange(
            left_edge,
            right_edge+tick_step,
            tick_step
        )

        if len(ticks)>15:
            ticks=ticks[::2]

        self.ax.set_xticks(ticks)

        self.ax.set_xticklabels(
            [f"{x:.2f}" for x in ticks]
        )

        self.ax.axvline(
            mean,
            color="#444",
            linestyle="--",
            linewidth=1
        )

        self.ax.set_title(
            self.main.t("histogram_with_fit"),
            fontsize=14,
            pad=15
        )

        self.ax.set_xlabel(
            self.main.t(self.main.t("value")),
            fontsize=11
        )

        self.ax.set_ylabel(
            self.main.t(self.main.t("frequency")),
            fontsize=11
        )

        self.ax.grid(
            True,
            alpha=0.18,
            linewidth=0.5
        )

        self.ax.set_axisbelow(True)

        self.fig.patch.set_facecolor(self.main.theme_manager.palette["plot"])

        self.ax.set_facecolor(self.main.theme_manager.palette["plot"])

        self.ax.margins(x=0.02)

        self.fig.tight_layout()

    def show_group_histogram(self):
        
        data=np.array(self.data)

        mean=np.mean(data)

        stdev=np.std(
            data,
            ddof=1
        )

        data_min=min(data)
        data_max=max(data)

        range_data=data_max-data_min

        if self.bins=="auto":

            bin_width=round(
                range_data/10,
                2
            )

        else:

            bin_width=range_data/self.bins

        left_edge=mean

        while left_edge>data_min:
            left_edge-=bin_width

        right_edge=mean

        while right_edge<data_max:
            right_edge+=bin_width

        bins=np.arange(
            left_edge,
            right_edge+bin_width,
            bin_width
        )

        counts,bin_edges,_=self.ax.hist(
            data,
            bins=bins,
            color="#6baed6",
            edgecolor="#2b2b2b",
            linewidth=0.8,
            rwidth=0.97
        )

        centers=0.5*(
            bin_edges[1:]+bin_edges[:-1]
        )

        self.ax.plot(
            centers,
            counts,
            color="#d95f02",
            linewidth=1.8,
            marker="o",
            markersize=4
        )

        tick_step=round(
            bin_width,
            2
        )

        ticks=np.arange(
            left_edge,
            right_edge+tick_step,
            tick_step
        )

        if len(ticks)>15:
            ticks=ticks[::2]

        self.ax.set_xticks(ticks)

        self.ax.set_xticklabels(
            [f"{x:.2f}" for x in ticks]
        )

        self.ax.axvline(
            mean,
            color="#444",
            linestyle="--",
            linewidth=1
        )

        self.ax.set_title(
            self.main.t("grouped_histogram"),
            fontsize=14,
            pad=15
        )

        self.ax.set_xlabel(
            self.main.t("value"),
            fontsize=11
        )

        self.ax.set_ylabel(
            self.main.t("frequency"),
            fontsize=11
        )

        self.ax.grid(
            True,
            alpha=0.18,
            linewidth=0.5
        )

        self.ax.set_axisbelow(True)

        self.fig.patch.set_facecolor(self.main.theme_manager.palette["plot"])

        self.ax.set_facecolor(self.main.theme_manager.palette["plot"])

        self.ax.margins(x=0.02)

        self.fig.tight_layout()
