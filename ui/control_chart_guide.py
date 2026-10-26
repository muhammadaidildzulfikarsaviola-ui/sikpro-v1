"""Beginner-oriented routing to the existing control chart dialogs."""
import tkinter as tk
from tkinter import ttk

from logic.imr_chart import IMRConfigPopup
from logic.xbar_r import XbarRConfigPopup
from logic.xbar_s import XbarSConfigPopup
from logic.p_chart import PChartConfigPopup
from logic.np_chart import NPChartConfigPopup
from logic.c_chart import CChartConfigPopup
from logic.u_chart import UChartConfigPopup, UChartConvertedPopup
from logic.converter import AttributeConverterPopup
from ui.dialogs import deliver_result


# Each option describes the data shape and assumptions before opening its
# existing configuration dialog. Keys are stable route identifiers.
GUIDANCE = {
    "en": {
        "imr": ("One measurement at a time — I-MR", "Use when each row is one continuous measurement and there is no rational subgroup.", "One numeric column; one observation per row, in time order.", "Time | Temperature\n09:00 | 21.4\n09:15 | 21.6\n09:30 | 21.3", "Measurements must be comparable and ordered over time. The chart uses successive observations for moving ranges."),
        "xbar_r": ("Measurements in small subgroups — X-bar R", "Use for continuous measurements collected in small, equal-sized subgroups.", "Across columns: each row is one subgroup and columns are repeated measurements. One column: consecutive rows are grouped by the selected subgroup size. Blank size defaults to 5.", "Across columns (row = subgroup)\nBatch | M1 | M2 | M3\n1 | 10.1 | 10.4 | 10.2\n2 | 10.3 | 10.2 | 10.5\n\nOne column (subgroup size = 3)\nMeasurement\n10.1\n10.4\n10.2\n10.3\n10.2\n10.5", "Subgroup size must be 2–10 and consistent. X-bar R is commonly used for subgroup sizes up to 10."),
        "xbar_s": ("Measurements in larger subgroups — X-bar S", "Use for continuous measurements collected in equal-sized subgroups, especially when subgroup size is larger.", "Across columns: each row is one subgroup and columns are repeated measurements. One column: consecutive rows are grouped by the selected subgroup size. Blank size defaults to 5.", "Across columns (row = subgroup)\nBatch | M1 | M2 | M3 | M4\n1 | 10.1 | 10.4 | 10.2 | 10.3\n2 | 10.3 | 10.2 | 10.5 | 10.4\n\nOne column (subgroup size = 4)\nMeasurement\n10.1\n10.4\n10.2\n10.3\n10.3\n10.2\n10.5\n10.4", "Subgroup size must be 2–10 in the current application. Keep subgroup size consistent."),
        "p": ("Fraction defective — p chart", "Use to track the fraction of inspected units that are defective in each sample.", "One or more columns with individual 0/1 values, in time order; enter the fixed number of rows grouped into each sample (default 50).", "Result | Defective\n1 | 0\n2 | 1\n3 | 0\n4 | 0", "Use 1 for defective and 0 for not defective. Although p charts can support varying sample sizes, this dialog currently groups rows into equal-sized samples; total rows must divide evenly."),
        "np": ("Number defective — np chart", "Use when you need the count of defective units per sample and every sample has the same size.", "One or more columns with individual 0/1 values, in time order; enter the fixed number of rows per sample (default 50).", "Result | Defective\n1 | 0\n2 | 1\n3 | 0\n4 | 0", "Use 1 for defective and 0 for not defective. The sample size must stay constant; total rows must divide evenly."),
        "c": ("Count of defects — c chart", "Use to track the number of defects when the inspected area or opportunity is constant.", "One or more columns of non-negative defect counts; each row is one comparable inspection period or unit.", "Period | Scratches\n1 | 3\n2 | 2\n3 | 5", "The opportunity for defects must be the same for every observation. For varying opportunities, choose a U chart."),
        "u_raw": ("Defects per varying opportunity — U chart", "Use when defect counts are paired with sample sizes or opportunities that can vary.", "Two aligned columns: defect count and inspected units/opportunities; each row is one period.", "Period | Defects | Units\n1 | 4 | 100\n2 | 6 | 150\n3 | 3 | 80", "Both columns must have matching rows and positive sample sizes. Select the distribution in the configuration dialog."),
        "u_converted": ("Prepared defect-rate values — U chart", "Use when a single column already contains the converted U-rate observations.", "One numeric converted-rate column; one observation per row, in time order.", "Period | Defects per unit\n1 | 0.040\n2 | 0.040\n3 | 0.037", "This route calculates the center as the mean and limits as ±3 sample standard deviations, with the lower limit clipped at zero. It does not use the raw U distribution selector."),
    },
    "id": {
        "imr": ("Satu pengukuran setiap waktu — I-MR", "Gunakan saat setiap baris berisi satu pengukuran kontinu dan tidak ada subgrup yang wajar.", "Satu kolom numerik; satu pengamatan per baris, berurutan menurut waktu.", "Waktu | Suhu\n09:00 | 21,4\n09:15 | 21,6\n09:30 | 21,3", "Pengukuran harus sebanding dan berurutan menurut waktu. Grafik memakai rentang dari pengamatan berurutan."),
        "xbar_r": ("Pengukuran dalam subgrup kecil — X-bar R", "Gunakan untuk pengukuran kontinu yang dikumpulkan dalam subgrup berukuran sama dan kecil.", "Antarkolom: tiap baris adalah subgrup dengan pengukuran berulang di kolom. Satu kolom: baris berurutan dikelompokkan dengan ukuran subgrup terpilih. Jika kosong, ukuran = 5.", "Antarkolom (baris = subgrup)\nBatch | M1 | M2 | M3\n1 | 10,1 | 10,4 | 10,2\n2 | 10,3 | 10,2 | 10,5\n\nSatu kolom (ukuran subgrup = 3)\nPengukuran\n10,1\n10,4\n10,2\n10,3\n10,2\n10,5", "Ukuran subgrup harus 2–10 dan konsisten. X-bar R umum digunakan untuk subgrup hingga 10."),
        "xbar_s": ("Pengukuran dalam subgrup lebih besar — X-bar S", "Gunakan untuk pengukuran kontinu dalam subgrup berukuran sama, terutama saat ukuran subgrup lebih besar.", "Antarkolom: tiap baris adalah subgrup dengan pengukuran berulang di kolom. Satu kolom: baris berurutan dikelompokkan dengan ukuran subgrup terpilih. Jika kosong, ukuran = 5.", "Antarkolom (baris = subgrup)\nBatch | M1 | M2 | M3 | M4\n1 | 10,1 | 10,4 | 10,2 | 10,3\n2 | 10,3 | 10,2 | 10,5 | 10,4\n\nSatu kolom (ukuran subgrup = 4)\nPengukuran\n10,1\n10,4\n10,2\n10,3\n10,3\n10,2\n10,5\n10,4", "Ukuran subgrup pada aplikasi ini harus 2–10. Gunakan ukuran yang konsisten."),
        "p": ("Proporsi unit cacat — p", "Gunakan untuk memantau proporsi unit yang cacat pada setiap sampel.", "Satu atau beberapa kolom berisi nilai 0/1 tiap unit, berurutan menurut waktu; masukkan jumlah baris tetap per sampel (default 50).", "Unit | Cacat\n1 | 0\n2 | 1\n3 | 0\n4 | 0", "Gunakan 1 untuk cacat dan 0 untuk tidak cacat. Peta p dapat mendukung ukuran sampel yang berubah, tetapi dialog ini saat ini mengelompokkan baris dengan ukuran yang sama; total baris harus habis dibagi."),
        "np": ("Jumlah unit cacat — np", "Gunakan untuk menghitung unit cacat per sampel dengan ukuran sampel yang selalu sama.", "Satu atau beberapa kolom berisi nilai 0/1 tiap unit, berurutan menurut waktu; masukkan jumlah baris tetap per sampel (default 50).", "Unit | Cacat\n1 | 0\n2 | 1\n3 | 0\n4 | 0", "Gunakan 1 untuk cacat dan 0 untuk tidak cacat. Ukuran sampel harus tetap; total baris harus habis dibagi."),
        "c": ("Jumlah cacat — c", "Gunakan untuk memantau jumlah cacat ketika luas atau peluang pemeriksaan konstan.", "Satu atau beberapa kolom berisi jumlah cacat non-negatif; setiap baris adalah periode atau unit yang sebanding.", "Periode | Goresan\n1 | 3\n2 | 2\n3 | 5", "Peluang cacat harus sama pada setiap pengamatan. Untuk peluang yang berubah, pilih U."),
        "u_raw": ("Cacat per peluang yang berubah — U", "Gunakan saat jumlah cacat dipasangkan dengan ukuran sampel atau peluang yang dapat berubah.", "Dua kolom sejajar: jumlah cacat dan unit/peluang yang diperiksa; tiap baris adalah satu periode.", "Periode | Cacat | Unit\n1 | 4 | 100\n2 | 6 | 150\n3 | 3 | 80", "Kedua kolom harus memiliki baris yang sesuai dan ukuran sampel positif. Pilih distribusi di dialog konfigurasi."),
        "u_converted": ("Nilai laju cacat U yang sudah disiapkan", "Gunakan jika satu kolom sudah berisi pengamatan laju U hasil konversi.", "Satu kolom numerik berisi nilai laju konversi; satu pengamatan per baris, berurutan menurut waktu.", "Periode | Cacat per unit\n1 | 0,040\n2 | 0,040\n3 | 0,037", "Jalur ini menghitung garis tengah sebagai rata-rata dan batas ±3 simpangan baku sampel, dengan batas bawah minimum nol. Pemilih distribusi U mentah tidak digunakan."),
    },
}

