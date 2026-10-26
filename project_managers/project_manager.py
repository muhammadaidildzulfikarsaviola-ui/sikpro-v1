import json
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
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

        df = pd.read_excel(filepath)

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

    def generate_report(self,main):

        self.main = main

        self.withdraw()

        messagebox.showerror(
            "Under Maintenance",
            "Feature is currently under maintenance"
        )

        self.destroy()