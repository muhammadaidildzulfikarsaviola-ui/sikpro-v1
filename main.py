import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import ctypes

from ui.main_page import MainPage
from ui.sheet import Sheet

def resource_path(relative_path):

    try:
        base_path = sys._MEIPASS

    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(
        base_path,
        relative_path
    )

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
    "sikpro.app.1.0"
)

root = tk.Tk()

root.withdraw()

current_file = None

is_saved = True

splash = tk.Toplevel()

splash.title("Loading...")

splash.geometry("400x200")

splash.overrideredirect(True)

screen_w = splash.winfo_screenwidth()
screen_h = splash.winfo_screenheight()

x = (screen_w // 2) - (400 // 2)
y = (screen_h // 2) - (200 // 2)

splash.geometry(
    f"400x200+{x}+{y}"
)

tk.Label(
    splash,
    text="Loading SIKPRO Application...",
    font=("Segoe UI", 14)
).pack(pady=40)

progress = ttk.Progressbar(
    splash,
    mode="indeterminate",
    length=250
)

progress.pack(pady=20)

progress.start()

def update_title():

    global current_file
    global is_saved

    title = "SIKPRO"

    if current_file:

        filename = os.path.basename(
            current_file
        )

        title += f" - {filename}"

    if not is_saved:

        title += " *"

    root.title(title)

def on_close():

    global is_saved

    if not is_saved:

        result = messagebox.askyesnocancel(
            "Unsaved Changes",
            "Data belum disimpan.\n\nSimpan sebelum keluar?"
        )

        if result is None:

            return

        elif result:

            try:

                app.save_file()

                root.destroy()

            except Exception as e:

                messagebox.showerror(
                    "Save Error",
                    str(e)
                )

        else:

            root.destroy()

    else:

        root.destroy()

def start_app():

    global app

    try:
        root.iconbitmap(
            resource_path(
                "assets\\app2.ico"
            )
        )

    except:
        pass

    try:

        icon = tk.PhotoImage(
            file=resource_path(
                "assets/app2.png"
            )
        )

        root.iconphoto(
            True,
            icon
        )

    except:
        pass

    app = MainPage(root)

    app.current_file = current_file

    app.is_saved = is_saved

    splash.destroy()

    root.deiconify()

    root.state("zoomed")

    update_title()

    root.protocol(
        "WM_DELETE_WINDOW",
        on_close
    )
root.after(
    2000,
    start_app
)

root.mainloop()