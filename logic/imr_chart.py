import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


from models.analysis import Analysis
from core.lang import LANG
from PIL import Image, ImageTk

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
    "Rule 1": "rules/rules1.png",
    "Rule 2": "rules/rules2.png",
    "Rule 3": "rules/rules3.png",
    "Rule 4": "rules/rules4.png",
    "Rule 5": "rules/rules5.png",
    "Rule 6": "rules/rules6.png",
    "Rule 7": "rules/rules7.png",
    "Rule 8": "rules/rules8.png",
}
def clean_numeric(data):

    cleaned = []

    for x in data:

        try:
            cleaned.append(float(x))
        except:
            pass

    return cleaned


def moving_range(data):

    mr = []

    for i in range(1, len(data)):

        mr.append(
            abs(data[i] - data[i - 1])
        )

    return mr


def control_limits(data):

    mean = np.mean(data)

    mr = moving_range(data)

    mr_bar = np.mean(mr)

    sigma = mr_bar / 1.128

    ucl = mean + (3 * sigma)
    lcl = mean - (3 * sigma)

    return mean, ucl, lcl, sigma


def check_nelson_rules(
    data,
    mean,
    ucl,
    lcl
):

    violations = []

    sigma = (ucl - mean) / 3

    zone_a = 2 * sigma
    zone_b = sigma

    for i, val in enumerate(data):

        if val > ucl or val < lcl:

            violations.append(
                (
                    "Rule 1",
                    i + 1,
                    "Point beyond control limit"
                )
            )

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

            violations.append(
                (
                    "Rule 2",
                    i + 1,
                    "Shift detected"
                )
            )

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

            violations.append(
                (
                    "Rule 3",
                    i + 1,
                    "Upward trend"
                )
            )

        if down >= 5:

            violations.append(
                (
                    "Rule 3",
                    i + 1,
                    "Downward trend"
                )
            )

    zigzag = 0

    for i in range(2, len(data)):

        if (
            data[i] > data[i - 1] < data[i - 2]
        ) or (
            data[i] < data[i - 1] > data[i - 2]
        ):

            zigzag += 1

        else:

            zigzag = 0

        if zigzag >= 13:

            violations.append(
                (
                    "Rule 4",
                    i + 1,
                    "Oscillation"
                )
            )

    for i in range(len(data) - 2):

        subset = data[i:i + 3]

        count = sum(
            abs(x - mean) > zone_a
            for x in subset
        )

        if count >= 2:

            violations.append(
                (
                    "Rule 5",
                    i + 3,
                    "Zone A violation"
                )
            )

    for i in range(len(data) - 4):

        subset = data[i:i + 5]

        count = sum(
            abs(x - mean) > zone_b
            for x in subset
        )

        if count >= 4:

            violations.append(
                (
                    "Rule 6",
                    i + 5,
                    "Zone B pattern"
                )
            )

    for i in range(len(data) - 14):

        subset = data[i:i + 15]

        if all(
            abs(x - mean) < zone_b
            for x in subset
        ):

            violations.append(
                (
                    "Rule 7",
                    i + 15,
                    "Stratification"
                )
            )

    for i in range(len(data) - 7):

        subset = data[i:i + 8]

        if all(
            abs(x - mean) > zone_b
            for x in subset
        ):

            violations.append(
                (
                    "Rule 8",
                    i + 8,
                    "Mixture"
                )
            )

    return violations


