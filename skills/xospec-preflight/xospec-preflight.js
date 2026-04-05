#!/usr/bin/env node
// =============================================================================
// xospec-preflight.js — PreToolUse Hook
//
// 攔截 Write/Edit 操作，確保 Agent 在修改程式碼前：
//   1. 專案有 xospec/ 結構（若無則跳過，不干擾非 x.ospec 專案）
//   2. 有 active change（.planning/STATE.md 或 xospec/changes/ 有進行中的 change）
//   3. 該 change 的 tasks.md 有未完成的任務
//   4. 不在 spec 範圍外亂改檔案（scope drift 警告）
//
// Hook 類型：PreToolUse（Write|Edit）
// 退出碼：0 = 放行，2 = 阻擋（附帶 stderr 訊息）
// =============================================================================

const fs = require('fs');
const path = require('path');

// ── 設定 ──────────────────────────────────────────────────────────────────────

// 不檢查的路徑 patterns（這些目錄本身就是 spec/docs，不需要 preflight）
const SKIP_PATTERNS = [
  /xospec\//,
  /\.planning\//,
  /\.xospec-map\.md/,
  /AGENTS\.md/,
  /CLAUDE\.md/,
  /README\.md/,
  /CHANGELOG/,
  /docs\//,
  /\.gitignore/,
  /package\.json/,
  /package-lock\.json/,
  /yarn\.lock/,
  /pnpm-lock\.yaml/,
  /requirements\.txt/,
  /pyproject\.toml/,
  /Cargo\.toml/,
  /go\.mod/,
  /go\.sum/,
  /\.env/,
  /tsconfig/,
  /\.eslint/,
  /\.prettier/,
  /\.vscode\//,
  /\.idea\//,
  /node_modules\//,
  /\.git\//,
  /test.*\.(js|ts|py|go|rs)$/,   // 測試檔案允許直接修改（TDD 流程需要）
  /spec.*\.(js|ts|py|go|rs)$/,
  /__tests__\//,
];

// ── 工具函式 ──────────────────────────────────────────────────────────────────

function findProjectRoot(startPath) {
  let dir = startPath;
  for (let i = 0; i < 10; i++) {
    if (fs.existsSync(path.join(dir, 'xospec'))) return dir;
    if (fs.existsSync(path.join(dir, '.git'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

function isx.ospecProject(root) {
  return fs.existsSync(path.join(root, 'xospec'));
}

function getActiveChange(root) {
  // 方法 1: 從 .planning/STATE.md 讀取
  const statePath = path.join(root, '.planning', 'STATE.md');
  if (fs.existsSync(statePath)) {
    const content = fs.readFileSync(statePath, 'utf8');
    const nameMatch = content.match(/\*\*Name:\*\*\s*(.+)/);
    const statusMatch = content.match(/\*\*Status:\*\*\s*(.+)/);
    if (nameMatch && statusMatch) {
      const status = statusMatch[1].trim().toLowerCase();
      if (status !== 'completed' && status !== 'done') {
        return nameMatch[1].trim();
      }
    }
  }

  // 方法 2: 掃描 xospec/changes/ 找有未完成 tasks 的 change
  const changesDir = path.join(root, 'xospec', 'changes');
  if (!fs.existsSync(changesDir)) return null;

  const changes = fs.readdirSync(changesDir, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  for (const change of changes) {
    const tasksPath = path.join(changesDir, change, 'tasks.md');
    if (fs.existsSync(tasksPath)) {
      const content = fs.readFileSync(tasksPath, 'utf8');
      const unchecked = (content.match(/- \[ \]/g) || []).length;
      if (unchecked > 0) return change;
    }
  }

  return null;
}

function getTaskStatus(root, changeId) {
  const tasksPath = path.join(root, 'xospec', 'changes', changeId, 'tasks.md');
  if (!fs.existsSync(tasksPath)) return { total: 0, done: 0, remaining: 0 };

  const content = fs.readFileSync(tasksPath, 'utf8');
  const checked = (content.match(/- \[x\]/gi) || []).length;
  const unchecked = (content.match(/- \[ \]/g) || []).length;
  return { total: checked + unchecked, done: checked, remaining: unchecked };
}

function shouldSkipFile(filePath) {
  return SKIP_PATTERNS.some(pattern => pattern.test(filePath));
}

// ── 主程式 ────────────────────────────────────────────────────────────────────

let input = '';
const timeout = setTimeout(() => process.exit(0), 3000);

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(timeout);

  let data;
  try {
    data = JSON.parse(input);
  } catch {
    process.exit(0); // 無法解析則放行
  }

  const toolName = data?.tool_name || '';
  const toolInput = data?.tool_input || {};

  // 只攔截 Write 和 Edit
  if (toolName !== 'Write' && toolName !== 'Edit') {
    process.exit(0);
  }

  const filePath = toolInput.file_path || toolInput.path || '';
  if (!filePath) {
    process.exit(0);
  }

  // 跳過不需要檢查的檔案
  if (shouldSkipFile(filePath)) {
    process.exit(0);
  }

  // 找專案根目錄
  const projectRoot = findProjectRoot(path.dirname(filePath));
  if (!projectRoot) {
    process.exit(0); // 不在任何專案中，放行
  }

  // 非 x.ospec 專案，放行
  if (!isx.ospecProject(projectRoot)) {
    process.exit(0);
  }

  // ── 檢查 1: 是否有 active change ──
  const activeChange = getActiveChange(projectRoot);
  if (!activeChange) {
    process.stderr.write(
      `\n⛔ x.ospec Preflight 攔截\n` +
      `   修改檔案: ${path.relative(projectRoot, filePath)}\n` +
      `   問題: 沒有進行中的 Change Package\n` +
      `   修正: 先在 xospec/changes/ 建立新的 Change Package\n` +
      `         （proposal.md → design.md → tasks.md），再開始寫程式碼\n`
    );
    process.exit(2);
  }

  // ── 檢查 2: tasks.md 是否有待辦任務 ──
  const taskStatus = getTaskStatus(projectRoot, activeChange);

  if (taskStatus.total === 0) {
    process.stderr.write(
      `\n⚠️  x.ospec Preflight 警告\n` +
      `   Active change: ${activeChange}\n` +
      `   問題: tasks.md 是空的或不存在\n` +
      `   建議: 先在 xospec/changes/${activeChange}/tasks.md 列出任務清單\n`
    );
    // 警告但不阻擋（可能正在初始設定）
    process.exit(0);
  }

  if (taskStatus.remaining === 0) {
    process.stderr.write(
      `\n⚠️  x.ospec Preflight 警告\n` +
      `   Active change: ${activeChange}\n` +
      `   問題: tasks.md 的所有任務已完成 (${taskStatus.done}/${taskStatus.total})\n` +
      `   你正在修改計畫外的程式碼。如果這是新需求，請建立新的 Change Package。\n`
    );
    // 警告但不阻擋
    process.exit(0);
  }

  // ── 通過：顯示進度 ──
  process.stderr.write(
    `✅ x.ospec: ${activeChange} [${taskStatus.done}/${taskStatus.total}]\n`
  );
  process.exit(0);
});
