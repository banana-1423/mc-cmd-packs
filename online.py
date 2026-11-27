# -*- coding: utf-8 -*-
"""线上模式：从 GitHub 仓库拉取指令包（纯静态，无需服务器）。"""

import json
import os
import time
from urllib import error as urlerror
from urllib import request as urlrequest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "packs_all.json")

USER_AGENT = "mc-command-toolkit/1.0"


def normalize_repo(text):
    """把各种写法统一成 owner/repo。"""
    value = (text or "").strip().strip("/")
    if not value:
        return ""
    if "github.com/" in value:
        value = value.split("github.com/")[-1]
    if value.endswith(".git"):
        value = value[:-4]
    parts = [part for part in value.split("/") if part]
    if len(parts) >= 2:
        return "%s/%s" % (parts[0], parts[1])
    return ""


def raw_url(repo, branch, path):
    return "https://raw.githubusercontent.com/%s/%s/%s" % (
        repo, branch or "main", path)


def page_url(repo, branch, path):
    return "https://github.com/%s/blob/%s/%s" % (repo, branch or "main", path)


def upload_url(repo, branch):
    return "https://github.com/%s/new/%s/packs" % (repo, branch or "main")


def home_url(repo):
    return "https://github.com/%s" % repo


def fetch_json(url, timeout=12):
    request = urlrequest.Request(url, headers={"User-Agent": USER_AGENT})
    response = urlrequest.urlopen(request, timeout=timeout)
    try:
        raw = response.read()
    finally:
        response.close()
    return json.loads(raw.decode("utf-8"))


def _result(ok, message, packs=None, from_cache=False, updated=""):
    return {
        "ok": ok,
        "message": message,
        "packs": packs or [],
        "from_cache": from_cache,
        "updated": updated,
    }


def save_cache(repo, branch, payload, packs, updated):
    try:
        if not os.path.isdir(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        data = {
            "repo": repo,
            "branch": branch,
            "fetched_at": int(time.time()),
            "updated": updated,
            "packs": packs,
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False)
    except (IOError, OSError):
        pass


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and isinstance(data.get("packs"), list):
            return data
    except (IOError, ValueError):
        pass
    return None


def cache_age_text():
    data = load_cache()
    if not data:
        return "尚未同步"
    stamp = data.get("fetched_at") or 0
    if not stamp:
        return "尚未同步"
    delta = int(time.time()) - int(stamp)
    if delta < 60:
        return "刚刚同步"
    if delta < 3600:
        return "%d 分钟前同步" % (delta // 60)
    if delta < 86400:
        return "%d 小时前同步" % (delta // 3600)
    return "%d 天前同步" % (delta // 86400)


def sync(repo, branch="main", timeout=12):
    """拉取 packs/all.json，失败时退回本地缓存。"""
    import pack_spec

    repo = normalize_repo(repo)
    branch = (branch or "main").strip() or "main"
    if not repo:
        return _result(False, "仓库地址格式应为 owner/repo")

    try:
        data = fetch_json(raw_url(repo, branch, "packs/all.json"), timeout)
    except urlerror.HTTPError as exc:
        if exc.code == 404:
            message = "仓库里没有 packs/all.json，请先在仓库里运行一次 Actions 或在本地执行 tools/build_index.py"
        else:
            message = "服务器返回 HTTP %s" % exc.code
        return _fallback(message)
    except urlerror.URLError as exc:
        return _fallback("网络不可用（%s）" % getattr(exc, "reason", exc))
    except (ValueError, UnicodeDecodeError):
        return _fallback("返回内容不是合法 JSON")
    except Exception as exc:  # noqa: BLE001 网络库异常种类较多
        return _fallback("同步失败（%s）" % exc)

    packs = []
    errors = []
    for item in data.get("packs", []):
        pack, pack_errors = pack_spec.ensure_pack(item)
        if pack is None:
            errors.append(pack_errors[0]["message"] if pack_errors else "未知错误")
            continue
        packs.append(pack)

    if not packs:
        return _fallback("远端没有可用的指令包")

    updated = data.get("updated", "")
    save_cache(repo, branch, data, packs, updated)
    message = "已同步 %d 个指令包" % len(packs)
    if errors:
        message += "，跳过 %d 个异常包" % len(errors)
    return _result(True, message, packs, False, updated)


def _fallback(message):
    import pack_spec

    cached = load_cache()
    if cached:
        packs = []
        for item in cached.get("packs", []):
            pack, _errors = pack_spec.ensure_pack(item)
            if pack is not None:
                packs.append(pack)
        if packs:
            return _result(True, message + "，已使用本地缓存（%s）" %
                           cache_age_text(), packs, True,
                           cached.get("updated", ""))
    return _result(False, message)
