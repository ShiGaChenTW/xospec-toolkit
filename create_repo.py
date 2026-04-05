"""OpenSpec Toolkit — Jinja2 templates, CLI mode, git init, full workflow."""

from pathlib import Path
import argparse
import curses
from datetime import date
import os
import re
import subprocess
import sys
import textwrap

import yaml
from jinja2 import Environment, FileSystemLoader

# ── Constants ────────────────────────────────────────────────────────────────

TEMPLATES_DIR = Path(__file__).parent / "templates"
CONFIG_FILE = ".openspec-generator.yml"

MIN_SCREEN_WIDTH = 110
FORM_TOP_ROW = 5
ROW_HEIGHT_PER_QUESTION = 4
FORM_BOTTOM_RESERVED_ROWS = 3

PAIR_TITLE = 1
PAIR_SUBTITLE = 2
PAIR_ACTIVE_LABEL = 3
PAIR_ACTIVE_INPUT = 4
PAIR_INACTIVE_LABEL = 5
PAIR_HINT = 6
PAIR_STATUS_OK = 7
PAIR_STATUS_WARN = 8
PAIR_CURSOR_LINE = 9
PAIR_REQUIRED = 10

QUESTIONS = [
    ("project_name", "Project name*", "專案名稱（例如：My Billing Service）*", True, "my-project"),
    ("target_dir", "Target directory", "專案根目錄資料夾（相對或絕對路徑；留空使用專案名稱轉成的 slug）", False, None),
    ("capabilities", "Capabilities (comma separated)*", "系統的 capabilities，以逗號分隔*", True, "auth, billing"),
    ("first_change_name", "First feature / change name*", "第一個 feature / change 名稱*", True, None),
    ("first_change_capability", "Which capability does this first change belong to?*", "這個第一個 change 主要屬於哪個 capability？*", True, None),
    ("user_problem", "Main user problem*", "這個專案想解決的主要使用者問題是什麼？*", True, "Users cannot complete the core task efficiently"),
    ("target_user", "Main target user*", "主要目標使用者是誰？*", True, "End users"),
    ("feature_why", "Why is this first feature needed?", "為什麼需要先做這個第一個 feature？", False, "It delivers the first meaningful user value"),
    ("overwrite", "Overwrite existing files?", "若目標路徑已有同名檔案，是否覆寫？（yes / no）", False, "no"),
    ("enable_superpowers", "Enable Superpowers integration?", "是否加入 Superpowers 工程紀律整合？（yes / no）", False, "yes"),
    ("git_init", "Run git init after generation?", "生成後自動執行 git init + 初始 commit？（yes / no）", False, "yes"),
]

MIN_SCREEN_HEIGHT = FORM_TOP_ROW + (len(QUESTIONS) * ROW_HEIGHT_PER_QUESTION) + FORM_BOTTOM_RESERVED_ROWS


# ── Utility ──────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "item"


def parse_capabilities(raw_caps: str) -> list[str]:
    capabilities = [slugify(x) for x in raw_caps.split(",") if x.strip()]
    return capabilities or ["core"]


def validate_path(path_str: str) -> tuple[bool, str]:
    """Validate target directory path."""
    if not path_str.strip():
        return True, ""
    expanded = Path(path_str).expanduser()
    invalid_chars = set('<>"|?*') if sys.platform == "win32" else set('\0')
    if any(c in str(expanded) for c in invalid_chars):
        return False, f"路徑包含不合法字元: {invalid_chars}"
    if expanded.exists() and (expanded / ".git").exists():
        return True, "warning: 目標路徑已有 git repo"
    return True, ""


# ── Defaults & Validation ────────────────────────────────────────────────────

def build_default_values(config: dict | None = None) -> dict[str, str]:
    values: dict[str, str] = {}
    for qid, _, _, _, default in QUESTIONS:
        if config and qid in config:
            values[qid] = str(config[qid])
        else:
            values[qid] = "" if default is None else str(default)
    values["target_dir"] = slugify(values["project_name"])
    capabilities = parse_capabilities(values["capabilities"])
    values["first_change_name"] = values["first_change_name"] or f"add-{capabilities[0]}"
    values["first_change_capability"] = values["first_change_capability"] or capabilities[0]
    return values


