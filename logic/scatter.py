import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from scipy.stats import linregress

from models.analysis import Analysis


class ScatterMenuPopup(tk.Toplevel):

    def __init__(self, main, sheet):
        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title(self.main.t("scatterplot"))
        self.geometry("320x300")

        self.center_window(320, 300)

        ttk.Label(
            self,
            text=self.main.t("choose_scatter_plot"),
            font=("Segoe UI", 12, "bold")
        ).pack(pady=15)

        ttk.Button(
            self,
            text=self.main.t("simple_scatterplot"),
            command=lambda: self.open_config("simple")
        ).pack(fill="x", padx=20, pady=5)

        ttk.Button(
            self,
            text=self.main.t("with_regression"),
            command=lambda: self.open_config("regression")
        ).pack(fill="x", padx=20, pady=5)

        ttk.Button(
            self,
            text=self.main.t("with_regression"),
            command=lambda: self.open_config("group")
        ).pack(fill="x", padx=20, pady=5)

        ttk.Button(
            self,
            text=self.main.t("regression_and_group"),
            command=lambda: self.open_config("regression_group")
        ).pack(fill="x", padx=20, pady=5)

        ttk.Button(
            self,
            text=self.main.t("connect_line"),
            command=lambda: self.open_config("line")
        ).pack(fill="x", padx=20, pady=5)

    def center_window(self, width, height):

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))

        self.geometry(f"{width}x{height}+{x}+{y}")

    def open_config(self, mode):

        ScatterConfigPopup(
            self.main,
            self,
            self.sheet,
            mode
        )

class ScatterConfigPopup(tk.Toplevel):

    def __init__(self, main, menu_popup, sheet, mode):
        super().__init__(main.root)

        self.main = main
        self.menu_popup = menu_popup
        self.sheet = sheet
        self.mode = mode

        self.title(self.main.t("scatterplot_configuration"))
        self.geometry("760x460")

        self.center_window(760, 460)

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

        ttk.Label(
            left_frame,
            text="X Variable"
        ).pack(anchor="w", pady=(0, 5))

        self.x_var = tk.StringVar()

        ttk.Entry(
            left_frame,
            textvariable=self.x_var
        ).pack(fill="x")

        ttk.Button(
            left_frame,
            text=self.main.t("select"),
            command=lambda: self.insert_selected(
                self.x_var
            )
        ).pack(anchor="w", pady=(5, 15))

        ttk.Label(
            left_frame,
            text=self.main.t("x_variable")
        ).pack(anchor="w", pady=(0, 5))

        self.y_vars = []

        self.y_display = tk.Text(
            left_frame,
            height=3
        )

        self.y_display.pack(fill="x")

        ttk.Button(
            left_frame,
            text=self.main.t("y_variable"),
            command=self.add_y_column
        ).pack(anchor="w", pady=(5, 15))

        ttk.Label(
            left_frame,
            text=self.main.t("group_variable_optional")
        ).pack(anchor="w", pady=(0, 5))

        self.group_var = tk.StringVar()

        ttk.Entry(
            left_frame,
            textvariable=self.group_var
        ).pack(fill="x")

        ttk.Button(
            left_frame,
            text=self.main.t("select"),
            command=lambda: self.insert_selected(
                self.group_var
            )
        ).pack(anchor="w", pady=(5, 25))

        ttk.Button(
            left_frame,
            text=self.main.t("generate_scatterplot"),
            command=self.generate
        ).pack()


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

        self.column_listbox.pack(fill="y")

        self.load_columns()

    def load_columns(self):

        columns = self.sheet.get_column_names()

        for i, col in enumerate(columns):

            data = self.sheet.get_column_data(i)

            filled = any(
                str(x).strip() != ""
                for x in data
            )

            if filled:
                self.column_listbox.insert(
                    "end",
                    col
                )

    def insert_selected(self, target_var):

        selected = self.column_listbox.curselection()

        if not selected:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("pelase_select_column")
            )

            return

        column_name = self.column_listbox.get(
            selected[0]
        )

        target_var.set(column_name)

    def add_y_column(self):
        
        selected = self.column_listbox.curselection()

        if not selected:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("pelase_select_column")
            )

            return

        column_name = self.column_listbox.get(
            selected[0]
        )

        if column_name not in self.y_vars:

            self.y_vars.append(column_name)

            self.y_display.delete(
                "1.0",
                "end"
            )

            self.y_display.insert(
                "end",
                ", ".join(self.y_vars)
            )

    def generate(self):

        x_col = self.x_var.get().strip()
        y_cols = self.y_vars
        group_col = self.group_var.get().strip()

        if x_col == "" or len(y_cols) == 0:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("x_y_reuired")            )

            return

        ScatterChartPopup(
            self.main,
            self,
            self.sheet,
            self.mode,
            x_col,
            y_cols,
            group_col
        )

