import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.analysis import Analysis


class ParetoConfigPopup(tk.Toplevel):

    def __init__(self, main, sheet):
        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title(self.main.t("pareto_chart"))
        self.geometry("760x450")

        self.center_window(760, 450)

        self.selected_target = None

        self.create_ui()

    def center_window(self, width, height):

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))

        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_ui(self):

        main_frame = ttk.Frame(self)
        main_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(
            side="left",
            fill="both",
            expand=True
        )

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(
            side="right",
            fill="y",
            padx=(20, 0)
        )
##
        ttk.Label(
            left_frame,
            text="Defects or Attribute Data"
        ).pack(anchor="w", pady=(0, 5))

        self.defect_var = tk.StringVar()

        self.defect_entry = ttk.Entry(
            left_frame,
            textvariable=self.defect_var
        )

        self.defect_entry.pack(fill="x")

        ttk.Button(
            left_frame,
            text=self.main.t("select"),
            command=lambda: self.insert_selected_column(
                self.defect_var,
                require_numeric=False
            )
        ).pack(anchor="w", pady=(5, 15))
##
        ttk.Label(
            left_frame,
            text=self.main.t("frequency_optional")
        ).pack(anchor="w", pady=(0, 5))

        self.freq_var = tk.StringVar()

        self.freq_entry = ttk.Entry(
            left_frame,
            textvariable=self.freq_var
        )

        self.freq_entry.pack(fill="x")

        ttk.Button(
            left_frame,
            text=self.main.t("select"),
            command=lambda: self.insert_selected_column(
                self.freq_var,
                require_numeric=True
            )
        ).pack(anchor="w", pady=(5, 15))
##
        ttk.Label(
            left_frame,
            text=self.main.t("by_variable_optional")
        ).pack(anchor="w", pady=(0, 5))

        self.by_var = tk.StringVar()

        self.by_entry = ttk.Entry(
            left_frame,
            textvariable=self.by_var
        )

        self.by_entry.pack(fill="x")

        ttk.Button(
            left_frame,
            text=self.main.t("select"),
            command=lambda: self.insert_selected_column(
                self.by_var
            )
        ).pack(anchor="w", pady=(5, 25))
##
        ttk.Button(
            left_frame,
            text=self.main.t("generate_pareto_chart"),
            command=self.generate
        ).pack()
##
        ttk.Label(
            right_frame,
            text=self.main.t("available_column"),
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.column_listbox = tk.Listbox(
            right_frame,
            height=20,
            width=28
        )

        self.column_listbox.pack(
            fill="y",
            pady=(5, 0)
        )

        self.load_columns()

    def load_columns(self):
        
        columns = self.sheet.get_column_names()

        self.all_columns = {}

        for i, col in enumerate(columns):

            data = self.sheet.get_column_data(i)

            cleaned = [
                str(x).strip()
                for x in data
                if str(x).strip() != ""
            ]

            if len(cleaned) == 0:
                continue

            is_numeric = True

            for x in cleaned:

                try:
                    float(x)
                except:
                    is_numeric = False
                    break

            self.all_columns[col] = {
                "index": i,
                "numeric": is_numeric
            }

            self.column_listbox.insert(
                "end",
                col
            )

    def insert_selected_column(
        self,
        target_var,
        require_numeric=None
    ):

        selected = self.column_listbox.curselection()

        if not selected:

            messagebox.showerror(
                self.main.t("error"),
                "Please select column"
            )

            return

        column_name = self.column_listbox.get(
            selected[0]
        )

        info = self.all_columns[column_name]

        if require_numeric is True and not info["numeric"]:

            messagebox.showerror(
                self.main.t("error"),
                "Column must be numeric"
            )

            return

        if require_numeric is False and info["numeric"]:

            messagebox.showerror(
                self.main.t("error"),
                "Column must contain text/category"
            )

            return

        target_var.set(column_name)

    def generate(self):
    
        defect_col = self.defect_var.get().strip()
        freq_col = self.freq_var.get().strip()
        by_col = self.by_var.get().strip()

        if defect_col == "":

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("defect_column_reuired")
            )

            return

        ParetoChartPopup(
            self.main,
            self,
            self.sheet,
            defect_col,
            freq_col,
            by_col
        )

