<#
.SYNOPSIS
    DevGuard 1-Click Demo & Presentation Launcher for Windows / PowerShell.
.DESCRIPTION
    Launches DevGuard for live demonstration or testing.
    Modes:
      1. Mock    - Starts zero-dependency Mock Live Server on port 8765 + Streamlit UI on 8501.
      2. Live    - Starts full DevGuard Backend (requires Ollama Gemma 4) + Streamlit UI.
      3. UIOnly  - Starts Streamlit UI in offline Fixture Mode.
.EXAMPLE
    .\demo\run_demo.ps1 -Mode Mock
#>

param (
    [ValidateSet("Mock", "Live", "UIOnly", "Prompt")]
    [string]$Mode = "Prompt"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "           DevGuard Demo & Presentation Launcher           " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Repo Root: $RepoRoot" -ForegroundColor Gray

# Check python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Detected Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python was not found in PATH. Please install Python 3.11+." -ForegroundColor Red
    exit 1
}

if ($Mode -eq "Prompt") {
    Write-Host "`nSelect presentation mode:" -ForegroundColor Yellow
    Write-Host "  [1] Mock Live Server + Dashboard (Recommended for offline rehearsal; zero dependencies)"
    Write-Host "  [2] Real DevGuard Backend + Dashboard (Requires local Ollama & gemma4:e4b-it-q4_K_M)"
    Write-Host "  [3] Dashboard Only in Fixture Mode (Offline sample evaluation)"
    $choice = Read-Host "`nEnter choice [1-3] (Default: 1)"
    switch ($choice) {
        "2" { $Mode = "Live" }
        "3" { $Mode = "UIOnly" }
        default { $Mode = "Mock" }
    }
}

Write-Host "`nStarting in mode: $Mode..." -ForegroundColor Cyan

$serverProcess = $null

try {
    if ($Mode -eq "Mock") {
        Write-Host "[*] Starting DevGuard Mock Live Server on http://127.0.0.1:8765/api/v1..." -ForegroundColor Yellow
        $serverProcess = Start-Process python -ArgumentList "$RepoRoot\demo\mock_live_server.py --port 8765" -PassThru -NoNewWindow
        Start-Sleep -Seconds 2
        Write-Host "[OK] Mock Live Server active (PID: $($serverProcess.Id))" -ForegroundColor Green
    } elseif ($Mode -eq "Live") {
        Write-Host "[*] Starting DevGuard Full Backend on port 8765..." -ForegroundColor Yellow
        $serverProcess = Start-Process python -ArgumentList "-m devguard" -WorkingDirectory $RepoRoot -PassThru -NoNewWindow
        Start-Sleep -Seconds 3
        Write-Host "[OK] Backend process active (PID: $($serverProcess.Id))" -ForegroundColor Green
    }

    Write-Host "[*] Launching Streamlit Operator Dashboard on http://localhost:8501..." -ForegroundColor Yellow
    python -m streamlit run "$RepoRoot\devguard\ui\app.py"

} finally {
    if ($serverProcess -ne $null -and -not $serverProcess.HasExited) {
        Write-Host "`n[*] Terminating backend server process (PID: $($serverProcess.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Server process stopped." -ForegroundColor Green
    }
}
