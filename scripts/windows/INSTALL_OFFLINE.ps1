param(
    [string]$PythonExecutable = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$BundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $BundleRoot "hazard-red-zone-system"
$Wheelhouse = Join-Path $BundleRoot "wheelhouse"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$VenvRoot = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$InstallReceipt = Join-Path $BundleRoot "INSTALL_OK.txt"

function Resolve-Python312 {
    param([string]$ExplicitPath)

    if ($ExplicitPath) {
        if (-not (Test-Path $ExplicitPath)) {
            throw "Python executable not found: $ExplicitPath"
        }
        return (Resolve-Path $ExplicitPath).Path
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $resolved = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $resolved) {
            return $resolved.Trim()
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $resolved = & python -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $resolved) {
            return $resolved.Trim()
        }
    }

    throw "Python 3.12 was not found. Install 64-bit Python 3.12, then run this script again."
}

function Invoke-Checked {
    param(
        [string]$Executable,
        [string[]]$Arguments
    )

    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Executable $($Arguments -join ' ')"
    }
}

Write-Host "Hazard Command — offline bundle installer" -ForegroundColor Cyan
Write-Host "Bundle: $BundleRoot"

if (-not (Test-Path $ProjectRoot)) {
    throw "Project folder is missing: $ProjectRoot"
}
if (-not (Test-Path $Wheelhouse)) {
    throw "Offline wheelhouse is missing: $Wheelhouse"
}
if (-not (Test-Path $Requirements)) {
    throw "requirements.txt is missing: $Requirements"
}

$BasePython = Resolve-Python312 -ExplicitPath $PythonExecutable
$Version = & $BasePython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0 -or $Version.Trim() -ne "3.12") {
    throw "This field bundle requires Python 3.12. Found: $Version at $BasePython"
}

Write-Host "Using Python: $BasePython" -ForegroundColor Green

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating isolated environment..."
    Invoke-Checked -Executable $BasePython -Arguments @("-m", "venv", $VenvRoot)
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment creation did not produce: $VenvPython"
}

Write-Host "Installing dependencies from the bundled wheelhouse only..."
Invoke-Checked -Executable $VenvPython -Arguments @(
    "-m", "pip", "install",
    "--no-index",
    "--find-links", $Wheelhouse,
    "-r", $Requirements
)

Write-Host "Running strict competition preflight..."
Push-Location $ProjectRoot
try {
    Invoke-Checked -Executable $VenvPython -Arguments @(
        "scripts\field_preflight.py",
        "--strict-road-cache"
    )
}
finally {
    Pop-Location
}

$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
@"
Hazard Command offline installation completed successfully.
Installed: $Timestamp
Python: $BasePython
Virtual environment: $VenvRoot
Strict field preflight: PASS

Next: double-click START_OFFLINE.cmd
"@ | Set-Content -Encoding UTF8 $InstallReceipt

Write-Host "" 
Write-Host "INSTALLATION COMPLETE" -ForegroundColor Green
Write-Host "Strict field preflight passed."
Write-Host "Next: double-click START_OFFLINE.cmd"
