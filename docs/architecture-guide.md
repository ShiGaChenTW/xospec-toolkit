# x.ospec + Superpowers + GSD 三合一架構說明書

## 目錄

1. [三個框架各自是什麼](#1-三個框架各自是什麼)
2. [為什麼要整合在一起](#2-為什麼要整合在一起)
3. [五層架構總覽](#3-五層架構總覽)
4. [架構中各處使用了哪個框架的原理](#4-架構中各處使用了哪個框架的原理)
5. [一個完整的開發循環](#5-一個完整的開發循環)
6. [生成的 Repo 結構與檔案對照](#6-生成的-repo-結構與檔案對照)

---

## 1. 三個框架各自是什麼

### x.ospec — 規格驅動開發（Spec-Driven Development）

x.ospec 是一套以「規格文件活在 repo 裡」為核心理念的輕量開發框架。它的設計哲學是：

- **Spec 是真相來源（Single Source of Truth）：** 所有系統行為的定義都寫在 `xospec/specs/` 下的 Markdown 檔案中，而非散落在 Jira ticket、Slack 訊息或團隊記憶裡。
- **Change 是最小變更單位：** 每次功能修改都是一個獨立的 change（放在 `xospec/changes/` 下），包含 proposal（為什麼做）、design（怎麼做）、tasks（做哪些事）三份文件。
- **Spec Delta 回寫機制：** 當 change 完成後，變更的行為差異（spec delta）會合併回 living spec，確保規格永遠是最新的。
- **Tool-agnostic：** 不綁定任何特定 IDE 或 AI 工具。Markdown 檔案可以被 Claude Code、Cursor、Copilot、Kiro 或任何文字編輯器讀取。

**x.ospec 解決的問題：** 在 AI Coding 中，Agent 缺乏對「系統應該長什麼樣」的結構化理解。沒有 spec，Agent 只能依賴 chat context 來猜測需求，結果容易偏離。

### Superpowers — AI 工程紀律層（Engineering Discipline）

Superpowers 是一套為 AI Coding Agent 設計的 skills 框架，目的是把軟體工程最佳實踐注入 AI 的工作流程中。它提供的不是程式碼，而是**行為規範**：

- **brainstorming：** 在動手之前先發散思考，探索多種方案，避免 Agent 直接跳進第一個想到的解法。
- **writing-plans：** 強制在寫程式碼前先寫出實作計畫，確保步驟明確、可審核。
- **test-driven-development（TDD）：** 先寫測試、再寫實作、最後重構，保證每一步都有驗證。
- **requesting-code-review：** 完成實作後自動觸發程式碼審查，檢查品質、安全性、效能。
- **verification-before-completion：** 在宣告完成前再跑一次驗證，防止遺漏。
- **finishing-a-development-branch：** 引導 merge/PR 流程，確保分支乾淨。

**Superpowers 解決的問題：** AI Agent 預設行為是「收到指令就開始寫程式碼」，缺乏計畫、測試、審查的紀律。Superpowers 在 Agent 的決策迴路中插入品質關卡。

### GSD（Get Stuff Done）— 階段式執行引擎（Phase-Based Execution）

GSD 是 Superpowers 生態圈中的執行編排系統。如果 Superpowers 定義了「應該有哪些工程實踐」，GSD 就定義了「按什麼順序、用什麼工具、怎麼驗收」：

- **PROJECT.md：** 專案的全域上下文（願景、使用者、技術棧、限制條件）。
- **ROADMAP.md：** 把整個專案拆成 milestone → phase 的層級結構，每個 phase 對應一個可交付的功能切片。
- **STATE.md：** 追蹤當前進度、已做的決策、遭遇的阻礙。
- **Phase 工作流：** 每個 phase 經歷 discuss → research → plan → execute → verify 五個階段。
- **Quality Gates：** 每個階段都有明確的閘門條件，不通過就不能推進到下一階段。

**GSD 解決的問題：** 即使有了 spec 和工程紀律，如果沒有明確的執行順序和進度追蹤，大型專案仍然會失控。GSD 提供了「從 roadmap 到交付」的完整調度機制。

---

## 2. 為什麼要整合在一起

### 傳統 AI Coding 的五個核心問題

| # | 問題 | 症狀 | 本架構如何解決 |
|---|------|------|----------------|
| 1 | **Context 遺失** | Agent 不記得上一輪對話講過什麼，反覆問同樣的問題 | x.ospec 的 spec 和 change 文件**活在 repo 裡**，Agent 每次開始工作都先讀檔案，不依賴 chat 記憶 |
| 2 | **Scope 漂移** | 要求做 A 功能，Agent 自作主張加了 B、C、D | x.ospec 的 proposal + tasks 嚴格定義「只做什麼」，AGENTS.md 規定「flag scope drift before coding」 |
| 3 | **品質失控** | Agent 產出的程式碼沒有測試、沒有 review，直接宣稱完成 | Superpowers 的 TDD、code-review、verification skills 強制插入品質關卡 |
| 4 | **執行無序** | Agent 隨意跳著做，沒有先後順序，難以追蹤進度 | GSD 的 ROADMAP + phase 工作流提供結構化的執行順序和進度追蹤 |
| 5 | **跨工具不可攜** | 在 Cursor 裡設定好的 workflow，換到 Claude Code 就要重來 | 三個框架都是**純 Markdown 檔案**，存在 repo 裡，搬到任何工具都能用 |

### 三者互補的關係

```
「做什麼」         「怎麼做得好」         「按什麼順序做」
 x.ospec    +     Superpowers     +      GSD
 (Spec)            (Discipline)           (Orchestration)
    │                   │                      │
    │    ┌──────────────┘                      │
    │    │                                     │
    ▼    ▼                                     ▼
 ┌─────────────────────────────────────────────────┐
 │  repo 裡的 Markdown 檔案（跨工具可攜）              │
 │                                                   │
 │  xospec/specs/       ← 規格真相（x.ospec）       │
 │  xospec/changes/     ← 變更包（x.ospec）         │
 │  .planning/ROADMAP.md  ← 執行計畫（GSD）            │
 │  .planning/STATE.md    ← 進度追蹤（GSD）            │
 │  AGENTS.md             ← Agent 行為規範（三者整合）   │
 │  docs/superpowers.md   ← 工程紀律指引（Superpowers） │
 └─────────────────────────────────────────────────┘
```

**核心價值：** 單獨使用任何一個框架都只解決部分問題。x.ospec 沒有執行順序；Superpowers 沒有規格管理；GSD 沒有 spec delta 機制。三者整合後，從「需求定義 → 計畫 → 執行 → 驗證 → 規格回寫」的完整循環才真正閉合。

---

## 3. 五層架構總覽

```
Layer 5  Superpowers + GSD   工程紀律 + 階段式執行引擎
         ────────────────────────────────────────────
Layer 4  x.ospec CLI         Spec 自動化工具（可選）
         ────────────────────────────────────────────
Layer 3  changes/             單次變更包（proposal / design / tasks）
         ────────────────────────────────────────────
Layer 2  specs/               長期 living specs（系統行為的真相來源）
         ────────────────────────────────────────────
Layer 1  repo + git           底座（版本控制 + 檔案結構）
```

### 各層的職責

| 層級 | 主要框架 | 職責 | 檔案位置 |
|------|----------|------|----------|
| Layer 1 | Git | 版本控制、分支策略、commit 歷史 | `.git/`, `.gitignore` |
| Layer 2 | x.ospec | 定義系統的「應然」狀態，每個 capability 一份 spec | `xospec/specs/<cap>/spec.md` |
| Layer 3 | x.ospec | 每次變更的完整記錄：為什麼做、怎麼做、做了什麼 | `xospec/changes/<id>/` |
| Layer 4 | x.ospec CLI | （可選）自動化生成 change skeleton、驗證 spec 一致性 | CLI 工具，不存 repo |
| Layer 5 | Superpowers + GSD | 工程紀律 skills + phase-based 執行編排 | `docs/superpowers.md`, `.planning/` |

---

## 4. 架構中各處使用了哪個框架的原理

### 4.1 `xospec/specs/<capability>/spec.md` — x.ospec 原理

**來自 x.ospec 的概念：Living Spec**

每個 capability（如 auth、billing、notification）有自己的 spec 檔案。這份文件：

- 用 RFC 2119 風格的語言（SHALL, SHOULD, MAY）描述系統行為
- 包含 Given/When/Then 格式的驗收場景
- 隨著 change 完成而持續演進（spec delta merge 回來）
- 是 Agent 判斷「我該做什麼」的第一參考來源

**為什麼不用 Jira / Notion？** 因為 AI Agent 無法直接讀取外部工具的內容。Spec 放在 repo 裡，Agent 用 `Read` 工具就能取得完整上下文。

### 4.2 `xospec/changes/<change-id>/` — x.ospec 原理

**來自 x.ospec 的概念：Change Package**

每個 change 資料夾包含三份核心文件：

| 檔案 | 用途 | x.ospec 原理 |
|------|------|---------------|
| `proposal.md` | Why — 為什麼要做這個變更 | 強制 Agent 先理解動機，再開始實作 |
| `design.md` | How — 技術設計決策 | 避免 Agent 直接跳進程式碼，先做架構思考 |
| `tasks.md` | What — 具體任務清單 | 每個任務一個 checkbox，Agent 逐一完成 |
| `specs/<cap>/spec.md` | Spec Delta — 行為差異 | 記錄這次變更對 living spec 的影響 |

### 4.3 `.planning/PROJECT.md` — GSD 原理

**來自 GSD 的概念：Project Context**

PROJECT.md 是專案的「全域記憶」。它記錄：

- 願景與使用者問題（對應 x.ospec 的 proposal 動機）
- 技術棧選擇
- 全域限制條件（效能、安全、相容性）
- 團隊組成

**為什麼需要它？** x.ospec 的 spec 是分散在各 capability 下的，缺少一個「全專案鳥瞰圖」。PROJECT.md 補上這個缺口。

### 4.4 `.planning/ROADMAP.md` — GSD 原理

**來自 GSD 的概念：Phase-Based Execution**

ROADMAP 把整個專案拆成：

```
Milestone 1: MVP
  └── Phase 1: add-auth       ← 對應 xospec/changes/add-auth/
  └── Phase 2: add-billing    ← 對應 xospec/changes/add-billing/
  └── Phase 3: add-dashboard  ← 對應 xospec/changes/add-dashboard/
```

**關鍵映射：1 個 GSD Phase = 1 個 x.ospec Change**

這是整合架構最核心的設計決策。GSD 負責「按什麼順序做」，x.ospec 負責「做的內容是什麼」。Phase 編號和 change-id 一一對應，不會產生兩套追蹤系統。

### 4.5 `.planning/STATE.md` — GSD 原理

**來自 GSD 的概念：Project Memory**

STATE.md 追蹤：

- 當前在哪個 phase
- 已做過的關鍵決策及理由
- 遭遇的阻礙

**為什麼 tasks.md 不夠？** tasks.md 只追蹤單一 change 內的任務進度。STATE.md 追蹤的是跨 change 的全域進度和決策歷史。

### 4.6 `AGENTS.md` — 三者整合

**來自三個框架的整合：Agent 行為規範**

AGENTS.md 是 AI Agent 進入 repo 後的第一份指示。它整合了：

| 規則 | 來源框架 | 原理 |
|------|----------|------|
| 「先讀 spec 和 change 文件再動手」 | x.ospec | Spec-driven：Agent 必須理解規格再行動 |
| 「使用 brainstorming skill 探索方案」 | Superpowers | 避免 Agent 直接跳進第一個解法 |
| 「使用 TDD skill 先寫測試」 | Superpowers | 品質閘門：無測試不算完成 |
| 「檢查 ROADMAP 當前 phase」 | GSD | 確保 Agent 做的事在計畫範圍內 |
| 「完成後更新 STATE.md」 | GSD | 進度追蹤：下次開啟對話時有延續性 |
| 「Flag scope drift before coding」 | x.ospec + GSD | 防止 Agent 超出 proposal 和 phase 範圍 |

### 4.7 `docs/engineering-principles.md` — Superpowers 原理

**來自 Superpowers 的概念：Definition of Done**

這份文件定義了：

- Product boundaries（做真正的使用者問題，不做 demo）
- Technical rules（偏好簡單方案、避免過度抽象）
- Testing standard（每個 bug fix 要有回歸測試）
- Definition of Done checklist（spec 更新、tasks 勾完、測試通過、文件更新）

**Superpowers 的 verification-before-completion skill 會參考這份文件**來判斷工作是否真的完成。

### 4.8 `docs/superpowers.md` — Superpowers + GSD 整合

**整合指南文件**

這份文件是給 Agent 和開發者的操作手冊，說明：

- 哪些 Superpowers skills 在什麼時機觸發
- GSD command 和 x.ospec change 的對應關係
- 檔案位置速查表

---

## 5. 一個完整的開發循環

以下是使用本架構開發一個新功能的完整流程：

```
步驟 1: 確認 Phase（GSD）
├── 讀 .planning/ROADMAP.md，找到當前 phase
├── 讀 .planning/STATE.md，確認沒有未解決的 blocker
└── 框架原理：GSD 的 phase-based execution

步驟 2: 理解需求（x.ospec）
├── 讀 xospec/changes/<change-id>/proposal.md
├── 讀相關的 xospec/specs/<cap>/spec.md
└── 框架原理：x.ospec 的 spec-driven 理念

步驟 3: 探索方案（Superpowers）
├── 觸發 brainstorming skill
├── 列出 2-3 個方案並評估取捨
└── 框架原理：Superpowers 的「先思考再行動」

步驟 4: 撰寫計畫（Superpowers + x.ospec）
├── 觸發 writing-plans skill
├── 輸出到 xospec/changes/<change-id>/design.md
├── 輸出到 xospec/changes/<change-id>/tasks.md
└── 框架原理：Superpowers 驅動，x.ospec 承載

步驟 5: TDD 實作（Superpowers）
├── 觸發 test-driven-development skill
├── 每完成一個 task，勾掉 tasks.md 中的 checkbox
├── 更新 .planning/STATE.md 記錄進度
└── 框架原理：Superpowers 的 TDD + GSD 的 state tracking

步驟 6: 程式碼審查（Superpowers）
├── 觸發 requesting-code-review skill
├── 修復 CRITICAL 和 HIGH 問題
└── 框架原理：Superpowers 的品質閘門

步驟 7: Spec 回寫（x.ospec）
├── 更新 xospec/changes/<change-id>/specs/<cap>/spec.md（delta）
├── 將 delta 合併回 xospec/specs/<cap>/spec.md（living spec）
└── 框架原理：x.ospec 的 spec delta merge

步驟 8: 完成驗收（GSD + Superpowers）
├── 觸發 verification-before-completion skill
├── 檢查 Definition of Done
├── 更新 .planning/ROADMAP.md 標記 phase 完成
├── 更新 .planning/STATE.md 推進到下一個 phase
└── 框架原理：GSD 的 quality gate + Superpowers 的 verification
```

---

## 6. 生成的 Repo 結構與檔案對照

```
<project>/
├── CLAUDE.md                                    [開發規範] 專案指示 + 開發日誌規則
├── README.md                                    [三者整合] 專案說明 + 架構圖
├── AGENTS.md                                    [三者整合] AI Agent 行為規範
├── .gitignore                                   [Layer 1]  Git 基礎設施
│
├── CHANGELOG/                                   [開發記錄]
│   ├── CHANGELOG-LIST.md                        [開發記錄] 日誌索引
│   └── YYYY-MM-DD_HHMM.md                      [開發記錄] 各 session 日誌
│
├── docs/
│   ├── CHANGELOG.md                             [版本記錄] 重大架構變更追蹤
│   ├── engineering-principles.md                [Superpowers] 工程原則 + DoD
│   └── superpowers.md                           [Superpowers + GSD] 操作指南
│
├── xospec/                                    [x.ospec]
│   ├── README.md                                [x.ospec]  目錄說明
│   ├── specs/
│   │   ├── <capability-1>/spec.md               [x.ospec]  Living spec
│   │   └── <capability-2>/spec.md               [x.ospec]  Living spec
│   └── changes/
│       └── <first-change>/
│           ├── proposal.md                      [x.ospec]  變更提案
│           ├── design.md                        [x.ospec]  技術設計
│           ├── tasks.md                         [x.ospec]  任務清單
│           └── specs/
│               └── <capability>/spec.md         [x.ospec]  Spec delta
│
└── .planning/                                   [GSD]
    ├── PROJECT.md                               [GSD]  專案全域上下文
    ├── ROADMAP.md                               [GSD]  Phase 執行計畫
    └── STATE.md                                 [GSD]  當前進度追蹤
```

### 框架歸屬摘要

| 框架 | 負責的檔案 | 核心職責 |
|------|-----------|----------|
| **x.ospec** | `xospec/` 整個目錄 | 定義「系統應該是什麼樣」 |
| **Superpowers** | `docs/engineering-principles.md`, `docs/superpowers.md` | 定義「怎麼做得好」 |
| **GSD** | `.planning/` 整個目錄 | 定義「按什麼順序做、做到哪了」 |
| **三者整合** | `README.md`, `AGENTS.md` | 統一入口 + Agent 行為規範 |
| **開發規範** | `CLAUDE.md` | 專案指示、開發日誌規則 |
| **開發記錄** | `CHANGELOG/` 整個目錄 | 每次 session 的結構化日誌與索引 |
| **版本記錄** | `docs/CHANGELOG.md` | 重大架構變更的版本追蹤 |

---

## 附錄：術語對照表

| 術語 | 所屬框架 | 定義 |
|------|----------|------|
| Living Spec | x.ospec | 隨專案演進持續更新的系統行為規格文件 |
| Change | x.ospec | 一次功能變更的完整包（proposal + design + tasks + spec delta） |
| Spec Delta | x.ospec | 一次 change 對 living spec 造成的行為差異 |
| Capability | x.ospec | 系統的功能領域（如 auth、billing） |
| Skill | Superpowers | 一個可被 Agent 自動觸發的工程實踐（如 TDD、code-review） |
| Definition of Done | Superpowers | 判斷一個任務是否真正完成的檢查清單 |
| Phase | GSD | 一個可交付的功能切片，對應一個 x.ospec change |
| Milestone | GSD | 多個 phase 組成的交付里程碑（如 MVP） |
| Quality Gate | GSD | 階段推進前必須通過的驗證條件 |
| STATE | GSD | 專案的當前進度快照，包含決策歷史和阻礙記錄 |
