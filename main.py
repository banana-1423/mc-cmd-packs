# -*- coding: utf-8 -*-
"""MC 指令工具台 · 主窗口

明亮、简洁、科幻感的桌面工具，纯标准库 tkinter：

    python main.py
    python main.py --page 2      # 直接打开指定页面
"""

import importlib
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import font as tkfont

import data_mods
import data_vanilla
import online
import pack_spec
import ui
from data_common import CATEGORIES, VERSIONS, build_index
from store import Store
from ui import (ACCENT, ACCENT_DEEP, ACCENT_TINT, BG, BORDER, BORDER_SOFT,
                FONT_MONO, FONT_UI, GREEN, SURFACE, SURFACE_TINT, TEXT,
                TEXT_MUTE, TEXT_SUB, WHITE, Card, Chip, Dropdown, NavItem,
                bind_tree, u)
from view_composer import ComposerView
from view_explorer import ExplorerView
from view_misc import FavoritesView, SettingsView
from view_packs import PacksView
from view_server import ServerView

APP_TITLE = "MC 指令工具台"
APP_VERSION = "v0.3.0"

PAGES = [
    ("指令速查", "原版指令检索 · 参数解释 · 一键复制"),
    ("命令生成", "选模板、填参数，实时生成可复制的指令"),
    ("模组索引", "热门模组与线上指令包的快捷指令"),
    ("服务器", "server.properties 编辑与服务器指令"),
    ("收藏夹", "你保存下来的常用指令"),
    ("指令包", "线上同步 · 上传指引 · 格式校验"),
    ("设置", "版本、数据与本地状态"),
]


