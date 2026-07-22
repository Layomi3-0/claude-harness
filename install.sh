#!/usr/bin/env bash
#
# install.sh — drop the clean-code harness into a project (default) or your
# user-global Claude config. Copies agents, commands, and standards, fills in
# placeholders from harness.config, and (project mode) hides the harness from
# the target repo via .git/info/exclude so it never reaches the remote.
#
# Usage:
#   ./install.sh                      # install into ./.claude (current repo)
#   ./install.sh --project <path>     # install into <path>/.claude
#   ./install.sh --global             # install into ~/.claude
#   ./install.sh --config <file>      # use a specific config (default: ./harness.config)
#   ./install.sh --with-adw           # also install the ADW runner (.claude/adw)
#
set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="project"
TARGET_REPO="$PWD"
CONFIG="$HARNESS_DIR/harness.config"
WITH_ADW="no"

while [ $# -gt 0 ]; do
  case "$1" in
    --global)   MODE="global"; shift ;;
    --project)  MODE="project"; TARGET_REPO="${2:?--project needs a path}"; shift 2 ;;
    --config)   CONFIG="${2:?--config needs a file}"; shift 2 ;;
    --with-adw) WITH_ADW="yes"; shift ;;
    -h|--help)  sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ── Build a sed script from config (KEY=value lines) ──
# Portable to bash 3.2 (macOS) — no associative arrays.
SED_SCRIPT="$(mktemp)"
trap 'rm -f "$SED_SCRIPT"' EXIT

if [ -f "$CONFIG" ]; then
  while IFS='=' read -r key value; do
    case "$key" in ''|'#'*) continue ;; esac
    key="$(echo "$key" | xargs)"                 # trim whitespace
    value="${value%$'\r'}"                        # strip CR if present
    value="$(printf '%s' "$value" | sed -e 's/[\\&|]/\\&/g')"  # escape for sed RHS
    printf 's|{{%s}}|%s|g\n' "$key" "$value" >> "$SED_SCRIPT"
  done < "$CONFIG"
else
  echo "⚠️  No config at $CONFIG — placeholders will keep their defaults." >&2
fi

substitute() {
  # Replace every configured {{KEY}} in $1.
  #
  # LC_ALL=C makes sed treat the file as bytes. Without it, BSD sed aborts with
  # "RE error: illegal byte sequence" on any file holding multi-byte characters
  # under a non-UTF-8 locale — which is every ADW script, since they print emoji.
  # Byte-wise substitution is safe here because the {{KEY}} patterns are ASCII.
  LC_ALL=C sed -i.bak -f "$SED_SCRIPT" "$1" && rm -f "$1.bak"
}

copy_tree() {
  # copy_tree <src-subdir> <dest-dir>; substitutes placeholders in every file.
  local src="$HARNESS_DIR/core/$1" dest="$2"
  mkdir -p "$dest"
  cp -R "$src/." "$dest/"
  local f
  while IFS= read -r -d '' f; do substitute "$f"; done \
    < <(find "$dest" -type f -print0)
}

install_into() {
  local base="$1"
  copy_tree agents    "$base/agents"
  copy_tree commands  "$base/commands"
  copy_tree standards "$base/standards"
  echo "✓ agents, commands, standards → $base"
}

install_adw() {
  # The ADW runner. Copies the scripts but never clobbers adw.env (secrets) or
  # runs/ (transcripts) — cp -R overwrites only files that exist in the source.
  local base="$1"
  copy_tree adw "$base/adw"
  chmod +x "$base/adw"/*.py "$base/adw"/*.sh 2>/dev/null || true
  echo "✓ adw runner → $base/adw"
  if [ -f "$base/adw/adw.env" ]; then
    echo "• adw.env already exists — left untouched"
  else
    echo "  next: cp $base/adw/adw.env.sample $base/adw/adw.env  &&  edit it"
    echo "        then: cd $base/adw && uv run health_check.py"
  fi
}

if [ "$MODE" = "global" ]; then
  install_into "$HOME/.claude"
  [ "$WITH_ADW" = "yes" ] && echo "• --with-adw is per-project only (it needs a git remote) — skipped"
  echo "Done. Re-run this script after editing the harness to update."
  exit 0
fi

# ── Project mode ──
CLAUDE_DIR="$TARGET_REPO/.claude"
install_into "$CLAUDE_DIR"
[ "$WITH_ADW" = "yes" ] && install_adw "$CLAUDE_DIR"

# ── Per-project overlay ──
# Project-specific files that don't belong in the generic core (e.g. a repo's own
# /run-local command) live in overlays/<config-name>/, mirroring core/'s layout.
# They install after core, so an overlay can also override a core file.
OVERLAY_DIR="$HARNESS_DIR/overlays/$(basename "${CONFIG%.config}")"
if [ -d "$OVERLAY_DIR" ]; then
  for sub in agents commands standards; do
    [ -d "$OVERLAY_DIR/$sub" ] || continue
    mkdir -p "$CLAUDE_DIR/$sub"
    cp -R "$OVERLAY_DIR/$sub/." "$CLAUDE_DIR/$sub/"
    while IFS= read -r -d '' f; do substitute "$f"; done \
      < <(find "$CLAUDE_DIR/$sub" -type f -print0)
  done
  echo "✓ project overlay → applied from ${OVERLAY_DIR#$HARNESS_DIR/}"
fi

# Stamp CLAUDE.md if the project doesn't have one yet. A stamped CLAUDE.md is
# harness-generated, so we also hide it from the repo. A pre-existing one is the
# project's own file — leave it tracked and untouched.
EXCLUDE_ENTRIES=".claude/ CLAUDE.local.md"
if [ ! -f "$TARGET_REPO/CLAUDE.md" ]; then
  cp "$HARNESS_DIR/templates/CLAUDE.md.template" "$TARGET_REPO/CLAUDE.md"
  substitute "$TARGET_REPO/CLAUDE.md"
  EXCLUDE_ENTRIES="$EXCLUDE_ENTRIES CLAUDE.md"
  echo "✓ stamped CLAUDE.md from template (will be hidden from the repo)"
else
  echo "• CLAUDE.md already exists — left untouched. Merge the Clean Code section"
  echo "  from templates/CLAUDE.md.template manually if you want it there."
fi

# Hide the harness from the target repo (local-only, never committed/pushed).
EXCLUDE="$TARGET_REPO/.git/info/exclude"
if [ -d "$TARGET_REPO/.git" ]; then
  mkdir -p "$TARGET_REPO/.git/info"
  for entry in $EXCLUDE_ENTRIES; do
    grep -qxF "$entry" "$EXCLUDE" 2>/dev/null || echo "$entry" >> "$EXCLUDE"
  done
  echo "✓ excluded ($EXCLUDE_ENTRIES) via .git/info/exclude (local-only)"
else
  echo "• Not a git repo — skipped .git/info/exclude. Add .claude/ to .gitignore yourself."
fi

echo "Done. The harness lives in $CLAUDE_DIR and is invisible to the project's remote."
