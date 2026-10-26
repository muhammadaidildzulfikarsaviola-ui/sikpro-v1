"""Shared base for Matplotlib chart views hosted in the main workspace."""

import tkinter as tk


def favor_chart_panel(paned, ratio=0.82, minimum_results_width=220):
    """Give the chart most of the initial width while keeping results usable."""
    def position(event=None):
        if getattr(paned, "_chart_sash_initialized", False):
            return
        try:
            width = paned.winfo_width()
            if width <= 2 or len(paned.panes()) < 2:
                return
            right_width = max(minimum_results_width, int(width * (1 - ratio)))
            chart_width = min(width - 140, max(280, width - right_width))
            paned.sashpos(0, chart_width)
            paned._chart_sash_initialized = True
        except tk.TclError:
            return

    paned.bind("<Configure>", position, add="+")


class EmbeddedChartFrame(tk.Frame):
    def __init__(self, root, **kwargs):
        host = getattr(root, "_sikpro_chart_host", None)
        if host is None:
            raise RuntimeError("The SIKPRO chart workspace has not been initialized")
        host.prepare_chart_view()
        super().__init__(host.chart_canvas, **kwargs)
        self._chart_host = host
        self._window_title = ""
        self._close_handler = None
        self.pack(fill="both", expand=True)
        host.activate_chart_view(self)

    def title(self, value=None):
        if value is not None:
            self._window_title = value
            self._chart_host.set_chart_title(value)
        return self._window_title

    def state(self, value=None):
        # Retain Toplevel-compatible call sites while this view is a Frame.
        return "normal"

    def geometry(self, value=None):
        return ""

    def protocol(self, name=None, func=None):
        if name == "WM_DELETE_WINDOW":
            self._close_handler = func
        return self._close_handler

    def destroy(self):
        host = getattr(self, "_chart_host", None)
        try:
            super().destroy()
        finally:
            if host is not None:
                host.chart_view_destroyed(self)
