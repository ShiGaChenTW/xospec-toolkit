---
name: xospec-brownfield-onboard
description: 將 x.ospec Toolkit 框架導入既有專案 — 互動式引導掃描現有結構、推斷 Capabilities、建立最小規格骨架，不動既有程式碼
version: 1.0.0
triggers:
  - brownfield
  - 導入 xospec
  - 既有專案加入 xospec
  - 套用 xospec
  - retrofit xospec
  - add xospec to existing project
---

# x.ospec Brownfield Onboard

## 核心原則

> **最小侵入，受影響範圍優先。**
> 不改動既有程式碼、不改動既有目錄結構、不覆蓋任何現有檔案。
> 只新增 x.ospec 框架所需的 Markdown 檔案。

## 何時使用

- 專案已存在且有程式碼，想導入 x.ospec spec-driven 開發流程
- 從其他開發方式（Jira-driven, ad-hoc）遷移到 spec-driven
- 專案已有 git 但沒有 `xospec/` 目錄

## 導入流程（5 步驟）

Agent 收到導入請求後，**嚴格按以下順序執行**：

---

### Step 1: 掃描與理解

**目標：** 建立對專案現狀的認知地圖

```
行動清單：
1. 讀取 README.md（若有）了解專案目的
2. 執行目錄掃描：ls -la && find . -type f -name "*.md" | head -20
3. 檢查技術棧：package.json / pyproject.toml / go.mod / Cargo.toml / build.gradle
4. 檢查是否已有 xospec/（若有，跳到 Step 4 直接新增 Change）
5. 檢查是否已有 AGENTS.md / .planning/（部分導入的情況）
```

**輸出：向使用者報告**
```
📋 專案掃描結果：
- 專案名稱：<name>
- 技術棧：<stack>
- 主要目錄：<top-level dirs>
- 現有文件：<existing docs>
- x.ospec 狀態：❌ 未導入 / ⚠️ 部分導入 / ✅ 已導入
```

---

### Step 2: 推斷 Capabilities

**目標：** 從既有程式碼結構推斷功能領域

```
推斷規則（依優先順序）：
1. src/ 下的一級子目錄 → 每個可能是一個 Capability
   例：src/auth/, src/billing/, src/notification/ → auth, billing, notification
2. app/ 或 apps/ 下的子目錄（Django/Rails 風格）
3. packages/ 下的子目錄（monorepo 風格）
4. routes/ 或 api/ 下的檔案名稱
5. 若以上都無法判斷 → 使用專案名稱作為單一 Capability
```

**與使用者確認：**
```
🔍 推斷的 Capabilities：
1. auth — src/auth/ (登入、權限管理)
2. billing — src/billing/ (支付、發票)
3. notification — src/notification/ (通知推送)

請確認或修改（可新增/刪除/重新命名）：
```

**等待使用者確認後才進入 Step 3。**

---

### Step 3: 建立最小骨架

**目標：** 只新增 x.ospec 框架檔案，不動既有內容

#### 3a. 必建檔案（Layer 1-2）

```
<project>/                          ← 不動
├── .xospec-map.md               ← 新增：空間索引
├── AGENTS.md                      ← 新增：Agent 行為規範（若不存在）
├── xospec/
│   ├── README.md                  ← 新增：xospec 目錄說明
│   └── specs/
│       └── <capability>/spec.md   ← 新增：每個確認的 capability 一份基準 spec
```

#### 3b. 選擇性檔案

詢問使用者：

```
📦 選擇要導入的層級：

[必選] Layer 1-2: xospec 基本結構 + Living Specs
[ ] Layer 5a: docs/engineering-principles.md（工程原則）
[ ] Layer 5b: docs/superpowers.md + .planning/（GSD 整合）

建議：第一次導入先只裝 Layer 1-2，熟悉後再加 Layer 5。
```

#### 3c. 基準 Spec 內容

**重點：Brownfield 的基準 spec 不需要完整，只需記錄「當前已知的行為」。**

```markdown
# Spec: <capability>

## Overview
<從程式碼和文件推斷的一句話描述>

## Current Behaviors (Baseline)
<!-- 以下行為根據現有程式碼推斷，尚未完整驗證 -->

### <行為 1>
- **GIVEN** <前置條件>
- **WHEN** <觸發動作>
- **THEN** <預期結果>

## Notes
- 此基準 spec 建立於 <date>，從既有程式碼反向推斷
- 標記 `[unverified]` 的行為尚未經人工確認
- 後續 Change 的 spec_delta 將持續豐富此文件
```

