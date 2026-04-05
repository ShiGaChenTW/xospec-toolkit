---
name: xospec-architect
description: x.ospec Toolkit 原生架構師 — Agent 根據五層結構規範，動態生成與維護 spec-driven repo，支援 Greenfield/Brownfield，跨 AI 工具通用
version: 2.1.0
triggers:
  - xospec
  - repo 骨架
  - scaffold
  - 變更提案
  - change proposal
  - spec driven
  - 建立 Change Package
  - 新增 change
---

# x.ospec-Architect-Native (純認知導航版)

## 1. 核心定位

- **角色**：x.ospec 原生架構師
- **哲學**：**Repo 即地圖，檔案即真相**。不依賴外部 Python 腳本，由 Agent 根據專案現況動態生成符合 x.ospec Toolkit 規範的五層結構
- **注意**：Greenfield 新專案請改用 `xospec-create` Skill，本 Skill 負責既有 x.ospec 專案的日常開發與擴展
- **跨工具通用**：完全相容 Cursor、Claude Code、GitHub Copilot、Kiro 等所有具備檔案讀寫能力的 AI 工具

## 2. 空間感知：地圖導航機制

為解決跨 LLM 時的認知分歧，Agent 必須維護 `.xospec-map.md` 作為空間索引。

### 啟動校準流程

1. 進入專案第一件事：檢查是否存在 `.xospec-map.md`
2. 若無地圖：執行 `ls -R` 並產出地圖（目錄樹 + Capability 映射備註）
3. 每次對話開始或接手新任務：**必須先讀取地圖**確認開發上下文

### 地圖檔案結構 (.xospec-map.md)

```markdown
# x.ospec Project Map

## Directory Tree & Annotations
- src/auth/            # [Capability: auth] 處理登入與 Session
- src/billing/         # [Capability: billing] 處理支付與發票邏輯
- xospec/
  - specs/             # Layer 2: 長期規格庫 (Living Specs)
  - changes/           # Layer 3: 變更執行包 (Change Packages)

## Active Status
- [Active] add-auth-remember-me (ID: add-auth-remember-me)
- [Last Update] 2026-03-31
```

## 3. 判定邏輯：何時啟動變更流程？

Agent 必須在動手寫碼前，自主判定是否建立 `/xospec/changes/<id>/`：

**觸發條件：**
- 涉及業務邏輯增強
- API 協議改動
- UI 流程變更
- 非瑣碎 Bug 修復

**Change ID 命名規範：** `[動作]-[能力]-[簡短描述]`，全小寫、數字與連字號 `-`
- 正確：`add-billing-pdf-export`, `fix-auth-session-leak`

## 4. 五層結構規範

```
Layer 5  Superpowers      → 工程紀律（plan / TDD / review）       [可選]
Layer 4  x.ospec CLI      → 自動生成 spec 流程                    [可選]
Layer 3  changes/         → 單次變更包（proposal/design/tasks）    [核心]
Layer 2  specs/           → 長期 living specs                      [核心]
Layer 1  repo + git       → 底座                                  [必備]
```

### Greenfield（新專案）

Agent 直接在根目錄生成 Layer 1-3 骨架：

1. **Layer 1**：生成 `AGENTS.md` 與 `docs/engineering-principles.md`
2. **Layer 2**：建立初始 `xospec/specs/<capability>/spec.md`
3. **Layer 3**：建立第一個 Change Package

生成的目錄結構：

```
<project>/
├── README.md
├── AGENTS.md
├── .gitignore
├── .xospec-map.md
├── docs/
│   ├── engineering-principles.md
│   └── superpowers.md                 [可選]
├── xospec/
│   ├── README.md
│   ├── specs/
│   │   └── <capability>/spec.md
│   └── changes/
│       └── <first-change>/
│           ├── proposal.md
│           ├── design.md
│           ├── tasks.md
│           └── spec_delta.md          ← 行為變更規格
```

### Brownfield（既有專案）

1. **受影響範圍原則**：僅針對本次變更涉及的功能，在 `xospec/specs/` 補齊基準線規格
2. **掛載變更包**：建立資料夾並填充 `proposal.md`, `design.md`, `tasks.md`

## 5. 檔案內容標準模板

### proposal.md — 為什麼要做

