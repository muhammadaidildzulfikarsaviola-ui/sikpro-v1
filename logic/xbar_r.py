from logic.validation import handle_validation_errors, numeric_values, numeric_subgroups
from logic.nelson_rules import check_nelson_rules as _shared_nelson_rules, rule_details, localize_chart_results
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import matplotlib.pyplot as plt

from collections import Counter

from logic.chart_canvas import FigureCanvasTkAgg, marker_stride
from ui.chart_view import EmbeddedChartFrame, favor_chart_panel
from ui.dialogs import deliver_result

from models.analysis import Analysis
from PIL import Image, ImageTk
from resources import resource_path
rule_images = {
    1: resource_path("rules/rules1.png"),
    2: resource_path("rules/rules2.png"),
    3: resource_path("rules/rules3.png"),
    4: resource_path("rules/rules4.png"),
    5: resource_path("rules/rules5.png"),
    6: resource_path("rules/rules6.png"),
    7: resource_path("rules/rules7.png"),
    8: resource_path("rules/rules8.png"),
}

A2_CONSTANTS = {
    2: 1.880,
    3: 1.023,
    4: 0.729,
    5: 0.577,
    6: 0.483,
    7: 0.419,
    8: 0.373,
    9: 0.337,
    10: 0.308
}

D3_CONSTANTS = {
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    6: 0,
    7: 0.076,
    8: 0.136,
    9: 0.184,
    10: 0.223
}

D4_CONSTANTS = {
    2: 3.267,
    3: 2.574,
    4: 2.282,
    5: 2.114,
    6: 2.004,
    7: 1.924,
    8: 1.864,
    9: 1.816,
    10: 1.777
}
A3_CONSTANTS = {
    2: 2.659,
    3: 1.954,
    4: 1.628,
    5: 1.427,
    6: 1.287,
    7: 1.182,
    8: 1.099,
    9: 1.032,
    10: 0.975
}

B3_CONSTANTS = {
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    6: 0.030,
    7: 0.118,
    8: 0.185,
    9: 0.239,
    10: 0.284
}

B4_CONSTANTS = {
    2: 3.267,
    3: 2.568,
    4: 2.266,
    5: 2.089,
    6: 1.970,
    7: 1.882,
    8: 1.815,
    9: 1.761,
    10: 1.716
}


def clean_numeric(data):
    return numeric_values(data)


def build_vertical_subgroups(sheet, columns):
    columns = list(columns)
    if not columns:
        raise ValueError("Select at least one column for vertical subgroups")
    rows = sheet.get_sheet_data()
    selected = []
    for row_index, row in enumerate(rows):
        cells = [row[column] if column < len(row) else "" for column in columns]
        if any(value is not None and str(value).strip() != "" for value in cells):
            selected.append((row_index + 1, cells))
    if not selected:
        raise ValueError("No subgroup data was entered")

    groups = []
    for row_number, cells in selected:
        present = [value is not None and str(value).strip() != "" for value in cells]
        if not any(present):
            continue
        if not all(present):
            missing_column = columns[present.index(False)]
            raise ValueError(
                f"Incomplete subgroup at row {row_number}, column C{missing_column + 1}"
            )
        group = []
        for column, value in zip(columns, cells):
            group.append(numeric_values([value], f"row {row_number}, column C{column + 1}")[0])
        groups.append(group)
    if not groups:
        raise ValueError("No complete subgroup data was entered")
    return groups


def build_horizontal_subgroups(data, subgroup_size):
    values = numeric_values(data, "horizontal subgroup data")
    if isinstance(subgroup_size, bool) or not isinstance(subgroup_size, int):
        raise ValueError("Subgroup size must be an integer")
    if not 2 <= subgroup_size <= 10:
        raise ValueError("Subgroup size must be between 2 and 10")
    if not values:
        raise ValueError("At least one observation is required")
    if len(values) % subgroup_size:
        raise ValueError(
            f"Incomplete final subgroup: {len(values)} observations is not divisible by {subgroup_size}"
        )
    return [values[i:i + subgroup_size] for i in range(0, len(values), subgroup_size)]


