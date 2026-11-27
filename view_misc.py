# -*- coding: utf-8 -*-
"""收藏夹与设置页。"""

import os
import tkinter as tk

import online
from data_common import VERSIONS, VERSION_NOTES, version_label
from store import DATA_DIR, STATE_FILE
from ui import (ACCENT, ACCENT_DEEP, ACCENT_TINT, BG, BORDER_SOFT, FONT_MONO,
                FONT_UI, SURFACE, SURFACE_SOFT, TEXT, TEXT_MUTE, TEXT_SUB,
                Card, Dropdown, GhostButton, Input, PrimaryButton, ScrollFrame,
                u)


class FavoritesView(tk.Frame):
    def __init__(self, master, app):
        tk.Frame.__init__(self, master, bg=BG)
        self.app = app

        card = Card(self, pad=20, radius=16)
        card.pack(fill="both", expand=True)
        body = card.body

        head = tk.Frame(body, bg=SURFACE)
        head.pack(fill="x")
        tk.Label(head, text="收藏夹", bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 13, "bold")).pack(side="left")
        self.count_label = tk.Label(head, text="", bg=SURFACE, fg=TEXT_MUTE,
                                    font=(FONT_UI, 8))
        self.count_label.pack(side="left", padx=(u(10), 0), pady=(u(4), 0))
        GhostButton(head, "清空收藏", command=self._clear, width=80,
                    height=30, font_size=8).pack(side="right")

        tk.Frame(body, bg=BORDER_SOFT, height=1).pack(fill="x", pady=(u(10), u(4)))

        self.scroll = ScrollFrame(body, bg=SURFACE)
        self.scroll.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        inner = self.scroll.inner
        for child in inner.winfo_children():
            child.destroy()

        entries = []
        for cmd_id in self.app.store.favorites:
            entry = self.app.index.get(cmd_id)
            if entry:
                entries.append(entry)

        self.count_label.configure(text="共 %d 条" % len(entries))
        if not entries:
            tk.Label(inner, text="还没有收藏的指令\n在「指令速查」或「模组索引」里点收藏即可",
                     bg=SURFACE, fg=TEXT_MUTE, font=(FONT_UI, 9),
                     justify="left").pack(anchor="w", padx=u(4), pady=u(40))
            return

        for index, entry in enumerate(entries):
            if index:
                tk.Frame(inner, bg=BORDER_SOFT, height=1).pack(fill="x")
            row = tk.Frame(inner, bg=SURFACE)
            row.pack(fill="x", pady=u(6))

            text_block = tk.Frame(row, bg=SURFACE)
            text_block.pack(side="left", fill="x", expand=True, padx=(u(4), u(10)))
            tk.Label(text_block, text=entry["name"], bg=SURFACE, fg=TEXT,
                     font=(FONT_UI, 9, "bold"), anchor="w").pack(fill="x")
            tk.Label(text_block, text=entry["syntax"], bg=SURFACE, fg=TEXT_SUB,
                     font=(FONT_MONO, 8), anchor="w", justify="left",
                     wraplength=u(420)).pack(fill="x", pady=(u(2), 0))
            tk.Label(text_block, text="%s · %s" % (entry["category"],
                                                   version_label(entry)),
                     bg=SURFACE, fg=TEXT_MUTE, font=(FONT_UI, 7),
                     anchor="w").pack(fill="x", pady=(u(2), 0))

            GhostButton(row, "移除", command=lambda c=entry["id"]: self._remove(c),
                        width=56, height=30, font_size=8).pack(side="right")
            PrimaryButton(row, "复制", command=lambda e=entry: self._copy(e),
                          width=62, height=30, font_size=8).pack(
                side="right", padx=(0, u(8)))

    def _copy(self, entry):
        examples = entry["examples"]
        self.app.copy(examples[0] if examples else entry["syntax"])

    def _remove(self, cmd_id):
        self.app.toggle_favorite(cmd_id)
        self.refresh()
        self.app.notify("已取消收藏")

    def _clear(self):
        if not self.app.store.favorites:
            return
        self.app.store.clear_favorites()
        self.refresh()
        self.app.notify("收藏夹已清空")


