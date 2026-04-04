#!/bin/bash
# Shiftee Analysis 실행 스크립트
# 사용법: ./run_analysis.sh

# 오류 발생 시 중단
set -euo pipefail

# 로그 파일 설정
LOG_FILE="./logs/run_analysis.log"
mkdir -p ./logs

{
    echo "================================================================"
    echo "START: $(date)"
    echo "================================================================"

    # 스크립트가 있는 디렉토리로 이동 (필수)
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$DIR"
    echo "📂 Working Directory: $PWD"

    # PATH 설정 (cron 등 비대화형 환경 대응)
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

    MISE_BIN="$(command -v mise || true)"
    if [ -z "$MISE_BIN" ]; then
        echo "❌ mise command not found"
        echo "💡 Please install tools first: mise install"
        exit 1
    fi

    "$MISE_BIN" install --quiet

    echo "🚀 Running shiftee-analyze via mise + uv..."
    "$MISE_BIN" exec -- uv run --frozen shiftee-analyze --download --send-kakao

    echo "----------------------------------------------------------------"
    echo "✅ FINISHED: $(date)"
    echo "================================================================"

} 2>&1 | tee -a "$LOG_FILE"