def calculate_xbar_r(subgroups):
    subgroups = numeric_subgroups(subgroups, "subgroups", min_size=2, max_size=10)
    subgroup_size = len(subgroups[0])
    xbars = [np.mean(group) for group in subgroups]
    ranges = [max(group) - min(group) for group in subgroups]
    xbar_bar = float(np.mean(xbars))
    r_bar = float(np.mean(ranges))
    A2 = A2_CONSTANTS[subgroup_size]
    D3 = D3_CONSTANTS[subgroup_size]
    D4 = D4_CONSTANTS[subgroup_size]
    return {
        "xbars": xbars, "ranges": ranges,
        "xbar_bar": xbar_bar, "r_bar": r_bar,
        "xbar_ucl": xbar_bar + A2 * r_bar,
        "xbar_lcl": xbar_bar - A2 * r_bar,
        "r_ucl": D4 * r_bar, "r_lcl": D3 * r_bar,
        "subgroup_size": subgroup_size,
    }

def get_rule_explanation(rule_no, language="id"):
    details = rule_details(rule_no, language)
    return details["description"], details["interpretation"]


def check_nelson_rules(data, mean, ucl, lcl, language="id"):
    raw_violations = _shared_nelson_rules(data, mean, ucl, lcl, language=language)
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

def generate_interpretation(
    xbar_violations,
    s_violations
):

    total = len(xbar_violations) + len(s_violations)

    if total == 0:

        return (
            "Process appears statistically controlled. "
            "No Nelson Rule violations detected."
        )

    interpretation = []

    interpretation.append(
        f'Total violations detected: {total}'
    )

    if len(xbar_violations) > 0:

        interpretation.append(
            "Xbar chart indicates instability in process mean."
        )

    if len(s_violations) > 0:

        interpretation.append(
            "R indicates instability in process variation."
        )

    dominant = get_most_frequent_rule(
        xbar_violations + s_violations
    )

    interpretation.append(
        f'Dominant violation: {dominant}'
    )

    return "\n".join(interpretation)


def generate_recommendation(
    xbar_violations,
    s_violations
):

    recommendations = []

    all_rules = [
        v["rule"]
        for v in xbar_violations + s_violations
    ]

    if "Rule 1" in all_rules:

        recommendations.append(
            "- Check machine calibration and operator method"
        )

    if "Rule 2" in all_rules:

        recommendations.append(
            "- Investigate possible process shift"
        )

    if "Rule 3" in all_rules:

        recommendations.append(
            "- Check gradual tool wear or temperature drift"
        )

    if "Rule 4" in all_rules:

        recommendations.append(
            "- Investigate alternating sources or repeated process adjustments"
        )

    if "Rule 5" in all_rules:

        recommendations.append(
            "- Monitor process variability closely"
        )

    if "Rule 6" in all_rules:

        recommendations.append(
            "- Review raw material consistency and setup"
        )

    if "Rule 7" in all_rules:

        recommendations.append(
            "- Review measurement resolution and possible over-control"
        )

    if "Rule 8" in all_rules:

        recommendations.append(
            "- Investigate mixed machines, operators, or production batches"
        )

    if len(recommendations) == 0:

        recommendations.append(
            "- Continue monitoring process routinely"
        )

    return "\n".join(recommendations)

