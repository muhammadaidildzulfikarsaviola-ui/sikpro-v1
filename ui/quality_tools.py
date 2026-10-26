"""Workspace views for Fishbone, Check Sheet, and defect concentration."""
import re
import textwrap
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Ellipse, FancyBboxPatch

from logic.chart_canvas import FigureCanvasTkAgg
from models.quality_tools import FishboneModel, CheckSheetModel, DefectConcentrationModel
from help.quality_tool_help import QUALITY_TOOL_HELP


class ToolView(tk.Frame):
    def __init__(self, main, key, title_key, guidance_key, **kwargs):
        self.main = main
        self.tool_key = key
        self.host = main.root._sikpro_chart_host
        self.host.prepare_chart_view()
        super().__init__(self.host.chart_canvas, bg=main.theme_manager.palette["surface"], **kwargs)
        self.pack(fill="both", expand=True)
        self._window_title = main.t(title_key)
        self.host.activate_chart_view(self)
        self.host.workspace_title.configure(text=self._window_title)
        self.host.context_title.configure(text=main.t(title_key))
        self.host.context_help.configure(text=main.t(guidance_key))
        self.host.set_active_navigation(key)
        if key in QUALITY_TOOL_HELP["en"]:
            self.host.context_tool_help_button.configure(
                text=main.t("quality_tool_help"),
                command=self.open_help,
            )
            self.host.context_tool_help_button.pack(anchor="w", padx=14, pady=(0, 12))

    def title(self, value=None):
        if value is not None:
            self._window_title = value
            self.host.set_chart_title(value)
        return self._window_title

    def close_all(self):
        self.destroy()

    def open_help(self):
        if getattr(self, "_help_dialog", None) is not None:
            try:
                if self._help_dialog.winfo_exists():
                    self._help_dialog.lift()
                    self._help_dialog.focus_force()
                    return self._help_dialog
            except tk.TclError:
                pass
        self._help_dialog = QualityToolHelpDialog(self.main, self.tool_key)
        return self._help_dialog

    def _error(self, exc):
        text = str(exc)
        key = {
            "Category is required": "validation_category_required",
            "Cause is required": "validation_cause_required",
            "Category already exists": "validation_duplicate_category",
            "Reassign causes before deleting this category": "validation_category_has_causes",
            "Default categories cannot be deleted": "validation_default_category",
            "Choose a different category": "validation_choose_different_category",
            "Unknown category": "validation_unknown_category",
            "Unknown cause": "validation_unknown_cause",
            "Unknown record": "validation_unknown_record",
            "Unknown mark": "validation_unknown_mark",
            "Count is required": "validation_count_required",
            "Count must be a nonnegative integer": "validation_count_integer",
            "Reassign or delete records before deleting this category": "validation_category_has_records",
            "Reassign or delete marks before deleting this category": "validation_category_has_marks",
            "Defect position must be inside the inspection area": "location_inside_object",
        }.get(text)
        messagebox.showerror(self.main.t("error"), self.main.t(key) if key else text, parent=self.main.root)


