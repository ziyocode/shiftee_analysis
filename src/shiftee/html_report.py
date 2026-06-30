"""HTML 보고서 생성 모듈.

분석 결과를 시각적인 HTML 보고서로 생성합니다.
디자인: 신한(Shinhan) 블루 테마 — 모던 corporate 리포트.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd


# 신한 블루 테마 스타일시트 (report6.html 디자인 언어 차용)
_REPORT_CSS = """
:root {
  --shinhan-blue: #0046ff;
  --shinhan-light-blue: #8cd2f5;
  --shinhan-royal-blue: #2878f5;
  --shinhan-navy: #00236e;
  --shinhan-bg: #f3f8ff;
  --shinhan-line: #d7e8ff;
  --ink: #071a3d;
  --muted: #5c6b82;
  --line: var(--shinhan-line);
  --surface: #ffffff;
  --danger: #b42318;
  --danger-soft: #fef3f2;
  --warn: #953800;
  --warn-soft: #fff7ed;
  --success: #067647;
  --success-soft: #ecfdf3;
  --info-soft: #e8f6ff;
}
* { box-sizing: border-box; }
body {
  background:
    radial-gradient(circle at 8% 0%, rgba(140, 210, 245, 0.34), transparent 31%),
    radial-gradient(circle at 92% 4%, rgba(0, 70, 255, 0.14), transparent 34%),
    linear-gradient(145deg, #ffffff 0%, var(--shinhan-bg) 48%, #eaf4ff 100%);
  color: var(--ink);
  font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', 'Segoe UI', sans-serif;
  margin: 0;
  padding: 40px 24px;
}
.report-shell { max-width: 1280px; margin: 0 auto; }
.hero {
  position: relative;
  overflow: hidden;
  color: #fff;
  background:
    linear-gradient(128deg, rgba(0, 35, 110, 0.98), rgba(0, 70, 255, 0.96) 58%, rgba(40, 120, 245, 0.94)),
    linear-gradient(90deg, var(--shinhan-navy), var(--shinhan-blue));
  border-radius: 32px;
  padding: 42px;
  margin-bottom: 28px;
  box-shadow: 0 30px 70px rgba(0, 35, 110, 0.24);
}
.hero:after {
  content: "";
  position: absolute;
  width: 360px; height: 360px;
  right: -120px; top: -130px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(140, 210, 245, 0.58), rgba(140, 210, 245, 0.08) 66%, transparent 70%);
}
.hero-eyebrow {
  position: relative;
  color: var(--shinhan-light-blue);
  font-size: 13px; font-weight: 800;
  letter-spacing: 0.22em; text-transform: uppercase;
}
.hero h1 { position: relative; font-size: 40px; line-height: 1.1; margin: 12px 0; max-width: 820px; }
.hero-lede { position: relative; color: rgba(255,255,255,0.84); font-size: 16px; margin: 0; }
h2 {
  color: var(--shinhan-navy);
  font-size: 22px;
  margin: 0 0 16px;
  padding-left: 14px;
  border-left: 5px solid var(--shinhan-blue);
}
.panel {
  background: rgba(255,255,255,0.94);
  border: 1px solid rgba(215, 232, 255, 0.92);
  border-radius: 22px;
  padding: 24px;
  margin-bottom: 22px;
  box-shadow: 0 16px 40px rgba(0, 35, 110, 0.09);
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
}
.summary-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-left: 5px solid var(--shinhan-blue);
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 12px 28px rgba(0, 35, 110, 0.07);
}
.summary-card span { color: var(--muted); font-size: 12px; font-weight: 800; letter-spacing: 0.06em; }
.summary-card strong { display: block; font-size: 30px; line-height: 1.1; letter-spacing: -0.02em; margin-top: 6px; }
.summary-card small { color: var(--muted); font-size: 12px; font-weight: 700; }
.summary-card.is-total { border-left-color: var(--shinhan-navy); }
.summary-card.is-total strong { color: var(--shinhan-navy); }
.summary-card.is-normal { border-left-color: var(--success); }
.summary-card.is-normal strong { color: var(--success); }
.summary-card.is-risk { border-left-color: var(--warn); }
.summary-card.is-risk strong { color: var(--warn); }
.summary-card.is-legal { border-left-color: var(--danger); }
.summary-card.is-legal strong { color: var(--danger); }
.dist-bar {
  display: flex;
  width: 100%;
  height: 38px;
  border-radius: 12px;
  overflow: hidden;
  margin-top: 20px;
  border: 1px solid var(--line);
}
.dist-seg {
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 12px; font-weight: 800; white-space: nowrap;
  min-width: 0; overflow: hidden;
}
.dist-normal { background: var(--success); }
.dist-risk { background: #d2691e; }
.dist-legal { background: var(--danger); }
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--surface);
  box-shadow: 0 12px 32px rgba(0, 35, 110, 0.06);
}
table { border-collapse: separate; border-spacing: 0; width: 100%; background: var(--surface); }
th, td { border-bottom: 1px solid var(--line); padding: 13px 16px; text-align: left; vertical-align: middle; }
th { background: #eff7ff; color: var(--shinhan-navy); font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
th.num { text-align: right; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:nth-child(even) td { background: #fbfdff; }
tbody tr:hover td { background: #eaf6ff; }
.status-pill {
  display: inline-flex; align-items: center;
  border-radius: 999px; padding: 4px 12px;
  font-size: 12px; font-weight: 800; letter-spacing: 0.03em;
}
.pill-legal { color: #fff; background: var(--danger); }
.pill-risk { color: var(--warn); background: var(--warn-soft); border: 1px solid rgba(149, 56, 0, 0.24); }
.pill-normal { color: #fff; background: var(--success); }
.delta-legal { color: var(--danger); font-weight: 800; }
.delta-risk { color: #b25a17; font-weight: 800; }
.no-data {
  text-align: center; padding: 36px;
  color: var(--success); font-size: 16px; font-weight: 700;
  background: var(--success-soft); border: 1px solid #c3ecd6; border-radius: 16px;
}
.footer {
  text-align: center; color: var(--muted); font-size: 13px;
  padding: 24px 0 8px;
}
.footer .brand { color: var(--shinhan-navy); font-weight: 800; }
@media (max-width: 720px) {
  body { padding: 20px 12px; }
  .hero { border-radius: 22px; padding: 28px; }
  .hero h1 { font-size: 30px; }
  th, td { padding: 10px 12px; }
}
"""


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

    period = f"{start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}"

    # ── HTML 헤더 + 요약 ──
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>초과근로 분석 보고서 - {start_date.strftime('%Y년 %m월')}</title>
    <style>{_REPORT_CSS}</style>
</head>
<body>
    <main class="report-shell">
        <section class="hero">
            <div class="hero-eyebrow">Shinhan DS · Workforce Compliance</div>
            <h1>초과근로 적정성 분석 보고서</h1>
            <p class="hero-lede">분석 기간 · {period}</p>
        </section>

        <section class="panel">
            <h2>분석 요약</h2>
            <div class="summary-grid">
                <div class="summary-card is-total">
                    <span>총 직원</span>
                    <strong>{total}</strong>
                    <small>명</small>
                </div>
                <div class="summary-card is-normal">
                    <span>정상</span>
                    <strong>{normal}</strong>
                    <small>{normal_pct:.1f}%</small>
                </div>
                <div class="summary-card is-risk">
                    <span>위험</span>
                    <strong>{risk_only}</strong>
                    <small>{risk_pct:.1f}%</small>
                </div>
                <div class="summary-card is-legal">
                    <span>법규 초과</span>
                    <strong>{legal_exceed}</strong>
                    <small>{legal_pct:.1f}%</small>
                </div>
            </div>
            <div class="dist-bar">
                <div class="dist-seg dist-normal" style="width: {normal_pct}%;">{normal}명 ({normal_pct:.1f}%)</div>
                <div class="dist-seg dist-risk" style="width: {risk_pct}%;">{risk_only}명 ({risk_pct:.1f}%)</div>
                <div class="dist-seg dist-legal" style="width: {legal_pct}%;">{legal_exceed}명 ({legal_pct:.1f}%)</div>
            </div>
        </section>
"""

    # ── 법규초과 직원 ──
    if not legal_df.empty:
        html += f"""
        <section class="panel">
            <h2>🚨 법규 기준 초과자 ({len(legal_df)}명)</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>직원</th>
                            <th>본조직</th>
                            <th class="num">실제 초과근로 (h)</th>
                            <th class="num">법규 기준 (h)</th>
                            <th class="num">초과 시간 (h)</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for _, row in legal_df.sort_values("O_실제초과근로_조기출근제외", ascending=False).iterrows():
            exceed_hours = row["O_실제초과근로_조기출근제외"] - row["R_법규위반_전일까지"]
            html += f"""                        <tr>
                            <td><strong>{row["B_직원"]}</strong></td>
                            <td>{row["C_본조직"]}</td>
                            <td class="num">{row["O_실제초과근로_조기출근제외"]:.2f}</td>
                            <td class="num">{row["R_법규위반_전일까지"]:.2f}</td>
                            <td class="num"><span class="delta-legal">+{exceed_hours:.2f}</span></td>
                            <td><span class="status-pill pill-legal">법규초과</span></td>
                        </tr>
"""
        html += """                    </tbody>
                </table>
            </div>
        </section>
"""

    # ── 위험 직원 ──
    if not risk_only_df.empty:
        html += f"""
        <section class="panel">
            <h2>⚠️ 위험 직원 ({len(risk_only_df)}명)</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>직원</th>
                            <th>본조직</th>
                            <th class="num">실제 초과근로 (h)</th>
                            <th class="num">법정 기준 (h)</th>
                            <th class="num">초과 시간 (h)</th>
                            <th>상태</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for _, row in risk_only_df.sort_values("O_실제초과근로_조기출근제외", ascending=False).iterrows():
            exceed_hours = row["O_실제초과근로_조기출근제외"] - row["Q_법정초과근로시간"]
            html += f"""                        <tr>
                            <td><strong>{row["B_직원"]}</strong></td>
                            <td>{row["C_본조직"]}</td>
                            <td class="num">{row["O_실제초과근로_조기출근제외"]:.2f}</td>
                            <td class="num">{row["Q_법정초과근로시간"]:.2f}</td>
                            <td class="num"><span class="delta-risk">+{exceed_hours:.2f}</span></td>
                            <td><span class="status-pill pill-risk">위험</span></td>
                        </tr>
"""
        html += """                    </tbody>
                </table>
            </div>
        </section>
"""

    # ── 주의 필요 직원 없음 ──
    if legal_df.empty and risk_only_df.empty:
        html += """
        <section class="panel">
            <div class="no-data">✅ 주의 필요 직원이 없습니다. 모든 직원이 정상 범위 내에서 근무하고 있습니다.</div>
        </section>
"""

    # ── 팀별 통계 ──
    if len(team_stats) > 0:
        html += """
        <section class="panel">
            <h2>📊 팀별 통계</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>본조직</th>
                            <th class="num">총인원</th>
                            <th class="num">정상</th>
                            <th class="num">위험</th>
                            <th class="num">법규초과</th>
                            <th class="num">위험률</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for team, row in team_stats.iterrows():
            risk_rate = (row["위험"] / row["총인원"] * 100) if row["총인원"] > 0 else 0
            html += f"""                        <tr>
                            <td><strong>{team}</strong></td>
                            <td class="num">{int(row["총인원"])}</td>
                            <td class="num" style="color: var(--success);">{int(row["정상"])}</td>
                            <td class="num" style="color: var(--warn);">{int(row["위험"] - row["법규초과"])}</td>
                            <td class="num" style="color: var(--danger);">{int(row["법규초과"])}</td>
                            <td class="num"><strong>{risk_rate:.1f}%</strong></td>
                        </tr>
"""
        html += """                    </tbody>
                </table>
            </div>
        </section>
"""

    # ── Footer ──
    html += f"""
        <div class="footer">
            <div>보고서 생성: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</div>
            <div class="brand">Shiftee 초과근로 분석 시스템</div>
        </div>
    </main>
</body>
</html>
"""

    # HTML 파일 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"📄 HTML 보고서 생성 완료: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")


__all__ = ["generate_html_report"]
