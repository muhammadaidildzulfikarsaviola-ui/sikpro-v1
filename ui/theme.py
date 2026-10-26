"""Small application-wide Light/Dark theme manager for Tk and Matplotlib."""
import json
import os
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk


PALETTES = {
    "light": {
        "window": "#f3f6fa", "surface": "#ffffff", "panel": "#f8fafc",
        "input": "#ffffff", "text": "#1e293b", "text_soft": "#334155",
        "muted": "#64748b", "disabled": "#94a3b8", "border": "#dbe3ec",
        "accent": "#2563eb", "accent_hover": "#1d4ed8", "selected": "#dbeafe",
        "selected_text": "#1e293b", "hover": "#eaf2ff", "plot": "#ffffff",
        "plot_grid": "#dbe3ec", "danger": "#b91c1c", "success": "#15803d",
    },
    "dark": {
        "window": "#171c24", "surface": "#222a35", "panel": "#1d2530",
        "input": "#18212b", "text": "#e7edf5", "text_soft": "#d3dce8",
        "muted": "#a5b1c1", "disabled": "#778496", "border": "#3a4655",
        "accent": "#78aaff", "accent_hover": "#a4c5ff", "selected": "#304766",
        "selected_text": "#f3f7fc", "hover": "#2a394c", "plot": "#202833",
        "plot_grid": "#465363", "danger": "#ff8585", "success": "#75d49a",
    },
}

_COLOR_ROLES = {}
for _role, _colors in {
    "window": ("#f3f6fa", "#171c24"),
    "surface": ("#ffffff", "#222a35"),
    "panel": ("#f8fafc", "#1d2530", "#f1f5f9"),
    "input": ("#ffffff", "#18212b"),
    "text": ("#1e293b", "#0f172a", "#e7edf5", "black", "#000000", "#333333", "#444"),
    "text_soft": ("#334155", "#d3dce8"),
    "muted": ("#64748b", "#475569", "#a5b1c1"),
    "disabled": ("#94a3b8", "#778496"),
    "border": ("#dbe3ec", "#e2e8f0", "#3a4655", "#2b2b2b"),
    "accent": ("#2563eb", "#1d4ed8", "#1d4ed8", "#78aaff"),
    "selected": ("#dbeafe", "#eaf2ff", "#e2e8f0", "#304766", "#2a394c"),
    "selected_text": ("#1e293b", "#f3f7fc"),
    "plot": ("#202833",),
}.items():
    for _color in _colors:
        _COLOR_ROLES[_color] = _role
for _mode_palette in PALETTES.values():
    for _role, _color in _mode_palette.items():
        _COLOR_ROLES[_color.lower()] = _role


def default_settings_path():
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / "SIKPRO" / "settings.json"


