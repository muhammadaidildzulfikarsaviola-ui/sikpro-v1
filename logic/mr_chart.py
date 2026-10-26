import tkinter as tk
from tkinter import ttk, messagebox


class MovingRangeConfigPopup(tk.Toplevel):

    def __init__(self, main):

        super().__init__(main.root)

        self.main = main

        self.withdraw()

        messagebox.showerror(
            "Under Maintenance",
            "Feature is currently under maintenance"
        )

        self.destroy()


class MovingRangeChartPopup(tk.Toplevel):

    def __init__(self, main):

        super().__init__(main.root)

        self.main = main

        self.withdraw()

        messagebox.showerror(
            "Under Maintenance",
            "Feature is currently under maintenance"
        )

        self.destroy()