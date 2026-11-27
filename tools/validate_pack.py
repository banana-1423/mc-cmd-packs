#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验指令包文件。

    python tools/validate_pack.py packs/xxx.json
    python tools/validate_pack.py --changed <base> <head>
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pack_spec  # noqa: E402


def validate_file(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError) as exc:
        return False, "无法读取：%s" % exc

    if len(raw) > 1024 * 1024:
        return False, "文件超过 1 MB"

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return False, "文件必须是 UTF-8 编码（可用记事本另存为 UTF-8）"

    data, errors = pack_spec.parse_json(text)
    if errors:
        return False, errors[0]["message"]

    pack, errors = pack_spec.validate_pack(data)
    if errors:
        lines = []
        for item in errors:
            lines.append("%s：%s" % (item.get("path", "?"), item["message"]))
        return False, "\n    ".join(lines)

    return True, "「%s」%d 条指令" % (pack["name"], len(pack["items"]))


def changed_files(base, head):
    try:
        output = subprocess.check_output(
            ["git", "diff", "--name-only", base, head, "--", "packs"],
            cwd=ROOT)
    except (subprocess.CalledProcessError, OSError):
        return []
    files = []
    for line in output.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line.endswith(".json"):
            continue
        if os.path.basename(line) in ("index.json", "all.json"):
            continue
        files.append(line)
    return files


def main():
    parser = argparse.ArgumentParser(description="校验 Minecraft 指令包 JSON")
    parser.add_argument("files", nargs="*", help="要校验的 JSON 文件")
    parser.add_argument("--changed", nargs=2, metavar=("BASE", "HEAD"),
                        help="校验两个提交之间变动的 packs/*.json")
    args = parser.parse_args()

    files = list(args.files)
    if args.changed:
        files.extend(changed_files(args.changed[0], args.changed[1]))

    if not files:
        print("没有需要校验的指令包文件")
        return 0

    failed = 0
    for path in files:
        ok, message = validate_file(path)
        if ok:
            print("PASS  %s  %s" % (path, message))
        else:
            failed += 1
            print("FAIL  %s\n    %s" % (path, message))

    print("\n共 %d 个文件，成功 %d，失败 %d" % (len(files), len(files) - failed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
