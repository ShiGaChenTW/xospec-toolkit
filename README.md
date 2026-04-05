# X.OSpec Toolkit

互動式 TUI + CLI 工具，一鍵建立符合 X.OSpec 規範的 repo 骨架。

## 背景

基於「GithubX.OSpec框架」＋Superpowers 研究結論，採用 **X.OSpec + Superpowers** 的「repo 檔案驅動、可跨工具搬移」workflow。本工具自動生成五層架構中的 Layer 1–3，不需先安裝 X.OSpec CLI 或 Superpowers。

```
Layer 5  Superpowers      → 工程紀律（plan / TDD / review）       [可選整合]
Layer 4  X.OSpec CLI      → 自動生成 spec 流程                    [可選]
Layer 3  changes/         → 單次變更包（proposal/design/tasks）    [✓ 本工具生成]
Layer 2  specs/           → 長期 living specs                      [✓ 本工具生成]
Layer 1  repo + git       → 底座                                  [✓ 本工具生成]
```

## 快速開始

```bash
git clone https://github.com/ShiGaChenTW/xospec-toolkit xospec-toolkit
```

根據你的情境，選擇對應的使用路徑：

### 情境 1：全新專案（Greenfield）

```bash
cd xospec-toolkit
./setup.sh
```

啟動 TUI 互動介面，填寫專案資訊後自動生成完整的 X.OSpec repo 骨架。

### 情境 2：既有專案導入（Brownfield）

已有專案想套用 X.OSpec 框架，不動既有程式碼：

```bash
cd /path/to/your-existing-project
/path/to/xospec-toolkit/setup.sh --brownfield
```

自動掃描當前目錄，注入 `xospec/`、`AGENTS.md`、`.xospec-map.md` 等框架檔案。

### 情境 3：Fork 下來的專案

從 GitHub fork 或 clone 一個專案後，導入 X.OSpec 開發流程：

```bash
# Step 1: Fork & Clone 目標專案
git clone https://github.com/someone/some-project.git
cd some-project

# Step 2: 導入 X.OSpec 框架
/path/to/xospec-toolkit/setup.sh --brownfield

# Step 3: 開始第一個 Change（選用）
/path/to/xospec-toolkit/setup.sh --add-change "add-my-feature"
```

導入後的目錄結構：

```
some-project/                      ← 既有內容不動
├── src/                           ← 原始程式碼（不動）
├── package.json                   ← 原始設定（不動）
├── .xospec-map.md               ← 新增：空間索引
├── AGENTS.md                      ← 新增：AI Agent 規則
├── xospec/                      ← 新增：X.OSpec 框架
│   ├── README.md
│   ├── specs/<capability>/spec.md
│   └── changes/<change-id>/       ← 新增 Change 後出現
│       ├── proposal.md
│       ├── design.md
│       ├── tasks.md
│       └── spec_delta.md
└── docs/
    └── engineering-principles.md   ← 新增：工程原則
```

### 情境 4：追加 Change Package

在已導入 X.OSpec 的專案中，開始一個新的變更：

```bash
cd /path/to/your-xospec-project
/path/to/xospec-toolkit/setup.sh --add-change "fix-auth-session-leak"
```

### 情境 5：CI/CD 自動化

```bash
/path/to/xospec-toolkit/setup.sh --non-interactive \
  --project-name "my-billing-service" \
  --capabilities "auth,billing,notification" \
  --target-dir ./my-billing-service
```

### 建議：設定全域別名

如果經常使用，可在 `~/.zshrc` 或 `~/.bashrc` 加入：

```bash
export XOSPEC_HOME="/path/to/xospec-toolkit"
alias xospec="$XOSPEC_HOME/setup.sh"
```

之後在任何目錄都能直接使用：

```bash
xospec                                       # 新專案
xospec--brownfield                           # 導入既有專案
xospec--add-change "add-billing-export"      # 追加 Change
```

### setup.sh 選項一覽

