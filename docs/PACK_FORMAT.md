# 指令包 JSON 规范（mc-cmd-pack/1）

线上模式的指令包全部存放在仓库的 `packs/` 目录里。一个文件 = 一个指令包。
文件名用英文与短横线，例如 `survival-basics.json`；不能叫 `index.json` 或 `all.json`（这两个是自动生成的索引）。

**每一条指令都必须带自己的简介（`note`）**，只写指令本体会被驳回。

## 1. 完整示例

```json
{
  "spec": "mc-cmd-pack/1",
  "name": "生存实用指令",
  "description": "开新档常用的一组指令",
  "author": "张三",
  "version": "1.0",
  "commands": {
    "1": { "command": "/give @p minecraft:diamond_pickaxe 1", "note": "给自己一把钻石镐" },
    "2": { "command": "/time set day", "note": "把时间调到白天" },
    "3": { "command": "/weather clear", "note": "立刻放晴" },
    "4": { "command": "/gamerule keepInventory true", "note": "开启死亡不掉落" }
  }
}
```

`commands` 也可以写成数组（编号按顺序自动补 1、2、3…，也可以自己写 `id`）：

```json
"commands": [
  { "id": 1, "command": "/give @p diamond 1", "note": "给自己一颗钻石" },
  { "command": "/tp @p ~ ~10 ~", "note": "向上瞬移十格" }
]
```

以下两种写法是**错误**的，会被校验器驳回（第一条只写了字符串，第二条 `note` 为空）：

```json
"commands": {
  "1": "/time set day",
  "2": { "command": "/weather clear", "note": "" }
}
```

## 2. 字段说明

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `spec` | 否 | 固定写 `"mc-cmd-pack/1"`，写错会报错 |
| `name` | 是 | 包名，1~40 个字符，同名视为同一个包（更新会覆盖） |
| `description` | 是 | 整包简介，1~300 个字符 |
| `author` | 否 | 作者，最多 40 字 |
| `version` | 否 | 版本号，自己定，例如 `1.0` |
| `commands` | 是 | 编号 → 指令的映射，或数组，1~500 条 |
| `commands.*.command` | 是 | 指令本体，必须 `/` 开头，≤200 字符，不能有换行 |
| `commands.*.note` | 是 | 这一条指令自己的简介，1~60 字，会作为指令名显示 |
| `commands.*.id` | 否 | 仅数组写法可用，不写就按顺序补 1、2、3… |

## 3. 校验规则

1. 文件必须是 UTF-8 编码的 JSON 对象（可带 BOM），不超过 1 MB。
2. `name`、`description` 必填且非空；`name` ≤40 字，`description` ≤300 字。
3. `commands` 必须是对象或数组，1~500 条。
4. 编号必须是正整数，不能重复；数组写法可省略编号。
5. 每条指令必须写成 `{"command": "...", "note": "..."}`，两个字段都必填，不能只写一个字符串。
6. `command` 必须以 `/` 开头，不能只有 `/`，不能包含换行，长度 ≤200。
7. `note` 是这一条指令的简介，1~60 字，会作为它在索引里的名字。

不满足以上任何一条，机器人会驳回并指出**具体是哪一条**。

## 4. 错误提示长什么样

校验失败时会返回带路径的中文错误，例如：

```
commands["1"]：每条指令都要写成 {"command": "...", "note": "..."}，不能只写一个字符串
commands["2"].note：缺少 note：每条指令都必须有简介
commands["3"].note：note 过长（78 字），最多 60 字
commands["4"].command：指令必须以 / 开头，当前是 'give @p stone'
commands["5x"]：编号必须是正整数，当前是 '5x'
```

数组写法用下标定位（从 0 开始）：

```
commands[1].note：缺少 note：每条指令都必须有简介
commands[2].command：指令不能包含换行
name：name 必填，且必须是非空字符串
```

JSON 本身写错（少逗号、用了中文引号）会提示行号与列号：

```
JSON 解析失败：第 3 行第 24 列附近（Expecting ',' delimiter）
```

## 5. 入库流程

1. 提交 / 上传 `packs/你的包名.json`（网页新建文件或 Pull Request 都可以）。
2. GitHub Actions 自动运行 `tools/validate_pack.py`。
3. 通过 → 机器人评论「校验通过」并自动 squash 合并；不通过 → 评论错误并关闭 PR。
4. 合并后自动重建 `packs/index.json` 与 `packs/all.json`。
5. 客户端「线上模式」点同步，即可在「模组索引」看到这个包，条目名就是每条指令的 `note`。

## 6. 常见错误

| 现象 | 原因 |
| --- | --- |
| `不能只写一个字符串` | 用了 `"1": "/time set day"` 简写，改成 `{"command": ..., "note": ...}` |
| `缺少 note：每条指令都必须有简介` | 这条只写了 command，补一句 1~60 字的简介 |
| `note 过长（xx 字），最多 60 字` | 简介写太长了，精简到 60 字以内 |
| `Expecting property name enclosed in double quotes` | 用了中文引号 `“”`，或少了逗号 |
| `指令必须以 / 开头` | 写成了 `give @p ...`，要写 `/give @p ...` |
| `编号必须是正整数` | 键写成了 `1a`、`-1`、`第一条` |
| `编号 3 重复出现` | 映射里同一个编号出现两次，或数组里 `id` 重复 |
| 中文变乱码 | 文件不是 UTF-8，用记事本「另存为 → UTF-8」 |
