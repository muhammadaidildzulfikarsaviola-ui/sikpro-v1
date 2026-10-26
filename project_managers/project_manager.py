import json
import os
import pprint
import textwrap
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ui.sheet import Sheet

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
            return

        self.clear_all()

        self.current_project_path = None

    def save_project(self):

        if not self.current_project_path:
            self.save_as_project()
            return

        self._write_project(self.current_project_path)

    def save_as_project(self):

        filepath = filedialog.asksaveasfilename(
            defaultextension=".spcproj",
            filetypes=[
                ("SPC Project", "*.spcproj")
            ]
        )

        if not filepath:
            return

        self.current_project_path = filepath

        self._write_project(filepath)

    def load_project(self):

        filepath = filedialog.askopenfilename(
            filetypes=[
                ("SPC Project", "*.spcproj")
            ]
        )

        if not filepath:
            return

        with open(filepath, "r") as file:
            project_data = json.load(file)

        self.clear_all()

        from models.analysis import Analysis

        for analysis_data in project_data["analyses"]:

            analysis = Analysis(
                analysis_type=analysis_data["analysis_type"],
                title=analysis_data["title"],
                data=analysis_data["data"],
                stats=analysis_data["stats"],
                settings=analysis_data["settings"],
                navigator_name=analysis_data.get(
                    "navigator_name",
                    "Unknown Analysis"
                )
            )

            self.main.navigator.add_analysis(analysis)

        sheet_data = project_data["sheet_data"]

        self.main.sheet.set_sheet_data(sheet_data)

        self.current_project_path = filepath

        messagebox.showinfo(
            self.main.t("load_project"),
            self.main.t("project_load_success")
        )

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

        self.main.sheet.set_sheet_data(data)

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

    def _write_project(self, filepath):

        project_data = {

            "analyses": [
                analysis.to_dict()
                for analysis in self.main.analysis_objects
            ],

            "sheet_data": self.main.sheet.get_sheet_data()

        }

        with open(filepath, "w") as file:
            json.dump(project_data, file)

        messagebox.showinfo(
            self.main.t("save_project"),
            self.main.t("project_saved_success")
        )

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