class App(object):
    def __init__(self, root, start_page=0):
        self.root = root
        self.store = Store()
        self.version = self.store.version
        self.mode = self.store.mode

        self.vanilla_entries = data_vanilla.VANILLA
        self.mod_entries = data_mods.MOD_COMMANDS
        self.packs = []
        self.pack_entries = []
        self.sync_message = ""
        self.sync_busy = False
        self._load_cached_packs()
        self._rebuild_index()

        self.pages = {}
        self.nav_items = []
        self.current = None
        self.status_text = tk.StringVar(value="就绪 · 本地模式")

        self._build()
        self.show_page(start_page)
        self.root.bind("<Control-c>", self._on_ctrl_c)

        if self.mode == "online" and self.store.repo:
            self.root.after(600, lambda: self.sync_online())

    # -------------------------------------------------------------- 数据
    def _rebuild_index(self):
        self.index = {}
        for entry in self.vanilla_entries + self.mod_entries + self.pack_entries:
            self.index[entry["id"]] = entry
        self.vanilla_count = len(self.vanilla_entries)
        self.mod_count = len(self.mod_entries)
        self.pack_count = len(self.pack_entries)

    def _load_cached_packs(self):
        cached = online.load_cache()
        packs = []
        for item in (cached or {}).get("packs", []):
            pack, errors = pack_spec.ensure_pack(item)
            if pack is None:
                continue
            pack["id"] = item.get("id") or pack_spec.pack_id_for(pack["name"])
            pack["file"] = item.get("file", "")
            packs.append(pack)
        self.packs = packs
        self._rebuild_pack_entries()

    def _rebuild_pack_entries(self):
        entries = []
        for pack in self.packs:
            pack_id = pack.get("id") or pack_spec.pack_id_for(pack["name"])
            entries.extend(pack_spec.pack_to_entries(pack, pack_id))
        self.pack_entries = entries
        build_index(entries)

    def _mod_filters(self):
        filters = [("全部", "全部")]
        filters.extend((mod["id"], mod["name"]) for mod in data_mods.MODS)
        for pack in self.packs:
            pack_id = "pack:%s" % (pack.get("id") or
                                   pack_spec.pack_id_for(pack["name"]))
            filters.append((pack_id, pack["name"]))
        return filters

    def set_packs(self, packs):
        self.packs = packs
        self._rebuild_pack_entries()
        self._rebuild_index()
        self._update_count()

        mods_page = self.pages.get(2)
        if mods_page is not None:
            mods_page.entries = self.mod_entries + self.pack_entries
            mods_page.set_filters(self._mod_filters())
            mods_page.sync_fav()
        favorites = self.pages.get(4)
        if favorites is not None:
            favorites.refresh()
        packs_page = self.pages.get(5)
        if packs_page is not None:
            packs_page.refresh()

    # -------------------------------------------------------------- 线上同步
    def sync_online(self, manual=False):
        if self.sync_busy:
            return
        repo = online.normalize_repo(self.store.repo)
        if not repo:
            self.sync_message = "未设置仓库地址"
            self.notify("先在「指令包」页填写 owner/repo")
            self._refresh_packs_page()
            return
        self.sync_busy = True
        self.sync_message = "同步中…"
        self._refresh_packs_page()

        def work():
            result = online.sync(repo, self.store.branch)
            self.root.after(0, lambda: self._on_sync_done(result))

        threading.Thread(target=work, daemon=True).start()

    def _on_sync_done(self, result):
        self.sync_busy = False
        self.sync_message = result["message"]
        if result["ok"] and result["packs"]:
            self.set_packs(result["packs"])
        self._refresh_packs_page()
        self.notify(result["message"])

    def _refresh_packs_page(self):
        page = self.pages.get(5)
        if page is not None:
            page.refresh()

    def set_mode(self, mode):
        mode = "online" if mode == "online" else "offline"
        if mode == self.mode:
            return
        self.mode = mode
        self.store.mode = mode
        self._sync_mode_chips()
        if mode == "online":
            self.sync_online()
            self.notify("已切换到线上模式")
        else:
            self.notify("已切换到离线模式")
        self.status_right.configure(text=self._status_right(self.current))

    def _sync_mode_chips(self):
        self.mode_offline.set_active(self.mode == "offline")
        self.mode_online.set_active(self.mode == "online")

    def open_url(self, url):
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 打开浏览器失败不应影响使用
            pass

    def open_pack(self, pack_id):
        self.show_page(2)
        page = self.pages.get(2)
        if page is not None:
            page._set_filter(pack_id)

    def reload_data(self):
        importlib.reload(data_vanilla)
        importlib.reload(data_mods)
        self.vanilla_entries = data_vanilla.VANILLA
        self.mod_entries = data_mods.MOD_COMMANDS
        self._rebuild_index()
        for key in (0, 2):
            page = self.pages.get(key)
            if page is not None:
                if key == 0:
                    page.entries = self.vanilla_entries
                    page.refresh()
                else:
                    page.entries = self.mod_entries + self.pack_entries
                    page.set_filters(self._mod_filters())
        self.notify("指令数据已重新载入")

    # -------------------------------------------------------------- 布局
    def _build(self):
        self.sidebar = tk.Frame(self.root, bg=SURFACE, width=u(236))
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        right = tk.Frame(self.root, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_header(right)
        self._build_status(right)
        self._update_count()

        self.container = tk.Frame(right, bg=BG)
        self.container.pack(fill="both", expand=True, padx=u(24),
                            pady=(0, u(4)))

    def _build_sidebar(self):
        bar = self.sidebar

        brand = tk.Frame(bar, bg=SURFACE)
        brand.pack(fill="x", padx=u(20), pady=(u(20), u(18)))

        mark = tk.Canvas(brand, width=u(36), height=u(36), bg=SURFACE,
                         highlightthickness=0, bd=0)
        mark.pack(side="left")
        ui.rounded(mark, u(1), u(1), u(35), u(35), u(11), fill=ACCENT, outline="")
        ui.rounded(mark, u(9), u(9), u(27), u(27), u(6), fill=WHITE, outline="")
        mark.create_text(u(18), u(18), text="MC", font=(FONT_UI, 6, "bold"),
                         fill=ACCENT)

        titles = tk.Frame(brand, bg=SURFACE)
        titles.pack(side="left", padx=(u(10), 0), fill="x")
        tk.Label(titles, text="指令工具台", bg=SURFACE, fg=TEXT,
                 font=(FONT_UI, 11, "bold")).pack(anchor="w")
        tk.Label(titles, text="COMMAND TOOLKIT", bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_MONO, 7)).pack(anchor="w")

        tk.Frame(bar, bg=BORDER_SOFT, height=u(1)).pack(fill="x")

        tk.Label(bar, text="导航", bg=SURFACE, fg=TEXT_MUTE,
                 font=(FONT_UI, 8)).pack(anchor="w", padx=u(26), pady=(u(16), u(8)))

        for index, (title, _sub) in enumerate(PAGES):
            item = NavItem(bar, "%02d" % (index + 1), title,
                           command=lambda i=index: self.show_page(i))
            item.pack(fill="x", pady=u(1))
            self.nav_items.append(item)

        bottom = tk.Frame(bar, bg=SURFACE)
        bottom.pack(side="bottom", fill="x", padx=u(20), pady=u(16))

        tk.Frame(bottom, bg=BORDER_SOFT, height=u(1)).pack(fill="x")
        row = tk.Frame(bottom, bg=SURFACE)
        row.pack(fill="x", pady=(u(14), 0))
        self.mode_dot = tk.Canvas(row, width=u(8), height=u(8), bg=SURFACE,
                                  highlightthickness=0, bd=0)
        self.mode_dot.pack(side="left", pady=(u(2), 0))
        self.mode_dot.create_oval(0, 0, u(7), u(7), fill=GREEN, outline="")
        self.mode_label = tk.Label(row, text="离线模式", bg=SURFACE,
                                   fg=TEXT_SUB, font=(FONT_UI, 8))
        self.mode_label.pack(side="left", padx=(u(6), 0))

        tk.Label(bottom, text="%s · 明亮主题" % APP_VERSION, bg=SURFACE,
                 fg=TEXT_MUTE, font=(FONT_UI, 8)).pack(anchor="w", pady=(u(4), 0))

        tk.Frame(bar, bg=BORDER, width=u(1)).place(relx=1.0, rely=0,
                                                   relheight=1.0, x=-u(1))

    def _build_header(self, parent):
        header = tk.Frame(parent, bg=BG, height=u(82))
        header.pack(side="top", fill="x", padx=u(24))
        header.pack_propagate(False)

        left = tk.Frame(header, bg=BG)
        left.pack(side="left", fill="y", pady=u(16))
        self.header_title = tk.Label(left, text="", bg=BG, fg=TEXT,
                                     font=(FONT_UI, 16, "bold"), anchor="w")
        self.header_title.pack(anchor="w")
        self.header_sub = tk.Label(left, text="", bg=BG, fg=TEXT_SUB,
                                   font=(FONT_UI, 9), anchor="w")
        self.header_sub.pack(anchor="w", pady=(u(2), 0))

        right = tk.Frame(header, bg=BG)
        right.pack(side="right", fill="y", pady=u(16))

        self.mode_offline = Chip(right, "离线", height=30, font_size=8,
                                 command=lambda: self.set_mode("offline"))
        self.mode_offline.pack(side="left")
        self.mode_online = Chip(right, "线上", height=30, font_size=8,
                                command=lambda: self.set_mode("online"))
        self.mode_online.pack(side="left", padx=(u(6), u(14)))
        self._sync_mode_chips()

        tk.Label(right, text="游戏版本", bg=BG, fg=TEXT_MUTE,
                 font=(FONT_UI, 8)).pack(side="left", padx=(0, u(8)))
        self.version_dd = Dropdown(right, VERSIONS, value=self.version,
                                   width=104, height=34, font_size=9,
                                   command=self.set_version)
        self.version_dd.pack(side="left")

    def _build_status(self, parent):
        bar = tk.Frame(parent, bg=BG, height=u(34))
        bar.pack(side="bottom", fill="x", padx=u(24))
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=BG)
        left.pack(side="left", pady=u(8))
        dot = tk.Canvas(left, width=u(7), height=u(7), bg=BG,
                        highlightthickness=0, bd=0)
        dot.pack(side="left", pady=(u(2), 0))
        dot.create_oval(0, 0, u(6), u(6), fill=GREEN, outline="")
        tk.Label(left, textvariable=self.status_text, bg=BG, fg=TEXT_SUB,
                 font=(FONT_UI, 8)).pack(side="left", padx=(u(6), 0))

        self.status_right = tk.Label(bar, text="", bg=BG,
                                     fg=TEXT_MUTE, font=(FONT_UI, 8))
        self.status_right.pack(side="right", pady=u(8))

        self.count_label = tk.Label(bar, text="", bg=BG, fg=TEXT_MUTE,
                                    font=(FONT_UI, 8))
        self.count_label.pack(side="right", padx=(0, u(14)), pady=u(8))

    # -------------------------------------------------------------- 页面
    def _ensure_page(self, index):
        if index in self.pages:
            return self.pages[index]
        if index == 0:
            filters = [("全部", "全部")] + [(c, c) for c in CATEGORIES]
            page = ExplorerView(self.container, self, self.vanilla_entries,
                                filters, filter_kind="category")
        elif index == 2:
            page = ExplorerView(self.container, self,
                                self.mod_entries + self.pack_entries,
                                self._mod_filters(), filter_kind="mod",
                                placeholder="搜索模组 / 指令包，例如 carpet / 假人")
        elif index == 1:
            page = ComposerView(self.container, self)
        elif index == 3:
            page = ServerView(self.container, self)
        elif index == 4:
            page = FavoritesView(self.container, self)
            self.favorites_view = page
        elif index == 5:
            page = PacksView(self.container, self)
        else:
            page = SettingsView(self.container, self)
        self.pages[index] = page
        return page

    def show_page(self, index):
        if self.current == index:
            return
        if self.current is not None:
            self.pages[self.current].pack_forget()
        page = self._ensure_page(index)
        page.pack(fill="both", expand=True)
        self.current = index

        for i, item in enumerate(self.nav_items):
            item.set_active(i == index)

        self.header_title.configure(text=PAGES[index][0])
        self.header_sub.configure(text=PAGES[index][1])
        self.status_text.set(self._page_status(index))
        self.status_right.configure(text=self._status_right(index))

        if index in (4, 5):
            page.refresh()
        elif index == 6:
            page.refresh()
        elif hasattr(page, "sync_fav"):
            page.sync_fav()

    def _page_status(self, index):
        if index == 4:
            return "收藏夹 · 共 %d 条" % len(self.store.favorites)
        if index == 5:
            return "指令包 · %d 个包 / %d 条指令" % (
                len(self.packs), len(self.pack_entries))
        if index == 6:
            return "设置 · 版本 %s · %s" % (
                self.version, "线上" if self.mode == "online" else "离线")
        return "%s · 共 %d 条指令" % (PAGES[index][0], len(self.index))

    def _status_right(self, index):
        mode = "线上模式" if self.mode == "online" else "离线模式"
        base = "%s · 版本 %s" % (mode, self.version)
        if index in (0, 2):
            return "Ctrl+C 复制当前示例 · " + base
        if index == 5:
            return (self.store.repo or "未设置仓库") + " · " + base
        return base

    # -------------------------------------------------------------- 公共动作
    def _on_ctrl_c(self, _event=None):
        focus = self.root.focus_get()
        if isinstance(focus, (tk.Entry, tk.Text)):
            return
        page = self.pages.get(self.current)
        if page is None:
            return
        if self.current in (0, 2) and getattr(page, "_selected", None):
            page._copy_example()
        elif self.current == 1:
            page._copy()

    def copy(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update_idletasks()
        except tk.TclError:
            pass
        self.notify("已复制：%s" % text)

    def notify(self, text):
        self.status_text.set(text)

    def toggle_favorite(self, cmd_id):
        flag = self.store.toggle_favorite(cmd_id)
        if getattr(self, "favorites_view", None) is not None:
            self.favorites_view.refresh()
        return flag

    def set_version(self, value):
        if value == self.version:
            return
        self.version = value
        self.store.version = value
        for key in (0, 2):
            page = self.pages.get(key)
            if page is not None:
                page.refresh()
        composer = self.pages.get(1)
        if composer is not None:
            composer._update_preview()
        settings = self.pages.get(6)
        if settings is not None:
            settings.refresh()
        self.version_dd.set(value)
        self.status_right.configure(text=self._status_right(self.current)
                                    if self.current is not None else "")
        self.notify("已切换到版本 %s" % value)

    def _update_count(self):
        text = "原版 %d · 模组 %d" % (self.vanilla_count, self.mod_count)
        if self.pack_entries:
            text += " · 包 %d" % len(self.pack_entries)
        self.count_label.configure(text=text)


# ------------------------------------------------------------------ 启动
def compute_scale(root):
    try:
        dpi = root.winfo_fpixels("1i")
    except tk.TclError:
        return 1.0
    return max(1.0, min(3.0, dpi / 96.0))


def center(root, width, height):
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    win_w = min(u(width), screen_w - u(60))
    win_h = min(u(height), screen_h - u(100))
    x = max(u(20), int((screen_w - win_w) / 2))
    y = max(u(20), int((screen_h - win_h) / 2) - u(20))
    root.geometry("%dx%d+%d+%d" % (win_w, win_h, x, y))


def fade_in(root, steps=8, interval=16):
    try:
        root.attributes("-alpha", 0.0)
    except tk.TclError:
        return

    def step(i):
        try:
            if i > steps:
                root.attributes("-alpha", 1.0)
                return
            root.attributes("-alpha", min(1.0, (i / float(steps)) ** 0.7))
            root.after(interval, step, i + 1)
        except tk.TclError:
            pass

    root.after(interval, step, 1)


def enable_dpi_awareness():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def main():
    enable_dpi_awareness()

    root = tk.Tk()
    root.title(APP_TITLE)
    root.configure(bg=BG)

    ui.SCALE = compute_scale(root)
    ui.resolve_fonts(root)
    root.minsize(u(1100), u(710))
    center(root, 1160, 760)

    start_page = 0
    if "--page" in sys.argv:
        try:
            start_page = max(0, min(len(PAGES) - 1,
                                    int(sys.argv[sys.argv.index("--page") + 1])))
        except (IndexError, ValueError):
            start_page = 0

    app = App(root, start_page)

    if "--selftest" in sys.argv:
        root.update()
        for index in range(len(PAGES)):
            app.show_page(index)
            root.update()
            root.update_idletasks()
        root.update()
        print("selftest ok: scale=%.2f size=%sx%s pages=%d packs=%d" % (
            ui.SCALE, root.winfo_width(), root.winfo_height(),
            len(app.pages), len(app.packs)))
        root.after(400, root.destroy)
        root.mainloop()
        return

    fade_in(root)
    root.mainloop()


if __name__ == "__main__":
    main()
