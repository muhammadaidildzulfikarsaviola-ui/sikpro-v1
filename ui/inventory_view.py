"""Tk workspace for finished-goods stock and physical stocktaking."""
from pathlib import Path
import math
import tkinter as tk
from tkinter import messagebox, ttk

from core.lang import LANG
from inventory.models import InventoryValidationError
from inventory.persistence import InventoryStore
from ui.theme import ThemeManager


class InventoryApplication:
    def __init__(self, root, theme_manager=None, store=None, data_path=None):
        self.root = root
        self.theme_manager = theme_manager or ThemeManager(self)
        self.theme_manager.main = self
        self.current_lang = self.theme_manager.language
        self.lang_data = LANG[self.current_lang]
        self.store = store or InventoryStore(data_path)
        self.root.title(self.t("inv_title"))
        self.root.resizable(True, True)
        self.root.minsize(980, 680)
        self.root.state("zoomed")
        self.theme_manager.install(root)
        self.build()
        self.root.protocol("WM_DELETE_WINDOW", self.request_close)

    @property
    def book(self):
        return self.store.book

    @property
    def palette(self):
        return self.theme_manager.palette

    def t(self, key):
        return self.lang_data.get(key, key)

    def build(self):
        if hasattr(self, "outer") and self.outer.winfo_exists():
            self.outer.destroy()
        self.root.configure(bg=self.palette["window"])
        self.outer = ttk.Frame(self.root, padding=12)
        self.outer.pack(fill="both", expand=True)
        self.outer.columnconfigure(0, weight=1)
        self.outer.rowconfigure(2, weight=1)
        self._build_toolbar()
        self._build_dashboard()
        self._build_tabs()
        self.refresh_all()

    def _build_toolbar(self):
        toolbar = ttk.Frame(self.outer)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        toolbar.columnconfigure(1, weight=1)
        title = ttk.Label(toolbar, text=self.t("inv_title"), font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, sticky="w", padx=(0, 12))
        intro = ttk.Label(toolbar, text=self.t("inv_intro"), foreground=self.palette["muted"])
        intro.grid(row=0, column=1, sticky="w")
        controls = ttk.Frame(toolbar)
        controls.grid(row=0, column=2, sticky="e")
        self.language_var = tk.StringVar(value="English" if self.current_lang == "en" else "Bahasa Indonesia")
        language = ttk.Combobox(controls, textvariable=self.language_var, state="readonly", width=17,
                                values=("English", "Bahasa Indonesia"))
        language.pack(side="left", padx=(0, 6))
        language.bind("<<ComboboxSelected>>", lambda _event: self.set_language(
            "en" if self.language_var.get() == "English" else "id"))
        self.theme_var = tk.StringVar(value=self.t("inv_light" if self.theme_manager.mode == "light" else "inv_dark"))
        self.theme_box = ttk.Combobox(controls, textvariable=self.theme_var, state="readonly", width=9,
                                     values=(self.t("inv_light"), self.t("inv_dark")))
        self.theme_box.pack(side="left", padx=(0, 6))
        self.theme_box.bind("<<ComboboxSelected>>", lambda _event: self.set_theme(
            "light" if self.theme_var.get() == self.t("inv_light") else "dark"))
        ttk.Button(controls, text=self.t("inv_help"), command=self.open_help).pack(side="left")

    def _build_dashboard(self):
        panel = ttk.Frame(self.outer)
        panel.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)
        panel.columnconfigure(2, weight=2)
        self.active_value = self._summary_card(panel, 0, "inv_active_skus")
        self.low_value = self._summary_card(panel, 1, "inv_low_stock")
        recent = ttk.LabelFrame(panel, text=self.t("inv_recent_transactions"), padding=5)
        recent.grid(row=0, column=2, sticky="nsew", padx=(6, 0))
        self.recent_tree = self._tree(recent, ("date", "item", "kind", "quantity"),
                                      ("inv_date", "inv_item", "inv_type", "inv_quantity"),
                                      (140, 210, 120, 100), height=3)

    def _summary_card(self, parent, column, label_key):
        frame = ttk.LabelFrame(parent, text=self.t(label_key), padding=(12, 6))
        frame.grid(row=0, column=column, sticky="nsew", padx=(0, 6))
        value = ttk.Label(frame, text="0", font=("Segoe UI", 18, "bold"))
        value.pack(anchor="w")
        return value

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.outer)
        self.notebook.grid(row=2, column=0, sticky="nsew")
        self.items_tab = ttk.Frame(self.notebook, padding=8)
        self.transactions_tab = ttk.Frame(self.notebook, padding=8)
        self.stocktaking_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.items_tab, text=self.t("inv_items"))
        self.notebook.add(self.transactions_tab, text=self.t("inv_transactions"))
        self.notebook.add(self.stocktaking_tab, text=self.t("inv_stocktaking"))
        self._build_items_tab()
        self._build_transactions_tab()
        self._build_stocktaking_tab()

    def _build_items_tab(self):
        tab = self.items_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        filters = ttk.Frame(tab)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(filters, text=self.t("inv_search")).pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_args: self._refresh_items())
        search = ttk.Entry(filters, textvariable=self.search_var, width=28)
        search.pack(side="left", padx=(0, 12))
        ttk.Label(filters, text=self.t("inv_filter")).pack(side="left", padx=(0, 6))
        self.filter_var = tk.StringVar(value=self.t("inv_filter_all"))
        self.filter_box = ttk.Combobox(filters, textvariable=self.filter_var, state="readonly", width=16,
                                       values=(self.t("inv_filter_all"), self.t("inv_filter_low")))
        self.filter_box.pack(side="left", padx=(0, 8))
        self.filter_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh_items())
        self.inactive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filters, text=self.t("inv_show_inactive"), variable=self.inactive_var,
                        command=self._refresh_items).pack(side="left")
        self.item_tree = self._tree(tab, ("code", "name", "category", "unit", "stock", "minimum", "status"),
                                    ("inv_code", "inv_name", "inv_category", "inv_unit", "inv_stock",
                                     "inv_minimum_stock", "inv_status"),
                                    (120, 220, 140, 75, 115, 115, 95), height=12, row=1)
        self.item_tree.bind("<<TreeviewSelect>>", lambda _event: self._refresh_item_buttons())
        buttons = ttk.Frame(tab)
        buttons.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self._button(buttons, "inv_add_item", self.add_item).pack(side="left", padx=(0, 4))
        self.edit_button = self._button(buttons, "inv_edit_item", self.edit_item)
        self.edit_button.pack(side="left", padx=4)
        self.status_button = self._button(buttons, "inv_deactivate_item", self.toggle_active)
        self.status_button.pack(side="left", padx=4)
        self.delete_button = self._button(buttons, "inv_delete_item", self.delete_item)
        self.delete_button.pack(side="left", padx=4)
        self._button(buttons, "inv_stock_in", lambda: self.open_transaction("in")).pack(side="right", padx=4)
        self._button(buttons, "inv_stock_out", lambda: self.open_transaction("out")).pack(side="right", padx=4)

    def _build_transactions_tab(self):
        tab = self.transactions_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        self.transaction_tree = self._tree(
            tab, ("date", "code", "name", "kind", "quantity", "reference", "notes"),
            ("inv_date", "inv_code", "inv_name", "inv_type", "inv_quantity", "inv_reference", "inv_notes"),
            (155, 110, 190, 115, 100, 150, 220), height=16, row=0)

    def _build_stocktaking_tab(self):
        tab = self.stocktaking_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        form = ttk.LabelFrame(tab, text=self.t("inv_record_count"), padding=8)
        form.grid(row=0, column=0, sticky="ew", pady=(0, 7))
        ttk.Label(form, text=self.t("inv_item")).grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.count_item_var = tk.StringVar()
        self.count_item_box = ttk.Combobox(form, textvariable=self.count_item_var, state="readonly", width=28)
        self.count_item_box.grid(row=0, column=1, sticky="w", padx=4, pady=3)
        ttk.Label(form, text=self.t("inv_physical_count")).grid(row=0, column=2, sticky="w", padx=4, pady=3)
        self.count_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.count_var, width=14).grid(row=0, column=3, padx=4, pady=3)
        ttk.Label(form, text=self.t("inv_count_notes")).grid(row=0, column=4, sticky="w", padx=4, pady=3)
        self.count_notes_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.count_notes_var, width=30).grid(row=0, column=5, padx=4, pady=3)
        self._button(form, "inv_record_count", self.record_stocktake).grid(row=0, column=6, padx=4, pady=3)
        self.stocktake_tree = self._tree(
            tab, ("date", "code", "name", "system", "physical", "variance", "notes", "adjustment"),
            ("inv_count_date", "inv_code", "inv_name", "inv_system_stock", "inv_physical_count",
             "inv_variance", "inv_count_notes", "inv_adjustment"),
            (155, 100, 170, 110, 110, 100, 190, 220), height=12, row=1)
        self.stocktake_tree.bind("<<TreeviewSelect>>", lambda _event: self._refresh_adjustment_state())
        adjust = ttk.Frame(tab)
        adjust.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        ttk.Label(adjust, text=self.t("inv_adjustment_reason")).pack(side="left", padx=(0, 6))
        self.adjustment_reason_var = tk.StringVar()
        ttk.Entry(adjust, textvariable=self.adjustment_reason_var, width=50).pack(side="left", padx=(0, 8))
        self.adjust_button = self._button(adjust, "inv_adjust", self.adjust_stocktake)
        self.adjust_button.pack(side="left")

    def _tree(self, parent, columns, headings, widths, height=10, row=0):
        wrapper = ttk.Frame(parent)
        wrapper.grid(row=row, column=0, sticky="nsew")
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
        tree = ttk.Treeview(wrapper, columns=columns, show="headings", height=height,
                            selectmode="browse")
        scroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(0, weight=1)
        for column, key, width in zip(columns, headings, widths):
            tree.heading(column, text=self.t(key))
            tree.column(column, width=width, minwidth=55, stretch=True)
        return tree

    def _button(self, parent, key, command):
        return ttk.Button(parent, text=self.t(key), command=command)

    def _selected_item(self):
        selected = self.item_tree.selection()
        if not selected:
            return None
        try:
            return self.book.item(selected[0])
        except InventoryValidationError:
            return None

    def _refresh_items(self):
        if not hasattr(self, "item_tree"):
            return
        query = self.search_var.get().strip().casefold()
        low_only = self.filter_var.get() == self.t("inv_filter_low")
        self.item_tree.delete(*self.item_tree.get_children())
        for item in self.book.items:
            if not item.active and not self.inactive_var.get():
                continue
            balance = self.book.balance(item.id)
            if low_only and (not item.active or balance > item.minimum_stock):
                continue
            if query and query not in " ".join((item.code, item.name, item.category)).casefold():
                continue
            self.item_tree.insert("", "end", iid=item.id, values=(
                item.code, item.name, item.category or "—", item.unit, _number(balance),
                _number(item.minimum_stock), self.t("inv_active" if item.active else "inv_inactive")))
        self._refresh_item_buttons()
        if not self.item_tree.get_children():
            self.item_tree.insert("", "end", iid="__empty__",
                                  values=(self.t("inv_no_items"), "", "", "", "", "", ""), tags=("empty",))

    def _refresh_item_buttons(self):
        item = self._selected_item()
        state = "normal" if item else "disabled"
        self.edit_button.configure(state=state)
        self.status_button.configure(state=state)
        self.delete_button.configure(state=state)
        if item:
            self.status_button.configure(text=self.t("inv_deactivate_item" if item.active else "inv_activate_item"))

    def _refresh_adjustment_state(self):
        selection = self.stocktake_tree.selection()
        enabled = False
        if selection:
            stocktake_id = selection[0]
            enabled = not any(row.stocktake_id == stocktake_id for row in self.book.adjustments)
        self.adjust_button.configure(state="normal" if enabled else "disabled")

    def refresh_all(self):
        if not hasattr(self, "item_tree"):
            return
        active = [item for item in self.book.items if item.active]
        low = [item for item in active if self.book.balance(item.id) <= item.minimum_stock]
        self.active_value.configure(text=str(len(active)))
        self.low_value.configure(text=str(len(low)))
        item_by_id = {item.id: item for item in self.book.items}
        transactions = sorted(self.book.transactions, key=lambda row: row.occurred_at, reverse=True)
        self._fill_tree(self.recent_tree, transactions[:4], lambda tx: (
            tx.occurred_at, f"{item_by_id[tx.item_id].code} — {item_by_id[tx.item_id].name}",
            self.t("inv_transaction_in" if tx.kind == "in" else "inv_transaction_out"), _number(tx.quantity)))
        self._fill_tree(self.transaction_tree, transactions, lambda tx: (
            tx.occurred_at, item_by_id[tx.item_id].code, item_by_id[tx.item_id].name,
            self.t("inv_transaction_in" if tx.kind == "in" else "inv_transaction_out"),
            _number(tx.quantity), tx.reference or "—", tx.notes or "—"))
        self._refresh_items()
        self._refresh_count_item_options()
        self._refresh_stocktakes()

    def _fill_tree(self, tree, rows, values):
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", "end", iid=row.id, values=values(row))
        if not rows and tree is self.recent_tree:
            tree.insert("", "end", iid="__empty_recent__", values=(self.t("inv_no_transactions"), "", "", ""))

    def _refresh_count_item_options(self):
        self._count_choices = {}
        for item in self.book.items:
            if item.active:
                label = f"{item.code} — {item.name}"
                self._count_choices[label] = item.id
        values = tuple(self._count_choices)
        current = self.count_item_var.get()
        self.count_item_box.configure(values=values)
        if current not in self._count_choices:
            self.count_item_var.set(values[0] if values else "")

    def _refresh_stocktakes(self):
        items = {item.id: item for item in self.book.items}
        adjustments = {row.stocktake_id: row for row in self.book.adjustments}
        self.stocktake_tree.delete(*self.stocktake_tree.get_children())
        for row in sorted(self.book.stocktakes, key=lambda entry: entry.occurred_at, reverse=True):
            item = items[row.item_id]
            adjustment = adjustments.get(row.id)
            audit = (f"{self.t('inv_adjusted')}: {adjustment.reason}" if adjustment
                     else self.t("inv_not_adjusted"))
            self.stocktake_tree.insert("", "end", iid=row.id, values=(
                row.occurred_at, item.code, item.name, _number(row.system_stock),
                _number(row.physical_count), _number(row.variance), row.notes or "—", audit))
        if not self.book.stocktakes:
            self.stocktake_tree.insert("", "end", iid="__empty_stocktake__",
                                       values=(self.t("inv_no_stocktakes"), "", "", "", "", "", "", ""))
        self._refresh_adjustment_state()

    def _mutate(self, operation):
        self._mutation_failed = False
        try:
            result = self.store.perform(operation)
        except InventoryValidationError as exc:
            self._mutation_failed = True
            messagebox.showerror(self.t("inv_title"), self.t(f"inv_err_{exc.code}"), parent=self.root)
            return None
        except (OSError, ValueError, TypeError) as exc:
            self._mutation_failed = True
            messagebox.showerror(self.t("inv_title"), self.t("inv_err_save_failed"), parent=self.root)
            return None
        self.refresh_all()
        return result

    def add_item(self):
        self._item_dialog()

    def edit_item(self):
        item = self._selected_item()
        if item is None:
            return
        self._item_dialog(item)

    def _item_dialog(self, item=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("inv_edit_title" if item else "inv_add_title"))
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        form = ttk.Frame(dialog, padding=14)
        form.pack(fill="both", expand=True)
        keys = [("inv_code", item.code if item else ""),
                ("inv_name", item.name if item else ""),
                ("inv_category", item.category if item else ""),
                ("inv_unit", item.unit if item else "pcs"),
                ("inv_minimum_stock", _number(item.minimum_stock) if item else "0")]
        if item is None:
            keys.append(("inv_opening_stock", "0"))
        variables = {}
        for row_index, (key, value) in enumerate(keys):
            ttk.Label(form, text=self.t(key)).grid(row=row_index, column=0, sticky="w", padx=(0, 10), pady=4)
            variable = tk.StringVar(value=value)
            variables[key] = variable
            ttk.Entry(form, textvariable=variable, width=32).grid(row=row_index, column=1, sticky="ew", pady=4)
        buttons = ttk.Frame(form)
        buttons.grid(row=len(keys), column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text=self.t("inv_cancel"), command=dialog.destroy).pack(side="right", padx=(6, 0))

        def save():
            try:
                minimum = _parse_number(variables["inv_minimum_stock"].get())
            except ValueError:
                messagebox.showerror(self.t("inv_title"), self.t("inv_err_minimum_stock_invalid"), parent=dialog)
                return
            if item:
                self._mutate(lambda book: book.update_item(
                        item.id, variables["inv_code"].get(), variables["inv_name"].get(),
                    variables["inv_category"].get(), variables["inv_unit"].get(), minimum))
            else:
                try:
                    opening = _parse_number(variables["inv_opening_stock"].get())
                except ValueError:
                    messagebox.showerror(self.t("inv_title"), self.t("inv_err_opening_stock_invalid"), parent=dialog)
                    return
                self._mutate(lambda book: book.create_item(
                        variables["inv_code"].get(), variables["inv_name"].get(),
                        variables["inv_category"].get(), variables["inv_unit"].get(), opening, minimum))
            if self._last_mutation_failed():
                return
            dialog.destroy()

        ttk.Button(buttons, text=self.t("inv_save"), command=save).pack(side="right")
        self._center_dialog(dialog, 490, 380)
        dialog.bind("<Return>", lambda _event: save())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())

    def _last_mutation_failed(self):
        # _mutate sets this transient flag so validation or write failures keep
        # a dialog open for correction without committing partial state.
        return getattr(self, "_mutation_failed", False)

    def toggle_active(self):
        item = self._selected_item()
        if item:
            self._mutate(lambda book: book.set_active(item.id, not item.active))

    def delete_item(self):
        item = self._selected_item()
        if not item:
            return
        if not messagebox.askyesno(self.t("inv_delete_item"), self.t("inv_confirm_delete"), parent=self.root):
            return
        self._mutate(lambda book: book.delete_item(item.id))

    def open_transaction(self, kind):
        item = self._selected_item()
        if item is None:
            messagebox.showinfo(self.t("inv_title"), self.t("inv_select_item"), parent=self.root)
            return
        if not item.active:
            messagebox.showerror(self.t("inv_title"), self.t("inv_err_item_inactive"), parent=self.root)
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("inv_transaction_title"))
        dialog.transient(self.root)
        dialog.grab_set()
        form = ttk.Frame(dialog, padding=14)
        form.pack(fill="both", expand=True)
        ttk.Label(form, text=self.t("inv_item")).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Label(form, text=f"{item.code} — {item.name}").grid(row=0, column=1, sticky="w", pady=4)
        ttk.Label(form, text=self.t("inv_type")).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Label(form, text=self.t("inv_transaction_in" if kind == "in" else "inv_transaction_out")).grid(
            row=1, column=1, sticky="w", pady=4)
        quantity_var, reference_var, notes_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for index, (key, variable) in enumerate((("inv_quantity", quantity_var),
                                                  ("inv_reference", reference_var),
                                                  ("inv_notes", notes_var)), 2):
            ttk.Label(form, text=self.t(key)).grid(row=index, column=0, sticky="w", padx=(0, 10), pady=4)
            ttk.Entry(form, textvariable=variable, width=34).grid(row=index, column=1, sticky="ew", pady=4)
        buttons = ttk.Frame(form)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text=self.t("inv_cancel"), command=dialog.destroy).pack(side="right", padx=(6, 0))

        def save():
            try:
                quantity = _parse_number(quantity_var.get())
            except ValueError:
                messagebox.showerror(self.t("inv_title"), self.t("inv_err_transaction_quantity_invalid"), parent=dialog)
                return
            result = self._mutate(lambda book: book.transact(
                item.id, kind, quantity, reference_var.get(), notes_var.get()))
            if result is not None:
                dialog.destroy()

        ttk.Button(buttons, text=self.t("inv_save"), command=save).pack(side="right")
        self._center_dialog(dialog, 470, 350)
        dialog.bind("<Return>", lambda _event: save())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())

    def record_stocktake(self):
        label = self.count_item_var.get()
        item_id = self._count_choices.get(label)
        if not item_id:
            messagebox.showinfo(self.t("inv_title"), self.t("inv_select_item"), parent=self.root)
            return
        try:
            count = _parse_number(self.count_var.get())
        except ValueError:
            messagebox.showerror(self.t("inv_title"), self.t("inv_err_physical_count_invalid"), parent=self.root)
            return
        result = self._mutate(lambda book: book.stocktake(item_id, count, self.count_notes_var.get()))
        if result is not None:
            self.count_var.set("")
            self.count_notes_var.set("")

    def adjust_stocktake(self):
        selection = self.stocktake_tree.selection()
        if not selection:
            messagebox.showinfo(self.t("inv_title"), self.t("inv_select_stocktake"), parent=self.root)
            return
        stocktake_id = selection[0]
        reason = self.adjustment_reason_var.get()
        result = self._mutate(lambda book: book.adjust_to_stocktake(stocktake_id, reason))
        if result is not None:
            self.adjustment_reason_var.set("")

    def open_help(self):
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("inv_help_title"))
        dialog.transient(self.root)
        dialog.configure(bg=self.palette["window"])
        content = ttk.Frame(dialog, padding=14)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text=self.t("inv_help_title"), font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        text = tk.Text(content, width=86, height=19, wrap="word", relief="flat", padx=10, pady=10)
        text.pack(fill="both", expand=True)
        text.insert("1.0", self.t("inv_help_text"))
        text.configure(state="disabled")
        ttk.Button(content, text=self.t("inv_close"), command=dialog.destroy).pack(anchor="e", pady=(8, 0))
        self._center_dialog(dialog, 760, 540)

    def set_language(self, language):
        if language not in LANG:
            raise ValueError(f"Unknown language: {language}")
        self.current_lang = language
        self.lang_data = LANG[language]
        self.theme_manager.set_language(language)
        self.root.title(self.t("inv_title"))
        self.build()

    def set_theme(self, mode):
        self.theme_manager.set_theme(mode)
        self.root.configure(bg=self.palette["window"])
        self.theme_var.set(self.t("inv_light" if mode == "light" else "inv_dark"))

    def request_close(self):
        self.root.destroy()

    def _center_dialog(self, dialog, width, height):
        dialog.update_idletasks()
        parent_x, parent_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        parent_w, parent_h = self.root.winfo_width(), self.root.winfo_height()
        screen_w, screen_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x = min(max(0, parent_x + (parent_w - width) // 2), max(0, screen_w - width))
        y = min(max(0, parent_y + (parent_h - height) // 2), max(0, screen_h - height))
        dialog.geometry(f"{width}x{height}+{x}+{y}")


def _parse_number(value):
    normalized = value.strip().replace(",", ".")
    if not normalized:
        raise ValueError("number required")
    number = float(normalized)
    if not math.isfinite(number):
        raise ValueError("number must be finite")
    return number


def _number(value):
    return f"{value:g}"
