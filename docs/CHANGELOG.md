# Changelog

## 2.0.0 — 開發日誌機制（2026-04-03）

### 背景

專案原本缺少 `CLAUDE.md` 專案指示檔與開發日誌規範，AI agent 進入 repo 時缺乏上下文。本次新增結構化的開發日誌機制，確保每次 session 有完整記錄可追溯。

### 核心設計決策

**每次 session 獨立一檔，索引集中管理**

日誌存放在專案根目錄 `CHANGELOG/`，檔名格式 `YYYY-MM-DD_HHMM.md`，每次 session 獨立建檔。`CHANGELOG-LIST.md` 作為索引表格，彙整所有日誌的日期、agent、摘要與連結。

### 新增檔案

| 檔案 | 用途 |
|------|------|
| `CLAUDE.md` | 專案級 Claude Code 指示 — 專案簡介、開發日誌規則、日誌結構定義 |
| `CHANGELOG/CHANGELOG-LIST.md` | 日誌索引 — 以表格格式彙整所有 session 日誌 |
| `CHANGELOG/2026-04-03_1524.md` | 第一筆開發日誌（本次 session） |

### 修改檔案

#### `docs/CHANGELOG.md`

新增本區塊（2.0.0），記錄開發日誌機制的架構變更。

### 日誌結構說明

每份日誌檔包含 9 大區塊：

1. **Session 資訊** — 啟動/結束時間、agent、工作目錄、觸發方式、context 使用量
2. **變更統計** — 新增/修改/刪除檔案數、行數變更、Git 狀態
3. **檔案異動明細** — 每個異動檔案的狀態、路徑、說明、行數
4. **Session 目標** — 本次要完成的事項
5. **決策記錄** — 技術選擇與原因
6. **遇到的問題** — Bug、阻礙、意外行為
7. **解決方式** — 如何解決或標記 pending
8. **待辦事項** — 未完成的接續工作
9. **學到的東西**（可選）— 值得記住的發現

### 生成結果變化

**Before（1.1）：**
```
<project>/
├── README.md
├── AGENTS.md
├── .gitignore
├── docs/
├── xospec/
└── .planning/
```

**After（1.0.2）：**
```
<project>/
├── CLAUDE.md                       <-- 新增：專案指示與日誌規範
├── README.md
├── AGENTS.md
├── .gitignore
├── CHANGELOG/                      <-- 新增：開發日誌目錄
│   ├── CHANGELOG-LIST.md           <-- 日誌索引
│   └── YYYY-MM-DD_HHMM.md         <-- 各 session 日誌
├── docs/
├── xospec/
└── .planning/
```

### 向後相容性

- 已生成的 1.1 repo 不受影響
- `CHANGELOG/` 為獨立目錄，不干擾 `xospec/` 或 `.planning/`
- `CLAUDE.md` 僅供 Claude Code 讀取，不影響其他工具

---

## 1.1.0 — GSD 整合（2026-04-02）

### 背景

1.0 原本採用 x.ospec + Superpowers 的五層架構。本次更新將 GSD（Get Stuff Done）執行引擎整合進 Layer 5，使生成的 repo 同時具備「規格驅動」（x.ospec）、「工程紀律」（Superpowers）和「階段式執行編排」（GSD）三合一能力。

### 核心設計決策

**1 個 GSD Phase = 1 個 x.ospec Change**

這是本次整合最關鍵的映射關係。GSD 負責「按什麼順序做」，x.ospec 負責「做的內容是什麼」。兩套系統共用同一個變更粒度，不會產生重複追蹤。

### 新增檔案

| 檔案 | 用途 |
|------|------|
| `templates/gsd_project.md.j2` | GSD PROJECT.md 模板 — 專案願景、使用者、capabilities、限制條件 |
| `templates/gsd_roadmap.md.j2` | GSD ROADMAP.md 模板 — milestone/phase 結構，phase 編號對應 x.ospec change |
| `templates/gsd_state.md.j2` | GSD STATE.md 模板 — 當前 phase 進度、決策記錄、blocker 追蹤 |
| `templates/superpowers.md.j2` | Superpowers 整合指南模板 — 取代原本硬編碼在 Python 中的字串，新增 GSD command 對照表 |
| `docs/architecture-guide.md` | 三合一架構完整說明書 — 三框架說明、整合原因、五層架構、逐檔案原理解說、開發循環、術語表 |
| `CHANGELOG.md` | 本檔案 — 版本追蹤 |

