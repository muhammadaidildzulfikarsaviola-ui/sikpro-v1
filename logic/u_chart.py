from logic.validation import handle_validation_errors, numeric_values
from logic.nelson_rules import check_nelson_rules as _shared_nelson_rules, rule_details, localize_chart_results, localize_violations
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import matplotlib.pyplot as plt
from resources import resource_path

from collections import Counter

from logic.chart_canvas import FigureCanvasTkAgg, marker_stride
from ui.chart_view import EmbeddedChartFrame, favor_chart_panel
from ui.dialogs import deliver_result

from models.analysis import Analysis
from PIL import Image, ImageTk
def center_window(window):

    window.update_idletasks()

    width = window.winfo_width()
    height = window.winfo_height()

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    window.geometry(
        f"{width}x{height}+{x}+{y}"
    )

def clean_numeric(data):
    return numeric_values(data)


def get_rule_explanation(rule_no, language="id"):
    details = rule_details(rule_no, language)
    return details["description"], details["interpretation"]


def check_nelson_rules(data, mean, ucls, lcls, language="id"):
    raw_violations = _shared_nelson_rules(data, mean, ucls, lcls, language=language)
    violations = []
    for rule, point, description in raw_violations:
        details = rule_details(rule, language)
        violations.append({"rule": rule, "point": point,
                           "description": description,
                           "cause": details["interpretation"]})
    return violations


def get_most_frequent_rule(all_violations):

    if len(all_violations) == 0:

        return "No dominant violations"

    rules = [
        v["rule"]
        for v in all_violations
    ]

    counter = Counter(rules)

    most_common = counter.most_common(1)[0]

    return f'{most_common[0]} ({most_common[1]} times)'


def calculate_u_chart(defects, sample_sizes, distribution="Poisson"):
    """Calculate u-chart points and limits; preserve the legacy result keys."""
    defects = numeric_values(defects, "defects")
    sample_sizes = numeric_values(sample_sizes, "sample sizes")
    if not defects:
        raise ValueError("At least one defect observation is required")
    if len(defects) != len(sample_sizes):
        raise ValueError("Defect and sample-size columns must have equal lengths")
    if any(value < 0 for value in defects):
        raise ValueError("Defect counts must be nonnegative")
    if any(value <= 0 for value in sample_sizes):
        raise ValueError("Sample sizes must be positive")
    if distribution not in ("Poisson", "Normal", "Binomial"):
        raise ValueError("Distribution must be Poisson, Normal, or Binomial")

    u_values = [defects[i] / sample_sizes[i] for i in range(len(defects))]
    total_units = sum(sample_sizes)
    u_bar = sum(defects) / total_units

    if distribution == "Poisson":
        sigmas = [np.sqrt(u_bar / size) for size in sample_sizes]
    elif distribution == "Normal":
        if len(u_values) < 2:
            raise ValueError("Normal mode requires at least two observations")
        sigma = float(np.std(u_values, ddof=1))
        sigmas = [sigma] * len(u_values)
    else:
        # Retain the application's legacy binomial rate model; it is not the
        # standard Poisson u-chart model. Reject impossible proportions explicitly.
        if any(defect > size for defect, size in zip(defects, sample_sizes)):
            raise ValueError("Binomial mode requires defects not to exceed sample size")
        sigmas = [np.sqrt(u_bar * (1 - u_bar) / size) for size in sample_sizes]

    ucls = [u_bar + 3 * sigma for sigma in sigmas]
    lcls = [max(0.0, u_bar - 3 * sigma) for sigma in sigmas]
    return {
        "u_values": u_values,
        "sample_sizes": sample_sizes,
        "u_bar": u_bar,
        "ucls": ucls,
        "lcls": lcls,
        "distribution": distribution,
    }

class UChartModePopup(tk.Toplevel):

    def __init__(self, main, sheet):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title("Select U Chart Mode")

        self.geometry("320x200")
        center_window(self)

        self.resizable(False, False)

        self.create_ui()

    def create_ui(self):

        container = ttk.Frame(
            self,
            padding=20
        )

        container.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            container,
            text="Select Data Source",
            font=("Segoe UI", 11, "bold")
        ).pack(
            pady=(0, 20)
        )

        ttk.Button(
            container,
            text="Use Raw Data",
            command=self.use_raw
        ).pack(
            fill="x",
            pady=10,
            ipady=6
        )

        ttk.Button(
            container,
            text="Use Converted Data",
            command=self.use_converted
        ).pack(
            fill="x",
            pady=10,
            ipady=6
        )

    def use_raw(self):
        deliver_result(self, lambda: UChartConfigPopup(self.main, self.sheet))

    def use_converted(self):
        deliver_result(self, lambda: UChartConvertedPopup(self.main, self.sheet))
