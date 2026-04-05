---
name: xospec-create
description: X.OSpec 新專案建造入口 — 對話式收集參數，自動偵測 toolkit 後以 CLI 或認知導航生成完整 repo 骨架，完成後提供下一步選單
version: 1.0.0
triggers:
  - xospec-create
  - 建新專案
  - new project
  - start project
  - xospec 開發
  - xospec coding
  - 用 xospec 開始開發
---

# xospec-create — 新專案建造 Skill

## 1. 核心定位

使用者安裝好 X.OSpec Toolkit 後，每次要開新專案時呼叫此 Skill。Agent 透過對話收集參數，自動建造符合 x.ospec 五層結構的完整 repo。

## 2. 啟動流程（4 階段）

```
Phase 1 → 環境偵測（自動，不問使用者）
Phase 2 → 對話式收集參數
Phase 3 → 生成專案
Phase 4 → 完成後選單
```

---

## Phase 1: 環境偵測

Agent 啟動後，**靜默**執行以下偵測（不需要問使用者）：

### 步驟

1. 依序檢查以下路徑，找到第一個包含 `create_repo.py` 的即為 toolkit 路徑：
   - 環境變數 `$XOSPEC_TOOLKIT_PATH`
   - `$HOME/Documents/Coding-Project/xospec-toolkit/`
   - `$HOME/xospec-toolkit/`
2. 若找到 toolkit：
   - 確認 `python3 --version` >= 3.10
   - 確認 `python3 -c "import jinja2, yaml"` 不報錯
   - 全部通過 → `mode = "cli"`
   - 任一失敗 → 提示使用者，`mode = "fallback"`
3. 若未找到 toolkit → `mode = "fallback"`

### 輸出

向使用者簡短報告偵測結果：

- CLI 模式：`✔ 偵測到 X.OSpec Toolkit（<path>），將使用 CLI 模式生成專案。`
- Fallback 模式：`⚠ 未偵測到 X.OSpec Toolkit，將由 Agent 直接生成專案結構。`

---

## Phase 2: 對話式收集參數

Agent **逐一**向使用者詢問以下欄位。每次一個問題，收到回答後再問下一個。

### 必填欄位（依序詢問）

| # | 欄位 | 問法 | 說明 |
|---|------|------|------|
| 1 | project_name | 「專案名稱是什麼？」 | 例如：My Billing Service |
| 2 | capabilities | 「這個系統有哪些 capabilities？（逗號分隔）」 | 例如：auth, billing, notification |
| 3 | first_change_name | 「第一個要做的 feature / change 名稱？」 | 例如：新增登入功能 |
| 4 | first_change_capability | 「這個 change 主要屬於哪個 capability？」 | 從上面的 capabilities 中選 |
| 5 | user_problem | 「這個專案想解決什麼使用者問題？」 | 一句話描述痛點 |
| 6 | target_user | 「主要目標使用者是誰？」 | 例如：End users |

### 選填欄位（一次性列出，讓使用者確認或修改）

詢問完必填欄位後，顯示選填欄位的預設值，讓使用者一次確認：

```
以下為選填設定（直接按 Enter 使用預設值）：

- 專案目錄：<project_name 的 slug>
- 為什麼先做這個 feature：It delivers the first meaningful user value
- 覆寫已存在檔案：no
- 啟用 Superpowers 整合：yes
- 自動 git init：yes

需要調整哪一項嗎？（輸入欄位名稱修改，或直接確認）
```

### 確認摘要

所有參數收集完畢後，顯示**完整摘要表格**讓使用者最終確認：

```
┌─ 專案建造摘要 ─────────────────────────┐
│ 專案名稱：My Billing Service            │
│ 目標目錄：./my-billing-service           │
│ Capabilities：auth, billing              │
│ 第一個 Change：add-auth-login            │
│ 所屬 Capability：auth                    │
│ 使用者問題：使用者無法追蹤發票            │
│ 目標使用者：End users                    │
│ Superpowers：yes                         │
│ Git Init：yes                            │
│ 生成模式：CLI / Fallback                 │
└──────────────────────────────────────────┘

確認開始生成？（Y/n）
```

---

## Phase 3: 生成專案

### 路徑 A — CLI 模式（有 Toolkit）

組裝 CLI 參數並執行：

```bash
cd <toolkit_path> && python3 create_repo.py \
  --non-interactive \
  --project-name "<project_name>" \
  --capabilities "<capabilities>" \
  --target-dir "<絕對路徑>" \
  --first-change-name "<first_change_name>" \
  --first-change-capability "<first_change_capability>" \
  --user-problem "<user_problem>" \
  --target-user "<target_user>" \
  --feature-why "<feature_why>" \
  --overwrite "<overwrite>" \
  --enable-superpowers "<enable_superpowers>" \
  --git-init "<git_init>"
```

