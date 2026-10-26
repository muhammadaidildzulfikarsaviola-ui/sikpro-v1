"""TkAgg canvas with frame-limited resize handling and safe teardown."""

import tkinter as tk
from weakref import WeakSet

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as _FigureCanvasTkAgg


def marker_stride(point_count, target_markers=200):
    """Skip dense point glyphs while retaining every observation in line data."""
    point_count = max(0, int(point_count))
    return max(1, (point_count + target_markers - 1) // target_markers)


class FigureCanvasTkAgg(_FigureCanvasTkAgg):
    """Debounce expensive Agg renders while keeping the Tk canvas current."""

    resize_debounce_ms = 50
    instances = WeakSet()

    def __init__(self, figure, master=None, **kwargs):
        self.resize_events = 0
        self.resize_applied = 0
        self._resize_draw_after_id = None
        self._handling_resize = False
        super().__init__(figure, master=master, **kwargs)
        self.instances.add(self)
        self._tkcanvas.bind("<Destroy>", self._cancel_pending_resize, add="+")

    def resize(self, event):
        self.resize_events += 1
        self._handling_resize = True
        try:
            # Keep the Tk image surface and figure dimensions in sync. The
            # expensive Agg draw is deferred by draw_idle below.
            super().resize(event)
            self.resize_applied += 1
        except tk.TclError:
            pass
        finally:
            self._handling_resize = False

    def draw_idle(self):
        if not self._handling_resize:
            return super().draw_idle()

        if self._resize_draw_after_id is not None:
            try:
                self._tkcanvas.after_cancel(self._resize_draw_after_id)
            except tk.TclError:
                self._resize_draw_after_id = None
        try:
            self._resize_draw_after_id = self._tkcanvas.after(
                self.resize_debounce_ms,
                self._draw_after_resize,
            )
        except tk.TclError:
            self._resize_draw_after_id = None

    def _draw_after_resize(self):
        self._resize_draw_after_id = None
        try:
            if self._tkcanvas.winfo_exists():
                super().draw_idle()
        except tk.TclError:
            return

    def _cancel_pending_resize(self, event=None):
        if event is not None and event.widget is not self._tkcanvas:
            return
        if self._resize_draw_after_id is not None:
            try:
                self._tkcanvas.after_cancel(self._resize_draw_after_id)
            except tk.TclError:
                pass
            self._resize_draw_after_id = None
        try:
            plt.close(self.figure)
        except (AttributeError, tk.TclError):
            pass
        idle_draw_id = getattr(self, "_idle_draw_id", None)
        if idle_draw_id is not None:
            try:
                self._tkcanvas.after_cancel(idle_draw_id)
            except tk.TclError:
                pass
            self._idle_draw_id = None
