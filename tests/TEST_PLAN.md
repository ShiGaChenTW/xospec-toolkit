# OpenSpec Toolkit 測試計畫

## 測試對象總覽

| 元件 | 類型 | 檔案位置 | 測試重點 |
|------|------|----------|----------|
| `create_repo.py` | Python CLI | 專案根目錄 | Greenfield / Brownfield / add-change 三種模式 |
| `openspec-preflight.js` | Node.js hook | `~/.claude/hooks/` | PreToolUse 攔截邏輯 |
| Jinja2 模板 (15 個) | Template | `templates/` | 渲染結果正確性 |

---

## A. create_repo.py 測試

### A1. Greenfield 模式（完整生成）

#### A1-1: 基本生成 — 預設值

```
指令：python3 create_repo.py --non-interactive --project-name "test-project" --target-dir $TMPDIR/test-greenfield
預期：
  ✅ 生成 README.md
  ✅ 生成 .gitignore
  ✅ 生成 AGENTS.md
  ✅ 生成 .openspec-map.md
  ✅ 生成 openspec/README.md
  ✅ 生成 openspec/specs/auth/spec.md（預設 capability）
  ✅ 生成 openspec/specs/billing/spec.md（預設 capability）
  ✅ 生成 openspec/changes/add-auth/proposal.md
  ✅ 生成 openspec/changes/add-auth/design.md
  ✅ 生成 openspec/changes/add-auth/tasks.md
  ✅ 生成 openspec/changes/add-auth/spec_delta.md（扁平路徑，非 specs/<cap>/spec.md）
  ✅ 生成 docs/engineering-principles.md
  ✅ 生成 docs/superpowers.md（預設 enable_superpowers=yes）
  ✅ 生成 .planning/PROJECT.md
  ✅ 生成 .planning/ROADMAP.md
  ✅ 生成 .planning/STATE.md
  ✅ 自動 git init + initial commit
  ✅ git log 有一筆 commit，訊息含 "bootstrap OpenSpec"
驗證：
  - find $TMPDIR/test-greenfield -type f | sort（比對檔案清單）
  - git -C $TMPDIR/test-greenfield log --oneline（確認 commit）
```

#### A1-2: 自訂參數

```
指令：python3 create_repo.py --non-interactive \
  --project-name "billing-service" \
  --capabilities "payment,invoice,notification" \
  --first-change-name "add-payment-gateway" \
  --first-change-capability "payment" \
  --user-problem "Users cannot pay online" \
  --target-user "E-commerce buyers" \
  --feature-why "Enable core revenue flow" \
  --target-dir $TMPDIR/test-custom
預期：
  ✅ openspec/specs/ 下有 payment/, invoice/, notification/ 三個目錄
  ✅ openspec/changes/add-payment-gateway/ 存在
  ✅ proposal.md 含 "Users cannot pay online"
  ✅ proposal.md 含 "E-commerce buyers"
  ✅ .openspec-map.md 含 "payment", "invoice", "notification"
  ✅ .planning/ROADMAP.md 含 "add-payment-gateway"
  ✅ .planning/STATE.md 含 "add-payment-gateway"
```

#### A1-3: 停用 Superpowers

```
指令：python3 create_repo.py --non-interactive \
  --project-name "minimal" \
  --enable-superpowers no \
  --target-dir $TMPDIR/test-minimal
預期：
  ✅ docs/superpowers.md 不存在
  ✅ .planning/ 目錄不存在
  ✅ 其他核心檔案仍正常生成
```

#### A1-4: 停用 git init

```
指令：python3 create_repo.py --non-interactive \
  --project-name "no-git" \
  --git-init no \
  --target-dir $TMPDIR/test-no-git
預期：
  ✅ .git/ 目錄不存在
  ✅ 所有模板檔案正常生成
```

#### A1-5: overwrite=no 不覆蓋

```
前置：先生成一次，然後修改 README.md 內容
指令：再跑一次相同指令（overwrite=no）
預期：
  ✅ README.md 內容未被覆蓋（保留修改後的版本）
  ✅ stdout 顯示 "skip" 而非 "write"
```