class ParetoChartPopup(tk.Toplevel):

    def __init__(
        self,
        main,
        config_popup,
        sheet,
        defect_col,
        freq_col,
        by_col,
        analysis=None,
        save_to_history=True
    ):

        super().__init__(main.root)

        self.main = main
        self.config_popup = config_popup
        self.sheet = sheet

        self.defect_col = defect_col
        self.freq_col = freq_col
        self.by_col = by_col

        self.labels = []
        self.values = []

        self.title(self.main.t("pareto_chart"))

        self.state("zoomed")

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_all
        )

        self.create_chart()

        if save_to_history:
            self.save_analysis()

    def close_all(self):

        try:
            self.config_popup.destroy()
        except:
            pass

        try:
            self.destroy()
        except:
            pass

    def get_column_index(self, name):

        columns = self.sheet.get_column_names()

        return columns.index(name)

    def save_analysis(self):

        analysis = Analysis(
            analysis_type="Pareto",
            title="Pareto Chart",
            navigator_name=f"Pareto Chart of {self.defect_col}",
            data={
                "labels": self.labels,
                "values": self.values
            },
            stats={
                "total": sum(self.values),
                "categories": len(self.labels)
            },
            settings={
                "defect_col": self.defect_col,
                "freq_col": self.freq_col,
                "by_col": self.by_col
            }
        )

        self.main.navigator.add_analysis(
            analysis
        )

    def create_chart(self):

        defect_idx = self.get_column_index(
            self.defect_col
        )

        defects = self.sheet.get_column_data(
            defect_idx
        )

        if self.freq_col != "":

            freq_idx = self.get_column_index(
                self.freq_col
            )

            freq_data = self.sheet.get_column_data(
                freq_idx
            )

            labels = []
            values = []

            for d, f in zip(defects, freq_data):

                try:

                    d = str(d).strip()

                    if d == "":
                        continue

                    labels.append(d)

                    values.append(float(f))

                except:
                    pass

        else:

            counts = {}

            for d in defects:

                d = str(d).strip()

                if d == "":
                    continue

                counts[d] = counts.get(d, 0) + 1

            sorted_items = sorted(
                counts.items(),
                key=lambda x: x[1],
                reverse=True
            )

            labels = [x[0] for x in sorted_items]

            values = [x[1] for x in sorted_items]

        self.labels = labels
        self.values = values

        cumulative = np.cumsum(values)

        cumulative_percent = (
            cumulative / cumulative[-1]
        ) * 100

        fig, ax1 = plt.subplots(
            figsize=(13, 7)
        )

        bars = ax1.bar(
            labels,
            values,
            color="#6baed6",
            edgecolor="#2b2b2b",
            linewidth=0.8
        )

        ax1.set_ylabel(
            "Frequency",
            fontsize=11
        )

        ax1.set_xlabel(
            "Defects",
            fontsize=11
        )

        ax1.set_title(
            "Pareto Chart",
            fontsize=15,
            pad=15
        )

        ax1.grid(
            True,
            alpha=0.2,
            linewidth=0.5
        )

        ax1.set_axisbelow(True)

        # =====================================
        # CUMULATIVE LINE
        # =====================================

        ax2 = ax1.twinx()

        ax2.plot(
            labels,
            cumulative_percent,
            color="#d95f02",
            marker="o",
            linewidth=2
        )

        ax2.set_ylabel(
            "Cumulative %",
            fontsize=11
        )

        ax2.set_ylim(0, 110)

        for i, value in enumerate(cumulative_percent):

            ax2.text(
                i,
                value + 2,
                f"{value:.1f}%",
                ha="center",
                fontsize=8
            )

        for label in ax1.get_xticklabels():
            
            label.set_rotation(45)
            label.set_horizontalalignment("right")

        fig.subplots_adjust(
            bottom=0.25
        )

        fig.tight_layout()
        

        canvas = FigureCanvasTkAgg(
            fig,
            master=self
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )