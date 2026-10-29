"""Desktop workspace for EOQ, reorder point, and single-item MRP planning."""
import tkinter as tk
from tkinter import ttk

from core.lang import LANG
from inventory.calculators import calculate_eoq, calculate_mrp, calculate_rop
from ui.theme import ThemeManager


class InventoryApplication:
    def __init__(self, root, theme_manager=None):
        self.root = root
        self.theme_manager = theme_manager or ThemeManager(self)
        self.theme_manager.main = self
        self.current_lang = self.theme_manager.language
        self.lang_data = LANG[self.current_lang]
        self.root.title(self.t("inv_title"))
        self.root.resizable(True, True)
        self.root.minsize(920, 640)
        self.root.state("zoomed")
        self.theme_manager.install(root)
        self.build()

    @property
    def palette(self):
        return self.theme_manager.palette

    def t(self, key):
        return self.lang_data.get(key, key)

    def set_on_back(self, callback):
        self.on_back = callback
        if hasattr(self, "back_button") and self.back_button.winfo_exists():
            self.back_button.configure(command=lambda: self.on_back() if self.on_back else None)

    def build(self):
        self.root.title(self.t("inv_title"))
        if hasattr(self, "outer") and self.outer.winfo_exists():
            self.outer.destroy()
        self.outer = ttk.Frame(self.root, padding=14)
        self.outer.pack(fill="both", expand=True)
        self.outer.columnconfigure(0, weight=1)
        self.outer.rowconfigure(1, weight=1)
        bar = ttk.Frame(self.outer)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        bar.columnconfigure(1, weight=1)
        ttk.Label(bar, text=self.t("inv_title"), font=("Segoe UI", 17, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 12))
        ttk.Label(bar, text=self.t("inv_intro"), foreground=self.palette["muted"]).grid(row=0, column=1, sticky="w")
        self.back_button = ttk.Button(bar, text=self.t("back_to_apps"), command=lambda: self.on_back() if getattr(self, "on_back", None) else None)
        self.back_button.grid(row=0, column=2, padx=4)
        self.language_var = tk.StringVar(value="English" if self.current_lang == "en" else "Bahasa Indonesia")
        lang = ttk.Combobox(bar, textvariable=self.language_var, state="readonly", width=17, values=("English", "Bahasa Indonesia"))
        lang.grid(row=0, column=3, padx=(4, 6))
        lang.bind("<<ComboboxSelected>>", lambda _e: self.set_language("en" if self.language_var.get() == "English" else "id"))
        self.theme_var = tk.StringVar(value=self.theme_manager.mode)
        self.theme_box = ttk.Combobox(bar, textvariable=self.theme_var, state="readonly", width=10,
                                      values=(self.t("light"), self.t("dark")))
        self.theme_box.grid(row=0, column=4, padx=4)
        self.theme_var.set(self.t(self.theme_manager.mode))
        self.theme_box.bind("<<ComboboxSelected>>", self._theme_selection_changed)
        self.tabs = ttk.Notebook(self.outer)
        self.tabs.grid(row=1, column=0, sticky="nsew")
        self._build_eoq()
        self._build_rop()
        self._build_mrp()

    def _tab(self, key):
        frame = ttk.Frame(self.tabs, padding=14)
        frame.columnconfigure(0, weight=1)
        self.tabs.add(frame, text=self.t(key))
        return frame

    def _form(self, parent, entries, *, row=0):
        box = ttk.LabelFrame(parent, text=self.t("inv_inputs"), padding=12)
        box.grid(row=row, column=0, sticky="new")
        variables = {}
        for row, (key, default) in enumerate(entries):
            ttk.Label(box, text=self.t(key)).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
            var = tk.StringVar(value=str(default))
            variables[key] = var
            if key == "inv_lot_method":
                widget = ttk.Combobox(box, textvariable=var, width=21, state="readonly", values=("LFL", "FOQ", "POQ"))
            else:
                widget = ttk.Entry(box, textvariable=var, width=24)
            widget.grid(row=row, column=1, sticky="w", pady=5)
            variables[key + "__widget"] = widget
            variables[key + "__label"] = box.grid_slaves(row=row, column=0)[0]
            err = ttk.Label(box, text="", foreground=self.palette["danger"])
            err.grid(row=row, column=2, sticky="w", padx=8)
            variables[key + "__error"] = err
        return variables

    def _actions(self, parent, calculate, reset, *, row=1):
        bar = ttk.Frame(parent)
        bar.grid(row=row, column=0, sticky="w", pady=(8, 8))
        ttk.Button(bar, text=self.t("inv_calculate"), command=calculate).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text=self.t("inv_reset"), command=reset).pack(side="left")

    def _result(self, parent, *, row=2):
        out = ttk.LabelFrame(parent, text=self.t("inv_results"), padding=12)
        out.grid(row=row, column=0, sticky="nsew")
        parent.rowconfigure(row, weight=1)
        label = ttk.Label(out, text=self.t("inv_result_prompt"), justify="left", anchor="nw", wraplength=1000)
        label.pack(fill="both", expand=True, anchor="nw")
        return label

    def _build_eoq(self):
        tab = self._tab("inv_eoq")
        self.eoq_mode = tk.StringVar(value=getattr(self, "_eoq_mode", "unit"))
        selector = ttk.Combobox(tab, state="readonly", values=(self.t("inv_eoq_unit_mode"), self.t("inv_eoq_cost_mode")), width=30)
        selector.current(0 if self.eoq_mode.get() == "unit" else 1)
        selector.grid(row=0, column=0, sticky="w", pady=(0, 8))
        selector.bind("<<ComboboxSelected>>", lambda _e: self._show_eoq_mode())
        self.eoq_vars = self._form(tab, (("inv_annual_demand", ""), ("inv_ordering_cost", ""), ("inv_holding_cost", ""), ("inv_operating_days", "365"), ("inv_unit_price", "")), row=1)
        self.eoq_mode_selector = selector
        self._show_eoq_mode()
        self.eoq_result = self._result(tab, row=3)
        self._actions(tab, self.calculate_eoq, lambda: self._reset(self.eoq_vars, {"inv_operating_days": "365"}, self.eoq_result), row=2)

    def _show_eoq_mode(self):
        # Shared required inputs stay visible; only the mode-specific field changes.
        self.eoq_mode.set("unit" if self.eoq_mode_selector.current() == 0 else "cost")
        unit_mode = self.eoq_mode.get() == "unit"
        for key in ("inv_operating_days", "inv_unit_price"):
            visible = (key == "inv_operating_days") == unit_mode
            for suffix in ("__label", "__widget", "__error"):
                widget = self.eoq_vars[key + suffix]
                widget.grid() if visible else widget.grid_remove()

    def _build_rop(self):
        tab = self._tab("inv_rop")
        self.rop_vars = self._form(tab, (("inv_average_demand", ""), ("inv_lead_time", ""), ("inv_safety_stock", "0")))
        self.rop_result = self._result(tab)
        self._actions(tab, self.calculate_rop, lambda: self._reset(self.rop_vars, {"inv_safety_stock": "0"}, self.rop_result))

    def _build_mrp(self):
        tab = self._tab("inv_mrp")
        entries = (("inv_periods", ""), ("inv_gross_requirements", ""), ("inv_initial_on_hand", "0"), ("inv_scheduled_receipts", ""), ("inv_lead_time", "0"), ("inv_lot_method", "LFL"), ("inv_fixed_quantity", ""), ("inv_poq_interval", ""))
        self.mrp_vars = self._form(tab, entries, row=0)
        note = ttk.Label(tab, text=self.t("inv_mrp_format"), foreground=self.palette["muted"], wraplength=1000)
        note.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.mrp_help = note
        self.mrp_output = ttk.Frame(tab)
        self.mrp_output.grid(row=3, column=0, sticky="nsew")
        columns = ("period", "gross", "scheduled", "available", "net", "receipts", "releases")
        self.mrp_tree = ttk.Treeview(self.mrp_output, columns=columns, show="headings", height=8)
        heading_keys = ("inv_period", "inv_gross", "inv_scheduled", "inv_available", "inv_net", "inv_receipts", "inv_releases")
        for column, key in zip(columns, heading_keys):
            self.mrp_tree.heading(column, text=self.t(key))
            self.mrp_tree.column(column, width=130, minwidth=85, anchor="e", stretch=True)
        scroll = ttk.Scrollbar(self.mrp_output, orient="horizontal", command=self.mrp_tree.xview)
        self.mrp_tree.configure(xscrollcommand=scroll.set)
        self.mrp_tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=1, column=0, sticky="ew")
        self.mrp_output.columnconfigure(0, weight=1)
        self.mrp_output.rowconfigure(0, weight=1)
        self.mrp_warning = ttk.Label(self.mrp_output, text="", foreground=self.palette["danger"], wraplength=1000)
        self.mrp_warning.grid(row=2, column=0, sticky="w", pady=(5, 0))
        self.mrp_assumption = ttk.Label(self.mrp_output, text="", foreground=self.palette["muted"], wraplength=1000)
        self.mrp_assumption.grid(row=3, column=0, sticky="w", pady=(5, 0))
        tab.rowconfigure(3, weight=1)
        self._actions(tab, self.calculate_mrp, self._reset_mrp, row=1)

    def _reset_mrp(self):
        self._reset(self.mrp_vars, {"inv_initial_on_hand": "0", "inv_lead_time": "0", "inv_lot_method": "LFL"}, self.mrp_warning)
        self.mrp_tree.delete(*self.mrp_tree.get_children())
        self.mrp_warning.configure(text="")
        self.mrp_assumption.configure(text="")

    def _reset(self, variables, defaults, output):
        for key, var in variables.items():
            if key.endswith("__error"):
                var.configure(text="")
            elif isinstance(var, tk.StringVar):
                var.set(defaults.get(key, ""))
        output.configure(text=self.t("inv_result_prompt"))

    def _values(self, variables):
        values = {}
        for key, var in variables.items():
            if key.endswith("__error"):
                var.configure(text="")
            elif isinstance(var, tk.StringVar):
                values[key] = var.get().strip()
        return values

    @staticmethod
    def _fmt(value):
        return f"{value:,.4g}"

    def _error(self, variables, message):
        field = message.split(" ")[0]
        reverse = {"annual_demand": "inv_annual_demand", "ordering_cost": "inv_ordering_cost", "holding_cost": "inv_holding_cost", "operating_days": "inv_operating_days", "average_demand": "inv_average_demand", "lead_time": "inv_lead_time", "safety_stock": "inv_safety_stock", "periods": "inv_periods", "gross_requirements[0]": "inv_gross_requirements", "scheduled_receipts[0]": "inv_scheduled_receipts", "initial_on_hand": "inv_initial_on_hand", "fixed_order_quantity": "inv_fixed_quantity", "poq_interval": "inv_poq_interval"}
        key = reverse.get(field)
        if field.startswith("gross_requirements["):
            key = "inv_gross_requirements"
        elif field.startswith("scheduled_receipts["):
            key = "inv_scheduled_receipts"
        label = variables.get(key + "__error") if key else None
        if label:
            label.configure(text=message)
        else:
            next(v for k, v in variables.items() if k.endswith("__error")).configure(text=message)

    def calculate_eoq(self):
        v = self._values(self.eoq_vars)
        try:
            unit_mode = self.eoq_mode_selector.current() == 0
            days = v["inv_operating_days"] if unit_mode else 365
            price = v["inv_unit_price"] or None if not unit_mode else None
            r = calculate_eoq(v["inv_annual_demand"], v["inv_ordering_cost"], v["inv_holding_cost"], days, price)
            rows = [f"EOQ: {self._fmt(r['eoq'])} units/order", f"Annual ordering cost: {self._fmt(r['annual_ordering_cost'])}", f"Annual holding cost: {self._fmt(r['annual_holding_cost'])}", f"Relevant annual inventory cost: {self._fmt(r['relevant_annual_cost'])}"]
            if unit_mode:
                rows[1:1] = [f"Orders per year: {self._fmt(r['orders_per_year'])}", f"Order interval: {self._fmt(r['order_interval_days'])} operating days", f"Average cycle stock: {self._fmt(r['eoq'] / 2)} units"]
            elif price is not None:
                rows.extend((f"Annual purchase cost: {self._fmt(r['annual_purchase_cost'])}", f"Total annual cost including purchases: {self._fmt(r['total_annual_cost'])}"))
            rows.extend(("EOQ = sqrt((2 × D × S) / H)", self.t("inv_eoq_assumption"), self.t("inv_eoq_purchase_note")))
            self.eoq_result.configure(text="\n".join(rows))
        except ValueError as exc:
            self._error(self.eoq_vars, str(exc))

    def calculate_rop(self):
        v = self._values(self.rop_vars)
        try:
            r = calculate_rop(v["inv_average_demand"], v["inv_lead_time"], v["inv_safety_stock"])
            self.rop_result.configure(text=f"{self.t('inv_rop_value')}: {self._fmt(r['rop'])}\n{self.t('inv_lead_demand')}: {self._fmt(r['lead_time_demand'])}\n{self.t('inv_safety_stock_used')}: {self._fmt(r['safety_stock'])}\n\n{self.t('inv_rop_interpretation')}\n{self.t('inv_rop_assumption')}")
        except ValueError as exc:
            self._error(self.rop_vars, str(exc))

    def calculate_mrp(self):
        v = self._values(self.mrp_vars)
        try:
            periods = int(v["inv_periods"])
            if periods <= 0:
                raise ValueError("periods must be positive")
            def series(value, name):
                chunks = [item.strip() for item in value.split(",")]
                if len(chunks) != periods:
                    raise ValueError(f"{name} must contain exactly {periods} comma-separated values")
                return [float(item) for item in chunks]
            gross = series(v["inv_gross_requirements"], "gross_requirements")
            scheduled = series(v["inv_scheduled_receipts"], "scheduled_receipts") if v["inv_scheduled_receipts"] else [0] * periods
            result = calculate_mrp(gross, v["inv_initial_on_hand"], scheduled, v["inv_lead_time"], v["inv_lot_method"], v["inv_fixed_quantity"] or None, v["inv_poq_interval"] or None)
            self.mrp_tree.delete(*self.mrp_tree.get_children())
            for row in result.rows:
                self.mrp_tree.insert("", "end", values=(row.period, self._fmt(row.gross_requirements), self._fmt(row.scheduled_receipts), self._fmt(row.projected_available), self._fmt(row.net_requirements), self._fmt(row.planned_order_receipts), self._fmt(row.planned_order_releases)))
            if result.releases_before_horizon:
                self.mrp_warning.configure(text=self.t("inv_mrp_release_warning") + ": " + ", ".join(f"P{p}: {self._fmt(q)}" for p, q in result.releases_before_horizon))
            else:
                self.mrp_warning.configure(text="")
            self.mrp_assumption.configure(text=self.t("inv_mrp_assumption"))
        except (ValueError, TypeError) as exc:
            self._error(self.mrp_vars, str(exc))

    def set_theme(self, mode):
        if mode not in ("light", "dark"):
            raise ValueError(f"Unknown theme: {mode}")
        self.theme_manager.set_theme(mode)
        self.build()

    def _theme_selection_changed(self, *_args):
        selection = self.theme_box.current()
        mode = {0: "light", 1: "dark"}.get(selection)
        if mode is None:
            return
        if mode != self.theme_manager.mode:
            self.set_theme(mode)

    def set_language(self, language):
        if hasattr(self, "eoq_mode_selector"):
            self._eoq_mode = "unit" if self.eoq_mode_selector.current() == 0 else "cost"
        self.current_lang = language
        self.lang_data = LANG[language]
        self.theme_manager.set_language(language)
        self.build()


def _number(value):
    return f"{value:,.4g}"
