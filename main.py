"""SIKPRO application entry point."""
import os
import sys
import tkinter as tk
from core.lang import LANG

from ui.launcher import ApplicationLauncher
from ui.inventory_view import InventoryApplication
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
    app_state = {"app": None, "theme_manager": None}

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

    def show_launcher(manager=None):
        for child in root.winfo_children():
            if isinstance(child, tk.Toplevel):
                child.destroy()
            elif child is not root:
                child.destroy()
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        launcher = ApplicationLauncher(root, open_spc, open_layout=open_layout,
                                       open_inventory=open_inventory)
        if manager is not None:
            launcher.theme_manager = manager
            manager.main = launcher
            launcher.current_lang = manager.language
            launcher.lang_data = LANG[manager.language]
            launcher.build()
        app_state["theme_manager"] = launcher.theme_manager
        return launcher

    def return_to_launcher(app):
        manager = app.theme_manager
        show_launcher(manager)

    def close_spc():
        app = app_state["app"]
        if app is None or app.confirm_close():
            root.destroy()

    def open_spc(theme_manager):
        app = MainPage(root, theme_manager=theme_manager)
        app_state["app"] = app
        app.set_on_back(lambda: return_to_launcher(app))
        root.protocol("WM_DELETE_WINDOW", close_spc)
        return app

    def open_layout(theme_manager):
        app = LayoutApplication(root, theme_manager=theme_manager)
        app.set_on_back(lambda: return_to_launcher(app))
        root.protocol("WM_DELETE_WINDOW", app.request_close)
        app_state["layout"] = app
        return app

    def open_inventory(theme_manager):
        app = InventoryApplication(root, theme_manager=theme_manager)
        app.set_on_back(lambda: return_to_launcher(app))
        root.protocol("WM_DELETE_WINDOW", lambda: return_to_launcher(app))
        app_state["inventory"] = app
        return app

    show_launcher()
    root.mainloop()


if __name__ == "__main__":
    main()
