#Requires -Version 5.1
<#
.SYNOPSIS
    Runs the productivity-agent weekly review + nudge engine via Claude Code,
    creates a Gmail draft with the results, and shows Windows toast notifications.

.NOTES
    Triggered by Windows Task Scheduler every Friday at 08:00.
    Requires: Claude Code CLI installed and authenticated on this machine.
#>

param(
    [string]$RecipientEmail = "walkerhchance@gmail.com",
    [string]$LogDir = "$PSScriptRoot\logs"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Show-ToastNotification {
    param(
        [string]$Title,
        [string]$Message,
        [ValidateSet("Info","Warning","Error")] [string]$Icon = "Info"
    )

    # Use the Windows Runtime toast API (works on Win 10/11 without extra modules)
    try {
        $appId = "Claude.ProductivityAgent"

        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null

        $template = @"
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>$Title</text>
      <text>$Message</text>
    </binding>
  </visual>
</toast>
"@
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
    }
    catch {
        # Fallback: balloon notification via System.Windows.Forms NotifyIcon
        try {
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            $balloon = New-Object System.Windows.Forms.NotifyIcon
            $balloon.Icon = [System.Drawing.SystemIcons]::Information
            $balloon.BalloonTipIcon  = [System.Windows.Forms.ToolTipIcon]::$Icon
            $balloon.BalloonTipTitle = $Title
            $balloon.BalloonTipText  = $Message
            $balloon.Visible = $true
            $balloon.ShowBalloonTip(8000)
            Start-Sleep -Seconds 9
            $balloon.Dispose()
        }
        catch {
            Write-Warning "Could not show desktop notification: $_"
        }
    }
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $script:LogFile -Value $line
}

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

try {
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir | Out-Null
    }

    $datestamp      = Get-Date -Format "yyyy-MM-dd"
    $script:LogFile = Join-Path $LogDir "weekly_review_$datestamp.log"
}
catch {
    Show-ToastNotification -Title "Weekly Review Failed" `
        -Message "Could not initialise log directory: $_" -Icon "Error"
    exit 1
}

Write-Log "=== Weekly Review Job Started ==="
Write-Log "Recipient : $RecipientEmail"
Write-Log "Log file  : $($script:LogFile)"

# ---------------------------------------------------------------------------
# Step 1 - Opening notification
# ---------------------------------------------------------------------------

Show-ToastNotification `
    -Title "Weekly Review Starting" `
    -Message "Claude is running your Friday review. Results will be drafted to Gmail."

# ---------------------------------------------------------------------------
# Step 2 - Locate claude CLI
# ---------------------------------------------------------------------------

$ClaudeCli = Get-Command claude -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $ClaudeCli) {
    # Common install paths
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\claude\claude.exe",
        "$env:LOCALAPPDATA\Programs\Claude\claude.exe",
        "C:\Program Files\claude\claude.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $ClaudeCli = $c; break }
    }
}

if (-not $ClaudeCli) {
    Write-Log "Claude CLI not found. Ensure 'claude' is on PATH." "ERROR"
    Show-ToastNotification -Title "Weekly Review Failed" `
        -Message "Claude CLI not found. Check PATH." -Icon "Error"
    exit 1
}

Write-Log "Claude CLI: $ClaudeCli"

# ---------------------------------------------------------------------------
# Step 3 - Build the prompt
# ---------------------------------------------------------------------------

