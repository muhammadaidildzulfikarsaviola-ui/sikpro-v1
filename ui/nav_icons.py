"""Small Tk Canvas icons for the persistent navigation rail."""
import tkinter as tk


class NavButton(tk.Frame):
    def __init__(self, parent, kind, label, command, selected=False, enabled=True):
        self.enabled = enabled
        self.command = command
        self.kind = kind
        self.selected = selected
        self._palette = None
        self._bg = "#eaf2ff" if selected else "#f8fafc"
        self._fg = "#1d4ed8" if selected else ("#334155" if enabled else "#94a3b8")
        super().__init__(parent, bg=self._bg, cursor="hand2" if enabled else "arrow", height=38)
        self.pack_propagate(False)
        self.icon = tk.Canvas(self, width=22, height=22, bg=self._bg, highlightthickness=0)
        self.icon.pack(side="left", padx=(12, 10), pady=8)
        self.text = tk.Label(self, text=label, bg=self._bg, fg=self._fg,
                             font=("Segoe UI", 9), anchor="w")
        self.text.pack(side="left", fill="both", expand=True, padx=(0, 8))
        for widget in (self, self.icon, self.text):
            widget.bind("<Button-1>", self._invoke)
        self._draw()

    def _invoke(self, _event=None):
        if self.enabled and self.command:
            self.command()

    def configure(self, cnf=None, **kwargs):
        # UI selection updates use the same configure(bg=..., fg=...) contract
        # as the former text-only Tk buttons.
        bg = kwargs.pop("bg", kwargs.pop("background", None))
        fg = kwargs.pop("fg", kwargs.pop("foreground", None))
        if bg is not None:
            self._bg = bg
            self.selected = bg == "#eaf2ff"
            super().configure(bg=bg)
            self.icon.configure(bg=bg)
            self.text.configure(bg=bg)
        if fg is not None:
            self._fg = fg
            self.text.configure(fg=fg)
        if kwargs or cnf:
            super().configure(cnf, **kwargs)
        self._draw()

    config = configure

    def set_theme(self, palette):
        self._palette = palette
        self._bg = palette["selected"] if self.selected else palette["panel"]
        self._fg = palette["accent"] if self.selected else (palette["text_soft"] if self.enabled else palette["disabled"])
        tk.Frame.configure(self, bg=self._bg)
        self.icon.configure(bg=self._bg)
        self.text.configure(bg=self._bg, fg=self._fg)
        self._draw()

    def _draw(self):
        c = self.icon
        c.delete("all")
        color = self._fg if self.selected else (
            self._palette["muted"] if self._palette and self.enabled else
            self._palette["disabled"] if self._palette else
            ("#64748b" if self.enabled else "#94a3b8")
        )
        line = lambda *xy: c.create_line(*xy, fill=color, width=1.7, capstyle=tk.ROUND, joinstyle=tk.ROUND)
        rect = lambda x1,y1,x2,y2: c.create_rectangle(x1,y1,x2,y2,outline=color,width=1.6)
        oval = lambda x1,y1,x2,y2: c.create_oval(x1,y1,x2,y2,outline=color,width=1.6)
        k = self.kind
        if k == "grid":
            rect(2,3,20,19); line(8,3,8,19); line(14,3,14,19); line(2,8,20,8); line(2,13,20,13)
        elif k == "line_chart":
            line(3,3,3,19,20,19); line(5,15,9,11,13,13,19,5)
            for x,y in ((5,15),(9,11),(13,13),(19,5)): oval(x-1,y-1,x+1,y+1)
        elif k in ("bars", "pareto"):
            line(3,3,3,19,20,19)
            heights = (7,11,15) if k == "bars" else (14,10,6)
            for x,h in zip((6,11,16),heights): c.create_rectangle(x,19-h,x+3,19,outline=color,width=1.5)
            if k == "pareto": line(7,7,12,5,17,3)
        elif k == "scatter":
            line(3,3,3,19,20,19)
            for x,y in ((7,14),(10,9),(14,13),(17,5),(6,7),(15,8)): oval(x-1,y-1,x+1,y+1)
        elif k == "checklist":
            rect(5,2,19,20); line(8,7,10,9,13,5); line(14,7,17,7); line(8,13,10,15,13,11); line(14,13,17,13); line(8,18,17,18)
        elif k == "fishbone":
            line(2,11,19,11); line(19,11,16,8); line(19,11,16,14)
            for x,y in ((6,11),(10,11),(14,11)):
                line(x,y,x-3,y-4); line(x,y,x-3,y+4)
        elif k == "target":
            oval(2,2,20,20); oval(6,6,16,16); line(12,3,12,8); line(12,12,18,6); oval(10.5,10.5,13.5,13.5)
        elif k == "new":
            rect(5,2,17,20); line(8,7,14,7); line(8,10,14,10); line(8,15,12,15); line(16,13,16,19); line(13,16,19,16)
        elif k == "folder":
            line(2,6,8,6,10,8,20,8,18,18,3,18,2,6); line(3,9,19,9)
            line(8,13,15,13); line(13,11,15,13,13,15)
        elif k == "export":
            rect(3,10,19,19); line(11,14,11,3,7,7); line(11,3,15,7); line(7,10,7,14,15,14,15,10)
        elif k == "globe":
            oval(2,2,20,20); line(2,11,20,11); oval(7,2,15,20); line(4,6,18,6); line(4,16,18,16)
        elif k == "help":
            oval(2,2,20,20); c.create_arc(7,5,16,13,start=25,extent=300,style=tk.ARC,outline=color,width=1.7); line(11.5,13,11.5,15); oval(10.8,17.1,12.2,18.5)


def add_nav_button(parent, kind, label, command, selected=False, enabled=True):
    button = NavButton(parent, kind, label, command, selected, enabled)
    button.pack(fill="x", padx=8, pady=1)
    return button
