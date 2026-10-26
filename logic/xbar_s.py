import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import matplotlib.pyplot as plt

from collections import Counter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.analysis import Analysis
from PIL import Image, ImageTk
from resources import resource_path
rule_info = {

    "Rule 1": {
        "name": "Point Beyond Control Limits",
        "interpretation":
        "Terdapat satu atau lebih titik data yang berada di luar batas kendali (UCL/LCL), mengindikasikan adanya special cause variation dalam proses.",
        "recommendation":
        "Lakukan investigasi terhadap kondisi proses pada titik tersebut, termasuk faktor mesin, material, metode, dan operator."
    },

    "Rule 2": {
        "name": "Shift (Process Shift)",
        "interpretation":
        "Terjadi pergeseran rata-rata proses yang ditandai dengan beberapa titik berturut-turut berada di satu sisi garis tengah.",
        "recommendation":
        "Evaluasi kemungkinan perubahan sistematis seperti penyesuaian mesin, pergantian operator, atau perubahan bahan baku."
    },

    "Rule 3": {
        "name": "Trend (Systematic Trend)",
        "interpretation":
        "Terdapat kecenderungan peningkatan atau penurunan secara bertahap yang menunjukkan adanya perubahan sistematis dalam proses.",
        "recommendation":
        "Identifikasi potensi drift pada mesin, keausan alat, atau faktor lingkungan yang berubah secara gradual."
    },

    "Rule 4": {
        "name": "Oscillation (Alternating Pattern)",
        "interpretation":
        "Pola data menunjukkan fluktuasi naik-turun secara bergantian, mengindikasikan adanya variasi yang tidak acak.",
        "recommendation":
        "Periksa kemungkinan over-adjustment (tampering) atau inkonsistensi dalam pengendalian proses."
    },

    "Rule 5": {
        "name": "Zone A Violation",
        "interpretation":
        "Beberapa titik berada pada zona A (mendekati batas kendali), menunjukkan adanya indikasi awal ketidakstabilan proses.",
        "recommendation":
        "Lakukan monitoring lebih intensif dan identifikasi faktor penyebab sebelum terjadi out of control."
    },

    "Rule 6": {
        "name": "Zone B Pattern",
        "interpretation":
        "Pola titik menunjukkan kecenderungan berada di zona B, mengindikasikan potensi bias sistematis dalam proses.",
        "recommendation":
        "Evaluasi konsistensi proses dan kondisi operasional yang mungkin menyebabkan deviasi berulang."
    },

    "Rule 7": {
        "name": "Stratification (Overcontrol)",
        "interpretation":
        "Variasi proses terlalu kecil dan seluruh titik berada dekat garis tengah, mengindikasikan kemungkinan overcontrol atau kurangnya variasi alami.",
        "recommendation":
        "Tinjau metode pengendalian proses dan pastikan tidak terjadi manipulasi data atau penyesuaian berlebihan."
    },

    "Rule 8": {
        "name": "Mixture (High Variation)",
        "interpretation":
        "Data menunjukkan penyebaran yang luas dengan pola tidak beraturan, mengindikasikan adanya variasi tinggi dari berbagai sumber.",
        "recommendation":
        "Identifikasi dan pisahkan sumber variasi yang berbeda, seperti perbedaan mesin, operator, atau batch produksi."
    }
}
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

    cleaned = []

    for x in data:

        try:
            cleaned.append(float(x))

        except:
            pass

    return cleaned


def build_vertical_subgroups(sheet, columns):

    subgroup_data = []

    min_len = min([
        len(clean_numeric(sheet.get_column_data(c)))
        for c in columns
    ])

    for row in range(min_len):

        subgroup = []

        for col in columns:

            data = clean_numeric(
                sheet.get_column_data(col)
            )

            subgroup.append(data[row])

        subgroup_data.append(subgroup)

    return subgroup_data


def build_horizontal_subgroups(data, subgroup_size):

    subgroup_data = []

    for i in range(0, len(data), subgroup_size):

        subgroup = data[i:i + subgroup_size]

        if len(subgroup) == subgroup_size:

            subgroup_data.append(subgroup)

    return subgroup_data


