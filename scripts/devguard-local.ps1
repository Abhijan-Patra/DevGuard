# Use this checkout's virtualenv without activation or global PATH changes.
$ErrorActionPreference = 'Stop'
$TaskRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $TaskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) {
    & (Join-Path $PSScriptRoot 'setup.ps1')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
& $Python -m devguard.local @args
exit $LASTEXITCODE