```markdown
# Proposal: <change-id>

## Why (使用者問題)
<描述使用者遇到的痛點>

## Who (目標對象)
<受影響的使用者角色>

## What (變更內容)
<高層次描述這次要做什麼>

## Acceptance Criteria (驗收標準)
- [ ] <可驗證的條件 1>
- [ ] <可驗證的條件 2>
```

### design.md — 怎麼做

```markdown
# Design: <change-id>

## Overview (技術決策)
<架構選擇與理由>

## Implementation Notes (實作筆記)
<具體實作細節>

## Open Questions (未決事項)
- [ ] <待確認的問題>
```

### tasks.md — 做的順序

```markdown
# Tasks: <change-id>

- [ ] 任務 1：<具體可執行的小步驟>
- [ ] 任務 2：<具體可執行的小步驟>
- [ ] 任務 3：<具體可執行的小步驟>
```

嚴格執行「完成一個小任務、勾選一個 `[x]`」的紀律。

### spec_delta.md — 行為變更規格

使用 GIVEN/WHEN/THEN 格式精確描述行為變更：

```markdown
# Spec Delta: <change-id>

## <行為名稱>
- **GIVEN** <前置條件>
- **WHEN** <觸發動作>
- **THEN** <預期結果>
```

## 6. GSD 整合：`.planning/` 目錄規範

當使用者啟用 Superpowers（`--enable-superpowers yes`），同時生成 GSD 執行層：

### 生成的檔案

```
.planning/
├── PROJECT.md    # 專案全局上下文（願景、技術棧、約束）
├── ROADMAP.md    # 里程碑 → Phase 層級結構
└── STATE.md      # 當前進度、決策記錄、阻塞項
```

### 核心映射：1 Phase = 1 x.ospec Change

| GSD 概念 | x.ospec 對應 | 說明 |
|----------|--------------|------|
| Milestone | 一組相關 Changes | 產品版本或功能群組 |
| Phase | `xospec/changes/<id>/` | 單次變更執行單元 |
| Phase Goal | `proposal.md` 的 Acceptance Criteria | 驗收標準 |
| Phase Plan | `design.md` + `tasks.md` | 技術方案與執行步驟 |

### Agent 行為要求

1. 開始新 Phase 前：先建立對應的 Change Package
2. Phase 完成時：更新 `STATE.md` 並確認 `tasks.md` 全部勾選
3. 里程碑完成時：將所有 `spec_delta.md` 合併回 Living Specs

### Spec Delta 合併流程

當一個 Change 的所有 tasks 完成且通過驗收：

1. 讀取 `xospec/changes/<id>/spec_delta.md` 中的 GIVEN/WHEN/THEN
2. 將新行為追加到對應的 `xospec/specs/<capability>/spec.md`
3. 在 `spec_delta.md` 頂部標記 `Status: Merged`
4. 提交：`docs: merge spec delta <id> into living spec`

## 7. Agent 行為約束 (Hard Constraints)

1. **檔案驅動**：嚴禁在未更新 `tasks.md` 或 `design.md` 的情況下直接修改代碼
2. **地圖同步**：每當建立新 Change 或新的 Capability 資料夾，必須立即更新 `.xospec-map.md`
3. **小步提交**：保持 Diff 最小化，優先確保測試通過
4. **跨工具共識**：Agent 應主動告知使用者：「我已根據 `.xospec-map.md` 定位上下文，現在準備執行 `tasks.md` 中的下一個任務。」

## 8. Generator 工具（可選）

本 Skill 內建 Python 腳本，可批次生成骨架。Generator 工具位於專案根目錄：

```
xospec-toolkit/
├── create_repo.py
├── .xospec-generator.yml.example
├── templates/              # 15 個 Jinja2 模板（含 GSD + Superpowers + Map）
├── docs/                   # 架構指南與框架比較文件
└── skills/
    └── xospec-generator/
        └── SKILL.md        # 本檔案
```

使用方式（以專案根目錄為基準）：

```bash
# TUI 互動模式
python3 create_repo.py

# CLI Non-Interactive 模式
python3 create_repo.py \
  --non-interactive \
  --project-name "my-billing-service" \
  --capabilities "auth,billing,notification" \
  --target-dir ./my-billing-service \
  --target-user "End users" \
  --user-problem "Users cannot track invoices efficiently"
```

需求：Python 3.10+、`pip install -r requirements.txt`
