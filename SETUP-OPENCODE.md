# LifeOS agent team on OpenCode: setup and daily schedule

## What is in this folder
- `AGENTS.md`: project rules every agent follows (stack, workflow, ownership, definition of done, hard limits).
- `opencode.json`: loads AGENTS.md and sets safety permissions. The deny list blocks pushing to main, force-push, merging PRs, deleting, sudo, deploys, and migration downgrades.
- `.opencode/agents/`: the team.
  - `scrum-lead` (primary): picks the next sprint issue, delegates, enforces QA and security, opens the PR, writes the daily report.
  - `backend`, `frontend`, `database`, `uiux`, `qa`, `devops` (subagents): one owner per area.
  - `security` (subagent): read-only reviewer, cannot edit.
- `scripts/agents/create-sprint-1.sh`: creates labels and 5 Sprint 1 issues (CI plus tests, since LifeOS has no tests yet).
- `scripts/agents/daily.sh`: the daily unattended run.
- `.github/workflows/agents-daily.yml.example`: optional cloud version that runs in GitHub Actions instead of on your laptop.

You are the PM: you write and label issues, review PRs, and merge. Agents never merge.

## One-time setup (about 20 minutes)
1. Copy everything in this folder into the root of your LifeOS repo. Add `logs/` to `.gitignore`.
2. Install tools: OpenCode (see opencode.ai/docs for your OS) and the GitHub CLI, then run `gh auth login`.
3. Connect a model: run `opencode auth login` and pick a provider. Note on cost: a cheaper or free model protects your Claude Pro limits for the job team, but makes more mistakes, so keep the QA and security steps. Check the provider's terms before using any subscription in OpenCode.
4. Check the team loaded: `opencode agent list` should show all 8 agents.
5. Commit the files on a branch and merge them yourself.
6. Create Sprint 1: `bash scripts/agents/create-sprint-1.sh`. Read the issues on GitHub and edit anything you disagree with.

## First run: watch it
Do not schedule anything until one supervised run looks right.
1. Open `opencode` in the repo, switch to the scrum-lead agent (Tab), and say: "Run today's daily cycle."
2. Approve or deny prompts as they come. Watch what each subagent does.
3. Check the PR it opens and `docs/reports/<today>.md`.
4. If an agent misbehaves, edit only its file in `.opencode/agents/` and run again.

## Schedule it daily

### Option A: on your laptop (uses your local setup)
The laptop must be awake, online, and plugged in at the scheduled time. Pick a time you are normally using it, not 3am. A sleeping laptop skips the run.

macOS or Linux (cron):
1. `chmod +x scripts/agents/daily.sh`
2. `crontab -e` and add one line (fix the paths, and use `which opencode` to find its folder):
   ```
   PATH=/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin
   30 12 * * * LIFEOS_REPO=$HOME/code/lifeos /bin/bash $HOME/code/lifeos/scripts/agents/daily.sh
   ```
   That runs at 12:30 every day. On macOS, give your terminal Full Disk Access if cron cannot read the folder.

Windows (Task Scheduler with Git Bash):
1. Task Scheduler, Create Basic Task, Daily, pick a time.
2. Action: Start a program. Program: `C:\Program Files\Git\bin\bash.exe`. Arguments: `-lc "LIFEOS_REPO=/c/Users/<you>/code/lifeos /c/Users/<you>/code/lifeos/scripts/agents/daily.sh"`.
3. In the task's settings, tick "Run task as soon as possible after a scheduled start is missed".

### Option B: in GitHub Actions (laptop can be off)
Rename `.github/workflows/agents-daily.yml.example` to `agents-daily.yml`, add the secrets listed at the top of the file, and trigger it once by hand with "Run workflow". It is an untested sketch, so check the first run's log before relying on the schedule. GitHub gives private repos a monthly allowance of free Actions minutes; a long agent run uses a lot of them.

## Every day, your part
- Read `docs/reports/<today>.md` (or the run log in `logs/agents/`).
- Review and merge, or comment on, the PRs. Cap is 2 PRs per run so review stays manageable.
- Keep 3 to 5 issues labeled `sprint`. Label anything unclear `needs-son` so agents skip it.

## Safety notes
- `--auto` approves every action that is not explicitly denied. The deny list in `opencode.json` is what keeps unattended runs safe. Do not delete those rules.
- The daily script refuses to run if you have uncommitted changes, so agents never touch your own work in progress.
- Agents cannot deploy. Deploys still happen only from `main` after you merge.
