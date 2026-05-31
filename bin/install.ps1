# Wevex installer for Windows -- one-time bootstrap.
#
# Usage (run in PowerShell):
#   irm https://raw.githubusercontent.com/Asanali111/wevex/main/bin/install.ps1 | iex
# or, from inside a cloned repo:
#   .\bin\install.ps1
#
# What it does:
#   1. Verify Python 3.9+
#   2. Create a venv at ~\.wevex\venv
#   3. pip install Wevex into it
#   4. Add ~\.wevex\venv\Scripts to your user PATH permanently
#   5. Print "now run wevex up"
#
# Idempotent -- safe to re-run; updates an existing install in place.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Write-Die($msg)  { Write-Host "  [X]  $msg" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------------------
# 1. Check Python 3.9+
# ---------------------------------------------------------------------------
$python = $null
foreach ($candidate in @("py", "python3", "python")) {
    $ver = $null
    try {
        $ver = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    } catch {}
    if ($ver -and ([System.Version]$ver -ge [System.Version]"3.9")) {
        $python = $candidate
        break
    }
}
if (-not $python) {
    Write-Die "Python 3.9+ is required. Download from https://python.org/downloads"
}
$pyVersion = & $python --version
Write-Ok "Found $pyVersion"

# ---------------------------------------------------------------------------
# 2. Locate source: local checkout or PyPI
# ---------------------------------------------------------------------------
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Split-Path -Parent $scriptDir
$installFrom = $null

if ((Test-Path (Join-Path $projectRoot "pyproject.toml")) -and
    (Test-Path (Join-Path $projectRoot "wevex"))) {
    $installFrom = $projectRoot
    Write-Ok "Installing from local checkout: $installFrom"
} else {
    $installFrom = $null   # will pip install from PyPI
    Write-Ok "Installing wevex from PyPI"
}

# ---------------------------------------------------------------------------
# 3. Create venv (if missing) and install
# ---------------------------------------------------------------------------
$wevexHome = if ($env:WEVEX_HOME) { $env:WEVEX_HOME } else { Join-Path $env:USERPROFILE ".wevex" }
$venvDir   = Join-Path $wevexHome "venv"

if (-not (Test-Path $venvDir)) {
    Write-Host "  Creating venv at $venvDir ..."
    & $python -m venv $venvDir
    Write-Ok "Created venv"
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvWevex  = Join-Path $venvDir "Scripts\wevex.exe"

Write-Host "  Installing Wevex (this may take a minute on first run)..."
# Drive pip via `python -m pip` -- on Windows `pip.exe install -U pip` fails
# because pip.exe is locked while running. The pip upgrade is best-effort.
& $venvPython -m pip install --quiet --upgrade pip 2>$null
if ($installFrom) {
    & $venvPython -m pip install --quiet -e $installFrom
} else {
    & $venvPython -m pip install --quiet --upgrade wevex
}
if ($LASTEXITCODE -ne 0) { Write-Die "pip install failed (exit $LASTEXITCODE). See output above." }
Write-Ok "Wevex installed in $venvDir"

if (-not (Test-Path $venvWevex)) {
    Write-Die "Install completed but $venvWevex not found -- please file a bug."
}

# ---------------------------------------------------------------------------
# 4. Add venv\Scripts to user PATH permanently
# ---------------------------------------------------------------------------
$scriptsDir  = Join-Path $venvDir "Scripts"
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
$entries     = if ($currentPath) { $currentPath -split ";" | Where-Object { $_ -ne "" } } else { @() }

if ($scriptsDir -notin $entries) {
    $newPath = ($entries + $scriptsDir) -join ";"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    $env:PATH = "$scriptsDir;$env:PATH"
    Write-Ok "Added $scriptsDir to your user PATH"
} else {
    Write-Ok "$scriptsDir is already on PATH"
}

# ---------------------------------------------------------------------------
# 5. Summary
# ---------------------------------------------------------------------------
# `wevex --version` prints e.g. "wevex, version 0.2.1" -- pull out just the number.
$installedVersion = ((& $venvWevex --version 2>$null) | Out-String).Trim() -replace '.*?([0-9][0-9.]*).*', '$1'
Write-Host ""
Write-Ok "Wevex $installedVersion ready.  Now run:"
Write-Host ""
Write-Host "    cd `"$env:USERPROFILE\Documents\your-project`""
Write-Host "    wevex up"
Write-Host ""
Write-Host "  If 'wevex' is not found yet, open a new PowerShell window first."
