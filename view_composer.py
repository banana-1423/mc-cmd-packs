# -*- coding: utf-8 -*-
"""命令生成页：选模板 → 填参数 → 实时生成指令。"""

import tkinter as tk

from data_common import version_index
from data_templates import TEMPLATES
from ui import (ACCENT, ACCENT_DEEP, ACCENT_TINT, BG, BORDER_SOFT, FONT_MONO,
                FONT_UI, ORANGE, SURFACE, SURFACE_SOFT, TEXT, TEXT_MUTE,
                TEXT_SUB, Card, Dropdown, GhostButton, Input, PrimaryButton,
                ScrollFrame, bind_tree, u)


class ComposerView(tk.Frame):
    def __init__(self, master, app):
        tk.Frame.__init__(self, master, bg=BG)
        self.app = app
        self.template = None
        self.values = {}
        self.widgets = {}
        self._rows = {}
        self._bars = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0, minsize=u(280))
        self.grid_columnconfigure(1, weight=1)

        self._build_list()
        self._build_panel()
        self.select(TEMPLATES[0])

    # -------------------------------------------------------------- 模板列表
    def _build_list(self):
        card = Card(self, pad=14, radius=16)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, u(14)))
        body = card.body

        tk.Label(body, text="指令模板", bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 10, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text="选一个模板，右边填参数", bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8), anchor="w").pack(fill="x", pady=(u(2), u(8)))

        scroll = ScrollFrame(body, bg=SURFACE)
        scroll.pack(fill="both", expand=True)
        self.list_scroll = scroll

        for index, template in enumerate(TEMPLATES):
            if index:
                tk.Frame(scroll.inner, bg=BORDER_SOFT, height=1).pack(fill="x")
            self._make_row(scroll.inner, template)

    def _make_row(self, parent, template):
        row = tk.Frame(parent, bg=SURFACE, cursor="hand2")
        row.pack(fill="x")
        bar = tk.Frame(row, bg=SURFACE, width=u(3))
        bar.place(x=0, y=0, relheight=1.0)

        body = tk.Frame(row, bg=SURFACE)
        body.pack(fill="x", padx=(u(12), u(10)), pady=u(9))
        tk.Label(body, text=template["name"], bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 9, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text=template["desc"], bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8), anchor="w", justify="left",
                 wraplength=u(210)).pack(fill="x", pady=(u(2), 0))

        for seq in ("<ButtonRelease-1>",):
            bind_tree(row, seq, lambda e, t=template: self.select(t))
        bind_tree(row, "<Enter>",
                  lambda e, t=template: self._hover(t, True))
        bind_tree(row, "<Leave>",
                  lambda e, t=template: self._hover(t, False))

        self._rows[template["id"]] = row
        self._bars[template["id"]] = bar

    def _hover(self, template, flag):
        row = self._rows.get(template["id"])
        if row is None:
            return
        selected = self.template is template
        color = ACCENT_TINT if selected else ("#F6FAFF" if flag else SURFACE)
        self._recolor(row, color)

    def _recolor(self, widget, color):
        try:
            widget.configure(bg=color)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._recolor(child, color)

    # -------------------------------------------------------------- 右侧面板
    def _build_panel(self):
        card = Card(self, pad=20, radius=16)
        card.grid(row=0, column=1, sticky="nsew")
        body = card.body

        head = tk.Frame(body, bg=SURFACE)
        head.pack(fill="x")
        self.title_label = tk.Label(head, text="", bg=SURFACE, fg=TEXT,
                                    font=(FONT_UI, 14, "bold"), anchor="w")
        self.title_label.pack(side="left")
        self.since_label = tk.Label(head, text="", bg=ACCENT_TINT,
                                    fg=ACCENT_DEEP, font=(FONT_UI, 7),
                                    padx=u(8), pady=u(3))
        self.since_label.pack(side="left", padx=(u(10), 0), pady=(u(4), 0))

        self.desc_label = tk.Label(body, text="", bg=SURFACE, fg=TEXT_SUB,
                                   font=(FONT_UI, 9), anchor="w", justify="left")
        self.desc_label.pack(fill="x", pady=(u(6), 0))

        # 底部操作栏
        bar = tk.Frame(body, bg=SURFACE)
        bar.pack(side="bottom", fill="x", pady=(u(10), 0))
        self.reset_btn = GhostButton(bar, "重置参数", command=self.reset,
                                     width=88, height=36, font_size=9)
        self.reset_btn.pack(side="left")
        self.copy_btn = PrimaryButton(bar, "复制指令", command=self._copy,
                                      width=100, height=36, font_size=9)
        self.copy_btn.pack(side="left", padx=(u(8), 0))
        self.warn_label = tk.Label(bar, text="", bg=SURFACE, fg=ORANGE,
                                   font=(FONT_UI, 8))
        self.warn_label.pack(side="right")

        # 生成结果
        preview = tk.Frame(body, bg=SURFACE)
        preview.pack(side="bottom", fill="x", pady=(u(8), 0))
        tk.Label(preview, text="生成结果", bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8), anchor="w").pack(fill="x", pady=(0, u(4)))
        box = tk.Frame(preview, bg=SURFACE_SOFT)
        box.pack(fill="x")
        self.preview_label = tk.Label(box, text="", bg=SURFACE_SOFT,
                                      fg=ACCENT_DEEP, font=(FONT_MONO, 10),
                                      anchor="w", justify="left",
                                      padx=u(12), pady=u(12))
        self.preview_label.pack(fill="x")
        box.bind("<Configure>", lambda e: self.preview_label.configure(
            wraplength=max(u(160), e.width - u(24))))

        # 表单
        tk.Label(body, text="参数", bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8), anchor="w").pack(fill="x", pady=(u(14), u(6)))
        self.form = tk.Frame(body, bg=SURFACE)
        self.form.pack(fill="x")
        self.form.columnconfigure(0, weight=1)
        self.form.columnconfigure(1, weight=1)

        self.tips_frame = tk.Frame(body, bg=SURFACE)
        self.tips_frame.pack(fill="both", expand=True, pady=(u(6), 0))
        tk.Label(self.tips_frame, text="使用提示", bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8), anchor="w").pack(fill="x", pady=(0, u(4)))
        self.tips_label = tk.Label(self.tips_frame, text="", bg=SURFACE_SOFT,
                                   fg=TEXT_SUB, font=(FONT_UI, 9), anchor="w",
                                   justify="left", padx=u(12), pady=u(10))
        self.tips_label.pack(fill="x")
        self.tips_frame.bind("<Configure>", lambda e: self.tips_label.configure(
            wraplength=max(u(160), e.width - u(24))))

    # -------------------------------------------------------------- 交互
    def select(self, template):
        previous = self.template
        if previous is not None and previous["id"] in self._rows:
            self._recolor(self._rows[previous["id"]], SURFACE)
            self._bars[previous["id"]].configure(bg=SURFACE)
        self.template = template
        row = self._rows.get(template["id"])
        if row is not None:
            self._recolor(row, ACCENT_TINT)
            self._bars[template["id"]].configure(bg=ACCENT)

        self.title_label.configure(text=template["name"])
        self.since_label.configure(text=template["since"] + " 起")
        self.desc_label.configure(text=template["desc"])
        self.tips_label.configure(text=template.get("tips") or "")
        self.values = {}
        self._build_fields()
        self._update_preview()

    def _build_fields(self):
        for child in self.form.winfo_children():
            child.destroy()
        self.widgets = {}

        fields = self.template["fields"]
        for index, field in enumerate(fields):
            row, col = divmod(index, 2)
            cell = tk.Frame(self.form, bg=SURFACE)
            cell.grid(row=row, column=col, sticky="ew",
                      padx=(0, u(10) if col == 0 else 0), pady=(0, u(10)))
            tk.Label(cell, text=field["label"], bg=SURFACE, fg=TEXT_SUB,
                     font=(FONT_UI, 8), anchor="w").pack(fill="x",
                                                        pady=(0, u(4)))
            default = field.get("default", "")
            self.values[field["key"]] = default
            if field["type"] == "choice":
                widget = Dropdown(cell, field["options"], value=default,
                                  width=200, height=34, font_size=9,
                                  command=lambda v, k=field["key"]: self._set_value(k, v))
                widget.pack(fill="x")
            else:
                widget = Input(cell, value=default, height=34, font_size=9,
                               mono=field["key"] in ("extra", "nbt", "text",
                                                     "command"))
                widget.pack(fill="x")
                widget.bind_change(lambda k=field["key"], w=widget: self._set_value(k, w.get()))
            self.widgets[field["key"]] = widget

            if field.get("hint"):
                tk.Label(cell, text=field["hint"], bg=SURFACE, fg=TEXT_MUTE,
                         font=(FONT_UI, 7), anchor="w", justify="left",
                         wraplength=u(200)).pack(fill="x", pady=(u(3), 0))

    def _set_value(self, key, value):
        self.values[key] = value
        self._update_preview()

    def _build_command(self):
        parts = []
        for part in self.template["parts"]:
            if part.startswith("{") and part.endswith("}"):
                value = (self.values.get(part[1:-1]) or "").strip()
                if value:
                    parts.append(value)
            else:
                parts.append(part)
        return " ".join(parts)

    def _update_preview(self):
        command = self._build_command()
        self.preview_label.configure(text=command or "（请填写参数）")
        available = (version_index(self.template["since"]) <=
                     version_index(self.app.version))
        if available:
            self.warn_label.configure(text="")
            self.copy_btn.set_enabled(True)
        else:
            self.warn_label.configure(
                text="当前版本 %s 低于模板要求" % self.app.version)
            self.copy_btn.set_enabled(False)

    def reset(self):
        for field in self.template["fields"]:
            key = field["key"]
            value = field.get("default", "")
            self.values[key] = value
            widget = self.widgets.get(key)
            if isinstance(widget, Input):
                widget.set(value)
            elif isinstance(widget, Dropdown):
                widget.set(value)
        self._update_preview()
        self.app.notify("已重置模板参数")

    def _copy(self):
        command = self._build_command()
        if command:
            self.app.copy(command)
