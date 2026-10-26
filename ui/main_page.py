import tkinter as tk
from ui.ui import UI
from core.lang import LANG
from ui.sheet import Sheet

class MainPage:
    def __init__(self, root):
        self.root = root

        self.root.title("SPC App")
        self.root.state("zoomed")

        self.current_lang = "en"
        self.lang_data = LANG[self.current_lang]

        self.sheet = Sheet(self)
        self.analysis_objects=[]

        self.ui = UI(self)
        self.ui.build()
        
    def t(self, key):
        return self.lang_data.get(key, key)
        
    def set_lang(self, lang):
        
        sheet_data = self.sheet.get_sheet_data()

        analysis_data = self.analysis_objects

        self.current_lang = lang
        self.lang_data = LANG[lang]

        for widget in self.root.winfo_children():
            widget.destroy()

        self.sheet = Sheet(self)
        self.ui = UI(self)

        self.ui.build()

        self.sheet.set_sheet_data(sheet_data)
        self.sheet.update_headers()

        self.analysis_objects = analysis_data

        for analysis in self.analysis_objects:
            self.navigator.add_analysis(
                        analysis,
                        save=False
                    )