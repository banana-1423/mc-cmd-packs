# -*- coding: utf-8 -*-
"""服务器页：server.properties 编辑 + 常用服务器指令。"""

import os
import tkinter as tk
from tkinter import filedialog

from data_vanilla import VANILLA
from ui import (ACCENT, ACCENT_DEEP, BG, BORDER_SOFT, FONT_MONO, FONT_UI,
                SURFACE, SURFACE_SOFT, TEXT, TEXT_MUTE, TEXT_SUB, Card,
                Dropdown, GhostButton, Input, PrimaryButton, ScrollFrame, u)

PROPERTIES = [
    ("motd", "服务器标题", "text", "A Minecraft Server"),
    ("server-port", "端口", "text", "25565"),
    ("max-players", "最大人数", "text", "20"),
    ("gamemode", "默认模式", "choice", "survival"),
    ("difficulty", "难度", "choice", "normal"),
    ("online-mode", "正版验证", "choice", "true"),
    ("pvp", "允许 PVP", "choice", "true"),
    ("allow-flight", "允许飞行", "choice", "false"),
    ("enable-command-block", "命令方块", "choice", "false"),
    ("view-distance", "视距", "text", "10"),
    ("simulation-distance", "模拟距离", "text", "10"),
    ("spawn-protection", "出生点保护", "text", "16"),
    ("level-name", "世界文件夹", "text", "world"),
    ("level-seed", "世界种子", "text", ""),
    ("white-list", "开启白名单", "choice", "false"),
    ("enforce-whitelist", "强制白名单", "choice", "false"),
]

CHOICES = {
    "gamemode": ["survival", "creative", "adventure", "spectator"],
    "difficulty": ["peaceful", "easy", "normal", "hard"],
    "online-mode": ["true", "false"],
    "pvp": ["true", "false"],
    "allow-flight": ["true", "false"],
    "enable-command-block": ["true", "false"],
    "white-list": ["true", "false"],
    "enforce-whitelist": ["true", "false"],
}

JVM_LINES = [
    ("启动（4G 内存）", "java -Xms4G -Xmx4G -jar server.jar nogui"),
    ("G1 垃圾回收参数", "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200"),
]