class QualityToolHelpDialog(tk.Toplevel):
    """Nonmodal, localized instructions that leave the active tool untouched."""
    def __init__(self, main, tool_key):
        super().__init__(main.root)
        self.main = main
        self.tool_key = tool_key
        self.title(f'{main.t(tool_key)} — {main.t("quality_tool_help")}')
        self.transient(main.root)
        self.resizable(True, True)
        self.minsize(480, 360)
        self.geometry("640x520")
        palette = main.theme_manager.palette
        self.configure(background=palette["surface"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=main.t(tool_key), font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 8)
        )
        text_frame = ttk.Frame(self)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=18)
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.content = tk.Text(
            text_frame, wrap="word", relief="flat", bd=0, padx=12, pady=10,
            bg=palette["input"], fg=palette["text"], insertbackground=palette["text"],
            font=("Segoe UI", 10), spacing1=2, spacing3=5, state="disabled",
        )
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.content.yview)
        self.content.configure(yscrollcommand=scroll.set)
        self.content.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.content.tag_configure("heading", foreground=palette["accent"],
                                   font=("Segoe UI", 10, "bold"), spacing1=8, spacing3=4)
        self.content.tag_configure("body", foreground=palette["text"], lmargin1=4, lmargin2=4)
        self._render()

        actions = ttk.Frame(self)
        actions.grid(row=2, column=0, sticky="e", padx=18, pady=14)
        self.close_button = ttk.Button(actions, text=main.t("quality_help_close"), command=self.destroy)
        self.close_button.pack()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _render(self):
        language = self.main.current_lang if self.main.current_lang in QUALITY_TOOL_HELP else "en"
        content = QUALITY_TOOL_HELP[language][self.tool_key]
        self.content.configure(state="normal")
        self.content.insert("end", f'{self.main.t("quality_help_purpose")}\n', "heading")
        self.content.insert("end", content["purpose"] + "\n\n", "body")
        self.content.insert("end", f'{self.main.t("quality_help_steps")}\n', "heading")
        for index, step in enumerate(content["steps"], start=1):
            self.content.insert("end", f"{index}. {step}\n", "body")
        self.content.insert("end", f'\n{self.main.t("quality_help_next")}\n', "heading")
        self.content.insert("end", content["next"] + "\n", "body")
        self.content.configure(state="disabled")

    def set_theme(self, palette):
        self.configure(background=palette["surface"])
        self.content.configure(
            background=palette["input"], foreground=palette["text"],
            insertbackground=palette["text"],
        )
        self.content.tag_configure("heading", foreground=palette["accent"])
        self.content.tag_configure("body", foreground=palette["text"])


