#!/bin/bash

################################################################################
# Shiftee 월말 급여 보고서 자동 생성 스크립트
#
# 용도: 월말마다 Shiftee에서 데이터를 다운로드하고 Excel 보고서를 자동 생성
# 실행: ./scripts/monthly_report.sh
# Cron: 0 0 1 * * /path/to/shiftee_analysis/scripts/monthly_report.sh
################################################################################

set -euo pipefail  # 에러 발생 시 중단, undefined 변수 사용 금지

################################################################################
# 설정
################################################################################

# 프로젝트 루트 디렉터리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 환경 변수 파일
ENV_FILE="${PROJECT_ROOT}/.env"

# 템플릿 파일 경로 (환경 변수 또는 기본값)
TEMPLATE_PATH="${TEMPLATE_PATH:-$HOME/Downloads/레포트_템플릿.xlsx}"

# 출력 디렉터리
OUTPUT_DIR="${PROJECT_ROOT}/output"
mkdir -p "$OUTPUT_DIR"

# 로그 디렉터리
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "$LOG_DIR"

# 로그 파일 (날짜별)
LOG_FILE="${LOG_DIR}/monthly_report_$(date +%Y%m%d_%H%M%S).log"

# Python 실행 파일 (가상환경 사용 시 경로 변경)
PYTHON="${PYTHON:-python}"

# 메인 스크립트
MAIN_SCRIPT="${PROJECT_ROOT}/shiftee_analysis.py"

# 이메일 설정 (선택적)
SEND_EMAIL="${SEND_EMAIL:-false}"
EMAIL_TO="${EMAIL_TO:-}"
EMAIL_FROM="${EMAIL_FROM:-noreply@example.com}"
EMAIL_SUBJECT="Shiftee 월말 급여 보고서 - $(date +%Y년\ %m월)"

################################################################################
# 함수 정의
################################################################################

# 로그 함수
log() {
    local level=$1
    shift
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

info() {
    log "INFO" "$@"
}

warn() {
    log "WARN" "$@"
}

error() {
    log "ERROR" "$@"
}

# 성공 메시지
success() {
    log "SUCCESS" "$@"
}

# 에러 핸들러
error_handler() {
    local line=$1
    error "스크립트 실행 실패 (라인 $line)"
    exit 1
}

trap 'error_handler $LINENO' ERR

# 환경 변수 로드
load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        info ".env 파일 로드: $ENV_FILE"
        # shellcheck disable=SC1090
        set -a
        source "$ENV_FILE"
        set +a
    else
        warn ".env 파일이 없습니다: $ENV_FILE"
        warn "환경 변수를 직접 설정하거나 .env 파일을 생성하세요"
    fi
}

# 템플릿 파일 확인
check_template() {
    if [[ ! -f "$TEMPLATE_PATH" ]]; then
        error "템플릿 파일을 찾을 수 없습니다: $TEMPLATE_PATH"
        error "TEMPLATE_PATH 환경 변수를 설정하거나 파일을 준비하세요"
        exit 1
    fi
    info "템플릿 파일 확인: $TEMPLATE_PATH"
}

# Python 환경 확인
check_python() {
    if ! command -v "$PYTHON" &> /dev/null; then
        error "Python을 찾을 수 없습니다: $PYTHON"
        error "PYTHON 환경 변수를 설정하거나 PATH에 python을 추가하세요"
        exit 1
    fi

    local python_version
    python_version=$($PYTHON --version 2>&1 | awk '{print $2}')
    info "Python 버전: $python_version"

    # Python 3.10 이상 확인
    local major minor
    major=$(echo "$python_version" | cut -d. -f1)
    minor=$(echo "$python_version" | cut -d. -f2)

    if [[ $major -lt 3 ]] || [[ $major -eq 3 && $minor -lt 10 ]]; then
        error "Python 3.10 이상이 필요합니다 (현재: $python_version)"
        exit 1
    fi
}

# 메인 스크립트 확인
check_main_script() {
    if [[ ! -f "$MAIN_SCRIPT" ]]; then
        error "메인 스크립트를 찾을 수 없습니다: $MAIN_SCRIPT"
        exit 1
    fi
    info "메인 스크립트 확인: $MAIN_SCRIPT"
}

