"""SIKPRO application entry point."""
import os
import sys
import tkinter as tk

from ui.launcher import ApplicationLauncher
from ui.layout_view import LayoutApplication
from ui.main_page import MainPage


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    root = tk.Tk()
    app_state = {"app": None}

    try:
        root.iconbitmap(resource_path("assets\\app2.ico"))
    except (tk.TclError, OSError):
        pass
    try:
        icon = tk.PhotoImage(file=resource_path("assets/app2.png"))
        root.iconphoto(True, icon)
        root._sikpro_icon = icon
    except (tk.TclError, OSError):
        pass

    def close_launcher():
        root.destroy()

    def close_spc():
        app = app_state["app"]
        if app is None or app.confirm_close():
            root.destroy()

    def open_spc(theme_manager):
        app = MainPage(root, theme_manager=theme_manager)
        app_state["app"] = app
        root.protocol("WM_DELETE_WINDOW", close_spc)
        return app

    def open_layout(theme_manager):
        app = LayoutApplication(root, theme_manager=theme_manager)
        app_state["layout"] = app
        return app

    root.protocol("WM_DELETE_WINDOW", close_launcher)
    ApplicationLauncher(root, open_spc, open_layout=open_layout)
    root.mainloop()


if __name__ == "__main__":
    main()
