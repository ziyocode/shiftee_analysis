# 계산 시트 열 매핑 분석 결과

## 📊 분석 일자
- 날짜: 2024-12-17
- 분석 파일: `data/레포트_20251101-1130_뱅킹인프라본부.xlsx`
- 대상 시트: "계산"

---

## 🔍 전체 열 구조 (A~X열)

| 열 | 헤더명 | 데이터 소스 / 수식 |
|----|--------|-------------------|
| A | (비어있음) | - |
| **B** | 직원 | `=shiftee데이타!B2` |
| **C** | 본조직 | `=shiftee데이타!C2` |
| **D** | 소정근로시간 | `=shiftee데이타!G2` |
| **E** | 승인된 근로시간 | `=shiftee데이타!H2` |
| **F** | 실제 근로시간 | `=shiftee데이타!J2` |
| **G** | 실제 근로시간(결근,퇴근누락포함) | `=shiftee데이타!J2+shiftee데이타!W2*8+shiftee데이타!X2*8` (추정) |
| **H** | 실제 근로시간(결근,퇴근누락포함) 실제퇴근시간-출근등록시간 | SUMPRODUCT 수식 (shiftee데이타2 사용) |
| **I** | 표준 근로시간 | `=shiftee데이타!K2+shiftee데이타!T2` (추정) |
| **J** | 표준 근로시간(결근,퇴근누락포함) | 표준 근로시간 + 결근*8 + 퇴근누락*8 |
| **K** | 유급휴가시간 | `=shiftee데이타!L2` |
| **L** | 법정근로시간 | `=D2-I2` (소정근로시간 - 표준근로시간) |
| **M** | 실제 초과근로시간 | `=IF((F2-K2)<0,0,F2-K2)` |
| **N** | 실제 초과근로시간(결근,퇴근누락포함) | `=IF((G2-L2)<0,0,G2-L2)` |
| **O** | 실제 초과근로시간(결근,퇴근누락포함,조기출근제외) | `=IF(OR((H2-L2)>N2,H2>300),N2,IF((H2-L2)<0,0,H2-L2))` |
| **P** | 조기출근 합산 | `=N2-O2` |
| **Q** | 법정 초과 근로시간 | `=DAY($X$1)/7*10` |
| **R** | 법규 위반(전일까지) | `=DAY($X$1)/7*12` |
| **S** | 월법규 위반시간 | `=12*4.3` |
| **T** | 월말까지 가능한 초과근로시간 | `=IF((S2-O2)<0,"가능시간없음",S2-O2)` |
| **U** | 적정성 | `=IF(O2>Q2,"위험","정상")` ⚠️ |
| **V** | 법규 기준초과자 | `=IF(AND(O2<>0,O2>=R2),"법기준초과","")` |
| **W** | 167 | 상수 (용도 불명) |
| **X** | 2025-11-30 00:00:00 | 월의 마지막 날짜 (기준일) |

---

## 🎯 핵심 계산 로직 상세 분석

### 1. D열: 소정근로시간
```excel
=shiftee데이타!G2
```
**의미**: 원본 데이터(shiftee_data1.xlsx)의 G열
**Python**: `df1['소정근로시간']`

### 2. F열: 실제 근로시간
```excel
=shiftee데이타!J2
```
**의미**: 원본 데이터(shiftee_data1.xlsx)의 J열
**Python**: `df1['실제 근로시간']`

### 3. N열: 실제 초과근로시간(결근,퇴근누락포함)
```excel
=IF((G2-L2)<0,0,G2-L2)
```
**의미**:
- G열(실제 근로시간 결근/퇴근누락포함) - L열(법정근로시간)
- 음수면 0으로 처리

**Python**:
```python
df['실제_초과근로시간_결근포함'] = df.apply(
    lambda row: max(0, row['G'] - row['L']), axis=1
)
```

### 4. O열: 실제 초과근로시간(결근,퇴근누락포함,조기출근제외) ⭐
```excel
=IF(OR((H2-L2)>N2,H2>300),N2,IF((H2-L2)<0,0,H2-L2))
```
**의미**:
- H열(실제퇴근-출근 기반 근로시간) - L열(법정근로시간)
- 조건 1: (H-L) > N 또는 H > 300 → N 사용
- 조건 2: (H-L) < 0 → 0
- 그 외: H - L

**Python**:
```python
def calculate_overtime_excluding_early(row):
    h_minus_l = row['H'] - row['L']
    if h_minus_l > row['N'] or row['H'] > 300:
        return row['N']
    elif h_minus_l < 0:
        return 0
    else:
        return h_minus_l

df['O'] = df.apply(calculate_overtime_excluding_early, axis=1)
```

