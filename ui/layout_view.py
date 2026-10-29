"""Tk workspace for the SIKPRO facility layout planner."""
import json
import math
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.lang import LANG
from layout.algorithm import (closeness_score, generate_alternatives,
                              material_flow_distance, validate_geometry,
                              violated_x_relationships)
from layout.export import export_pdf, export_png
from layout.models import LayoutInputError, LayoutProject, RATINGS, relation_key
from layout.persistence import load_project, save_project
from layout.visualization import canvas_to_world, fit_department_label, fit_floor_view
from ui.theme import ThemeManager


class LayoutApplication:
    def __init__(self, root, theme_manager=None):
        self.root = root
        self.theme_manager = theme_manager or ThemeManager(self)
        self.theme_manager.main = self
        self.current_lang = self.theme_manager.language
        self.lang_data = LANG[self.current_lang]
        self.project = LayoutProject()
        self.current_path = None
        self.selected_alternative_id = None
        self.selected_department_id = None
        self._saved_snapshot = self._snapshot()
        self._translated_widgets = []
        self._heading_translations = []
        self._drag_state = None
        self.root.title(self.t("layout_title"))
        self.root.resizable(True, True)
        self.root.minsize(900, 620)
        # The launcher and SPC both use the same Tk root. Match SPC's startup
        # behavior before building the layout widgets so no small window flashes.
        self.root.state("zoomed")
        self.theme_manager.install(root)
        self.build()
        self.root.protocol("WM_DELETE_WINDOW", self.request_close)

    def t(self, key):
        return self.lang_data.get(key, key)

    def set_on_back(self, callback):
        self.on_back = callback
        if hasattr(self, "back_button") and self.back_button.winfo_exists():
            self.back_button.configure(command=lambda: self.on_back() if self.on_back else None)

    @property
    def palette(self):
        return self.theme_manager.palette

    def build(self):
        self.root.configure(bg=self.palette["window"])
        self.outer = tk.Frame(self.root, bg=self.palette["window"])
        self.outer.pack(fill="both", expand=True, padx=12, pady=10)
        self.outer.columnconfigure(0, weight=1)
        self.outer.rowconfigure(2, weight=1)
        self._build_toolbar()
        self._build_heading()
        self._build_workspace()
        self._sync_project_fields()
        self.refresh_all()

    def _register(self, widget, key, option="text"):
        self._translated_widgets.append((widget, key, option))
        widget.configure(**{option: self.t(key)})
        return widget

    def _build_toolbar(self):
        bar = ttk.Frame(self.outer)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._button(bar, "layout_file_new", self.new_project).pack(side="left", padx=(0, 4))
        self._button(bar, "layout_file_open", self.open_project).pack(side="left", padx=4)
        self._button(bar, "layout_file_save", self.save_project).pack(side="left", padx=4)
        self._button(bar, "layout_file_save_as", self.save_project_as).pack(side="left", padx=4)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        self.generate_button = self._button(bar, "layout_generate", self.generate)
        self.generate_button.pack(side="left", padx=4)
        self.png_button = self._button(bar, "layout_file_png", self.export_selected_png)
        self.png_button.pack(side="left", padx=4)
        self.pdf_button = self._button(bar, "layout_file_pdf", self.export_report_pdf)
        self.pdf_button.pack(side="left", padx=4)
        self._button(bar, "layout_file_help", self.open_help).pack(side="left", padx=4)
        self.back_button = ttk.Button(bar, text=self.t("back_to_apps"), command=lambda: self.on_back() if getattr(self, "on_back", None) else None)
        self.back_button.pack(side="left", padx=4)
        self.language_var = tk.StringVar(value="English" if self.current_lang == "en" else "Bahasa Indonesia")
        language = ttk.Combobox(bar, textvariable=self.language_var, state="readonly", width=17,
                                values=("English", "Bahasa Indonesia"))
        language.pack(side="right", padx=(8, 0))
        language.bind("<<ComboboxSelected>>", lambda _event: self.set_language(
            "en" if self.language_var.get() == "English" else "id"))
        self.theme_var = tk.StringVar(value=self.t(self.theme_manager.mode))
        self.theme_box = ttk.Combobox(bar, textvariable=self.theme_var, state="readonly", width=10,
                                     values=(self.t("light"), self.t("dark")))
        self.theme_box.pack(side="right", padx=(8, 0))
        self.theme_box.bind("<<ComboboxSelected>>", lambda _event: self.set_theme(
            "light" if self.theme_var.get() == self.t("light") else "dark"))

    def _build_heading(self):
        header = ttk.Frame(self.outer)
        header.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.title_label = self._register(ttk.Label(header, font=("Segoe UI", 15, "bold")), "layout_title")
        self.title_label.pack(side="left")
        self.intro_label = self._register(ttk.Label(header, wraplength=620, foreground=self.palette["muted"]), "layout_intro")
        self.intro_label.pack(side="left", padx=(18, 0))
        self.project_path_label = ttk.Label(header, foreground=self.palette["muted"])
        self.project_path_label.pack(side="right")

    def _build_workspace(self):
        self.panes = ttk.Panedwindow(self.outer, orient="horizontal")
        self.panes.grid(row=2, column=0, sticky="nsew")
        self.left = ttk.Frame(self.panes, padding=(0, 0, 8, 0))
        self.right = ttk.Frame(self.panes, padding=(8, 0, 0, 0))
        self.panes.add(self.left, weight=1)
        self.panes.add(self.right, weight=3)
        self.left.rowconfigure(1, weight=1)
        self.left.columnconfigure(0, weight=1)
        self._build_project_panel()
        self._build_tabs()
        self._build_right_panel()

    def _build_project_panel(self):
        panel = ttk.LabelFrame(self.left, padding=8)
        self._register(panel, "layout_project")
        panel.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        panel.columnconfigure(1, weight=1)
        self.name_label = self._label(panel, "layout_project_name")
        self.name_label.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)
        self.project_name_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.project_name_var, width=25).grid(
            row=0, column=1, sticky="ew", pady=2)
        self.floor_width_label = self._label(panel, "layout_floor_width")
        self.floor_width_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=2)
        self.floor_width_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.floor_width_var, width=10).grid(
            row=1, column=1, sticky="ew", pady=2)
        self.floor_height_label = self._label(panel, "layout_floor_height")
        self.floor_height_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=2)
        self.floor_height_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.floor_height_var, width=10).grid(
            row=2, column=1, sticky="ew", pady=2)

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.left)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        self.department_tab = ttk.Frame(self.notebook, padding=6)
        self.relationship_tab = ttk.Frame(self.notebook, padding=6)
        self.flow_tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.department_tab, text=self.t("layout_departments"))
        self.notebook.add(self.relationship_tab, text=self.t("layout_relationships"))
        self.notebook.add(self.flow_tab, text=self.t("layout_flow"))
        self._translated_widgets.extend([
            (self.notebook, "layout_departments", "tab:0"),
            (self.notebook, "layout_relationships", "tab:1"),
            (self.notebook, "layout_flow", "tab:2"),
        ])
        for tab in (self.department_tab, self.relationship_tab, self.flow_tab):
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(0, weight=1)
        self._build_department_tab()
        self._build_relationship_tab()
        self._build_flow_tab()

    def _build_department_tab(self):
        self.department_tree = ttk.Treeview(self.department_tab, columns=("id", "name", "area"),
                                            show="headings", selectmode="browse", height=10)
        for column, key, width in (("id", "layout_id", 48), ("name", "layout_name", 145),
                                   ("area", "layout_area", 88)):
            self.department_tree.heading(column, text=self.t(key))
            self.department_tree.column(column, width=width, minwidth=38, stretch=True)
            self._heading_translations.append((self.department_tree, column, key))
        self.department_tree.grid(row=0, column=0, sticky="nsew")
        self.department_tree.bind("<<TreeviewSelect>>", self._department_selected)
        self.department_tree.bind("<Double-Button-1>", lambda _event: self.edit_department())
        buttons = ttk.Frame(self.department_tab)
        buttons.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self._button(buttons, "layout_add", self.add_department).pack(side="left", padx=(0, 4))
        self._button(buttons, "layout_edit", self.edit_department).pack(side="left", padx=4)
        self._button(buttons, "layout_delete", self.delete_department).pack(side="left", padx=4)

    def _build_relationship_tab(self):
        self.relationship_tree = ttk.Treeview(
            self.relationship_tab, columns=("pair", "rating", "reason"), show="headings",
            selectmode="browse", height=10,
        )
        for column, key, width in (("pair", "layout_pair", 120), ("rating", "layout_rating", 55),
                                   ("reason", "layout_reason", 150)):
            self.relationship_tree.heading(column, text=self.t(key))
            self.relationship_tree.column(column, width=width, minwidth=40, stretch=True)
            self._heading_translations.append((self.relationship_tree, column, key))
        self.relationship_tree.grid(row=0, column=0, sticky="nsew")
        self.relationship_tree.bind("<Double-Button-1>", lambda _event: self.edit_relationship())
        buttons = ttk.Frame(self.relationship_tab)
        buttons.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self._button(buttons, "layout_edit", self.edit_relationship).pack(side="left", padx=(0, 4))
        self._button(buttons, "layout_delete", self.delete_relationship).pack(side="left", padx=4)
        self._button(buttons, "layout_relationship_help", self.show_rating_help).pack(side="right")

    def _build_flow_tab(self):
        self.flow_tree = ttk.Treeview(self.flow_tab, columns=("from", "to", "quantity"),
                                      show="headings", selectmode="browse", height=9)
        for column, key, width in (("from", "layout_source", 85), ("to", "layout_target", 85),
                                   ("quantity", "layout_quantity", 110)):
            self.flow_tree.heading(column, text=self.t(key))
            self.flow_tree.column(column, width=width, minwidth=40, stretch=True)
            self._heading_translations.append((self.flow_tree, column, key))
        self.flow_tree.grid(row=0, column=0, sticky="nsew")
        self.flow_tree.bind("<Double-Button-1>", lambda _event: self.add_or_edit_flow())
        buttons = ttk.Frame(self.flow_tab)
        buttons.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self._button(buttons, "layout_add_flow", self.add_or_edit_flow).pack(side="left", padx=(0, 4))
        self._button(buttons, "layout_remove_flow", self.delete_flow).pack(side="left", padx=4)

    def _build_right_panel(self):
        self.right.rowconfigure(1, weight=1)
        self.right.columnconfigure(0, weight=1)
        alternatives_panel = ttk.LabelFrame(self.right, padding=6)
        self._register(alternatives_panel, "layout_alternatives")
        alternatives_panel.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        alternatives_panel.columnconfigure(0, weight=1)
        self.alternative_tree = ttk.Treeview(alternatives_panel, columns=("name", "score", "valid"),
                                             show="headings", selectmode="browse", height=4)
        for column, key, width in (("name", "layout_alternatives", 150),
                                   ("score", "layout_score", 110),
                                   ("valid", "layout_geometry", 100)):
            self.alternative_tree.heading(column, text=self.t(key))
            self.alternative_tree.column(column, width=width, minwidth=60, stretch=True)
            self._heading_translations.append((self.alternative_tree, column, key))
        self.alternative_tree.grid(row=0, column=0, sticky="ew")
        self.alternative_tree.bind("<<TreeviewSelect>>", self._alternative_selected)
        visual = ttk.LabelFrame(self.right, padding=6)
        self._register(visual, "layout_title")
        visual.grid(row=1, column=0, sticky="nsew")
        visual.rowconfigure(0, weight=1)
        visual.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(visual, highlightthickness=0, background=self.palette["panel"])
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _event: self.draw_layout())
        self.canvas.bind("<ButtonPress-1>", self._canvas_press)
        self.canvas.bind("<B1-Motion>", self._canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)
        self.canvas.bind("<Double-Button-1>", lambda _event: self.edit_selected_department())
        bottom = ttk.Frame(self.right)
        bottom.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.fit_button = self._button(bottom, "layout_fit", self.draw_layout)
        self.fit_button.pack(side="right")
        self.score_value = ttk.Label(bottom, foreground=self.palette["text"], wraplength=580)
        self.score_value.pack(side="left", anchor="w")
        self.status_value = ttk.Label(bottom, foreground=self.palette["muted"], wraplength=580)
        self.status_value.pack(side="left", anchor="w", padx=(12, 0))

    def _label(self, parent, key):
        return self._register(ttk.Label(parent), key)

    def _button(self, parent, key, command):
        return self._register(ttk.Button(parent, command=command), key)

    def set_theme(self, mode):
        self.theme_manager.set_theme(mode)
        self.theme_var.set(self.t(mode))
        self._apply_theme_colors()
        self.refresh_all()

    def set_language(self, language):
        if language not in LANG:
            raise ValueError(f"Unknown language: {language}")
        self.current_lang = language
        self.lang_data = LANG[language]
        self.theme_manager.set_language(language)
        self.root.title(self.t("layout_title"))
        for widget, key, option in self._translated_widgets:
            if option.startswith("tab:"):
                widget.tab(int(option.split(":")[1]), text=self.t(key))
            else:
                widget.configure(**{option: self.t(key)})
        for tree, column, key in self._heading_translations:
            tree.heading(column, text=self.t(key))
        self.language_var.set("English" if language == "en" else "Bahasa Indonesia")
        self.theme_box.configure(values=(self.t("light"), self.t("dark")))
        self.theme_var.set(self.t(self.theme_manager.mode))
        self.back_button.configure(text=self.t("back_to_apps"))
        self._update_details()
        self._update_path_label()
        self.draw_layout()

    def _apply_theme_colors(self):
        palette = self.palette
        self.root.configure(bg=palette["window"])
        self.outer.configure(bg=palette["window"])
        self.canvas.configure(bg=palette["panel"])
        self.project_path_label.configure(foreground=palette["muted"])
        self.intro_label.configure(foreground=palette["muted"])
        self.score_value.configure(foreground=palette["text"])
        self.status_value.configure(foreground=palette["muted"])

    def _sync_project_fields(self):
        self.project_name_var.set(self.project.project_name)
        self.floor_width_var.set(_format_number(self.project.floor_width))
        self.floor_height_var.set(_format_number(self.project.floor_height))

    def _commit_project_fields(self):
        name = self.project_name_var.get().strip()
        try:
            width = float(self.floor_width_var.get())
            height = float(self.floor_height_var.get())
        except ValueError:
            raise LayoutInputError(["floor_width_positive", "floor_height_positive"])
        if not name:
            raise LayoutInputError(["project_name_required"])
        if not math.isfinite(width) or width <= 0:
            raise LayoutInputError(["floor_width_positive"])
        if not math.isfinite(height) or height <= 0:
            raise LayoutInputError(["floor_height_positive"])
        if (self.project.project_name, self.project.floor_width, self.project.floor_height) != (name, width, height):
            self.project.set_floor(name, width, height)

    def _snapshot(self):
        state = {
            "project": self.project.to_dict(),
            "draft": [self.project_name_var.get() if hasattr(self, "project_name_var") else self.project.project_name,
                      self.floor_width_var.get() if hasattr(self, "floor_width_var") else _format_number(self.project.floor_width),
                      self.floor_height_var.get() if hasattr(self, "floor_height_var") else _format_number(self.project.floor_height)],
        }
        return json.dumps(state, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    def has_unsaved_changes(self):
        return self._snapshot() != self._saved_snapshot

    def _confirm_unsaved(self):
        if not self.has_unsaved_changes():
            return True
        choice = messagebox.askyesnocancel(self.t("layout_unsaved_title"), self.t("layout_unsaved_prompt"),
                                           parent=self.root)
        if choice is None:
            return False
        if choice:
            return self.save_project()
        return True

    def request_close(self):
        if self._confirm_unsaved():
            callback = getattr(self, "on_back", None)
            if callback:
                callback()
            else:
                self.root.destroy()

    def new_project(self):
        if not self._confirm_unsaved():
            return
        self.project = LayoutProject()
        self.current_path = None
        self.selected_alternative_id = None
        self.selected_department_id = None
        self._sync_project_fields()
        self._saved_snapshot = self._snapshot()
        self.refresh_all()

    def open_project(self):
        if not self._confirm_unsaved():
            return
        path = filedialog.askopenfilename(parent=self.root, title=self.t("layout_open_dialog"),
                                          filetypes=(("SIKPRO Layout", "*.layoutproj"), ("JSON", "*.json")))
        if not path:
            return
        self._load_path(path)

    def _load_path(self, path):
        try:
            staged = load_project(path)
        except Exception as exc:
            self._show_error(str(exc))
            return False
        previous = self.project
        previous_path = self.current_path
        previous_department = self.selected_department_id
        previous_alternative = self.selected_alternative_id
        previous_saved_snapshot = self._saved_snapshot
        previous_draft = (self.project_name_var.get(), self.floor_width_var.get(), self.floor_height_var.get())
        try:
            self.project = staged
            self.current_path = str(path)
            self.selected_department_id = None
            self.selected_alternative_id = staged.alternatives[0].id if staged.alternatives else None
            self._sync_project_fields()
            self.refresh_all()
            self._saved_snapshot = self._snapshot()
            return True
        except Exception as exc:
            self.project = previous
            self.current_path = previous_path
            self.selected_department_id = previous_department
            self.selected_alternative_id = previous_alternative
            self._saved_snapshot = previous_saved_snapshot
            self.project_name_var.set(previous_draft[0])
            self.floor_width_var.set(previous_draft[1])
            self.floor_height_var.set(previous_draft[2])
            self.refresh_all()
            self._show_error(str(exc))
            return False

    def save_project(self):
        path = self.current_path
        if not path:
            return self.save_project_as()
        try:
            self._commit_project_fields()
            save_project(path, self.project)
        except Exception as exc:
            self._show_error(str(exc))
            return False
        self._saved_snapshot = self._snapshot()
        self._update_path_label()
        self.refresh_all()
        return True

    def save_project_as(self):
        try:
            self._commit_project_fields()
        except LayoutInputError as exc:
            self._show_errors(exc.errors)
            return False
        path = filedialog.asksaveasfilename(parent=self.root, title=self.t("layout_save_dialog"),
                                            defaultextension=".layoutproj",
                                            filetypes=(("SIKPRO Layout", "*.layoutproj"),))
        if not path:
            return False
        try:
            save_project(path, self.project)
        except Exception as exc:
            self._show_error(str(exc))
            return False
        self.current_path = path
        self._saved_snapshot = self._snapshot()
        self._update_path_label()
        self.refresh_all()
        return True

    def add_department(self):
        self._department_dialog()

    def edit_department(self):
        department = self._selected_department()
        if not department:
            self._show_message("layout_select_department")
            return
        self._department_dialog(department)

    def edit_selected_department(self):
        if self.selected_department_id:
            self._department_dialog(self.project.get_department(self.selected_department_id))

    def _department_dialog(self, department=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("layout_edit") if department else self.t("layout_add"))
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg=self.palette["window"])
        form = ttk.Frame(dialog, padding=16)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)
        specs = (("layout_name", department.name if department else ""),
                 ("layout_area", _format_number(department.required_area) if department else ""),
                 ("layout_preferred_width", _format_number(department.preferred_width) if department and department.preferred_width else ""),
                 ("layout_preferred_height", _format_number(department.preferred_height) if department and department.preferred_height else ""))
        variables = []
        for row, (key, initial) in enumerate(specs):
            ttk.Label(form, text=self.t(key)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            variable = tk.StringVar(value=initial)
            ttk.Entry(form, textvariable=variable, width=28).grid(row=row, column=1, sticky="ew", pady=5)
            variables.append(variable)
        error_label = ttk.Label(form, foreground=self.palette["danger"], wraplength=340)
        error_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=4)
        buttons = ttk.Frame(form)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text=self.t("layout_cancel"), command=dialog.destroy).pack(side="right", padx=(6, 0))

        def submit():
            name, area_text, width_text, height_text = [variable.get().strip() for variable in variables]
            try:
                area = float(area_text)
                width = float(width_text) if width_text else None
                height = float(height_text) if height_text else None
            except ValueError:
                error_label.configure(text=self.t("layout_err_department_area_positive"))
                return
            errors = []
            if not name:
                errors.append("department_name_required")
            if not math.isfinite(area) or area <= 0:
                errors.append("department_area_positive")
            if (width is None) != (height is None):
                errors.append("department_dimensions_pair")
            elif width is not None and (not math.isfinite(width) or not math.isfinite(height)
                                        or width <= 0 or height <= 0):
                errors.append("department_dimensions_positive")
            if any(d.name.casefold() == name.casefold() and (department is None or d.id != department.id)
                   for d in self.project.departments):
                errors.append("department_names_unique")
            area_total = sum(d.required_area for d in self.project.departments if department is None or d.id != department.id) + (area if math.isfinite(area) and area > 0 else 0)
            try:
                floor_area = float(self.floor_width_var.get()) * float(self.floor_height_var.get())
            except ValueError:
                floor_area = self.project.floor_width * self.project.floor_height
            if area_total > floor_area + 1e-8:
                errors.append("required_area_exceeds_floor")
            if errors:
                error_label.configure(text="\n".join(self._localized_errors(errors)))
                return
            if department:
                self.project.update_department(department.id, name, area, width, height)
                self.selected_department_id = department.id
            else:
                self.selected_department_id = self.project.add_department(name, area, width, height).id
            dialog.destroy()
            self.refresh_all()

        ttk.Button(buttons, text=self.t("layout_save"), command=submit).pack(side="right")
        self._place_dialog(dialog, 500, 335)
        dialog.bind("<Return>", lambda _event: submit())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        self.root.wait_window(dialog)

    def delete_department(self):
        department = self._selected_department()
        if not department:
            self._show_message("layout_select_department")
            return
        if not messagebox.askyesno(self.t("layout_delete"), self.t("layout_confirm_delete_department"), parent=self.root):
            return
        self.project.remove_department(department.id)
        self.selected_department_id = None
        self.refresh_all()

    def _selected_department(self):
        selection = self.department_tree.selection()
        if not selection:
            return None
        try:
            return self.project.get_department(selection[0])
        except KeyError:
            return None

    def _department_selected(self, _event=None):
        department = self._selected_department()
        self.selected_department_id = department.id if department else None
        self._update_details()
        self.draw_layout()

    def edit_relationship(self):
        selection = self.relationship_tree.selection()
        if not selection:
            self._show_message("layout_select_relationship")
            return
        first, second = selection[0].split("::", 1)
        relationship = self.project.relationships.get(relation_key(first, second))
        self._relationship_dialog(first, second, relationship)

    def delete_relationship(self):
        selection = self.relationship_tree.selection()
        if not selection:
            self._show_message("layout_select_relationship")
            return
        first, second = selection[0].split("::", 1)
        self.project.remove_relationship(first, second)
        self.refresh_all()

    def _relationship_dialog(self, first, second, relationship=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("layout_relationships"))
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        form = ttk.Frame(dialog, padding=16)
        form.pack(fill="both", expand=True)
        pair_text = f"{self.project.get_department(first).name}  ↔  {self.project.get_department(second).name}"
        ttk.Label(form, text=pair_text, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Label(form, text=self.t("layout_rating")).grid(row=1, column=0, sticky="w", padx=(0, 12), pady=4)
        rating_var = tk.StringVar(value=(relationship.rating if relationship and relationship.rating else ""))
        rating_box = ttk.Combobox(form, textvariable=rating_var, state="readonly", values=RATINGS, width=8)
        rating_box.grid(row=1, column=1, sticky="w", pady=4)
        ttk.Label(form, text=self.t("layout_reason")).grid(row=2, column=0, sticky="w", padx=(0, 12), pady=4)
        reason_var = tk.StringVar(value=relationship.reason if relationship else "")
        ttk.Entry(form, textvariable=reason_var, width=38).grid(row=2, column=1, sticky="ew", pady=4)
        error = ttk.Label(form, foreground=self.palette["danger"])
        error.grid(row=3, column=0, columnspan=2, sticky="w")
        buttons = ttk.Frame(form)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text=self.t("layout_cancel"), command=dialog.destroy).pack(side="right", padx=(6, 0))

        def submit():
            rating = rating_var.get().strip().upper()
            if rating not in RATINGS:
                error.configure(text=self.t("layout_err_relationship_rating_required"))
                return
            self.project.set_relationship(first, second, rating, reason_var.get())
            dialog.destroy()
            self.refresh_all()

        ttk.Button(buttons, text=self.t("layout_save"), command=submit).pack(side="right")
        self._place_dialog(dialog, 520, 245)
        dialog.bind("<Return>", lambda _event: submit())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        self.root.wait_window(dialog)

    def show_rating_help(self):
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("layout_help_title"))
        dialog.transient(self.root)
        dialog.configure(bg=self.palette["window"])
        content = ttk.Frame(dialog, padding=16)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text=self.t("layout_help_title"), font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        text = tk.Text(content, wrap="word", width=70, height=13, relief="flat", padx=10, pady=10)
        text.pack(fill="both", expand=True)
        text.insert("1.0", self.t("layout_help_text"))
        text.configure(state="disabled")
        ttk.Button(content, text=self.t("layout_cancel"), command=dialog.destroy).pack(anchor="e", pady=(8, 0))
        self._place_dialog(dialog, 720, 500)

    def open_help(self):
        self.show_rating_help()

    def add_or_edit_flow(self):
        if len(self.project.departments) < 2:
            self._show_message("layout_err_department_required")
            return
        selected = self.flow_tree.selection()
        current = None
        if selected:
            source, target = selected[0].split("::", 1)
            current = self.project.material_flows.get((source, target))
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("layout_add_flow"))
        dialog.transient(self.root)
        dialog.grab_set()
        form = ttk.Frame(dialog, padding=16)
        form.pack(fill="both", expand=True)
        departments = [(d.id, d.name) for d in self.project.departments]
        names = [f"{department_id} — {name}" for department_id, name in departments]
        first_var = tk.StringVar(value=names[0])
        second_var = tk.StringVar(value=names[1])
        for row, (key, variable) in enumerate((("layout_source", first_var), ("layout_target", second_var))):
            ttk.Label(form, text=self.t(key)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            ttk.Combobox(form, textvariable=variable, state="readonly", values=names, width=30).grid(
                row=row, column=1, sticky="ew", pady=5)
        if selected:
            first_var.set(names[[item[0] for item in departments].index(source)])
            second_var.set(names[[item[0] for item in departments].index(target)])
        ttk.Label(form, text=self.t("layout_quantity")).grid(row=2, column=0, sticky="w", padx=(0, 10), pady=5)
        quantity_var = tk.StringVar(value=_format_number(current) if current is not None else "")
        ttk.Entry(form, textvariable=quantity_var, width=18).grid(row=2, column=1, sticky="w", pady=5)
        error = ttk.Label(form, foreground=self.palette["danger"])
        error.grid(row=3, column=0, columnspan=2, sticky="w")
        buttons = ttk.Frame(form)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text=self.t("layout_cancel"), command=dialog.destroy).pack(side="right", padx=(6, 0))

        def submit():
            first = first_var.get().split(" — ", 1)[0]
            second = second_var.get().split(" — ", 1)[0]
            try:
                quantity = float(quantity_var.get())
                if not math.isfinite(quantity) or quantity < 0:
                    raise ValueError
            except ValueError:
                error.configure(text=self.t("layout_err_material_flow_quantity_invalid"))
                return
            if first == second:
                error.configure(text=self.t("layout_err_material_flow_departments_invalid"))
                return
            self.project.set_material_flow(first, second, quantity)
            dialog.destroy()
            self.refresh_all()

        ttk.Button(buttons, text=self.t("layout_save"), command=submit).pack(side="right")
        self._place_dialog(dialog, 500, 290)
        dialog.bind("<Return>", lambda _event: submit())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        self.root.wait_window(dialog)

    def delete_flow(self):
        selection = self.flow_tree.selection()
        if not selection:
            self._show_message("layout_select_flow")
            return
        if not messagebox.askyesno(self.t("layout_delete"), self.t("layout_confirm_delete_flow"), parent=self.root):
            return
        self.project.set_material_flow(*selection[0].split("::", 1), None)
        self.refresh_all()

    def generate(self):
        try:
            self._commit_project_fields()
            alternatives = generate_alternatives(self.project)
        except LayoutInputError as exc:
            self._show_errors(exc.errors)
            return
        except Exception as exc:
            self._show_error(str(exc))
            return
        self.selected_alternative_id = alternatives[0].id if alternatives else None
        self.refresh_all()
        if alternatives:
            self.status_value.configure(text=self.t("layout_generated_message").format(count=len(alternatives)))

    def export_selected_png(self):
        alternative = self.selected_alternative()
        if alternative is None:
            self._show_message("layout_no_alternative")
            return False
        path = filedialog.asksaveasfilename(
            parent=self.root, title=self.t("layout_file_png"), defaultextension=".png",
            filetypes=(("PNG image", "*.png"),),
        )
        if not path:
            return False
        try:
            if not alternative.is_valid:
                messagebox.showwarning(self.t("layout_error_title"), self.t("layout_invalid_export"), parent=self.root)
            export_png(path, self.project, alternative, self.palette, self.current_lang)
        except Exception as exc:
            self._show_error(str(exc))
            return False
        self._show_message("layout_exported")
        return True

    def export_report_pdf(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, title=self.t("layout_file_pdf"), defaultextension=".pdf",
            filetypes=(("PDF report", "*.pdf"),),
        )
        if not path:
            return False
        try:
            export_pdf(path, self.project, self.palette, self.current_lang)
        except Exception as exc:
            self._show_error(str(exc))
            return False
        self._show_message("layout_exported")
        return True

    def refresh_all(self):
        if not hasattr(self, "department_tree"):
            return
        self._refresh_departments()
        self._refresh_relationships()
        self._refresh_flows()
        self._refresh_alternatives()
        self._update_path_label()
        self._update_details()
        self.draw_layout()

    def _refresh_departments(self):
        selected = self.selected_department_id
        self.department_tree.delete(*self.department_tree.get_children())
        for department in self.project.departments:
            self.department_tree.insert("", "end", iid=department.id,
                                        values=(department.id, department.name, _format_number(department.required_area)))
        if selected and selected in {item.id for item in self.project.departments}:
            self.department_tree.selection_set(selected)
        else:
            self.selected_department_id = None

    def _refresh_relationships(self):
        selected = self.relationship_tree.selection()
        keep = selected[0] if selected else None
        self.relationship_tree.delete(*self.relationship_tree.get_children())
        for index, first in enumerate(self.project.departments):
            for second in self.project.departments[index + 1:]:
                pair = relation_key(first.id, second.id)
                relationship = self.project.relationships.get(pair)
                self.relationship_tree.insert(
                    "", "end", iid=f"{pair[0]}::{pair[1]}",
                    values=(f"{first.name} ↔ {second.name}", relationship.rating or "—",
                            relationship.reason if relationship else ""),
                )
        if keep and self.relationship_tree.exists(keep):
            self.relationship_tree.selection_set(keep)

    def _refresh_flows(self):
        self.flow_tree.delete(*self.flow_tree.get_children())
        names = {department.id: department.name for department in self.project.departments}
        for (source, target), quantity in sorted(self.project.material_flows.items()):
            self.flow_tree.insert("", "end", iid=f"{source}::{target}",
                                  values=(names.get(source, source), names.get(target, target), _format_number(quantity)))

    def _refresh_alternatives(self):
        self.alternative_tree.delete(*self.alternative_tree.get_children())
        for index, alternative in enumerate(self.project.alternatives, 1):
            name = self.t("layout_alternative").format(number=index)
            self.alternative_tree.insert("", "end", iid=alternative.id,
                                         values=(name, f"{alternative.score:.2f}",
                                                 self.t("layout_valid") if alternative.is_valid else self.t("layout_invalid")))
        if self.selected_alternative_id and self.alternative_tree.exists(self.selected_alternative_id):
            self.alternative_tree.selection_set(self.selected_alternative_id)
        elif self.project.alternatives:
            self.selected_alternative_id = self.project.alternatives[0].id
            self.alternative_tree.selection_set(self.selected_alternative_id)
        else:
            self.selected_alternative_id = None
            self.png_button.configure(state="disabled")
            self.pdf_button.configure(state="disabled")
        if self.project.alternatives:
            self.png_button.configure(state="normal")
            self.pdf_button.configure(state="normal")

    def _alternative_selected(self, _event=None):
        selection = self.alternative_tree.selection()
        self.selected_alternative_id = selection[0] if selection else None
        self._update_details()
        self.draw_layout()

    def selected_alternative(self):
        for alternative in self.project.alternatives:
            if alternative.id == self.selected_alternative_id:
                return alternative
        return None

    def _update_details(self):
        alternative = self.selected_alternative()
        if alternative is None:
            self.score_value.configure(text="")
            self.status_value.configure(text=self.t("layout_empty_canvas"))
            return
        names = {department.id: department.name for department in self.project.departments}
        score = self.t("layout_score") + f": {alternative.score:.2f}"
        if alternative.flow_distance is None:
            flow = self.t("layout_not_calculated")
        else:
            flow = f"{self.t('layout_flow_distance')}: {alternative.flow_distance:.2f} quantity·m"
        self.score_value.configure(text=score + "   •   " + flow)
        violations = ", ".join(f"{names.get(a, a)} ↔ {names.get(b, b)}" for a, b in alternative.violated_x)
        if not violations:
            violations = "—"
        state = self.t("layout_valid") if alternative.is_valid else self.t("layout_invalid")
        details = []
        if self.selected_department_id:
            selected = next((item for item in self.project.departments
                             if item.id == self.selected_department_id), None)
            if selected:
                details.append(
                    f"{self.t('layout_selected_department')}: {selected.id} · {selected.name} · "
                    f"{selected.required_area:g} m²"
                )
        details.extend((f"{self.t('layout_violated_x')}: {violations}",
                        f"{self.t('layout_geometry')}: {state}"))
        if alternative.geometry_errors:
            details.extend(self._localized_geometry_errors(alternative.geometry_errors))
        self.status_value.configure(text="   •   ".join(details),
                                    foreground=self.palette["success"] if alternative.is_valid else self.palette["danger"])

    def draw_layout(self):
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        alternative = self.selected_alternative()
        if alternative is None:
            self.canvas.create_text(max(20, self.canvas.winfo_width() / 2),
                                    max(20, self.canvas.winfo_height() / 2),
                                    text=self.t("layout_empty_canvas"), fill=self.palette["muted"],
                                    width=max(120, self.canvas.winfo_width() - 50), justify="center")
            return
        floor_width, floor_height = self.project.floor_width, self.project.floor_height
        if not math.isfinite(floor_width) or not math.isfinite(floor_height) or floor_width <= 0 or floor_height <= 0:
            return
        width = max(200, self.canvas.winfo_width())
        height = max(160, self.canvas.winfo_height())
        padding = 34
        view = fit_floor_view(width, height, floor_width, floor_height, padding)
        scale = view["scale"]
        origin_x, origin_y = view["origin_x"], view["origin_y"]
        drawn_width, drawn_height = view["width"], view["height"]
        valid = not validate_geometry(self.project, alternative)
        outline = self.palette["border"] if valid else self.palette["danger"]
        self.canvas.create_rectangle(origin_x, origin_y, origin_x + drawn_width, origin_y + drawn_height,
                                     outline=outline, width=2, fill=self.palette["surface"], tags=("floor",))
        shades = (("#dbeafe", "#263f5d"), ("#dcfce7", "#244339"), ("#fef3c7", "#504329"),
                  ("#fce7f3", "#4b3042"), ("#e0e7ff", "#323b5a"), ("#cffafe", "#23454b"),
                  ("#ffedd5", "#4e3928"))
        is_dark = self.theme_manager.mode == "dark"
        for index, department in enumerate(self.project.departments):
            rectangle = alternative.rectangles.get(department.id)
            if rectangle is None:
                continue
            x1 = origin_x + rectangle.x * scale
            x2 = origin_x + (rectangle.x + rectangle.width) * scale
            y1 = origin_y + (floor_height - rectangle.y - rectangle.height) * scale
            y2 = origin_y + (floor_height - rectangle.y) * scale
            selected = department.id == self.selected_department_id
            fill = shades[index % len(shades)][1 if is_dark else 0]
            edge = self.palette["accent"] if selected else (self.palette["danger"] if not valid else self.palette["border"])
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=edge,
                                         width=3 if selected else 1.4,
                                         tags=(f"department:{department.id}", "department"))
            label = fit_department_label(department.id, department.name,
                                         department.required_area, x2 - x1, y2 - y1)
            if label:
                label_text, font_size = label
                self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2,
                                        text=label_text, fill=self.palette["text"],
                                        width=max(1, x2 - x1 - 8),
                                        font=("Segoe UI", font_size), justify="center",
                                        tags=(f"department:{department.id}",))
        self.canvas.create_text(origin_x, origin_y - 10, anchor="sw",
                                text=f"{floor_width:g} × {floor_height:g} m", fill=self.palette["muted"])
        if not valid:
            self.canvas.create_text(origin_x + drawn_width / 2, origin_y + 12,
                                    text=self.t("layout_invalid"), fill=self.palette["danger"],
                                    font=("Segoe UI", 10, "bold"))

    def _canvas_press(self, event):
        alternative = self.selected_alternative()
        if alternative is None:
            return
        point = self._canvas_to_world(event.x, event.y)
        if point is None:
            return
        # Test the actual world-space block bounds. Canvas ``find_closest`` can
        # select a neighboring label when small adjacent blocks touch.
        department_id = None
        for department in reversed(self.project.departments):
            rectangle = alternative.rectangles.get(department.id)
            if rectangle and rectangle.x - 1e-8 <= point[0] <= rectangle.x + rectangle.width + 1e-8 \
                    and rectangle.y - 1e-8 <= point[1] <= rectangle.y + rectangle.height + 1e-8:
                department_id = department.id
                break
        if not department_id:
            return
        rectangle = alternative.rectangles[department_id]
        self.selected_department_id = department_id
        self._drag_state = (department_id, point[0] - rectangle.x, point[1] - rectangle.y)
        if self.department_tree.exists(department_id):
            self.department_tree.selection_set(department_id)
        self._update_details()
        self.draw_layout()

    def _canvas_drag(self, event):
        if not self._drag_state:
            return
        alternative = self.selected_alternative()
        point = self._canvas_to_world(event.x, event.y)
        if alternative is None or point is None:
            return
        department_id, offset_x, offset_y = self._drag_state
        rectangle = alternative.rectangles[department_id]
        rectangle.x = point[0] - offset_x
        rectangle.y = point[1] - offset_y
        alternative.geometry_errors = validate_geometry(self.project, alternative)
        alternative.score = closeness_score(self.project, alternative.rectangles)
        alternative.violated_x = violated_x_relationships(self.project, alternative.rectangles)
        alternative.flow_distance = material_flow_distance(self.project, alternative.rectangles)
        self._update_details()
        self.draw_layout()

    def _canvas_release(self, _event):
        self._drag_state = None
        alternative = self.selected_alternative()
        if alternative:
            alternative.geometry_errors = validate_geometry(self.project, alternative)
            self._update_details()
            self._refresh_alternatives()
            self.draw_layout()

    def _canvas_to_world(self, x, y):
        width = max(200, self.canvas.winfo_width())
        height = max(160, self.canvas.winfo_height())
        floor_width, floor_height = self.project.floor_width, self.project.floor_height
        if floor_width <= 0 or floor_height <= 0:
            return None
        view = fit_floor_view(width, height, floor_width, floor_height, padding=34)
        return canvas_to_world(x, y, floor_height, view)

    def _localized_errors(self, errors):
        messages = []
        for error in errors:
            code, _, detail = error.partition(":")
            text = self.t(f"layout_err_{code}")
            if text == f"layout_err_{code}":
                text = error.replace("_", " ").capitalize()
            if detail and code.startswith("department_"):
                text += f" ({detail})"
            elif detail and code.startswith("relationship_"):
                text += f" ({detail.replace(':', ' – ')})"
            messages.append(text)
        return messages

    def _localized_geometry_errors(self, errors):
        result = []
        for error in errors:
            code, _, detail = error.partition(":")
            key = f"layout_err_{code}"
            text = self.t(key)
            if text == key:
                text = error.replace("_", " ").capitalize()
            result.append(text + (f" ({detail.replace(':', ' – ')})" if detail else ""))
        return result

    def _show_errors(self, errors):
        messagebox.showerror(self.t("layout_error_title"), "\n".join(self._localized_errors(errors)), parent=self.root)

    def _show_error(self, message):
        messagebox.showerror(self.t("layout_error_title"), message, parent=self.root)

    def _show_message(self, key):
        messagebox.showinfo(self.t("layout_title"), self.t(key), parent=self.root)

    def _update_path_label(self):
        name = Path(self.current_path).name if self.current_path else self.project.project_name
        self.project_path_label.configure(text=name)

    def _place_dialog(self, dialog, width, height):
        dialog.update_idletasks()
        parent_x, parent_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        parent_w, parent_h = self.root.winfo_width(), self.root.winfo_height()
        x = max(0, parent_x + (parent_w - width) // 2)
        y = max(0, parent_y + (parent_h - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.minsize(width, height)


def _format_number(value):
    if value is None:
        return ""
    return f"{value:g}"