class FishboneView(ToolView):
    def __init__(self, main):
        super().__init__(main, "fishbone", "fishbone", "fishbone_help")
        self.model = main.tool_models.setdefault("fishbone", FishboneModel(main.current_lang))
        self._build()
        self.refresh()

    def _build(self):
        p = self.main.theme_manager.palette
        top = tk.Frame(self, bg=p["surface"]); top.pack(fill="x", padx=14, pady=10)
        tk.Label(top, text=self.main.t("effect"), bg=p["surface"], fg=p["text"]).pack(side="left")
        self.effect_var = tk.StringVar(value=self.model.effect)
        self.effect_entry = ttk.Entry(top, textvariable=self.effect_var)
        self.effect_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.effect_var.trace_add("write", lambda *_: self._effect_changed())
        ttk.Button(top, text=self.main.t("add_cause"), command=self.add_cause).pack(side="left")
        ttk.Button(top, text=self.main.t("add_category"), command=self.add_category).pack(side="left", padx=5)
        ttk.Button(top, text=self.main.t("rename_category"), command=self.rename_category).pack(side="left")
        ttk.Button(top, text=self.main.t("delete_category"), command=self.delete_category).pack(side="left", padx=5)
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=6)
        bottom = tk.Frame(self, bg=p["surface"]); bottom.pack(fill="x", padx=14, pady=(0, 10))
        ttk.Button(bottom, text="PNG", command=lambda: self.export("png")).pack(side="right", padx=4)
        ttk.Button(bottom, text="PDF", command=lambda: self.export("pdf")).pack(side="right")
        ttk.Button(bottom, text=self.main.t("edit_cause"), command=self.edit_cause).pack(side="left")
        ttk.Button(bottom, text=self.main.t("move_cause"), command=self.move_cause).pack(side="left", padx=4)
        ttk.Button(bottom, text="↑", width=3, command=lambda: self.reorder_cause(-1)).pack(side="left")
        ttk.Button(bottom, text="↓", width=3, command=lambda: self.reorder_cause(1)).pack(side="left", padx=(2, 0))
        ttk.Button(bottom, text=self.main.t("delete_cause"), command=self.delete_cause).pack(side="left", padx=4)
        self.listbox = tk.Listbox(bottom, height=4, width=54, exportselection=False)
        self.listbox.pack(side="left", padx=10)

    def _effect_changed(self):
        self.model.effect = self.effect_var.get().strip()
        self.refresh()

    def _selected_category(self):
        if not self.model.categories:
            raise ValueError(self.main.t("add_category"))
        names = [f'{c["name"]} ({sum(x.category_id == c["id"] for x in self.model.causes)})' for c in self.model.categories]
        picker = CategoryPicker(self.main.root, self.main.t("category"), names)
        if picker.value is None:
            return None
        return self.model.categories[picker.value]["id"]

    def add_cause(self):
        category_id = self._selected_category()
        if not category_id: return
        CauseEditorDialog(self.main, self.main.t("add_cause"), "",
                          lambda value: self._save_cause(category_id, value))

    def _save_cause(self, category_id, value):
        cause_id = self.model.add_cause(category_id, value)
        self.refresh()
        return cause_id

    def edit_cause(self):
        index = self.listbox.curselection()
        if not index: return
        cause = self.model.causes[index[0]]
        CauseEditorDialog(self.main, self.main.t("edit_cause"), cause.text,
                          lambda value: self._edit_cause(cause.id, value))

    def _edit_cause(self, cause_id, value):
        self.model.edit_cause(cause_id, value)
        self.refresh()
        return cause_id

    def delete_cause(self):
        index = self.listbox.curselection()
        if index: self.model.delete_cause(self.model.causes[index[0]].id); self.refresh()

    def move_cause(self):
        index = self.listbox.curselection()
        if not index: return
        category_id = self._selected_category()
        if category_id:
            self.model.edit_cause(self.model.causes[index[0]].id, self.model.causes[index[0]].text, category_id)
            self.refresh()

    def reorder_cause(self, offset):
        index = self.listbox.curselection()
        if not index: return
        self.model.move_cause_order(self.model.causes[index[0]].id, offset)
        self.refresh()

    def add_category(self):
        value = CategoryTextDialog(self.main, self.main.t("add_category"), "").value
        if value is None: return
        try: self.model.add_category(value); self.refresh()
        except ValueError as exc: self._error(exc)

    def rename_category(self):
        category_id = self._selected_category()
        if not category_id: return
        category = next(c for c in self.model.categories if c["id"] == category_id)
        value = CategoryTextDialog(self.main, self.main.t("rename_category"), category["name"]).value
        if value is None: return
        try: self.model.rename_category(category_id, value); self.refresh()
        except ValueError as exc: self._error(exc)

    def delete_category(self):
        category_id = self._selected_category()
        if not category_id: return
        category = next(c for c in self.model.categories if c["id"] == category_id)
        if not messagebox.askyesno(self.main.t("delete_category"), self.main.t("confirm_delete_category"), parent=self.main.root): return
        try: self.model.delete_category(category_id); self.refresh()
        except ValueError as exc: self._error(exc)

    def refresh(self):
        if not hasattr(self, "ax"): return
        self.listbox.delete(0, tk.END)
        for cause in self.model.causes:
            cat = next((c["name"] for c in self.model.categories if c["id"] == cause.category_id), "")
            self.listbox.insert(tk.END, f"{cat}: {cause.text}")
        self.ax.clear(); self.ax.axis("off")
        categories = self.model.categories
        self.ax.set_xlim(0, 1.48)
        self.ax.set_ylim(-1.2, 1.2)
        p = self.main.theme_manager.palette
        self.figure.set_facecolor(p["plot"])
        self.ax.set_facecolor(p["plot"])
        self.ax.annotate("", xy=(1.00, 0), xytext=(.05, 0),
                         arrowprops={"arrowstyle": "->", "lw": 2.2, "color": p["text_soft"]})
        effect = textwrap.fill(self.model.effect or self.main.t("effect_required"), width=28)
        self.ax.text(1.04, 0, effect,
                     ha="left", va="center", fontsize=10, wrap=True,
                     color=p["text"], bbox={"boxstyle": "round,pad=.45", "fc": p["selected"], "ec": p["accent"]})

        # Keep the six cause groups in separate columns. Cause text is wrapped
        # within its own category block and the figure grows with dense entries.
        max_lines = 1
        for i, category in enumerate(categories):
            causes = [c.text for c in self.model.causes if c.category_id == category["id"]]
            wrapped = [textwrap.fill(cause, width=25) for cause in causes]
            block = category["name"] + ("\n" + "\n".join(f"• {cause}" for cause in wrapped) if wrapped else "")
            max_lines = max(max_lines, block.count("\n") + 1)
            column = i // 2
            x = .12 + column * .29
            sign = 1 if i % 2 == 0 else -1
            branch_y = sign * .43
            label_y = sign * (.72 + max(0, max_lines - 2) * .08)
            self.ax.plot([x + .10, x + .22], [0, branch_y], color=p["muted"], lw=1.5)
            self.ax.plot([x + .14, x + .10], [branch_y - sign * .12, branch_y], color=p["border"], lw=1)
            self.ax.text(x, label_y, block, ha="left", va="bottom" if sign > 0 else "top",
                         fontsize=8, weight="bold", color=p["accent"], linespacing=1.2)

        half_height = max(1.25, .78 + max_lines * .16)
        self.ax.set_ylim(-half_height, half_height)
        self.figure.set_size_inches(12, max(6, 2.8 + max_lines * .34), forward=True)
        self.figure.subplots_adjust(left=.025, right=.975, top=.96, bottom=.06)
        self.canvas.draw_idle()

    def export(self, ext):
        if not self.model.effect.strip():
            messagebox.showerror(self.main.t("error"), self.main.t("effect_required"), parent=self.main.root); return
        base = re.sub(r"[^\w-]+", "_", self.model.effect.strip(), flags=re.UNICODE).strip("_")[:60] or "fishbone"
        path = filedialog.asksaveasfilename(parent=self.main.root, defaultextension=f".{ext}", initialfile=f"{base}.{ext}", filetypes=[(ext.upper(), f"*.{ext}")])
        if not path: return
        try:
            if ext == "png": self.figure.savefig(path, dpi=180, bbox_inches="tight")
            else:
                with PdfPages(path) as pdf: pdf.savefig(self.figure, bbox_inches="tight")
            messagebox.showinfo(self.main.t("export_success"), path, parent=self.main.root)
        except Exception as exc: self._error(exc)