#### A1-6: CLI 預設值警告

```
指令：python3 create_repo.py --non-interactive --project-name "warn-test" --target-dir $TMPDIR/test-warn
預期：
  ✅ stdout 含 "⚠ 以下必填參數未提供，使用預設值"
  ✅ 列出 --capabilities, --first-change-name, --first-change-capability, --user-problem, --target-user
```

#### A1-7: 缺少 project-name 應報錯

```
指令：python3 create_repo.py --non-interactive --target-dir $TMPDIR/fail
預期：
  ✅ exit code != 0
  ✅ stderr/stdout 含 "必須提供 --project-name"
```

---

### A2. Brownfield 模式（既有專案導入）

#### A2-1: 基本 brownfield 導入

```
前置：
  mkdir -p $TMPDIR/test-brown/src/auth $TMPDIR/test-brown/src/billing
  echo "# Existing" > $TMPDIR/test-brown/README.md
  git -C $TMPDIR/test-brown init && git -C $TMPDIR/test-brown add . && git -C $TMPDIR/test-brown commit -m "init"

指令：python3 create_repo.py --non-interactive --brownfield \
  --project-name "test-brown" \
  --capabilities "auth,billing" \
  --target-dir $TMPDIR/test-brown
預期：
  ✅ README.md 內容仍是 "# Existing"（未被覆蓋）
  ✅ .gitignore 未被生成（brownfield 不產生）
  ✅ openspec/ 結構正確
  ✅ AGENTS.md 存在
  ✅ .openspec-map.md 存在
  ✅ git log 有第二筆 commit，訊息含 "brownfield onboard"
```

#### A2-2: brownfield + superpowers 停用

```
指令：同 A2-1 但加 --enable-superpowers no
預期：
  ✅ .planning/ 不存在
  ✅ docs/superpowers.md 不存在
  ✅ docs/engineering-principles.md 仍存在
```

---

### A3. --add-change 模式

#### A3-1: 在既有 openspec repo 新增 change

```
前置：先用 Greenfield 模式生成 $TMPDIR/test-add-change

指令：python3 create_repo.py --add-change "fix-auth-session-leak" \
  --first-change-capability auth \
  --target-dir $TMPDIR/test-add-change
預期：
  ✅ openspec/changes/fix-auth-session-leak/ 存在
  ✅ 含 proposal.md, design.md, tasks.md, spec_delta.md
  ✅ .openspec-map.md 含 "fix-auth-session-leak"
  ✅ openspec/specs/auth/spec.md 未被覆蓋（已存在）
```

#### A3-2: 自動推斷 capability

```
指令：python3 create_repo.py --add-change "add-billing-pdf-export" \
  --target-dir $TMPDIR/test-add-change
預期（不提供 --first-change-capability）：
  ✅ 從 change name 推斷 capability 為 "billing"
  ✅ openspec/changes/add-billing-pdf-export/ 存在
```

#### A3-3: 重複 change name 應報錯

```
前置：A3-1 已建立 fix-auth-session-leak
指令：再跑一次相同的 --add-change "fix-auth-session-leak"
預期：
  ✅ exit code != 0
  ✅ stdout 含 "已存在"
```

#### A3-4: 無 openspec/ 目錄應報錯

```
指令：python3 create_repo.py --add-change "some-change" --target-dir $TMPDIR/empty-dir
預期：
  ✅ exit code != 0
  ✅ stdout 含 "不存在" 和 "--brownfield"
```

#### A3-5: 新 capability 自動建立 spec

```
指令：python3 create_repo.py --add-change "add-analytics-dashboard" \
  --first-change-capability analytics \
  --target-dir $TMPDIR/test-add-change
預期：
  ✅ openspec/specs/analytics/spec.md 被新建（之前不存在）
  ✅ openspec/changes/add-analytics-dashboard/ 存在
```

#### A3-6: GSD STATE.md 自動更新

```
前置：$TMPDIR/test-add-change 有 .planning/STATE.md
指令：A3-1 的指令
預期：
  ✅ .planning/STATE.md 中 **Name:** 更新為 "fix-auth-session-leak"
```

---

## B. openspec-preflight.js 測試