class UChartConfigPopup(tk.Toplevel):

    def __init__(self, main, sheet, analysis=None, save_to_history=True):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title("U Chart")

        self.geometry("1100x650")
        center_window(self)

        self.defect_column = None
        self.sample_column = None

        self.create_ui()

    def create_ui(self):

        container = ttk.Frame(self)

        container.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        left = ttk.Frame(container)

        left.pack(
            side="left",
            fill="both",
            expand=True
        )

        center = ttk.Frame(container)

        center.pack(
            side="left",
            padx=15
        )

        right = ttk.Frame(container)

        right.pack(
            side="right",
            fill="both",
            expand=True
        )

        ttk.Label(
            left,
            text="Available Columns",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.column_listbox = tk.Listbox(
            left,
            selectmode="browse",
            height=25
        )

        self.column_listbox.pack(
            fill="both",
            expand=True
        )

        columns = self.sheet.get_column_names()

        self.numeric_columns = {}

        for i, col in enumerate(columns):

            data = self.sheet.get_column_data(i)

            if not any(value is not None and str(value).strip() for value in data):
                continue

            self.numeric_columns[col] = i

            self.column_listbox.insert(
                "end",
                col
            )

        ttk.Label(
            right,
            text="Distribution"
        ).pack(
            anchor="w",
            pady=(15, 0)
        )

        self.distribution_var = tk.StringVar(
            value="Poisson"
        )

        distribution_combo = ttk.Combobox(
            right,
            textvariable=self.distribution_var,
            state="readonly",
            values=[
                "Poisson",
                "Normal",
                "Binomial"
            ]
        )

        distribution_combo.pack(
            fill="x",
            pady=(5, 10)
        )

        ttk.Button(
            center,
            text="Set as Defect Count →",
            command=self.set_defect_column
        ).pack(
            pady=(120, 10),
            ipadx=10,
            ipady=5
        )

        ttk.Button(
            center,
            text="Set as Sample Size →",
            command=self.set_sample_column
        ).pack(
            pady=10,
            ipadx=10,
            ipady=5
        )

        config = ttk.LabelFrame(
            right,
            text="Selected Columns",
            padding=10
        )

        config.pack(
            fill="x"
        )

        self.defect_label = ttk.Label(
            config,
            text="Defect Count : -"
        )

        self.defect_label.pack(
            anchor="w",
            pady=5
        )

        self.sample_label = ttk.Label(
            config,
            text="Sample Size : -"
        )

        self.sample_label.pack(
            anchor="w",
            pady=5
        )

        ttk.Button(
            right,
            text="Generate U Chart",
            command=self.generate
        ).pack(
            fill="x",
            pady=(20, 0),
            ipady=6
        )

    def set_defect_column(self):

        selected = self.column_listbox.curselection()

        if not selected:
            return

        self.defect_column = self.column_listbox.get(
            selected[0]
        )

        self.defect_label.config(
            text=f'Defect Count : {self.defect_column}'
        )

    def set_sample_column(self):

        selected = self.column_listbox.curselection()

        if not selected:
            return

        self.sample_column = self.column_listbox.get(
            selected[0]
        )

        self.sample_label.config(
            text=f'Sample Size : {self.sample_column}'
        )

    @handle_validation_errors
    def generate(self):

        if not self.defect_column:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("select_defect_count_column")
            )

            return

        if not self.sample_column:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("select_sample_size_column")
            )

            return

        defect_idx = self.numeric_columns[
            self.defect_column
        ]

        sample_idx = self.numeric_columns[
            self.sample_column
        ]

        defects = clean_numeric(
            self.sheet.get_column_data(defect_idx)
        )

        sample_sizes = clean_numeric(
            self.sheet.get_column_data(sample_idx)
        )

        distribution = self.distribution_var.get()

        result = calculate_u_chart(
            defects,
            sample_sizes,
            distribution
        )

        violations = check_nelson_rules(
            result["u_values"],
            result["u_bar"],
            result["ucls"],
            result["lcls"],
                language=self.main.current_lang
        )

        deliver_result(self, lambda: UChartPopup(
            self.main, result, violations, self.defect_column, distribution
        ))


