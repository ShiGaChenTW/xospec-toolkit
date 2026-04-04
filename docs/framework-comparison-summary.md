# Superpowers vs Spec Kit vs OpenSpec 研究總結

> 原始資料來源：Perplexity AI 對話（8 輪問答）
> 原始檔案：`Superpowers vs spec-kit vs openspec,可以混用嗎.md`
> 總結日期：2026-04-02

---

## 1. 三個框架定位

| 框架 | 定位 | 核心能力 |
|------|------|----------|
| **OpenSpec** | 輕量 spec-driven 規格層 | specs 活在 repo 裡，按 capability 組織，brownfield-first，tool-agnostic |
| **Spec Kit** | 完整 SDD 流程框架 | intent-driven，涵蓋 greenfield/brownfield/creative exploration，multi-step refinement |
| **Superpowers** | AI Agent 工程紀律層 | brainstorming、planning、TDD、code review、verification 等 skills |

## 2. 混用結論

### 推薦組合：OpenSpec + Superpowers

- OpenSpec 管需求、變更與 spec delta
- Superpowers 管 TDD、review、refactor 等工程紀律
- 兩者不衝突，OpenSpec 管「做什麼」，Superpowers 管「怎麼做得好」

### 可行但需注意：Spec Kit + Superpowers

- Spec Kit 當主 spec/plan/tasks 流程，Superpowers 補強實作紀律
- 必須先定義哪一邊是文件真相來源

### 不建議：OpenSpec + Spec Kit 同時當主系統

- 兩者都管理規格、計畫與任務，會造成雙份文件和雙份維護
- 核心原則：**同一個專案只保留一套主 spec 系統**

## 3. 跨工具可攜性分析

### 關鍵決策：選擇「repo 檔案驅動」而非「IDE 一條龍」

對話中確認的 workflow 偏好是 **repo 檔案驅動、可跨工具搬移**，理由：

- OpenSpec 把自己定位為 universal planning layer，不綁定特定 AI agent
- specs 直接 check in 到 codebase，透過 git/PR/review 協作
- 真正延續上下文的不是聊天串，而是 repo 裡的文件
- 可跨 Cursor、Claude Code、Copilot、Kiro 共用同一批 artifacts

### 與 Kiro 的關係

- Kiro 有原生 Specs（Requirements → Design → Tasks），可取代 OpenSpec 或 Spec Kit
- 如果用 Kiro 原生 Specs，就不要再疊 OpenSpec 或 Spec Kit，否則會雙重管理
- Superpowers 在 Kiro 上可行但屬社群做法，非官方內建
- 結論：如果走 repo-first 路線，Kiro 只當 IDE 宿主，不啟用 Kiro Specs

## 4. OpenSpec 兩層架構

對話中深入探討了 OpenSpec 的核心設計——把 repo 拆成兩種不同壽命的知識：

### 長期規格層：`openspec/specs/`

- Capability library，每個能力一份 `spec.md`
- 描述 Purpose、Requirements、Scenarios（Given/When/Then）
- 作為系統的「穩定真相來源」
- 類比：系統的說明書，新人或新 Agent 進來先讀這裡

### 單次變更層：`openspec/changes/<change-id>/`

- 每次功能變更的完整包：proposal → design → tasks → spec delta
- `proposal.md`：為什麼做（Why + Scope + Out of Scope + Acceptance）
- `design.md`：技術決策（Context + Decision + Impact + Risks）
- `tasks.md`：可逐步勾選的任務清單
- `specs/<cap>/spec.md`：spec delta，顯示需求如何被修改
- 類比：一張工單的完整記錄，做完後 delta 合併回 living spec

### 兩層的關係

- Change 是暫時層，spec 是最終沉澱的長期層
- 完成後 spec delta merge 回 living spec
- Reviewer 先看 intent（proposal + spec delta），再看 code diff

## 5. 建議的五層架構

對話中最終確認的架構（後來成為 OpenSpec Toolkit 的基礎）：

```
Layer 5  Superpowers       → 工程紀律（plan / TDD / review）
Layer 4  OpenSpec CLI       → Spec 自動化工具（可選）
Layer 3  changes/           → 單次變更包（proposal/design/tasks）
Layer 2  specs/             → 長期 living specs
Layer 1  repo + git         → 底座
```

- Layer 1-3 由 generator 自動生成
- Layer 4 可選安裝 OpenSpec CLI
- Layer 5 可選安裝 Superpowers skills

## 6. 日常開發流程

對話中整理出的標準操作流程：

1. 確認 `openspec/specs/<capability>/spec.md` 存在，沒有就先補基本規格
2. 開 change folder，先寫 `proposal.md`（why + scope + acceptance）
3. 寫 `design.md`（技術決策 + 影響 + 風險）
4. 拆 `tasks.md`，每個 task 控制在一次 agent 執行可完成的大小
5. 實作時只給 Agent 當次 change folder + 相關 spec，避免過多無關上下文
6. 每完成一個 task 更新 `tasks.md`，行為改變時同步更新 spec delta
7. PR review 順序：proposal → design → tasks → spec delta → code diff

## 7. 通用提示詞（跨工具可用）

### 開 Proposal

```
Read docs/engineering-principles.md and the relevant files under openspec/specs/.
I want to add a new feature.
First, create a new change folder under openspec/changes/<change-id>/.
Write: proposal.md, design.md, tasks.md, any necessary spec delta.
Do not write code yet.
```

### 做單一 Task

```
Read: engineering-principles.md, related spec.md, proposal.md, design.md, tasks.md.
Implement only the next unchecked task. Keep the diff small. Add or update tests.
When finished, mark only that task as done.
```

### 做 Review

```
Review this change in the following order:
1. proposal.md  2. design.md  3. tasks.md  4. spec delta  5. code diff
Report: scope mismatch, design risks, missing tests, spec/code inconsistency.
Do not rewrite code yet; review first.
```

## 8. 關鍵決策記錄

| 決策 | 選擇 | 排除 | 理由 |
|------|------|------|------|
| 主規格系統 | OpenSpec | Spec Kit | 更輕量、明確主打 repo-first 和 brownfield-first |
| Workflow 類型 | Repo 檔案驅動 | IDE 一條龍 | 跨工具可攜，不綁定 Kiro/Cursor/任何 IDE |
| Superpowers 角色 | 工程紀律層 | 規格管理 | 與 OpenSpec 互補，不重疊 |
| Kiro 角色 | 純 IDE 宿主 | 啟用 Kiro Specs | 避免與 OpenSpec 雙重管理 |
| Spec Kit 命運 | 不採用 | 與 OpenSpec 並存 | 同專案不保留兩套 spec 系統 |

---

> 本總結濃縮自約 1700 行 Perplexity 對話原文。原文包含重複段落（每則回覆被複製兩次），以及範例檔案模板（已由 OpenSpec Toolkit 的 Jinja2 模板取代）。如需查閱原始對話細節，參見原始檔案。
