"""Application selection screen for SIKPRO's available desktop modules."""
import tkinter as tk
from tkinter import messagebox, ttk

from core.lang import LANG
from ui.theme import ThemeManager


class ApplicationLauncher:
    WINDOW_WIDTH = 960
    WINDOW_HEIGHT = 640

    def __init__(self, root, open_spc, settings_path=None, open_layout=None):
        self.root = root
        self.open_spc_callback = open_spc
        self.open_layout_callback = open_layout
        self.theme_manager = ThemeManager(self, settings_path=settings_path)
        self.current_lang = self.theme_manager.language
        self.lang_data = LANG[self.current_lang]
        self._opening_spc = False
        self._opening_layout = False
        self.root.title("SIKPRO")
        self.root.state("normal")
        self.root.resizable(False, False)
        self._center_window()
        self.theme_manager.install(root)
        self.build()

    def _center_window(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width - self.WINDOW_WIDTH) // 2)
        y = max(0, (screen_height - self.WINDOW_HEIGHT) // 2)
        self.root.geometry(
            f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}"
        )

    def t(self, key):
        return self.lang_data.get(key, key)

    def set_theme(self, mode):
        self.theme_manager.set_theme(mode)
        self.build()

    def set_language(self, language):
        self.current_lang = language
        self.lang_data = LANG[language]
        self.theme_manager.set_language(language)
        self.build()

    def build(self):
        palette = self.theme_manager.palette
        if hasattr(self, "frame"):
            self.frame.destroy()
        self.root.configure(background=palette["window"])
        self.frame = tk.Frame(self.root, background=palette["window"])
        self.frame.pack(fill="both", expand=True, padx=28, pady=16)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)

        controls = tk.Frame(self.frame, background=palette["window"])
        controls.grid(row=0, column=0, sticky="e", pady=(0, 10))
        tk.Label(controls, text=self.t("language"), background=palette["window"],
                 foreground=palette["text"]).pack(side="left", padx=(0, 6))
        language_var = tk.StringVar(value="English" if self.current_lang == "en" else "Bahasa Indonesia")
        language_box = ttk.Combobox(controls, state="readonly", width=18,
                                    textvariable=language_var,
                                    values=("English", "Bahasa Indonesia"))
        language_box.pack(side="left", padx=(0, 14))
        language_box.bind("<<ComboboxSelected>>", lambda _event: self.set_language(
            "en" if language_var.get() == "English" else "id"))
        tk.Label(controls, text=self.t("theme"), background=palette["window"],
                 foreground=palette["text"]).pack(side="left", padx=(0, 6))
        theme_var = tk.StringVar(value=self.t(self.theme_manager.mode))
        theme_box = ttk.Combobox(controls, state="readonly", width=11,
                                 textvariable=theme_var,
                                 values=(self.t("light"), self.t("dark")))
        theme_box.pack(side="left")
        theme_box.bind("<<ComboboxSelected>>", lambda _event: self.set_theme(
            "light" if theme_var.get() == self.t("light") else "dark"))

        heading = tk.Frame(self.frame, background=palette["window"])
        heading.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        tk.Label(heading, text="SIKPRO", background=palette["window"],
                 foreground=palette["accent"], font=("Segoe UI", 20, "bold")).pack(anchor="center")
        tk.Label(heading, text=self.t("launcher_title"), background=palette["window"],
                 foreground=palette["text"], font=("Segoe UI", 14, "bold")).pack(anchor="center", pady=(3, 1))
        tk.Label(heading, text=self.t("launcher_intro"), background=palette["window"],
                 foreground=palette["muted"], font=("Segoe UI", 10), wraplength=760,
                 justify="center").pack(anchor="center")

        cards = tk.Frame(self.frame, background=palette["window"])
        cards.grid(row=2, column=0, sticky="nsew")
        self.cards = cards
        self.card_description_labels = []
        self.cards_by_key = {}
        for index in range(3):
            cards.columnconfigure(index, weight=1, uniform="app_cards")
        for index in range(3):
            cards.rowconfigure(index, weight=1, uniform="app_card_rows")

        applications = (
            ("spc", "launcher_app_spc", "launcher_spc_description", "launcher_available", "launcher_open_spc", "chart", True),
            ("layout", "launcher_app_layout", "launcher_layout_description",
             "launcher_available" if self.open_layout_callback else "launcher_in_development",
             "launcher_open_layout" if self.open_layout_callback else "launcher_coming_soon",
             "layout", bool(self.open_layout_callback)),
            ("inventory", "launcher_app_inventory", "launcher_inventory_description", "launcher_planned", "launcher_unavailable", "inventory", False),
            ("forecasting", "launcher_app_forecasting", "launcher_forecasting_description", "launcher_planned", "launcher_unavailable", "forecasting", False),
            ("mrp", "launcher_app_mrp", "launcher_mrp_description", "launcher_planned", "launcher_unavailable", "mrp", False),
            ("work_measurement", "launcher_app_work_measurement", "launcher_work_measurement_description", "launcher_planned", "launcher_unavailable", "work_measurement", False),
            ("optimization", "launcher_app_optimization", "launcher_optimization_description", "launcher_planned", "launcher_unavailable", "optimization", False),
        )
        for index, (key, title_key, description_key, status_key, action_key, icon, enabled) in enumerate(applications):
            row, column = divmod(index, 3)
            self.cards_by_key[key] = self._card(
                cards, row, column, key, title_key, description_key,
                status_key, action_key, icon, palette, enabled,
            )
        self.spc_card = self.cards_by_key["spc"]["frame"]
        self.layout_card = self.cards_by_key["layout"]["frame"]
        self.spc_button = self.cards_by_key["spc"]["button"]
        self.layout_button = self.cards_by_key["layout"]["button"]
        cards.bind("<Configure>", self._resize_card_text)

    def _resize_card_text(self, event):
        width = max(145, (event.width - 48) // 3 - 34)
        for label in self.card_description_labels:
            label.configure(wraplength=width)

    def _card(self, parent, row, column, key, title_key, description_key,
              status_key, action_key, icon_kind, palette, enabled):
        card = tk.Frame(parent, background=palette["surface"], highlightthickness=1,
                        highlightbackground=palette["border"], padx=12, pady=9)
        card.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        heading = tk.Frame(card, background=palette["surface"])
        heading.grid(row=0, column=0, sticky="ew")
        icon = tk.Canvas(heading, width=26, height=26, background=palette["surface"],
                         highlightthickness=0)
        icon.pack(side="left", padx=(0, 7))
        self._draw_application_icon(icon, icon_kind, palette["accent"])
        tk.Label(heading, text=self.t(title_key), background=palette["surface"],
                 foreground=palette["text"], font=("Segoe UI", 11, "bold"),
                 anchor="w").pack(side="left", fill="x", expand=True)
        status = tk.Label(heading, text=self.t(status_key), background=palette["surface"],
                          foreground=palette["success"] if enabled else palette["muted"],
                          font=("Segoe UI", 8, "bold"), anchor="e")
        status.pack(side="right", padx=(4, 0))

        description = tk.Label(card, text=self.t(description_key), background=palette["surface"],
                               foreground=palette["text_soft"], font=("Segoe UI", 9), justify="left",
                               anchor="nw", wraplength=235)
        description.grid(row=1, column=0, sticky="new", pady=(5, 5))
        self.card_description_labels.append(description)
        if enabled:
            command = self.open_spc if key == "spc" else self.open_layout
            button = ttk.Button(card, text=self.t(action_key), command=command)
        else:
            button = ttk.Button(card, text=self.t(action_key), state="disabled")
        button.grid(row=2, column=0, sticky="ew")
        self._style_card_button(button, palette, enabled)
        return {"frame": card, "title": heading.winfo_children()[-2],
                "description": description, "status": status, "button": button}

    def _style_card_button(self, button, palette, enabled):
        # Theme colors are defined once per semantic state and applied equally
        # to cards recreated after language or theme changes.
        try:
            style = ttk.Style(self.root)
            style.configure("LauncherActive.TButton", foreground=palette["text"], padding=(6, 3))
            style.configure("LauncherDisabled.TButton", foreground=palette["disabled"], padding=(6, 3))
            button.configure(style="LauncherActive.TButton" if enabled else "LauncherDisabled.TButton")
        except tk.TclError:
            pass

    @staticmethod
    def _draw_application_icon(canvas, kind, color):
        line = lambda *points: canvas.create_line(*points, fill=color, width=1.8,
                                                   capstyle=tk.ROUND, joinstyle=tk.ROUND)
        rect = lambda *box: canvas.create_rectangle(*box, outline=color, width=1.6)
        oval = lambda *box: canvas.create_oval(*box, outline=color, width=1.6)
        if kind in ("chart", "forecasting"):
            line(4, 4, 4, 22, 23, 22)
            points = (5, 17, 10, 12, 14, 15, 21, 7) if kind == "chart" else (5, 18, 10, 16, 15, 12, 21, 6)
            line(*points)
            if kind == "forecasting":
                line(17, 6, 21, 6, 21, 10)
        elif kind == "layout":
            rect(3, 4, 11, 11); rect(15, 4, 23, 11); rect(3, 15, 11, 22); rect(15, 15, 23, 22)
            line(11, 7, 15, 7); line(7, 11, 7, 15); line(19, 11, 19, 15)
        elif kind == "inventory":
            rect(3, 6, 23, 22); line(3, 11, 23, 11); line(9, 6, 9, 11); line(17, 6, 17, 11)
            line(9, 15, 17, 15)
        elif kind == "mrp":
            for x, y in ((6, 7), (20, 7), (13, 20)):
                oval(x - 3, y - 3, x + 3, y + 3)
            line(9, 8, 17, 8); line(8, 10, 12, 17); line(18, 10, 14, 17)
        elif kind == "work_measurement":
            oval(3, 5, 23, 25); line(13, 3, 13, 6); line(9, 3, 17, 3); line(13, 11, 13, 16, 17, 18)
        elif kind == "optimization":
            oval(3, 3, 23, 23); oval(8, 8, 18, 18); oval(11, 11, 15, 15)

    def open_spc(self):
        if self._opening_spc:
            return
        self._opening_spc = True
        self.spc_button.configure(state="disabled")
        try:
            self.open_spc_callback(self.theme_manager)
        except Exception as exc:
            self._opening_spc = False
            self.spc_button.configure(state="normal")
            messagebox.showerror(self.t("error"), str(exc), parent=self.root)
            return
        self.frame.destroy()

    def open_layout(self):
        if self._opening_layout or not self.open_layout_callback:
            return
        self._opening_layout = True
        self.layout_button.configure(state="disabled")
        try:
            self.open_layout_callback(self.theme_manager)
        except Exception as exc:
            self._opening_layout = False
            self.layout_button.configure(state="normal")
            messagebox.showerror(self.t("error"), str(exc), parent=self.root)
            return
        self.frame.destroy()

