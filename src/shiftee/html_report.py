"""HTML 보고서 생성 모듈.

분석 결과를 시각적인 HTML 보고서로 생성합니다.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd


def generate_html_report(df: pd.DataFrame, output_path: Path, start_date: datetime, end_date: datetime):
    """분석 결과를 HTML 보고서로 생성.

    Args:
        df: 분석 결과 DataFrame
        output_path: HTML 파일 저장 경로
        start_date: 분석 시작 날짜
        end_date: 분석 종료 날짜
    """
    # 통계 계산
    total = len(df)
    normal = len(df[df["U_적정성"] == "정상"])
    risk = len(df[df["U_적정성"] == "위험"])
    legal_exceed = len(df[df["V_법규기준초과자"] == "법기준초과"])
    risk_only = risk - legal_exceed

    normal_pct = (normal / total * 100) if total > 0 else 0
    risk_pct = (risk_only / total * 100) if total > 0 else 0
    legal_pct = (legal_exceed / total * 100) if total > 0 else 0

    # 위험 직원 목록
    legal_df = df[df["V_법규기준초과자"] == "법기준초과"].copy()
    risk_only_df = df[
        (df["U_적정성"] == "위험") & (df["V_법규기준초과자"] != "법기준초과")
    ].copy()

    # 팀별 통계
    team_stats = df.groupby("C_본조직").agg({
        "B_직원": "count",
        "U_적정성": lambda x: (x == "위험").sum(),
        "V_법규기준초과자": lambda x: (x == "법기준초과").sum(),
    }).rename(columns={
        "B_직원": "총인원",
        "U_적정성": "위험",
        "V_법규기준초과자": "법규초과"
    })
    team_stats["정상"] = team_stats["총인원"] - team_stats["위험"]
    team_stats = team_stats.sort_values("위험", ascending=False)

    # HTML 생성
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>초과근로 분석 보고서 - {start_date.strftime('%Y년 %m월')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Malgun Gothic', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .header .period {{
            font-size: 1.2em;
            opacity: 0.95;
        }}

        .content {{
            padding: 40px;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            border-left: 5px solid;
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .stat-card.total {{
            border-color: #667eea;
        }}

        .stat-card.normal {{
            border-color: #10b981;
        }}

        .stat-card.risk {{
            border-color: #f59e0b;
        }}

        .stat-card.legal {{
            border-color: #ef4444;
        }}

        .stat-card .label {{
            font-size: 0.9em;
            color: #6b7280;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .stat-card.total .value {{ color: #667eea; }}
        .stat-card.normal .value {{ color: #10b981; }}
        .stat-card.risk .value {{ color: #f59e0b; }}
        .stat-card.legal .value {{ color: #ef4444; }}

        .stat-card .percent {{
            font-size: 0.9em;
            color: #9ca3af;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 20px;
            color: #1f2937;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .progress-bar {{
            width: 100%;
            height: 40px;
            background: #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
            display: flex;
            margin-bottom: 30px;
        }}

        .progress-segment {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9em;
            transition: all 0.3s;
        }}

        .progress-segment:hover {{
            opacity: 0.9;
        }}

        .progress-normal {{
            background: #10b981;
        }}

        .progress-risk {{
            background: #f59e0b;
        }}

        .progress-legal {{
            background: #ef4444;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-radius: 10px;
            overflow: hidden;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
        }}

        td {{
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
        }}

        tbody tr {{
            transition: background 0.2s;
        }}

        tbody tr:hover {{
            background: #f9fafb;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-legal {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .badge-risk {{
            background: #fef3c7;
            color: #92400e;
        }}

        .no-data {{
            text-align: center;
            padding: 40px;
            color: #6b7280;
            font-size: 1.1em;
        }}

        .footer {{
            background: #f9fafb;
            padding: 30px;
            text-align: center;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
        }}

        .footer .timestamp {{
            margin-bottom: 10px;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .container {{
                box-shadow: none;
            }}

            .stat-card:hover {{
                transform: none;
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 초과근로 분석 보고서</h1>
            <div class="period">{start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}</div>
        </div>

        <div class="content">
            <!-- 요약 통계 -->
            <div class="summary">
                <div class="stat-card total">
                    <div class="label">총 직원</div>
                    <div class="value">{total}</div>
                    <div class="percent">명</div>
                </div>
                <div class="stat-card normal">
                    <div class="label">✅ 정상</div>
                    <div class="value">{normal}</div>
                    <div class="percent">{normal_pct:.1f}%</div>
                </div>
                <div class="stat-card risk">
                    <div class="label">⚠️ 위험</div>
                    <div class="value">{risk_only}</div>
                    <div class="percent">{risk_pct:.1f}%</div>
                </div>
                <div class="stat-card legal">
                    <div class="label">🚨 법규초과</div>
                    <div class="value">{legal_exceed}</div>
                    <div class="percent">{legal_pct:.1f}%</div>
                </div>
            </div>

            <!-- 진행률 바 -->
            <div class="progress-bar">
                <div class="progress-segment progress-normal" style="width: {normal_pct}%;">
                    {normal}명 ({normal_pct:.1f}%)
                </div>
                <div class="progress-segment progress-risk" style="width: {risk_pct}%;">
                    {risk_only}명 ({risk_pct:.1f}%)
                </div>
                <div class="progress-segment progress-legal" style="width: {legal_pct}%;">
                    {legal_exceed}명 ({legal_pct:.1f}%)
                </div>
            </div>
"""

    # 법규초과 직원 테이블
    if not legal_df.empty:
        html += """
            <div class="section">
                <h2 class="section-title">🚨 법규 기준 초과자 ({} 명)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>직원</th>
                            <th>본조직</th>
                            <th>실제 초과근로 (h)</th>
                            <th>법규 기준 (h)</th>
                            <th>초과 시간 (h)</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>
""".format(len(legal_df))

        for _, row in legal_df.sort_values("O_실제초과근로_조기출근제외", ascending=False).iterrows():
            exceed_hours = row["O_실제초과근로_조기출근제외"] - row["R_법규위반_전일까지"]
            html += f"""
                        <tr>
                            <td><strong>{row["B_직원"]}</strong></td>
                            <td>{row["C_본조직"]}</td>
                            <td>{row["O_실제초과근로_조기출근제외"]:.2f}</td>
                            <td>{row["R_법규위반_전일까지"]:.2f}</td>
                            <td><strong style="color: #ef4444;">+{exceed_hours:.2f}</strong></td>
                            <td><span class="badge badge-legal">법규초과</span></td>
                        </tr>
"""

        html += """
                    </tbody>
                </table>
            </div>
"""

    # 위험 직원 테이블
    if not risk_only_df.empty:
        html += """
            <div class="section">
                <h2 class="section-title">⚠️ 위험 직원 ({} 명)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>직원</th>
                            <th>본조직</th>
                            <th>실제 초과근로 (h)</th>
                            <th>법정 기준 (h)</th>
                            <th>초과 시간 (h)</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>
""".format(len(risk_only_df))

        for _, row in risk_only_df.sort_values("O_실제초과근로_조기출근제외", ascending=False).iterrows():
            exceed_hours = row["O_실제초과근로_조기출근제외"] - row["Q_법정초과근로시간"]
            html += f"""
                        <tr>
                            <td><strong>{row["B_직원"]}</strong></td>
                            <td>{row["C_본조직"]}</td>
                            <td>{row["O_실제초과근로_조기출근제외"]:.2f}</td>
                            <td>{row["Q_법정초과근로시간"]:.2f}</td>
                            <td><strong style="color: #f59e0b;">+{exceed_hours:.2f}</strong></td>
                            <td><span class="badge badge-risk">위험</span></td>
                        </tr>
"""

        html += """
                    </tbody>
                </table>
            </div>
"""

    # 주의 필요 직원이 없는 경우
    if legal_df.empty and risk_only_df.empty:
        html += """
            <div class="section">
                <div class="no-data">
                    ✅ 주의 필요 직원이 없습니다!<br>
                    모든 직원이 정상 범위 내에서 근무하고 있습니다.
                </div>
            </div>
"""

    # 팀별 통계
    if len(team_stats) > 0:
        html += """
            <div class="section">
                <h2 class="section-title">📊 팀별 통계</h2>
                <table>
                    <thead>
                        <tr>
                            <th>본조직</th>
                            <th>총인원</th>
                            <th>정상</th>
                            <th>위험</th>
                            <th>법규초과</th>
                            <th>위험률</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        for team, row in team_stats.iterrows():
            risk_rate = (row["위험"] / row["총인원"] * 100) if row["총인원"] > 0 else 0
            html += f"""
                        <tr>
                            <td><strong>{team}</strong></td>
                            <td>{int(row["총인원"])}</td>
                            <td style="color: #10b981;">{int(row["정상"])}</td>
                            <td style="color: #f59e0b;">{int(row["위험"] - row["법규초과"])}</td>
                            <td style="color: #ef4444;">{int(row["법규초과"])}</td>
                            <td><strong>{risk_rate:.1f}%</strong></td>
                        </tr>
"""

        html += """
                    </tbody>
                </table>
            </div>
"""

    # Footer
    html += f"""
        </div>

        <div class="footer">
            <div class="timestamp">보고서 생성: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</div>
            <div>Shiftee 초과근로 분석 시스템</div>
        </div>
    </div>
</body>
</html>
"""

    # HTML 파일 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"📄 HTML 보고서 생성 완료: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")


__all__ = ["generate_html_report"]
