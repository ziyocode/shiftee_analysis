# CLI 사용 가이드

## 개요

`scripts/calculate_risk_direct.py`는 Shiftee 데이터를 분석하여 직원들의 초과근로 적정성을 판정하는 CLI 도구입니다.

## 설치

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 설정

`.env` 파일 또는 `config/settings.toml`에 Shiftee 로그인 정보를 설정하세요:

```bash
# .env
SHIFTEE_ID=your-email@example.com
SHIFTEE_PASSWORD=your-password
SHIFTEE_HEADLESS=true
```

## 실행 방법

```bash
python scripts/calculate_risk_direct.py [옵션]
```

## 옵션

### 날짜 범위 옵션

- `--start YYYY-MM-DD`: 분석 시작 날짜 (기본: 현재 월 1일)
- `--end YYYY-MM-DD`: 분석 종료 날짜 (기본: 전일(어제))

**기본 동작:**
- `--end` 미지정 시 무조건 어제 날짜 사용 (요일 무관)

### 기타 옵션

- `--output, -o FILE`: 결과를 CSV 또는 Excel 파일로 저장 (기본: `output/report_YYYYMMDD.xlsx`)
- `--download`: Shiftee에서 데이터를 먼저 다운로드한 후 분석 (날짜 미지정시 기본값 사용)
- `--data1 FILE`: shiftee_data1.xlsx 파일 경로 (기본: `data/shiftee_data1.xlsx`)
- `--data2 FILE`: shiftee_data2.xlsx 파일 경로 (기본: `data/shiftee_data2.xlsx`)
- `-h, --help`: 도움말 표시

## 사용 예시

### 1. 가장 간단한 실행 (모든 기본값 사용)

```bash
python scripts/calculate_risk_direct.py
```

- 자동으로 `output/report_YYYYMMDD.xlsx` 파일이 생성됩니다
- 시작 날짜: 이번 달 1일
- 종료 날짜: 전일(어제)

### 2. 특정 기간 분석

```bash
python scripts/calculate_risk_direct.py --start 2025-11-01 --end 2025-11-30
```

출력:
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
 직원   본조직  실제초과근로(h)   법정기준(h) 적정성 법규초과
이상훈 뱅킹IS팀  45.383333 42.857143  위험
박근혁 뱅킹IS팀  44.433333 42.857143  위험
이준우 뱅킹IS팀  44.116667 42.857143  위험
```

### 3. 커스텀 파일명으로 Excel 리포트 생성

```bash
python scripts/calculate_risk_direct.py --start 2025-11-01 --end 2025-11-30 --output report_11월.xlsx
```

생성되는 Excel 파일:
- 원본 레포트와 동일한 구조
- 한글 컬럼 헤더
- 위험 직원: 빨간색 배경
- 법규초과: 주황색 배경
- W열(167), X열(날짜) 포함

### 4. CSV로 저장

```bash
python scripts/calculate_risk_direct.py --start 2025-11-01 --end 2025-11-30 --output report.csv
```

### 5. 다운로드부터 한 번에 실행

**기본 날짜로 다운로드:**
```bash
python scripts/calculate_risk_direct.py --download
```
- 이번 달 1일 ~ 전일(어제) 데이터를 자동 다운로드

**특정 기간 다운로드:**
```bash
python scripts/calculate_risk_direct.py --download --start 2025-11-01 --end 2025-11-30
```

이 명령어는:
1. Shiftee에 로그인
2. 해당 기간의 데이터 다운로드
3. 분석 수행
4. Excel 리포트 생성

### 6. 특정 데이터 파일 지정

```bash
python scripts/calculate_risk_direct.py \
  --data1 data/custom_realtime.xlsx \
  --data2 data/custom_payroll.xlsx \
  --start 2025-11-01 \
  --end 2025-11-30 \
  --output report.xlsx
```

### 7. 여러 기간 분석 (배치 실행)

```bash
# 11월 분석
python scripts/calculate_risk_direct.py --start 2025-11-01 --end 2025-11-30 --output report_11월.xlsx

# 12월 분석
python scripts/calculate_risk_direct.py --start 2025-12-01 --end 2025-12-31 --output report_12월.xlsx