class ThemeManager:
    def __init__(self, main, settings_path=None):
        self.main = main
        self.settings_path = Path(settings_path) if settings_path else default_settings_path()
        self.mode = "light"
        self.last_persistence_error = None
        self._bound_root = None
        try:
            value = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if value.get("theme") in PALETTES:
                self.mode = value["theme"]
        except (OSError, ValueError, AttributeError):
            pass

    @property
    def palette(self):
        return PALETTES[self.mode]

    def install(self, root):
        if self._bound_root != str(root):
            root.bind_all("<Map>", self._on_map, add="+")
            self._bound_root = str(root)
        self._configure_ttk(root)
        self.apply(root)

    def set_theme(self, mode, persist=True):
        if mode not in PALETTES:
            raise ValueError(f"Unknown theme: {mode}")
        self.mode = mode
        self._configure_ttk(self.main.root)
        self.apply(self.main.root)
        ui = getattr(self.main, "ui", None)
        if ui is not None and getattr(ui, "theme_var", None) is not None:
            ui.theme_var.set(mode)
        if persist:
            self.save()

    def save(self):
        payload = {}
        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                payload = {}
        except (OSError, ValueError):
            pass
        payload["theme"] = self.mode
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix="settings-", suffix=".tmp", dir=self.settings_path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    json.dump(payload, stream, indent=2)
                os.replace(temporary, self.settings_path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            self.last_persistence_error = None
        except OSError as exc:
            # os.replace can be denied by Windows profile/sandbox ACLs even
            # when the settings file itself is writable. Fall back to a
            # direct UTF-8 write so a theme choice can still persist.
            try:
                self.settings_path.parent.mkdir(parents=True, exist_ok=True)
                self.settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                self.last_persistence_error = None
            except OSError as fallback_exc:
                self.last_persistence_error = fallback_exc

    def apply(self, root=None):
        root = root or self.main.root
        palette = self.palette
        self._apply_matplotlib_defaults(palette)
        self._apply_tree(root)
        self._apply_sheet()
        self._apply_open_figures()

    def _configure_ttk(self, root):
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        p = self.palette
        style.configure(".", background=p["surface"], foreground=p["text"],
                        font=("Segoe UI", 9))
        style.configure("TFrame", background=p["surface"])
        style.configure("TLabel", background=p["surface"], foreground=p["text"])
        style.configure("TButton", background=p["panel"], foreground=p["text"],
                        bordercolor=p["border"], lightcolor=p["panel"], darkcolor=p["panel"],
                        focuscolor=p["accent"], padding=(9, 5))
        style.map("TButton", background=[("disabled", p["window"]), ("pressed", p["selected"]), ("active", p["hover"])],
                  foreground=[("disabled", p["disabled"]), ("active", p["text"])])
        style.configure("TEntry", fieldbackground=p["input"], foreground=p["text"],
                        insertcolor=p["text"], bordercolor=p["border"], lightcolor=p["accent"],
                        darkcolor=p["border"])
        style.map("TEntry", fieldbackground=[("disabled", p["panel"])],
                  foreground=[("disabled", p["disabled"])])
        style.configure("TCombobox", fieldbackground=p["input"], background=p["panel"],
                        foreground=p["text"], arrowcolor=p["text"], bordercolor=p["border"])
        style.map("TCombobox", fieldbackground=[("readonly", p["input"]), ("disabled", p["panel"])],
                  foreground=[("disabled", p["disabled"])], selectbackground=[("readonly", p["selected"])],
                  selectforeground=[("readonly", p["selected_text"])])
        style.configure("Treeview", background=p["input"], fieldbackground=p["input"],
                        foreground=p["text"], bordercolor=p["border"], rowheight=25)
        style.map("Treeview", background=[("selected", p["selected"])],
                  foreground=[("selected", p["selected_text"])])
        style.configure("Treeview.Heading", background=p["panel"], foreground=p["text"],
                        bordercolor=p["border"])
        style.map("Treeview.Heading", background=[("active", p["hover"])])
        style.configure("TScrollbar", background=p["panel"], troughcolor=p["window"],
                        arrowcolor=p["muted"], bordercolor=p["border"])
        style.configure("TSeparator", background=p["border"])
        style.configure("TNotebook", background=p["window"], bordercolor=p["border"])
        style.configure("TNotebook.Tab", background=p["panel"], foreground=p["text"], padding=(9, 5))
        style.map("TNotebook.Tab", background=[("selected", p["surface"]), ("active", p["hover"])],
                  foreground=[("disabled", p["disabled"])])
        style.configure("TPanedwindow", background=p["window"])
        style.configure("TLabelframe", background=p["surface"], foreground=p["text"], bordercolor=p["border"])
        style.configure("TLabelframe.Label", background=p["surface"], foreground=p["text"])
        for name in ("TCheckbutton", "TRadiobutton"):
            style.configure(name, background=p["surface"], foreground=p["text"], focuscolor=p["accent"])
            style.map(name, background=[("active", p["surface"])], foreground=[("disabled", p["disabled"])])

    def _on_map(self, event):
        widget = event.widget
        try:
            if isinstance(widget, (tk.Toplevel, tk.Menu)):
                widget.after_idle(lambda: self._apply_tree(widget) if widget.winfo_exists() else None)
            elif widget is self.main.root or isinstance(widget, (tk.Frame, tk.Label, tk.Canvas, tk.Entry, tk.Text, tk.Listbox, tk.Button, tk.Scrollbar)):
                widget.after_idle(lambda: self._apply_widget(widget) if widget.winfo_exists() else None)
        except tk.TclError:
            pass

    def _apply_tree(self, widget):
        self._apply_widget(widget)
        try:
            children = widget.winfo_children()
        except tk.TclError:
            return
        for child in children:
            self._apply_tree(child)

    def _apply_widget(self, widget):
        p = self.palette
        if hasattr(widget, "set_theme"):
            try:
                widget.set_theme(p)
                return
            except (tk.TclError, TypeError):
                pass
        try:
            kind = widget.winfo_class()
            if isinstance(widget, ttk.Widget):
                return
            current_bg = self._get(widget, "background", "bg")
            current_fg = self._get(widget, "foreground", "fg")
            if kind in ("Tk", "Toplevel"):
                bg_role = "window"
            elif kind == "Menu":
                bg_role = "panel"
            elif kind in ("Entry", "Text", "Listbox"):
                bg_role = "input"
            elif kind == "Canvas":
                bg_role = "plot"
            else:
                bg_role = self._role(current_bg, "surface")
            options = {"background": p[bg_role]}
            if kind in ("Menu", "Button", "Entry", "Text", "Listbox", "Label", "Frame", "Toplevel", "Tk", "Canvas", "Checkbutton", "Radiobutton", "Scrollbar"):
                fg_role = self._role(current_fg, "text")
                options["foreground"] = p[fg_role]
                options["activebackground"] = p["hover"]
                options["activeforeground"] = p["text"]
                options["disabledforeground"] = p["disabled"]
            if kind in ("Entry", "Text", "Listbox"):
                options.update(insertbackground=p["text"], selectbackground=p["selected"],
                               selectforeground=p["selected_text"], highlightbackground=p["border"],
                               highlightcolor=p["accent"])
            elif kind == "Menu":
                options.update(activebackground=p["selected"], activeforeground=p["selected_text"],
                               selectcolor=p["accent"])
            elif kind == "Canvas":
                options.update(highlightbackground=p["border"])
            elif kind == "Scrollbar":
                options.update(troughcolor=p["window"], activebackground=p["hover"])
            self._configure_supported(widget, options)
        except (tk.TclError, TypeError, AttributeError):
            return

    @staticmethod
    def _get(widget, *names):
        for name in names:
            try:
                value = widget.cget(name)
                if value:
                    return str(value).lower()
            except (tk.TclError, TypeError):
                pass
        return ""

    @staticmethod
    def _role(color, fallback):
        color = str(color).lower()
        if color in ("#ffffff", "white"):
            return fallback
        return _COLOR_ROLES.get(color, fallback)

    @staticmethod
    def _configure_supported(widget, options):
        try:
            keys = set(widget.keys())
        except (tk.TclError, AttributeError):
            return
        allowed = {key: value for key, value in options.items() if key in keys}
        if allowed:
            widget.configure(**allowed)

    def _apply_sheet(self):
        sheet = getattr(getattr(self.main, "sheet", None), "sheet", None)
        if sheet is None:
            return
        p = self.palette
        options = {
            "header_bg": p["panel"], "header_fg": p["text"], "header_grid_fg": p["border"],
            "header_selected_cells_bg": p["selected"], "header_selected_cells_fg": p["selected_text"],
            "index_bg": p["panel"], "index_fg": p["muted"], "index_grid_fg": p["border"],
            "index_selected_cells_bg": p["selected"], "index_selected_cells_fg": p["selected_text"],
            "top_left_bg": p["panel"], "top_left_fg": p["muted"],
            "table_bg": p["input"], "table_fg": p["text"], "table_grid_fg": p["border"],
            "table_selected_cells_bg": p["selected"], "table_selected_cells_fg": p["selected_text"],
            "table_selected_cells_border_fg": p["accent"], "table_selected_box_cells_fg": p["accent"],
            "table_editor_bg": p["input"], "table_editor_fg": p["text"],
            "table_editor_select_bg": p["selected"], "table_editor_select_fg": p["selected_text"],
        }
        try:
            sheet.set_options(redraw=False, **options)
            sheet.refresh()
        except (tk.TclError, TypeError, AttributeError):
            return

    def _apply_matplotlib_defaults(self, p):
        try:
            import matplotlib as mpl
            mpl.rcParams.update({
                "figure.facecolor": p["plot"], "figure.edgecolor": p["plot"],
                "axes.facecolor": p["plot"], "axes.edgecolor": p["border"],
                "axes.labelcolor": p["text"], "axes.titlecolor": p["text"],
                "text.color": p["text"], "xtick.color": p["muted"], "ytick.color": p["muted"],
                "grid.color": p["plot_grid"], "legend.facecolor": p["surface"],
                "legend.edgecolor": p["border"], "savefig.facecolor": p["plot"],
            })
        except (ImportError, ValueError):
            return

    def _apply_open_figures(self):
        try:
            from matplotlib._pylab_helpers import Gcf
            for manager in Gcf.get_all_fig_managers():
                self.apply_figure(manager.canvas.figure)
        except (ImportError, AttributeError):
            pass

    def apply_figure(self, figure):
        p = self.palette
        figure.set_facecolor(p["plot"])
        figure.set_edgecolor(p["plot"])
        for axes in figure.axes:
            axes.set_facecolor(p["plot"])
            axes.title.set_color(p["text"])
            axes.xaxis.label.set_color(p["text"])
            axes.yaxis.label.set_color(p["text"])
            axes.tick_params(colors=p["muted"])
            for spine in axes.spines.values():
                spine.set_color(p["border"])
            for line in axes.get_xgridlines() + axes.get_ygridlines():
                line.set_color(p["plot_grid"])
            for patch in axes.patches:
                from matplotlib.colors import to_hex
                face = to_hex(patch.get_facecolor()).lower()
                edge = to_hex(patch.get_edgecolor()).lower()
                if face in _COLOR_ROLES:
                    patch.set_facecolor(p[self._role(face, "panel")])
                if edge in _COLOR_ROLES:
                    patch.set_edgecolor(p[self._role(edge, "border")])
            for text in axes.texts:
                old = str(text.get_color()).lower()
                role = self._role(old, "text")
                if old in _COLOR_ROLES or old in ("black", "#000000", "#333333"):
                    text.set_color(p[role])
                box = text.get_bbox_patch()
                if box is not None:
                    from matplotlib.colors import to_hex
                    face = to_hex(box.get_facecolor()).lower()
                    if face in _COLOR_ROLES:
                        box.set_facecolor(p[self._role(face, "panel")])
                    box.set_edgecolor(p["border"])
            legend = axes.get_legend()
            if legend:
                legend.get_frame().set_facecolor(p["surface"])
                legend.get_frame().set_edgecolor(p["border"])
                for text in legend.get_texts():
                    text.set_color(p["text"])
        try:
            figure.canvas.draw_idle()
        except (tk.TclError, AttributeError):
            pass
