# OpenSpec Toolkit

互動式 TUI + CLI 工具，一鍵建立符合 OpenSpec 規範的 repo 骨架。

## 背景

基於「GithubOpenSpec框架」＋Superpowers 研究結論，採用 **OpenSpec + Superpowers** 的「repo 檔案驅動、可跨工具搬移」workflow。本工具自動生成五層架構中的 Layer 1–3，不需先安裝 OpenSpec CLI 或 Superpowers。

```
Layer 5  Superpowers      → 工程紀律（plan / TDD / review）       [可選整合]
Layer 4  OpenSpec CLI      → 自動生成 spec 流程                    [可選]
Layer 3  changes/         → 單次變更包（proposal/design/tasks）    [✓ 本工具生成]
Layer 2  specs/           → 長期 living specs                      [✓ 本工具生成]
Layer 1  repo + git       → 底座                                  [✓ 本工具生成]
```

## 需求

- Python 3.10+
- Jinja2（`pip install jinja2`）
- PyYAML（`pip install pyyaml`）
- Terminal 最小尺寸 110 x 48（TUI 模式）

## 使用方式

### 互動式 TUI 模式

```bash
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
python create_repo.py --non-interactive \
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

在專案目錄或 `$HOME` 放一個 `.openspec-generator.yml`，TUI 會自動載入作為預填值：

```yaml
project_name: my-project
capabilities: auth, billing
target_user: End users
enable_superpowers: "yes"
git_init: "yes"
```

範例檔見 `.openspec-generator.yml.example`。

## 生成的 Repo 結構

```
<project>/
├── README.md                          ← 專案說明
├── AGENTS.md                          ← AI coding agent 規則
├── .gitignore
├── .openspec-map.md                   ← 空間索引（Agent 導航用）
├── docs/
│   ├── engineering-principles.md      ← 工程原則與交付標準
│   └── superpowers.md                 ← Superpowers 整合說明（可選）
├── openspec/
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
| 7 | config 檔支援 | 讀取 `.openspec-generator.yml` 預填預設值 |
| 8 | 路徑驗證強化 | 檢查非法字元、偵測目標已有 git repo |
| 9 | Brownfield 導入 | `--brownfield` 模式導入既有專案，不動既有檔案 |
| 10 | 追加 Change | `--add-change` 在既有 repo 新增 Change Package |

## 檔案結構

```
openspec-toolkit/
├── create_repo.py                   ← 主程式
├── README.md                           ← 本檔案
├── .openspec-generator.yml.example     ← config 範例
└── templates/
    ├── readme.md.j2                    ← 專案 README
    ├── gitignore.j2                    ← .gitignore
    ├── openspec_readme.md.j2           ← openspec/ 目錄說明
    ├── openspec_map.md.j2              ← .openspec-map.md 空間索引
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

- Side project 快速啟動 OpenSpec workflow
- 建立可跨 Cursor / Claude Code / Copilot / Kiro 搬移的 repo
- 學習 spec-driven development 的入門範本
- CI/CD 中自動初始化新專案骨架
