"""GUI 모드 메인 엔트리포인트.

Windows .exe 배포용 GUI 진입점입니다.
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import traceback

# Playwright 브라우저 경로 설정 (PyInstaller 빌드용)
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 경우
    application_path = Path(sys.executable).parent
    # ms-playwright 폴더가 실행 파일과 같은 위치에 있음
    playwright_browsers_path = application_path / "ms-playwright"
    if playwright_browsers_path.exists():
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(playwright_browsers_path)

# GUI 로그인 - 절대 import로 변경
from shiftee.gui_login import get_credentials
from shiftee.settings import ShifteeSettings
from shiftee.cli import (
    download_shiftee_data,
    load_shiftee_data1,
    load_shiftee_data2,
    load_shiftee_leave_data,
    calculate_basic_columns,
    calculate_g_column,
    calculate_h_column,
    calculate_i_j_l_columns,
    calculate_overtime_columns,
    calculate_legal_limits_and_risk,
    calculate_remaining_compensatory_leave,
    print_summary,
    print_risk_employees,
    print_remaining_leave,
    save_to_excel,
)
from shiftee.html_report import generate_html_report


def run_gui_mode():
    """GUI 모드로 실행."""
    print("\n" + "=" * 80)
    print("  Shiftee 근무 데이터 분석 도구 (GUI 모드)")
    print("=" * 80 + "\n")

    # GUI로 로그인 정보 입력받기
    credentials = get_credentials()

    if not credentials:
        print("로그인이 취소되었습니다.")
        return 1

    user_id, password, team_filter_list = credentials

    # 임시 환경변수 설정
    os.environ['SHIFTEE_ID'] = user_id
    os.environ['SHIFTEE_PASSWORD'] = password
    if team_filter_list:
        os.environ['SHIFTEE_TEAM_FILTER'] = ','.join(team_filter_list)

    # 날짜 설정 (이번 달 1일 ~ 어제)
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1)
    end_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    # 출력 디렉토리 생성
    data_dir = Path("data")
    output_dir = Path("output")
    data_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    try:
        print("\n1️⃣  Shiftee 데이터 다운로드 중...\n")

        # 데이터 다운로드
        settings = ShifteeSettings()
        data1_path, data2_path, leave_path = asyncio.run(
            download_shiftee_data(start_date, end_date, data_dir)
        )

        print("\n2️⃣  데이터 분석 중...\n")
        print("=" * 80)
        print("🚀 Shiftee 적정성 위험 판정")
        print("=" * 80 + "\n")

        # 데이터 로드
        print("📂 1단계: 데이터 로드")
        df1 = load_shiftee_data1(data1_path)
        df2 = load_shiftee_data2(data2_path)

        # 팀 필터 적용
        if team_filter_list and "본조직" in df1.columns:
            before = len(df1)
            df1 = df1[df1["본조직"].isin(team_filter_list)].copy()
            excluded = before - len(df1)
            if excluded:
                team_label = ", ".join(team_filter_list)
                print(f"🏢 [{team_label}] 필터: {len(df1)}명 대상 (타 조직 {excluded}명 제외)")
                if "이름" in df2.columns and "직원" in df1.columns:
                    target_employees = df1["직원"].tolist()
                    df2 = df2[df2["이름"].isin(target_employees)].copy()

        # 직무 제외
        if settings.exclude_role and "본직무" in df1.columns:
            shift_workers = df1[df1["본직무"] == settings.exclude_role]["직원"].tolist() if "직원" in df1.columns else []
            df1 = df1[df1["본직무"] != settings.exclude_role].copy()
            if shift_workers:
                print(f"⚠️  {settings.exclude_role} 직원 {len(shift_workers)}명 제외")
                if "이름" in df2.columns:
                    df2 = df2[~df2["이름"].isin(shift_workers)].copy()

        # 계산 수행
        print("\n🔢 2단계: 계산 수행")
        df = calculate_basic_columns(df1)
        df = calculate_g_column(df)
        df = calculate_h_column(df, df1, df2)
        df = calculate_i_j_l_columns(df)
        df = calculate_overtime_columns(df)
        df = calculate_legal_limits_and_risk(df, start_date, end_date)

        # 결과 출력
        print_summary(df)
        print_risk_employees(df)

        # 잔여 대체휴가 계산
        leave_summary = None
        if leave_path.exists():
            df_leave = load_shiftee_leave_data(leave_path)
            leave_summary = calculate_remaining_compensatory_leave(df1, df_leave)
            print_remaining_leave(leave_summary)

        # Excel 저장
        print("\n💾 3️⃣  결과 저장 중...")
        save_to_excel(df, output_path, start_date, end_date, leave_df=leave_summary)

        # HTML 보고서 생성
        html_path = output_path.with_suffix('.html')
        generate_html_report(df, html_path, start_date, end_date, leave_df=leave_summary)

        print("\n" + "=" * 80)
        print("✅ 분석 완료!")
        print("=" * 80)
        print(f"\n📊 Excel 리포트: {output_path.absolute()}")
        print(f"📄 HTML 보고서: {html_path.absolute()}")
        print(f"📁 데이터 위치: {data_dir.absolute()}")
        print("\n아무 키나 누르면 종료됩니다...")
        input()

        return 0

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ 오류 발생")
        print("=" * 80)
        print(f"\n{e}")
        print("\n상세 오류:")
        traceback.print_exc()
        print("\n아무 키나 누르면 종료됩니다...")
        input()
        return 1


def main():
    """GUI 메인 함수."""
    return run_gui_mode()


if __name__ == "__main__":
    sys.exit(main())
