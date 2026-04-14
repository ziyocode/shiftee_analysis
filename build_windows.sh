#!/bin/bash
# Windows용 Shiftee Analyzer 크로스 빌드 스크립트 (Linux/macOS에서 실행)
#
# 사용법: bash build_windows.sh
#
# 요구사항:
# - Python 3.10 이상
# - uv 패키지 매니저
# - Wine (선택사항, Windows .exe 테스트용)

set -e

echo "========================================"
echo "Shiftee Analyzer Windows 빌드"
echo "========================================"
echo ""

# 1. 의존성 설치
echo "[1/5] 의존성 설치 중..."
uv sync --extra build
echo ""

# 2. Playwright 브라우저 설치
echo "[2/5] Playwright Chromium 브라우저 설치 중..."
uv run playwright install chromium
echo ""

# 3. 이전 빌드 정리
echo "[3/5] 이전 빌드 정리 중..."
rm -rf build dist
echo ""

# 4. PyInstaller 빌드
echo "[4/5] PyInstaller로 .exe 빌드 중..."
uv run pyinstaller shiftee.spec
echo ""

# 5. Playwright 브라우저를 dist 폴더에 복사
echo "[5/5] Playwright 브라우저를 배포 폴더에 복사 중..."
PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright"
if [ -d "$PLAYWRIGHT_BROWSERS_PATH" ]; then
    cp -r "$PLAYWRIGHT_BROWSERS_PATH" "dist/ShifteeAnalyzer/ms-playwright"
else
    echo "경고: Playwright 브라우저 경로를 찾을 수 없습니다."
    echo "Windows에서 직접 빌드하는 것을 권장합니다."
fi
echo ""

# 6. 배포용 README 복사
echo "사용 설명서를 배포 폴더에 복사 중..."
if [ -f DISTRIBUTION_README.md ]; then
    cp DISTRIBUTION_README.md dist/ShifteeAnalyzer/README.txt
elif [ -f README.md ]; then
    cp README.md dist/ShifteeAnalyzer/README.txt
fi
echo ""

echo "========================================"
echo "빌드 완료!"
echo "========================================"
echo ""
echo "배포 폴더: dist/ShifteeAnalyzer/"
echo "실행 파일: dist/ShifteeAnalyzer/ShifteeAnalyzer.exe"
echo ""
echo "배포 방법:"
echo "1. dist/ShifteeAnalyzer 폴더 전체를 압축"
echo "2. 동료들에게 압축 파일 전달"
echo "3. 압축 해제 후 ShifteeAnalyzer.exe 실행"
echo ""
