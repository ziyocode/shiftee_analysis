# "계산" 시트 로직 Python 구현 계획

`레포트_20251101-1130_뱅킹인프라본부.xlsx` 파일의 `계산` 시트 로직을 Python으로 구현하기 위한 분석 및 계획입니다.

## 1. 개요

- **목표**: 엑셀의 `계산` 시트에 있는 모든 주요 컬럼의 수식을 Python (`pandas`) 코드로 정확히 재현.
- **활용**: 생성된 데이터는 향후 리포트 생성 또는 위험 분석에 사용.

## 2. 컬럼별 상세 로직 구현 계획

| 컬럼 (엑셀) | 항목 | Python 변수명 | 계산 로직 / 수식 매핑 | 비고 |
| :--- | :--- | :--- | :--- | :--- |
| **B** | 직원 | `name` | `shiftee_data1['직원']` | Primary Key |
| **C** | 본조직 | `dept` | `shiftee_data1['본조직']` | |
| **D** | 소정근로시간 | `contract_hours` | `shiftee_data1['소정근로시간']` | |
| **E** | 승인된 근로시간 | `approved_hours` | `shiftee_data1['승인된 근로시간']` | |
| **F** | 실제 근로시간 | `actual_hours_raw` | `shiftee_data1['실제 근로시간']` | (결근/퇴근누락 미포함 값) |
| **G** | 실제 근로시간(보정) | `actual_hours_corr` | `Payroll_Sum + Absent*8 + Missing*8` | **핵심 로직** (아래 구현 상세 참조) |
| **H** | 실제 근로시간(단순) | `actual_hours_simple` | `shiftee_data1['실제 근로시간'] + Absent*8 + Missing*8` | 보정 로직과 비교용 |
| **K** | 유급휴가시간 | `paid_leave` | `shiftee_data1['유급휴가시간']` | |
| **L** | 법정근로시간 | `legal_hours` | `contract_hours - paid_leave` | `D - K` |
| **M** | 실제 초과근로 | `overtime_real` | `actual_hours_raw - legal_hours` | `F - L` (음수는 0처리) |
| **N** | 실제 초과근로(보정) | `overtime_corr` | `actual_hours_corr - legal_hours` | `G - L` (음수는 0처리) |
| **O** | 실제 초과근로(최종) | `overtime_final` | `IF(...)` 복합 로직 | `H`와 `N` 비교 및 이상치 처리 |
| **P** | 조기출근 합산 | `early_arrival` | `overtime_corr - overtime_final` | `N - O` |
| **Q** | 법정 초과 한도 | `limit_hours` | `(Day / 7) * 12` | 날짜 경과에 따른 한도 |
| **R** | 월 법규 위반 기준 | `monthly_limit` | `12 * 4.3` (약 51.6 ~ 52) | 고정값 |
| **S** | 월말까지 가능시간 | `remaining_hours` | `limit_hours - overtime_final` | `Q - O` |
| **T** | 월말까지 가능(누적) | `remaining_total` | `52 - overtime_final` | (추정) |
| **U** | 적정성 | `status` | `IF(O > Q, "위험", "정상")` | 위험 여부 판단 |
| **V** | 법규 기준초과자 | `legal_violation` | `IF(O >= R, "법기준초과", "")` | |

## 3. 핵심 구현 로직 (G열 등)

### 3.1 G열: 실제 근로시간 (결근, 퇴근누락 포함, 정밀 계산)
- **소스**: `shiftee_data2` (Payroll)
- **로직**:
    ```python
    def calculate_precise_work_hours(payroll_df, name):
        # 1. 해당 직원의 Payroll 기록 필터링
        records = payroll_df[payroll_df['이름'] == name]
        total_hours = 0
        for record in records:
            # 퇴근시간 - 출근시간 (분 단위 절삭 로직 적용 가능성 있음, 엑셀 수식 확인 필요)
            # 수식: (INT(퇴근*1440)/1440 - INT(출근*1440)/1440)*24 - 휴게시간
            work = (floor(end) - floor(start)) - break
            total_hours += work
        return total_hours
    
    # 2. 결근/퇴근누락 패널티 추가
    g_value = total_hours + (absent_count * 8) + (missing_count * 8)
    ```

### 3.2 O열: 실제 초과근로 (최종)
- **엑셀 수식**: `IF(OR((H-L)>N, H>300), N, IF((H-L)<0, 0, H-L))`
- **해석**:
    - `H(단순계산)`가 `N(보정계산)`보다 크거나, `H`가 비정상적으로 크면(300초과), `N(보정계산)`을 사용.
    - 그렇지 않으면 `H - L`(단순 초과) 사용.
    - 음수 방어 로직 포함.

## 4. 구현 방안

- **Module**: `src.shiftee.calculator` (신규 생성)
- **Methods**:
    - `calculate_full_metrics(realtime_df, payroll_df)` -> `pd.DataFrame`
- **Output**:
    - 계산된 모든 컬럼을 포함하는 DataFrame 반환.
    - 엑셀 파일로 저장 기능 제공.

## 5. 실행 계획

1. `src/shiftee/calculator.py` 생성.
2. 위 로직을 Pandas vectorized 연산 또는 apply 함수로 구현.
3. `cli.py`에 `calculate` 명령어 추가 (디버깅용).
