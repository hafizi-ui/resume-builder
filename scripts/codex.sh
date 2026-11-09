#!/usr/bin/env bash
# Wrapper so Claude (or you) can call Codex as a second reviewer.
# Usage:
#   scripts/codex.sh status                 # installed? signed in?
#   scripts/codex.sh review [base-branch]   # review uncommitted changes, or the branch vs base
#   scripts/codex.sh ask "question"         # read-only second opinion; answer printed to stdout
#   scripts/codex.sh ask - < prompt.txt     # same, prompt from stdin
set -euo pipefail

ensure_installed() {
  if ! command -v codex >/dev/null 2>&1; then
    echo "codex not found; installing @openai/codex..." >&2
    npm install -g @openai/codex >&2
  fi
}

ensure_signed_in() {
  if ! codex login status >/dev/null 2>&1; then
    cat >&2 <<'MSG'
Codex is installed but not signed in. Pick one:
  - API key:  printenv OPENAI_API_KEY | codex login --with-api-key
  - ChatGPT:  codex login --device-auth
MSG
    exit 2
  fi
}

cmd="${1:-status}"; shift || true
ensure_installed

case "$cmd" in
  status)
    codex --version
    codex login status || true
    ;;
  review)
    ensure_signed_in
    if [ -n "${1:-}" ]; then
      codex review --base "$1"
    else
      codex review --uncommitted
    fi
    ;;
  ask)
    ensure_signed_in
    prompt="${1:-}"
    [ "$prompt" = "-" ] || [ -z "$prompt" ] && prompt="$(cat)"
    out="$(mktemp)"
    codex exec --sandbox read-only --ephemeral --skip-git-repo-check \
      -o "$out" "$prompt" >/dev/null
    cat "$out"; rm -f "$out"
    ;;
  *)
    echo "unknown command: $cmd (use status | review | ask)" >&2; exit 1 ;;
esac