class CauseEditorDialog(tk.Toplevel):
    """Multiline cause editor that keeps standard Text editing keys local."""
    def __init__(self, main, title, initial_value, on_save):
        super().__init__(main.root)
        self.main = main
        self.on_save = on_save
        self.title(title)
        self.transient(main.root)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.resizable(True, True)
        self.minsize(440, 260)
        self.geometry("620x380")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=main.t("cause_editor_guidance"), wraplength=560).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 8)
        )
        text_frame = ttk.Frame(self)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=16)
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.editor = tk.Text(text_frame, wrap="word", undo=True, maxundo=-1,
                              padx=8, pady=7, height=9, font=("Segoe UI", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.editor.yview)
        self.editor.configure(yscrollcommand=scrollbar.set)
        self.editor.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.editor.insert("1.0", initial_value)
        self.editor.mark_set("insert", "end-1c")
        self.editor.edit_reset()
        self.editor.bind("<Control-a>", self._select_all)
        self.editor.bind("<Control-A>", self._select_all)
        self.editor.bind("<Control-z>", self._undo)
        self.editor.bind("<Control-Z>", self._undo)
        self.editor.bind("<Control-y>", self._redo)
        self.editor.bind("<Control-Y>", self._redo)
        self.editor.bind("<Control-Shift-z>", self._redo)
        self.editor.bind("<Control-Return>", self.save)
        self.editor.bind("<Escape>", self.cancel)

        actions = ttk.Frame(self)
        actions.grid(row=2, column=0, sticky="e", padx=16, pady=14)
        ttk.Button(actions, text=main.t("cancel"), command=self.cancel).pack(side="right", padx=(8, 0))
        ttk.Button(actions, text=main.t("save"), command=self.save).pack(side="right")
        self.grab_set()
        self.after_idle(self._focus_editor)

    def _focus_editor(self):
        try:
            self.editor.focus_force()
            self.editor.mark_set("insert", "end-1c")
        except tk.TclError:
            pass

    def _select_all(self, _event=None):
        self.editor.tag_add("sel", "1.0", "end-1c")
        self.editor.mark_set("insert", "end-1c")
        self.editor.see("insert")
        return "break"

    def _undo(self, _event=None):
        try:
            self.editor.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def _redo(self, _event=None):
        try:
            self.editor.edit_redo()
        except tk.TclError:
            pass
        return "break"

    def save(self, _event=None):
        value = self.editor.get("1.0", "end-1c")
        try:
            self.on_save(value)
        except ValueError as exc:
            key = {"Cause is required": "validation_cause_required"}.get(str(exc))
            messagebox.showerror(self.main.t("error"), self.main.t(key) if key else str(exc), parent=self)
            return "break"
        self.destroy()
        return "break"

    def cancel(self, _event=None):
        self.destroy()
        return "break"


class CategoryTextDialog:
    """Small synchronous text prompt for category names, preserving current flow."""
    def __init__(self, main, title, initial_value):
        self.value = None
        dialog = tk.Toplevel(main.root)
        dialog.title(title)
        dialog.transient(main.root)
        dialog.grab_set()
        dialog.columnconfigure(0, weight=1)
        ttk.Label(dialog, text=main.t("category")).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 5))
        entry = ttk.Entry(dialog, width=42)
        entry.grid(row=1, column=0, sticky="ew", padx=12)
        entry.insert(0, initial_value)
        actions = ttk.Frame(dialog)
        actions.grid(row=2, column=0, sticky="e", padx=12, pady=12)
        def finish(value):
            self.value = value
            dialog.destroy()
        ttk.Button(actions, text=main.t("cancel"), command=lambda: finish(None)).pack(side="right", padx=(8, 0))
        ttk.Button(actions, text=main.t("ok"), command=lambda: finish(entry.get())).pack(side="right")
        entry.bind("<Return>", lambda _event: finish(entry.get()))
        entry.bind("<Escape>", lambda _event: finish(None))
        dialog.protocol("WM_DELETE_WINDOW", lambda: finish(None))
        dialog.after_idle(entry.focus_force)
        dialog.wait_window()


