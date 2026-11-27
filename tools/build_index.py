#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 packs/*.json，生成 packs/index.json 与 packs/all.json。

内容没变化时不会改写文件，避免 Actions 反复提交。
"""

import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pack_spec  # noqa: E402

PACK_DIR = os.path.join(ROOT, "packs")
INDEX_FILE = os.path.join(PACK_DIR, "index.json")
ALL_FILE = os.path.join(PACK_DIR, "all.json")
INDEX_SPEC = "mc-cmd-index/1"
ALL_SPEC = "mc-cmd-all/1"


def load_existing(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (IOError, ValueError):
        return None


def write_json(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def collect():
    packs = []
    skipped = []
    if not os.path.isdir(PACK_DIR):
        return packs, skipped

    for name in sorted(os.listdir(PACK_DIR)):
        if not name.endswith(".json"):
            continue
        if name in ("index.json", "all.json"):
            continue
        path = os.path.join(PACK_DIR, name)
        with open(path, "rb") as handle:
            raw = handle.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append((name, "不是 UTF-8 编码"))
            continue
        data, errors = pack_spec.parse_json(text)
        if errors:
            skipped.append((name, errors[0]["message"]))
            continue
        pack, errors = pack_spec.validate_pack(data)
        if errors:
            skipped.append((name, errors[0]["message"]))
            continue
        packs.append({
            "file": name,
            "id": pack_spec.pack_id_for(pack["name"]),
            "name": pack["name"],
            "description": pack["description"],
            "author": pack.get("author", ""),
            "version": pack.get("version", ""),
            "count": len(pack["items"]),
            "sha256": hashlib.sha256(raw).hexdigest()[:16],
            "pack": pack,
        })

    packs.sort(key=lambda item: item["name"])
    return packs, skipped


def main():
    packs, skipped = collect()

    index_payload = [{
        "file": item["file"],
        "id": item["id"],
        "name": item["name"],
        "description": item["description"],
        "author": item["author"],
        "version": item["version"],
        "count": item["count"],
        "sha256": item["sha256"],
    } for item in packs]

    all_payload = []
    for item in packs:
        pack = dict(item["pack"])
        pack["id"] = item["id"]
        pack["file"] = item["file"]
        all_payload.append(pack)

    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    changed = False

    old_index = load_existing(INDEX_FILE) or {}
    if old_index.get("packs") != index_payload or not os.path.isfile(INDEX_FILE):
        write_json(INDEX_FILE, {
            "spec": INDEX_SPEC,
            "updated": stamp,
            "count": len(index_payload),
            "packs": index_payload,
        })
        changed = True

    old_all = load_existing(ALL_FILE) or {}
    if old_all.get("packs") != all_payload or not os.path.isfile(ALL_FILE):
        write_json(ALL_FILE, {
            "spec": ALL_SPEC,
            "updated": stamp,
            "count": len(all_payload),
            "packs": all_payload,
        })
        changed = True

    for name, reason in skipped:
        print("SKIP  %s  %s" % (name, reason))
    print("%s：%d 个指令包" % ("已更新" if changed else "无变化", len(packs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