def refresh_derived_defaults(values: dict[str, str], touched: dict[str, bool]) -> None:
    if not touched["target_dir"]:
        values["target_dir"] = slugify(values["project_name"])
    capabilities = parse_capabilities(values["capabilities"])
    if not touched["first_change_name"]:
        values["first_change_name"] = f"add-{capabilities[0]}"
    if not touched["first_change_capability"]:
        values["first_change_capability"] = capabilities[0]


def validate_answers(values: dict[str, str]) -> tuple[bool, str]:
    for qid, label_en, _, required, _ in QUESTIONS:
        raw_value = values.get(qid, "").strip()
        if required and not raw_value:
            return False, f"{label_en} 尚未填寫"
    overwrite_value = values["overwrite"].strip().lower()
    if overwrite_value not in {"yes", "no", "y", "n"}:
        return False, "Overwrite existing files? 只能輸入 yes / no"
    path_ok, path_msg = validate_path(values["target_dir"])
    if not path_ok:
        return False, path_msg
    return True, "全部已回答完成"


def normalize_answers(values: dict[str, str]) -> dict[str, str]:
    normalized = {key: value.strip() for key, value in values.items()}
    normalized["target_dir"] = normalized["target_dir"] or slugify(normalized["project_name"])
    capabilities = parse_capabilities(normalized["capabilities"])
    normalized["capabilities"] = ", ".join(capabilities)
    if not normalized["first_change_name"]:
        normalized["first_change_name"] = f"add-{capabilities[0]}"
    if not normalized["first_change_capability"]:
        normalized["first_change_capability"] = capabilities[0]
    for key in ("overwrite", "enable_superpowers", "git_init"):
        normalized[key] = "yes" if normalized.get(key, "").lower() in {"yes", "y"} else "no"
    return normalized


# ── Config file ──────────────────────────────────────────────────────────────

def load_config() -> dict | None:
    """Load defaults from .openspec-generator.yml if it exists."""
    config_path = Path.cwd() / CONFIG_FILE
    if not config_path.exists():
        config_path = Path.home() / CONFIG_FILE
    if not config_path.exists():
        return None
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ── TUI ──────────────────────────────────────────────────────────────────────

