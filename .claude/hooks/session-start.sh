#!/bin/bash
# SessionStart hook — installs backend + frontend dependencies so tests and
# linters work in Claude Code on the web. Idempotent and non-interactive.
set -euo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

# --- Backend (FastAPI) ------------------------------------------------------
# A venv is required: the base image ships a Debian-managed `cryptography`
# whose Rust bindings conflict with python-jose, so we isolate deps in a venv.
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
pip install --quiet --upgrade pip --timeout 120 --retries 5
pip install --quiet -e ".[dev]" --timeout 120 --retries 5
deactivate

# Make the backend venv the default python/pytest/ruff for this session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$ROOT/backend/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi

# --- Frontend (Next.js) -----------------------------------------------------
cd "$ROOT/frontend"
npm install --no-audit --no-fund

echo "session-start: backend + frontend dependencies installed"
