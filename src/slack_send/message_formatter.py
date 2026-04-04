"""Slack용 메시지 포맷터.

DataFrame의 위험 직원 데이터를 Slack mrkdwn 형식으로 변환합니다.
"""

import pandas as pd
from datetime import datetime


def format_slack_message(
    df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime,
    show_all: bool = False,
) -> str:
    """위험 직원 목록을 Slack mrkdwn 형식으로 변환."""
    period = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

    total_count = len(df)
    risk_count = len(df[df["U_적정성"] == "위험"])
    violation_count = len(df[df["V_법규기준초과자"] == "법기준초과"])
    normal_count = total_count - risk_count - violation_count

    msg = f":bar_chart: *초과근로 적정성 분석 결과*\n"
    msg += f":calendar: 분석 기간: {period}\n\n"
    msg += f"*전체 현황*\n"
    msg += f"총 직원: {total_count}명\n"
    msg += f">:white_check_mark: 정상: {normal_count}명 ({normal_count/total_count*100:.1f}%)\n"
    msg += f">:warning: 위험: {risk_count}명 ({risk_count/total_count*100:.1f}%)\n"
    msg += f">:rotating_light: 법규기준초과: {violation_count}명 ({violation_count/total_count*100:.1f}%)\n"

    if risk_count > 0 or violation_count > 0:
        msg += "\n---\n"
        msg += ":warning: *주의 필요 직원 목록*\n\n"

        violation_df = df[df["V_법규기준초과자"] == "법기준초과"]
        if len(violation_df) > 0:
            msg += ":rotating_light: *법규기준 초과자:*\n"
            for _, row in violation_df.iterrows():
                msg += (
                    f"• :fire: *{row['B_직원']}* ({row['C_본조직']})\n"
                    f"   초과근로: {row['O_실제초과근로_조기출근제외']:.2f}h / "
                    f"법규기준: {row['R_법규위반_전일까지']:.2f}h\n"
                )

        risk_only_df = df[
            (df["U_적정성"] == "위험") & (df["V_법규기준초과자"] != "법기준초과")
        ]
        if len(risk_only_df) > 0:
            msg += "\n:warning: *위험 직원:*\n"
            for _, row in risk_only_df.iterrows():
                msg += (
                    f"• *{row['B_직원']}* ({row['C_본조직']})\n"
                    f"   초과근로: {row['O_실제초과근로_조기출근제외']:.2f}h / "
                    f"법정기준: {row['Q_법정초과근로시간']:.2f}h\n"
                )

    if show_all and total_count > 0:
        msg += "\n---\n"
        msg += ":clipboard: *전체 직원 목록*\n"
        for _, row in df.iterrows():
            if row["V_법규기준초과자"] == "법기준초과":
                icon = ":rotating_light:"
            elif row["U_적정성"] == "위험":
                icon = ":warning:"
            else:
                icon = ":white_check_mark:"

            msg += (
                f"{icon} {row['B_직원']} ({row['C_본조직']})"
                f" — 초과근로: {row['O_실제초과근로_조기출근제외']:.2f}h\n"
            )

    msg += f"\n_생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
    return msg


def format_slack_summary(
    df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime,
) -> str:
    """요약 메시지만 생성 (위험 직원 목록 제외)."""
    period = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

    total_count = len(df)
    risk_count = len(df[df["U_적정성"] == "위험"])
    violation_count = len(df[df["V_법규기준초과자"] == "법기준초과"])
    normal_count = total_count - risk_count - violation_count

    msg = f":bar_chart: *초과근로 적정성 분석 완료*\n"
    msg += f":calendar: 기간: {period}\n\n"
    msg += f"총 {total_count}명\n"
    msg += f">:white_check_mark: 정상: {normal_count}명 ({normal_count/total_count*100:.1f}%)\n"
    msg += f">:warning: 위험: {risk_count}명 ({risk_count/total_count*100:.1f}%)\n"
    msg += f">:rotating_light: 법규초과: {violation_count}명 ({violation_count/total_count*100:.1f}%)\n"
    msg += f"\n_생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
    return msg