class UChartPopup(EmbeddedChartFrame):

    def __init__(
        self,
        main,
        result,
        violations=None,
        column_name="U-CHART",
        distribution="Poisson",
        save_to_history=True,
        calculation_method_key=None
    ):

        super().__init__(main.root)

        self.main = main

        self.result = result
        if "ucls" not in self.result and not self.result.get("_limits_unavailable"):

            u_values = self.result["u_values"]

            u_bar = self.result["u_bar"]

            sigma = np.std(
                u_values,
                ddof=1
            )

            ucl = u_bar + (3 * sigma)

            lcl = u_bar - (3 * sigma)

            if lcl < 0:

                lcl = 0

            self.result["ucls"] = [
                ucl
                for _ in u_values
            ]

            self.result["lcls"] = [
                lcl
                for _ in u_values
            ]

        self.violations = localize_violations(violations or [], self.main.current_lang)

        self.column_name = column_name

        self.distribution = distribution

        self.calculation_method_key = calculation_method_key

        self.save_to_history = save_to_history

        self.title("U Chart")

        self.state("zoomed")

        self.create_ui()

        if self.save_to_history:

            self.save_analysis()

    def save_analysis(self):

        analysis = Analysis(
            analysis_type="U-CHART",
            title="U Chart",
            navigator_name=f'U Chart of {self.column_name}',
            data={
                "u_values": self.result["u_values"],
                "ucls": self.result["ucls"],
                "lcls": self.result["lcls"],
                "violations": self.violations
            },
            stats={
                "u_bar": self.result["u_bar"]
            },
            settings={
                "column": self.column_name,
                "distribution": self.distribution,
                "calculation_method": self.calculation_method_key,
            }
        )

        self.main.navigator.add_analysis(
            analysis
        )

    def create_ui(self):

        container = ttk.PanedWindow(
            self,
            orient="horizontal"
        )

        container.pack(
            fill="both",
            expand=True
        )

        left = ttk.Frame(container)

        container.add(
            left,
            weight=5
        )

        right = ttk.Frame(container)

        container.add(
            right,
            weight=1
        )

        favor_chart_panel(container)

        fig, ax = plt.subplots(
            figsize=(15, 6)
        )

        x = list(range(
            1,
            len(self.result["u_values"]) + 1
        ))

        ax.plot(
            x,
            self.result["u_values"],
            marker="o",
            markevery=marker_stride(len(self.result["u_values"])),
            linewidth=1.8,
            label="U"
        )

        if "ucls" in self.result and "lcls" in self.result:
            ax.plot(
                x,
                self.result["ucls"],
                linestyle="--",
                color="red",
                label="UCL"
            )

            ax.plot(
                x,
                self.result["lcls"],
                linestyle="--",
                color="red",
                label="LCL"
            )
        max_u = max(self.result["u_values"])

        max_ucl = max(self.result.get("ucls", [0]))

        ax.set_ylim(
            0,
            max(
                max_u * 1.5,
                max_ucl * 1.1
            )
        )

        ax.axhline(
            self.result["u_bar"],
            linestyle="--",
            color="green",
            label=f'Ubar = {round(self.result["u_bar"], 4)}'
        )

        for v in self.violations:

            idx = v["point"] - 1

            if idx >= len(self.result["u_values"]):
                continue

            short_rule = v["rule"].replace(
                "Rule ",
                ""
            )

            ax.scatter(
                v["point"],
                self.result["u_values"][idx],
                color="red",
                marker="s",
                s=120
            )

            ax.annotate(
                short_rule,
                (
                    v["point"],
                    self.result["u_values"][idx]
                ),
                textcoords="offset points",
                xytext=(0, 10),
                rotation=90,
                fontsize=8,
                color="red"
            )

        ax.set_title(
            f'U Chart - {self.column_name}'
        )

        ax.grid(
            True,
            alpha=0.3
        )

        ax.legend()

        canvas = FigureCanvasTkAgg(
            fig,
            master=left
        )

        canvas.draw_idle()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        info = ttk.LabelFrame(
            right,
            text="Analysis Result",
            padding=10
        )

        info.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        text = tk.Text(
            info,
            wrap="word"
        )

        text.pack(
            fill="both",
            expand=True
        )

        if self.calculation_method_key == "converted_sample_sd":
            method = self.main.t("converted_u_limit_method")
            text.insert("end", f'{self.main.t("limit_method")} : {method}\n')
        else:
            text.insert("end", f'{self.main.t("distribution")} : {self.distribution}\n')
        text.insert(
            "end",
            f'Data Source : {self.column_name}\n\n'
        )

        text.insert(
            "end",
            f'Ubar : {round(self.result["u_bar"], 5)}\n\n'
        )

        text.insert(
            "end",
            "VIOLATIONS\n\n"
        )

        if len(self.violations) == 0:

            text.insert(
                "end",
                "No violations detected"
            )

        else:

            for v in self.violations:

                text.insert(
                    "end",
                    f'{v["rule"]}\n'
                )

                text.insert(
                    "end",
                    f'Point : {v["point"]}\n'
                )

                text.insert(
                    "end",
                    f'Description : {v["description"]}\n'
                )

                text.insert(
                    "end",
                    f'Cause : {v["cause"]}\n\n'
                )

        dominant = get_most_frequent_rule(
            self.violations
        )

        text.insert(
            "end",
            "\nMOST FREQUENT VIOLATION\n\n"
        )

        text.insert(
            "end",
            dominant
        )

        text.config(
            state="disabled"
        )