### 測試方式

以 stdin 傳入模擬的 PreToolUse JSON，檢查 exit code 和 stderr 輸出：

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"<PATH>"}}' | node openspec-preflight.js
echo "Exit: $?"
```

#### B1-1: 非 OpenSpec 專案 → 放行

```
前置：mkdir -p $TMPDIR/test-hook-plain/src
輸入：{"tool_name":"Write","tool_input":{"file_path":"$TMPDIR/test-hook-plain/src/app.js"}}
預期：
  ✅ exit code = 0
  ✅ 無 stderr 輸出
```

#### B1-2: OpenSpec 專案、無 active change → 阻擋

```
前置：
  mkdir -p $TMPDIR/test-hook-block/openspec/specs/auth
  # 不建立任何 changes/

輸入：{"tool_name":"Write","tool_input":{"file_path":"$TMPDIR/test-hook-block/src/auth.js"}}
預期：
  ✅ exit code = 2
  ✅ stderr 含 "⛔" 和 "沒有進行中的 Change Package"
```

#### B1-3: 有 active change + 未完成 tasks → 放行並顯示進度

```
前置：
  mkdir -p $TMPDIR/test-hook-ok/openspec/changes/add-auth
  echo "- [ ] Task 1\n- [x] Task 2\n- [ ] Task 3" > $TMPDIR/test-hook-ok/openspec/changes/add-auth/tasks.md

輸入：{"tool_name":"Write","tool_input":{"file_path":"$TMPDIR/test-hook-ok/src/auth.js"}}
預期：
  ✅ exit code = 0
  ✅ stderr 含 "✅ OpenSpec: add-auth [1/3]"
```

#### B1-4: 全部 tasks 已完成 → 警告但放行

```
前置：
  mkdir -p $TMPDIR/test-hook-done/openspec/changes/add-auth
  echo "- [x] Task 1\n- [x] Task 2" > $TMPDIR/test-hook-done/openspec/changes/add-auth/tasks.md

輸入：{"tool_name":"Write","tool_input":{"file_path":"$TMPDIR/test-hook-done/src/auth.js"}}
預期：
  ✅ exit code = 0
  ✅ stderr 含 "⚠️" 和 "所有任務已完成"
```

#### B1-5: 修改 spec 檔案 → 跳過檢查

```
輸入：{"tool_name":"Edit","tool_input":{"file_path":"$TMPDIR/test-hook-ok/openspec/specs/auth/spec.md"}}
預期：
  ✅ exit code = 0
  ✅ 無 stderr（跳過，不檢查）
```

#### B1-6: 修改測試檔案 → 跳過檢查

```
輸入：{"tool_name":"Write","tool_input":{"file_path":"$TMPDIR/test-hook-block/src/auth.test.js"}}
預期：
  ✅ exit code = 0
  ✅ 無 stderr（測試檔案不受 preflight 限制）
```

#### B1-7: 修改 docs/ → 跳過檢查

```
輸入：{"tool_name":"Edit","tool_input":{"file_path":"$TMPDIR/test-hook-block/docs/README.md"}}
預期：
  ✅ exit code = 0
```

#### B1-8: 修改設定檔 → 跳過檢查

```
輸入：{"tool_name":"Write","tool_input":{"file_path":"$TMPDIR/test-hook-block/package.json"}}
預期：
  ✅ exit code = 0
```

#### B1-9: 非 Write/Edit 工具 → 放行

```
輸入：{"tool_name":"Bash","tool_input":{"command":"ls"}}
預期：
  ✅ exit code = 0
```

#### B1-10: 無效 JSON → 放行（不 crash）

```
輸入：not-json-at-all
預期：
  ✅ exit code = 0
```

#### B1-11: STATE.md 提供 active change

```
前置：
  mkdir -p $TMPDIR/test-hook-state/openspec/specs/auth
  mkdir -p $TMPDIR/test-hook-state/.planning
  # 注意：沒有 changes/ 目錄，但 STATE.md 指向一個 change
  cat > $TMPDIR/test-hook-state/.planning/STATE.md << 'EOF'
  ## Current Phase
  - **Name:** add-auth
  - **Status:** in-progress
  EOF
  mkdir -p $TMPDIR/test-hook-state/openspec/changes/add-auth
  echo "- [ ] Task A" > $TMPDIR/test-hook-state/openspec/changes/add-auth/tasks.md

