#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
export ALT_DATA_DIR="${ALT_DATA_DIR:-$ROOT/data}"
export ALT_MODELS_DIR="${ALT_MODELS_DIR:-$ROOT/models}"
export ALT_CACHE_DIR="${ALT_CACHE_DIR:-$ROOT/cache}"
export ALT_LOGS_DIR="${ALT_LOGS_DIR:-$ROOT/logs}"
export HF_HOME="${HF_HOME:-$ROOT/cache/huggingface}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-$HF_HOME/hub}"
export HF_XET_CACHE="${HF_XET_CACHE:-$HF_HOME/xet}"
export HF_ASSETS_CACHE="${HF_ASSETS_CACHE:-$HF_HOME/assets}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$ROOT/cache/pip}"
export TMPDIR="${TMPDIR:-$ROOT/cache/temp}"
mkdir -p "$ALT_DATA_DIR" "$ALT_MODELS_DIR" "$ALT_CACHE_DIR" "$ALT_LOGS_DIR" "$HF_HOME" "$PIP_CACHE_DIR" "$TMPDIR"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt
.venv/bin/python -m app.bootstrap
echo "[start] Academic Live Translator beta 0.2 -> http://127.0.0.1:8765"
.venv/bin/python run.py
