# Shiftee 초과근로 적정성 분석 도구

Shiftee.io 근무 데이터를 분석하여 직원들의 초과근로 적정성을 자동으로 판정하는 Python CLI 도구입니다.

## 주요 기능

- 📊 **자동 적정성 판정**: Excel 데이터 기반으로 법정 초과근로 기준 대비 위험도 자동 계산
- 🔥 **법규 위반 감지**: 52시간 법규 기준 초과자 실시간 감지
- 📥 **Shiftee 자동 다운로드**: 리포트 및 급여정산 데이터 자동 다운로드 (Playwright)
- 💬 **카카오톡 알림**: 위험 직원 목록 자동 전송 (선택 사항)
- 🔄 **교대제 자동 제외**: 교대제 직원은 분석 대상에서 자동 제외
- 📈 **Excel 리포트 생성**: 색상 강조 및 수식 포함 분석 리포트

## 필수 요구사항

- Python 3.10 이상
- pip (Python 패키지 관리자)

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Playwright 브라우저 설치

```bash
playwright install chromium
```

### 3. 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성:

```bash
SHIFTEE_ID=your-email@example.com
SHIFTEE_PASSWORD=your-password
SHIFTEE_HEADLESS=true
```

또는 `config/settings.toml` 사용:

```toml
SHIFTEE_ID = "your-email@example.com"
SHIFTEE_PASSWORD = "your-password"
SHIFTEE_HEADLESS = true
```

## 사용법

### 기본 실행 (데이터 파일이 있는 경우)

```bash
python scripts/calculate_risk_direct.py
```

- 기본 데이터: `data/shiftee_data1.xlsx`, `data/shiftee_data2.xlsx`
- 출력: `output/report_YYYYMMDD.xlsx`
- 기간: 이번 달 1일 ~ 전일(어제)

### 다운로드 + 분석 (한 번에 실행)

```bash
# 기본 날짜 (이번 달 1일 ~ 어제)
python scripts/calculate_risk_direct.py --download

# 특정 기간 지정
python scripts/calculate_risk_direct.py --download --start 2025-11-01 --end 2025-11-30
```

### 카카오톡 알림

```bash
# 위험 직원 목록 전송
python scripts/calculate_risk_direct.py --send-kakao

# 요약만 전송
python scripts/calculate_risk_direct.py --kakao-summary

# 다운로드 + 분석 + 카카오톡 전송 (한 번에)
python scripts/calculate_risk_direct.py --download --send-kakao
```

### 주요 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--start YYYY-MM-DD` | 분석 시작 날짜 | 이번 달 1일 |
| `--end YYYY-MM-DD` | 분석 종료 날짜 | 전일(어제) |
| `--download` | Shiftee에서 데이터 자동 다운로드 | - |
| `--output FILE` | 출력 파일 경로 (.xlsx, .csv) | `output/report_YYYYMMDD.xlsx` |
| `--data1 FILE` | shiftee_data1.xlsx 경로 | `data/shiftee_data1.xlsx` |
| `--data2 FILE` | shiftee_data2.xlsx 경로 | `data/shiftee_data2.xlsx` |
| `--send-kakao` | 위험 직원 목록 카카오톡 전송 | - |
| `--kakao-summary` | 요약만 카카오톡 전송 | - |

### 사용 예시

```bash
# 1. 11월 데이터 다운로드 및 분석
python scripts/calculate_risk_direct.py --download --start 2025-11-01 --end 2025-11-30

# 2. 기존 파일로 분석만 수행
python scripts/calculate_risk_direct.py --start 2025-11-01 --end 2025-11-30

# 3. 특정 파일 지정 및 CSV 출력
python scripts/calculate_risk_direct.py \
  --data1 data/custom_report.xlsx \
  --data2 data/custom_payroll.xlsx \
  --output report_11월.csv

# 4. 분석 후 카카오톡 알림
python scripts/calculate_risk_direct.py --send-kakao

# 5. 다운로드 + 분석 + 카카오톡 (완전 자동화)
python scripts/calculate_risk_direct.py --download --start 2025-12-01 --end 2025-12-15 --send-kakao
```

### Shell 스크립트 자동화

더 간편한 실행을 위한 shell 스크립트를 제공합니다:

```bash
# 기본 실행 (이번 달 1일 ~ 어제)
./scripts/auto_analyze_and_notify.sh

# 특정 기간 지정
./scripts/auto_analyze_and_notify.sh --start 2025-12-01 --end 2025-12-15

# cron 작업 등록 (매일 오전 9시)
0 9 * * * cd /path/to/shiftee_analysis && ./scripts/auto_analyze_and_notify.sh
```

**스크립트 기능:**
- ✅ 프로젝트 루트 자동 이동
- ✅ 가상환경 자동 활성화
- ✅ 오류 발생 시 즉시 중단
- ✅ 성공/실패 상태 출력

## 출력 결과

### 콘솔 출력

```
================================================================================
📊 적정성 분석 결과
================================================================================

총 직원: 46명
  - ✅ 정상: 43명 (93.5%)
  - ⚠️  위험: 3명 (6.5%)
  - 🚨 법규기준초과: 0명 (0.0%)

================================================================================
⚠️  위험 직원 목록
================================================================================
 직원   본조직      실제초과근로(h)  법정기준(h)  적정성  법규초과
이상훈 뱅킹IS팀     45.383333       42.857143    위험
박근혁 뱅킹IS팀     44.433333       42.857143    위험
이준우 뱅킹IS팀     44.116667       42.857143    위험
```

### Excel 리포트 (report_YYYYMMDD.xlsx)

