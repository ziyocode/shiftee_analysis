#!/usr/bin/env python3
"""특정 직원의 근무시간 계산 상세 분석 스크립트

강희대님의 실제근로시간(퇴근출근기반) 계산 과정을 상세히 출력합니다.
"""
import sys
from pathlib import Path
from datetime import datetime, time, timedelta
import pandas as pd

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def to_excel_serial(dt_value):
    """datetime/float를 Excel serial date로 변환"""
    if isinstance(dt_value, datetime):
        excel_epoch = datetime(1899, 12, 30)
        delta = dt_value - excel_epoch
        return delta.total_seconds() / 86400
    elif isinstance(dt_value, (int, float)):
        return dt_value
    else:
        return 0


def calculate_work_hours_debug(row, row_num):
    """각 행의 근무시간 계산 - 디버깅 정보 포함"""
    try:
        start = row["시작시간"]
        end = row["퇴근시간"]
        rest = row["휴게시간"]

        # 1. Excel serial date 변환
        start_serial = to_excel_serial(start)
        end_serial = to_excel_serial(end)

        # 2. INT(time*1440)/1440 로직
        start_minutes = int(start_serial * 1440)
        start_day = start_minutes / 1440

        end_minutes = int(end_serial * 1440)
        end_day = end_minutes / 1440

        # 3. 휴게시간 처리
        rest_hours = 0
        if rest is not None:
            if isinstance(rest, time):
                rest_hours = rest.hour + rest.minute / 60 + rest.second / 3600
            elif isinstance(rest, timedelta):
                rest_hours = rest.total_seconds() / 3600
            elif isinstance(rest, (int, float)):
                rest_hours = rest * 24
            else:
                rest_hours = 0

        # 4. 근무시간 계산
        work_hours = (end_day - start_day) * 24 - rest_hours
        work_hours = max(0, work_hours)

        # 디버깅 정보 출력
        print(f"\n  [{row_num}] 출근: {start}, 퇴근: {end}")
        print(f"      → Excel serial: {start_serial:.6f} ~ {end_serial:.6f}")
        print(f"      → 분 단위 절삭: {start_day:.6f} ~ {end_day:.6f}")
        print(f"      → 휴게시간: {rest_hours:.2f}h")
        print(f"      → 근무시간: ({end_day:.6f} - {start_day:.6f}) * 24 - {rest_hours:.2f} = {work_hours:.2f}h")

        return work_hours

    except Exception as e:
        print(f"\n  [{row_num}] ❌ 계산 오류: {e}")
        return 0


def analyze_employee(employee_name: str, start_date: str, end_date: str, data_dir: str = "data"):
    """특정 직원의 근무시간 계산 과정 분석

    Args:
        employee_name: 직원 이름
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        data_dir: 데이터 디렉토리
    """
    print("=" * 80)
    print(f"🔍 {employee_name} 님 근무시간 분석")
    print("=" * 80)
    print(f"📅 기간: {start_date} ~ {end_date}\n")

    # 날짜 파싱
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # 데이터 파일 찾기
    data_path = Path(data_dir)
    excel_files = sorted(data_path.glob("*.xlsx"))

    if not excel_files:
        print(f"❌ {data_dir}/ 디렉토리에 Excel 파일이 없습니다.")
        return

    # 가장 최근 파일 사용
    latest_file = excel_files[-1]
    print(f"📂 파일: {latest_file.name}\n")

    # Excel 파일 읽기
    try:
        df1 = pd.read_excel(latest_file, sheet_name="shiftee_data1")
        df2 = pd.read_excel(latest_file, sheet_name="shiftee_data2")
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}")
        return

    # shiftee_data1에서 직원 정보 찾기
    employee_row = df1[df1["이름"] == employee_name]

    if employee_row.empty:
        print(f"❌ '{employee_name}' 직원을 찾을 수 없습니다.")
        print(f"📋 가능한 직원 목록:")
        for name in sorted(df1["이름"].unique()):
            print(f"   - {name}")
        return

    # 직원 기본 정보
    emp_data = employee_row.iloc[0]
    print("=" * 80)
    print("📋 기본 정보 (shiftee_data1)")
    print("=" * 80)
    print(f"이름: {emp_data['이름']}")
    print(f"소정근로시간 (D): {emp_data.get('소정근로시간', 'N/A')}")
    print(f"실제근로시간 (F): {emp_data.get('실제 근로시간', 'N/A')}")
    print(f"결근: {emp_data.get('결근', 0)}일")
    print(f"퇴근누락: {emp_data.get('퇴근누락', 0)}일")

    absence_penalty = emp_data.get('결근', 0) * 8 + emp_data.get('퇴근누락', 0) * 8
    print(f"\n📊 페널티 시간: {emp_data.get('결근', 0)}일*8 + {emp_data.get('퇴근누락', 0)}일*8 = {absence_penalty}h")

    # shiftee_data2에서 출퇴근 기록 찾기
    attendance_records = df2[df2["이름"] == employee_name].copy()
    attendance_records = attendance_records[attendance_records["퇴근시간"].notna()]

    print("\n" + "=" * 80)
    print(f"📅 출퇴근 기록 (shiftee_data2) - 총 {len(attendance_records)}건")
    print("=" * 80)

    if attendance_records.empty:
        print("❌ 출퇴근 기록이 없습니다.")
        print(f"\n⚠️  결론: H열 = 0 + {absence_penalty}h(페널티) = {absence_penalty}h")
        return

    # 각 기록별 근무시간 계산
    df2_filtered = attendance_records[["이름", "근무일정\n시작시간", "퇴근시간", "(실제)\n총 휴게시간"]].copy()
    df2_filtered.columns = ["직원명", "시작시간", "퇴근시간", "휴게시간"]

    total_hours = 0
    for idx, (_, row) in enumerate(df2_filtered.iterrows(), 1):
        hours = calculate_work_hours_debug(row, idx)
        total_hours += hours

    print("\n" + "=" * 80)
    print("📊 최종 계산")
    print("=" * 80)
    print(f"출퇴근 기록 합계: {total_hours:.2f}h")
    print(f"페널티 (결근+퇴근누락): {absence_penalty}h")
    print(f"H열 (실제근로시간_퇴근출근기반): {total_hours:.2f} + {absence_penalty} = {total_hours + absence_penalty:.2f}h")

    print("\n" + "=" * 80)
    print("✅ 분석 완료")
    print("=" * 80)


if __name__ == "__main__":
    # 기본값
    employee = "강희대"
    start = "2025-12-01"
    end = "2025-12-19"

    # 명령행 인자가 있으면 사용
    if len(sys.argv) >= 2:
        employee = sys.argv[1]
    if len(sys.argv) >= 3:
        start = sys.argv[2]
    if len(sys.argv) >= 4:
        end = sys.argv[3]

    analyze_employee(employee, start, end)
