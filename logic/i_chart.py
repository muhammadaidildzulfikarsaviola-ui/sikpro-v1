from tkinter import ttk, messagebox
import tkinter as tk

class IndividualConfigPopup(tk.Toplevel):
    
    def __init__(self, main):

        super().__init__(main.root)

        self.main = main

        self.withdraw()

        messagebox.showerror(
            "Under Maintenance",
            "Feature is currently under maintenance"
        )

        self.destroy()
class IndividualChartPopup(tk.Toplevel):

    def __init__(self, main):

        super().__init__(main.root)

        self.main = main

        self.withdraw()

        messagebox.showerror(
            "Under Maintenance",
            "Feature is currently under maintenance"
        )

        self.destroy()