- **헤더 행**: 회색 배경, 굵은 글씨
- **위험 직원**: 빨간색 배경 (#FFE6E6)
- **법규초과**: 주황색 배경 (#FFE6CC)
- **수식 포함**: 초과근로시간, 적정성 판단 등

## 프로젝트 구조

```
shiftee_analysis/
├── scripts/
│   ├── calculate_risk_direct.py    # 메인 분석 스크립트
│   ├── compare_outputs.py          # 검증용 비교 스크립트
│   ├── debug_employee.py           # 직원별 디버깅 도구
│   └── verify_excel_compatibility.py
├── kakao_send/                      # 카카오톡 API 통합
│   ├── __init__.py
│   ├── kakao_get_token.py          # 토큰 발급
│   ├── kakao_refresh_token.py      # 토큰 갱신
│   ├── message_formatter.py        # 메시지 포맷팅
│   └── README.md                   # 카카오톡 설정 가이드
├── src/shiftee/                     # Shiftee 자동화 모듈
│   ├── settings.py                 # 설정 관리
│   ├── login.py                    # 로그인 자동화
│   └── attendance.py               # 데이터 다운로드
├── docs/
│   ├── CLI_USAGE.md                # 📖 상세 CLI 사용 가이드
│   ├── calculation_formulas.md     # 계산 수식 설명
│   └── COMPLETION_SUMMARY.md       # 구현 완료 요약
├── config/
│   └── settings.example.toml       # 설정 예시
├── data/                            # 다운로드 데이터 (gitignore)
├── output/                          # 분석 결과 (gitignore)
├── .env                             # 환경 변수 (gitignore)
├── .gitignore
├── README.md
└── requirements.txt
```

## 계산 로직

### 핵심 수식

1. **법정근로시간**: `소정근로시간 - 유급휴가시간`
2. **실제 초과근로시간**: `실제 근로시간 - 법정근로시간`
3. **실제 초과근로(조기출근 제외)**: Excel SUMPRODUCT 로직 구현
4. **법정 초과 기준**: `(월 마지막 날 / 7) × 10 시간`
5. **적정성 판단**: `실제 초과근로(조기출근 제외) > 법정 초과 기준` → "위험"

### 월별 기준값

| 월 | 마지막 날 | 법정 초과 | 법규 위반 |
|----|-----------|-----------|-----------|
| 11월 | 30일 | 42.86시간 | 51.43시간 |
| 12월 | 31일 | 44.29시간 | 53.14시간 |
| 2월 (평년) | 28일 | 40.00시간 | 48.00시간 |
| 2월 (윤년) | 29일 | 41.43시간 | 49.71시간 |

### 제외 대상

- **교대제 직원**: 본직무가 "교대제"인 직원은 자동으로 분석에서 제외됩니다
- **제외 이유**: 야간근무 등 특수 근무 패턴으로 인해 일반 기준 적용 부적합

## 카카오톡 설정

카카오톡 메시지 전송 기능 사용 시 추가 설정이 필요합니다:

1. **카카오 개발자 앱 생성**: [developers.kakao.com](https://developers.kakao.com)
2. **REST API 키 발급**
3. **토큰 발급**: `kakao_send/README.md` 참고
4. **토큰 파일 생성**: `kakao_send/kakao_token.json`

자세한 내용은 `kakao_send/README.md`를 참고하세요.

## 데이터 파일 형식

### shiftee_data1.xlsx (REALTIME-REPORT)

- **시트명**: `YYYYMMDD-YYYYMMDD` 형식 (예: `20251101-20251130`)
- **필수 컬럼**: 직원, 본조직, 본직무, 소정근로시간, 승인된 근로시간, 실제 근로시간, 유급휴가시간, 결근, 퇴근누락

### shiftee_data2.xlsx (PAYROLL)

- **헤더 행**: 3행
- **필수 컬럼**: 이름, 근무일정 시작시간, 퇴근시간, (실제) 총 휴게시간

## 문제 해결

### 파일을 찾을 수 없음

```bash
❌ 오류: FileNotFoundError: data/shiftee_data1.xlsx

# 해결 방법 1: 자동 다운로드
python scripts/calculate_risk_direct.py --download

# 해결 방법 2: 파일 경로 직접 지정
python scripts/calculate_risk_direct.py --data1 path/to/file1.xlsx --data2 path/to/file2.xlsx
```

### Playwright 브라우저 없음

```bash
❌ 오류: Playwright browser not found

# 해결 방법
playwright install chromium
```

### 로그인 실패

```bash
❌ 오류: Login failed

# 해결 방법
# 1. .env 파일 확인 (SHIFTEE_ID, SHIFTEE_PASSWORD)
# 2. 브라우저 표시 모드로 디버깅
SHIFTEE_HEADLESS=false python scripts/calculate_risk_direct.py --download
```

### 시트를 찾을 수 없음

```bash
❌ 오류: Sheet '20251101-20251130' not found

# 해결 방법: Excel 파일의 시트명 확인
python -c "import openpyxl; wb = openpyxl.load_workbook('data/shiftee_data1.xlsx'); print(wb.sheetnames)"
```

## 참고 문서

- **📖 상세 CLI 사용법**: [`docs/CLI_USAGE.md`](docs/CLI_USAGE.md)
- **🧮 계산 수식**: [`docs/calculation_formulas.md`](docs/calculation_formulas.md)
- **✅ 완료 요약**: [`docs/COMPLETION_SUMMARY.md`](docs/COMPLETION_SUMMARY.md)
- **💬 카카오톡 설정**: [`kakao_send/README.md`](kakao_send/README.md)

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다.