class XbarRConfigPopup(tk.Toplevel):

    def __init__(self, main, sheet):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title(self.main.t("xbar_r_chart"))

        self.geometry("1100x650")

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

        left_panel = ttk.Frame(container)

        left_panel.pack(
            side="left",
            fill="both",
            expand=True
        )

        center_panel = ttk.Frame(container)

        center_panel.pack(
            side="left",
            fill="y",
            padx=15
        )

        right_panel = ttk.Frame(container)

        right_panel.pack(
            side="right",
            fill="both",
            expand=True
        )

        ttk.Label(
            left_panel,
            text=self.main.t("available_columns"),
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")


        self.column_listbox = tk.Listbox(
            left_panel,
            selectmode="extended",
            height=25
        )

        self.column_listbox.pack(
            fill="both",
            expand=True,
            pady=(5, 0)
        )

        self.load_columns()

        ttk.Button(
            center_panel,
            text=self.main.t("chart_select_column_action"),
            command=self.select_column
        ).pack(
            pady=(120, 10),
            ipadx=10,
            ipady=5
        )

        ttk.Button(
            center_panel,
            text=self.main.t("chart_remove_column_action"),
            command=self.remove_column
        ).pack(
            pady=10,
            ipadx=10,
            ipady=5
        )

        ttk.Label(
            right_panel,
            text=self.main.t("chart_selected_columns"),
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        selected_container = ttk.Frame(
            right_panel
        )

        selected_container.pack(
            fill="both",
            expand=True,
            pady=(5, 0)
        )

        self.selected_canvas = tk.Canvas(
            selected_container,
            highlightthickness=0
        )

        selected_scrollbar = ttk.Scrollbar(
            selected_container,
            orient="vertical",
            command=self.selected_canvas.yview
        )

        self.selected_canvas.configure(
            yscrollcommand=selected_scrollbar.set
        )

        selected_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.selected_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.selected_frame = ttk.Frame(
            self.selected_canvas
        )

        self.selected_canvas.create_window(
            (0, 0),
            window=self.selected_frame,
            anchor="nw"
        )

        self.selected_frame.bind(
            "<Configure>",
            lambda e: self.selected_canvas.configure(
                scrollregion=self.selected_canvas.bbox("all")
            )
        )

        config_frame = ttk.LabelFrame(
            right_panel,
            text=self.main.t("chart_configuration"),
            padding=10
        )

        config_frame.pack(
            fill="x",
            pady=(15, 0)
        )

        ttk.Label(
            config_frame,
            text=self.main.t("chart_subgroup_guidance"),
            wraplength=280,
            justify="left"
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            config_frame,
            text=self.main.t("chart_subgroup_mode")
        ).pack(anchor="w")

        self.mode_var = tk.StringVar(
            value="horizontal"
        )
        self.mode_var.trace_add(
            "write",
            self.toggle_subgroup_entry
        )
        
        ttk.Radiobutton(
            config_frame,
            text=self.main.t("chart_observations_one_column"),
            variable=self.mode_var,
            value="horizontal"
        ).pack(anchor="w")

        ttk.Radiobutton(
            config_frame,
            text=self.main.t("chart_observations_across_columns"),
            variable=self.mode_var,
            value="vertical"
        ).pack(anchor="w")

        ttk.Label(
            config_frame,
            text=self.main.t("chart_subgroup_size_one_column")
        ).pack(
            anchor="w",
            pady=(15, 0)
        )

        self.subgroup_size_var = tk.StringVar()

        self.subgroup_entry = ttk.Entry(
            config_frame,
            textvariable=self.subgroup_size_var
        )

        self.subgroup_entry.pack(
            fill="x",
            pady=(5, 0)
        )

        ttk.Label(
            config_frame,
            text=self.main.t("chart_default_subgroup_five")
        ).pack(anchor="w")
        self.toggle_subgroup_entry()

        ttk.Button(
            config_frame,
            text=self.main.t("chart_generate_xbar_r"),
            command=self.generate
        ).pack(
            pady=(20, 0),
            fill="x",
            ipady=6
        )

    def load_columns(self):

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

    def toggle_subgroup_entry(self, *args):

        mode = self.mode_var.get()

        if mode == "vertical":

            self.subgroup_entry.config(
                state="disabled"
            )

            self.subgroup_size_var.set("")

        else:

            self.subgroup_entry.config(
                state="normal"
            )

    def select_column(self):

        selected = self.column_listbox.curselection()

        if not selected:
            return

        for idx in selected:

            col_name = self.column_listbox.get(idx)

            if col_name not in self.selected_columns:

                self.selected_columns.append(
                    col_name
                )

        self.refresh_selected_columns()

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

        self.refresh_selected_columns()

    def refresh_selected_columns(self):

        for widget in self.selected_frame.winfo_children():

            widget.destroy()

        self.selected_listbox = tk.Listbox(
            self.selected_frame,
            height=15
        )

        self.selected_listbox.pack(
            fill="both",
            expand=True
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

        subgroup_size = 5

        if self.mode_var.get() == "horizontal":

            subgroup_text = self.subgroup_size_var.get().strip()

            if subgroup_text != "":

                try:

                    subgroup_size = int(
                        subgroup_text
                    )

                except:

                    messagebox.showerror(
                        self.main.t("error"),
                        self.main.t("subgroup_size_integer")
                    )

                    return

        mode = self.mode_var.get()

        results = []

        if mode == "vertical":

            all_idx = [
                self.numeric_columns[x]
                for x in self.selected_columns
            ]

            subgroups = build_vertical_subgroups(
                self.sheet,
                all_idx
            )

            result = calculate_xbar_r(
                subgroups
            )

            xbar_violations = check_nelson_rules(
                result["xbars"],
                result["xbar_bar"],
                result["xbar_ucl"],
                result["xbar_lcl"],
                language=self.main.current_lang
            )

            s_violations = check_nelson_rules(
                result["ranges"],
                result["r_bar"],
                result["r_ucl"],
                result["r_lcl"],
                language=self.main.current_lang
            )

            results.append({

                "column": ", ".join(
                    self.selected_columns
                ),

                "result": result,

                "xbar_violations": xbar_violations,

                "s_violations": s_violations,

                "interpretation": generate_interpretation(
                    xbar_violations,
                    s_violations
                ),

                "recommendation": generate_recommendation(
                    xbar_violations,
                    s_violations
                )
            })

        else:

            for col_name in self.selected_columns:

                idx = self.numeric_columns[
                    col_name
                ]

                data = clean_numeric(
                    self.sheet.get_column_data(idx)
                )

                subgroups = build_horizontal_subgroups(
                    data,
                    subgroup_size
                )

                if len(subgroups) == 0:
                    continue

                result = calculate_xbar_r(
                    subgroups
                )

                xbar_violations = check_nelson_rules(
                    result["xbars"],
                    result["xbar_bar"],
                    result["xbar_ucl"],
                    result["xbar_lcl"],
                language=self.main.current_lang
                )

                s_violations = check_nelson_rules(
                    result["ranges"],
                    result["r_bar"],
                    result["r_ucl"],
                    result["r_lcl"],
                    language=self.main.current_lang
                )

                results.append({

                    "column": col_name,

                    "result": result,

                    "xbar_violations": xbar_violations,

                    "s_violations": s_violations,

                    "interpretation": generate_interpretation(
                        xbar_violations,
                        s_violations
                    ),

                    "recommendation": generate_recommendation(
                        xbar_violations,
                        s_violations
                    )
                })

        if len(results) == 0:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t("no_valid_subgroup")
            )

            return

        deliver_result(self, lambda: XbarRChartPopup(self.main, results))

class XbarRChartPopup(EmbeddedChartFrame):

    def __init__(
        self,
        main,
        results,
        analysis=None, 
        save_to_history=True
    ):

        super().__init__(main.root)

        self.main = main

        self.results = localize_chart_results(results, self.main.current_lang)

        self.title(self.main.t("xbar_r_chart"))

        self.state("zoomed")

        self.create_ui()

        if save_to_history:
            self.save_analysis()

    def save_analysis(self):

        for item in self.results:

            result = item["result"]

            analysis = Analysis(
                analysis_type="XBAR-R",
                title="Xbar-R",
                navigator_name=f'Xbar-R of {item["column"]}',
                data={
                    "xbars": result["xbars"],
                    "ranges": result["ranges"],
                    "xbar_violations": item.get("xbar_violations", []),
                    "s_violations": item.get("s_violations", [])
                },
                stats={
                    "xbar_bar": result["xbar_bar"],
                    "r_bar": result["r_bar"],
                    "xbar_ucl": result["xbar_ucl"],
                    "xbar_lcl": result["xbar_lcl"],
                    "r_ucl": result["r_ucl"],
                    "r_lcl": result["r_lcl"]
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

        left_panel = ttk.Frame(container)

        container.add(
            left_panel,
            weight=5
        )

        right_panel = ttk.Frame(container)

        container.add(
            right_panel,
            weight=1
        )

        favor_chart_panel(container)

        left_canvas = tk.Canvas(
            left_panel,
            highlightthickness=0
        )

        left_scrollbar = ttk.Scrollbar(
            left_panel,
            orient="vertical",
            command=left_canvas.yview
        )

        left_canvas.configure(
            yscrollcommand=left_scrollbar.set
        )

        left_scrollbar.pack(
            side="right",
            fill="y"
        )

        left_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        left_frame = ttk.Frame(
            left_canvas
        )

        left_window = left_canvas.create_window(
            (0, 0),
            window=left_frame,
            anchor="nw"
        )

        left_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(
                scrollregion=left_canvas.bbox("all")
            )
        )

        left_canvas.bind(
            "<Configure>",
            lambda e: left_canvas.itemconfig(
                left_window,
                width=e.width
            )
        )

        right_canvas = tk.Canvas(
            right_panel,
            highlightthickness=0
        )

        

        right_scrollbar = ttk.Scrollbar(
            right_panel,
            orient="vertical",
            command=right_canvas.yview
        )

        right_canvas.configure(
            yscrollcommand=right_scrollbar.set
        )

        right_scrollbar.pack(
            side="right",
            fill="y"
        )

        right_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        right_frame = ttk.Frame(
            right_canvas
        )

        right_window = right_canvas.create_window(
            (0, 0),
            window=right_frame,
            anchor="nw"
        )

        right_frame.bind(
            "<Configure>",
            lambda e: right_canvas.configure(
                scrollregion=right_canvas.bbox("all")
            )
        )

        right_canvas.bind(
            "<Configure>",
            lambda e: right_canvas.itemconfig(
                right_window,
                width=e.width,
                height=e.height
            )
        )

        for item in self.results:

            col_name = item["column"]

            result = item["result"]

            xbar_violations = item[
                "xbar_violations"
            ]

            s_violations = item[
                "s_violations"
            ]

            section = ttk.LabelFrame(
                left_frame,
                text=col_name,
                padding=10
            )

            section.pack(
                fill="both",
                expand=True,
                padx=10,
                pady=10
            )

            fig, axes = plt.subplots(
                2,
                1,
                figsize=(15, 8)
            )

            plt.subplots_adjust(
                hspace=0.4
            )

            ax_xbar = axes[0]
            ax_s = axes[1]

            x = list(range(
                1,
                len(result["xbars"]) + 1
            ))

            ax_xbar.plot(
                x,
                result["xbars"],
                marker="o",
                markevery=marker_stride(len(result["xbars"])),
                linewidth=1.8,
                label="Xbar"
            )

            ax_xbar.axhline(
                result["xbar_bar"],
                linestyle="--",
                color="green",
                label=f'Mean = {round(result["xbar_bar"], 4)}'
            )

            ax_xbar.axhline(
                result["xbar_ucl"],
                linestyle="--",
                color="red",
                label=f'UCL = {round(result["xbar_ucl"], 4)}'
            )

            ax_xbar.axhline(
                result["xbar_lcl"],
                linestyle="--",
                color="red",
                label=f'LCL = {round(result["xbar_lcl"], 4)}'
            )

            for v in xbar_violations:

                idx = v["point"] - 1

                if idx >= len(result["xbars"]):
                    continue

                short_rule = v["rule"].replace(
                    "Rule ",
                    ""
                )

                ax_xbar.scatter(
                    v["point"],
                    result["xbars"][idx],
                    color="red",
                    marker="s",
                    s=120
                )

                ax_xbar.annotate(
                    short_rule,
                    (
                        v["point"],
                        result["xbars"][idx]
                    ),
                    textcoords="offset points",
                    xytext=(0, 10),
                    rotation=90,
                    fontsize=8,
                    color="red"
                )

            ax_xbar.set_title(
                f'Xbar-R Chart - {col_name}'
            )

            ax_xbar.grid(
                True,
                alpha=0.3
            )

            ax_xbar.legend()

            ax_s.plot(
                x,
                result["ranges"],
                marker="o",
                markevery=marker_stride(len(result["ranges"])),
                linewidth=1.8,
                color="#9467bd",
                label="R"
            )

            ax_s.axhline(
                result["r_bar"],
                linestyle="--",
                color="green",
                label=f'Mean = {round(result["r_bar"], 4)}'
            )

            ax_s.axhline(
                result["r_lcl"],
                linestyle="--",
                color="red",
                label=f'LCL = {round(result["r_lcl"], 4)}'
            )

            ax_s.axhline(
                result["r_ucl"],
                linestyle="--",
                color="red",
                label=f'UCL = {round(result["r_ucl"], 4)}'
            )

            for v in s_violations:

                idx = v["point"] - 1

                if idx >= len(result["ranges"]):
                    continue

                short_rule = v["rule"].replace(
                    "Rule ",
                    ""
                )

                ax_s.scatter(
                    v["point"],
                    result["ranges"][idx],
                    color="red",
                    marker="s",
                    s=120
                )

                ax_s.annotate(
                    short_rule,
                    (
                        v["point"],
                        result["ranges"][idx]
                    ),
                    textcoords="offset points",
                    xytext=(0, 10),
                    rotation=90,
                    fontsize=8,
                    color="red"
                )

            ax_s.set_title(
                f'R Chart of - {col_name}'
            )

            ax_s.grid(
                True,
                alpha=0.3
            )

            ax_s.legend()

            chart_canvas = FigureCanvasTkAgg(
                fig,
                master=section
            )

            chart_canvas.draw_idle()

            chart_canvas.get_tk_widget().pack(
                fill="both",
                expand=True
            )

            info_section = ttk.LabelFrame(
                right_frame,
                text=col_name,
                padding=10
            )

            info_section.pack(
                fill="both",
                expand=True,
                padx=10,
                pady=10
            )

            text = tk.Text(
                info_section,
                wrap="word",
                height=30
            )

            text.pack(
                fill="both",
                expand=True
            )
            all_violations = (
                xbar_violations +
                s_violations
            )

            text.config(
                state="normal"
            )

            text.delete(
                "1.0",
                "end"
            )

            if not all_violations:

                text.insert(
                    "end",
                    self.main.t("no_violations_detected")
                )

                text.config(
                    state="disabled"
                )

                continue

            detected_rules = []

            counter = {}

            for v in all_violations:

                rule = v["rule"]

                counter[rule] = (
                    counter.get(rule, 0) + 1
                )

                if rule not in detected_rules:

                    detected_rules.append(rule)

            dominant_rule = max(
                counter,
                key=counter.get
            )

            additional_rules = [
                r for r in detected_rules
                if r != dominant_rule
            ]

            text.insert(
                "end",
                f'{col_name}\n\n',
                "title"
            )


            text.insert(
                "end",
                "XBAR VIOLATIONS\n\n",
                "subtitle"
            )

            if len(xbar_violations) == 0:

                text.insert(
                    "end",
                    f'{self.main.t("no_violations_detected")}\n\n'
                )

            else:

                for v in xbar_violations:

                    text.insert(
                        "end",
                        f'[{v["rule"]}]\n',
                        "subtitle"
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
                        f'Possible Cause : {v["cause"]}\n\n'
                    )


            text.insert(
                "end",
                "R VIOLATIONS\n\n",
                "subtitle"
            )

            if len(s_violations) == 0:

                text.insert(
                    "end",
                    f'{self.main.t("no_violations_detected")}\n\n'
                )

            else:

                for v in s_violations:

                    text.insert(
                        "end",
                        f'[{v["rule"]}]\n',
                        "subtitle"
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
                        f'Possible Cause : {v["cause"]}\n\n'
                    )

            text.insert(
                "end",
                "Dominant Rule:\n",
                "subtitle"
            )

            text.insert(
                "end",
                f'- {dominant_rule}\n\n'
            )

            if additional_rules:

                text.insert(
                    "end",
                    f'{self.main.t("additional_detected_rules")}:\n',
                    "subtitle"
                )

                for r in additional_rules:

                    text.insert(
                        "end",
                        f'- {r}\n'
                    )

                text.insert(
                    "end",
                    "\n"
                )

            # =====================================
            # INTERPRETATION + IMAGE
            # =====================================

            for rule in detected_rules:

                info = rule_details(rule, self.main.current_lang)

                if not info:
                    continue

                text.insert(
                    "end",
                    f'{rule} - {info["name"]}\n',
                    "subtitle"
                )

                text.insert(
                    "end",
                    f'{self.main.t("interpretation")}:\n',
                    "subtitle"
                )

                text.insert(
                    "end",
                    f'- {info["interpretation"]}\n\n'
                )

                text.insert(
                    "end",
                    f'{self.main.t("recommendation")}:\n',
                    "subtitle"
                )

                text.insert(
                    "end",
                    f'- {info["recommendation"]}\n\n'
                )

                image_path = rule_images.get(rule)

                if image_path:

                    try:

                        img = Image.open(
                            image_path
                        )

                        img = img.resize(
                            (360, 200)
                        )

                        photo = ImageTk.PhotoImage(
                            img
                        )

                        if not hasattr(
                            text,
                            "images"
                        ):

                            text.images = []

                        text.images.append(
                            photo
                        )

                        image_label = tk.Label(
                            text.master,
                            image=photo,
                            bd=2,
                            relief="solid"
                        )

                        text.window_create(
                            "end",
                            window=image_label
                        )

                        text.insert(
                            "end",
                            "\n"
                        )

                        caption = tk.Label(
                            text.master,
                            text=f"Example {rule}",
                            font=("Segoe UI", 9, "italic"),
                            fg="gray"
                        )

                        text.window_create(
                            "end",
                            window=caption
                        )

                        text.insert(
                            "end",
                            "\n\n"
                        )

                    except Exception as e:

                        text.insert(
                            "end",
                            f"Image error: {e}\n\n"
                        )

            text.tag_configure(
                "title",
                foreground="red",
                font=("Segoe UI", 11, "bold")
            )

            text.tag_configure(
                "subtitle",
                font=("Segoe UI", 9, "bold")
            )
            text.config(
                state="disabled"
            )
