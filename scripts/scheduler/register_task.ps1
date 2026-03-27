#Requires -Version 5.1
#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Registers (or updates) the Windows Scheduled Task that runs the weekly
    productivity review every Friday at 08:00 AM.

.EXAMPLE
    # Run from an elevated PowerShell prompt:
    .\register_task.ps1

    # Override the script path or time:
    .\register_task.ps1 -ScriptPath "D:\repos\claude-system\scripts\scheduler\run_weekly_review.ps1" -RunAt "09:00"
#>

param(
    [string]$ScriptPath = (Join-Path $PSScriptRoot "run_weekly_review.ps1"),
    [string]$TaskName   = "Claude_WeeklyProductivityReview",
    [string]$TaskPath   = "\ClaudeSystem\",
    [string]$RunAt      = "08:00",          # 24-hour HH:mm
    [string]$RunAsUser  = $env:USERNAME     # runs as current user by default
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script not found: $ScriptPath`nUpdate -ScriptPath to the correct absolute path."
    exit 1
}

$resolvedScript = Resolve-Path $ScriptPath | Select-Object -ExpandProperty Path
Write-Host "Script path : $resolvedScript"
Write-Host "Task name   : $TaskPath$TaskName"
Write-Host "Schedule    : Every Friday at $RunAt"
Write-Host "Run as      : $RunAsUser"
Write-Host ""

# ---------------------------------------------------------------------------
# Build task components
# ---------------------------------------------------------------------------

# Action: run PowerShell with ExecutionPolicy bypass so no profile is needed
$psExe  = "powershell.exe"
$psArgs = '-NonInteractive -ExecutionPolicy Bypass -File "{0}"' -f $resolvedScript

$action  = New-ScheduledTaskAction -Execute $psExe -Argument $psArgs
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At $RunAt

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -WakeToRun:$false

# Run as current logged-in user (interactive session required for toast notifications)
$principal = New-ScheduledTaskPrincipal `
    -UserId    $RunAsUser `
    -LogonType Interactive `
    -RunLevel  Highest

# ---------------------------------------------------------------------------
# Register (replace if existing)
# ---------------------------------------------------------------------------

$fullPath = "$TaskPath$TaskName"

if (Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Existing task found - updating..."
    Unregister-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName  $TaskName `
    -TaskPath  $TaskPath `
    -Action    $action `
    -Trigger   $trigger `
    -Settings  $settings `
    -Principal $principal `
    -Description "Runs the Claude productivity-agent weekly review (Nudge Engine + Weekly Review) every Friday at $RunAt and drafts results to Gmail." | Out-Null

Write-Host "Task registered: $fullPath" -ForegroundColor Green
Write-Host ""
Write-Host "To test immediately (without waiting for Friday):"
Write-Host "  Start-ScheduledTask -TaskPath '$TaskPath' -TaskName '$TaskName'"
Write-Host ""
Write-Host "To view task status:"
Write-Host "  Get-ScheduledTaskInfo -TaskPath '$TaskPath' -TaskName '$TaskName'"
Write-Host ""
Write-Host "To remove the task:"
Write-Host "  Unregister-ScheduledTask -TaskPath '$TaskPath' -TaskName '$TaskName'"
