#!/usr/bin/env bash
# Bootstrap helper: create envs and basic setup (unix)
set -e
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
echo "Bootstrap complete."