class UChartConvertedPopup(tk.Toplevel):

    def __init__(self, main, sheet):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title("U Chart - Converted Data")

        self.geometry("500x750")
        center_window(self)

        self.converted_column = None

        self.create_ui()

    def create_ui(self):

        container = ttk.Frame(
            self,
            padding=20
        )

        container.pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            container,
            text="Using Converted Data",
            font=("Segoe UI", 11, "bold")
        ).pack(
            pady=(0, 20)
        )

        # =====================================
        # COLUMN LIST
        # =====================================

        ttk.Label(
            container,
            text="Available Columns"
        ).pack(
            anchor="w"
        )

        self.column_listbox = tk.Listbox(
            container,
            height=12
        )

        self.column_listbox.pack(
            fill="both",
            expand=True,
            pady=(5, 15)
        )

        columns = self.sheet.get_column_names()

        self.numeric_columns = {}

        for i, col in enumerate(columns):

            data = self.sheet.get_column_data(i)

            if not any(value is not None and str(value).strip() for value in data):
                continue

            self.numeric_columns[col] = i

            self.column_listbox.insert(
                "end",
                col
            )

        # =====================================
        # SELECT COLUMN
        # =====================================

        ttk.Button(
            container,
            text="Set as Converted Column",
            command=self.set_converted_column
        ).pack(
            fill="x",
            pady=5
        )

        self.converted_label = ttk.Label(
            container,
            text="Converted Column : -"
        )

        self.converted_label.pack(
            anchor="w",
            pady=(10, 15)
        )

        ttk.Label(
            container,
            text=self.main.t("converted_u_limit_method"),
            wraplength=450,
            justify="left"
        ).pack(anchor="w", pady=(0, 16))

        # =====================================
        # GENERATE
        # =====================================

        ttk.Button(
            container,
            text="Generate U Chart",
            command=self.generate
        ).pack(
            fill="x",
            ipady=6
        )

    def set_converted_column(self):

        selected = self.column_listbox.curselection()

        if not selected:
            return

        self.converted_column = self.column_listbox.get(
            selected[0]
        )

        self.converted_label.config(
            text=f'Converted Column : {self.converted_column}'
        )

    @handle_validation_errors
    def generate(self):

        if not self.converted_column:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("select_converted_column")
            )

            return

        converted_idx = self.numeric_columns[
            self.converted_column
        ]

        u_values = clean_numeric(
            self.sheet.get_column_data(
                converted_idx
            )
        )

        if len(u_values) < 2:
            raise ValueError("At least two valid converted observations are required")

        # =====================================
        # SIMPLIFIED U CHART
        # =====================================

        u_bar = np.mean(
            u_values
        )

        sigma = np.std(
            u_values,
            ddof=1
        )

        ucl = u_bar + (3 * sigma)

        lcl = u_bar - (3 * sigma)

        if lcl < 0:

            lcl = 0

        result = {

            "u_values": u_values,

            "u_bar": u_bar,

            "ucls": [
                ucl
                for _ in u_values
            ],

            "lcls": [
                lcl
                for _ in u_values
            ],

            "calculation_method": "converted_sample_sd"
        }

        violations = check_nelson_rules(
            result["u_values"],
            result["u_bar"],
            result["ucls"],
            result["lcls"],
                language=self.main.current_lang
        )

        deliver_result(self, lambda: UChartPopup(
            self.main,
            result,
            violations,
            self.converted_column,
            distribution=None,
            calculation_method_key="converted_sample_sd"
        ))