### 5. Q열: 법정 초과 근로시간 📅
```excel
=DAY($X$1)/7*10
```
**의미**:
- X1 셀: 월의 마지막 날짜 (예: 2025-11-30)
- DAY(): 날짜에서 일(day) 추출 → 30
- 30 / 7 * 10 = 42.857... 시간

**Python**:
```python
from datetime import datetime
import calendar

# 월의 마지막 날짜 계산
year, month = 2025, 11
last_day = calendar.monthrange(year, month)[1]  # 30

법정_초과근로시간 = last_day / 7 * 10  # 42.857...
```

### 6. R열: 법규 위반(전일까지) 📅
```excel
=DAY($X$1)/7*12
```
**의미**:
- 30 / 7 * 12 = 51.428... 시간

**Python**:
```python
법규_위반_전일까지 = last_day / 7 * 12  # 51.428...
```

### 7. S열: 월법규 위반시간
```excel
=12*4.3
```
**의미**:
- 고정값: 12 * 4.3 = 51.6 시간

**Python**:
```python
월법규_위반시간 = 12 * 4.3  # 51.6
```

---

## ⚠️ 적정성 판정 로직 (최종 목표)

### U열: 적정성
```excel
=IF(O2>Q2,"위험","정상")
```

**판정 기준**:
- **O열** (실제 초과근로시간, 결근/퇴근누락포함, 조기출근제외) > **Q열** (법정 초과근로시간)
- 초과 → "위험"
- 미초과 → "정상"

**실제 값 예시 (11월 30일 기준)**:
- Q열 = 30/7*10 = **42.857 시간**
- 직원 A의 O열 = 26.73시간 → **정상** ✅
- 직원 B의 O열 = 45.00시간 → **위험** ⚠️

**Python 구현**:
```python
def calculate_risk_status(row, legal_overtime_limit):
    """적정성 판정"""
    if row['O'] > legal_overtime_limit:
        return "위험"
    else:
        return "정상"

df['적정성'] = df.apply(
    lambda row: calculate_risk_status(row, 법정_초과근로시간),
    axis=1
)

# 위험 직원 필터링
risk_employees = df[df['적정성'] == '위험']
```

---

## 📋 shiftee_data1.xlsx 열 매핑

| 계산 시트 | shiftee_data1.xlsx | 헤더명 |
|-----------|-------------------|--------|
| D열 | G열 | 소정근로시간 |
| E열 | H열 | 승인된 근로시간 |
| F열 | J열 | 실제 근로시간 |
| I열 | K열 + T열 | 표준 근로시간 + 표준 최대 잔여유급시간 |
| K열 | L열 | 유급휴가시간 |
| - | W열 | 결근 |
| - | X열 | 퇴근누락 |

---

## 📋 shiftee_data2.xlsx 활용

H열 계산에 사용 (SUMPRODUCT 수식):
```excel
=SUMPRODUCT(
    (shiftee_data2!M$5:M$5000<>"") *
    ((INT(shiftee_data2!M$5:M$5000*1440)/1440 - INT(shiftee_data2!I$5:I$5000*1440)/1440)*24 - shiftee데이타2!S$5:S$5000*24) *
    (shiftee_data2!B$5:B$5000=B10)
) + shiftee_data!W10*8 + shiftee_data!X10*8
```

**의미**:
- B열: 직원명 (필터링 키)
- I열: 출근등록시간
- M열: 실제퇴근시간
- S열: 휴게/제외시간
- 계산: (퇴근시간 - 출근시간) - 휴게시간

---

## 🔑 핵심 발견 사항

### 1. To_do_list1.md의 열 참조 오류 확정
To_do_list1.md에 명시된 열 참조가 일부 잘못되었음:

| To_do_list1.md | 실제 (계산 시트) | 비고 |
|----------------|-----------------|------|
| D열 = 소정근로시간(K열) | D열 = 소정근로시간(G열) | ❌ 오류 |
| F열 = 승인된근로시간-유급휴가 | F열 = 실제근로시간(J열) | ❌ 오류 |
| N열 = 법정초과근로시간 | N열 = 실제초과근로(결근포함) | ❌ 오류 |

**정정**: To_do_list1.md의 계산식이 아닌 **실제 Excel 수식**을 따라야 함

### 2. 필수 계산 단계
1. **G열**: 실제 근로시간(결근,퇴근누락포함) = `J + W*8 + X*8`
2. **H열**: shiftee_data2에서 일별 근무시간 합산 (복잡한 SUMPRODUCT)
3. **L열**: 법정근로시간 = `D - I`
4. **N열**: 실제 초과근로(결근포함) = `max(0, G - L)`
5. **O열**: 실제 초과근로(조기출근제외) = 조건부 계산
6. **Q열**: 법정 초과근로시간 = `월말일 / 7 * 10`
7. **U열**: 적정성 = `"위험" if O > Q else "정상"`

