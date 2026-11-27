# -*- coding: utf-8 -*-
"""指令包 JSON 规范与校验（服务端与客户端共用）。"""

import hashlib
import json

SPEC_VERSION = "mc-cmd-pack/1"
MAX_NAME = 40
MAX_DESC = 300
MAX_AUTHOR = 40
MAX_NOTE = 60
MAX_COMMAND = 200
MAX_COMMANDS = 500

SAMPLE = {
    "spec": "mc-cmd-pack/1",
    "name": "生存实用指令",
    "description": "常用生存指令合集，编号即指令序号",
    "author": "你的名字",
    "version": "1.0",
    "commands": {
        "1": "/give @p minecraft:diamond 1",
        "2": "/time set day",
        "3": {"command": "/gamerule keepInventory true", "note": "死亡不掉落"},
    },
}

SPEC_DOC = """{
  "spec": "mc-cmd-pack/1",
  "name": "生存实用指令",
  "description": "常用生存指令合集",
  "author": "张三",
  "version": "1.0",
  "commands": {
    "1": "/give @p diamond 1",
    "2": {"command": "/time set day",
          "note": "设为白天"}
  }
}

也可以写成数组，编号自动补：
"commands": [
  {"id": 1,
   "command": "/give @p diamond 1",
   "note": "给钻石"}
]"""

RULES = [
    "文件必须是 UTF-8 编码的 JSON 对象，最大 1 MB。",
    "name 必填，1~40 个字符；description 必填，1~300 个字符。",
    "commands 必填，支持「编号映射」或「数组」两种写法，1~500 条。",
    "编号必须是正整数且不重复；数组写法可省略编号，按顺序补 1、2、3…",
    "每条指令必须以 / 开头，长度不超过 200，不能包含换行。",
    "note（备注）可选，最多 60 字，会作为指令说明显示。",
    "校验通过后自动入库，出现在「模组索引」的扩展包分组里。",
]


def _err(errors, path, message, index=None):
    item = {"path": path, "message": message}
    if index is not None:
        item["index"] = index
    errors.append(item)


def parse_json(text):
    """解析文本，失败时返回可直接展示的中文错误。"""
    if text is None:
        return None, [{"path": "root", "message": "内容为空，没有收到 JSON"}]
    text = text.lstrip("\ufeff").strip()
    if not text:
        return None, [{"path": "root", "message": "内容为空，没有收到 JSON"}]
    try:
        return json.loads(text), []
    except json.JSONDecodeError as exc:
        return None, [{
            "path": "root",
            "message": "JSON 解析失败：第 %d 行第 %d 列附近（%s）" % (
                exc.lineno, exc.colno, exc.msg),
        }]


def validate_pack(data):
    """校验并规范化指令包，返回 (pack, errors)。"""
    errors = []

    if not isinstance(data, dict):
        return None, [{"path": "root", "message": "顶层必须是一个 JSON 对象 { ... }"}]

    spec = data.get("spec")
    if spec is not None and spec != SPEC_VERSION:
        _err(errors, "spec", "spec 只能是 \"%s\"，当前为 %r" % (SPEC_VERSION, spec))

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        _err(errors, "name", "name 必填，且必须是非空字符串")
        name = ""
    else:
        name = name.strip()
        if len(name) > MAX_NAME:
            _err(errors, "name", "name 过长（%d 字），最多 %d 字" % (len(name), MAX_NAME))

    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        _err(errors, "description", "description 必填，且必须是非空字符串")
        desc = ""
    else:
        desc = desc.strip()
        if len(desc) > MAX_DESC:
            _err(errors, "description",
                 "description 过长（%d 字），最多 %d 字" % (len(desc), MAX_DESC))

    author = data.get("author", "")
    if author is None:
        author = ""
    if not isinstance(author, str):
        _err(errors, "author", "author 必须是字符串")
        author = ""
    author = author.strip()[:MAX_AUTHOR]

    version = data.get("version", "")
    if version is None:
        version = ""
    if not isinstance(version, str):
        _err(errors, "version", "version 必须是字符串")
        version = ""

    raw_commands = data.get("commands")
    items = []

    if raw_commands is None:
        _err(errors, "commands", "commands 必填，可以是编号映射或数组")
    elif isinstance(raw_commands, dict):
        if not raw_commands:
            _err(errors, "commands", "commands 不能为空对象")
        if len(raw_commands) > MAX_COMMANDS:
            _err(errors, "commands", "指令过多（%d 条），最多 %d 条" % (
                len(raw_commands), MAX_COMMANDS))
        for key, value in raw_commands.items():
            path = 'commands["%s"]' % key
            try:
                number = int(str(key).strip())
            except (TypeError, ValueError):
                _err(errors, path, "编号必须是正整数，当前是 %r" % key)
                continue
            if number <= 0:
                _err(errors, path, "编号必须从 1 开始，当前是 %d" % number)
                continue
            parsed = _parse_item(value, path, number, errors)
            if parsed:
                items.append(parsed)
    elif isinstance(raw_commands, list):
        if not raw_commands:
            _err(errors, "commands", "commands 不能为空数组")
        if len(raw_commands) > MAX_COMMANDS:
            _err(errors, "commands", "指令过多（%d 条），最多 %d 条" % (
                len(raw_commands), MAX_COMMANDS))
        for position, value in enumerate(raw_commands):
            path = "commands[%d]" % position
            number = position + 1
            if isinstance(value, dict) and "id" in value:
                try:
                    number = int(value["id"])
                except (TypeError, ValueError):
                    _err(errors, path + ".id",
                         "id 必须是整数，当前是 %r" % value["id"])
                    continue
                if number <= 0:
                    _err(errors, path + ".id", "id 必须从 1 开始")
                    continue
            parsed = _parse_item(value, path, number, errors)
            if parsed:
                items.append(parsed)
    else:
        _err(errors, "commands",
             "commands 必须是对象 {编号: 指令} 或数组 [ ... ]，当前是 %s" %
             type(raw_commands).__name__)

    seen = {}
    for position, item in enumerate(items):
        item["index"] = position + 1
    for item in items:
        if item["id"] in seen:
            _err(errors, "commands", "编号 %d 重复出现（第 %d 条与第 %d 条）" % (
                item["id"], seen[item["id"]], item["index"]), item["index"])
        else:
            seen[item["id"]] = item["index"]

    if errors:
        return None, errors

    items.sort(key=lambda entry: entry["id"])
    for position, item in enumerate(items):
        item["index"] = position + 1

    return {
        "spec": SPEC_VERSION,
        "name": name,
        "description": desc,
        "author": author,
        "version": version,
        "items": items,
    }, []