class SettingsView(tk.Frame):
    def __init__(self, master, app):
        tk.Frame.__init__(self, master, bg=BG)
        self.app = app

        card = Card(self, pad=22, radius=16)
        card.pack(fill="both", expand=True)
        body = card.body

        tk.Label(body, text="偏好与数据", bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 13, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text="版本、数据与本地状态", bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8), anchor="w").pack(fill="x", pady=(u(2), u(12)))

        self._row(body, "默认游戏版本", "所有页面的指令会按这个版本过滤")
        version_row = tk.Frame(body, bg=SURFACE)
        version_row.pack(fill="x", pady=(0, u(6)))
        self.version_dd = Dropdown(version_row, VERSIONS, value=app.version,
                                   width=150, height=34, font_size=9,
                                   command=self._change_version)
        self.version_dd.pack(side="left")
        self.version_note = tk.Label(version_row, text="", bg=SURFACE,
                                     fg=TEXT_MUTE, font=(FONT_UI, 8))
        self.version_note.pack(side="left", padx=(u(10), 0))
        self._update_version_note()

        self._divider(body)
        self._row(body, "本地数据", "收藏与设置保存在项目目录里")
        path_row = tk.Frame(body, bg=SURFACE)
        path_row.pack(fill="x", pady=(0, u(6)))
        tk.Label(path_row, text=STATE_FILE, bg=SURFACE_SOFT, fg=TEXT_SUB,
                 font=(FONT_MONO, 8), padx=u(10), pady=u(7),
                 anchor="w").pack(side="left", fill="x", expand=True)
        GhostButton(path_row, "打开目录", command=self._open_dir, width=82,
                    height=32, font_size=8).pack(side="left", padx=(u(8), 0))

        self._divider(body)
        self._row(body, "线上仓库", "GitHub 仓库 owner/repo，线上模式从这里同步指令包")
        repo_row = tk.Frame(body, bg=SURFACE)
        repo_row.pack(fill="x", pady=(0, u(6)))
        self.repo_input = Input(repo_row, value=app.store.repo, height=34,
                                font_size=8, mono=True)
        self.repo_input.pack(side="left", fill="x", expand=True)
        self.branch_input = Input(repo_row, value=app.store.branch, width=86,
                                  height=34, font_size=8, mono=True)
        self.branch_input.pack(side="left", padx=(u(6), 0))
        GhostButton(repo_row, "保存", command=self._save_repo, width=52,
                    height=34, font_size=8).pack(side="left", padx=(u(6), 0))

        mode_row = tk.Frame(body, bg=SURFACE)
        mode_row.pack(fill="x", pady=(u(4), 0))
        self.mode_label = tk.Label(mode_row, text="", bg=SURFACE, fg=TEXT_SUB,
                                   font=(FONT_UI, 8))
        self.mode_label.pack(side="left")
        GhostButton(mode_row, "切换模式", command=self._toggle_mode, width=82,
                    height=32, font_size=8).pack(side="right")
        GhostButton(mode_row, "立即同步", command=self._sync, width=82,
                    height=32, font_size=8).pack(side="right",
                                                  padx=(0, u(6)))

        self._divider(body)
        self._row(body, "数据统计", "当前索引与收藏情况")
        self.stats = tk.Label(body, text="", bg=SURFACE, fg=TEXT_SUB,
                              font=(FONT_UI, 9), anchor="w", justify="left")
        self.stats.pack(fill="x")
        stats_row = tk.Frame(body, bg=SURFACE)
        stats_row.pack(fill="x", pady=(u(10), 0))
        GhostButton(stats_row, "清空收藏", command=self._clear_favorites,
                    width=82, height=32, font_size=8).pack(side="left")
        GhostButton(stats_row, "重新载入数据", command=self._reload,
                    width=100, height=32, font_size=8).pack(side="left",
                                                             padx=(u(8), 0))

        self._divider(body)
        self._row(body, "关于", "纯本地运行的 Minecraft 指令工具")
        tk.Label(body, text=("指令数据内置于 data_vanilla.py / data_mods.py，"
                             "可自行增删；模组指令以常见版本为准。\n"
                             "版本选择只影响「是否显示」，不会联网校验。"),
                 bg=SURFACE, fg=TEXT_MUTE, font=(FONT_UI, 8),
                 anchor="w", justify="left").pack(fill="x")
        self._refresh_stats()

    # -------------------------------------------------------------- 组件
    def _row(self, parent, title, subtitle):
        block = tk.Frame(parent, bg=SURFACE)
        block.pack(fill="x", pady=(u(4), u(6)))
        tk.Label(block, text=title, bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 9, "bold"), anchor="w").pack(fill="x")
        tk.Label(block, text=subtitle, bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8), anchor="w").pack(fill="x", pady=(u(2), 0))

    def _divider(self, parent):
        tk.Frame(parent, bg=BORDER_SOFT, height=1).pack(fill="x", pady=u(14))

    def _update_version_note(self):
        note = VERSION_NOTES.get(self.app.version, "")
        self.version_note.configure(text=note)

    def _refresh_stats(self):
        mode = "线上模式" if self.app.mode == "online" else "离线模式"
        packs = len(self.app.packs)
        self.mode_label.configure(
            text="%s · 已同步 %d 个指令包 · %s" % (
                mode, packs, self.app.sync_message or
                ("已设置仓库" if self.app.store.repo else "未设置仓库")))
        self.stats.configure(
            text="原版指令 %d 条 · 模组指令 %d 条 · 指令包 %d 条 · 已收藏 %d 条" % (
                self.app.vanilla_count, self.app.mod_count,
                len(self.app.pack_entries), len(self.app.store.favorites)))

    def _save_repo(self):
        repo = online.normalize_repo(self.repo_input.get())
        if not repo:
            self.app.notify("请填写 owner/repo 形式的仓库地址")
            return
        self.app.store.repo = repo
        self.app.store.branch = self.branch_input.get().strip() or "main"
        self.app.sync_message = ""
        self.repo_input.set(repo)
        self.branch_input.set(self.app.store.branch)
        self.refresh()
        self.app.notify("仓库配置已保存：%s" % repo)

    def _sync(self):
        self._save_repo()
        if self.app.store.repo:
            self.app.sync_online(manual=True)

    def _toggle_mode(self):
        self.app.set_mode("offline" if self.app.mode == "online" else "online")
        self.refresh()

    # -------------------------------------------------------------- 操作
    def _change_version(self, value):
        self.app.set_version(value)
        self.version_note.configure(text=VERSION_NOTES.get(value, ""))
        self.app.notify("已切换到版本 %s" % value)

    def _open_dir(self):
        try:
            os.startfile(DATA_DIR)
        except (OSError, AttributeError):
            self.app.notify("无法打开目录：%s" % DATA_DIR)

    def _clear_favorites(self):
        self.app.store.clear_favorites()
        favorites = getattr(self.app, "favorites_view", None)
        if favorites is not None:
            favorites.refresh()
        self._refresh_stats()
        self.app.notify("收藏夹已清空")

    def _reload(self):
        self.app.reload_data()
        self._refresh_stats()

    def refresh(self):
        self.version_dd.set(self.app.version)
        self._update_version_note()
        self.repo_input.set(self.app.store.repo)
        self.branch_input.set(self.app.store.branch)
        self._refresh_stats()