def show_imr(
    main,
    data,
    col_name,
    violations=None,
    ax=None
):

    if not data:

        fig, ax = plt.subplots(
            figsize=(10, 5)
        )

        ax.text(
            0.5,
            0.5,
            main.t("empty_data"),
            ha="center",
            va="center"
        )

        return {
            "fig": fig
        }

    mean, ucl, lcl, sigma = control_limits(data)

    x = list(range(1, len(data) + 1))

    if ax is None:

        fig, ax = plt.subplots(
            figsize=(12, 6)
        )

    else:

        fig = ax.figure

    out_x = []
    out_y = []

    for i, val in enumerate(data):

        if val > ucl or val < lcl:

            out_x.append(i + 1)
            out_y.append(val)

    z1_upper = mean + sigma
    z1_lower = mean - sigma

    z2_upper = mean + (2 * sigma)
    z2_lower = mean - (2 * sigma)

    ax.axhspan(
        z2_upper,
        ucl,
        color="#d46b6b",
        alpha=0.3
    )

    ax.axhspan(
        lcl,
        z2_lower,
        color="#d46b6b",
        alpha=0.3
    )

    ax.axhspan(
        z1_upper,
        z2_upper,
        color="#d8b447",
        alpha=0.3
    )

    ax.axhspan(
        z2_lower,
        z1_lower,
        color="#d8b447",
        alpha=0.3
    )

    ax.axhspan(
        z1_lower,
        z1_upper,
        color="#94df94",
        alpha=0.3
    )

    ax.plot(
        x,
        data,
        marker="o",
        linewidth=1.8
    )

    if out_x:

        ax.scatter(
            out_x,
            out_y,
            color="black",
            s=150,
            label=main.t("out_of_control")
        )

    if violations:

        v_x = []
        v_y = []

        for v in violations:

            idx = v[1] - 1

            if 0 <= idx < len(data):

                v_x.append(idx + 1)
                v_y.append(data[idx])

        ax.scatter(
            v_x,
            v_y,
            color="purple",
            s=170,
            edgecolors="white",
            linewidths=1.5,
            label=main.t("nelson_violation")
        )

    ax.axhline(
        mean,
        linestyle="--",
        color="green",
        label=main.t("mean")
    )

    ax.axhline(
        ucl,
        linestyle="--",
        color="red",
        label=main.t("ucl")
    )

    ax.axhline(
        lcl,
        linestyle="--",
        color="red",
        label=main.t("lcl")
    )

    ax.set_title(
        f"{main.t('imr_chart')} - {col_name}"
    )

    ax.set_xlabel(
        main.t("sample")
    )

    ax.set_ylabel(
        col_name
    )

    ax.grid(
        True,
        alpha=0.2
    )

    ax.legend()

    return {
        "fig": fig,
        "mean": mean,
        "ucl": ucl,
        "lcl": lcl,
        "sigma": sigma
    }


