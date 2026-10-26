from logic.validation import handle_validation_errors, numeric_values
from logic.nelson_rules import check_nelson_rules as _shared_nelson_rules, rule_details, localize_chart_results
import tkinter as tk
from tkinter import ttk, messagebox
from resources import resource_path
import numpy as np
import matplotlib.pyplot as plt

from collections import Counter

from logic.chart_canvas import FigureCanvasTkAgg, marker_stride
from ui.chart_view import EmbeddedChartFrame, favor_chart_panel
from ui.dialogs import deliver_result

from models.analysis import Analysis
from PIL import Image, ImageTk

def clean_numeric(data):
    return numeric_values(data)


def build_horizontal_groups(data, subgroup_size):
    values = numeric_values(data, "attribute chart data")
    if isinstance(subgroup_size, bool) or not isinstance(subgroup_size, int) or subgroup_size <= 0:
        raise ValueError("Subgroup size must be a positive integer")
    if not values:
        raise ValueError("At least one observation is required")
    if len(values) % subgroup_size:
        raise ValueError(
            f"Incomplete final subgroup: {len(values)} observations is not divisible by {subgroup_size}"
        )
    return [values[index:index + subgroup_size]
            for index in range(0, len(values), subgroup_size)]


def calculate_p_chart(defect_groups):
    if defect_groups is None:
        raise ValueError("At least one p-chart subgroup is required")
    groups = [numeric_values(group, f"p-chart subgroup {index}")
              for index, group in enumerate(defect_groups, start=1)]
    if not groups or any(not group for group in groups):
        raise ValueError("p-chart subgroups must not be empty")
    if any(value not in (0, 1) for group in groups for value in group):
        raise ValueError("p-chart data must contain only 0 or 1 defect indicators")
    subgroup_sizes = [len(group) for group in groups]
    defect_counts = [sum(group) for group in groups]
    proportions = [count / size for count, size in zip(defect_counts, subgroup_sizes)]
    p_bar = sum(defect_counts) / sum(subgroup_sizes)
    sigmas = [np.sqrt(p_bar * (1 - p_bar) / size) for size in subgroup_sizes]
    ucls = [p_bar + 3 * sigma for sigma in sigmas]
    lcls = [max(0.0, p_bar - 3 * sigma) for sigma in sigmas]
    return {
        "proportions": proportions,
        "subgroup_sizes": subgroup_sizes,
        "p_bar": p_bar,
        "ucls": ucls,
        "lcls": lcls,
    }


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


class PChartConfigPopup(tk.Toplevel):

    def __init__(self, main, sheet, analysis=None, save_to_history=True):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title("P Chart")

        self.geometry("1000x650")

        self.selected_columns = []

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
            selectmode="extended",
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

        ttk.Button(
            center,
            text="Select →",
            command=self.select_column
        ).pack(
            pady=(120, 10),
            ipadx=10,
            ipady=5
        )

        ttk.Button(
            center,
            text="← Remove",
            command=self.remove_column
        ).pack(
            pady=10,
            ipadx=10,
            ipady=5
        )

        ttk.Label(
            right,
            text="Selected Columns",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.selected_listbox = tk.Listbox(
            right,
            height=15
        )

        self.selected_listbox.pack(
            fill="both",
            expand=True
        )

        config = ttk.LabelFrame(
            right,
            text="Configuration",
            padding=10
        )

        config.pack(
            fill="x",
            pady=(15, 0)
        )

        ttk.Label(
            config,
            text=self.main.t("chart_attribute_guidance"),
            wraplength=300,
            justify="left"
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            config,
            text="Subgroup Size"
        ).pack(anchor="w")

        self.subgroup_var = tk.StringVar(
            value="50"
        )

        ttk.Entry(
            config,
            textvariable=self.subgroup_var
        ).pack(
            fill="x",
            pady=(5, 0)
        )

        ttk.Label(
            config,
            text="Default = 50"
        ).pack(anchor="w")

        ttk.Button(
            config,
            text="Generate P Chart",
            command=self.generate
        ).pack(
            fill="x",
            pady=(20, 0),
            ipady=6
        )

    def select_column(self):

        selected = self.column_listbox.curselection()

        for idx in selected:

            col_name = self.column_listbox.get(idx)

            if col_name not in self.selected_columns:

                self.selected_columns.append(
                    col_name
                )

        self.refresh_selected()

    def remove_column(self):

        selected = self.selected_listbox.curselection()

        if not selected:
            return

        col_name = self.selected_listbox.get(
            selected[0]
        )

        self.selected_columns.remove(
            col_name
        )

        self.refresh_selected()

    def refresh_selected(self):

        self.selected_listbox.delete(
            0,
            "end"
        )

        for col in self.selected_columns:

            self.selected_listbox.insert(
                "end",
                col
            )

    @handle_validation_errors
    def generate(self):

        if len(self.selected_columns) == 0:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("select_at_least_one_column")
            )

            return

        try:

            subgroup_size = int(
                self.subgroup_var.get()
            )

        except:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("invalid_subgroup_size")
            )

            return

        results = []

        for col_name in self.selected_columns:

            idx = self.numeric_columns[
                col_name
            ]

            data = clean_numeric(
                self.sheet.get_column_data(idx)
            )

            groups = build_horizontal_groups(
                data,
                subgroup_size
            )

            if len(groups) == 0:
                continue

            result = calculate_p_chart(
                groups
            )

            violations = check_nelson_rules(
                result["proportions"],
                result["p_bar"],
                result["ucls"],
                result["lcls"],
                language=self.main.current_lang
            )

            results.append({

                "column": col_name,
                "result": result,
                "violations": violations
            })

        if len(results) == 0:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("no_valid_subgroup")
            )

            return

        deliver_result(self, lambda: PChartPopup(self.main, results))


