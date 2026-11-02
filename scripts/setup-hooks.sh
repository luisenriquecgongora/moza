#!/usr/bin/env bash
# Installs local git config and the commit-standards hooks for this clone.
# Safe to re-run. Pre-existing hooks are kept as <hook>.local and still run.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
HOOKS_DIR=$(git rev-parse --git-path hooks)
MARKER="# commit-standards-hook"
mkdir -p "$HOOKS_DIR"

# --- Local git config -------------------------------------------------------
git config --local diff.renames true
git config --local diff.renameLimit 2000
git config --local apply.whitespace fix
git config --local core.autocrlf input
git config --local core.whitespace "trailing-space,space-before-tab"

# --- Hook installation ------------------------------------------------------
install_hook() {
  local name="$1" target="$HOOKS_DIR/$1"
  if [ -f "$target" ] && ! grep -q "$MARKER" "$target"; then
    if [ -e "$target.local" ]; then
      echo "❌ $target.local already exists; resolve manually before re-running." >&2
      exit 1
    fi
    mv "$target" "$target.local"
    echo "↪ Kept existing $name hook as $name.local (chained)."
  fi
  cat > "$target"
  chmod +x "$target"
  echo "✅ Installed $name hook."
}

install_hook commit-msg <<'EOF'
#!/usr/bin/env bash
# commit-standards-hook
MSG=$(head -n 1 "$1")
PATTERN="^(feat|fix|refactor|perf|chore|test|docs|build|ci|model|data|eval|exp)(\([a-zA-Z0-9_-]+\))?!?: .{1,72}$"
AUTOGEN='^(Merge |Revert "|fixup! |squash! |amend! )'

if ! echo "$MSG" | grep -Eq "$AUTOGEN" && ! echo "$MSG" | grep -Eq "$PATTERN"; then
  echo "❌ [Format Error] Invalid commit message: \"$MSG\""
  echo "Required: <type>(<scope>): <short imperative subject>"
  echo "Types: feat, fix, refactor, perf, chore, test, docs, build, ci, model, data, eval, exp"
  exit 1
fi

if [ -f "$0.local" ]; then
  "$0.local" "$@"
fi
EOF

install_hook pre-commit <<'EOF'
#!/usr/bin/env bash
# commit-standards-hook
set -euo pipefail

if ! git diff --cached --check; then
  echo "❌ [Pre-Commit] Staged diff contains whitespace errors (see above)." >&2
  exit 1
fi

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -vE '(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|\.md$|\.gitattributes$|\.editorconfig$)' || true)
FILE_COUNT=$(echo "$STAGED_FILES" | sed '/^$/d' | wc -l)

if [ "$FILE_COUNT" -gt 5 ]; then
  echo "❌ [Pre-Commit] Blast-radius cap exceeded: $FILE_COUNT non-doc files staged (max 5)." >&2
  exit 1
fi

if [ -f "$0.local" ]; then
  "$0.local" "$@"
fi
EOF

echo "🎉 Commit standards hooks installed."