# 보고서 생성
generate_report() {
    info "============================================================"
    info "Shiftee 월말 보고서 생성 시작"
    info "============================================================"

    local output_file="${OUTPUT_DIR}/report_$(date +%Y%m%d_%H%M%S).xlsx"

    info "출력 파일: $output_file"

    # 전체 워크플로우 실행
    if $PYTHON "$MAIN_SCRIPT" full \
        --template "$TEMPLATE_PATH" \
        --output "$output_file" \
        --overwrite \
        -v >> "$LOG_FILE" 2>&1; then

        success "보고서 생성 완료: $output_file"

        # 파일 크기 확인
        local file_size
        file_size=$(du -h "$output_file" | cut -f1)
        info "파일 크기: $file_size"

        echo "$output_file"
        return 0
    else
        error "보고서 생성 실패"
        return 1
    fi
}

# 이메일 전송
send_email() {
    local report_file=$1

    if [[ "$SEND_EMAIL" != "true" ]]; then
        info "이메일 전송 건너뛰기 (SEND_EMAIL=false)"
        return 0
    fi

    if [[ -z "$EMAIL_TO" ]]; then
        warn "이메일 수신자가 설정되지 않았습니다 (EMAIL_TO)"
        return 0
    fi

    info "이메일 전송 중: $EMAIL_TO"

    # 이메일 본문
    local email_body
    email_body=$(cat <<EOF
Shiftee 월말 급여 보고서가 생성되었습니다.

생성 일시: $(date +'%Y-%m-%d %H:%M:%S')
파일 경로: $report_file
파일 크기: $(du -h "$report_file" | cut -f1)

다음 단계:
1. Excel에서 보고서 파일을 엽니다
2. 수식이 자동으로 재계산됩니다
3. 공지용 시트를 생성합니다 (필요 시)

자동 생성 스크립트: $0
로그 파일: $LOG_FILE
EOF
)

    # mail 명령 사용 (또는 sendmail, mutt 등)
    if command -v mail &> /dev/null; then
        echo "$email_body" | mail -s "$EMAIL_SUBJECT" -a "$report_file" "$EMAIL_TO"
        success "이메일 전송 완료: $EMAIL_TO"
    else
        warn "mail 명령을 찾을 수 없습니다. 이메일 전송 건너뛰기"
        info "mailutils 설치: sudo apt-get install mailutils (Ubuntu/Debian)"
    fi
}

# 오래된 파일 정리
cleanup_old_files() {
    local days=${CLEANUP_DAYS:-30}

    info "오래된 파일 정리 (${days}일 이전)"

    # 오래된 로그 파일 삭제
    find "$LOG_DIR" -name "*.log" -mtime "+$days" -delete 2>/dev/null || true

    # 오래된 보고서 파일 삭제 (선택적)
    if [[ "${CLEANUP_REPORTS:-false}" == "true" ]]; then
        find "$OUTPUT_DIR" -name "report_*.xlsx" -mtime "+$days" -delete 2>/dev/null || true
        info "오래된 보고서 파일 삭제 완료"
    fi

    info "파일 정리 완료"
}

# 실행 요약
print_summary() {
    local report_file=$1
    local start_time=$2
    local end_time=$3
    local duration=$((end_time - start_time))

    info "============================================================"
    info "실행 요약"
    info "============================================================"
    info "시작 시간: $(date -r "$start_time" +'%Y-%m-%d %H:%M:%S')"
    info "종료 시간: $(date -r "$end_time" +'%Y-%m-%d %H:%M:%S')"
    info "실행 시간: ${duration}초"
    info "보고서 파일: $report_file"
    info "로그 파일: $LOG_FILE"
    info "============================================================"
}

################################################################################
# 메인 실행
################################################################################

main() {
    local start_time
    start_time=$(date +%s)

    info "============================================================"
    info "Shiftee 월말 보고서 자동 생성 시작"
    info "실행 시간: $(date +'%Y-%m-%d %H:%M:%S')"
    info "============================================================"

    # 환경 설정
    load_env
    check_python
    check_main_script
    check_template

    # 작업 디렉터리 이동
    cd "$PROJECT_ROOT" || exit 1
    info "작업 디렉터리: $PROJECT_ROOT"

    # 보고서 생성
    local report_file
    if report_file=$(generate_report); then
        # 이메일 전송 (선택적)
        send_email "$report_file"

        # 오래된 파일 정리
        cleanup_old_files

        # 실행 요약
        local end_time
        end_time=$(date +%s)
        print_summary "$report_file" "$start_time" "$end_time"

        success "모든 작업 완료"
        exit 0
    else
        error "보고서 생성 실패"
        exit 1
    fi
}

# 스크립트 실행
main "$@"
