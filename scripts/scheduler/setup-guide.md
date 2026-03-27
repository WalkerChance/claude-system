# Weekly Review Scheduler — Setup Guide

Automates the productivity-agent **Nudge Engine + Weekly Review** every Friday at 08:00 AM.
On each run it:
1. Invokes the `productivity-agent` skill via the Claude Code CLI.
2. Creates a Gmail draft addressed to `walkerhchance@gmail.com` with the full report.
3. Shows Windows desktop toast notifications at start and finish.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Windows 10 / 11 | Toast notifications require Win 10+. |
| PowerShell 5.1+ | Ships with Windows; verify with `$PSVersionTable.PSVersion`. |
| **Claude Code CLI** | Must be installed and signed in. Run `claude --version` to confirm. |
| Gmail MCP configured | The MCP server must be registered in your Claude Code settings (`~/.claude/settings.json`). |
| Google Calendar MCP configured | Same — required for the weekly review calendar pull. |
| Network access on Friday mornings | Task is set to `RunOnlyIfNetworkAvailable`. |

### Verify Claude Code CLI is on PATH

```powershell
claude --version
# Should print something like: claude/1.x.x ...
```

If this fails, find the install path and add it to your user `PATH` environment variable.

---

## Installation

### 1. Clone / copy the repository to your Windows machine

```powershell
git clone https://github.com/walkerchance/claude-system.git C:\repos\claude-system
```

Or copy just the `scripts\scheduler\` folder anywhere you like — the path is configurable.

### 2. Run the registration script (elevated)

Open **PowerShell as Administrator** and run:

```powershell
Set-Location C:\repos\claude-system\scripts\scheduler

# Default: registers the task pointing at run_weekly_review.ps1 in the same folder
.\register_task.ps1
```

Custom path example:

```powershell
.\register_task.ps1 -ScriptPath "D:\tools\claude-system\scripts\scheduler\run_weekly_review.ps1" -RunAt "08:30"
```

### 3. Verify the task was created

Open **Task Scheduler** (taskschd.msc) and navigate to:

```
Task Scheduler Library > ClaudeSystem > Claude_WeeklyProductivityReview
```

Or from PowerShell:

```powershell
Get-ScheduledTaskInfo -TaskPath "\ClaudeSystem\" -TaskName "Claude_WeeklyProductivityReview"
```

---

## Test the Task Manually

Run it immediately without waiting for Friday:

```powershell
Start-ScheduledTask -TaskPath "\ClaudeSystem\" -TaskName "Claude_WeeklyProductivityReview"
```

Watch the log in real time:

```powershell
$logDir = Join-Path $PSScriptRoot "logs"
Get-ChildItem $logDir -Filter "weekly_review_*.log" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 |
    Get-Content -Wait
```

Check Gmail Drafts — a draft titled `Weekly Review — Friday, <date>` should appear within a few minutes of the task finishing.

---

## Log Files

Logs are written to `scripts\scheduler\logs\` (relative to the script):

| File | Contents |
|---|---|
| `weekly_review_YYYY-MM-DD.log` | Timestamped run log |
| `weekly_review_output_YYYY-MM-DD.txt` | Full Claude stdout |
| `weekly_review_stderr_YYYY-MM-DD.txt` | Claude stderr (errors only) |

Logs older than 12 weeks are automatically deleted on each run.

---

## Email Draft Note

The Gmail MCP only supports **creating drafts** (`gmail_create_draft`) — it cannot send email directly. After the task runs, open Gmail Drafts and send the review from there. This is by design to let you review before sending.

---

## Updating the Schedule

Re-run `register_task.ps1` with a new `-RunAt` time — it will replace the existing task:

```powershell
.\register_task.ps1 -RunAt "09:00"
```

---

## Uninstalling

```powershell
Unregister-ScheduledTask -TaskPath "\ClaudeSystem\" -TaskName "Claude_WeeklyProductivityReview" -Confirm:$false
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `claude: command not found` | Add Claude Code install dir to `PATH` in System Environment Variables |
| No toast notification | Task runs in a non-interactive session — check that `LogonType = Interactive` is set (the register script handles this) |
| Gmail draft not created | Confirm Gmail MCP is configured in `~/.claude/settings.json`; run `claude -p "list my gmail labels"` interactively to verify |
| Task shows "Last Run Result: 0x1" | Open the stderr log file for the error detail |
| `--dangerously-skip-permissions` warning | Required for unattended runs; remove the flag and run interactively if you prefer to approve each tool call |