class PChartPopup(EmbeddedChartFrame):

    def __init__(
        self,
        main,
        results,
        save_to_history=True,
    ):

        super().__init__(main.root)

        self.main = main

        self.results = localize_chart_results(results, self.main.current_lang)

        self.title("P Charts")

        self.state("zoomed")

        self.create_ui()

        if save_to_history:
            self.save_analysis()

    def save_analysis(self):

        for item in self.results:

            result = item["result"]

            analysis = Analysis(
                analysis_type="P-CHART",
                title="P Chart",
                navigator_name=f'P Chart of {item["column"]}',
                data={
                    "proportions": result["proportions"],
                    "ucls": result["ucls"],
                    "lcls": result["lcls"],
                    "violations": item["violations"]
                },
                stats={
                    "p_bar": result["p_bar"]
                },
                settings={
                    "column": item["column"]
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

        for item in self.results:

            section = ttk.LabelFrame(
                left,
                text=item["column"],
                padding=10
            )

            section.pack(
                fill="both",
                expand=True,
                padx=10,
                pady=10
            )

            result = item["result"]

            violations = item["violations"]

            fig, ax = plt.subplots(
                figsize=(15, 5)
            )

            x = list(range(
                1,
                len(result["proportions"]) + 1
            ))

            ax.plot(
                x,
                result["proportions"],
                marker="o",
                markevery=marker_stride(len(result["proportions"])),
                linewidth=1.8,
                label="P"
            )

            if "ucls" in result and "lcls" in result:
                ax.plot(
                    x,
                    result["ucls"],
                    linestyle="--",
                    color="red",
                    label="UCL"
                )

                ax.plot(
                    x,
                    result["lcls"],
                    linestyle="--",
                    color="red",
                    label="LCL"
                )

            ax.axhline(
                result["p_bar"],
                linestyle="--",
                color="green",
                label=f'Pbar = {round(result["p_bar"], 4)}'
            )

            for v in violations:

                idx = v["point"] - 1

                if idx >= len(result["proportions"]):
                    continue

                short_rule = v["rule"].replace(
                    "Rule ",
                    ""
                )

                ax.scatter(
                    v["point"],
                    result["proportions"][idx],
                    color="red",
                    marker="s",
                    s=120
                )

                ax.annotate(
                    short_rule,
                    (
                        v["point"],
                        result["proportions"][idx]
                    ),
                    textcoords="offset points",
                    xytext=(0, 10),
                    rotation=90,
                    fontsize=8,
                    color="red"
                )

            ax.set_title(
                f'P Chart - {item["column"]}'
            )

            ax.grid(
                True,
                alpha=0.3
            )

            ax.legend()

            canvas = FigureCanvasTkAgg(
                fig,
                master=section
            )

            canvas.draw_idle()

            canvas.get_tk_widget().pack(
                fill="both",
                expand=True
            )

            info = ttk.LabelFrame(
                right,
                text=item["column"],
                padding=10
            )

            info.pack(
                fill="x",
                padx=10,
                pady=10
            )

            text = tk.Text(
                info,
                height=25,
                wrap="word"
            )

            text.pack(
                fill="both",
                expand=True
            )

            text.insert(
                "end",
                f'Pbar : {round(result["p_bar"], 5)}\n\n'
            )

            text.insert(
                "end",
                "VIOLATIONS\n\n"
            )

            if len(violations) == 0:

                text.insert(
                    "end",
                    "No violations detected"
                )

            else:

                for v in violations:

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
                violations
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