輸入：{"tool_name":"Write","tool_input":{"file_path":"$TMPDIR/test-hook-state/src/main.js"}}
預期：
  ✅ exit code = 0
  ✅ stderr 含 "✅ OpenSpec: add-auth [0/1]"
```

---

## C. Jinja2 模板渲染測試

### 測試方式

用 Python 腳本載入模板、傳入標準 context、驗證渲染結果：

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates/"), keep_trailing_newline=True)
ctx = {
    "project_name": "test-project",
    "target_user": "End users",
    "user_problem": "Cannot track invoices",
    "feature_why": "Core revenue flow",
    "capabilities": ["auth", "billing"],
    "change_id": "add-billing-export",
    "first_change_capability": "billing",
    "enable_superpowers": True,
    "today": "2026-04-04",
    "capability": "auth",  # for spec.md.j2
}
```

#### C1: 每個模板都能無錯渲染

```
對 15 個 .j2 模板逐一呼叫 env.get_template(name).render(**ctx)
預期：
  ✅ 全部無 UndefinedError
  ✅ 全部輸出非空字串
```

#### C2: openspec_map.md.j2 內容驗證

```
result = env.get_template("openspec_map.md.j2").render(**ctx)
預期：
  ✅ 含 "auth" 和 "billing" 在 Capability Registry 表格中
  ✅ 含 "add-billing-export" 在 Active Changes 表格中
  ✅ 含 "2026-04-04" 日期
  ✅ 含 ".planning/" 區塊（因為 enable_superpowers=True）
```

#### C3: openspec_map.md.j2 停用 superpowers

```
ctx_no_sp = {**ctx, "enable_superpowers": False}
result = env.get_template("openspec_map.md.j2").render(**ctx_no_sp)
預期：
  ✅ 不含 ".planning/"
```

#### C4: spec.md.j2 使用 capability 變數

```
result = env.get_template("spec.md.j2").render(capability="billing", **ctx)
預期：
  ✅ 標題含 "billing"
```

#### C5: gsd_roadmap.md.j2 含 change 對應

```
result = env.get_template("gsd_roadmap.md.j2").render(**ctx)
預期：
  ✅ 含 "add-billing-export"
  ✅ 含 "openspec/changes/add-billing-export/"
```

---

## D. 整合測試（端到端）

### D1: 完整 Greenfield → add-change → preflight 流程

```
步驟 1: Greenfield 生成
  python3 create_repo.py --non-interactive \
    --project-name "e2e-test" \
    --capabilities "auth,billing" \
    --target-dir $TMPDIR/e2e-test

步驟 2: 驗證 preflight 放行（有 active change + tasks）
  echo '{"tool_name":"Write","tool_input":{"file_path":"'$TMPDIR'/e2e-test/src/auth.js"}}' \
    | node openspec-preflight.js
  → exit code = 0, stderr 含 "✅"

步驟 3: 把所有 tasks 勾完
  sed -i '' 's/- \[ \]/- [x]/g' $TMPDIR/e2e-test/openspec/changes/add-auth/tasks.md

步驟 4: 驗證 preflight 警告（tasks 全完成）
  echo '{"tool_name":"Write","tool_input":{"file_path":"'$TMPDIR'/e2e-test/src/auth.js"}}' \
    | node openspec-preflight.js
  → exit code = 0, stderr 含 "⚠️"

步驟 5: 新增 change
  python3 create_repo.py --add-change "add-billing-invoice" \
    --first-change-capability billing \
    --target-dir $TMPDIR/e2e-test

步驟 6: 驗證 preflight 再次放行（新 change 有 tasks）
  → exit code = 0, stderr 含 "✅ OpenSpec: add-billing-invoice"
```

### D2: 完整 Brownfield → add-change → preflight 流程