def _parse_item(value, path, number, errors):
    note = ""
    command = value

    if isinstance(value, dict):
        command = value.get("command")
        note = value.get("note", "") or ""
        if not isinstance(note, str):
            _err(errors, path + ".note", "note 必须是字符串")
            note = ""
        elif len(note.strip()) > MAX_NOTE:
            _err(errors, path + ".note",
                 "note 过长（%d 字），最多 %d 字" % (len(note.strip()), MAX_NOTE))
        note = note.strip()
        if "command" not in value:
            _err(errors, path, "缺少 command 字段")
            return None

    if not isinstance(command, str):
        _err(errors, path + ".command", "指令必须是字符串，当前是 %s" %
             type(command).__name__)
        return None

    command = command.strip()
    if not command:
        _err(errors, path + ".command", "指令内容为空")
        return None
    if "\n" in command or "\r" in command:
        _err(errors, path + ".command", "指令不能包含换行")
        return None
    if len(command) > MAX_COMMAND:
        _err(errors, path + ".command",
             "指令过长（%d 字），最多 %d 字" % (len(command), MAX_COMMAND))
        return None
    if not command.startswith("/"):
        _err(errors, path + ".command",
             "指令必须以 / 开头，当前是 %r" % command[:24])
        return None
    if command == "/":
        _err(errors, path + ".command", "指令不能只有一个 /")
        return None

    return {"id": number, "command": command, "note": note}


def pack_to_entries(pack, pack_id):
    """把指令包转换成指令库条目。"""
    mod_id = "pack:%s" % pack_id
    entries = []
    for item in pack["items"]:
        note = item["note"]
        entries.append({
            "name": note or ("%s · %d" % (pack["name"], item["id"])),
            "syntax": item["command"],
            "category": "扩展",
            "desc": note or "来自扩展包「%s」的第 %d 条指令" % (
                pack["name"], item["id"]),
            "params": [
                ("编号", "#%d" % item["id"], "扩展包内编号"),
                ("来源", pack["name"], pack.get("author") or "未署名"),
            ],
            "examples": [item["command"]],
            "since": None,
            "until": None,
            "notes": pack["description"],
            "keywords": "%s %s %s" % (pack["name"], note, item["command"]),
            "mod": mod_id,
            "mod_name": pack["name"],
            "id": "p:%s:%d" % (pack_id, item["id"]),
        })
    return entries


def example_text():
    return json.dumps(SAMPLE, ensure_ascii=False, indent=2)


def pack_id_for(name):
    """由包名生成稳定 ID（同名视为同一个包，更新内容不会丢失收藏）。"""
    seed = (name or "").strip().lower().encode("utf-8")
    return hashlib.sha1(seed).hexdigest()[:10]


def ensure_pack(data):
    """接受「原始指令包」或「已构建的包对象」，统一返回 (pack, errors)。"""
    if not isinstance(data, dict):
        return None, [{"path": "root", "message": "指令包必须是 JSON 对象"}]

    if isinstance(data.get("items"), list) and "commands" not in data:
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            return None, [{"path": "name", "message": "指令包缺少 name"}]
        items = []
        errors = []
        for position, item in enumerate(data["items"]):
            path = "items[%d]" % position
            if not isinstance(item, dict):
                _err(errors, path, "条目必须是对象")
                continue
            command = item.get("command")
            if not isinstance(command, str) or not command.startswith("/"):
                _err(errors, path + ".command", "指令必须以 / 开头")
                continue
            try:
                number = int(item.get("id") or position + 1)
            except (TypeError, ValueError):
                _err(errors, path + ".id", "id 必须是整数")
                continue
            items.append({
                "id": number,
                "command": command.strip(),
                "note": str(item.get("note") or "").strip()[:MAX_NOTE],
                "index": position + 1,
            })
        if errors:
            return None, errors
        if not items:
            return None, [{"path": "items", "message": "指令包为空"}]
        return {
            "spec": SPEC_VERSION,
            "name": name.strip(),
            "description": str(data.get("description") or "").strip(),
            "author": str(data.get("author") or "").strip(),
            "version": str(data.get("version") or "").strip(),
            "items": items,
        }, []

    return validate_pack(data)