class IMRConfigPopup(tk.Toplevel):

    def __init__(self, main, sheet):

        super().__init__(main.root)

        self.main = main
        self.sheet = sheet

        self.title(
            self.main.t("imr_chart")
        )

        self.geometry("700x450")

        self.center_window(
            700,
            450
        )

        self.create_ui()

    def center_window(
        self,
        width,
        height
    ):

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = int(
            (screen_width / 2) - (width / 2)
        )

        y = int(
            (screen_height / 2) - (height / 2)
        )

        self.geometry(
            f"{width}x{height}+{x}+{y}"
        )

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
            text=self.main.t("variables")
        ).pack(
            anchor="w",
            pady=(0, 5)
        )

        self.column_var = tk.StringVar()

        ttk.Entry(
            left_frame,
            textvariable=self.column_var
        ).pack(fill="x")

        ttk.Button(
            left_frame,
            text=self.main.t("select"),
            command=self.select_column
        ).pack(
            anchor="w",
            pady=(5, 20)
        )

        ttk.Button(
            left_frame,
            text=self.main.t("generate_imr_chart"),
            command=self.generate
        ).pack(
            pady=(20, 0)
        )

        ttk.Label(
            right_frame,
            text=self.main.t(
                "available_columns"
            ),
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.column_listbox = tk.Listbox(
            right_frame,
            width=28,
            height=18
        )

        self.column_listbox.pack(
            fill="y",
            pady=(5, 0)
        )

        self.load_columns()

    def load_columns(self):

        columns = self.sheet.get_column_names()

        self.numeric_columns = {}

        for i, col in enumerate(columns):

            data = self.sheet.get_column_data(i)

            cleaned = clean_numeric(data)

            if len(cleaned) == 0:
                continue

            self.numeric_columns[col] = i

            self.column_listbox.insert(
                "end",
                col
            )

    def select_column(self):

        selected = (
            self.column_listbox.curselection()
        )

        if not selected:

            messagebox.showerror(
                self.main.t("error"),
                self.main.t(
                    "please_select_column"
                )
            )

            return

        column_name = (
            self.column_listbox.get(
                selected[0]
            )
        )

        self.column_var.set(
            column_name
        )

    def generate(self):

        column = (
            self.column_var.get().strip()
        )

        if column == "":

            messagebox.showerror(
                self.main.t("error"),
                self.main.t(
                    "please_select_column"
                )
            )

            return

        idx = self.numeric_columns[column]

        raw_data = (
            self.sheet.get_column_data(idx)
        )

        data = clean_numeric(raw_data)

        mean, ucl, lcl, sigma = (
            control_limits(data)
        )

        violations = check_nelson_rules(
            data,
            mean,
            ucl,
            lcl
        )

        IMRChartPopup(
            self.main,
            self,
            data,
            column,
            violations
        )


class IMRChartPopup(tk.Toplevel):
    
    def __init__(
        self,
        main,
        config_popup,
        data,
        column_name,
        violations,
        analysis=None, 
        save_to_history=True
    ):

        super().__init__(main.root)

        self.main = main

        self.config_popup = config_popup

        self.data = data
        self.column_name = column_name
        self.violations = violations

        self.title(
            f"{self.main.t('imr_chart')} - {column_name}"
        )

        self.state("zoomed")

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_all
        )

        self.save_to_history = save_to_history

        self.create_chart()

        if self.save_to_history:
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

    def save_analysis(self):

        mean, ucl, lcl, sigma = (
            control_limits(self.data)
        )

        analysis = Analysis(
            analysis_type="I-MR",
            title=self.main.t("imr_chart"),
            navigator_name=f"{self.main.t('imr_chart')} of {self.column_name}",
            data={
                "values": self.data,
                "violations": self.violations
            },
            stats={
                "mean": mean,
                "ucl": ucl,
                "lcl": lcl
            },
            settings={
                "column": self.column_name
            }
        )

        self.main.navigator.add_analysis(
            analysis
        )

    def create_chart(self):
        
        from matplotlib.lines import Line2D
        from matplotlib.patches import Patch

        container = ttk.PanedWindow(
            self,
            orient="horizontal"
        )

        container.pack(
            fill="both",
            expand=True
        )

        # =====================================
        # LEFT PANEL
        # =====================================

        left_outer = ttk.Frame(container)

        container.add(
            left_outer,
            weight=5
        )

        canvas_container = tk.Canvas(
            left_outer,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            left_outer,
            orient="vertical",
            command=canvas_container.yview
        )

        canvas_container.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        canvas_container.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollable_frame = ttk.Frame(
            canvas_container
        )

        canvas_window = canvas_container.create_window(
            (0, 0),
            window=scrollable_frame,
            anchor="nw"
        )

        def update_scrollregion(event=None):

            canvas_container.configure(
                scrollregion=canvas_container.bbox("all")
            )

        scrollable_frame.bind(
            "<Configure>",
            update_scrollregion
        )

        def resize_frame(event):

            canvas_container.itemconfig(
                canvas_window,
                width=event.width
            )

        canvas_container.bind(
            "<Configure>",
            resize_frame
        )

        # =====================================
        # RIGHT PANEL
        # =====================================

        right_panel = ttk.Frame(
            container,
            padding=10
        )

        container.add(
            right_panel,
            weight=1
        )

        # =====================================
        # DATA
        # =====================================

        mean, ucl, lcl, sigma = (
            control_limits(self.data)
        )

        mr_data = moving_range(
            self.data
        )

        mr_bar = np.mean(mr_data)

        mr_ucl = mr_bar * 3.267
        mr_lcl = 0

        x_i = list(
            range(1, len(self.data) + 1)
        )

        x_mr = list(
            range(2, len(self.data) + 1)
        )

        # =====================================
        # FIGURE
        # =====================================

        fig, axes = plt.subplots(
            3,
            1,
            figsize=(10, 14),
            constrained_layout=True
        )

        ax_i = axes[0]
        ax_mr = axes[1]
        ax_imr = axes[2]

        # =====================================
        # ZONES
        # =====================================

        z1_upper = mean + sigma
        z1_lower = mean - sigma

        z2_upper = mean + (2 * sigma)
        z2_lower = mean - (2 * sigma)

        def add_zones(ax):

            ax.axhspan(
                z2_upper,
                ucl,
                color="#ffb3b3",
                alpha=0.5
            )

            ax.axhspan(
                lcl,
                z2_lower,
                color="#ffb3b3",
                alpha=0.5
            )

            ax.axhspan(
                z1_upper,
                z2_upper,
                color="#ffe599",
                alpha=0.5
            )

            ax.axhspan(
                z2_lower,
                z1_lower,
                color="#ffe599",
                alpha=0.5
            )

            ax.axhspan(
                z1_lower,
                z1_upper,
                color="#b6d7a8",
                alpha=0.5
            )

        violation_points = {}

        for v in self.violations:

            rule = v[0]
            point = v[1]

            if point not in violation_points:

                violation_points[point] = []

            violation_points[point].append(rule)

        legend_elements = [

            Line2D(
                [0],
                [0],
                color="blue",
                lw=2,
                label=self.main.t("data")
            ),

            Line2D(
                [0],
                [0],
                color="red",
                lw=2,
                linestyle="--",
                label="UCL/LCL"
            ),

            Line2D(
                [0],
                [0],
                color="green",
                lw=2,
                linestyle="--",
                label=self.main.t("mean")
            ),

            Line2D(
                [0],
                [0],
                marker="s",
                color="w",
                markerfacecolor="red",
                markersize=8,
                label=self.main.t(
                    "violation"
                )
            ),

            Patch(
                facecolor="#ffb3b3",
                label=self.main.t(
                    "zone_a"
                )
            ),

            Patch(
                facecolor="#ffe599",
                label=self.main.t(
                    "zone_b"
                )
            ),

            Patch(
                facecolor="#b6d7a8",
                label=self.main.t(
                    "zone_c"
                )
            )
        ]

        add_zones(ax_i)

        ax_i.plot(
            x_i,
            self.data,
            marker="o",
            linewidth=1.8,
            color="blue"
        )

        for point, rules in violation_points.items():

            idx = point - 1

            if idx >= len(self.data):
                continue

            short_rules = ",".join([
                r.replace("Rule ", "")
                for r in rules
            ])

            ax_i.scatter(
                point,
                self.data[idx],
                marker="s",
                color="red",
                s=130
            )

            ax_i.annotate(
                short_rules,
                (
                    point,
                    self.data[idx]
                ),
                textcoords="offset points",
                xytext=(0, 10),
                rotation=90,
                fontsize=8,
                color="red"
            )

        ax_i.axhline(
            mean,
            linestyle="--",
            color="green"
        )

        ax_i.axhline(
            ucl,
            linestyle="--",
            color="red"
        )

        ax_i.axhline(
            lcl,
            linestyle="--",
            color="red"
        )

        ax_i.text(
            len(self.data),
            ucl,
            f'UCL = {ucl:.2f}',
            color="red",
            fontsize=8,
            ha="right"
        )

        ax_i.text(
            len(self.data),
            mean,
            f'Mean = {mean:.2f}',
            color="green",
            fontsize=8,
            ha="right"
        )

        ax_i.text(
            len(self.data),
            lcl,
            f'LCL = {lcl:.2f}',
            color="red",
            fontsize=8,
            ha="right"
        )

        ax_i.legend(
            handles=legend_elements,
            loc="upper left"
        )

        ax_i.set_title(
            f'{self.main.t("individual_chart")} - {self.column_name}'
        )

        ax_i.grid(
            True,
            alpha=0.2
        )

        # =====================================
        # MR CHART
        # =====================================

        mr_violations = []

        ax_mr.plot(
            x_mr,
            mr_data,
            marker="o",
            linewidth=1.8,
            color="#9467bd"
        )

        for i, val in enumerate(mr_data):

            if val > mr_ucl:

                point = i + 2

                mr_violations.append(
                    (
                        "MR Rule",
                        point,
                        "Moving range beyond control limit"
                    )
                )

                ax_mr.scatter(
                    point,
                    val,
                    marker="s",
                    color="red",
                    s=130
                )

                ax_mr.annotate(
                    "MR",
                    (
                        point,
                        val
                    ),
                    textcoords="offset points",
                    xytext=(0, 10),
                    rotation=90,
                    fontsize=8,
                    color="red"
                )

        ax_mr.axhline(
            mr_bar,
            linestyle="--",
            color="green"
        )

        ax_mr.axhline(
            mr_ucl,
            linestyle="--",
            color="red"
        )

        ax_mr.axhline(
            mr_lcl,
            linestyle="--",
            color="red"
        )

        ax_mr.text(
            len(mr_data),
            mr_ucl,
            f'UCL = {mr_ucl:.2f}',
            color="red",
            fontsize=8,
            ha="right"
        )

        ax_mr.text(
            len(mr_data),
            mr_bar,
            f'MR̄ = {mr_bar:.2f}',
            color="green",
            fontsize=8,
            ha="right"
        )

        ax_mr.legend(
            handles=legend_elements,
            loc="upper left"
        )

        ax_mr.set_title(
            f'{self.main.t("moving_range_chart")} - {self.column_name}'
        )

        ax_mr.grid(
            True,
            alpha=0.2
        )

        # =====================================
        # IMR CHART
        # =====================================

        add_zones(ax_imr)

        ax_imr.plot(
            x_i,
            self.data,
            marker="o",
            linewidth=1.8,
            color="#ff7f0e"
        )

        for point, rules in violation_points.items():

            idx = point - 1

            if idx >= len(self.data):
                continue

            short_rules = ",".join([
                r.replace("Rule ", "")
                for r in rules
            ])

            ax_imr.scatter(
                point,
                self.data[idx],
                marker="s",
                color="red",
                s=130
            )

            ax_imr.annotate(
                short_rules,
                (
                    point,
                    self.data[idx]
                ),
                textcoords="offset points",
                xytext=(0, 10),
                rotation=90,
                fontsize=8,
                color="red"
            )

        ax_imr.axhline(
            mean,
            linestyle="--",
            color="green"
        )

        ax_imr.axhline(
            ucl,
            linestyle="--",
            color="red"
        )

        ax_imr.axhline(
            lcl,
            linestyle="--",
            color="red"
        )

        ax_imr.text(
            len(self.data),
            ucl,
            f'UCL = {ucl:.2f}',
            color="red",
            fontsize=8,
            ha="right"
        )

        ax_imr.text(
            len(self.data),
            mean,
            f'Mean = {mean:.2f}',
            color="green",
            fontsize=8,
            ha="right"
        )

        ax_imr.text(
            len(self.data),
            lcl,
            f'LCL = {lcl:.2f}',
            color="red",
            fontsize=8,
            ha="right"
        )

        ax_imr.legend(
            handles=legend_elements,
            loc="upper left"
        )

        ax_imr.set_title(
            f'{self.main.t("imr_chart")} - {self.column_name}'
        )

        ax_imr.grid(
            True,
            alpha=0.2
        )

        # =====================================
        # CANVAS
        # =====================================

        chart_canvas = FigureCanvasTkAgg(
            fig,
            master=scrollable_frame
        )

        chart_canvas.draw()

        chart_canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        # =====================================
        # RIGHT PANEL
        # =====================================

        ttk.Label(
            right_panel,
            text=self.main.t(
                "detected_violations"
            ),
            font=("Segoe UI", 11, "bold")
        ).pack(
            anchor="w",
            pady=(0, 10)
        )

        notebook = ttk.Notebook(
            right_panel
        )

        notebook.pack(
            fill="both",
            expand=True
        )

        tabs = {

            "IMR": ttk.Frame(notebook),
            "I": ttk.Frame(notebook),
            "MR": ttk.Frame(notebook)

        }

        for name, frame in tabs.items():

            notebook.add(
                frame,
                text=name
            )

        def create_scroll_text(parent):

            frame = ttk.Frame(parent)

            frame.pack(
                fill="both",
                expand=True
            )

            text = tk.Text(
                frame,
                wrap="word"
            )

            scrollbar = ttk.Scrollbar(
                frame,
                orient="vertical",
                command=text.yview
            )

            text.configure(
                yscrollcommand=scrollbar.set
            )

            scrollbar.pack(
                side="right",
                fill="y"
            )

            text.pack(
                side="left",
                fill="both",
                expand=True
            )

            return text

        text_imr = create_scroll_text(
            tabs["IMR"]
        )

        text_i = create_scroll_text(
            tabs["I"]
        )

        text_mr = create_scroll_text(
            tabs["MR"]
        )

        def insert_violation(
            widget,
            chart_name,
            violations
        ):

            widget.config(
                state="normal"
            )

            widget.delete(
                "1.0",
                "end"
            )

            if not violations:

                widget.insert(
                    "end",
                    self.main.t(
                        "no_violations_detected"
                    )
                )

                widget.config(
                    state="disabled"
                )

                return

            detected_rules = []

            counter = {}

            for v in violations:

                rule = v[0]

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

            widget.insert(
                "end",
                f'{chart_name}\n\n',
                "title"
            )

            for v in violations:

                rule = v[0]
                point = v[1]
                desc = v[2]

                widget.insert(
                    "end",
                    f'{rule}\n'
                )

                widget.insert(
                    "end",
                    f'{self.main.t("point")}: {point}\n'
                )

                widget.insert(
                    "end",
                    f'{self.main.t("description")}: {desc}\n\n'
                )

            widget.insert(
                "end",
                "Dominant Rule:\n",
                "subtitle"
            )

            widget.insert(
                "end",
                f'- {dominant_rule}\n\n'
            )

            if additional_rules:

                widget.insert(
                    "end",
                    "Additional Detected Rules:\n",
                    "subtitle"
                )

                for r in additional_rules:

                    widget.insert(
                        "end",
                        f'- {r}\n'
                    )

                widget.insert(
                    "end",
                    "\n"
                )

            for rule in detected_rules:

                info = rule_info.get(rule)

                if not info:
                    continue

                widget.insert(
                    "end",
                    f'{rule} - {info["name"]}\n',
                    "subtitle"
                )

                widget.insert(
                    "end",
                    f'{self.main.t("interpretation")}:\n',
                    "subtitle"
                )

                widget.insert(
                    "end",
                    f'- {info["interpretation"]}\n\n'
                )

                widget.insert(
                    "end",
                    f'{self.main.t("recommendation")}:\n',
                    "subtitle"
                )

                widget.insert(
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
                            (420, 240)
                        )

                        photo = ImageTk.PhotoImage(
                            img
                        )

                        if not hasattr(
                            widget,
                            "images"
                        ):

                            widget.images = []

                        widget.images.append(
                            photo
                        )

                        image_label = tk.Label(
                            widget.master,
                            image=photo,
                            bd=2,
                            relief="solid"
                        )

                        widget.window_create(
                            "end",
                            window=image_label
                        )

                        widget.insert(
                            "end",
                            "\n"
                        )

                        example_label = tk.Label(
                            widget.master,
                            text=f"Example {rule}",
                            font=("Segoe UI", 9, "italic"),
                            fg="gray"
                        )

                        widget.window_create(
                            "end",
                            window=example_label
                        )

                        widget.insert(
                            "end",
                            "\n\n"
                        )

                    except Exception as e:

                        widget.insert(
                            "end",
                            f"Image error: {e}\n\n"
                        )

            widget.tag_configure(
                "title",
                foreground="red",
                font=("Segoe UI", 11, "bold")
            )

            widget.tag_configure(
                "subtitle",
                font=("Segoe UI", 9, "bold")
            )

            widget.config(
                state="disabled"
            )

        insert_violation(
            text_imr,
            "IMR",
            self.violations
        )

        insert_violation(
            text_i,
            "I",
            self.violations
        )

        insert_violation(
            text_mr,
            "MR",
            mr_violations
        )