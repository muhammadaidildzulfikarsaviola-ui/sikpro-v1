"""Shared ownership, placement, and native-dialog parenting for Tk dialogs."""
import ctypes
import re
import tkinter as tk
from ctypes import wintypes
from functools import wraps


def clamp_dialog_geometry(width, height, bounds, center):
    """Clamp a dialog to a monitor work area around the requested center."""
    left, top, right, bottom = bounds
    area_width, area_height = max(1, right - left), max(1, bottom - top)
    width, height = min(max(1, int(width)), area_width), min(max(1, int(height)), area_height)
    x = int(round(center[0] - width / 2))
    y = int(round(center[1] - height / 2))
    x = min(max(left, x), right - width)
    y = min(max(top, y), bottom - height)
    return width, height, x, y


def _windows_work_area(hwnd):
    if not hasattr(ctypes, "windll"):
        return None

    class MonitorInfo(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

    user32 = ctypes.windll.user32
    monitor = user32.MonitorFromWindow(wintypes.HWND(hwnd), 2)  # nearest monitor
    if not monitor:
        return None
    info = MonitorInfo()
    info.cbSize = ctypes.sizeof(info)
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return None
    area = info.rcWork
    return area.left, area.top, area.right, area.bottom


def _windows_window_rect(hwnd):
    if not hasattr(ctypes, "windll"):
        return None
    rect = wintypes.RECT()
    if not ctypes.windll.user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        return None
    return rect.left, rect.top, rect.right, rect.bottom


def _work_area(window, fallback):
    try:
        bounds = _windows_work_area(window.winfo_id())
        if bounds:
            return bounds
    except (AttributeError, OSError, tk.TclError):
        pass
    try:
        return (window.winfo_vrootx(), window.winfo_vrooty(),
                window.winfo_vrootx() + window.winfo_vrootwidth(),
                window.winfo_vrooty() + window.winfo_vrootheight())
    except tk.TclError:
        return fallback


def position_dialog(dialog, parent=None):
    """Center an application dialog on its parent's monitor and clamp it."""
    try:
        if not dialog.winfo_exists():
            return None
        dialog.update_idletasks()
        owner = parent
        if owner is None:
            owner = getattr(dialog, "master", None)
        try:
            owner = owner.winfo_toplevel() if owner is not None else None
        except tk.TclError:
            owner = None

        if owner is not None and owner.winfo_exists():
            try:
                owner_state = owner.state()
            except tk.TclError:
                owner_state = "withdrawn"
        else:
            owner_state = "withdrawn"

        if owner is not None and owner_state not in ("withdrawn", "iconic"):
            bounds = _work_area(owner, (0, 0, owner.winfo_screenwidth(), owner.winfo_screenheight()))
            owner_rect = _windows_window_rect(owner.winfo_id())
            if owner_rect:
                center = ((owner_rect[0] + owner_rect[2]) / 2,
                          (owner_rect[1] + owner_rect[3]) / 2)
            else:
                center = (owner.winfo_rootx() + owner.winfo_width() / 2,
                          owner.winfo_rooty() + owner.winfo_height() / 2)
        else:
            bounds = _work_area(dialog, (0, 0, dialog.winfo_screenwidth(), dialog.winfo_screenheight()))
            center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)

        geometry = dialog.geometry()
        match = re.match(r"(\d+)x(\d+)", geometry)
        width, height = (int(match.group(1)), int(match.group(2))) if match else (
            max(1, dialog.winfo_reqwidth()), max(1, dialog.winfo_reqheight()))
        width, height, x, y = clamp_dialog_geometry(width, height, bounds, center)
        try:
            if owner is not None and dialog.transient() == "":
                dialog.transient(owner)
        except tk.TclError:
            pass
        dialog.geometry(f"{width}x{height}{x:+d}{y:+d}")
        dialog.update_idletasks()
        actual_rect = _windows_window_rect(dialog.winfo_id())
        if actual_rect:
            desired_width = actual_rect[2] - actual_rect[0]
            desired_height = actual_rect[3] - actual_rect[1]
            target_x = min(max(bounds[0], int(round(center[0] - desired_width / 2))),
                           bounds[2] - desired_width)
            target_y = min(max(bounds[1], int(round(center[1] - desired_height / 2))),
                           bounds[3] - desired_height)
            x += target_x - actual_rect[0]
            y += target_y - actual_rect[1]
            dialog.geometry(f"{width}x{height}{x:+d}{y:+d}")
        return width, height, x, y
    except tk.TclError:
        return None


def deliver_result(dialog, create_result, *related_dialogs):
    """Create the result first; close its configuration chain only on success."""
    result = create_result()
    if result is None:
        raise RuntimeError("The result view was not created")
    for candidate in (dialog,) + related_dialogs:
        try:
            if candidate is not None and candidate.winfo_exists():
                candidate.destroy()
        except (AttributeError, tk.TclError):
            continue
    return result


def install_dialog_services(root):
    """Place Tk toplevels and parent native dialogs to the main application."""
    def on_map(event):
        window = event.widget
        if not isinstance(window, tk.Toplevel) or window is root:
            return
        if getattr(window, "_sikpro_position_scheduled", False):
            return
        window._sikpro_position_scheduled = True

        def place():
            try:
                if window.winfo_exists():
                    position_dialog(window, getattr(window, "master", None) or root)
            except tk.TclError:
                return

        try:
            window.after_idle(place)
        except tk.TclError:
            pass

    root.bind_all("<Map>", on_map, add="+")

    # Native dialogs are owned by the application window unless the caller
    # explicitly supplies another parent.
    from tkinter import filedialog, messagebox
    for module, names in ((messagebox, ("showinfo", "showwarning", "showerror", "askyesno", "askokcancel", "askretrycancel", "askyesnocancel")),
                          (filedialog, ("askopenfilename", "asksaveasfilename", "askopenfilenames", "askopenfile", "askopenfiles", "asksaveasfile", "askdirectory"))):
        for name in names:
            current = getattr(module, name)
            if getattr(current, "_sikpro_parent_wrapper", False):
                current._sikpro_parent_state["root"] = root
                continue
            parent_state = {"root": root}
            @wraps(current)
            def owned(*args, __original=current, __parent_state=parent_state, **kwargs):
                kwargs.setdefault("parent", __parent_state["root"])
                return __original(*args, **kwargs)
            owned._sikpro_parent_wrapper = True
            owned._sikpro_parent_state = parent_state
            setattr(module, name, owned)
