---
name: xospec-preflight
description: PreToolUse hook — 攔截 Write/Edit，確保 Agent 在 x.ospec 專案中遵守「先有 Change Package，再寫程式碼」的紀律
version: 1.0.0
triggers:
  - xospec preflight
  - xospec guard
  - 程式碼攔截
  - change package check
---

# x.ospec Preflight Guard

## 核心功能

PreToolUse hook，在 Agent 修改程式碼前自動檢查：

1. **Active Change 檢查** — 是否有進行中的 Change Package
2. **Tasks 狀態檢查** — tasks.md 是否有未完成的任務
3. **計畫外修改警告** — 所有任務已完成時，警告可能的 scope drift

## 行為邏輯

```
Agent 要 Write/Edit 檔案
    │
    ├── 檔案是 spec/docs/config？ → 放行（不檢查）
    ├── 專案沒有 xospec/ 目錄？ → 放行（非 x.ospec 專案）
    │
    ├── 沒有 active change？
    │   └── ⛔ 阻擋 + 提示建立 Change Package
    │
    ├── tasks.md 是空的？
    │   └── ⚠️ 警告 + 放行（可能在初始設定）
    │
    ├── tasks.md 全部完成？
    │   └── ⚠️ 警告 scope drift + 放行
    │
    └── 有未完成任務？
        └── ✅ 放行 + 顯示進度 [done/total]
```

## 不檢查的檔案

以下路徑自動跳過，不觸發 preflight：

- `xospec/` — spec 文件本身
- `.planning/` — GSD 執行層
- `docs/`, `AGENTS.md`, `README.md`, `CLAUDE.md` — 文件
- `CHANGELOG/` — 日誌
- 設定檔（`package.json`, `tsconfig`, `.eslintrc` 等）
- 測試檔案（`*.test.ts`, `*.spec.py`, `__tests__/`）
- 套件鎖定檔（`package-lock.json`, `yarn.lock` 等）

## 安裝

### 1. 複製 hook 腳本到 hooks 目錄

```bash
cp xospec-preflight.js ~/.claude/hooks/xospec-preflight.js
```

### 2. 在 settings.json 加入 PreToolUse hook

在 `~/.claude/settings.json` 的 `hooks` 區塊中加入：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "node ~/.claude/hooks/xospec-preflight.js"
          }
        ]
      }
    ]
  }
}
```

### 3. 建立 Skill symlink（選用）

```bash
ln -sfn /path/to/xospec-toolkit/skills/xospec-preflight ~/.claude/skills/xospec-preflight
```

## 與其他 Skills 的協作

| Skill | 關係 |
|-------|------|
| `xospec-generator` | 生成的 repo 結構是 preflight 的檢查依據 |
| `superpowers:writing-plans` | 建立 design.md + tasks.md，滿足 preflight 的前置條件 |
| `superpowers:test-driven-development` | 測試檔案被豁免檢查，TDD 流程不受干擾 |
| GSD (`gsd:plan-phase`) | 更新 `.planning/STATE.md`，提供 active change 資訊 |

## 疑難排解

**Q: Hook 誤擋了不該擋的檔案？**
A: 在 `SKIP_PATTERNS` 陣列中加入該路徑的 pattern。

**Q: 我不想在某個專案啟用 preflight？**
A: 只要專案根目錄沒有 `xospec/` 資料夾，hook 就會自動跳過。

**Q: 阻擋時怎麼快速修正？**
A: 執行 `/xospec-generator` skill 建立 Change Package，或手動建立 `xospec/changes/<id>/` 目錄與 `proposal.md`、`design.md`、`tasks.md`。
