# OpenSpec Toolkit

## 專案簡介

互動式 TUI + CLI 工具，一鍵建立符合 OpenSpec 規範的 repo 骨架。

- 主程式：`create_repo.py`（單檔，Python 3.10+，依賴 Jinja2 + PyYAML）
- 模板目錄：`templates/*.j2`（15 個 Jinja2 模板）
- 架構：OpenSpec + Superpowers + GSD 三合一五層架構
- 詳細架構說明：`docs/architecture-guide.md`
- 版本記錄：`docs/CHANGELOG.md`

## 開發日誌規則

每次啟動開發 session 時，必須在 `CHANGELOG/` 建立當次 session 日誌檔，並更新索引。

### 檔案規範

- 存放目錄：`CHANGELOG/`（專案根目錄第一層）
- 檔名格式：`YYYY-MM-DD_HHMM.md`（日期 + 啟動時間）
- 索引檔案：`CHANGELOG/CHANGELOG-LIST.md`（每次新增日誌後同步更新）
- 版本記錄：`docs/CHANGELOG.md`（重大架構變更時更新）

### 日誌結構

每份日誌檔包含以下區塊，依序排列：

#### 1. Session 資訊（表格）

| 欄位 | 說明 | 來源 |
|------|------|------|
| 啟動時間 | session 開始時記錄，`YYYY-MM-DD HH:MM` | 手動記錄 |
| 結束時間 | session 結束時回填 | 手動回填 |
| 執行時長 | 結束 - 啟動，單位：分鐘 | 自動計算 |
| 啟動 Agent | 當前執行的 AI agent 與模型 | 如 Claude Code (Opus 4.6) |
| 工作目錄 | 當前操作的 repo 絕對路徑 | `$PWD` |
| 觸發方式 | 手動啟動 / hook / cron / CLI | 區分人工或自動化 |
| Context 使用量 | token 消耗量 / 上限 | agent 統計 |

#### 2. 變更統計（表格）

| 欄位 | 說明 |
|------|------|
| 新增檔案 | 本次 session 新增的檔案數量 |
| 修改檔案 | 本次 session 修改的檔案數量 |
| 刪除檔案 | 本次 session 刪除的檔案數量 |
| 新增行數 | `+N` |
| 刪除行數 | `-N` |
| 淨變更行數 | 新增 - 刪除 |
| Git 分支 | 當前工作分支名稱 |
| Git 狀態 | untracked / modified / staged 各幾個 |
| Commit 數 | 本次 session 產生的 commit 數量 |
| Commit Hash | 最後一筆 commit 的 short hash，未 commit 填 `--` |

#### 3. 檔案異動明細（表格）

| 欄位 | 說明 |
|------|------|
| 狀態 | 新增 / 修改 / 刪除 |
| 檔案路徑 | 相對於專案根目錄的路徑 |
| 說明 | 這個檔案做了什麼 |
| 行數變更 | `+N` / `-N` / `+N / -M` |

#### 4. Session 目標

本次 session 要完成的事項，1-3 句話。

#### 5. 決策記錄

做了什麼技術決策、為什麼這樣選。每條一行。

#### 6. 遇到的問題

開發中碰到的 bug、阻礙、意外行為。

#### 7. 解決方式

問題如何解決，或標記 `[pending]`。

#### 8. 待辦事項

本次未完成、下次需接續的工作，用 `- [ ]` 格式。

#### 9. 學到的東西（可選）

值得記住的發現或 pattern。

### CHANGELOG-LIST.md 索引格式

每筆一行，包含日期、時間、agent、摘要：

```markdown
| 日期 | 時間 | Agent | 摘要 |
|------|------|-------|------|
| 2026-04-03 | 15:24 | Claude Code (Opus 4.6) | 建立開發日誌機制與 CLAUDE.md |
```
