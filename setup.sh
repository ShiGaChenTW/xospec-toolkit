#!/usr/bin/env bash
# =============================================================================
# OpenSpec Toolkit — Setup & Launcher
#
# 一鍵完成：環境檢查 → 安裝依賴 → 安裝 Skills & Hook → 啟動 Generator
# =============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
CLAUDE_DIR="$HOME/.claude"
SKILLS_DIR="$CLAUDE_DIR/skills"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# ── 顏色 ─────────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { printf "${CYAN}▸${NC} %s\n" "$1"; }
ok()    { printf "${GREEN}✔${NC} %s\n" "$1"; }
warn()  { printf "${YELLOW}⚠${NC} %s\n" "$1"; }
fail()  { printf "${RED}✖${NC} %s\n" "$1"; exit 1; }
header(){ printf "\n${BOLD}── %s ──${NC}\n\n" "$1"; }

# ── 使用說明 ──────────────────────────────────────────────────────────────────

usage() {
  cat <<EOF
${BOLD}OpenSpec Toolkit Setup${NC}

用法: ./setup.sh [選項]

${BOLD}基本選項:${NC}
  --install             只安裝依賴與 Skills（不啟動 Generator）
  --run                 跳過安裝，直接啟動 Generator TUI
  --uninstall           移除已安裝的 Skills 與 Hook
  --status              顯示目前安裝狀態
  --help                顯示此說明

${BOLD}使用情境:${NC}

  ${CYAN}1. 全新專案（Greenfield）${NC}
     ./setup.sh
     → 啟動 TUI，填寫資訊後生成新的 OpenSpec repo

  ${CYAN}2. 既有專案導入（Brownfield）${NC}
     cd /path/to/your-existing-project
     /path/to/openspec-toolkit/setup.sh --brownfield
     → 在當前目錄注入 OpenSpec 框架，不動既有程式碼

  ${CYAN}3. Fork 下來的專案${NC}
     git clone https://github.com/someone/some-project.git
     cd some-project
     /path/to/openspec-toolkit/setup.sh --brownfield
     → 對 fork 專案導入 OpenSpec 框架

  ${CYAN}4. 追加 Change Package${NC}
     cd /path/to/your-openspec-project
     /path/to/openspec-toolkit/setup.sh --add-change "add-billing-export"
     → 在既有 OpenSpec 專案中新增一個 Change Package

  ${CYAN}5. CI/CD 自動化${NC}
     ./setup.sh --non-interactive --project-name "my-app" --capabilities "auth,billing"

所有 create_repo.py 的參數皆可直接附加在 setup.sh 後面。
EOF
  exit 0
}

# ── Step 1: 環境檢查 ─────────────────────────────────────────────────────────

check_env() {
  header "Step 1/4: 環境檢查"

  # Python 版本
  if ! command -v python3 &>/dev/null; then
    fail "找不到 python3，請先安裝 Python 3.10+"
  fi

  PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
  PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

  if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    fail "需要 Python 3.10+，目前為 $PY_VER"
  fi
  ok "Python $PY_VER"

  # Node.js（preflight hook 需要）
  if command -v node &>/dev/null; then
    NODE_VER=$(node -v)
    ok "Node.js $NODE_VER（preflight hook 可用）"
  else
    warn "找不到 Node.js — preflight hook 將無法安裝（Generator 仍可正常使用）"
  fi

  # 終端尺寸（TUI 模式需要 110 x 48）
  COLS=$(tput cols 2>/dev/null || echo 0)
  ROWS=$(tput lines 2>/dev/null || echo 0)
  if [ "$COLS" -ge 110 ] && [ "$ROWS" -ge 48 ]; then
    ok "終端尺寸 ${COLS}x${ROWS}"
  else
    warn "終端尺寸 ${COLS}x${ROWS}（TUI 模式建議 110x48 以上）"
  fi
}

# ── Step 2: 安裝 Python 依賴 ─────────────────────────────────────────────────

