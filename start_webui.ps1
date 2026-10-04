$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Portable-by-default paths: keep app-generated data off AppData/C: unless the
# user explicitly overrides these variables before launch.
$env:ALT_DATA_DIR = Join-Path $PSScriptRoot "data"
$env:ALT_MODELS_DIR = Join-Path $PSScriptRoot "models"
$env:ALT_CACHE_DIR = Join-Path $PSScriptRoot "cache"
$env:ALT_LOGS_DIR = Join-Path $PSScriptRoot "logs"
$env:HF_HOME = Join-Path $PSScriptRoot "cache\huggingface"
$env:HF_HUB_CACHE = Join-Path $env:HF_HOME "hub"
$env:HF_XET_CACHE = Join-Path $env:HF_HOME "xet"
$env:HF_ASSETS_CACHE = Join-Path $env:HF_HOME "assets"
$env:PIP_CACHE_DIR = Join-Path $PSScriptRoot "cache\pip"
$env:TEMP = Join-Path $PSScriptRoot "cache\temp"
$env:TMP = $env:TEMP

@($env:ALT_DATA_DIR, $env:ALT_MODELS_DIR, $env:ALT_CACHE_DIR, $env:ALT_LOGS_DIR, $env:HF_HOME, $env:PIP_CACHE_DIR, $env:TEMP) | ForEach-Object {
    New-Item -ItemType Directory -Force -Path $_ | Out-Null
}

function Get-PythonCommand {
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py" }
    throw "Python 3.11-3.13 was not found. Install Python or Conda and make sure 'python' is available in PowerShell."
}

$python = Get-PythonCommand

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[setup] Creating portable virtual environment in .venv ..."
    & $python -m venv .venv
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Write-Host "[setup] Installing/updating dependencies ..."
& $venvPython -m pip install --disable-pip-version-check -r requirements.txt

Write-Host "[setup] Preparing the default local ASR model (first run only) ..."
& $venvPython -m app.bootstrap

Write-Host "[start] Academic Live Translator beta 0.3 -> http://127.0.0.1:8765"
Start-Process "http://127.0.0.1:8765"
& $venvPython run.py
