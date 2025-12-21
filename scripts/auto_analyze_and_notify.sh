#!/bin/bash
#
# Shiftee 자동 분석 및 카카오톡 알림 스크립트
#
# 기능:
#   1. Shiftee에서 데이터 자동 다운로드
#   2. 초과근로 적정성 분석
#   3. 위험 직원 목록 카카오톡 전송
#
# 사용법:
#   ./scripts/auto_analyze_and_notify.sh
#   ./scripts/auto_analyze_and_notify.sh --start 2025-12-01 --end 2025-12-15
#

set -e  # 오류 발생 시 즉시 중단

# 프로젝트 루트 디렉터리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "════════════════════════════════════════════════════════════════"
echo "🤖 Shiftee 자동 분석 및 카카오톡 알림"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Python 가상환경 확인
if [ -d ".venv" ]; then
    echo "📦 가상환경 활성화 중..."
    source .venv/bin/activate
fi

# Python 실행
echo "🚀 분석 시작..."
echo ""

python scripts/calculate_risk_direct.py --download --send-kakao "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "✅ 완료: 분석 및 카카오톡 전송 성공"
    echo "════════════════════════════════════════════════════════════════"
else
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "❌ 실패: 오류 코드 $EXIT_CODE"
    echo "════════════════════════════════════════════════════════════════"
    exit $EXIT_CODE
fi