**注意事項：**
- `--target-dir` 必須使用絕對路徑（因為 cd 到了 toolkit 目錄）
- 參數值中若含空白或特殊字元，需用引號包裹
- 執行後顯示 `create_repo.py` 的輸出

### 路徑 B — Fallback 認知導航（無 Toolkit）

Agent 使用 Write 工具，**完全對齊** `create_repo.py` 的產出，逐一生成以下檔案：

#### 必定生成（Layer 1-3）

```
<project>/
├── README.md                              ← readme.md.j2
├── AGENTS.md                              ← agents.md.j2
├── .gitignore                             ← gitignore.j2
├── .xospec-map.md                         ← xospec_map.md.j2
├── docs/
│   └── engineering-principles.md          ← engineering_principles.md.j2
├── xospec/
│   ├── README.md                          ← xospec_readme.md.j2
│   ├── specs/
│   │   └── <capability>/spec.md           ← spec.md.j2（每個 capability 一個）
│   └── changes/
│       └── <first-change>/
│           ├── proposal.md                ← proposal.md.j2
│           ├── design.md                  ← design.md.j2
│           ├── tasks.md                   ← tasks.md.j2
│           └── spec_delta.md              ← spec_delta.md.j2
```

#### enable_superpowers = yes 時額外生成

```
├── docs/
│   └── superpowers.md                     ← superpowers.md.j2
└── .planning/
    ├── PROJECT.md                         ← gsd_project.md.j2
    ├── ROADMAP.md                         ← gsd_roadmap.md.j2
    └── STATE.md                           ← gsd_state.md.j2
```

#### Fallback 內容對齊規則

Agent 在生成每個檔案時，必須遵守以下原則：

1. **結構對齊**：每個檔案的標題、章節順序、格式必須與對應 `.j2` 模板一致
2. **變數替換**：將模板變數替換為使用者提供的實際值
3. **條件邏輯**：`.xospec-map.md` 中的 `.planning/` 區塊僅在 `enable_superpowers=yes` 時包含
4. **Git Init**：若 `git_init=yes`，執行 `git init` + `git add .` + `git commit -m "chore: bootstrap x.ospec repo structure"`

### 模板變數對照表

| 變數名 | 來源 |
|--------|------|
| `project_name` | 使用者輸入 |
| `target_user` | 使用者輸入 |
| `user_problem` | 使用者輸入 |
| `feature_why` | 使用者輸入或預設值 |
| `capabilities` | 使用者輸入，解析為 list |
| `change_id` | `first_change_name` 經 slugify |
| `first_change_capability` | 使用者輸入，經 slugify |
| `enable_superpowers` | 使用者輸入，布林值 |
| `today` | 當天日期，ISO 格式 |

**slugify 規則**：小寫 → 非英數字元替換為 `-` → 合併連續 `-` → 去首尾 `-`

---

## Phase 4: 完成後選單

生成完成後，顯示以下選單：

```
✔ 專案已建立完成！

接下來你想做什麼？

  1) 開始第一個 Change 開發（進入 xospec-generator 流程）
  2) 用 IDE 開啟專案
     - code <dir>（VS Code）
     - cursor <dir>（Cursor）
  3) 安裝 xospec Skills 到新專案
     - 將 xospec-generator、xospec-preflight 等 Skill symlink 到新專案

請選擇（1/2/3）：
```

### 選項行為

| 選項 | Agent 行為 |
|------|-----------|
| 1 | 提示使用者可呼叫 `xospec-generator` Skill，或直接說明如何開始第一個 Change 的開發 |
| 2 | 詢問使用者偏好的 IDE，執行對應的 `code <dir>` 或 `cursor <dir>` 指令 |
| 3 | 說明如何將 Skills symlink 到 `~/.claude/skills/`，或執行 `setup.sh` 的 Skill 安裝段落 |

---

## 3. 錯誤處理

| 情境 | 處理方式 |
|------|----------|
| Python 版本不足 | 提示升級，自動 fallback 到認知導航 |
| 依賴未安裝 | 詢問是否自動 `pip install -r requirements.txt`，否則 fallback |
| 目標路徑已存在且 overwrite=no | 提示使用者選擇：覆寫、換路徑、或取消 |
| `create_repo.py` 執行失敗 | 顯示錯誤輸出，自動 fallback 到認知導航 |
| 使用者中途取消 | 尊重取消，不留殘留檔案 |

---

## 4. 與其他 Skill 的關係

| Skill | 何時銜接 |
|-------|----------|
| `xospec-generator` | 專案建好後，使用者選擇「開始開發」時提示可用 |
| `xospec-brownfield-onboard` | 若使用者的意圖是導入既有專案而非建新專案，引導至此 Skill |
| `xospec-preflight` | 專案建好後自動生效（若已安裝為 hook） |
