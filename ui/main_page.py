import tkinter as tk
from types import SimpleNamespace
from ui.ui import UI
from core.lang import LANG
from ui.sheet import Sheet
from ui.theme import ThemeManager
from models.quality_tools import default_tool_models

class MainPage:
    def __init__(self, root):
        self.root = root

        self.root.title("SPC App")
        self.root.state("zoomed")

        self.current_lang = "en"
        self.lang_data = LANG[self.current_lang]
        self.theme_manager = ThemeManager(self)

        self.sheet = Sheet(self)
        self.analysis_objects=[]
        self.tool_models = default_tool_models(self.current_lang)

        self.ui = UI(self)
        self.ui.build()
        
    def t(self, key):
        return self.lang_data.get(key, key)

    def set_theme(self, theme):
        self.theme_manager.set_theme(theme)
        
    def set_lang(self, lang):

        selected_chart_index = None
        selected_tool = None
        if self.ui.active_chart_view is not None:
            selected_tool = getattr(self.ui.active_chart_view, "tool_key", None)
            if selected_tool is None:
                selected = self.ui.navigator_box.curselection()
                if selected:
                    selected_chart_index = selected[0]
        
        sheet_data = self.sheet.get_sheet_data()
        sheet_headers = self.sheet.get_column_names()

        analysis_data = self.analysis_objects

        self.current_lang = lang
        self.lang_data = LANG[lang]
        fishbone_model = self.tool_models.get("fishbone")
        if fishbone_model is not None:
            fishbone_model.set_language(lang)
        concentration_model = self.tool_models.get("defect_concentration")
        if concentration_model is not None:
            concentration_model.set_language(lang)

        for widget in self.root.winfo_children():
            widget.destroy()

        self.sheet = Sheet(self)
        self.ui = UI(self)

        self.ui.build()

        self.sheet.set_sheet_data_with_headers(sheet_data, sheet_headers)

        self.analysis_objects = analysis_data

        for analysis in self.analysis_objects:
            self.navigator.add_analysis(
                        analysis,
                        save=False
                    )

        if selected_chart_index is not None and selected_chart_index < len(self.analysis_objects):
            self.navigator.navigator_box.selection_set(selected_chart_index)
            self.navigator.open_analysis(SimpleNamespace(y=0))
        elif selected_tool:
            {"fishbone": self.ui.open_fishbone,
             "check_sheet": self.ui.open_check_sheet,
             "defect_concentration": self.ui.open_defect_concentration,
             "help": self.ui.open_help}.get(selected_tool, lambda: None)()