def calculate_xbar_s(subgroups):

    subgroup_size = len(subgroups[0])

    if subgroup_size not in A3_CONSTANTS:

        raise ValueError(
            "Subgroup size must be between 2 and 10"
        )

    xbars = [
        np.mean(g)
        for g in subgroups
    ]

    stds = [
        np.std(g, ddof=1)
        for g in subgroups
    ]

    xbar_bar = np.mean(xbars)

    s_bar = np.mean(stds)

    A3 = A3_CONSTANTS[subgroup_size]
    B3 = B3_CONSTANTS[subgroup_size]
    B4 = B4_CONSTANTS[subgroup_size]

    xbar_ucl = xbar_bar + (A3 * s_bar)
    xbar_lcl = xbar_bar - (A3 * s_bar)

    s_ucl = B4 * s_bar
    s_lcl = B3 * s_bar

    return {

        "xbars": xbars,
        "stds": stds,

        "xbar_bar": xbar_bar,
        "s_bar": s_bar,

        "xbar_ucl": xbar_ucl,
        "xbar_lcl": xbar_lcl,

        "s_ucl": s_ucl,
        "s_lcl": s_lcl,

        "subgroup_size": subgroup_size
    }


def get_rule_explanation(rule_no):

    explanations = {

        "Rule 1": (
            "Titik melewati batas kendali",
            "Kemungkinan special cause variation, setting mesin berubah, alat ukur bermasalah, atau operator error"
        ),

        "Rule 2": (
            "9 titik berturut pada satu sisi mean",
            "Menunjukkan process shift atau perubahan rata-rata proses"
        ),

        "Rule 3": (
            "Trend naik atau turun terus menerus",
            "Kemungkinan tool wear, overheating, atau drift proses"
        ),

        "Rule 5": (
            "2 dari 3 titik berada di zona A",
            "Variasi proses mulai membesar dan mendekati kondisi out of control"
        ),

        "Rule 6": (
            "4 dari 5 titik berada di zona B",
            "Proses menunjukkan pola abnormal dan ketidakstabilan"
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
            "S chart indicates instability in process variation."
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

    if "Rule 5" in all_rules:

        recommendations.append(
            "- Monitor process variability closely"
        )

    if "Rule 6" in all_rules:

        recommendations.append(
            "- Review raw material consistency and setup"
        )

    if len(recommendations) == 0:

        recommendations.append(
            "- Continue monitoring process routinely"
        )

    return "\n".join(recommendations)

class XbarSConfigPopup(tk.Toplevel):

    def __init__(self, main, sheet, analysis=None, save_to_history=True):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title("Xbar-S Chart")

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
            text="Available Columns",
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
            text="Select →",
            command=self.select_column
        ).pack(
            pady=(120, 10),
            ipadx=10,
            ipady=5
        )

        ttk.Button(
            center_panel,
            text="← Remove",
            command=self.remove_column
        ).pack(
            pady=10,
            ipadx=10,
            ipady=5
        )

        ttk.Label(
            right_panel,
            text="Selected Columns",
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
            text="Configuration",
            padding=10
        )

        config_frame.pack(
            fill="x",
            pady=(15, 0)
        )

        ttk.Label(
            config_frame,
            text="Subgroup Mode"
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
            text="Observations in one column",
            variable=self.mode_var,
            value="horizontal"
        ).pack(anchor="w")

        ttk.Radiobutton(
            config_frame,
            text="Observations across columns",
            variable=self.mode_var,
            value="vertical"
        ).pack(anchor="w")

        ttk.Label(
            config_frame,
            text="Subgroup Size"
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
            text="Leave empty for default = 5"
        ).pack(anchor="w")
        self.toggle_subgroup_entry()

        ttk.Button(
            config_frame,
            text="Generate Xbar-S",
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

    def generate(self):

        if len(self.selected_columns) == 0:

            messagebox.showerror(
                "Error",
                "Select at least one column"
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
                        "Error",
                        "Subgroup size must be integer"
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

            result = calculate_xbar_s(
                subgroups
            )

            xbar_violations = check_nelson_rules(
                result["xbars"],
                result["xbar_bar"],
                result["xbar_ucl"],
                result["xbar_lcl"]
            )

            s_violations = check_nelson_rules(
                result["stds"],
                result["s_bar"],
                result["s_ucl"],
                result["s_lcl"]
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

                result = calculate_xbar_s(
                    subgroups
                )

                xbar_violations = check_nelson_rules(
                    result["xbars"],
                    result["xbar_bar"],
                    result["xbar_ucl"],
                    result["xbar_lcl"]
                )

                s_violations = check_nelson_rules(
                    result["stds"],
                    result["s_bar"],
                    result["s_ucl"],
                    result["s_lcl"]
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
                "Error",
                "No valid subgroup generated"
            )

            return

        XbarSChartPopup(
            self.main,
            results
        )

class XbarSChartPopup(tk.Toplevel):

    def __init__(
        self,
        main,
        results,
        analysis=None, 
        save_to_history=True
    ):

        super().__init__(main.root)

        self.main = main

        self.results = results

        self.title("Xbar-S Charts")

        self.state("zoomed")

        self.create_ui()

        self.save_analysis()

    def save_analysis(self):

        for item in self.results:

            result = item["result"]

            analysis = Analysis(
                analysis_type="XBAR-S",
                title="Xbar-S Chart",
                navigator_name=f'Xbar-S of {item["column"]}',
                data={
                    "xbars": result["xbars"],
                    "stds": result["stds"]
                },
                stats={
                    "xbar_bar": result["xbar_bar"],
                    "s_bar": result["s_bar"],
                    "xbar_ucl": result["xbar_ucl"],
                    "xbar_lcl": result["xbar_lcl"],
                    "s_ucl": result["s_ucl"],
                    "s_lcl": result["s_lcl"]
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
                f'Xbar Chart - {col_name}'
            )

            ax_xbar.grid(
                True,
                alpha=0.3
            )

            ax_xbar.legend()

            ax_s.plot(
                x,
                result["stds"],
                marker="o",
                linewidth=1.8,
                color="#9467bd",
                label="S"
            )

            ax_s.axhline(
                result["s_bar"],
                linestyle="--",
                color="green",
                label=f'Mean = {round(result["s_bar"], 4)}'
            )

            ax_s.axhline(
                result["s_ucl"],
                linestyle="--",
                color="red",
                label=f'UCL = {round(result["s_ucl"], 4)}'
            )

            ax_s.axhline(
                result["s_lcl"],
                linestyle="--",
                color="red",
                label=f'LCL = {round(result["s_lcl"], 4)}'
            )

            for v in s_violations:

                idx = v["point"] - 1

                if idx >= len(result["stds"]):
                    continue

                short_rule = v["rule"].replace(
                    "Rule ",
                    ""
                )

                ax_s.scatter(
                    v["point"],
                    result["stds"][idx],
                    color="red",
                    marker="s",
                    s=120
                )

                ax_s.annotate(
                    short_rule,
                    (
                        v["point"],
                        result["stds"][idx]
                    ),
                    textcoords="offset points",
                    xytext=(0, 10),
                    rotation=90,
                    fontsize=8,
                    color="red"
                )

            ax_s.set_title(
                f'S Chart - {col_name}'
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

            chart_canvas.draw()

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

            text.insert(
                "end",
                "INTERPRETATION\n\n"
            )

            text.insert(
                "end",
                item["interpretation"]
            )

            text.insert(
                "end",
                "\n\n"
            )

            text.insert(
                "end",
                "RECOMMENDATION\n\n"
            )

            text.insert(
                "end",
                item["recommendation"]
            )

            text.insert(
                "end",
                "\n\n"
            )

            text.insert(
                "end",
                "XBAR VIOLATIONS\n\n"
            )

            if len(xbar_violations) == 0:

                text.insert(
                    "end",
                    "No violations detected\n\n"
                )

            else:

                for v in xbar_violations:

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
                        f'Possible Cause : {v["cause"]}\n\n'
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
                    "No violations detected"
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

            # =====================================
            # XBAR VIOLATIONS
            # =====================================

            text.insert(
                "end",
                "XBAR VIOLATIONS\n\n",
                "subtitle"
            )

            if len(xbar_violations) == 0:

                text.insert(
                    "end",
                    "No violations detected\n\n"
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

            # =====================================
            # S VIOLATIONS
            # =====================================

            text.insert(
                "end",
                "S VIOLATIONS\n\n",
                "subtitle"
            )

            if len(s_violations) == 0:

                text.insert(
                    "end",
                    "No violations detected\n\n"
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

            # =====================================
            # DOMINANT RULE
            # =====================================

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
                    "Additional Detected Rules:\n",
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

                info = rule_info.get(rule)

                if not info:
                    continue

                text.insert(
                    "end",
                    f'{rule} - {info["name"]}\n',
                    "subtitle"
                )

                text.insert(
                    "end",
                    "Interpretation:\n",
                    "subtitle"
                )

                text.insert(
                    "end",
                    f'- {info["interpretation"]}\n\n'
                )

                text.insert(
                    "end",
                    "Recommendation:\n",
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