# -*- coding: utf-8 -*-
"""本地状态存储：收藏、默认版本、服务器配置路径。"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATE_FILE = os.path.join(DATA_DIR, "user.json")

DEFAULTS = {
    "version": "1.21.4",
    "favorites": [],
    "server_properties": "",
    "mode": "offline",
    "repo": "",
    "branch": "main",
}


class Store(object):
    def __init__(self):
        self.state = dict(DEFAULTS)
        self.state["favorites"] = []
        self.load()

    # -------------------------------------------------------------- 读写
    def load(self):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                for key in DEFAULTS:
                    if key in data:
                        self.state[key] = data[key]
                if not isinstance(self.state["favorites"], list):
                    self.state["favorites"] = []
        except (IOError, ValueError):
            pass

    def save(self):
        try:
            if not os.path.isdir(DATA_DIR):
                os.makedirs(DATA_DIR)
            with open(STATE_FILE, "w", encoding="utf-8") as handle:
                json.dump(self.state, handle, ensure_ascii=False, indent=2)
        except (IOError, OSError):
            pass

    # -------------------------------------------------------------- 版本
    @property
    def version(self):
        return self.state.get("version") or DEFAULTS["version"]

    @version.setter
    def version(self, value):
        self.state["version"] = value
        self.save()

    # -------------------------------------------------------------- 收藏
    @property
    def favorites(self):
        return list(self.state.get("favorites") or [])

    def is_favorite(self, cmd_id):
        return cmd_id in self.state.get("favorites", [])

    def toggle_favorite(self, cmd_id):
        items = self.state.setdefault("favorites", [])
        if cmd_id in items:
            items.remove(cmd_id)
            flag = False
        else:
            items.append(cmd_id)
            flag = True
        self.save()
        return flag

    def clear_favorites(self):
        self.state["favorites"] = []
        self.save()

    # -------------------------------------------------------------- 其它
    @property
    def mode(self):
        return self.state.get("mode") or "offline"

    @mode.setter
    def mode(self, value):
        self.state["mode"] = "online" if value == "online" else "offline"
        self.save()

    @property
    def repo(self):
        return self.state.get("repo") or ""

    @repo.setter
    def repo(self, value):
        self.state["repo"] = (value or "").strip()
        self.save()

    @property
    def branch(self):
        return self.state.get("branch") or "main"

    @branch.setter
    def branch(self, value):
        self.state["branch"] = (value or "main").strip() or "main"
        self.save()

    @property
    def server_properties(self):
        return self.state.get("server_properties") or ""

    @server_properties.setter
    def server_properties(self, path):
        self.state["server_properties"] = path
        self.save()