| 指令 | 功能 |
|------|------|
| `./setup.sh` | 完整流程（安裝 + 啟動 TUI） |
| `./setup.sh --brownfield` | 在當前目錄導入 X.OSpec 框架 |
| `./setup.sh --add-change <name>` | 在當前目錄追加 Change Package |
| `./setup.sh --install` | 只安裝依賴與 Skills，不啟動 |
| `./setup.sh --run` | 跳過安裝，直接啟動 TUI |
| `./setup.sh --status` | 顯示目前安裝狀態 |
| `./setup.sh --uninstall` | 移除已安裝的 Skills 與 Hook |
| `./setup.sh --help` | 顯示說明 |

### setup.sh 會做什麼？

| Step | 說明 | 條件 |
|------|------|------|
| 1. 環境檢查 | 確認 Python 3.10+、Node.js、終端尺寸 | 必要 |
| 2. Python 依賴 | 安裝 jinja2, pyyaml（若缺少） | 必要 |
| 3. Claude Code Skills | 建立 3 個 skill 的 symlink 到 `~/.claude/skills/` | 有 Claude Code 時 |
| 4. Preflight Hook | 複製 hook 腳本到 `~/.claude/hooks/` | 有 Node.js 時 |

> 沒有 Claude Code 或 Node.js 也能正常使用 Generator，Skills 和 Hook 會自動跳過。

## 需求

- Python 3.10+
- Jinja2 + PyYAML（`setup.sh` 會自動安裝，或手動 `pip install -r requirements.txt`）
- Terminal 最小尺寸 110 x 48（TUI 模式）
- Node.js（選用，preflight hook 需要）
- Claude Code（選用，Skills 安裝需要）

## 使用方式

### 互動式 TUI 模式

```bash
./setup.sh
# 或
python create_repo.py
```

| 按鍵 | 功能 |
|------|------|
| Enter | 跳到下一題 |
| 方向鍵 / Tab | 在欄位間移動 |
| F2 | 送出並生成 repo |
| Esc | 取消離開 |

### CLI Non-Interactive 模式

適合腳本或 CI/CD 呼叫：

```bash
./setup.sh --non-interactive \
  --project-name "my-billing-service" \
  --capabilities "auth,billing,notification" \
  --target-dir ./my-billing-service \
  --target-user "End users" \
  --user-problem "Users cannot track invoices efficiently"
```

完整參數列表：

| 參數 | 必填 | 預設值 | 說明 |
|------|------|--------|------|
| `--project-name` | * | `my-project` | 專案名稱 |
| `--target-dir` | | 從專案名稱 slugify | 輸出路徑 |
| `--capabilities` | * | `auth, billing` | 功能模組，逗號分隔 |
| `--first-change-name` | * | `add-<第一個 capability>` | 第一個 feature 名稱 |
| `--first-change-capability` | * | 第一個 capability | 該 feature 屬於哪個 capability |
| `--user-problem` | * | （預設文字） | 主要使用者問題 |
| `--target-user` | * | `End users` | 目標使用者 |
| `--feature-why` | | （預設文字） | 為什麼先做這個 feature |
| `--overwrite` | | `no` | 是否覆寫已有檔案 |
| `--enable-superpowers` | | `yes` | 是否加入 Superpowers 整合 |
| `--git-init` | | `yes` | 生成後自動 git init + commit |

### Config 檔預設值

在專案目錄或 `$HOME` 放一個 `.xospec-generator.yml`，TUI 會自動載入作為預填值：

```yaml
project_name: my-project
capabilities: auth, billing
target_user: End users
enable_superpowers: "yes"
git_init: "yes"
```

範例檔見 `.xospec-generator.yml.example`。

## 生成的 Repo 結構

