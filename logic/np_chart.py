import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import matplotlib.pyplot as plt

from collections import Counter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.analysis import Analysis
from PIL import Image, ImageTk
from resources import resource_path

def clean_numeric(data):

    cleaned = []

    for x in data:

        try:
            cleaned.append(float(x))

        except:
            pass

    return cleaned


def build_horizontal_groups(data, subgroup_size):

    groups = []

    for i in range(0, len(data), subgroup_size):

        subgroup = data[i:i + subgroup_size]

        if len(subgroup) == subgroup_size:

            groups.append(subgroup)

    return groups


def calculate_np_chart(defect_groups):

    subgroup_size = len(defect_groups[0])

    defect_counts = [

        sum(g)

        for g in defect_groups
    ]

    total_defects = sum(defect_counts)

    total_samples = subgroup_size * len(defect_groups)

    p_bar = total_defects / total_samples

    np_bar = subgroup_size * p_bar

    sigma = np.sqrt(
        subgroup_size *
        p_bar *
        (1 - p_bar)
    )

    ucl = np_bar + (3 * sigma)

    lcl = np_bar - (3 * sigma)

    if lcl < 0:
        lcl = 0

    return {

        "defect_counts": defect_counts,

        "np_bar": np_bar,

        "ucl": ucl,
        "lcl": lcl,

        "subgroup_size": subgroup_size,

        "p_bar": p_bar
    }


def get_rule_explanation(rule_no):

    explanations = {

        "Rule 1": (
            "Titik melewati batas kendali",
            "Kemungkinan special cause variation"
        ),

        "Rule 2": (
            "9 titik berturut pada satu sisi mean",
            "Kemungkinan process shift"
        ),

        "Rule 3": (
            "Trend naik atau turun",
            "Kemungkinan drift proses"
        ),

        "Rule 5": (
            "2 dari 3 titik di zona A",
            "Variasi proses mulai membesar"
        ),

        "Rule 6": (
            "4 dari 5 titik di zona B",
            "Pola abnormal proses"
        )
    }

    return explanations.get(
        rule_no,
        ("Unknown", "No explanation")
    )


def check_nelson_rules(data, mean, ucl, lcl):

    violations = []

    sigma = (ucl - mean) / 3

    zone_a = 2 * sigma
    zone_b = sigma

    for i, val in enumerate(data):

        if val > ucl or val < lcl:

            desc, cause = get_rule_explanation("Rule 1")

            violations.append({

                "rule": "Rule 1",
                "point": i + 1,
                "description": desc,
                "cause": cause
            })

    count = 0
    side = None

    for i, val in enumerate(data):

        current = val > mean

        if current == side:

            count += 1

        else:

            count = 1
            side = current

        if count >= 9:

            desc, cause = get_rule_explanation("Rule 2")

            violations.append({

                "rule": "Rule 2",
                "point": i + 1,
                "description": desc,
                "cause": cause
            })

    up = 0
    down = 0

    for i in range(1, len(data)):

        if data[i] > data[i - 1]:

            up += 1
            down = 0

        elif data[i] < data[i - 1]:

            down += 1
            up = 0

        if up >= 5:

            desc, cause = get_rule_explanation("Rule 3")

            violations.append({

                "rule": "Rule 3",
                "point": i + 1,
                "description": desc,
                "cause": cause
            })

        if down >= 5:

            desc, cause = get_rule_explanation("Rule 3")

            violations.append({

                "rule": "Rule 3",
                "point": i + 1,
                "description": desc,
                "cause": cause
            })

    for i in range(len(data) - 2):

        subset = data[i:i + 3]

        count = sum(
            abs(x - mean) > zone_a
            for x in subset
        )

        if count >= 2:

            desc, cause = get_rule_explanation("Rule 5")

            violations.append({

                "rule": "Rule 5",
                "point": i + 3,
                "description": desc,
                "cause": cause
            })

    for i in range(len(data) - 4):

        subset = data[i:i + 5]

        count = sum(
            abs(x - mean) > zone_b
            for x in subset
        )

        if count >= 4:

            desc, cause = get_rule_explanation("Rule 6")

            violations.append({

                "rule": "Rule 6",
                "point": i + 5,
                "description": desc,
                "cause": cause
            })

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


class NPChartConfigPopup(tk.Toplevel):

    def __init__(self, main, sheet, analysis=None, save_to_history=True):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title("NP Chart")

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

            data = clean_numeric(
                self.sheet.get_column_data(i)
            )

            if len(data) == 0:
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
            text="Generate NP Chart",
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

    def generate(self):

        if len(self.selected_columns) == 0:

            messagebox.showerror(
                "Error",
                "Select at least one column"
            )

            return

        try:

            subgroup_size = int(
                self.subgroup_var.get()
            )

        except:

            messagebox.showerror(
                "Error",
                "Invalid subgroup size"
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

            result = calculate_np_chart(
                groups
            )

            violations = check_nelson_rules(
                result["defect_counts"],
                result["np_bar"],
                result["ucl"],
                result["lcl"]
            )

            results.append({

                "column": col_name,
                "result": result,
                "violations": violations
            })

        if len(results) == 0:

            messagebox.showerror(
                "Error",
                "No valid subgroup"
            )

            return

        NPChartPopup(
            self.main,
            results
        )


class NPChartPopup(tk.Toplevel):

    def __init__(
        self,
        main,
        results
    ):

        super().__init__(main.root)

        self.main = main

        self.results = results

        self.title("NP Charts")

        self.state("zoomed")

        self.create_ui()

        self.save_analysis()

    def save_analysis(self):

        for item in self.results:

            result = item["result"]

            analysis = Analysis(
                analysis_type="NP-CHART",
                title="NP Chart",
                navigator_name=f'NP Chart of {item["column"]}',
                data={
                    "defect_counts": result["defect_counts"]
                },
                stats={
                    "np_bar": result["np_bar"],
                    "ucl": result["ucl"],
                    "lcl": result["lcl"]
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
                len(result["defect_counts"]) + 1
            ))

            ax.plot(
                x,
                result["defect_counts"],
                marker="o",
                linewidth=1.8,
                label="NP"
            )

            ax.axhline(
                result["np_bar"],
                linestyle="--",
                color="green",
                label=f'NPbar = {round(result["np_bar"], 4)}'
            )

            ax.axhline(
                result["ucl"],
                linestyle="--",
                color="red",
                label=f'UCL = {round(result["ucl"], 4)}'
            )

            ax.axhline(
                result["lcl"],
                linestyle="--",
                color="red",
                label=f'LCL = {round(result["lcl"], 4)}'
            )

            for v in violations:

                idx = v["point"] - 1

                if idx >= len(result["defect_counts"]):
                    continue

                short_rule = v["rule"].replace(
                    "Rule ",
                    ""
                )

                ax.scatter(
                    v["point"],
                    result["defect_counts"][idx],
                    color="red",
                    marker="s",
                    s=120
                )

                ax.annotate(
                    short_rule,
                    (
                        v["point"],
                        result["defect_counts"][idx]
                    ),
                    textcoords="offset points",
                    xytext=(0, 10),
                    rotation=90,
                    fontsize=8,
                    color="red"
                )

            ax.set_title(
                f'NP Chart - {item["column"]}'
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

            canvas.draw()

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
                f'NPbar : {round(result["np_bar"], 5)}\n\n'
            )

            text.insert(
                "end",
                f'UCL : {round(result["ucl"], 5)}\n'
            )

            text.insert(
                "end",
                f'LCL : {round(result["lcl"], 5)}\n\n'
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