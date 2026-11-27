# -*- coding: utf-8 -*-
"""公共数据：版本表、分类、条目工厂。"""

VERSIONS = [
    "1.8.9", "1.12.2", "1.16.5", "1.18.2", "1.19.4",
    "1.20.1", "1.20.4", "1.21.1", "1.21.4", "1.21.8",
]

VERSION_NOTES = {
    "1.8.9": "经典版，指令使用数字 ID 与 NBT",
    "1.12.2": "模组生态最完整的老版本",
    "1.16.5": "下界更新，主流模组稳定版",
    "1.18.2": "洞穴与山崖",
    "1.19.4": "加入 /damage、/ride、/place",
    "1.20.1": "主流整合包常用版本",
    "1.20.4": "1.20 系列稳定版",
    "1.21.1": "1.21 首个稳定版",
    "1.21.4": "数据组件成熟版本",
    "1.21.8": "最新 1.21 系列",
}

CATEGORIES = ["物品", "实体", "世界", "玩家", "进阶", "服务器"]


def version_index(version):
    if version in VERSIONS:
        return VERSIONS.index(version)
    return len(VERSIONS) - 1


def available_in(entry, version):
    """判断条目在所选版本是否可用。"""
    idx = version_index(version)
    since = version_index(entry.get("since") or VERSIONS[0])
    until = entry.get("until")
    if idx < since:
        return False
    if until and idx > version_index(until):
        return False
    return True


def version_label(entry):
    since = entry.get("since")
    until = entry.get("until")
    if since and until:
        return "%s ~ %s" % (since, until)
    if since and since != VERSIONS[0]:
        return "%s+" % since
    if until:
        return "≤ %s" % until
    return "全版本"


def cmd(name, syntax, category, desc, params, examples,
        since=None, until=None, notes="", keywords="", mod=None, mod_name=""):
    return {
        "name": name,
        "syntax": syntax,
        "category": category,
        "desc": desc,
        "params": params,
        "examples": examples,
        "since": since,
        "until": until,
        "notes": notes,
        "keywords": keywords,
        "mod": mod,
        "mod_name": mod_name,
        "id": ("m:%s:%s" % (mod, name)) if mod else ("v:%s" % name),
    }


def build_index(entries):
    """建立搜索用的小写索引。"""
    for entry in entries:
        entry["_search"] = " ".join([
            entry["name"], entry["syntax"], entry["desc"],
            entry["category"], entry.get("keywords", ""),
            entry.get("mod_name", ""),
        ]).lower()
    return entries


def search(entries, keyword, category=None, mod=None, version=None):
    keyword = (keyword or "").strip().lower()
    result = []
    for entry in entries:
        if category and category != "全部" and entry["category"] != category:
            continue
        if mod and mod != "全部" and entry.get("mod") != mod:
            continue
        if version and not available_in(entry, version):
            continue
        if keyword and keyword not in entry["_search"]:
            continue
        result.append(entry)
    return result