```
<project>/
├── README.md                          ← 專案說明
├── AGENTS.md                          ← AI coding agent 規則
├── .gitignore
├── .xospec-map.md                   ← 空間索引（Agent 導航用）
├── docs/
│   ├── engineering-principles.md      ← 工程原則與交付標準
│   └── superpowers.md                 ← Superpowers 整合說明（可選）
├── xospec/
│   ├── README.md
│   ├── specs/
│   │   ├── <capability-1>/spec.md     ← 長期 living spec
│   │   └── <capability-2>/spec.md
│   └── changes/
│       └── <first-change>/
│           ├── proposal.md            ← 變更提案
│           ├── design.md              ← 技術設計
│           ├── tasks.md               ← 任務清單
│           └── spec_delta.md          ← spec delta
```

## 功能特色

| # | 功能 | 說明 |
|---|------|------|
| 1 | 模板抽離 | 15 個 `.j2` 模板檔在 `templates/`，用 Jinja2 渲染，方便自訂 |
| 2 | CLI non-interactive | `--non-interactive` 跳過 TUI 直接生成，適合腳本呼叫 |
| 3 | 自動 git init | 生成後自動 `git init` + initial commit |
| 4 | AGENTS.md | 自動生成 AI agent 工作規則 |
| 5 | engineering-principles.md | 自動生成工程原則文件 |
| 6 | Superpowers 整合 | 可選生成 `docs/superpowers.md` |
| 7 | config 檔支援 | 讀取 `.xospec-generator.yml` 預填預設值 |
| 8 | 路徑驗證強化 | 檢查非法字元、偵測目標已有 git repo |
| 9 | Brownfield 導入 | `--brownfield` 模式導入既有專案，不動既有檔案 |
| 10 | 追加 Change | `--add-change` 在既有 repo 新增 Change Package |

## 檔案結構

```
xospec-toolkit/
├── setup.sh                            ← 一鍵安裝 + 啟動
├── create_repo.py                      ← 主程式
├── requirements.txt                    ← Python 依賴
├── README.md                           ← 本檔案
├── .xospec-generator.yml.example     ← config 範例
├── skills/                             ← Claude Code Skills（隨專案發佈）
│   ├── xospec-generator/SKILL.md
│   ├── xospec-preflight/
│   │   ├── SKILL.md
│   │   └── xospec-preflight.js
│   └── xospec-brownfield-onboard/SKILL.md
└── templates/
    ├── readme.md.j2                    ← 專案 README
    ├── gitignore.j2                    ← .gitignore
    ├── xospec_readme.md.j2           ← xospec/ 目錄說明
    ├── xospec_map.md.j2              ← .xospec-map.md 空間索引
    ├── spec.md.j2                      ← Living spec
    ├── proposal.md.j2                  ← 變更提案
    ├── design.md.j2                    ← 技術設計
    ├── tasks.md.j2                     ← 任務清單
    ├── spec_delta.md.j2                ← Spec delta
    ├── agents.md.j2                    ← AGENTS.md
    ├── engineering_principles.md.j2    ← 工程原則
    ├── superpowers.md.j2               ← Superpowers 整合說明
    ├── gsd_project.md.j2               ← GSD PROJECT.md
    ├── gsd_roadmap.md.j2               ← GSD ROADMAP.md
    └── gsd_state.md.j2                 ← GSD STATE.md
```

## 自訂模板

修改 `templates/` 下的 `.j2` 檔案即可自訂生成內容。可用的 Jinja2 變數：

| 變數 | 類型 | 說明 |
|------|------|------|
| `{{ project_name }}` | str | 專案名稱 |
| `{{ target_user }}` | str | 目標使用者 |
| `{{ user_problem }}` | str | 使用者問題 |
| `{{ feature_why }}` | str | 第一個 feature 的原因 |
| `{{ capabilities }}` | list[str] | 所有 capability（已 slugify） |
| `{{ change_id }}` | str | 第一個 change 的 slug |
| `{{ first_change_capability }}` | str | 第一個 change 所屬 capability |
| `{{ capability }}` | str | 當前 capability（僅 spec.md.j2） |

## 適用情境

- Side project 快速啟動 X.OSpec workflow
- 建立可跨 Cursor / Claude Code / Copilot / Kiro 搬移的 repo
- 學習 spec-driven development 的入門範本
- CI/CD 中自動初始化新專案骨架