### 修改檔案

#### `create_repo_1.0.py`

**變更位置：** `generate_repo()` 函式中的 Superpowers integration 區塊（原第 422–436 行）

**Before：**
```python
if enable_superpowers:
    superpowers_note = (
        "# Superpowers Integration\n\n"
        "This project uses Superpowers for engineering discipline.\n\n"
        # ... 硬編碼的字串
    )
    write_file(repo_root / "docs" / "superpowers.md", superpowers_note, overwrite)
```

**After：**
```python
if enable_superpowers:
    # Superpowers 改用 Jinja2 模板
    write_file(
        repo_root / "docs" / "superpowers.md",
        env.get_template("superpowers.md.j2").render(ctx),
        overwrite,
    )

    # GSD .planning/ scaffold（新增）
    planning_dir = repo_root / ".planning"
    write_file(planning_dir / "PROJECT.md", env.get_template("gsd_project.md.j2").render(ctx), overwrite)
    write_file(planning_dir / "ROADMAP.md", env.get_template("gsd_roadmap.md.j2").render(ctx), overwrite)
    write_file(planning_dir / "STATE.md", env.get_template("gsd_state.md.j2").render(ctx), overwrite)
```

**設計考量：** GSD 生成邏輯綁定在 `enable_superpowers` 條件下，因為 GSD 是 Superpowers 生態圈的一部分，兩者不應獨立開關。

#### `templates/agents.md.j2`

**變更範圍：** 全檔重寫

**新增內容：**
- 「Read first」清單加入 `.planning/STATE.md` 和 `.planning/ROADMAP.md`
- 新增「Starting a new change (GSD + x.ospec)」workflow 章節，定義 8 步流程
- Rules 加入「Update `.planning/STATE.md` when phase status changes」

**設計考量：** AGENTS.md 是 AI Agent 進入 repo 後的第一份指示，必須整合三個框架的行為規範，而非只反映 x.ospec。

#### `templates/readme.md.j2`

**變更範圍：** 全檔重寫

**新增內容：**
- Architecture 區塊顯示五層架構圖
- Project Structure 加入 `.planning/` 目錄
- Workflow 步驟加入 GSD 的 ROADMAP 和 STATE 操作

### 生成結果變化

**Before（1.0）：**
```
<project>/
├── README.md
├── AGENTS.md
├── .gitignore
├── docs/
│   ├── engineering-principles.md
│   └── superpowers.md              ← 純 Superpowers
└── xospec/
    ├── README.md
    ├── specs/
    └── changes/
```

**After（1.1）：**
```
<project>/
├── README.md                       ← 含五層架構圖
├── AGENTS.md                       ← 整合三框架行為規範
├── .gitignore
├── docs/
│   ├── engineering-principles.md
│   └── superpowers.md              ← 含 GSD command 對照
├── xospec/
│   ├── README.md
│   ├── specs/
│   └── changes/
└── .planning/                      ← 新增：GSD 骨架
    ├── PROJECT.md
    ├── ROADMAP.md
    └── STATE.md
```

### 未變更的檔案

以下檔案在本次更新中**未修改**，維持 1.0 原樣：

- `templates/spec.md.j2` — Living spec 模板
- `templates/spec_delta.md.j2` — Spec delta 模板
- `templates/proposal.md.j2` — 變更提案模板
- `templates/design.md.j2` — 技術設計模板
- `templates/tasks.md.j2` — 任務清單模板
- `templates/xospec_readme.md.j2` — x.ospec 目錄說明
- `templates/gitignore.j2` — .gitignore 模板
- `templates/engineering_principles.md.j2` — 工程原則模板
- `.xospec-generator.yml.example` — Config 範例檔

### CLI 介面變化

**無變化。** `--enable-superpowers yes`（預設值）現在同時啟用 Superpowers 和 GSD。不需要新增 CLI 參數。

### 向後相容性

- 已生成的 1.0 repo 不受影響
- `--enable-superpowers no` 時行為與 1.0 完全相同（不生成 `docs/superpowers.md` 和 `.planning/`）
- 新增的 `.planning/` 目錄不會干擾 x.ospec 的 `xospec/` 目錄
