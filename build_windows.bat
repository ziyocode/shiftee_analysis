@echo off
REM Windows용 Shiftee Analyzer 빌드 스크립트
REM
REM 사용법: build_windows.bat
REM
REM 요구사항:
REM - Python 3.10 이상
REM - uv 패키지 매니저 (https://github.com/astral-sh/uv)

echo ========================================
echo Shiftee Analyzer Windows 빌드
echo ========================================
echo.

REM 1. 의존성 설치
echo [1/5] 의존성 설치 중...
uv sync --extra build
if %errorlevel% neq 0 (
    echo 의존성 설치 실패!
    pause
    exit /b 1
)
echo.

REM 2. Playwright 브라우저 설치
echo [2/5] Playwright Chromium 브라우저 설치 중...
uv run playwright install chromium
if %errorlevel% neq 0 (
    echo Playwright 브라우저 설치 실패!
    pause
    exit /b 1
)
echo.

REM 3. 이전 빌드 정리
echo [3/5] 이전 빌드 정리 중...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

REM 4. PyInstaller 빌드
echo [4/5] PyInstaller로 .exe 빌드 중...
uv run pyinstaller shiftee.spec
if %errorlevel% neq 0 (
    echo 빌드 실패!
    pause
    exit /b 1
)
echo.

REM 5. Playwright 브라우저를 dist 폴더에 복사
echo [5/5] Playwright 브라우저를 배포 폴더에 복사 중...
set PLAYWRIGHT_BROWSERS_PATH=%USERPROFILE%\AppData\Local\ms-playwright
if exist "%PLAYWRIGHT_BROWSERS_PATH%" (
    xcopy /E /I /Y "%PLAYWRIGHT_BROWSERS_PATH%" "dist\ShifteeAnalyzer\ms-playwright"
) else (
    echo 경고: Playwright 브라우저 경로를 찾을 수 없습니다.
    echo 수동으로 복사가 필요할 수 있습니다.
)
echo.

REM 6. 배포용 README 복사
echo 사용 설명서를 배포 폴더에 복사 중...
if exist DISTRIBUTION_README.md (
    copy DISTRIBUTION_README.md dist\ShifteeAnalyzer\README.txt
) else if exist README.md (
    copy README.md dist\ShifteeAnalyzer\README.txt
)
echo.

echo ========================================
echo 빌드 완료!
echo ========================================
echo.
echo 배포 폴더: dist\ShifteeAnalyzer\
echo 실행 파일: dist\ShifteeAnalyzer\ShifteeAnalyzer.exe
echo.
echo 배포 방법:
echo 1. dist\ShifteeAnalyzer 폴더 전체를 압축
echo 2. 동료들에게 압축 파일 전달
echo 3. 압축 해제 후 ShifteeAnalyzer.exe 실행
echo.
pause