$today   = Get-Date -Format "dddd, MMMM d, yyyy"
# Repo root is two directories up from scripts/scheduler/; Claude must run
# there so it can read CLAUDE.md and load the productivity-agent skill, which
# contains the instructions that trigger MCP tool calls (gmail_create_draft,
# gcal_list_events, etc.).
$repoRoot = (Resolve-Path "$PSScriptRoot\..\..\").Path

$prompt = @"
Today is $today (Friday). Run both of these workflows in sequence using the productivity-agent skill:

1. NUDGE ENGINE - surface any at-risk inbox items from this week that still need attention.
2. WEEKLY REVIEW - full review of this week's calendar and inbox, plus next week preview.

After generating both outputs, do the following:
- Combine them into a single well-formatted email body (plain text, no HTML needed).
- Use gmail_create_draft to create a draft addressed to $RecipientEmail with:
    Subject: Weekly Review - $today
    Body: the combined Nudge Report followed by the Weekly Review (clearly separated with headers).
- Confirm when the draft has been created.

Important: create the draft even if some MCP data is incomplete - include whatever you were able to retrieve.
"@

Write-Log "Prompt prepared. Invoking Claude..."
Write-Log "Repo root : $repoRoot"

# ---------------------------------------------------------------------------
# Step 4 - Run Claude
# ---------------------------------------------------------------------------

$outputFile = Join-Path $LogDir "weekly_review_output_$datestamp.txt"
$stderrFile = Join-Path $LogDir "weekly_review_stderr_$datestamp.txt"

# Write the prompt to a temp file and feed it via stdin.
# Rationale: Windows command-line quoting is unreliable for multi-line strings
# that contain double-quote characters (the prompt includes them in the Subject
# line). `--print` reads from stdin when no positional argument is given, with
# --input-format text as the default - confirmed via: echo "..." | claude --print
$promptFile = Join-Path $env:TEMP "claude_weekly_prompt_$datestamp.txt"
Set-Content -Path $promptFile -Value $prompt -Encoding UTF8

try {
    # --dangerously-skip-permissions bypasses all tool-use permission prompts
    # (including MCP tools) so the scheduler can run unattended.
    # -WorkingDirectory must point to the repo root so Claude reads CLAUDE.md
    # and the productivity-agent SKILL.md, which instruct it to call
    # gmail_create_draft and the Google Calendar MCP tools.
    $process = Start-Process -FilePath $ClaudeCli `
        -ArgumentList @(
            "--dangerously-skip-permissions",
            "--print"
        ) `
        -NoNewWindow `
        -Wait `
        -WorkingDirectory $repoRoot `
        -RedirectStandardInput  $promptFile `
        -RedirectStandardOutput $outputFile `
        -RedirectStandardError  $stderrFile `
        -PassThru

    Write-Log "Claude exited with code: $($process.ExitCode)"

    if ($process.ExitCode -ne 0) {
        throw "Claude exited with non-zero code $($process.ExitCode)"
    }

    $outputContent = Get-Content $outputFile -Raw
    $outputLength  = if ($outputContent) { $outputContent.Length } else { 0 }
    Write-Log "Claude output length: $outputLength characters"

    if ($outputContent -match "draft") {
        Write-Log "Draft creation confirmed in output."
        Show-ToastNotification `
            -Title "Weekly Review Complete" `
            -Message "Your Friday review is ready. Check Gmail Drafts for the summary."
    }
    else {
        Write-Log "Draft keyword not detected in output - verify Gmail Drafts manually." "WARN"
        Show-ToastNotification `
            -Title "Weekly Review Done (verify draft)" `
            -Message "Review ran but draft confirmation unclear. Check Gmail Drafts." `
            -Icon "Warning"
    }
}
catch {
    Write-Log "Claude run failed: $_" "ERROR"
    Show-ToastNotification `
        -Title "Weekly Review Failed" `
        -Message "Error running Claude. See log: $($script:LogFile)" `
        -Icon "Error"
    exit 1
}
finally {
    # Always remove the temp prompt file
    if (Test-Path $promptFile) {
        Remove-Item $promptFile -Force -ErrorAction SilentlyContinue
    }
}

# ---------------------------------------------------------------------------
# Step 5 - Rotate old logs (keep last 12 weeks)
# ---------------------------------------------------------------------------

try {
    $cutoff = (Get-Date).AddDays(-84)
    Get-ChildItem -Path $LogDir -Filter "weekly_review_*.log" |
        Where-Object { $_.LastWriteTime -lt $cutoff } |
        Remove-Item -Force
    Get-ChildItem -Path $LogDir -Filter "weekly_review_output_*.txt" |
        Where-Object { $_.LastWriteTime -lt $cutoff } |
        Remove-Item -Force
    Write-Log "Old log rotation complete."
}
catch {
    Write-Log "Log rotation skipped: $_" "WARN"
}

Write-Log "=== Weekly Review Job Finished ==="
exit 0