```
步驟 1: 建立既有專案
  mkdir -p $TMPDIR/e2e-brown/src/payments $TMPDIR/e2e-brown/src/users
  echo "console.log('hello')" > $TMPDIR/e2e-brown/src/payments/index.js
  echo "# My App" > $TMPDIR/e2e-brown/README.md
  git -C $TMPDIR/e2e-brown init
  git -C $TMPDIR/e2e-brown add . && git -C $TMPDIR/e2e-brown commit -m "init"

步驟 2: Brownfield 導入
  python3 create_repo.py --non-interactive --brownfield \
    --project-name "e2e-brown" \
    --capabilities "payments,users" \
    --target-dir $TMPDIR/e2e-brown

步驟 3: 驗證
  ✅ README.md 仍是 "# My App"
  ✅ openspec/specs/payments/spec.md 存在
  ✅ openspec/specs/users/spec.md 存在
  ✅ git log 有 "brownfield onboard" commit
  ✅ .openspec-map.md 含 "payments" 和 "users"

步驟 4: preflight 正常運作
  echo '{"tool_name":"Write","tool_input":{"file_path":"'$TMPDIR'/e2e-brown/src/payments/new.js"}}' \
    | node openspec-preflight.js
  → exit code = 0（有 active change）

步驟 5: add-change
  python3 create_repo.py --add-change "fix-users-session-bug" \
    --target-dir $TMPDIR/e2e-brown
  ✅ openspec/changes/fix-users-session-bug/ 存在
  ✅ capability 自動推斷為 "users"
```

---

## E. 邊界與錯誤處理測試

| # | 場景 | 預期 |
|---|------|------|
| E1 | `--project-name` 含特殊字元 `"My Project!!!"` | slugify 為 `my-project` |
| E2 | `--capabilities ""` 空字串 | 預設為 `["core"]` |
| E3 | `--target-dir` 指向不存在的深層路徑 | 自動 `mkdir -p` 建立 |
| E4 | `--first-change-capability` 不在 capabilities 中 | 自動加入 capabilities |
| E5 | 模板目錄不存在 | 報錯並 exit（不要 silent fail） |
| E6 | preflight hook stdin 超時（3秒） | exit 0（放行，不阻塞 Agent） |
| E7 | preflight hook 遇到 symlink 目錄 | 正常解析，不報錯 |

---

## 測試執行架構

```
tests/
├── TEST_PLAN.md              ← 本檔案
├── test_generator.sh         ← A 系列：shell 腳本跑 CLI 測試
├── test_preflight.sh         ← B 系列：shell 腳本跑 hook 測試
├── test_templates.py         ← C 系列：Python 跑模板渲染測試
├── test_e2e.sh               ← D 系列：端到端整合測試
└── fixtures/                 ← 測試用的假專案結構
    ├── plain-project/        ← 無 openspec 的普通專案
    ├── openspec-project/     ← 有完整 openspec 的專案
    └── partial-project/      ← 部分導入的專案
```

### 執行方式

```bash
# 全部跑
cd openspec-toolkit
bash tests/test_generator.sh && bash tests/test_preflight.sh && python3 tests/test_templates.py && bash tests/test_e2e.sh

# 單獨跑某系列
bash tests/test_generator.sh    # A 系列
bash tests/test_preflight.sh    # B 系列
python3 tests/test_templates.py # C 系列
bash tests/test_e2e.sh          # D 系列
```

### 交付給下一個 Agent 的指令

```
請根據 tests/TEST_PLAN.md 建立以下四個測試檔案：
1. tests/test_generator.sh — 涵蓋 A1~A3 所有案例
2. tests/test_preflight.sh — 涵蓋 B1~B11 所有案例
3. tests/test_templates.py — 涵蓋 C1~C5 所有案例
4. tests/test_e2e.sh — 涵蓋 D1~D2 完整流程

每個測試案例需要：
- 明確的 setup（建立臨時目錄和假資料）
- 執行指令
- 斷言（exit code、檔案存在、內容比對）
- teardown（清理臨時目錄）
- 輸出 PASS/FAIL 和總計

主程式路徑：./create_repo.py
Hook 路徑：~/.claude/hooks/openspec-preflight.js
模板路徑：./templates/
```