# 특정 기간 분석
python scripts/calculate_risk_direct.py --start 2025-12-01 --end 2025-12-14 --output report_12월_중간.xlsx
```

## 출력 파일 구조

### Excel 리포트 (--output report.xlsx)

생성되는 Excel 파일은 다음 구조를 가집니다:

#### 시트: "계산"

| 열 | 헤더 | 설명 |
|----|------|------|
| A | (빈 열) | 원본 레포트 형식 유지 |
| B | 직원 | 직원명 |
| C | 본조직 | 소속 조직 |
| D | 소정근로시간 | 계약상 근로시간 |
| E | 승인된 근로시간 | 승인된 시간 |
| F | 실제 근로시간 | 실제 근무한 시간 |
| G | 실제 근로시간(결근포함) | 결근, 퇴근누락 포함 |
| H | 실제 근로시간(퇴근출근기반) | SUMPRODUCT 계산 |
| I | 표준 근로시간 | 표준 기준 |
| J | 표준 근로시간(결근포함) | 표준 + 결근 |
| K | 유급휴가시간 | 휴가 시간 |
| L | 법정근로시간 | D - K (소정 - 유급) |
| M | 실제 초과근로시간 | F - L |
| N | 실제 초과근로(결근포함) | G - L |
| O | 실제 초과근로(조기출근제외) | ⭐ 핵심 판정 기준 |
| P | 조기출근 합산 | N - O |
| Q | 법정 초과 근로시간 | ⭐ 위험 기준선 (42.86h) |
| R | 법규 위반(전일까지) | 법규 기준선 (51.43h) |
| S | 월법규 위반시간 | 51.6시간 고정 |
| T | 월말까지 가능 초과근로 | S - O |
| U | 적정성 | ⭐ "위험" 또는 "정상" |
| V | 법규 기준초과자 | "법기준초과" 또는 "" |
| W | 167 | 고정값 |
| X | 날짜 | end_date |

#### 스타일링

- **헤더 행**: 회색 배경, 굵은 글씨, 가운데 정렬
- **위험 직원**: 빨간색 배경 (#FFE6E6)
- **법규초과**: 주황색 배경 (#FFE6CC)
- **모든 셀**: 테두리 적용

### CSV 파일 (--output report.csv)

모든 계산 결과를 CSV 형식으로 저장합니다. 스타일링은 적용되지 않습니다.

## 계산 로직

### 핵심 수식

1. **L열 (법정근로시간)**: `D - K` (소정근로시간 - 유급휴가시간)
2. **M열 (실제 초과근로시간)**: `max(0, F - L)` (실제 - 법정)
3. **O열 (조기출근 제외)**: Excel SUMPRODUCT 로직 구현
4. **Q열 (법정 초과)**: `(월 마지막 날 / 7) * 10`
5. **U열 (적정성)**: `O > Q` → "위험", else "정상" (STRICT >)

### 월별 기준값

| 월 | 마지막 날 | Q (법정초과) | R (법규위반) |
|----|----------|-------------|-------------|
| 11월 | 30일 | 42.86시간 | 51.43시간 |
| 12월 | 31일 | 44.29시간 | 53.14시간 |
| 2월 (평년) | 28일 | 40.00시간 | 48.00시간 |
| 2월 (윤년) | 29일 | 41.43시간 | 49.71시간 |

## 데이터 파일 형식

### shiftee_data1.xlsx (REALTIME-REPORT)

- **시트명**: `YYYYMMDD-YYYYMMDD` 형식 (예: `20251101-20251130`)
- **헤더 행**: 1행
- **데이터 시작**: 2행부터
- **필수 컬럼**:
  - B: 직원
  - C: 본조직
  - G: 소정근로시간
  - H: 승인된 근로시간
  - J: 실제 근로시간
  - L: 유급휴가시간
  - W: 결근
  - X: 퇴근누락

### shiftee_data2.xlsx (PAYROLL)

- **헤더 행**: 3행
- **데이터 시작**: 4행부터
- **필수 컬럼**:
  - B: 이름
  - I: 근무일정 시작시간 (datetime)
  - M: 퇴근시간 (datetime)
  - S: (실제) 총 휴게시간 (timedelta)

## 문제 해결

### 1. "No module named 'calculate_risk_direct'"

```bash
# Python path 확인
python -c "import sys; print('\n'.join(sys.path))"

# scripts 디렉터리가 없다면 PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/scripts"
python scripts/calculate_risk_direct.py --help
```

### 2. "FileNotFoundError: data/shiftee_data1.xlsx"

데이터 파일이 없습니다. 다음 중 하나를 선택하세요:

```bash
# 옵션 1: --download로 자동 다운로드
python scripts/calculate_risk_direct.py --download --start 2025-11-01 --end 2025-11-30