activate_venv() {
  if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
  fi
}

install_deps() {
  header "Step 2/4: Python 依賴"

  # 建立 venv（若不存在）
  if [ ! -d "$VENV_DIR" ]; then
    info "建立虛擬環境 .venv/"
    python3 -m venv "$VENV_DIR"
    ok "虛擬環境已建立"
  else
    ok "虛擬環境已存在"
  fi

  activate_venv

  local missing=()
  python3 -c "import jinja2" 2>/dev/null || missing+=(jinja2)
  python3 -c "import yaml"   2>/dev/null || missing+=(pyyaml)

  if [ ${#missing[@]} -eq 0 ]; then
    ok "jinja2, pyyaml 已安裝"
  else
    info "安裝缺少的套件: ${missing[*]}"
    python3 -m pip install --quiet -r "$SCRIPT_DIR/requirements.txt"
    ok "Python 依賴安裝完成"
  fi
}

# ── Step 3: 安裝 Claude Code Skills ──────────────────────────────────────────

install_skills() {
  header "Step 3/4: Claude Code Skills"

  # 檢查 Claude Code 是否存在
  if [ ! -d "$CLAUDE_DIR" ]; then
    warn "找不到 ~/.claude 目錄 — 跳過 Skills 安裝（Generator 仍可正常使用）"
    return 0
  fi

  mkdir -p "$SKILLS_DIR"

  local skills=("openspec-generator" "openspec-preflight" "openspec-brownfield-onboard")

  for skill in "${skills[@]}"; do
    local src="$SCRIPT_DIR/skills/$skill"
    local dst="$SKILLS_DIR/$skill"

    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
      ok "$skill（已安裝）"
    elif [ -e "$dst" ]; then
      warn "$skill — $dst 已存在且非本專案的 symlink，跳過"
    else
      ln -sfn "$src" "$dst"
      ok "$skill → 已建立 symlink"
    fi
  done
}

# ── Step 4: 安裝 Preflight Hook ──────────────────────────────────────────────

install_hook() {
  header "Step 4/4: Preflight Hook"

  if ! command -v node &>/dev/null; then
    warn "Node.js 未安裝，跳過 preflight hook"
    return 0
  fi

  if [ ! -d "$CLAUDE_DIR" ]; then
    warn "找不到 ~/.claude 目錄，跳過 preflight hook"
    return 0
  fi

  mkdir -p "$HOOKS_DIR"

  local hook_src="$SCRIPT_DIR/skills/openspec-preflight/openspec-preflight.js"
  local hook_dst="$HOOKS_DIR/openspec-preflight.js"

  # 複製 hook 腳本
  if [ -f "$hook_dst" ] && cmp -s "$hook_src" "$hook_dst" 2>/dev/null; then
    ok "openspec-preflight.js（已是最新）"
  else
    cp "$hook_src" "$hook_dst"
    ok "openspec-preflight.js → 已複製到 hooks/"
  fi

  # 檢查 settings.json 是否已設定
  if [ -f "$SETTINGS_FILE" ] && grep -q "openspec-preflight" "$SETTINGS_FILE" 2>/dev/null; then
    ok "settings.json 已包含 preflight hook 設定"
  else
    warn "請手動將 preflight hook 加入 ~/.claude/settings.json（參考 skills/openspec-preflight/SKILL.md）"
  fi
}

# ── 狀態檢查 ──────────────────────────────────────────────────────────────────

show_status() {
  header "OpenSpec Toolkit 安裝狀態"

  # Python
  if command -v python3 &>/dev/null; then
    ok "Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  else
    fail "Python 未安裝"
  fi

  # 依賴
  python3 -c "import jinja2" 2>/dev/null && ok "jinja2" || warn "jinja2 未安裝"
  python3 -c "import yaml"   2>/dev/null && ok "pyyaml" || warn "pyyaml 未安裝"

  # Skills
  local skills=("openspec-generator" "openspec-preflight" "openspec-brownfield-onboard")
  for skill in "${skills[@]}"; do
    if [ -L "$SKILLS_DIR/$skill" ]; then
      ok "Skill: $skill → $(readlink "$SKILLS_DIR/$skill")"
    else
      warn "Skill: $skill 未安裝"
    fi
  done

  # Hook
  if [ -f "$HOOKS_DIR/openspec-preflight.js" ]; then
    ok "Hook: openspec-preflight.js"
  else
    warn "Hook: openspec-preflight.js 未安裝"
  fi

  if [ -f "$SETTINGS_FILE" ] && grep -q "openspec-preflight" "$SETTINGS_FILE" 2>/dev/null; then
    ok "Hook: settings.json 已設定"
  else
    warn "Hook: settings.json 尚未設定"
  fi

  exit 0
}

# ── 移除 ──────────────────────────────────────────────────────────────────────

uninstall() {
  header "移除 OpenSpec Toolkit"

  local skills=("openspec-generator" "openspec-preflight" "openspec-brownfield-onboard")
  for skill in "${skills[@]}"; do
    local dst="$SKILLS_DIR/$skill"
    if [ -L "$dst" ]; then
      rm "$dst"
      ok "移除 Skill: $skill"
    fi
  done

  if [ -f "$HOOKS_DIR/openspec-preflight.js" ]; then
    rm "$HOOKS_DIR/openspec-preflight.js"
    ok "移除 Hook: openspec-preflight.js"
  fi

  warn "settings.json 中的 hook 設定請手動移除"
  info "Python 依賴 (jinja2, pyyaml) 未移除，如需移除請執行: pip uninstall jinja2 pyyaml"

  exit 0
}

# ── 啟動 Generator ────────────────────────────────────────────────────────────

run_generator() {
  activate_venv
  printf "\n${BOLD}${GREEN}🚀 啟動 OpenSpec Generator${NC}\n\n"
  exec python3 "$SCRIPT_DIR/create_repo.py" "$@"
}

# ── 主程式 ────────────────────────────────────────────────────────────────────

main() {
  # 無參數 → 完整流程（安裝 + 啟動）
  if [ $# -eq 0 ]; then
    check_env
    install_deps
    install_skills
    install_hook
    run_generator
    exit 0
  fi

  case "$1" in
    --help|-h)
      usage
      ;;
    --install)
      check_env
      install_deps
      install_skills
      install_hook
      printf "\n${GREEN}${BOLD}安裝完成！${NC} 執行 ${CYAN}./setup.sh --run${NC} 或 ${CYAN}python3 create_repo.py${NC} 啟動 Generator\n"
      ;;
    --run)
      shift
      run_generator "$@"
      ;;
    --uninstall)
      uninstall
      ;;
    --status)
      show_status
      ;;
    --brownfield)
      # Brownfield: 在當前目錄（pwd）注入 OpenSpec 框架
      check_env
      install_deps
      install_skills
      install_hook
      shift
      local proj_name
      proj_name=$(basename "$(pwd)")
      info "Brownfield 模式：在 $(pwd) 導入 OpenSpec 框架"
      run_generator --non-interactive --brownfield \
        --project-name "$proj_name" \
        --target-dir "$(pwd)" \
        "$@"
      ;;
    --add-change)
      # 追加 Change Package 到當前目錄的 OpenSpec 專案
      check_env
      install_deps
      shift
      if [ $# -eq 0 ]; then
        fail "請提供 Change 名稱，例如: ./setup.sh --add-change \"add-billing-export\""
      fi
      local change_name="$1"
      shift
      info "追加 Change Package: $change_name → $(pwd)"
      run_generator --add-change "$change_name" --target-dir "$(pwd)" "$@"
      ;;
    *)
      # 其他參數全部傳給 create_repo.py（如 --non-interactive）
      check_env
      install_deps
      install_skills
      install_hook
      run_generator "$@"
      ;;
  esac
}

main "$@"
