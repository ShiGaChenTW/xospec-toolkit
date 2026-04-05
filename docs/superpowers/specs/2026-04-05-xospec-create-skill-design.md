# Design: xospec-create Skill

> 使用者的「新專案入口」Skill — 一句話觸發，Agent 完成問答、建造專案、引導下一步。

## 1. 定位與觸發

### 角色

`xospec-create` 是 X.OSpec Toolkit 的 **Greenfield 專案建造入口**。使用者安裝好 toolkit 後，每次需要開新專案時呼叫此 Skill。

### 觸發詞

- `xospec-create`
- `建新專案` / `new project` / `start project`
- `開發` / `coding` / `開始開發`

### 與現有 Skill 的關係

| Skill | 角色 | 關係 |
|-------|------|------|
| **xospec-create**（本 Skill） | 建造入口 | 從 0 到 1 建立新專案 |
| xospec-generator | 架構師 | 建完後負責日常開發（新 Change、擴展 Capability） |
| xospec-brownfield-onboard | 既有專案導入 | 與 create 互斥（create = greenfield） |
| xospec-preflight | 開發守衛 | 專案建好後自動生效 |

## 2. 流程設計（3 階段）

### Phase 1: 環境偵測

Agent 啟動後自動偵測 xospec-toolkit 是否已安裝：

1. 檢查常見路徑：
   - `$HOME/Documents/Coding-Project/xospec-toolkit/`
   - `$HOME/xospec-toolkit/`
   - 環境變數 `$XOSPEC_TOOLKIT_PATH`
2. 檢查 `create_repo.py` 是否存在於偵測到的路徑
3. 若找到 toolkit：確認 Python 3.10+ 可用、依賴已安裝（`jinja2`, `pyyaml`）
4. 輸出：`toolkit_path`（字串）或 `null`（進入 fallback）

### Phase 2: 對話式收集參數

Agent 逐一詢問使用者以下資訊（對齊 `create_repo.py` 的 QUESTIONS）：

**必填欄位：**

| 欄位 | 說明 | 範例 |
|------|------|------|
| project_name | 專案名稱 | My Billing Service |
| capabilities | 系統 capabilities（逗號分隔） | auth, billing |
| first_change_name | 第一個 feature/change 名稱 | 新增登入功能 |
| first_change_capability | 第一個 change 屬於哪個 capability | auth |
| user_problem | 主要使用者問題 | 使用者無法追蹤發票 |
| target_user | 目標使用者 | End users |

**選填欄位（提供預設值，使用者可跳過）：**

| 欄位 | 預設值 |
|------|--------|
| target_dir | 專案名稱的 slug |
| feature_why | It delivers the first meaningful user value |
| overwrite | no |
| enable_superpowers | yes |
| git_init | yes |

收集完畢後，顯示**參數摘要**讓使用者確認再進入生成。

### Phase 3: 生成專案

#### 路徑 A — 有 Toolkit

組裝 CLI 參數，執行：

```bash
cd <toolkit_path> && python3 create_repo.py \
  --non-interactive \
  --project-name "<project_name>" \
  --capabilities "<capabilities>" \
  --target-dir "<target_dir>" \
  --first-change-name "<first_change_name>" \
  --first-change-capability "<first_change_capability>" \
  --user-problem "<user_problem>" \
  --target-user "<target_user>" \
  --feature-why "<feature_why>" \
  --overwrite "<overwrite>" \
  --enable-superpowers "<enable_superpowers>" \
  --git-init "<git_init>"
```

#### 路徑 B — 無 Toolkit（Fallback 認知導航）

Agent 讀取 toolkit 的 15 個 Jinja2 模板作為參考，使用 Write 工具逐一生成對應檔案，完全對齊 `create_repo.py` 的產出結構：

```
<project>/
├── README.md
├── AGENTS.md
├── .gitignore
├── .xospec-map.md
├── docs/
│   ├── engineering-principles.md
│   └── superpowers.md                 [enable_superpowers=yes 時]
├── xospec/
│   ├── README.md
│   ├── specs/
│   │   └── <capability>/spec.md       [每個 capability 一個]
│   └── changes/
│       └── <first-change>/
│           ├── proposal.md
│           ├── design.md
│           ├── tasks.md
│           └── spec_delta.md
└── .planning/                          [enable_superpowers=yes 時]
    ├── PROJECT.md
    ├── ROADMAP.md
    └── STATE.md
```

Fallback 時若 `git_init=yes`，Agent 執行 `git init` + 初始 commit。

### Phase 4: 完成後選單

生成完成後，顯示下一步選項：

```
專案已建立完成！接下來你想：

1. 開始第一個 Change 開發（進入 xospec-generator 流程）
2. 用 IDE 開啟專案（code <dir> / cursor <dir>）
3. 安裝 xospec Skills 到新專案
```

使用者選擇後，Agent 執行對應動作。

## 3. 錯誤處理

| 情境 | 處理方式 |
|------|----------|
| Python 版本不足 | 提示使用者升級，fallback 到認知導航 |
| 依賴未安裝 | 詢問是否自動 `pip install`，或 fallback |
| 目標路徑已存在 | 依 overwrite 欄位決定；預設不覆寫，提示使用者 |
| create_repo.py 執行失敗 | 顯示錯誤輸出，fallback 到認知導航 |

## 4. 設計決策

- **預設 CLI 模式（非 TUI）**：Agent 先對話收集參數，再一次性執行，避免 TUI 與 Agent 互動衝突
- **完全對齊產出**：Fallback 模式不做簡化版，確保無論哪條路徑產出一致
- **選單導引而非自動銜接**：給使用者選擇權，降低意外操作風險
