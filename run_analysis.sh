#!/bin/bash
# Shiftee Analysis 실행 스크립트
# 사용법: ./run_analysis.sh

# 오류 발생 시 중단
set -e

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

    # 가상환경의 실행 파일 절대 경로 설정
    VENV_PYTHON="$DIR/.venv/bin/python"
    
    # 가상환경 확인
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "❌ Virtual environment not found at $VENV_PYTHON"
        echo "💡 Please run 'pip install -e .' first."
        exit 1
    fi

    # PATH 설정 (시스템 명령어용)
    export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
    
    # PYTHONPATH에 src 추가 (ImportError 방지)
    export PYTHONPATH="$DIR/src:$PYTHONPATH"

    echo "🚀 Running shiftee-analyze..."
    
    # 패키지 모듈을 직접 실행 (가장 안정적)
    "$VENV_PYTHON" -m shiftee.cli --download --send-kakao

    echo "----------------------------------------------------------------"
    echo "✅ FINISHED: $(date)"
    echo "================================================================"

} 2>&1 | tee -a "$LOG_FILE"
