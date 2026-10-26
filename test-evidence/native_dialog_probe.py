"""Probe the actual Windows common file dialog control tree for automation."""
import ctypes
from ctypes import wintypes
import os
import tkinter as tk
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ui.main_page import MainPage

u32 = ctypes.windll.user32
root = tk.Tk()
app = MainPage(root)
root.state("normal")
root.geometry("900x650+80+60")
root.update()

def inspect_dialog():
    found = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _):
        if not u32.IsWindowVisible(hwnd): return True
        title = ctypes.create_unicode_buffer(512)
        u32.GetWindowTextW(hwnd, title, 512)
        pid = wintypes.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if title.value:
            found.append((hwnd, pid.value, title.value))
        return True
    u32.EnumWindows(each, 0)
    dialog = next(((hwnd,title) for hwnd,pid,title in found if pid==os.getpid() and title.casefold() in ("open", "save as")), None)
    if not dialog:
        print("NO_COMMON_DIALOG", found)
    else:
        hwnd,title = dialog
        controls=[]
        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def child(ch, _):
            cls=ctypes.create_unicode_buffer(256); text=ctypes.create_unicode_buffer(512)
            u32.GetClassNameW(ch,cls,256); u32.GetWindowTextW(ch,text,512)
            controls.append((ch,cls.value,text.value))
            return True
        u32.EnumChildWindows(hwnd,child,0)
        print("DIALOG", title, "CONTROLS", controls)
        u32.PostMessageW(hwnd,0x0010,0,0)
    root.after(200, root.destroy)

root.after(500, inspect_dialog)
root.after(150, app.ui.project_manager.import_excel)
root.mainloop()
