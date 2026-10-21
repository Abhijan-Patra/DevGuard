#!/bin/sh
# Reviewable source installer. No sudo, downloaded shell scripts or global config edits.
set -eu
TASK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$TASK_ROOT"
PYTHON_BIN=${DEVGUARD_PYTHON:-}
if [ -z "$PYTHON_BIN" ]; then
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,14)))' 2>/dev/null; then
      PYTHON_BIN=$candidate
      break
    fi
  done
fi
if [ -z "$PYTHON_BIN" ]; then
  echo 'Install Python 3.11 or 3.12 from https://www.python.org/downloads/ then run this script again.' >&2
  exit 1
fi
if [ -L .venv ]; then
  echo 'Refusing a symlinked .venv. Choose a fresh checkout.' >&2
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -c 'import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,14)))'
.venv/bin/python -m pip install -r requirements-runtime.lock.txt -r requirements-client.lock.txt
.venv/bin/python -m pip install --no-deps -e '.[clipboard,client]'
.venv/bin/python -m pip check
printf '\nInstalled. Check prerequisites: ./scripts/devguard-local doctor\n'
printf 'Start the app: ./scripts/devguard-local start\n'
printf 'Ollama, Gitleaks and Docker remain separate applications; see docs/INSTALL.md.\n'
