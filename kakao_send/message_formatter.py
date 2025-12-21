"""위험 직원 목록 메시지 포맷터

DataFrame의 위험 직원 데이터를 카카오톡 메시지 형식으로 변환합니다.
"""

import pandas as pd
from datetime import datetime


def format_risk_message(
    df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime,
    show_all: bool = False,
) -> str:
    """위험 직원 목록을 카카오톡 메시지 형식으로 변환

    Args:
        df: 분석 결과 DataFrame
        start_date: 분석 시작 날짜
        end_date: 분석 종료 날짜
        show_all: True이면 전체 직원 목록, False이면 위험 직원만 (기본값: False)

    Returns:
        str: 카카오톡 메시지 형식의 문자열
    """
    # 날짜 포맷
    period = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

    # 통계 계산
    total_count = len(df)
    risk_count = len(df[df["U_적정성"] == "위험"])
    violation_count = len(df[df["V_법규기준초과자"] == "법기준초과"])
    normal_count = total_count - risk_count - violation_count

    # 메시지 헤더
    message = f"""📊 초과근로 적정성 분석 결과
📅 분석 기간:
   {period}

━━━━━━━━━━━━━━
📈 전체 현황
━━━━━━━━━━━━━━
총 직원: {total_count}명
  ✅ 정상: {normal_count}명 ({normal_count/total_count*100:.1f}%)
  ⚠️ 위험: {risk_count}명 ({risk_count/total_count*100:.1f}%)
  🚨 법규기준초과: {violation_count}명 ({violation_count/total_count*100:.1f}%)
"""

    # 위험 직원 목록
    if risk_count > 0 or violation_count > 0:
        message += "\n━━━━━━━━━━━━━━\n"
        message += "⚠️ 주의 필요 직원 목록\n"
        message += "━━━━━━━━━━━━━━\n"

        # 법규초과 직원 먼저 표시
        violation_df = df[df["V_법규기준초과자"] == "법기준초과"]
        if len(violation_df) > 0:
            message += "\n🚨 법규기준 초과자:\n"
            for idx, row in violation_df.iterrows():
                message += (
                    f"  • 🔥 {row['B_직원']} ({row['C_본조직']})\n"
                    f"    초과근로: {row['O_실제초과근로_조기출근제외']:.2f}h / "
                    f"법규기준: {row['R_법규위반_전일까지']:.2f}h\n"
                )

        # 위험 직원 표시
        risk_only_df = df[
            (df["U_적정성"] == "위험") & (df["V_법규기준초과자"] != "법기준초과")
        ]
        if len(risk_only_df) > 0:
            message += "\n⚠️ 위험 직원:\n"
            for idx, row in risk_only_df.iterrows():
                message += (
                    f"  • {row['B_직원']} ({row['C_본조직']})\n"
                    f"    초과근로: {row['O_실제초과근로_조기출근제외']:.2f}h / "
                    f"법정기준: {row['Q_법정초과근로시간']:.2f}h\n"
                )

    # 전체 직원 목록 (옵션)
    if show_all and total_count > 0:
        message += "\n━━━━━━━━━━━━━━\n"
        message += "📋 전체 직원 목록\n"
        message += "━━━━━━━━━━━━━━\n"
        for idx, row in df.iterrows():
            status_icon = "✅"
            if row["V_법규기준초과자"] == "법기준초과":
                status_icon = "🚨"
            elif row["U_적정성"] == "위험":
                status_icon = "⚠️"

            message += (
                f"{status_icon} {row['B_직원']} ({row['C_본조직']})\n"
                f"   초과근로: {row['O_실제초과근로_조기출근제외']:.2f}h\n"
            )

    message += "\n━━━━━━━━━━━━━━\n"
    message += f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return message


def format_summary_message(
    df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime,
) -> str:
    """요약 메시지만 생성 (위험 직원 목록 제외)

    Args:
        df: 분석 결과 DataFrame
        start_date: 분석 시작 날짜
        end_date: 분석 종료 날짜

    Returns:
        str: 요약 메시지
    """
    period = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

    total_count = len(df)
    risk_count = len(df[df["U_적정성"] == "위험"])
    violation_count = len(df[df["V_법규기준초과자"] == "법기준초과"])
    normal_count = total_count - risk_count - violation_count

    message = f"""📊 초과근로 적정성 분석 완료

📅 기간: {period}

총 {total_count}명
✅ 정상: {normal_count}명 ({normal_count/total_count*100:.1f}%)
⚠️ 위험: {risk_count}명 ({risk_count/total_count*100:.1f}%)
🚨 법규초과: {violation_count}명 ({violation_count/total_count*100:.1f}%)

생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

    return message
