import json
import os
import pprint
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ui.sheet import Sheet
from models.quality_tools import (
    CheckSheetModel,
    DefectConcentrationModel,
    FishboneModel,
    default_tool_models,
)

class ProjectManager:
    
    def __init__(self, main):
        self.main = main
        self.main.sheet
        self.current_project_path = None
        self.main.analysis_objects


    def new_project(self):

        confirm = messagebox.askyesno(
            self.main.t("new_project"),
            self.main.t("clear_current_project")
        )

        if not confirm:
            return False

        self.clear_all()

        self.current_project_path = None
        return True

    def save_project(self):

        if not self.current_project_path:
            return self.save_as_project()
        try:
            self._write_project(self.current_project_path)
            return True
        except Exception as exc:
            messagebox.showerror(self.main.t("save"), f"Project save failed: {exc}", parent=self.main.root)
            return False

    def save_as_project(self):

        filepath = filedialog.asksaveasfilename(
            defaultextension=".spcproj",
            filetypes=[
                ("SPC Project", "*.spcproj")
            ]
        )

        if not filepath:
            return False
        try:
            self._write_project(filepath)
        except Exception as exc:
            messagebox.showerror(self.main.t("save_as"), f"Project save failed: {exc}", parent=self.main.root)
            return False
        self.current_project_path = filepath
        return True

    def load_project(self, filepath=None):
        if filepath is None:
            filepath = filedialog.askopenfilename(
                filetypes=[("SPC Project", "*.spcproj")]
            )
        if not filepath:
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                project_data = json.load(file)
            staged = self._stage_project(project_data)
            self._install_project(staged, filepath)
        except Exception as exc:
            messagebox.showerror(
                self.main.t("load_project"),
                f"Project could not be loaded: {exc}",
                parent=self.main.root,
            )
            return False

        messagebox.showinfo(
            self.main.t("load_project"),
            self.main.t("project_load_success"),
            parent=self.main.root,
        )
        return True

    def import_excel(self):

        filepath = filedialog.askopenfilename(
            filetypes=[
                ("Excel File", "*.xlsx")
            ]
        )

        if not filepath:
            return

        try:
            df = pd.read_excel(filepath, engine="openpyxl")
            if df.empty or len(df.columns) == 0:
                raise ValueError("The selected workbook contains no tabular data")
        except Exception as exc:
            messagebox.showerror(
                self.main.t("import_excel"),
                f"Excel import failed: {exc}",
                parent=self.main.root,
            )
            return

        data = df.values.tolist()
        headers = [str(column).strip() for column in df.columns]

        self.main.sheet.set_sheet_data_with_headers(data, headers)

        messagebox.showinfo(
            self.main.t("import_excel"),
            self.main.t("import_excel_success")
        )

    def export_pdf(self):

        messagebox.showinfo(
            self.main.t("export_pdf"),
            self.main.t("feature_under_development")
        )

    def clear_all(self):

        self.main.analysis_objects.clear()

        self.main.navigator.navigator_box.delete(0, tk.END)

        self.main.sheet.clear()
        self.main.tool_models = default_tool_models(self.main.current_lang)

    def _write_project(self, filepath):
        project_data = {
            "analyses": [
                analysis.to_dict()
                for analysis in self.main.analysis_objects
            ],
            "sheet_data": self.main.sheet.get_sheet_data(),
            "sheet_headers": self.main.sheet.get_column_names(),
            "tool_models": self._serialize_tool_models(),
        }
        # Serialize before touching the destination. Write to a sibling file so
        # os.replace is atomic on supported filesystems and never fall back to
        # truncating the last valid project in place.
        serialized = json.dumps(project_data)
        target = Path(filepath)
        fd, temporary = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent or Path("."))
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                stream.write(serialized)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        messagebox.showinfo(
            self.main.t("save_project"),
            self.main.t("project_saved_success"),
            parent=self.main.root,
        )
        return True

    def _serialize_tool_models(self):
        current = getattr(self.main, "tool_models", None)
        if not isinstance(current, dict):
            raise ValueError("Quality tool models are invalid")
        defaults = default_tool_models(self.main.current_lang)
        models = {key: current.get(key, default) for key, default in defaults.items()}
        expected = {
            "fishbone": FishboneModel,
            "check_sheet": CheckSheetModel,
            "defect_concentration": DefectConcentrationModel,
        }
        language = getattr(self.main, "current_lang", "en")
        validators = {
            "fishbone": lambda value: FishboneModel.from_dict(value, language),
            "check_sheet": CheckSheetModel.from_dict,
            "defect_concentration": lambda value: DefectConcentrationModel.from_dict(value, language),
        }
        payload = {}
        for key, model_type in expected.items():
            model = models[key]
            if not isinstance(model, model_type):
                raise ValueError(f"Invalid {key} quality tool model")
            payload[key] = model.to_dict()
            validators[key](payload[key])
        return payload

    def _stage_project(self, project_data):
        """Validate and build all project state before mutating the live session."""
        if not isinstance(project_data, dict):
            raise ValueError("Project root must be an object")
        if not isinstance(project_data.get("analyses"), list):
            raise ValueError("Project analyses must be a list")
        sheet_data = project_data.get("sheet_data")
        if not isinstance(sheet_data, list) or any(not isinstance(row, list) for row in sheet_data):
            raise ValueError("Project sheet_data must be a list of rows")
        for row in sheet_data:
            if any(not isinstance(cell, (str, int, float, bool, type(None))) for cell in row):
                raise ValueError("Project sheet cells must contain JSON scalar values")
        sheet_headers = project_data.get("sheet_headers")
        if sheet_headers is not None:
            if (not isinstance(sheet_headers, list)
                    or any(not isinstance(header, str) for header in sheet_headers)):
                raise ValueError("Project sheet_headers must be a list of strings")
            column_count = max((len(row) for row in sheet_data), default=0)
            if len(sheet_headers) < column_count:
                raise ValueError("Project sheet_headers must cover the worksheet columns")

        from models.analysis import Analysis
        analyses = []
        for index, value in enumerate(project_data["analyses"]):
            if not isinstance(value, dict):
                raise ValueError(f"Project analysis {index + 1} must be an object")
            required = ("analysis_type", "title", "data", "stats", "settings")
            if any(key not in value for key in required):
                raise ValueError(f"Project analysis {index + 1} is incomplete")
            if not isinstance(value["analysis_type"], str) or not isinstance(value["title"], str):
                raise ValueError(f"Project analysis {index + 1} has invalid labels")
            navigator_name = value.get("navigator_name", "Unknown Analysis")
            if not isinstance(navigator_name, str):
                raise ValueError(f"Project analysis {index + 1} has invalid navigator name")
            analyses.append(Analysis(
                analysis_type=value["analysis_type"],
                title=value["title"],
                data=value["data"],
                stats=value["stats"],
                settings=value["settings"],
                navigator_name=navigator_name,
            ))

        # Older project files have no tool_models field. Each omitted model is
        # initialized to its ordinary empty/default state.
        model_data = project_data.get("tool_models", {})
        if not isinstance(model_data, dict):
            raise ValueError("Project tool_models must be an object")
        language = getattr(self.main, "current_lang", "en")
        defaults = default_tool_models(language)
        model_readers = {
            "fishbone": lambda data: FishboneModel.from_dict(data, language),
            "check_sheet": CheckSheetModel.from_dict,
            "defect_concentration": lambda data: DefectConcentrationModel.from_dict(data, language),
        }
        restored_models = {}
        for key, default in defaults.items():
            restored_models[key] = model_readers[key](model_data[key]) if key in model_data else default
        return {
            "analyses": analyses,
            "sheet_data": sheet_data,
            "sheet_headers": sheet_headers,
            "tool_models": restored_models,
        }

    def _install_project(self, staged, filepath):
        old_sheet = self.main.sheet.get_sheet_data()
        old_headers = self.main.sheet.get_column_names()
        old_analyses = self.main.analysis_objects
        old_models = self.main.tool_models
        old_path = self.current_project_path
        navigator_box = self.main.navigator.navigator_box
        try:
            if staged["sheet_headers"] is None:
                self.main.sheet.set_sheet_data(staged["sheet_data"])
            else:
                self.main.sheet.set_sheet_data_with_headers(
                    staged["sheet_data"], staged["sheet_headers"]
                )
            self.main.analysis_objects = []
            self.main.tool_models = staged["tool_models"]
            navigator_box.delete(0, tk.END)
            for analysis in staged["analyses"]:
                self.main.navigator.add_analysis(analysis)
            self.current_project_path = filepath
        except Exception:
            self.main.sheet.set_sheet_data_with_headers(old_sheet, old_headers)
            self.main.analysis_objects = old_analyses
            self.main.tool_models = old_models
            self.current_project_path = old_path
            navigator_box.delete(0, tk.END)
            for analysis in old_analyses:
                self.main.navigator.add_analysis(analysis, save=False)
            raise

    def generate_report(self, main=None):
        """Export the active analysis history to a text-based PDF report."""
        if main is not None:
            self.main = main
        analyses = list(self.main.analysis_objects)
        if not analyses:
            messagebox.showerror(
                self.main.t("export_pdf"),
                "There are no saved analyses to export.",
                parent=self.main.root,
            )
            return

        filepath = filedialog.asksaveasfilename(
            parent=self.main.root,
            title=self.main.t("export_pdf"),
            defaultextension=".pdf",
            filetypes=[("PDF file", "*.pdf")],
        )
        if not filepath:
            return
        if not filepath.lower().endswith(".pdf"):
            filepath += ".pdf"
        if os.path.exists(filepath) and not messagebox.askyesno(
            self.main.t("export_pdf"),
            "The selected file already exists. Replace it?",
            parent=self.main.root,
        ):
            return

        try:
            self._write_report_pdf(filepath, analyses)
        except Exception as exc:
            messagebox.showerror(
                self.main.t("export_pdf"),
                f"PDF export failed: {exc}",
                parent=self.main.root,
            )
            return

        messagebox.showinfo(
            self.main.t("export_pdf"),
            f"Report exported to:\n{filepath}",
            parent=self.main.root,
        )

    @staticmethod
    def _write_report_pdf(filepath, analyses):
        if not analyses:
            raise ValueError("There are no analyses to include")

        with PdfPages(filepath) as pdf:
            info = pdf.infodict()
            info["Title"] = "SIKPRO Statistical Process Control Report"
            info["Author"] = "SIKPRO"
            info["CreationDate"] = datetime.now()

            title_lines = [
                "SIKPRO — Statistical Process Control Report",
                f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}",
                f"Saved analyses: {len(analyses)}",
                "",
                "This report contains the analysis data, statistics, and settings saved in the current session.",
                "Charts and Nelson Rule signals are included only when stored in the analysis record.",
            ]
            ProjectManager._write_pdf_page(pdf, "SIKPRO Report", title_lines)

            for index, analysis in enumerate(analyses, start=1):
                fields = [
                    ("Analysis type", getattr(analysis, "analysis_type", "Unknown")),
                    ("Title", getattr(analysis, "title", "Untitled")),
                    ("Name", getattr(analysis, "navigator_name", "")),
                    ("Statistics", getattr(analysis, "stats", {})),
                    ("Settings", getattr(analysis, "settings", {})),
                    ("Data", getattr(analysis, "data", None)),
                ]
                lines = []
                for label, value in fields:
                    rendered = pprint.pformat(value, width=88, sort_dicts=False)
                    lines.append(f"{label}:")
                    for paragraph in rendered.splitlines() or [""]:
                        wrapped = textwrap.wrap(
                            paragraph,
                            width=96,
                            break_long_words=True,
                            break_on_hyphens=False,
                        ) or [""]
                        lines.extend(f"  {line}" for line in wrapped)
                    lines.append("")

                chunks = [lines[offset:offset + 44] for offset in range(0, len(lines), 44)]
                for part, chunk in enumerate(chunks, start=1):
                    title = f"Analysis {index}: {getattr(analysis, 'title', 'Untitled')}"
                    if len(chunks) > 1:
                        title += f" (page {part}/{len(chunks)})"
                    ProjectManager._write_pdf_page(pdf, title, chunk)

        with open(filepath, "rb") as report_file:
            if report_file.read(4) != b"%PDF":
                raise ValueError("Generated file is not a valid PDF document")

    @staticmethod
    def _write_pdf_page(pdf, title, lines):
        figure = plt.figure(figsize=(8.27, 11.69))
        try:
            figure.text(0.08, 0.95, str(title), fontsize=16, weight="bold", va="top")
            figure.text(
                0.08,
                0.91,
                "\n".join(str(line) for line in lines),
                fontsize=8.5,
                family="DejaVu Sans Mono",
                va="top",
                linespacing=1.25,
            )
            pdf.savefig(figure, bbox_inches="tight")
        finally:
            plt.close(figure)