class ServerView(tk.Frame):
    def __init__(self, master, app):
        tk.Frame.__init__(self, master, bg=BG)
        self.app = app
        self.path_var = None
        self.widgets = {}
        self.raw_lines = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        self._build_properties()
        self._build_commands()
        self._restore_path()

    # -------------------------------------------------------------- 配置编辑
    def _build_properties(self):
        card = Card(self, pad=18, radius=16)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, u(14)))
        body = card.body

        tk.Label(body, text="server.properties", bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text="选择服务器目录里的配置文件，改完直接保存", bg=SURFACE,
                 fg=TEXT_MUTE, font=(FONT_UI, 8), anchor="w").pack(
            fill="x", pady=(u(2), u(10)))

        path_row = tk.Frame(body, bg=SURFACE)
        path_row.pack(fill="x")
        self.path_input = Input(path_row, value="", height=34, font_size=8, mono=True)
        self.path_input.pack(side="left", fill="x", expand=True)
        GhostButton(path_row, "浏览", command=self._browse, width=56,
                    height=34, font_size=8).pack(side="left", padx=(u(8), 0))
        GhostButton(path_row, "载入", command=self.load_file, width=56,
                    height=34, font_size=8).pack(side="left", padx=(u(6), 0))

        buttons = tk.Frame(body, bg=SURFACE)
        buttons.pack(fill="x", pady=(u(10), u(4)))
        PrimaryButton(buttons, "保存配置", command=self.save_file,
                      width=92, height=34, font_size=9).pack(side="left")
        self.status = tk.Label(buttons, text="尚未载入配置文件", bg=SURFACE,
                               fg=TEXT_MUTE, font=(FONT_UI, 8))
        self.status.pack(side="left", padx=(u(10), 0))

        tk.Frame(body, bg=BORDER_SOFT, height=1).pack(fill="x", pady=(u(8), 0))

        scroll = ScrollFrame(body, bg=SURFACE)
        scroll.pack(fill="both", expand=True, pady=(u(6), 0))
        inner = scroll.inner

        for index, (key, label, kind, default) in enumerate(PROPERTIES):
            row = tk.Frame(inner, bg=SURFACE)
            row.pack(fill="x", pady=u(5))
            tk.Label(row, text=label, bg=SURFACE, fg=TEXT_SUB,
                     font=(FONT_UI, 8), anchor="w", width=10).pack(side="left")
            if kind == "choice":
                widget = Dropdown(row, CHOICES[key], value=default, width=150,
                                  height=32, font_size=8)
                widget.pack(side="left", fill="x", expand=True)
            else:
                widget = Input(row, value=default, height=32, font_size=8,
                               mono=True)
                widget.pack(side="left", fill="x", expand=True)
            tk.Label(row, text=key, bg=SURFACE, fg=TEXT_MUTE,
                     font=(FONT_MONO, 7)).pack(side="right", padx=(u(8), 0))
            self.widgets[key] = widget

    # -------------------------------------------------------------- 服务器指令
    def _build_commands(self):
        card = Card(self, pad=18, radius=16)
        card.grid(row=0, column=1, sticky="nsew")
        body = card.body

        tk.Label(body, text="服务器指令", bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text="点一下即复制，可直接贴到控制台", bg=SURFACE,
                 fg=TEXT_MUTE, font=(FONT_UI, 8), anchor="w").pack(
            fill="x", pady=(u(2), u(10)))

        jvm = tk.Frame(body, bg=SURFACE)
        jvm.pack(side="bottom", fill="x", pady=(u(10), 0))
        tk.Label(jvm, text="启动命令参考", bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8), anchor="w").pack(fill="x", pady=(0, u(4)))
        for title, line in JVM_LINES:
            box = tk.Frame(jvm, bg=SURFACE_SOFT)
            box.pack(fill="x", pady=(0, u(6)))
            tk.Label(box, text=title, bg=SURFACE_SOFT, fg=TEXT_MUTE,
                     font=(FONT_UI, 7), anchor="w").pack(fill="x", padx=u(10),
                                                         pady=(u(6), 0))
            line_label = tk.Label(box, text=line, bg=SURFACE_SOFT, fg=TEXT,
                                  font=(FONT_MONO, 8), anchor="w", justify="left")
            line_label.pack(fill="x", padx=u(10), pady=(u(2), u(8)))
            box.bind("<Configure>", lambda e, lbl=line_label: lbl.configure(
                wraplength=max(u(120), e.width - u(20))))
            tk.Label(box, text="点击复制", bg=SURFACE_SOFT, fg=ACCENT,
                     font=(FONT_UI, 7), cursor="hand2").pack(
                anchor="e", padx=u(10), pady=(0, u(6)))
            box.bind("<Button-1>", lambda e, t=line: self.app.copy(t))
            for child in box.winfo_children():
                child.bind("<Button-1>", lambda e, t=line: self.app.copy(t))

        scroll = ScrollFrame(body, bg=SURFACE)
        scroll.pack(fill="both", expand=True)
        entries = [e for e in VANILLA if e["category"] == "服务器"]
        for index, entry in enumerate(entries):
            if index:
                tk.Frame(scroll.inner, bg=BORDER_SOFT, height=1).pack(fill="x")
            first = entry["examples"][0] if entry["examples"] else entry["syntax"]
            row = tk.Frame(scroll.inner, bg=SURFACE, cursor="hand2")
            row.pack(fill="x")
            text_block = tk.Frame(row, bg=SURFACE)
            text_block.pack(side="left", fill="x", expand=True,
                            padx=(u(8), u(4)), pady=u(6))
            tk.Label(text_block, text=entry["name"], bg=SURFACE, fg=TEXT,
                     font=(FONT_UI, 8, "bold"), anchor="w").pack(fill="x")
            tk.Label(text_block, text=first, bg=SURFACE, fg=ACCENT_DEEP,
                     font=(FONT_MONO, 8), anchor="w", justify="left",
                     wraplength=u(190)).pack(fill="x", pady=(u(2), 0))
            tk.Label(row, text="复制", bg=SURFACE, fg=TEXT_MUTE,
                     font=(FONT_UI, 7), cursor="hand2").pack(side="right",
                                                             padx=u(6))
            for widget in (row, text_block):
                widget.bind("<Button-1>", lambda e, t=first: self.app.copy(t))
            for widget in text_block.winfo_children():
                widget.bind("<Button-1>", lambda e, t=first: self.app.copy(t))

    # -------------------------------------------------------------- 文件操作
    def _restore_path(self):
        path = self.app.store.server_properties
        if path:
            self.path_input.set(path)
            if os.path.isfile(path):
                self.load_file(silent=True)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="选择 server.properties",
            filetypes=[("server.properties", "server.properties"),
                       ("所有文件", "*.*")])
        if path:
            self.path_input.set(path)
            self.load_file()

    def load_file(self, silent=False):
        path = self.path_input.get().strip()
        if not path or not os.path.isfile(path):
            if not silent:
                self.status.configure(text="文件不存在，请重新选择")
                self.app.notify("没有找到配置文件")
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                self.raw_lines = handle.read().splitlines()
        except (IOError, OSError):
            self.status.configure(text="读取失败")
            self.app.notify("读取配置文件失败")
            return

        values = {}
        for line in self.raw_lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()

        for key, widget in self.widgets.items():
            if key in values:
                widget.set(values[key])

        self.app.store.server_properties = path
        self.status.configure(text="已载入 %s" % os.path.basename(path))
        if not silent:
            self.app.notify("已载入服务器配置")

    def save_file(self):
        path = self.path_input.get().strip()
        if not path:
            self.status.configure(text="请先选择配置文件")
            self.app.notify("请先选择 server.properties")
            return

        current = {}
        for key, widget in self.widgets.items():
            current[key] = widget.get()

        lines = []
        written = set()
        for line in self.raw_lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in current:
                    lines.append("%s=%s" % (key, current[key]))
                    written.add(key)
                    continue
            lines.append(line)

        for key, _, _, _ in PROPERTIES:
            if key not in written:
                lines.append("%s=%s" % (key, current[key]))

        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n")
        except (IOError, OSError):
            self.status.configure(text="保存失败，请检查文件权限")
            self.app.notify("保存失败")
            return

        self.raw_lines = lines
        self.app.store.server_properties = path
        self.status.configure(text="已保存 %s" % os.path.basename(path))
        self.app.notify("配置已保存")