# 옵션 2: 파일 경로 직접 지정
python scripts/calculate_risk_direct.py --data1 path/to/file1.xlsx --data2 path/to/file2.xlsx --start 2025-11-01 --end 2025-11-30
```

### 3. "Sheet '20251101-20251130' not found"

shiftee_data1.xlsx 파일의 시트명이 예상과 다릅니다. 파일을 확인하세요:

```bash
# Excel 파일의 시트명 확인
python -c "import openpyxl; wb = openpyxl.load_workbook('data/shiftee_data1.xlsx'); print(wb.sheetnames)"
```

### 4. 위험 직원 수가 예상과 다름

원본 Excel 수식과 정확히 일치하는지 검증하세요:

```bash
# 비교 스크립트 실행 (개발자용)
python scripts/compare_outputs.py
```

### 5. 다운로드 실패

```bash
# 브라우저 표시 모드로 실행 (디버깅)
SHIFTEE_HEADLESS=false python scripts/calculate_risk_direct.py --download --start 2025-11-01 --end 2025-11-30

# 또는 환경 변수 없이
python scripts/calculate_risk_direct.py --download --start 2025-11-01 --end 2025-11-30
# 그런 다음 .env 파일 확인
```

## 고급 사용법

### 1. 스크립트로 자동화

```bash
#!/bin/bash
# monthly_report.sh

MONTH="2025-11"
START_DATE="${MONTH}-01"
END_DATE="${MONTH}-30"
OUTPUT="reports/report_${MONTH}.xlsx"

python scripts/calculate_risk_direct.py \
  --download \
  --start $START_DATE \
  --end $END_DATE \
  --output $OUTPUT

echo "Report generated: $OUTPUT"
```

### 2. 여러 부서 분석

```bash
# 각 부서별 데이터 파일이 있는 경우
for dept in 뱅킹IS팀 뱅킹인프라본부 디지털금융부; do
  python scripts/calculate_risk_direct.py \
    --data1 data/${dept}_data1.xlsx \
    --data2 data/${dept}_data2.xlsx \
    --start 2025-11-01 \
    --end 2025-11-30 \
    --output reports/report_${dept}_11월.xlsx
done
```

### 3. Python API 사용

```python
# custom_analysis.py
import sys
from pathlib import Path

# scripts 디렉터리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from calculate_risk_direct import (
    load_shiftee_data1,
    load_shiftee_data2,
    calculate_g_column,
    calculate_h_column,
    # ... 기타 함수들
)

# 데이터 로드
df1 = load_shiftee_data1(Path("data/shiftee_data1.xlsx"))
df2 = load_shiftee_data2(Path("data/shiftee_data2.xlsx"))

# 계산 수행
df = create_base_dataframe(df1)
df = calculate_g_column(df)
df = calculate_h_column(df, df1, df2)
# ... 기타 계산

# 결과 분석
risk_employees = df[df["U_적정성"] == "위험"]
print(f"위험 직원 수: {len(risk_employees)}")
```

## 분석 제외 대상

### 교대제 직원 자동 제외

**본직무**가 "교대제"인 직원은 분석에서 자동으로 제외됩니다.

**제외 이유:**
- 교대제 직원은 야간근무 등 특수 근무 패턴을 가짐
- 일반 직원과 다른 근무시간 기준이 적용되어야 함
- 표준 초과근로 기준으로 판정 시 부정확한 결과 발생

**제외 과정:**
1. 데이터 로드 후 자동으로 본직무 컬럼 확인
2. "교대제" 직원 명단 추출 및 출력
3. shiftee_data1에서 해당 직원 제외
4. shiftee_data2(출퇴근 기록)에서도 해당 직원 제외
5. 제외된 인원 수와 이름을 콘솔에 출력

**출력 예시:**
```
⚠️  교대제 직원 9명 제외:
   - 유현달
   - 김규완
   - 허지행
   - 김경현
   - 김산하
   - 강희대
   - 임경호
   - 서정우
   - 김정익

   ✅ 출퇴근 기록에서도 제외 완료
```

## 참고 문서

- **계산 수식**: `docs/calculation_formulas.md`
- **완료 요약**: `docs/COMPLETION_SUMMARY.md`
- **To-do 리스트**: `docs/To_do_list1.md`

## 지원

문제가 발생하면 GitHub Issues에 보고해주세요.
