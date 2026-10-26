"""Browsable, bilingual Help workspace backed by the existing help content."""
import tkinter as tk
from tkinter import ttk

from help.help import HELP_DATA
from ui.quality_tools import ToolView


class HelpView(ToolView):
    TOPIC_KEYS = {
        "en": ("Project", "Data Input", "Analysis", "Control Chart", "Export", "System"),
        "id": ("Proyek", "Input Data", "Analisis", "Peta Kendali", "Ekspor", "Sistem"),
    }

    def __init__(self, main):
        super().__init__(main, "help", "help", "help_guidance")
        self._build()
        self._populate()

    def set_theme(self, palette):
        self.configure(background=palette["surface"])
        self.text.tag_configure("section", foreground=palette["accent"])

    def _build(self):
        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=16, pady=14)

        navigation = ttk.Frame(paned, width=230)
        navigation.pack_propagate(False)
        self.tree = ttk.Treeview(navigation, show="tree", selectmode="browse")
        scrollbar = ttk.Scrollbar(navigation, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)

        content = ttk.Frame(paned)
        self.heading = ttk.Label(content, text="", font=("Segoe UI", 14, "bold"))
        self.heading.pack(anchor="w", padx=12, pady=(10, 4))
        self.text = tk.Text(content, wrap="word", relief="flat", bd=0, padx=12, pady=8,
                            bg="white", fg="#1e293b", font=("Segoe UI", 10),
                            spacing1=2, spacing3=5, state="disabled")
        text_scroll = ttk.Scrollbar(content, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=text_scroll.set)
        text_scroll.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("section", font=("Segoe UI", 11, "bold"), foreground="#1d4ed8", spacing1=10, spacing3=4)
        self.text.tag_configure("body", lmargin1=8, lmargin2=8)
        paned.add(navigation, weight=1)
        paned.add(content, weight=4)

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        lang = self.main.current_lang
        topics = HELP_DATA.get(lang, {})
        english_topics = HELP_DATA.get("en", {})
        localized_titles = self.TOPIC_KEYS.get(lang, self.TOPIC_KEYS["en"])
        english_titles = self.TOPIC_KEYS["en"]

        self._topic_ids = {}
        self._fallback_by_item = {}
        for index, title in enumerate(localized_titles):
            source = topics.get(title)
            fallback = source is None
            if fallback:
                source = english_topics.get(english_titles[index], {})
            topic_id = self.tree.insert("", "end", text=title, open=True)
            self._topic_ids[topic_id] = (title, None, source, fallback)
            self._fallback_by_item[topic_id] = fallback
            for article in source:
                item_id = self.tree.insert(topic_id, "end", text=article)
                self._topic_ids[item_id] = (title, article, source, fallback)
                self._fallback_by_item[item_id] = fallback
        first = next(iter(self._topic_ids), None)
        if first:
            self.tree.selection_set(first)
            self.tree.focus(first)
            self._render_selection(first)
        else:
            self.heading.configure(text=self.main.t("help"))
            self._set_text(self.main.t("help_empty"))

    def _selection_changed(self, _event=None):
        selected = self.tree.selection()
        if selected:
            self._render_selection(selected[0])

    def _render_selection(self, item_id):
        topic, article, topic_data, fallback = self._topic_ids[item_id]
        display_topic = topic

        if article is not None and topic_data and article in topic_data:
            chosen = {article: topic_data[article]}
            self.heading.configure(text=f"{display_topic} · {article}")
        else:
            chosen = topic_data or {}
            self.heading.configure(text=display_topic)

        blocks = []
        if fallback:
            blocks.append((self.main.t("help_fallback_title"), self.main.t("help_fallback")))
        if not chosen:
            blocks.append((self.main.t("help_empty_title"), self.main.t("help_empty")))
        for title, sections in chosen.items():
            blocks.append((title, ""))
            for heading, body in sections.items():
                blocks.append((heading, body.strip()))
        self._set_blocks(blocks)

    def _set_text(self, value):
        self._set_blocks([(self.main.t("help_empty_title"), value)])

    def _set_blocks(self, blocks):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for heading, body in blocks:
            self.text.insert("end", f"{heading}\n", "section")
            if body:
                self.text.insert("end", f"{body}\n\n", "body")
        self.text.configure(state="disabled")
        self.text.yview_moveto(0)