ROUTES = {
    "imr": IMRConfigPopup,
    "xbar_r": XbarRConfigPopup,
    "xbar_s": XbarSConfigPopup,
    "p": PChartConfigPopup,
    "np": NPChartConfigPopup,
    "c": CChartConfigPopup,
    "u_raw": UChartConfigPopup,
    "u_converted": UChartConvertedPopup,
}


class ControlChartGuide(tk.Toplevel):
    """A compact chooser that explains data shape before opening a chart form."""

    def __init__(self, main, sheet):
        super().__init__(main.root)
        self.main = main
        self.sheet = sheet
        self.language = "id" if getattr(main, "current_lang", "en") == "id" else "en"
        self.entries = GUIDANCE[self.language]
        self.keys = list(self.entries)
        self.title(self._text("title"))
        self.geometry("900x600")
        self.minsize(760, 500)
        self.transient(main.root)
        self._build()

    def _text(self, key):
        return {
            "en": {"title": "Choose a control chart", "choose": "Choose the data that best matches your worksheet:", "purpose": "When to use", "layout": "Data arrangement", "example": "Example worksheet", "assumption": "Check before generating", "open": "Open chart setup", "close": "Close", "converter": "Open attribute data converter"},
            "id": {"title": "Pilih peta kendali", "choose": "Pilih jenis data yang paling sesuai dengan lembar kerja:", "purpose": "Kapan digunakan", "layout": "Susunan data", "example": "Contoh lembar kerja", "assumption": "Periksa sebelum membuat grafik", "open": "Buka pengaturan grafik", "close": "Tutup", "converter": "Buka konverter data atribut"},
        }[self.language][key]

    def _build(self):
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=self._text("choose")).pack(anchor="w", pady=(0, 10))
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        self.choices = tk.Listbox(body, width=38, exportselection=False, activestyle="dotbox")
        self.choices.pack(side="left", fill="y", padx=(0, 12))
        panel = ttk.Frame(body)
        panel.pack(side="left", fill="both", expand=True)
        self.details = tk.Text(panel, wrap="word", height=20, padx=10, pady=10)
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.details.yview)
        self.details.configure(yscrollcommand=scrollbar.set, state="disabled")
        scrollbar.pack(side="right", fill="y")
        self.details.pack(side="left", fill="both", expand=True)
        for key in self.keys:
            self.choices.insert("end", self.entries[key][0])
        self.choices.bind("<<ListboxSelect>>", self._show_selected)
        self.choices.bind("<Double-Button-1>", lambda _event: self.after_idle(self.open_selected))
        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(12, 0))
        ttk.Button(actions, text=self._text("close"), command=self.destroy).pack(side="right")
        self.open_button = ttk.Button(actions, text=self._text("open"), command=self.open_selected)
        self.open_button.pack(side="right", padx=(0, 8))
        ttk.Button(actions, text=self._text("converter"), command=self.open_converter).pack(side="left")
        self.choices.selection_set(0)
        self._show_selected()

    def _show_selected(self, _event=None):
        selection = self.choices.curselection()
        if not selection:
            return
        entry = self.entries[self.keys[selection[0]]]
        sections = (("purpose", entry[1]), ("layout", entry[2]), ("example", entry[3]), ("assumption", entry[4]))
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        for label, content in sections:
            self.details.insert("end", f"{self._text(label)}\n", "heading")
            self.details.insert("end", f"{content}\n\n")
        self.details.tag_configure("heading", font=("Segoe UI", 10, "bold"))
        self.details.configure(state="disabled")

    def open_selected(self):
        selection = self.choices.curselection()
        if not selection:
            return
        route = ROUTES[self.keys[selection[0]]]
        return deliver_result(self, lambda: route(self.main, self.sheet))

    def open_converter(self):
        return deliver_result(self, lambda: AttributeConverterPopup(self.main, self.sheet))
