# Reviewable Windows source installer; no elevation or machine-wide changes.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$TaskRoot = Split-Path -Parent $PSScriptRoot
Push-Location $TaskRoot
try {
    if ($env:OS -ne 'Windows_NT') { throw 'Use scripts/setup.sh on macOS/Linux.' }
    if (Test-Path .venv) {
        if ((Get-Item .venv -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw 'Refusing a linked .venv. Choose a fresh checkout.'
        }
    }
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        $Candidates = @(
            @{ File = 'python'; Arguments = @() },
            @{ File = 'py'; Arguments = @('-3.12') },
            @{ File = 'py'; Arguments = @('-3.11') }
        )
        $Found = $false
        foreach ($Candidate in $Candidates) {
            $Executable = $Candidate.File
            if (-not (Get-Command $Executable -ErrorAction SilentlyContinue)) { continue }
            $Arguments = @($Candidate.Arguments)
            & $Executable @Arguments -c 'import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,14)))' 2>$null
            if ($LASTEXITCODE -eq 0) {
                & $Executable @Arguments -m venv .venv
                if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
                $Found = $true
                break
            }
        }
        if (-not $Found) { throw 'Install Python 3.12 from python.org, then retry.' }
    }
    $Python = Join-Path $TaskRoot '.venv\Scripts\python.exe'
    & $Python -c 'import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,14)))'
    if ($LASTEXITCODE -ne 0) { throw 'Use a Python 3.11/3.12 virtual environment.' }
    & $Python -m pip install -r requirements-runtime.lock.txt -r requirements-client.lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed; rerun after fixing the reported error.' }
    & $Python -m pip install --no-deps -e '.[clipboard,client]'
    if ($LASTEXITCODE -ne 0) { throw 'DevGuard installation failed.' }
    & $Python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency validation failed.' }
    Write-Host 'Installed. Run .\scripts\devguard-local.ps1 doctor'
    Write-Host 'Start: .\scripts\devguard-local.ps1 start'
    Write-Host 'Install/open Ollama and Gitleaks. Docker Desktop Linux containers is needed for repairs.'
} finally { Pop-Location }