#### 3d. .xospec-map.md

根據 Step 1 掃描結果和 Step 2 確認的 capabilities，生成完整地圖：

```markdown
# x.ospec Project Map

## Directory Tree & Annotations
- src/auth/            # [Capability: auth]
- src/billing/         # [Capability: billing]
- xospec/
  - specs/             # Layer 2: Living Specs
  - changes/           # Layer 3: Change Packages（尚無）

## Capability Registry
| Capability | Spec Path | Source | Status |
|------------|-----------|--------|--------|
| auth | xospec/specs/auth/spec.md | src/auth/ | Baseline |
| billing | xospec/specs/billing/spec.md | src/billing/ | Baseline |

## Active Changes
（尚無進行中的 Change）
```

---

### Step 4: 建立第一個 Change Package

**目標：** 為使用者接下來要做的工作建立 Change Package

```
詢問使用者：
你接下來要做什麼功能或修改？

範例回答：
- 「新增 PDF 發票匯出功能」→ change-id: add-billing-pdf-export
- 「修復登入 session 過期問題」→ change-id: fix-auth-session-leak
- 「先不做，我只是要導入框架」→ 跳過此步驟
```

若使用者有工作要做，建立：

```
xospec/changes/<change-id>/
├── proposal.md      ← 根據使用者描述填入 Why/Who/What
├── design.md        ← 留空模板，等使用者或 Agent 填寫
├── tasks.md         ← 留空模板
└── spec_delta.md    ← 留空模板
```

同時更新 `.xospec-map.md` 的 Active Changes 區塊。

若啟用了 GSD（Layer 5b），同時更新：
- `.planning/STATE.md` — 設定 active phase
- `.planning/ROADMAP.md` — 新增 phase

---

### Step 5: 提交與確認

```
行動：
1. git add xospec/ .xospec-map.md AGENTS.md docs/ .planning/ (若有)
2. git commit -m "chore: bootstrap x.ospec framework (brownfield onboard)"
3. 向使用者確認：

✅ x.ospec 導入完成！

新增的檔案：
  - .xospec-map.md
  - AGENTS.md
  - xospec/README.md
  - xospec/specs/auth/spec.md
  - xospec/specs/billing/spec.md
  (+ Change Package 如果有建立)

未修改任何既有檔案。

下一步：
  - 修改程式碼前，先更新 xospec/changes/<id>/tasks.md
  - 完成後，用 spec_delta.md 記錄行為變更
  - xospec-preflight hook 會自動提醒你遵守流程
```

---

## Agent 行為約束

1. **絕不修改既有程式碼** — 只新增 x.ospec 框架的 Markdown 檔案
2. **絕不覆蓋既有檔案** — 若 AGENTS.md 已存在，詢問是否合併而非覆蓋
3. **每一步都要確認** — 不要假設 capabilities，讓使用者確認
4. **最小範圍** — 只為使用者確認的 capabilities 建立 spec，不要預先建立整個系統的 spec
5. **標記不確定性** — 從程式碼推斷的行為標記 `[unverified]`

## 與其他 Skills 的協作

| Skill | 協作方式 |
|-------|---------|
| `xospec-generator` | Brownfield 不使用 generator 的 TUI/CLI，由本 Skill 的認知流程直接生成 |
| `xospec-preflight` | 導入完成後，preflight hook 自動啟動監督 |
| `superpowers:brainstorming` | Step 2 推斷 capabilities 時可用來探索方案 |
| `superpowers:writing-plans` | Step 4 建立 Change Package 時可用來填寫 design.md |
| GSD (`gsd:new-project`) | 若使用者選擇 Layer 5b，可用 GSD 初始化 .planning/ |

## 快速指令

```bash
# 方法 1: 用 Skill 互動式導入（推薦）
# 在專案目錄中對 Agent 說：「幫我導入 x.ospec」

# 方法 2: 用 generator CLI 快速建立骨架（不含互動推斷）
python create_repo.py \
  --non-interactive \
  --brownfield \
  --project-name "my-existing-project" \
  --capabilities "auth,billing" \
  --target-dir .
```
