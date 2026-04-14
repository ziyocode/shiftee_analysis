# Shiftee Analyzer Windows Build Script (PowerShell)
# Usage: .\build.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Shiftee Analyzer Windows Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Install dependencies
Write-Host "[1/5] Installing dependencies..." -ForegroundColor Yellow
uv sync --extra build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# 2. Install Playwright browser
Write-Host "[2/5] Installing Playwright Chromium..." -ForegroundColor Yellow
uv run playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install Playwright browser!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# 3. Clean previous builds
Write-Host "[3/5] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
Write-Host ""

# 4. Build with PyInstaller
Write-Host "[4/5] Building with PyInstaller..." -ForegroundColor Yellow
# .venv의 Python 직접 사용 (uv run 권한 문제 회피)
if (Test-Path ".venv\Scripts\python.exe") {
    .\.venv\Scripts\python.exe -m PyInstaller shiftee.spec
} else {
    uv run python -m PyInstaller shiftee.spec
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# 5. Copy Playwright browsers
Write-Host "[5/5] Copying Playwright browsers..." -ForegroundColor Yellow
$playwrightPath = "$env:USERPROFILE\AppData\Local\ms-playwright"
if (Test-Path $playwrightPath) {
    Copy-Item -Recurse -Force $playwrightPath "dist\ShifteeAnalyzer\ms-playwright"
    Write-Host "Playwright browsers copied successfully" -ForegroundColor Green
} else {
    Write-Host "WARNING: Playwright browser path not found at $playwrightPath" -ForegroundColor Yellow
}
Write-Host ""

# 6. Copy README
Write-Host "Copying README..." -ForegroundColor Yellow
if (Test-Path "DISTRIBUTION_README.md") {
    Copy-Item "DISTRIBUTION_README.md" "dist\ShifteeAnalyzer\README.txt"
} elseif (Test-Path "README.md") {
    Copy-Item "README.md" "dist\ShifteeAnalyzer\README.txt"
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output folder: dist\ShifteeAnalyzer\" -ForegroundColor Cyan
Write-Host "Executable: dist\ShifteeAnalyzer\ShifteeAnalyzer.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "How to distribute:" -ForegroundColor Yellow
Write-Host "1. Compress dist\ShifteeAnalyzer folder"
Write-Host "2. Send ZIP file to your team"
Write-Host "3. Extract and run ShifteeAnalyzer.exe"
Write-Host ""
Read-Host "Press Enter to exit"
