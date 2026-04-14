@echo off
chcp 65001 >nul
REM Shiftee Analyzer Windows Build Script
REM Usage: build.bat

echo ========================================
echo Shiftee Analyzer Windows Build
echo ========================================
echo.

REM 1. Install dependencies
echo [1/5] Installing dependencies...
uv sync --extra build
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.

REM 2. Install Playwright browser
echo [2/5] Installing Playwright Chromium...
uv run playwright install chromium
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Playwright browser!
    pause
    exit /b 1
)
echo.

REM 3. Clean previous builds
echo [3/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

REM 4. Build with PyInstaller
echo [4/5] Building with PyInstaller...
uv run pyinstaller shiftee.spec
if %errorlevel% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.

REM 5. Copy Playwright browsers
echo [5/5] Copying Playwright browsers...
set PLAYWRIGHT_BROWSERS_PATH=%USERPROFILE%\AppData\Local\ms-playwright
if exist "%PLAYWRIGHT_BROWSERS_PATH%" (
    xcopy /E /I /Y "%PLAYWRIGHT_BROWSERS_PATH%" "dist\ShifteeAnalyzer\ms-playwright"
) else (
    echo WARNING: Playwright browser path not found
)
echo.

REM 6. Copy README
echo Copying README...
if exist DISTRIBUTION_README.md (
    copy DISTRIBUTION_README.md dist\ShifteeAnalyzer\README.txt
) else if exist README.md (
    copy README.md dist\ShifteeAnalyzer\README.txt
)
echo.

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Output folder: dist\ShifteeAnalyzer\
echo Executable: dist\ShifteeAnalyzer\ShifteeAnalyzer.exe
echo.
echo How to distribute:
echo 1. Compress dist\ShifteeAnalyzer folder
echo 2. Send ZIP file to your team
echo 3. Extract and run ShifteeAnalyzer.exe
echo.
pause
