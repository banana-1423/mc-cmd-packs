# -*- coding: utf-8 -*-
"""指令包页：线上同步、包列表、上传指引与本地校验。"""

import json
import os
import tkinter as tk
from tkinter import filedialog

import online
import pack_spec
from ui import (ACCENT, ACCENT_DEEP, ACCENT_TINT, BG, BORDER_SOFT, FONT_MONO,
                FONT_UI, GREEN, ORANGE, SURFACE, SURFACE_SOFT, TEXT, TEXT_MUTE,
                TEXT_SUB, Card, GhostButton, Input, PrimaryButton, ScrollFrame,
                u)


class PacksView(tk.Frame):
    def __init__(self, master, app):
        tk.Frame.__init__(self, master, bg=BG)
        self.app = app
        self._pack_rows = []
        self._last_check = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)

        self._build_left()
        self._build_right()
        self.refresh()

    # -------------------------------------------------------------- 左：同步与包列表
    def _build_left(self):
        card = Card(self, pad=18, radius=16)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, u(14)))
        body = card.body

        head = tk.Frame(body, bg=SURFACE)
        head.pack(fill="x")
        tk.Label(head, text="线上指令包", bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 12, "bold")).pack(side="left")
        self.count_label = tk.Label(head, text="", bg=SURFACE, fg=TEXT_MUTE,
                                    font=(FONT_UI, 8))
        self.count_label.pack(side="left", padx=(u(8), 0), pady=(u(3), 0))
        self.sync_btn = PrimaryButton(head, "同步", command=self._sync,
                                      width=64, height=32, font_size=9)
        self.sync_btn.pack(side="right")

        repo_row = tk.Frame(body, bg=SURFACE)
        repo_row.pack(fill="x", pady=(u(10), 0))
        self.repo_input = Input(repo_row, value=self.app.store.repo, height=34,
                                font_size=8, mono=True)
        self.repo_input.pack(side="left", fill="x", expand=True)
        GhostButton(repo_row, "保存", command=self._save_repo, width=54,
                    height=34, font_size=8).pack(side="left", padx=(u(8), 0))
        tk.Label(repo_row, text=self.app.store.branch, bg=SURFACE,
                 fg=TEXT_MUTE, font=(FONT_MONO, 8)).pack(side="left",
                                                         padx=(u(8), 0))

        self.status_label = tk.Label(body, text="", bg=SURFACE, fg=TEXT_MUTE,
                                     font=(FONT_UI, 8), anchor="w",
                                     justify="left")
        self.status_label.pack(fill="x", pady=(u(6), u(4)))

        tk.Frame(body, bg=BORDER_SOFT, height=1).pack(fill="x", pady=(u(2), u(4)))

        self.list_scroll = ScrollFrame(body, bg=SURFACE)
        self.list_scroll.pack(fill="both", expand=True)

        hint = ("上传方式：在 GitHub 网页新建 packs/你的包名.json 并提交，"
                "机器人自动校验并通过即入库。")
        tk.Label(body, text=hint, bg=SURFACE, fg=TEXT_MUTE, font=(FONT_UI, 7),
                 anchor="w", justify="left").pack(fill="x", pady=(u(6), 0))

    # -------------------------------------------------------------- 右：上传与规范
    def _build_right(self):
        card = Card(self, pad=18, radius=16)
        card.grid(row=0, column=1, sticky="nsew")
        body = card.body

        tk.Label(body, text="上传与格式", bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text="任何人提交合法的 JSON 就会自动入库", bg=SURFACE,
                 fg=TEXT_MUTE, font=(FONT_UI, 8), anchor="w").pack(
            fill="x", pady=(u(2), u(8)))

        steps = [
            "1. 打开 GitHub 上传页，文件名用英文，例如 my-pack.json",
            "2. 粘贴 JSON 内容并提交，机器人会自动校验并合并",
            "3. 回到这里点「同步」，新指令立刻出现在模组索引里",
        ]
        for step in steps:
            tk.Label(body, text=step, bg=SURFACE, fg=TEXT_SUB,
                     font=(FONT_UI, 8), anchor="w", justify="left",
                     wraplength=u(260)).pack(fill="x", pady=(0, u(3)))

        btns = tk.Frame(body, bg=SURFACE)
        btns.pack(fill="x", pady=(u(8), u(6)))
        PrimaryButton(btns, "打开上传页", command=self._open_upload,
                      width=92, height=34, font_size=9).pack(side="left")
        GhostButton(btns, "导入本地 JSON", command=self._import_local,
                    width=96, height=34, font_size=8).pack(side="left",
                                                           padx=(u(6), 0))
        GhostButton(btns, "复制示例", command=self._copy_sample,
                    width=70, height=34, font_size=8).pack(side="left",
                                                           padx=(u(6), 0))

        self.result_frame = tk.Frame(body, bg=SURFACE)
        self.result_frame.pack(fill="x")

        tk.Frame(body, bg=BORDER_SOFT, height=1).pack(fill="x", pady=(u(10), u(6)))

        tk.Label(body, text="格式规范 · mc-cmd-pack/1", bg=SURFACE,
                 fg=TEXT_MUTE, font=(FONT_UI, 8), anchor="w").pack(fill="x")

        rules = "\n".join("· " + rule for rule in pack_spec.RULES[:5])
        tk.Label(body, text=rules, bg=SURFACE, fg=TEXT_SUB, font=(FONT_UI, 7),
                 anchor="w", justify="left",
                 wraplength=u(268)).pack(fill="x", pady=(u(4), u(6)))

        scroll = ScrollFrame(body, bg=SURFACE)
        scroll.pack(fill="both", expand=True)
        code = tk.Label(scroll.inner, text=pack_spec.SPEC_DOC, bg=SURFACE_SOFT,
                        fg=TEXT_SUB, font=(FONT_MONO, 7), anchor="w",
                        justify="left", padx=u(10), pady=u(8))
        code.pack(fill="x")

    # -------------------------------------------------------------- 数据刷新
    def refresh(self):
        packs = self.app.packs
        total = sum(len(pack.get("items", [])) for pack in packs)
        self.count_label.configure(text="%d 个包 · %d 条指令" % (len(packs), total))

        state = "线上模式" if self.app.mode == "online" else "离线模式"
        repo = self.app.store.repo or "未设置仓库"
        message = self.app.sync_message or online.cache_age_text()
        self.status_label.configure(text="%s · %s · %s" % (state, repo, message))

        self.repo_input.set(self.app.store.repo)

        inner = self.list_scroll.inner
        for child in inner.winfo_children():
            child.destroy()

        if not packs:
            tk.Label(inner, text=("还没有指令包\n"
                                  "填好 owner/repo 后点「同步」，或在浏览器上传后同步"),
                     bg=SURFACE, fg=TEXT_MUTE, font=(FONT_UI, 9),
                     justify="left").pack(anchor="w", padx=u(4), pady=u(32))
            return

        for index, pack in enumerate(packs):
            if index:
                tk.Frame(inner, bg=BORDER_SOFT, height=1).pack(fill="x")
            self._make_pack_row(inner, pack)

    def _make_pack_row(self, parent, pack):
        row = tk.Frame(parent, bg=SURFACE)
        row.pack(fill="x", pady=u(7))

        top = tk.Frame(row, bg=SURFACE)
        top.pack(fill="x")
        tk.Label(top, text=pack["name"], bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 9, "bold")).pack(side="left")
        tk.Label(top, text="%d 条" % len(pack.get("items", [])),
                 bg=ACCENT_TINT, fg=ACCENT_DEEP, font=(FONT_UI, 7),
                 padx=u(6), pady=u(2)).pack(side="left", padx=(u(8), 0))
        if pack.get("author"):
            tk.Label(top, text=pack["author"], bg=SURFACE, fg=TEXT_MUTE,
                     font=(FONT_UI, 7)).pack(side="right")

        tk.Label(row, text=pack.get("description", ""), bg=SURFACE,
                 fg=TEXT_SUB, font=(FONT_UI, 8), anchor="w", justify="left",
                 wraplength=u(360)).pack(fill="x", pady=(u(2), u(4)))

        actions = tk.Frame(row, bg=SURFACE)
        actions.pack(fill="x")
        pack_id = "pack:%s" % online_pack_id(pack)
        GhostButton(actions, "查看指令",
                    command=lambda p=pack_id: self.app.open_pack(p),
                    width=78, height=28, font_size=7).pack(side="left")
        GhostButton(actions, "复制全部",
                    command=lambda p=pack: self._copy_pack(p),
                    width=72, height=28, font_size=7).pack(side="left",
                                                           padx=(u(6), 0))
        tk.Label(actions, text=pack.get("file", ""), bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_MONO, 7)).pack(side="right")

    # -------------------------------------------------------------- 操作
    def _save_repo(self):
        repo = online.normalize_repo(self.repo_input.get())
        if not repo:
            self.app.notify("请填写 owner/repo 形式的仓库地址")
            return
        self.app.store.repo = repo
        self.repo_input.set(repo)
        self.app.sync_message = ""
        self.app.notify("仓库已保存：%s" % repo)
        self.refresh()

    def _sync(self):
        self.app.store.repo = online.normalize_repo(self.repo_input.get())
        if not self.app.store.repo:
            self.app.notify("请先填写仓库地址，例如 yourname/mc-cmd-packs")
            return
        self.app.sync_online(manual=True)

    def _open_upload(self):
        repo = online.normalize_repo(self.repo_input.get()) or self.app.store.repo
        if not repo:
            self.app.notify("请先填写仓库地址")
            return
        url = online.upload_url(repo, self.app.store.branch)
        self.app.open_url(url)

    def _copy_sample(self):
        self.app.copy(pack_spec.example_text())

    def _copy_pack(self, pack):
        commands = [item["command"] for item in pack.get("items", [])]
        if commands:
            self.app.copy("\n".join(commands))

    def _import_local(self):
        path = filedialog.askopenfilename(
            title="选择指令包 JSON", filetypes=[("JSON 文件", "*.json"),
                                            ("所有文件", "*.*")])
        if not path:
            return
        try:
            with open(path, "rb") as handle:
                raw = handle.read()
            text = raw.decode("utf-8")
        except (IOError, OSError):
            self._show_result(False, "无法读取文件", [])
            return
        except UnicodeDecodeError:
            self._show_result(False, "文件必须是 UTF-8 编码", [])
            return

        data, errors = pack_spec.parse_json(text)
        if errors:
            self._show_result(False, "JSON 解析失败", errors)
            return
        pack, errors = pack_spec.validate_pack(data)
        if errors:
            self._show_result(False, "格式校验未通过", errors)
            return

        self._show_result(True, "校验通过：%s，共 %d 条指令" % (
            pack["name"], len(pack["items"])), [])
        self.app.copy(json.dumps(pack, ensure_ascii=False, indent=2))
        self.app.notify("校验通过，已把规范化 JSON 复制到剪贴板，可直接粘贴上传")

    def _show_result(self, ok, title, errors):
        for child in self.result_frame.winfo_children():
            child.destroy()

        color = GREEN if ok else ORANGE
        tk.Label(self.result_frame, text=title, bg=SURFACE, fg=color,
                 font=(FONT_UI, 8, "bold"), anchor="w",
                 justify="left").pack(fill="x", pady=(u(6), u(2)))
        for item in errors[:6]:
            text = "%s：%s" % (item.get("path", "?"), item["message"])
            tk.Label(self.result_frame, text=text, bg=SURFACE, fg=TEXT_SUB,
                     font=(FONT_UI, 8), anchor="w", justify="left",
                     wraplength=u(250)).pack(fill="x", pady=(0, u(2)))
        if len(errors) > 6:
            tk.Label(self.result_frame, text="…还有 %d 条错误" % (len(errors) - 6),
                     bg=SURFACE, fg=TEXT_MUTE, font=(FONT_UI, 7),
                     anchor="w").pack(fill="x")


def online_pack_id(pack):
    return pack.get("id") or pack_spec.pack_id_for(pack.get("name", ""))