### 3. 복잡도 평가
- **단순 계산**: D, E, F, K, L, M, Q, R, S열 → pandas로 직접 계산 가능
- **중간 복잡도**: G, I, J, N, O열 → 조건부 계산 필요
- **높은 복잡도**: H열 → shiftee_data2와 조인 후 SUMPRODUCT 로직 구현 필요

---

## ✅ 다음 단계: Python 구현 계획

### Phase 2-1: 기본 데이터 로드
```python
def load_shiftee_data1(file_path: Path) -> pd.DataFrame:
    """shiftee_data1.xlsx 로드"""
    # 날짜 범위 시트 찾기 (예: 20251101-20251130)
    ...

def load_shiftee_data2(file_path: Path) -> pd.DataFrame:
    """shiftee_data2.xlsx 로드"""
    # 헤더는 3번째 행 (header_row=2)
    ...
```

### Phase 2-2: 단계별 계산 함수
```python
def calculate_column_D_to_K(df1: pd.DataFrame) -> pd.DataFrame:
    """D~K열: 기본 시간 데이터"""
    df = pd.DataFrame()
    df['B_직원'] = df1['직원']
    df['C_본조직'] = df1['본조직']
    df['D_소정근로시간'] = df1['소정근로시간']  # G열
    df['E_승인된근로시간'] = df1['승인된 근로시간']  # H열
    df['F_실제근로시간'] = df1['실제 근로시간']  # J열
    df['K_유급휴가시간'] = df1['유급휴가시간']  # L열
    return df

def calculate_column_G(df: pd.DataFrame, df1: pd.DataFrame) -> pd.DataFrame:
    """G열: 실제 근로시간(결근,퇴근누락포함)"""
    df['G'] = df1['실제 근로시간'] + df1['결근'] * 8 + df1['퇴근누락'] * 8
    return df

def calculate_column_H(df: pd.DataFrame, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """H열: SUMPRODUCT 로직 구현 (복잡)"""
    # shiftee_data2에서 직원별 일별 근무시간 합산
    ...

def calculate_overtime_columns(df: pd.DataFrame, month_last_day: int) -> pd.DataFrame:
    """N, O, Q, R, S, U열: 초과근로 및 적정성 판정"""
    # N열
    df['N'] = df.apply(lambda row: max(0, row['G'] - row['L']), axis=1)

    # O열 (핵심)
    def calc_o(row):
        h_minus_l = row['H'] - row['L']
        if h_minus_l > row['N'] or row['H'] > 300:
            return row['N']
        elif h_minus_l < 0:
            return 0
        else:
            return h_minus_l
    df['O'] = df.apply(calc_o, axis=1)

    # Q, R, S열 (법규 기준)
    df['Q'] = month_last_day / 7 * 10
    df['R'] = month_last_day / 7 * 12
    df['S'] = 12 * 4.3

    # U열 (적정성 판정)
    df['U_적정성'] = df['O'].apply(lambda x: "위험" if x > df['Q'].iloc[0] else "정상")

    return df
```

### Phase 2-3: 메인 워크플로우
```python
def main():
    # 1. 데이터 로드
    df1 = load_shiftee_data1("data/shiftee_data1.xlsx")
    df2 = load_shiftee_data2("data/shiftee_data2.xlsx")

    # 2. 단계별 계산
    df = calculate_column_D_to_K(df1)
    df = calculate_column_G(df, df1)
    df = calculate_column_H(df, df1, df2)
    df = calculate_column_I_J_L(df, df1)

    # 월의 마지막 날 계산
    import calendar
    year, month = 2025, 11
    last_day = calendar.monthrange(year, month)[1]

    df = calculate_overtime_columns(df, last_day)

    # 3. 위험 직원 필터링
    risk_employees = df[df['U_적정성'] == '위험']

    # 4. 결과 출력
    print_risk_report(risk_employees)
```

---

## 📝 결론

### ✅ 분석 완료
- 모든 불명확한 열(D, F, N, O, Q, R, S)의 수식 확인 완료
- 적정성 판정 로직 명확히 파악: `O > Q → "위험"`

### 🎯 구현 가능성
- **가능**: D~F, K~S, U열 → pandas로 구현 가능
- **도전적**: H열 → SUMPRODUCT 로직의 Python 변환 필요

### 🚧 다음 작업
1. ✅ `scripts/calculate_risk_direct.py` 스크립트 작성 시작
2. ⏳ H열 SUMPRODUCT 로직 Python 구현
3. ⏳ 기존 레포트와 결과 비교 검증
4. ⏳ CLI 인터페이스 및 문서화

---

## 📚 참고 자료
- 원본 레포트: `data/레포트_20251101-1130_뱅킹인프라본부.xlsx`
- To_do_list: `docs/To_do_list1.md` (일부 열 참조 오류 있음)
- 작업 계획: `docs/task1.md`
