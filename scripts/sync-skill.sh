#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_NAME="${1:-}"

if [[ -z "$SKILL_NAME" || ! -f "$REPO_ROOT/$SKILL_NAME/SKILL.md" ]]; then
  echo "用法: $0 <skill-name>" >&2
  echo "可用 skills:" >&2
  find "$REPO_ROOT" -maxdepth 2 -name SKILL.md -not -path "*/node_modules/*" \
    | sed 's#/SKILL.md$##' | while read -r p; do basename "$p"; done | sort >&2
  exit 1
fi

SRC="$REPO_ROOT/$SKILL_NAME"
PROJECT_QODER="$(dirname "$REPO_ROOT")/.qoder/skills/$SKILL_NAME"
TARGETS=(
  "$PROJECT_QODER"
  "$HOME/.qoder/skills/$SKILL_NAME"
  "$HOME/.codex/skills/$SKILL_NAME"
  "$HOME/.claude/skills/$SKILL_NAME"
)

synced=0
for dest in "${TARGETS[@]}"; do
  if [[ -L "$dest" ]]; then
    echo "SKIP  $dest (软链接)"
    continue
  fi
  if [[ ! -d "$dest" ]]; then
    echo "SKIP  $dest (未安装)"
    continue
  fi
  rsync -a --delete "$SRC/" "$dest/"
  echo "SYNC  $dest"
  synced=$((synced + 1))
done

echo "完成: ${SKILL_NAME}，同步 ${synced} 个本地副本"