class ScatterChartPopup(tk.Toplevel):

    def __init__(
        self,
        main,
        config_popup,
        sheet,
        mode,
        x_col,
        y_cols,
        group_col="",
        analysis=None,
        save_to_history=True
    ):

        super().__init__(main.root)

        self.main = main
        self.config_popup = config_popup
        self.sheet = sheet

        self.mode = mode

        self.x_col = x_col
        self.y_cols = y_cols
        self.group_col = group_col

        self.title("Scatterplot")

        self.state("zoomed")

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_all
        )

        self.create_chart()

        if save_to_history:
            self.save_analysis()

        if config_popup:
            self.menu_popup = config_popup.menu_popup
        else:
            self.menu_popup = None

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

    def get_column_index(self, name):

        columns = self.sheet.get_column_names()

        return columns.index(name)

    def get_numeric_data(self, column_name):

        idx = self.get_column_index(column_name)

        raw = self.sheet.get_column_data(idx)

        data = []

        for value in raw:

            try:
                data.append(float(value))
            except:
                data.append(np.nan)

        return np.array(data)

    def save_analysis(self):

        analysis = Analysis(
            analysis_type="Scatterplot",
            title="Scatterplot",
            navigator_name=(
                f'Scatterplot of '
                f'{self.x_col} vs '
                f'{", ".join(self.y_cols)}'
            ),
            data=[],
            stats={},
            settings={
                "mode": self.mode,
                "x_col": self.x_col,
                "y_cols": self.y_cols,
                "group_col": self.group_col
            }
        )

        self.main.navigator.add_analysis(
            analysis
        )

    def create_chart(self):
        
        x = self.get_numeric_data(
            self.x_col
        )

        fig, ax = plt.subplots(
            figsize=(12, 7)
        )

        colors = [
            "#4e79a7",
            "#f28e2b",
            "#59a14f",
            "#e15759",
            "#b07aa1",
            "#76b7b2"
        ]

        for y_index, y_col in enumerate(self.y_cols):

            y = self.get_numeric_data(
                y_col
            )

            mask = ~np.isnan(x) & ~np.isnan(y)

            x_clean = x[mask]
            y_clean = y[mask]

            base_color = colors[
                y_index % len(colors)
            ]

            if self.mode == "simple":

                ax.scatter(
                    x_clean,
                    y_clean,
                    label=y_col,
                    color=base_color,
                    s=45,
                    alpha=0.8
                )

            elif self.mode == "regression":

                ax.scatter(
                    x_clean,
                    y_clean,
                    label=y_col,
                    color=base_color,
                    s=45,
                    alpha=0.8
                )

                slope, intercept, r, p, std = linregress(
                    x_clean,
                    y_clean
                )

                line = (
                    slope * x_clean
                    + intercept
                )

                sorted_idx = np.argsort(
                    x_clean
                )

                ax.plot(
                    x_clean[sorted_idx],
                    line[sorted_idx],
                    color=base_color,
                    linewidth=2,
                    linestyle="--"
                )

            elif self.mode == "line":

                sorted_idx = np.argsort(
                    x_clean
                )

                ax.plot(
                    x_clean[sorted_idx],
                    y_clean[sorted_idx],
                    marker="o",
                    label=y_col,
                    color=base_color,
                    linewidth=1.8,
                    markersize=5
                )

            elif self.mode in [
                "group",
                "regression_group"
            ]:

                if self.group_col == "":

                    messagebox.showerror(
                        self.main.t("error"),
                        self.main.t("group_variable_reuired")
                    )

                    self.destroy()

                    return

                group_idx = self.get_column_index(
                    self.group_col
                )

                groups = self.sheet.get_column_data(
                    group_idx
                )

                groups = np.array(groups)[mask]

                unique_groups = np.unique(
                    groups
                )

                for grp_index, grp in enumerate(
                    unique_groups
                ):

                    grp_mask = groups == grp

                    grp_color = colors[
                        grp_index % len(colors)
                    ]

                    ax.scatter(
                        x_clean[grp_mask],
                        y_clean[grp_mask],
                        label=f"{y_col} - {grp}",
                        color=grp_color,
                        s=45,
                        alpha=0.8
                    )

                    if self.mode == "regression_group":

                        if np.sum(grp_mask) < 2:
                            continue

                        slope, intercept, _, _, _ = linregress(
                            x_clean[grp_mask],
                            y_clean[grp_mask]
                        )
                        x_min = np.min(
                            x_clean[grp_mask]
                        )

                        x_max = np.max(
                            x_clean[grp_mask]
                        )

                        line_x = np.linspace(
                            x_min,
                            x_max,
                            100
                        )

                        line_y = (
                            slope * line_x
                            + intercept
                        )

                        ax.plot(
                            line_x,
                            line_y,
                            color=grp_color,
                            linewidth=2,
                            linestyle="--"
                        )

        if (
            len(self.y_cols) > 1
            or self.mode in [
                "group",
                "regression_group"
            ]
        ):

            ax.legend()

        ax.set_title(
            self.main.t("scatterplot"),
            fontsize=15,
            pad=15
        )

        ax.set_xlabel(
            self.x_col,
            fontsize=11,
            color="#4e79a7"
        )

        ax.set_ylabel(
            ", ".join(self.y_cols),
            fontsize=11,
            color="#e15759"
        )

        ax.grid(
            True,
            alpha=0.2,
            linewidth=0.5
        )

        ax.set_axisbelow(True)

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