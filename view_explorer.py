# -*- coding: utf-8 -*-
"""指令浏览页：左侧筛选 + 列表，右侧详情解释。"""

import tkinter as tk

from data_common import search as search_entries, version_label
from ui import (ACCENT, ACCENT_DEEP, ACCENT_TINT, BG, BORDER_SOFT, FONT_MONO,
                FONT_UI, SURFACE, SURFACE_SOFT, TEXT, TEXT_MUTE, TEXT_SUB,
                Card, Chip, FlowFrame, GhostButton, PrimaryButton, ScrollFrame,
                SearchBar, bind_tree, u)


def recolor(widget, color):
    try:
        widget.configure(bg=color)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        recolor(child, color)


class ExplorerView(tk.Frame):
    """通用指令浏览器（原版 / 模组共用）。"""

    def __init__(self, master, app, entries, filters, filter_kind="category",
                 placeholder="搜索指令或关键词，例如 give"):
        tk.Frame.__init__(self, master, bg=BG)
        self.app = app
        self.entries = entries
        self.filters = filters
        self.filter_kind = filter_kind
        self._filter = filters[0][0]
        self._filter_chips = []
        self._results = []
        self._rows = {}
        self._bars = {}
        self._selected = None
        self._wrap_labels = []
        self._job = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0, minsize=u(328))
        self.grid_columnconfigure(1, weight=1)

        self._build_list(placeholder)
        self._build_detail()
        self.refresh()

    # -------------------------------------------------------------- 左侧
    def _build_list(self, placeholder):
        card = Card(self, pad=14, radius=16)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, u(14)))
        body = card.body

        self.search = SearchBar(body, width=286, height=38, placeholder=placeholder)
        self.search.pack(fill="x")
        self.search.bind_change(self._on_search_change)

        self.chips = FlowFrame(body, gap=6, bg=SURFACE)
        self.chips.configure(height=u(28))
        self.chips.pack(fill="x", pady=(u(10), u(6)))
        for key, label in self.filters:
            chip = Chip(self.chips, label, command=lambda k=key: self._set_filter(k))
            chip.set_active(key == self._filter)
            self.chips.add(chip)
            self._filter_chips.append((key, chip))

        self.count_label = tk.Label(body, text="", bg=SURFACE, fg=TEXT_MUTE,
                                    font=(FONT_UI, 8), anchor="w")
        self.count_label.pack(fill="x", pady=(0, u(4)))

        self.list_scroll = ScrollFrame(body, bg=SURFACE)
        self.list_scroll.pack(fill="both", expand=True)

    # -------------------------------------------------------------- 右侧
    def _build_detail(self):
        card = Card(self, pad=18, radius=16)
        card.grid(row=0, column=1, sticky="nsew")
        body = card.body

        bar = tk.Frame(body, bg=SURFACE)
        bar.pack(side="bottom", fill="x", pady=(u(10), 0))
        self.copy_btn = PrimaryButton(bar, "复制示例", command=self._copy_example,
                                      width=100, height=36, font_size=9)
        self.copy_btn.pack(side="left")
        self.fav_btn = GhostButton(bar, "收藏", command=self._toggle_favorite,
                                   width=74, height=36, font_size=9)
        self.fav_btn.pack(side="left", padx=(u(8), 0))
        self.hint_label = tk.Label(bar, text="", bg=SURFACE, fg=TEXT_MUTE,
                                   font=(FONT_UI, 8))
        self.hint_label.pack(side="right")

        self.detail_scroll = ScrollFrame(body, bg=SURFACE)
        self.detail_scroll.pack(fill="both", expand=True)
        self.detail_scroll.inner.bind("<Configure>", self._sync_wrap)

    def _sync_wrap(self, event):
        for label, pad in self._wrap_labels:
            try:
                label.configure(wraplength=max(u(120), event.width - pad))
            except tk.TclError:
                pass

    # -------------------------------------------------------------- 数据
    def refresh(self):
        self._apply_filter()

    def set_filters(self, filters):
        """外部（例如同步了新指令包）刷新筛选项。"""
        keys = [key for key, _ in filters]
        if self._filter not in keys:
            self._filter = filters[0][0] if filters else "全部"
        self.filters = filters
        self.chips.clear()
        self._filter_chips = []
        for key, label in filters:
            chip = Chip(self.chips, label,
                        command=lambda k=key: self._set_filter(k))
            chip.set_active(key == self._filter)
            self.chips.add(chip)
            self._filter_chips.append((key, chip))
        self._apply_filter()

    def _set_filter(self, key):
        self._filter = key
        for chip_key, chip in self._filter_chips:
            chip.set_active(chip_key == key)
        self._apply_filter()

    def _on_search_change(self):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(120, self._apply_filter)

    def _apply_filter(self):
        self._job = None
        keyword = self.search.get()
        category = self._filter if self.filter_kind == "category" else None
        mod = self._filter if self.filter_kind == "mod" else None
        self._results = search_entries(self.entries, keyword, category=category,
                                       mod=mod, version=self.app.version)
        self.count_label.configure(
            text="共 %d 条 · 版本 %s" % (len(self._results), self.app.version))
        self._render_list()

        if self._selected and self._selected in self._results:
            self._select(self._selected, keep_scroll=True)
        elif self._results:
            self._select(self._results[0])
        else:
            self._selected = None
            self._render_detail(None)

    # -------------------------------------------------------------- 列表
    def _render_list(self):
        inner = self.list_scroll.inner
        for child in inner.winfo_children():
            child.destroy()
        self._rows = {}
        self._bars = {}

        if not self._results:
            tk.Label(inner, text="没有找到匹配的指令\n换个关键词，或调整版本与分类",
                     bg=SURFACE, fg=TEXT_MUTE, font=(FONT_UI, 9),
                     justify="left").pack(padx=u(14), pady=u(36), anchor="w")
            return

        for index, entry in enumerate(self._results):
            if index:
                tk.Frame(inner, bg=BORDER_SOFT, height=1).pack(fill="x")
            self._rows[entry["id"]] = self._make_row(inner, entry)

    def _make_row(self, parent, entry):
        row = tk.Frame(parent, bg=SURFACE, cursor="hand2")
        row.pack(fill="x")

        bar = tk.Frame(row, bg=SURFACE, width=u(3))
        bar.place(x=0, y=0, relheight=1.0)

        top = tk.Frame(row, bg=SURFACE)
        top.pack(fill="x", padx=(u(12), u(10)), pady=(u(8), u(2)))
        tk.Label(top, text=entry["name"], bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 9, "bold"), anchor="w").pack(side="left")
        tk.Label(top, text=version_label(entry), bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 7)).pack(side="right")

        tk.Label(row, text=entry["syntax"], bg=SURFACE, fg=TEXT_SUB,
                 font=(FONT_MONO, 8), anchor="w", justify="left",
                 wraplength=u(262)).pack(fill="x", padx=(u(12), u(10)),
                                         pady=(0, u(8)))

        row.bind("<ButtonRelease-1>", lambda e, en=entry: self._select(en))
        row.bind("<Enter>", lambda e, en=entry: self._hover_row(en, True))
        row.bind("<Leave>", lambda e, en=entry: self._hover_row(en, False))
        bind_tree(row, "<ButtonRelease-1>", lambda e, en=entry: self._select(en))
        bind_tree(row, "<Enter>", lambda e, en=entry: self._hover_row(en, True))
        bind_tree(row, "<Leave>", lambda e, en=entry: self._hover_row(en, False))

        self._bars[entry["id"]] = bar
        return row

    def _hover_row(self, entry, flag):
        row = self._rows.get(entry["id"])
        if row is None:
            return
        selected = self._selected is entry
        color = ACCENT_TINT if selected else ("#F6FAFF" if flag else SURFACE)
        recolor(row, color)

    def _select(self, entry, keep_scroll=False):
        old = self._selected
        self._selected = entry
        if old is not None and old["id"] in self._rows:
            recolor(self._rows[old["id"]], SURFACE)
            self._bars[old["id"]].configure(bg=SURFACE)
        row = self._rows.get(entry["id"])
        if row is not None:
            recolor(row, ACCENT_TINT)
            self._bars[entry["id"]].configure(bg=ACCENT)
        self._render_detail(entry)
        if not keep_scroll:
            self.detail_scroll.to_top()

    # -------------------------------------------------------------- 详情
    def _render_detail(self, entry):
        inner = self.detail_scroll.inner
        for child in inner.winfo_children():
            child.destroy()
        self._wrap_labels = []

        if entry is None:
            self.copy_btn.set_enabled(False)
            self.fav_btn.set_enabled(False)
            self.hint_label.configure(text="")
            tk.Label(inner, text="选择左侧任意一条指令", bg=SURFACE, fg=TEXT_MUTE,
                     font=(FONT_UI, 9)).pack(anchor="w")
            return

        self.copy_btn.set_enabled(True)
        self.fav_btn.set_enabled(True)

        head = tk.Frame(inner, bg=SURFACE)
        head.pack(fill="x")
        tk.Label(head, text=entry["name"], bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 14, "bold"), anchor="w").pack(side="left")

        tags = tk.Frame(inner, bg=SURFACE)
        tags.pack(fill="x", pady=(u(8), 0))
        self._tag(tags, entry["category"])
        self._tag(tags, version_label(entry))
        if entry.get("mod_name"):
            self._tag(tags, entry["mod_name"])

        syntax = tk.Label(inner, text=entry["syntax"], bg=SURFACE_SOFT,
                          fg=ACCENT_DEEP, font=(FONT_MONO, 10), justify="left",
                          anchor="w", padx=u(12), pady=u(10))
        syntax.pack(fill="x", pady=(u(12), 0))
        self._track(syntax, u(26))

        self._section(inner, "说明")
        desc = tk.Label(inner, text=entry["desc"], bg=SURFACE, fg=TEXT_SUB,
                        font=(FONT_UI, 9), justify="left", anchor="w")
        desc.pack(fill="x")
        self._track(desc, u(4))

        if entry["params"]:
            self._section(inner, "参数")
            for name, values, note in entry["params"]:
                block = tk.Frame(inner, bg=SURFACE)
                block.pack(fill="x", pady=(u(2), u(6)))
                line = tk.Frame(block, bg=SURFACE)
                line.pack(fill="x")
                tk.Label(line, text=name, bg=SURFACE, fg=TEXT,
                         font=(FONT_UI, 9, "bold")).pack(side="left")
                values_label = tk.Label(line, text="  " + values, bg=SURFACE,
                                        fg=ACCENT_DEEP, font=(FONT_MONO, 8),
                                        anchor="w", justify="left")
                values_label.pack(side="left", fill="x", expand=True)
                self._track(values_label, u(120))
                if note:
                    note_label = tk.Label(block, text=note, bg=SURFACE,
                                          fg=TEXT_SUB, font=(FONT_UI, 8),
                                          anchor="w", justify="left")
                    note_label.pack(fill="x", pady=(u(2), 0))
                    self._track(note_label, u(4))

        if entry["examples"]:
            self._section(inner, "示例（可直接复制）")
            for example in entry["examples"]:
                box = tk.Frame(inner, bg=SURFACE_SOFT)
                box.pack(fill="x", pady=(u(4), 0))
                label = tk.Label(box, text=example, bg=SURFACE_SOFT, fg=TEXT,
                                 font=(FONT_MONO, 9), justify="left", anchor="w",
                                 padx=u(10), pady=u(8))
                label.pack(side="left", fill="x", expand=True)
                self._track(label, u(90))
                GhostButton(box, "复制", command=lambda t=example: self.app.copy(t),
                            width=54, height=28, font_size=8).pack(
                    side="right", padx=u(6), pady=u(5))

        if entry.get("notes"):
            self._section(inner, "提示")
            notes = tk.Label(inner, text=entry["notes"], bg=SURFACE_SOFT,
                             fg=TEXT_SUB, font=(FONT_UI, 8), justify="left",
                             anchor="w", padx=u(10), pady=u(8))
            notes.pack(fill="x")
            self._track(notes, u(24))

        self._sync_fav_button()
        self.hint_label.configure(text="共 %d 个示例" % len(entry["examples"]))

    def _tag(self, parent, text):
        tk.Label(parent, text=text, bg=ACCENT_TINT, fg=ACCENT_DEEP,
                 font=(FONT_UI, 7), padx=u(8), pady=u(3)).pack(
            side="left", padx=(0, u(6)))

    def _section(self, parent, title):
        tk.Label(parent, text=title, bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8), anchor="w").pack(fill="x", pady=(u(14), u(4)))

    def _track(self, label, pad):
        self._wrap_labels.append((label, pad))
        try:
            label.configure(wraplength=max(u(120),
                                           self.detail_scroll.inner.winfo_width() - pad))
        except tk.TclError:
            pass

    # -------------------------------------------------------------- 操作
    def sync_fav(self):
        self._sync_fav_button()

    def _copy_example(self):
        if not self._selected:
            return
        examples = self._selected["examples"]
        self.app.copy(examples[0] if examples else self._selected["syntax"])

    def _toggle_favorite(self):
        if not self._selected:
            return
        flag = self.app.toggle_favorite(self._selected["id"])
        self._sync_fav_button()
        self.app.notify("已加入收藏" if flag else "已取消收藏")

    def _sync_fav_button(self):
        if not self._selected:
            return
        flag = self.app.store.is_favorite(self._selected["id"])
        self.fav_btn._text = "已收藏" if flag else "收藏"
        self.fav_btn._accent = flag
        self.fav_btn._draw()