class CategoryPicker(tk.Toplevel):
    def __init__(self, parent, title, values):
        super().__init__(parent); self.title(title); self.transient(parent); self.grab_set(); self.value=None
        self.choice=ttk.Combobox(self, values=values, state="readonly"); self.choice.pack(padx=14,pady=12); self.choice.current(0)
        ttk.Button(self,text=parent.master.t("ok") if hasattr(parent,"master") and hasattr(parent.master,"t") else "OK",command=self._ok).pack(pady=(0,12)); self.wait_window(self)
    def _ok(self): self.value=self.choice.current(); self.destroy()


class CheckSheetView(ToolView):
    def __init__(self, main):
        super().__init__(main, "check_sheet", "check_sheet", "check_sheet_help")
        self.model = main.tool_models.setdefault("check_sheet", CheckSheetModel())
        self._build(); self.refresh()
    def _build(self):
        bar=tk.Frame(self,bg="white");bar.pack(fill="x",padx=14,pady=10)
        for text,command in (("add_category",self.add_category),("rename_category",self.rename_category),("delete_category",self.delete_category),("add_record",self.add_record),("edit_record",self.edit_record),("delete_record",self.delete_record),("clear_records",self.clear_records)):
            ttk.Button(bar,text=self.main.t(text),command=command).pack(side="left",padx=3)
        body=tk.Frame(self,bg="white");body.pack(fill="both",expand=True,padx=14,pady=6)
        self.tree=ttk.Treeview(body,columns=("date","item","category","count","notes"),show="headings",height=12)
        labels=("date","observation","category","count","notes")
        for key,label in zip(self.tree["columns"],labels): self.tree.heading(key,text=self.main.t(key));self.tree.column(key,width=130)
        self.tree.pack(side="left",fill="both",expand=True)
        self.figure,self.ax=plt.subplots(figsize=(4.2,3.4))
        self.chart=FigureCanvasTkAgg(self.figure,master=body);self.chart.get_tk_widget().pack(side="right",fill="both",expand=True,padx=(10,0))
        self.summary=tk.Label(self,bg="white",anchor="w",justify="left");self.summary.pack(fill="x",padx=18,pady=10)
    def add_category(self):
        value=simpledialog.askstring(self.main.t("add_category"),self.main.t("category"),parent=self.main.root)
        if value is None:return
        try:self.model.add_category(value);self.refresh()
        except ValueError as exc:self._error(exc)
    def _pick_category(self, title):
        if not self.model.categories: return None
        picker=CategoryPicker(self.main.root,title,[c["name"] for c in self.model.categories])
        return None if picker.value is None else self.model.categories[picker.value]
    def rename_category(self):
        cat=self._pick_category(self.main.t("rename_category"))
        if not cat:return
        value=simpledialog.askstring(self.main.t("rename_category"),self.main.t("category"),initialvalue=cat["name"],parent=self.main.root)
        if value is None:return
        try:self.model.rename_category(cat["id"],value);self.refresh()
        except ValueError as exc:self._error(exc)
    def delete_category(self):
        cat=self._pick_category(self.main.t("delete_category"))
        if not cat:return
        if not messagebox.askyesno(self.main.t("delete_category"),self.main.t("confirm_delete_category"),parent=self.main.root):return
        try:self.model.delete_category(cat["id"]);self.refresh()
        except ValueError as exc:self._error(exc)
    def _record_dialog(self, record=None):
        if not self.model.categories:
            messagebox.showinfo(self.main.t("check_sheet"),self.main.t("add_category_first"),parent=self.main.root);return
        dialog=tk.Toplevel(self.main.root);dialog.title(self.main.t("add_record" if record is None else "edit_record"));dialog.transient(self.main.root);dialog.grab_set()
        fields={}
        initial=(record or {})
        names=(("date",self.main.t("date")),("item",self.main.t("observation")),("count",self.main.t("count")),("notes",self.main.t("notes")))
        for row,(key,label) in enumerate(names):
            tk.Label(dialog,text=label).grid(row=row,column=0,sticky="w",padx=8,pady=5);v=tk.StringVar(value=str(initial.get(key,"")));ttk.Entry(dialog,textvariable=v,width=36).grid(row=row,column=1,padx=8,pady=5);fields[key]=v
        tk.Label(dialog,text=self.main.t("category")).grid(row=4,column=0,sticky="w",padx=8,pady=5)
        cats=self.model.categories;combo=ttk.Combobox(dialog,state="readonly",values=[c["name"] for c in cats]);combo.grid(row=4,column=1,padx=8,pady=5,sticky="ew")
        selected=next((i for i,c in enumerate(cats) if c["id"]==initial.get("category_id")),0);combo.current(selected)
        def save():
            try:
                if record is None:self.model.add_record(cats[combo.current()]["id"],fields["count"].get(),fields["date"].get(),fields["item"].get(),fields["notes"].get())
                else:self.model.edit_record(record["id"],category_id=cats[combo.current()]["id"],count=fields["count"].get(),date=fields["date"].get(),item=fields["item"].get(),notes=fields["notes"].get())
            except (ValueError,IndexError) as exc:self._error(exc);return
            dialog.destroy();self.refresh()
        ttk.Button(dialog,text=self.main.t("save"),command=save).grid(row=5,column=1,sticky="e",padx=8,pady=8)
    def add_record(self):self._record_dialog()
    def _selected(self):
        sel=self.tree.selection();return self.model._record(sel[0]) if sel else None
    def edit_record(self):
        record=self._selected()
        if record:self._record_dialog(record)
    def delete_record(self):
        record=self._selected()
        if record:self.model.delete_record(record["id"]);self.refresh()
    def clear_records(self):
        if self.model.records and messagebox.askyesno(self.main.t("clear_records"),self.main.t("confirm_clear_records"),parent=self.main.root):self.model.clear();self.refresh()
    def refresh(self):
        if not hasattr(self,"tree"):return
        self.tree.delete(*self.tree.get_children())
        names={c["id"]:c["name"] for c in self.model.categories}
        for r in self.model.records:self.tree.insert("","end",iid=r["id"],values=(r["date"],r["item"],names[r["category_id"]],r["count"],r["notes"]))
        totals=self.model.totals
        self.summary.configure(text=(self.main.t("empty_check_sheet") if not self.model.records else "   •   ".join(f'{names[cid]}: {total}' for cid,total in totals.items())+f'     |     {self.main.t("grand_total")}: {self.model.grand_total}'))
        self.ax.clear()
        labels=[c["name"] for c in self.model.categories]
        values=[totals[c["id"]] for c in self.model.categories]
        self.ax.bar(range(len(labels)),values,color="#3b82f6")
        self.ax.set_xticks(range(len(labels)),labels,rotation=35,ha="right")
        self.ax.set_ylabel(self.main.t("count"));self.ax.set_title(self.main.t("defect_frequency"))
        self.figure.tight_layout();self.chart.draw_idle()


