# 用 GitHub 做线上后端：一次性配置

线上模式不依赖任何服务器：指令包以 JSON 文件存在仓库里，GitHub Actions 负责校验与合并，
客户端直接读 `raw.githubusercontent.com` 上的 `packs/all.json`。

需要你手动做的只有下面几件事（大约 5 分钟）。

## 第 1 步：建仓库

1. 打开 https://github.com/new
2. Repository name 填一个好记的名字，例如 `mc-cmd-packs`
3. 选择 **Public**（必须公开，客户端才能匿名读取 raw 文件）
4. 不要勾选 "Add a README file"（本项目已经有示例文件，避免冲突）
5. 点 Create repository

## 第 2 步：把本项目推上去

在项目目录 `f:\mc指令py` 执行（把地址换成你自己的）：

```powershell
git init
git add .
git commit -m "init: MC 指令工具台 + 指令包仓库"
git branch -M main
git remote add origin https://github.com/<你的用户名>/mc-cmd-packs.git
git push -u origin main
```

如果这台电脑没配过 Git 身份，先执行一次：

```powershell
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

推送时 GitHub 会要求授权：浏览器会弹出登录窗口，登录后选择 **Authorize** 即可；
也可以在命令行使用 Personal Access Token（Settings → Developer settings → Personal access tokens），
推送时把它当密码输入。

## 第 3 步：给 Actions 授权（关键）

打开仓库 **Settings → Actions → General**：

1. **Actions permissions** 选 `Allow all actions and reusable workflows`
2. 拉到 **Workflow permissions**，选 **Read and write permissions**
   - 这是机器人自动合并 PR、提交索引所必需的
3. 勾选 **Allow GitHub Actions to create and approve pull requests**
4. 点 Save

再到 **Settings → General → Pull Requests**：

5. 勾选 **Allow squash merging**（工作流使用 squash 合并）

> 建议先不要开分支保护。如果开了保护，需要在 Rules 里把 GitHub Actions 加进 bypass 名单，
> 否则机器人无法自动合并。

## 第 4 步：生成第一份索引

首次推送 main 后，「重建指令包索引」工作流会自动运行；也可以手动触发：

1. 打开仓库 **Actions** 标签
2. 左侧选 **重建指令包索引** → 右侧 **Run workflow** → Run
3. 跑完后仓库里会出现 `packs/index.json` 与 `packs/all.json`

如果本地想先生成：在项目目录执行 `python tools\build_index.py` 再提交即可。

## 第 5 步：客户端连上仓库

1. 打开工具 → 顶部切到 **线上**，或进「指令包」页
2. 填仓库地址：`你的用户名/mc-cmd-packs`（直接粘贴 https 链接也行，会自动截取）
3. 点 **保存** → 点 **同步**
4. 成功后「模组索引」里会多出指令包分组，状态栏会显示「已同步 N 个指令包」

## 别人怎么上传（无需你操作）

**有写权限的协作者**：打开 `https://github.com/<用户名>/<仓库>/new/main/packs`，文件名写 `my-pack.json`，粘贴 JSON，提交即可（会直接进 main 或自动开 PR）。

**普通访客（推荐流程）**：

1. 打开仓库 → 点 **Fork**（复刻到自己账号）
2. 在自己复刻里进入 `packs/` → **Add file → Create new file**
3. 文件名：`my-pack.json`，内容粘贴自己的 JSON
4. 选 **Create a new branch for this commit and start a pull request** → 提 PR
5. 机器人自动校验：通过就合并入库，不通过就评论出错条目并关闭 PR

工具「指令包」页有 **打开上传页** 按钮，会直接跳到新建文件界面，方便你自己上传。

## 维护

| 想做的事 | 做法 |
| --- | --- |
| 更新某个包 | 直接编辑 `packs/同名文件.json` 并提交（同名包会覆盖，收藏不会丢） |
| 删除某个包 | 删除 `packs/xxx.json` 并提交，索引会自动重建 |
| 手动校验 | `python tools\validate_pack.py packs\xxx.json` |
| 手动重建索引 | `python tools\build_index.py` |

## 排错

| 现象 | 原因与处理 |
| --- | --- |
| 同步提示「仓库里没有 packs/all.json」 | Actions 还没跑过，去 Actions 跑一次「重建指令包索引」 |
| 同步提示 HTTP 404 | 仓库名/用户名写错，或仓库是 Private（客户端读不到） |
| PR 没被自动合并 | Settings → Actions 的权限没给 Read and write，或开了分支保护 |
| 注释里全是英文报错 | 那是 JSON 语法错误，按行号改标点即可 |
| 机器人没反应 | 检查 Actions 是否启用；PR 里是否有 `packs/*.json` 改动 |

## 安全性

- 仓库公开 = 任何人都能读、能提 PR；只有流程里的机器人（`GITHUB_TOKEN`）能合并
- 不需要把任何 Token 写进客户端或仓库
- 客户端只发 GET 请求读取静态 JSON，不上传你的本地数据
