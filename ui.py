# -*- coding: utf-8 -*-
"""界面主题与基础组件（明亮科技风，纯 tkinter）。"""

import tkinter as tk
from tkinter import font as tkfont

# ------------------------------------------------------------------ 配色
BG = "#F3F7FC"
SURFACE = "#FFFFFF"
SURFACE_SOFT = "#F5F9FE"
SURFACE_TINT = "#EAF2FE"
BORDER = "#E1EAF6"
BORDER_SOFT = "#EDF3FA"
ACCENT = "#2F7CF6"
ACCENT_DEEP = "#1B58D0"
ACCENT_TINT = "#E8F1FF"
CYAN = "#0FB0A6"
GREEN = "#2BB673"
ORANGE = "#E8833A"
TEXT = "#17243C"
TEXT_SUB = "#63738D"
TEXT_MUTE = "#94A3B8"
WHITE = "#FFFFFF"

FONT_UI = "Microsoft YaHei UI"
FONT_MONO = "Consolas"

SCALE = 1.0


def u(value):
    """设计稿像素 → 当前屏幕像素。"""
    return int(round(value * SCALE))


# ------------------------------------------------------------------ 绘图工具
def blend(c1, c2, t):
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded(canvas, x1, y1, x2, y2, r=12, **kw):
    """圆角矩形。"""
    r = max(0.0, min(r, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1,
        x2, y1 + r, x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2, x1, y2,
        x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, splinesteps=36, **kw)


def bind_tree(widget, seq, func):
    widget.bind(seq, func)
    for child in widget.winfo_children():
        bind_tree(child, seq, func)


def resolve_fonts(root):
    global FONT_UI, FONT_MONO
    families = set(tkfont.families(root))
    for name in ("Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "Segoe UI"):
        if name in families:
            FONT_UI = name
            break
    for name in ("Consolas", "Cascadia Mono", "Courier New"):
        if name in families:
            FONT_MONO = name
            break


_font_cache = {}


def ui_font(size, weight="normal"):
    key = (FONT_UI, size, weight)
    if key not in _font_cache:
        _font_cache[key] = tkfont.Font(family=FONT_UI, size=size, weight=weight)
    return _font_cache[key]


def mono_font(size, weight="normal"):
    key = (FONT_MONO, size, weight)
    if key not in _font_cache:
        _font_cache[key] = tkfont.Font(family=FONT_MONO, size=size, weight=weight)
    return _font_cache[key]


def text_width(text, size=9, mono=False, weight="normal"):
    font = mono_font(size, weight) if mono else ui_font(size, weight)
    return font.measure(text)


def hairline(parent, color=BORDER_SOFT, pady=0):
    line = tk.Frame(parent, bg=color, height=max(1, u(1)))
    line.pack(fill="x", pady=pady)
    return line


# ------------------------------------------------------------------ 卡片
class Card(tk.Frame):
    """圆角浅阴影卡片，内容放在 self.body。"""

    def __init__(self, master, pad=18, radius=16, fill=SURFACE,
                 outline=BORDER, shadow=True, **kw):
        tk.Frame.__init__(self, master, bg=master.cget("bg"), **kw)
        self._pad = u(pad)
        self._radius = u(radius)
        self._fill = fill
        self._outline = outline
        self._shadow = shadow

        self.canvas = tk.Canvas(self, bg=master.cget("bg"),
                                highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.body = tk.Frame(self, bg=fill)
        self.body.place(x=self._pad, y=self._pad, width=1, height=1)

        self.bind("<Configure>", self._redraw)

    def set_fill(self, fill):
        self._fill = fill
        self.body.configure(bg=fill)
        self._redraw()

    def _redraw(self, _event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 2 or h <= 2:
            return
        c = self.canvas
        c.delete("all")
        base = self.master.cget("bg")

        if self._shadow:
            for dy, strength in ((5, 0.05), (4, 0.07), (3, 0.09), (2, 0.11)):
                rounded(c, u(3), u(3 + dy), w - u(3), h - u(2),
                        self._radius, fill=blend(base, "#8CA4C4", strength),
                        outline="")
        rounded(c, u(1), u(1), w - u(1), h - u(2), self._radius,
                fill=self._fill, outline=self._outline, width=1)
        self.body.place_configure(
            width=max(1, w - 2 * self._pad),
            height=max(1, h - 2 * self._pad),
        )


# ------------------------------------------------------------------ 导航项
class NavItem(tk.Canvas):
    def __init__(self, master, index, label, command=None):
        tk.Canvas.__init__(self, master, height=u(40), bg=master.cget("bg"),
                           highlightthickness=0, bd=0, cursor="hand2")
        self._index = index
        self._label = label
        self._hover = False
        self._active = False
        self._command = command
        self._badge = ""
        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)

    def set_active(self, flag):
        if self._active != flag:
            self._active = flag
            self._draw()

    def set_badge(self, text):
        self._badge = text
        self._draw()

    def _on_enter(self, _e):
        self._hover = True
        self._draw()

    def _on_leave(self, _e):
        self._hover = False
        self._draw()

    def _on_click(self, _e):
        if self._command:
            self._command()

    def _draw(self, _event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 2:
            return
        self.delete("all")
        if self._active:
            rounded(self, u(10), u(1), w - u(12), h - u(1), u(10),
                    fill=ACCENT_TINT, outline="")
            rounded(self, u(12), h / 2 - u(9), u(15), h / 2 + u(9), u(1.5),
                    fill=ACCENT, outline="")
            fg_main, fg_index, weight = ACCENT_DEEP, ACCENT, "bold"
        elif self._hover:
            rounded(self, u(10), u(1), w - u(12), h - u(1), u(10),
                    fill="#F4F9FF", outline="")
            fg_main, fg_index, weight = TEXT, TEXT_MUTE, "normal"
        else:
            fg_main, fg_index, weight = TEXT_SUB, TEXT_MUTE, "normal"

        self.create_text(u(28), h / 2, text=self._index, anchor="w",
                         font=(FONT_MONO, 8), fill=fg_index)
        self.create_text(u(54), h / 2, text=self._label, anchor="w",
                         font=(FONT_UI, 10, weight), fill=fg_main)
        if self._badge:
            self.create_text(w - u(22), h / 2, text=self._badge, anchor="e",
                             font=(FONT_UI, 8), fill=TEXT_MUTE)


# ------------------------------------------------------------------ 按钮
class PrimaryButton(tk.Canvas):
    def __init__(self, master, text, command=None, width=104, height=40,
                 radius=10, font_size=10):
        self._btn_w = u(width)
        self._btn_h = u(height)
        tk.Canvas.__init__(self, master, width=self._btn_w, height=self._btn_h,
                           bg=master.cget("bg"), highlightthickness=0, bd=0,
                           cursor="hand2")
        self._text = text
        self._command = command
        self._radius = u(radius)
        self._font_size = font_size
        self._state = "normal"
        self._enabled_flag = True
        self.bind("<Enter>", lambda e: self._set("hover"))
        self.bind("<Leave>", lambda e: self._set("normal"))
        self.bind("<ButtonPress-1>", lambda e: self._set("press"))
        self.bind("<ButtonRelease-1>", self._release)
        self._draw()

    def set_text(self, text):
        self._text = text
        self._draw()

    def set_enabled(self, flag):
        self._enabled_flag = flag
        self.configure(cursor="hand2" if flag else "arrow")
        self._draw()

    def _set(self, state):
        self._state = state
        self._draw()

    def _release(self, event):
        inside = 0 <= event.x <= self._btn_w and 0 <= event.y <= self._btn_h
        self._set("hover" if inside else "normal")
        if inside and self._command and self._enabled_flag:
            self._command()

    def _draw(self):
        self.delete("all")
        fill = ACCENT
        if not self._enabled_flag:
            fill = blend(ACCENT, WHITE, 0.55)
        elif self._state == "hover":
            fill = blend(ACCENT, WHITE, 0.12)
        elif self._state == "press":
            fill = ACCENT_DEEP
        offset = u(1) if self._state == "press" else 0
        rounded(self, u(1), u(1) + offset, self._btn_w - u(1),
                self._btn_h - u(1) + offset, self._radius,
                fill=fill, outline="")
        self.create_text(self._btn_w / 2, self._btn_h / 2 + offset,
                         text=self._text, font=(FONT_UI, self._font_size, "bold"),
                         fill=WHITE)


class GhostButton(tk.Canvas):
    """描边按钮，用于次级操作。"""

    def __init__(self, master, text, command=None, width=None, height=36,
                 radius=10, font_size=9, accent=False):
        self._btn_h = u(height)
        self._btn_w = u(width) if width else text_width(text, font_size) + u(34)
        tk.Canvas.__init__(self, master, width=self._btn_w, height=self._btn_h,
                           bg=master.cget("bg"), highlightthickness=0, bd=0,
                           cursor="hand2")
        self._text = text
        self._command = command
        self._radius = u(radius)
        self._font_size = font_size
        self._accent = accent
        self._state = "normal"
        self._enabled = True
        self.bind("<Enter>", lambda e: self._set("hover"))
        self.bind("<Leave>", lambda e: self._set("normal"))
        self.bind("<ButtonRelease-1>", self._release)
        self._draw()

    def set_enabled(self, flag):
        self._enabled = flag
        self.configure(cursor="hand2" if flag else "arrow")
        self._draw()

    def _set(self, state):
        if not self._enabled:
            return
        self._state = state
        self._draw()

    def _release(self, event):
        inside = 0 <= event.x <= self._btn_w and 0 <= event.y <= self._btn_h
        self._set("hover" if inside else "normal")
        if inside and self._enabled and self._command:
            self._command()

    def _draw(self):
        self.delete("all")
        if not self._enabled:
            fill, outline, fg = SURFACE_SOFT, BORDER_SOFT, TEXT_MUTE
        elif self._state == "hover":
            fill = ACCENT_TINT if self._accent else "#F4F9FF"
            outline = blend(ACCENT, WHITE, 0.45)
            fg = ACCENT_DEEP
        else:
            fill = ACCENT_TINT if self._accent else SURFACE
            outline = blend(ACCENT, WHITE, 0.6) if self._accent else BORDER
            fg = ACCENT_DEEP if self._accent else TEXT_SUB
        rounded(self, u(1), u(1), self._btn_w - u(1), self._btn_h - u(1),
                self._radius, fill=fill, outline=outline, width=1)
        self.create_text(self._btn_w / 2, self._btn_h / 2, text=self._text,
                         font=(FONT_UI, self._font_size), fill=fg)


# ------------------------------------------------------------------ 搜索框
class SearchBar(tk.Frame):
    def __init__(self, master, width=360, height=42,
                 placeholder="搜索指令、关键词或模组"):
        self._bar_w = u(width)
        self._bar_h = u(height)
        tk.Frame.__init__(self, master, width=self._bar_w, height=self._bar_h,
                          bg=master.cget("bg"))
        self._placeholder = placeholder
        self._focused = False
        self._hover = False
        self._placeholder_on = False

        self.canvas = tk.Canvas(self, bg=master.cget("bg"),
                                highlightthickness=0, bd=0, cursor="xterm")
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var, bd=0, relief="flat",
                              bg=SURFACE_SOFT, fg=TEXT, highlightthickness=0,
                              insertbackground=ACCENT, font=(FONT_UI, 10))
        self._win = self.canvas.create_window(
            u(44), self._bar_h / 2, window=self.entry, anchor="w",
            width=self._bar_w - u(70), height=self._bar_h - u(16))

        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.canvas.bind("<Enter>", lambda e: self._set_hover(True))
        self.canvas.bind("<Leave>", lambda e: self._set_hover(False))
        self.entry.bind("<FocusIn>", lambda e: self._set_focus(True))
        self.entry.bind("<FocusOut>", lambda e: self._set_focus(False))
        self._apply_placeholder()

    def bind_change(self, func):
        self.var.trace_add("write", lambda *_: func())
        return self

    def bind_return(self, func):
        self.entry.bind("<Return>", lambda e: func())

    def get(self):
        if self._placeholder_on:
            return ""
        return self.var.get().strip()

    def set(self, text):
        self._clear_placeholder()
        self.var.set(text)

    def _set_hover(self, flag):
        self._hover = flag
        self._draw_bg()

    def _set_focus(self, flag):
        self._focused = flag
        if flag:
            self._clear_placeholder()
        else:
            self._apply_placeholder()
        self._draw_bg()

    def _apply_placeholder(self):
        if not self.var.get():
            self._placeholder_on = True
            self.entry.configure(fg=TEXT_MUTE)
            self.var.set(self._placeholder)

    def _clear_placeholder(self):
        if self._placeholder_on:
            self._placeholder_on = False
            self.var.set("")
            self.entry.configure(fg=TEXT)

    def _on_configure(self, _event):
        w = self.canvas.winfo_width()
        self.canvas.coords(self._win, u(44), self._bar_h / 2)
        self.canvas.itemconfigure(self._win, width=max(u(40), w - u(70)))
        self._draw_bg()

    def _draw_bg(self):
        c = self.canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w <= 2:
            return
        c.delete("bg")
        if self._focused:
            fill, outline, icon = WHITE, ACCENT, ACCENT
        elif self._hover:
            fill, outline, icon = WHITE, blend(ACCENT, WHITE, 0.6), TEXT_MUTE
        else:
            fill, outline, icon = SURFACE_SOFT, BORDER, TEXT_MUTE
        rounded(c, u(1), u(1), w - u(1), h - u(1), u(11),
                fill=fill, outline=outline, width=1, tags="bg")
        cy = h / 2.0
        c.create_oval(u(19), cy - u(5), u(29), cy + u(5),
                      outline=icon, width=u(1.4), tags="bg")
        c.create_line(u(29), cy + u(4), u(34), cy + u(9),
                      fill=icon, width=u(1.4), capstyle="round", tags="bg")
        c.tag_lower("bg")
        self.entry.configure(bg=fill)


# ------------------------------------------------------------------ 输入框
class Input(tk.Frame):
    def __init__(self, master, value="", width=200, height=36,
                 font_size=9, mono=False):
        self._h = u(height)
        tk.Frame.__init__(self, master, height=self._h,
                          bg=master.cget("bg"))
        self.canvas = tk.Canvas(self, bg=master.cget("bg"),
                                highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.var = tk.StringVar(value=value)
        self.entry = tk.Entry(
            self, textvariable=self.var, bd=0, relief="flat", bg=SURFACE_SOFT,
            fg=TEXT, highlightthickness=0, insertbackground=ACCENT,
            font=((FONT_MONO if mono else FONT_UI), font_size))
        self._win = self.canvas.create_window(
            u(10), self._h / 2, window=self.entry, anchor="w",
            width=u(width) - u(20), height=self._h - u(14))

        self._focused = False
        self._hover = False
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.canvas.bind("<Enter>", lambda e: self._set_hover(True))
        self.canvas.bind("<Leave>", lambda e: self._set_hover(False))
        self.entry.bind("<FocusIn>", lambda e: self._set_focus(True))
        self.entry.bind("<FocusOut>", lambda e: self._set_focus(False))
        self._draw_bg()

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def bind_change(self, func):
        self.var.trace_add("write", lambda *_: func())

    def _set_hover(self, flag):
        self._hover = flag
        self._draw_bg()

    def _set_focus(self, flag):
        self._focused = flag
        self._draw_bg()

    def _on_configure(self, _event):
        w = self.canvas.winfo_width()
        self.canvas.coords(self._win, u(10), self._h / 2)
        self.canvas.itemconfigure(self._win, width=max(u(30), w - u(20)))
        self._draw_bg()

    def _draw_bg(self):
        c = self.canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w <= 2:
            return
        if self._focused:
            fill, outline = WHITE, ACCENT
        elif self._hover:
            fill, outline = WHITE, blend(ACCENT, WHITE, 0.62)
        else:
            fill, outline = SURFACE_SOFT, BORDER
        c.delete("bg")
        rounded(c, u(1), u(1), w - u(1), h - u(1), u(9), fill=fill,
                outline=outline, width=1, tags="bg")
        c.tag_lower("bg")
        self.entry.configure(bg=fill)


# ------------------------------------------------------------------ 选项标签
class Chip(tk.Canvas):
    def __init__(self, master, text, command=None, active=False,
                 height=28, font_size=9):
        self._text = text
        self._command = command
        self._active = active
        self._hover = False
        self._chip_h = u(height)
        self._chip_w = text_width(text, font_size) + u(26)
        tk.Canvas.__init__(self, master, width=self._chip_w, height=self._chip_h,
                           bg=master.cget("bg"), highlightthickness=0, bd=0,
                           cursor="hand2")
        self._font_size = font_size
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)
        self._draw()

    def set_active(self, flag):
        if self._active != flag:
            self._active = flag
            self._draw()

    def _on_enter(self, _e):
        self._hover = True
        self._draw()

    def _on_leave(self, _e):
        self._hover = False
        self._draw()

    def _on_click(self, _e):
        if self._command:
            self._command()

    def _draw(self):
        self.delete("all")
        if self._active:
            fill, outline, fg = ACCENT, ACCENT, WHITE
        elif self._hover:
            fill, outline, fg = ACCENT_TINT, blend(ACCENT, WHITE, 0.55), ACCENT_DEEP
        else:
            fill, outline, fg = SURFACE, BORDER, TEXT_SUB
        rounded(self, u(1), u(1), self._chip_w - u(1), self._chip_h - u(1),
                self._chip_h / 2.0, fill=fill, outline=outline, width=1)
        self.create_text(self._chip_w / 2, self._chip_h / 2, text=self._text,
                         font=(FONT_UI, self._font_size), fill=fg)


# ------------------------------------------------------------------ 下拉框
class Dropdown(tk.Canvas):
    """轻量下拉选择器（弹出列表，带滚动）。"""

    def __init__(self, master, values, value=None, width=118, height=34,
                 command=None, font_size=9):
        self._dd_w = u(width)
        self._dd_h = u(height)
        tk.Canvas.__init__(self, master, width=self._dd_w, height=self._dd_h,
                           bg=master.cget("bg"), highlightthickness=0, bd=0,
                           cursor="hand2")
        self._values = list(values)
        self._value = value if value is not None else (
            self._values[0] if self._values else "")
        self._command = command
        self._font_size = font_size
        self._hover = False
        self._popup = None
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", self._toggle)
        self.bind("<Configure>", lambda e: self._draw())
        self._draw()

    def get(self):
        return self._value

    def set(self, value):
        if value in self._values:
            self._value = value
            self._draw()

    def set_values(self, values, value=None):
        self._values = list(values)
        if value in self._values:
            self._value = value
        elif self._value not in self._values and self._values:
            self._value = self._values[0]
        self._draw()

    def _set_hover(self, flag):
        self._hover = flag
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        if w <= 1:
            w = self._dd_w
        h = self._dd_h
        outline = blend(ACCENT, WHITE, 0.55) if self._hover else BORDER
        fill = WHITE if self._hover else SURFACE_SOFT
        rounded(self, u(1), u(1), w - u(1), h - u(1), u(9),
                fill=fill, outline=outline, width=1)
        self.create_text(u(12), h / 2, text=self._value, anchor="w",
                         font=(FONT_UI, self._font_size), fill=TEXT)
        cx = w - u(14)
        cy = h / 2 - u(1)
        self.create_line(cx - u(4), cy - u(2), cx, cy + u(2), cx + u(4), cy - u(2),
                         fill=TEXT_MUTE, width=u(1.4), capstyle="round",
                         joinstyle="round")

    def _toggle(self, _event=None):
        if self._popup is not None:
            self._close()
        else:
            self._open()

    def _close(self):
        if self._popup is not None:
            self._popup.destroy()
            self._popup = None

    def _open(self):
        pop = tk.Toplevel(self)
        pop.overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=BORDER)
        self._popup = pop

        inner = tk.Frame(pop, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=u(1), pady=u(1))

        max_rows = 12
        visible = self._values[:max_rows]
        for value in visible:
            row = tk.Label(inner, text=value, anchor="w", bg=SURFACE,
                           fg=TEXT if value != self._value else ACCENT_DEEP,
                           font=(FONT_UI, self._font_size),
                           padx=u(12), pady=u(7))
            row.pack(fill="x")
            row.bind("<Enter>", lambda e, w=row: w.configure(bg=ACCENT_TINT))
            row.bind("<Leave>", lambda e, w=row: w.configure(bg=SURFACE))
            row.bind("<ButtonRelease-1>", lambda e, v=value: self._choose(v))

        pop.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self._dd_h + u(4)
        w = max(self._dd_w, pop.winfo_reqwidth())
        h = pop.winfo_reqheight()
        screen_h = self.winfo_screenheight()
        if y + h > screen_h - u(20):
            y = self.winfo_rooty() - h - u(4)
        pop.geometry("%dx%d+%d+%d" % (w, h, x, y))
        pop.focus_force()
        pop.bind("<FocusOut>", lambda e: self._close())
        pop.bind("<Escape>", lambda e: self._close())

    def _choose(self, value):
        self._value = value
        self._close()
        self._draw()
        if self._command:
            self._command(value)


# ------------------------------------------------------------------ 滚动容器
class SlimScrollbar(tk.Canvas):
    """细圆角滚动条。"""

    def __init__(self, master, command, bg=SURFACE):
        tk.Canvas.__init__(self, master, width=u(8), bg=bg,
                           highlightthickness=0, bd=0)
        self._command = command
        self._first = 0.0
        self._last = 1.0
        self._hover = False
        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._drag)

    def set(self, first, last):
        self._first = float(first)
        self._last = float(last)
        self._draw()

    def _enter(self, _e):
        self._hover = True
        self._draw()

    def _leave(self, _e):
        self._hover = False
        self._draw()

    def _press(self, event):
        self._jump(event.y)

    def _drag(self, event):
        self._jump(event.y)

    def _jump(self, y):
        h = max(1, self.winfo_height())
        span = self._last - self._first
        frac = max(0.0, min(1.0 - span, y / float(h) - span / 2.0))
        self._command("moveto", frac)

    def _draw(self, _event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 2 or h <= 2:
            return
        if self._last - self._first >= 0.999:
            return
        y1 = int(self._first * h)
        y2 = int(self._last * h)
        if y2 - y1 < u(24):
            y2 = y1 + u(24)
            y1 = max(0, min(h - u(24), y1))
            y2 = min(h, y1 + u(24))
        color = blend(ACCENT, WHITE, 0.45) if self._hover else "#C9D8EC"
        rounded(self, u(2), y1 + u(2), w - u(2), y2 - u(2), w / 2.0,
                fill=color, outline="")


class FlowFrame(tk.Frame):
    """自动换行的放置容器（子控件用 add 加入）。"""

    def __init__(self, master, gap=8, bg=None):
        tk.Frame.__init__(self, master, bg=bg or master.cget("bg"))
        self._gap = u(gap)
        self._items = []
        self.bind("<Configure>", self._reflow)

    def add(self, widget):
        self._items.append(widget)
        widget.place(x=0, y=0)
        self._reflow()

    def clear(self):
        for widget in self._items:
            widget.destroy()
        self._items = []
        self.configure(height=1)

    def _reflow(self, _event=None):
        width = self.winfo_width()
        if width <= 1:
            return
        x = y = 0
        row_h = 0
        for item in self._items:
            iw = item.winfo_reqwidth()
            ih = item.winfo_reqheight()
            if x + iw > width and x > 0:
                x = 0
                y += row_h + self._gap
                row_h = 0
            item.place(x=x, y=y, width=iw, height=ih)
            x += iw + self._gap
            row_h = max(row_h, ih)
        self.configure(height=max(1, y + row_h))


class ScrollFrame(tk.Frame):
    """可滚动区域，内容放进 self.inner。"""

    def __init__(self, master, bg=SURFACE, wheel=True):
        tk.Frame.__init__(self, master, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.bar = SlimScrollbar(self, command=self.canvas.yview, bg=bg)
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bar.pack(side="right", fill="y")

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window(u(1), u(1), window=self.inner,
                                              anchor="nw")
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        if wheel:
            self.canvas.bind("<Enter>", self._bind_wheel)
            self.canvas.bind("<Leave>", self._unbind_wheel)
            self.inner.bind("<Enter>", self._bind_wheel)
            self.inner.bind("<Leave>", self._unbind_wheel)

    def _on_inner(self, _e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, event):
        self.canvas.itemconfigure(self._win, width=max(1, event.width - u(2)))

    def _bind_wheel(self, _e=None):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _unbind_wheel(self, _e=None):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, event):
        step = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(step * 3, "units")

    def to_top(self):
        self.canvas.yview_moveto(0)