class DefectConcentrationView(ToolView):
    COLORS=("#2563eb","#dc2626","#16a34a","#9333ea","#ea580c","#0891b2")
    MARKERS=("o","s","^","D","P","X")
    def __init__(self,main):
        super().__init__(main,"defect_concentration","defect_concentration","defect_concentration_help")
        self.model=main.tool_models.setdefault("defect_concentration",DefectConcentrationModel())
        self._build();self.refresh()
    def _build(self):
        bar=tk.Frame(self,bg="white");bar.pack(fill="x",padx=14,pady=10)
        ttk.Button(bar,text=self.main.t("add_category"),command=self.add_category).pack(side="left")
        ttk.Button(bar,text=self.main.t("rename_category"),command=self.rename_category).pack(side="left",padx=3)
        ttk.Button(bar,text=self.main.t("delete_category"),command=self.delete_category).pack(side="left")
        self.category=ttk.Combobox(bar,state="readonly",width=24);self.category.pack(side="left",padx=8)
        ttk.Button(bar,text=self.main.t("edit_mark"),command=self.edit_mark).pack(side="left",padx=3)
        ttk.Button(bar,text=self.main.t("delete_mark"),command=self.delete_mark).pack(side="left")
        self.total_label=tk.Label(bar,bg="white");self.total_label.pack(side="right")
        ttk.Button(bar,text="PNG",command=lambda:self.export("png")).pack(side="right",padx=4)
        ttk.Button(bar,text="PDF",command=lambda:self.export("pdf")).pack(side="right")
        self.figure,self.ax=plt.subplots(figsize=(8,5));self.canvas=FigureCanvasTkAgg(self.figure,master=self);self.canvas.get_tk_widget().pack(fill="both",expand=True,padx=10,pady=5)
        self.canvas.mpl_connect("button_press_event",self._click)
        self.selected_mark_id=None
        self.legend=tk.Label(self,bg="white",anchor="w");self.legend.pack(fill="x",padx=14,pady=8)
    def add_category(self):
        value=simpledialog.askstring(self.main.t("add_category"),self.main.t("category"),parent=self.main.root)
        if value is None:return
        try:self.model.add_category(value);self.refresh()
        except ValueError as exc:self._error(exc)
    def rename_category(self):
        if not self.model.categories:return
        idx=self.category.current()
        if idx<0:return
        cat=self.model.categories[idx];value=simpledialog.askstring(self.main.t("rename_category"),self.main.t("category"),initialvalue=cat["name"],parent=self.main.root)
        if value is None:return
        try:self.model.rename_category(cat["id"],value);self.refresh()
        except ValueError as exc:self._error(exc)
    def delete_category(self):
        if len(self.model.categories)<2:return
        idx=self.category.current()
        if idx<0:return
        cat=self.model.categories[idx]
        prompt = self.main.t("confirm_delete_category")
        fallback = next((c for c in self.model.categories if c["id"] != cat["id"]), None)
        if fallback and any(m["category_id"] == cat["id"] for m in self.model.marks):
            prompt = self.main.t("confirm_reassign_category").format(category=fallback["name"])
        if not messagebox.askyesno(self.main.t("delete_category"),prompt,parent=self.main.root):return
        fallback_id=fallback["id"] if fallback else None
        try:self.model.delete_category(cat["id"],reassign_to=fallback_id);self.refresh()
        except ValueError as exc:self._error(exc)
    def _click(self,event):
        if event.inaxes is not self.ax or event.xdata is None:return
        try:
            if self.selected_mark_id is None and self.model.marks:
                points=[(m,self.ax.transData.transform((.12+m["x"]*.76,.08+m["y"]*.84))) for m in self.model.marks]
                nearest,distance=min(points,key=lambda pair:(pair[1][0]-event.x)**2+(pair[1][1]-event.y)**2)
                if (distance[0]-event.x)**2+(distance[1]-event.y)**2 < 18**2:
                    self.selected_mark_id=nearest["id"];self.refresh();return
            if not (.12 <= event.xdata <= .88 and .08 <= event.ydata <= .92):
                raise ValueError(self.main.t("location_inside_object"))
            x=(event.xdata-.12)/.76; y=(event.ydata-.08)/.84
            idx=self.category.current()
            if idx<0:raise ValueError(self.main.t("select_category"))
            if self.selected_mark_id:
                self.model.edit_mark(self.selected_mark_id,category_id=self.model.categories[idx]["id"],x=float(x),y=float(y))
                self.selected_mark_id=None
            else:self.model.add_mark(self.model.categories[idx]["id"],float(x),float(y))
            self.refresh()
        except ValueError as exc:self._error(exc)
    def export(self,ext):
        path=filedialog.asksaveasfilename(parent=self.main.root,defaultextension=f".{ext}",initialfile=f"defect_concentration.{ext}",filetypes=[(ext.upper(),f"*.{ext}")])
        if not path:return
        try:
            if ext=="png":self.figure.savefig(path,dpi=180,bbox_inches="tight")
            else:
                with PdfPages(path) as pdf:pdf.savefig(self.figure,bbox_inches="tight")
            messagebox.showinfo(self.main.t("export_success"),path,parent=self.main.root)
        except Exception as exc:self._error(exc)
    def delete_mark(self):
        if not self.selected_mark_id:
            messagebox.showinfo(self.main.t("defect_concentration"),self.main.t("select_mark_first"),parent=self.main.root)
            return
        mark=next((m for m in self.model.marks if m["id"]==self.selected_mark_id),None)
        if mark is None:return
        self.model.delete_mark(mark["id"]);self.selected_mark_id=None;self.refresh()
    def edit_mark(self):
        if not self.selected_mark_id:
            messagebox.showinfo(self.main.t("defect_concentration"),self.main.t("select_mark_first"),parent=self.main.root)
            return
        mark=next((m for m in self.model.marks if m["id"]==self.selected_mark_id),None)
        if mark is None:return
        picker=CategoryPicker(self.main.root,self.main.t("category"),[c["name"] for c in self.model.categories])
        if picker.value is None:return
        note=simpledialog.askstring(self.main.t("notes"),self.main.t("notes"),initialvalue=mark["note"],parent=self.main.root)
        if note is not None:self.model.edit_mark(mark["id"],category_id=self.model.categories[picker.value]["id"],note=note);self.selected_mark_id=mark["id"];self.refresh()
    def refresh(self):
        if not hasattr(self,"ax"):return
        cats=self.model.categories;self.category.configure(values=[c["name"] for c in cats])
        if cats and self.category.current()<0:self.category.current(0)
        self.ax.clear();self.ax.set_xlim(0,1);self.ax.set_ylim(0,1);self.ax.set_aspect("equal");self.ax.set_xticks([]);self.ax.set_yticks([])
        self.ax.add_patch(FancyBboxPatch((.12,.08),.76,.84,boxstyle="round,pad=.02",fc="#f8fafc",ec="#475569",lw=2))
        self.ax.add_patch(Ellipse((.5,.5),.40,.56,fc="#e2e8f0",ec="#64748b",lw=1.4))
        self.ax.text(.5,.5,self.main.t("object_template"),ha="center",va="center",color="#475569",fontsize=9)
        for mark in self.model.marks:
            i=next(i for i,c in enumerate(cats) if c["id"]==mark["category_id"])
            x=.12+mark["x"]*.76; y=.08+mark["y"]*.84
            self.ax.scatter(x,y,s=90,c=self.COLORS[i%len(self.COLORS)],marker=self.MARKERS[i%len(self.MARKERS)],edgecolors="white",linewidths=1,zorder=5)
            if mark["id"]==self.selected_mark_id:self.ax.scatter(x,y,s=175,facecolors="none",edgecolors="#0f172a",linewidths=1.5,zorder=6)
        counts=self.model.counts
        self.total_label.configure(text=f'{self.main.t("defect_total")}: {self.model.total}')
        legend_text="   •   ".join(f'{c["name"]} ({counts[c["id"]]})  {self.MARKERS[i%len(self.MARKERS)]}' for i,c in enumerate(cats))
        self.legend.configure(text=legend_text)
        handles=[self.ax.scatter([],[],s=70,c=self.COLORS[i%len(self.COLORS)],marker=self.MARKERS[i%len(self.MARKERS)],label=f'{c["name"]} ({counts[c["id"]]})') for i,c in enumerate(cats)]
        self.ax.legend(handles=handles,loc="upper center",bbox_to_anchor=(.5,-.02),ncol=max(1,min(3,len(handles))),frameon=False)
        self.ax.set_title(f'{self.main.t("defect_total")}: {self.model.total}')
        self.figure.subplots_adjust(left=.04,right=.96,top=.91,bottom=.20);self.canvas.draw_idle()

