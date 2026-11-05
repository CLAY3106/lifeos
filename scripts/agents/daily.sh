#!/usr/bin/env bash
# Daily LifeOS agent run on your own computer. Schedule it with cron (macOS/Linux)
# or Task Scheduler (Windows, via Git Bash or WSL). See SETUP-OPENCODE.md.
set -euo pipefail

REPO="${LIFEOS_REPO:-$HOME/code/lifeos}"   # change to your repo path, or export LIFEOS_REPO
cd "$REPO"

mkdir -p logs/agents
LOG="logs/agents/$(date +%F).log"

{
  echo "=== LifeOS agent run $(date) ==="

  # Refuse to run on a dirty tree so agents never mix with your own uncommitted work.
  if [ -n "$(git status --porcelain)" ]; then
    echo "Working tree is dirty. Skipping today's run."
    exit 0
  fi

  git checkout main
  git pull --ff-only

  # --auto approves anything not explicitly denied in opencode.json, so the deny list
  # there is what keeps this safe. Never remove the deny rules.
  opencode run \
    --agent scrum-lead \
    --auto \
    --title "Daily sprint $(date +%F)" \
    "Run today's daily cycle exactly as your instructions describe. This run is unattended: never ask questions. If something is unclear or blocked, write it in the daily report and stop."

  git checkout main
  echo "=== Done $(date) ==="
} >> "$LOG" 2>&1