def init_theme() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(PAIR_TITLE, curses.COLOR_CYAN, -1)
    curses.init_pair(PAIR_SUBTITLE, curses.COLOR_MAGENTA, -1)
    curses.init_pair(PAIR_ACTIVE_LABEL, curses.COLOR_YELLOW, -1)
    curses.init_pair(PAIR_ACTIVE_INPUT, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(PAIR_INACTIVE_LABEL, curses.COLOR_WHITE, -1)
    curses.init_pair(PAIR_HINT, curses.COLOR_BLUE, -1)
    curses.init_pair(PAIR_STATUS_OK, curses.COLOR_GREEN, -1)
    curses.init_pair(PAIR_STATUS_WARN, curses.COLOR_MAGENTA, -1)
    curses.init_pair(PAIR_CURSOR_LINE, curses.COLOR_CYAN, -1)
    curses.init_pair(PAIR_REQUIRED, curses.COLOR_RED, -1)


def safe_addstr(stdscr: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    available_width = width - x
    if available_width <= 0:
        return
    try:
        stdscr.addstr(y, x, text[:available_width], attr)
    except curses.error:
        return


def safe_hline(stdscr: curses.window, y: int, x: int, ch: int, count: int, attr: int = 0) -> None:
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    if x < 0:
        count += x
        x = 0
    count = min(count, width - x)
    if count <= 0:
        return
    try:
        stdscr.hline(y, x, ch, count, attr)
    except curses.error:
        return


def draw_size_warning(stdscr: curses.window) -> None:
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    stdscr.bkgd(" ", curses.color_pair(PAIR_INACTIVE_LABEL))
    safe_addstr(stdscr, 2, 2, "OpenSpec Toolkit / Fullscreen", curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_hline(stdscr, 3, 2, ord("="), max(10, width - 4), curses.color_pair(PAIR_CURSOR_LINE))
    safe_addstr(stdscr, 6, 2, "畫面尺寸不足，請先放大 terminal 視窗。", curses.color_pair(PAIR_STATUS_WARN) | curses.A_BOLD)
    safe_addstr(stdscr, 8, 2, f"需要至少: {MIN_SCREEN_WIDTH} x {MIN_SCREEN_HEIGHT}", curses.color_pair(PAIR_ACTIVE_LABEL))
    safe_addstr(stdscr, 9, 2, f"目前尺寸: {width} x {height}", curses.color_pair(PAIR_INACTIVE_LABEL))
    safe_addstr(stdscr, 11, 2, "調整完成後畫面會自動繼續。按 Esc 可離開。", curses.color_pair(PAIR_SUBTITLE) | curses.A_BOLD)
    try:
        stdscr.refresh()
    except curses.error:
        return


def draw_form(stdscr: curses.window, current_index: int, values: dict[str, str], status: str) -> tuple[int, int]:
    stdscr.erase()
    stdscr.bkgd(" ", curses.color_pair(PAIR_INACTIVE_LABEL))
    height, width = stdscr.getmaxyx()
    content_x = 4
    content_width = max(20, width - (content_x * 2))
    input_inner_width = max(18, content_width - 4)

    title = "OpenSpec Toolkit / Fullscreen"
    subtitle = "Enter 逐題跳到下一題，方向鍵可移動，F2 送出，Esc 離開"
    safe_addstr(stdscr, 1, 2, title[: width - 4], curses.color_pair(PAIR_TITLE) | curses.A_BOLD)
    safe_addstr(stdscr, 2, 2, subtitle[: width - 4], curses.color_pair(PAIR_SUBTITLE) | curses.A_BOLD)
    safe_hline(stdscr, 3, 2, ord("="), max(10, width - 4), curses.color_pair(PAIR_CURSOR_LINE))

    row = FORM_TOP_ROW
    for index, (_, label_en, label_zh, required, _) in enumerate(QUESTIONS):
        prefix = ">" if index == current_index else " "
        label_attr = curses.color_pair(PAIR_ACTIVE_LABEL) | curses.A_BOLD if index == current_index else curses.color_pair(PAIR_INACTIVE_LABEL)
        input_attr = curses.color_pair(PAIR_ACTIVE_INPUT) | curses.A_BOLD if index == current_index else curses.color_pair(PAIR_HINT)
        label_text = f"{prefix} {index + 1}. {label_en.rstrip('*')}"
        safe_addstr(stdscr, row, content_x, label_text[:content_width], label_attr)
        if required and content_x + len(label_text) < content_x + content_width:
            safe_addstr(stdscr, row, content_x + len(label_text), "*", curses.color_pair(PAIR_REQUIRED) | curses.A_BOLD)

        input_value = values[QUESTIONS[index][0]]
        display_value = input_value[: max(1, input_inner_width - 3)]
        clean_label_zh = label_zh[:-1] if label_zh.endswith("*") else label_zh
        wrapped = textwrap.wrap(clean_label_zh, width=max(20, content_width - 2)) or [""]
        for offset, line in enumerate(wrapped[:1], start=1):
            hint_attr = curses.color_pair(PAIR_SUBTITLE) if index == current_index else curses.color_pair(PAIR_HINT)
            safe_addstr(stdscr, row + offset, content_x + 2, line[: content_width - 2], hint_attr)

        if index == current_index:
            safe_addstr(stdscr, row + 2, content_x, "=", input_attr)
            safe_addstr(stdscr, row + 2, content_x + 1, " " * input_inner_width, input_attr)
            safe_addstr(stdscr, row + 2, content_x + 3, display_value, input_attr | curses.A_BOLD)
            safe_addstr(stdscr, row + 2, content_x + 1 + input_inner_width, ">", input_attr)
        else:
            safe_addstr(stdscr, row + 2, content_x, "<", curses.color_pair(PAIR_HINT))
            safe_addstr(stdscr, row + 2, content_x + 1, " " * input_inner_width, curses.color_pair(PAIR_INACTIVE_LABEL))
            safe_addstr(stdscr, row + 2, content_x + 3, display_value, curses.color_pair(PAIR_INACTIVE_LABEL))
            safe_addstr(stdscr, row + 2, content_x + 1 + input_inner_width, ">", curses.color_pair(PAIR_HINT))
        row += ROW_HEIGHT_PER_QUESTION

    valid, valid_message = validate_answers(values)
    final_status = status or valid_message
    status_attr = curses.color_pair(PAIR_STATUS_OK) | curses.A_BOLD if valid else curses.color_pair(PAIR_STATUS_WARN) | curses.A_BOLD
    safe_hline(stdscr, height - 3, 2, ord("="), max(10, width - 4), curses.color_pair(PAIR_CURSOR_LINE))
    safe_addstr(stdscr, height - 2, 2, " " * max(10, width - 4), status_attr)
    safe_addstr(stdscr, height - 2, 2, final_status[: width - 4], status_attr)
    if valid:
        safe_addstr(stdscr, height - 1, 2, "按 F2 產生檔案", curses.color_pair(PAIR_STATUS_OK) | curses.A_BOLD)
    else:
        safe_addstr(stdscr, height - 1, 2, "請完成全部必填欄位後再送出", curses.color_pair(PAIR_SUBTITLE) | curses.A_BOLD)

    cursor_x = content_x + 3 + min(len(values[QUESTIONS[current_index][0]]), max(1, input_inner_width - 3))
    cursor_y = FORM_TOP_ROW + current_index * ROW_HEIGHT_PER_QUESTION + 2
    try:
        stdscr.move(cursor_y, cursor_x)
        stdscr.refresh()
    except curses.error:
        pass
    return input_inner_width, height


def run_form(stdscr: curses.window, config: dict | None = None) -> dict[str, str] | None:
    init_theme()
    curses.curs_set(1)
    stdscr.keypad(True)

    values = build_default_values(config)
    touched = {qid: False for qid, _, _, _, _ in QUESTIONS}
    current_index = 0
    status = ""

    while True:
        height, width = stdscr.getmaxyx()
        if width < MIN_SCREEN_WIDTH or height < MIN_SCREEN_HEIGHT:
            draw_size_warning(stdscr)
            key = stdscr.getch()
            if key == 27:
                return None
            continue

        refresh_derived_defaults(values, touched)
        input_width, _ = draw_form(stdscr, current_index, values, status)
        qid = QUESTIONS[current_index][0]
        key = stdscr.getch()

        if key == 27:
            return None
        if key == curses.KEY_F2:
            valid, valid_message = validate_answers(values)
            status = valid_message
            if valid:
                return normalize_answers(values)
            continue
        if key in {curses.KEY_UP, curses.KEY_BTAB}:
            current_index = max(0, current_index - 1)
            status = ""
            continue
        if key in {curses.KEY_DOWN, 9}:
            current_index = min(len(QUESTIONS) - 1, current_index + 1)
            status = ""
            continue
        if key in {10, 13, curses.KEY_ENTER}:
            touched[qid] = True
            if current_index < len(QUESTIONS) - 1:
                current_index += 1
                status = ""
                continue
            valid, valid_message = validate_answers(values)
            status = valid_message
            if valid:
                return normalize_answers(values)
            continue
        if key in {curses.KEY_BACKSPACE, 127, 8}:
            values[qid] = values[qid][:-1]
            touched[qid] = True
            status = ""
            continue
        if key == curses.KEY_RESIZE:
            status = ""
            continue
        if 32 <= key <= 126:
            if len(values[qid]) < max(1, input_width - 1):
                values[qid] += chr(key)
                touched[qid] = True
                status = ""


# ── Generation ───────────────────────────────────────────────────────────────

def write_file(path: Path, content: str, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        print(f"  skip  {path}")
        return
    path.write_text(content, encoding="utf-8")
    print(f"  write {path}")


def add_change(target_dir: str, change_name: str, capability: str | None,
               feature_why: str | None) -> Path:
    """Add a new Change Package to an existing OpenSpec repo."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    repo_root = Path(target_dir).expanduser()
    openspec_dir = repo_root / "openspec"

    if not openspec_dir.exists():
        print(f"錯誤：{openspec_dir} 不存在。請先導入 OpenSpec 框架（--brownfield）或建立新專案。")
        sys.exit(1)

    change_id = slugify(change_name)
    # Infer capability from change name if not provided (e.g., "add-billing-pdf" → "billing")
    if not capability:
        parts = change_id.split("-")
        capability = parts[1] if len(parts) > 1 else parts[0]
    capability = slugify(capability)

    changes_dir = openspec_dir / "changes" / change_id

    if changes_dir.exists():
        print(f"錯誤：{changes_dir} 已存在。")
        sys.exit(1)

    ctx = {
        "project_name": repo_root.name,
        "change_id": change_id,
        "first_change_capability": capability,
        "capabilities": [capability],
        "target_user": "End users",
        "user_problem": "",
        "feature_why": feature_why or "Delivers the next meaningful user value",
        "enable_superpowers": (repo_root / ".planning").exists(),
        "today": date.today().isoformat(),
    }

    print(f"\n新增 Change Package: {change_id}\n")

    write_file(changes_dir / "proposal.md", env.get_template("proposal.md.j2").render(ctx), False)
    write_file(changes_dir / "design.md", env.get_template("design.md.j2").render(ctx), False)
    write_file(changes_dir / "tasks.md", env.get_template("tasks.md.j2").render(ctx), False)
    write_file(changes_dir / "spec_delta.md", env.get_template("spec_delta.md.j2").render(ctx), False)

    # Ensure capability spec exists
    cap_spec = openspec_dir / "specs" / capability / "spec.md"
    if not cap_spec.exists():
        write_file(cap_spec, env.get_template("spec.md.j2").render(capability=capability, **ctx), False)

    # Update .openspec-map.md if it exists
    map_path = repo_root / ".openspec-map.md"
    if map_path.exists():
        map_content = map_path.read_text(encoding="utf-8")
        if change_id not in map_content:
            entry = f"| {change_id} | {capability} | In Progress | {date.today().isoformat()} |\n"
            map_content = map_content.rstrip() + "\n" + entry
            map_path.write_text(map_content, encoding="utf-8")
            print(f"  update {map_path}")

    # Update .planning/STATE.md if GSD is enabled
    state_path = repo_root / ".planning" / "STATE.md"
    if state_path.exists():
        state_content = state_path.read_text(encoding="utf-8")
        updated = state_content.replace(
            "**Status:** not-started",
            "**Status:** not-started",  # Keep existing status
        )
        # Update current phase name if it's still the old one
        if f"**Name:** {change_id}" not in state_content:
            new_state = (
                f"# Project State — {repo_root.name}\n\n"
                f"## Current Phase\n"
                f"- **Phase:** {change_id}\n"
                f"- **Name:** {change_id}\n"
                f"- **Status:** not-started\n\n"
                f"## Decisions\n"
                f"<!-- Record key decisions here as they happen -->\n\n"
                f"## Blockers\n"
                f"<!-- Track blockers that need resolution -->\n"
            )
            state_path.write_text(new_state, encoding="utf-8")
            print(f"  update {state_path}")

    return changes_dir


def generate_repo(answers: dict[str, str], brownfield: bool = False) -> Path:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )

    project_name = answers["project_name"]
    target_dir = Path(answers["target_dir"]).expanduser()
    capabilities = [slugify(x) for x in answers["capabilities"].split(",") if x.strip()] or ["core"]
    change_id = slugify(answers["first_change_name"])
    first_change_capability = slugify(answers["first_change_capability"])
    if first_change_capability not in capabilities:
        capabilities.append(first_change_capability)

    overwrite = answers["overwrite"] == "yes"
    enable_superpowers = answers.get("enable_superpowers", "no") == "yes"
    do_git_init = answers.get("git_init", "no") == "yes"

    ctx = {
        "project_name": project_name,
        "target_user": answers["target_user"],
        "user_problem": answers["user_problem"],
        "feature_why": answers["feature_why"],
        "capabilities": capabilities,
        "change_id": change_id,
        "first_change_capability": first_change_capability,
        "enable_superpowers": enable_superpowers,
        "today": date.today().isoformat(),
    }

    repo_root = target_dir
    openspec_dir = repo_root / "openspec"
    changes_dir = openspec_dir / "changes" / change_id

    mode_label = "Brownfield 導入" if brownfield else "生成 repo"
    print(f"\n{mode_label}: {repo_root}\n")

    # Core files (skip in brownfield — don't overwrite existing project files)
    if not brownfield:
        write_file(repo_root / "README.md", env.get_template("readme.md.j2").render(ctx), overwrite)
        write_file(repo_root / ".gitignore", env.get_template("gitignore.j2").render(ctx), overwrite)
    write_file(openspec_dir / "README.md", env.get_template("openspec_readme.md.j2").render(ctx), overwrite)

    # Capability specs
    for cap in capabilities:
        write_file(
            openspec_dir / "specs" / cap / "spec.md",
            env.get_template("spec.md.j2").render(capability=cap, **ctx),
            overwrite,
        )

    # Change artifacts
    write_file(changes_dir / "proposal.md", env.get_template("proposal.md.j2").render(ctx), overwrite)
    write_file(changes_dir / "design.md", env.get_template("design.md.j2").render(ctx), overwrite)
    write_file(changes_dir / "tasks.md", env.get_template("tasks.md.j2").render(ctx), overwrite)
    write_file(
        changes_dir / "spec_delta.md",
        env.get_template("spec_delta.md.j2").render(ctx),
        overwrite,
    )

    # AGENTS.md (#4)
    write_file(repo_root / "AGENTS.md", env.get_template("agents.md.j2").render(ctx), overwrite)

    # .openspec-map.md — 空間索引
    write_file(repo_root / ".openspec-map.md", env.get_template("openspec_map.md.j2").render(ctx), overwrite)

    # engineering-principles.md (#5)
    write_file(
        repo_root / "docs" / "engineering-principles.md",
        env.get_template("engineering_principles.md.j2").render(ctx),
        overwrite,
    )

    # Superpowers + GSD integration (#6)
    if enable_superpowers:
        write_file(
            repo_root / "docs" / "superpowers.md",
            env.get_template("superpowers.md.j2").render(ctx),
            overwrite,
        )

        # GSD .planning/ scaffold
        planning_dir = repo_root / ".planning"
        write_file(
            planning_dir / "PROJECT.md",
            env.get_template("gsd_project.md.j2").render(ctx),
            overwrite,
        )
        write_file(
            planning_dir / "ROADMAP.md",
            env.get_template("gsd_roadmap.md.j2").render(ctx),
            overwrite,
        )
        write_file(
            planning_dir / "STATE.md",
            env.get_template("gsd_state.md.j2").render(ctx),
            overwrite,
        )

    # Git (#3)
    if do_git_init:
        if brownfield:
            # Brownfield: repo already has git, just commit the new files
            print("\n提交 OpenSpec 框架檔案...")
            subprocess.run(["git", "add", "openspec/", ".openspec-map.md", "AGENTS.md",
                            "docs/"], cwd=str(repo_root), check=True, capture_output=True)
            if enable_superpowers:
                subprocess.run(["git", "add", ".planning/"], cwd=str(repo_root),
                               check=True, capture_output=True)
            result = subprocess.run(
                ["git", "commit", "-m", "chore: bootstrap OpenSpec framework (brownfield onboard)"],
                cwd=str(repo_root), capture_output=True, text=True,
            )
            if result.returncode == 0:
                print("  git commit 完成")
            else:
                err = result.stderr.strip()
                print(f"  ⚠ git commit 失敗：{err}")
                print(f"  檔案已生成，請在 {repo_root} 手動 git commit")
        else:
            print("\n初始化 git repo...")
            subprocess.run(["git", "init"], cwd=str(repo_root), check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=str(repo_root), check=True, capture_output=True)
            result = subprocess.run(
                ["git", "commit", "-m", "chore: bootstrap OpenSpec repo structure"],
                cwd=str(repo_root), capture_output=True, text=True,
            )
            if result.returncode == 0:
                print("  git init + initial commit 完成")
            else:
                err = result.stderr.strip()
                print(f"  ⚠ git commit 失敗：{err}")
                print("  可能原因：未設定 git user，請執行：")
                print("    git config --global user.name \"Your Name\"")
                print("    git config --global user.email \"you@example.com\"")
                print(f"  然後在 {repo_root} 手動執行 git commit")

    return repo_root


# ── CLI mode (#2) ────────────────────────────────────────────────────────────

def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenSpec Toolkit — 互動式或 CLI 模式建立 repo 骨架",
    )
    parser.add_argument("--project-name", help="專案名稱")
    parser.add_argument("--target-dir", help="輸出路徑")
    parser.add_argument("--capabilities", help="Capabilities，逗號分隔")
    parser.add_argument("--first-change-name", help="第一個 change 名稱")
    parser.add_argument("--first-change-capability", help="第一個 change 的 capability")
    parser.add_argument("--user-problem", help="主要使用者問題")
    parser.add_argument("--target-user", help="目標使用者")
    parser.add_argument("--feature-why", help="為什麼先做這個 feature")
    parser.add_argument("--overwrite", choices=["yes", "no"], default="no")
    parser.add_argument("--enable-superpowers", choices=["yes", "no"], default="yes")
    parser.add_argument("--git-init", choices=["yes", "no"], default="yes")
    parser.add_argument("--non-interactive", action="store_true", help="跳過 TUI，直接用 CLI 參數生成")
    parser.add_argument("--brownfield", action="store_true",
                        help="Brownfield 模式：不生成 README/.gitignore，只建立 openspec 框架檔案")
    parser.add_argument("--add-change", metavar="CHANGE_NAME",
                        help="在既有 openspec repo 中新增一個 Change Package")
    return parser.parse_args()


def cli_to_values(args: argparse.Namespace) -> dict[str, str]:
    """Convert CLI args to the same dict format as the TUI."""
    config = load_config() or {}
    values = build_default_values(config)

    cli_map = {
        "project_name": args.project_name,
        "target_dir": args.target_dir,
        "capabilities": args.capabilities,
        "first_change_name": args.first_change_name,
        "first_change_capability": args.first_change_capability,
        "user_problem": args.user_problem,
        "target_user": args.target_user,
        "feature_why": args.feature_why,
        "overwrite": args.overwrite,
        "enable_superpowers": args.enable_superpowers,
        "git_init": args.git_init,
    }
    for key, val in cli_map.items():
        if val is not None:
            values[key] = val

    return normalize_answers(values)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_cli_args()

    # ── Mode: --add-change ──
    if args.add_change:
        target = args.target_dir or "."
        result = add_change(
            target_dir=target,
            change_name=args.add_change,
            capability=args.first_change_capability,
            feature_why=args.feature_why,
        )
        print(f"\n全部完成！Change Package created at: {result}")
        if sys.stdin.isatty():
            post_generate_prompt(Path(target))
        return

    # ── Mode: --non-interactive (greenfield or brownfield) ──
    if args.non_interactive:
        if not args.project_name:
            print("錯誤：--non-interactive 模式必須提供 --project-name")
            sys.exit(1)
        answers = cli_to_values(args)
        # Warn about required fields using default values
        cli_provided = {
            "project_name": args.project_name, "capabilities": args.capabilities,
            "first_change_name": args.first_change_name,
            "first_change_capability": args.first_change_capability,
            "user_problem": args.user_problem, "target_user": args.target_user,
        }
        defaulted = [k for k, v in cli_provided.items() if v is None]
        if defaulted:
            print(f"⚠ 以下必填參數未提供，使用預設值：{', '.join('--' + k.replace('_', '-') for k in defaulted)}")
        valid, msg = validate_answers(answers)
        if not valid:
            print(f"驗證失敗：{msg}")
            sys.exit(1)
    else:
        config = load_config()
        answers = curses.wrapper(run_form, config)
        if answers is None:
            print("Cancelled.")
            return

    repo_root = generate_repo(answers, brownfield=args.brownfield)
    mode = "Brownfield 導入" if args.brownfield else "Repo created"
    print(f"\n全部完成！{mode} at: {repo_root}")

    post_generate_prompt(repo_root)


def check_skills_installed() -> dict[str, bool]:
    """Check which OpenSpec skills are installed in ~/.claude/skills/."""
    skills_dir = Path.home() / ".claude" / "skills"
    skills = {
        "openspec-generator": False,
        "openspec-preflight": False,
        "openspec-brownfield-onboard": False,
    }
    for name in skills:
        skill_path = skills_dir / name
        if skill_path.exists() or skill_path.is_symlink():
            skills[name] = True
    return skills


def find_toolkit_skills_dir() -> Path | None:
    """Find the skills/ directory relative to this script."""
    skills_dir = Path(__file__).parent / "skills"
    if skills_dir.is_dir():
        return skills_dir
    return None


def install_skills_interactive() -> None:
    """Guide user through skill installation."""
    claude_dir = Path.home() / ".claude"
    if not claude_dir.is_dir():
        print("  找不到 ~/.claude/ 目錄，請先安裝 Claude Code")
        return

    skills_src = find_toolkit_skills_dir()
    if not skills_src:
        print("  找不到 skills/ 目錄")
        return

    skills_dir = claude_dir / "skills"
    skills_dir.mkdir(exist_ok=True)

    skill_names = ["openspec-generator", "openspec-preflight", "openspec-brownfield-onboard"]
    installed_count = 0

    for name in skill_names:
        src = skills_src / name
        dst = skills_dir / name
        if dst.exists() or dst.is_symlink():
            print(f"  ✔ {name}（已安裝）")
            installed_count += 1
        elif src.is_dir():
            dst.symlink_to(src)
            print(f"  ✔ {name} → 已建立 symlink")
            installed_count += 1
        else:
            print(f"  ✖ {name} — 來源不存在")

    # Preflight hook
    hook_src = skills_src / "openspec-preflight" / "openspec-preflight.js"
    hooks_dir = claude_dir / "hooks"
    if hook_src.is_file():
        hooks_dir.mkdir(exist_ok=True)
        hook_dst = hooks_dir / "openspec-preflight.js"
        if not hook_dst.exists():
            import shutil
            shutil.copy2(str(hook_src), str(hook_dst))
            print(f"  ✔ preflight hook → 已複製到 ~/.claude/hooks/")
        else:
            print(f"  ✔ preflight hook（已安裝）")
        # Check settings.json
        settings_file = claude_dir / "settings.json"
        if settings_file.is_file() and "openspec-preflight" in settings_file.read_text():
            print(f"  ✔ settings.json 已設定 hook")
        else:
            print(f"  ⚠ 請手動將 preflight hook 加入 ~/.claude/settings.json")
            print(f"    參考：skills/openspec-preflight/SKILL.md")

    print(f"\n  已安裝 {installed_count}/{len(skill_names)} 個 Skills")


def post_generate_prompt(repo_root: Path) -> None:
    """Ask user what to do next: install skills, open in IDE, or stay in terminal."""

    # Check skill status
    skills_status = check_skills_installed()
    all_installed = all(skills_status.values())

    print("\n" + "─" * 50)
    print("下一步？\n")

    if not all_installed:
        missing = [name for name, ok in skills_status.items() if not ok]
        print(f"  ⚠ 偵測到 {len(missing)} 個 Claude Code Skill 尚未安裝：")
        for name in missing:
            print(f"    • {name}")
        print()

    print("  1) 安裝 Claude Code Skills（AI 開發輔助）")
    print("  2) 用 VS Code 開啟專案")
    print("  3) 用 Cursor 開啟專案")
    print("  4) 進入專案目錄（Terminal）")
    print("  5) 結束")
    print()

    if not all_installed:
        default = "1"
        prompt_text = "請選擇 [1/2/3/4/5]（預設 1）："
    else:
        default = "4"
        prompt_text = "請選擇 [1/2/3/4/5]（預設 4）："

    try:
        choice = input(prompt_text).strip() or default
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if choice == "1":
        print("\n安裝 Claude Code Skills...\n")
        install_skills_interactive()
        print("\n" + "─" * 50)
        print("\n接下來？\n")
        print("  2) 用 VS Code 開啟專案")
        print("  3) 用 Cursor 開啟專案")
        print("  4) 進入專案目錄（Terminal）")
        print("  5) 結束")
        print()
        try:
            choice = input("請選擇 [2/3/4/5]（預設 4）：").strip() or "4"
        except (EOFError, KeyboardInterrupt):
            print()
            return

    if choice == "2":
        print(f"\n開啟 VS Code → {repo_root}")
        subprocess.run(["code", str(repo_root)])
    elif choice == "3":
        print(f"\n開啟 Cursor → {repo_root}")
        subprocess.run(["cursor", str(repo_root)])
    elif choice == "4":
        print(f"\n請執行以下指令進入專案目錄：")
        print(f"  cd {repo_root}")
    elif choice == "5":
        print("\n再見！")
    else:
        print(f"\n請執行以下指令進入專案目錄：")
        print(f"  cd {repo_root}")


if __name__ == "__main__":
    main()
