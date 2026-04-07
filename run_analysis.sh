#!/bin/bash
# Shiftee 초과근로 분석 실행 스크립트
# - Shiftee에서 데이터 다운로드 → 분석 → 카카오톡/Slack 알림
# - 로그는 logs/run_analysis.log 에 누적 기록
# 사용법: ./run_analysis.sh

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

mkdir -p ./logs

{
    echo "=== START: $(date) ==="
    uv run --frozen shiftee-analyze --download --send-kakao --send-slack
    echo "=== FINISHED: $(date) ==="
} 2>&1 | tee -a ./logs/run_analysis.log
