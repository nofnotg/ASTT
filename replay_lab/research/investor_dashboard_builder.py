from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_investor_dashboard(reports_dir: str = "docs/reports") -> dict[str, str]:
    root = Path(reports_dir)
    summary = _read(root / "latest_true_walk_forward_summary.json") or _read(root / "latest_v62_full_investment_summary.json")
    defense = _read(root / "latest_drawdown_defense_summary.json")
    capital = summary.get("capital", {})
    archive = summary.get("archive_coverage", summary.get("coverage", {}))
    html = _dashboard_html(summary, capital, archive, defense)
    path = root / "astt_report_dashboard.html"
    path.write_text(html, encoding="utf-8")
    source = "latest_true_walk_forward_summary.json" if (root / "latest_true_walk_forward_summary.json").exists() else "latest_v62_full_investment_summary.json"
    return {"html": str(path), "source": source}


def _dashboard_html(summary: dict[str, Any], capital: dict[str, Any], archive: dict[str, Any], defense: dict[str, Any]) -> str:
    start = summary.get("investment_start_time") or archive.get("earliest_available_time") or "확인 필요"
    end = summary.get("investment_end_time") or archive.get("latest_time") or "확인 필요"
    final_equity = float(capital.get("final_equity_krw", 0.0))
    ret = float(capital.get("total_return_pct", 0.0))
    mdd = float(capital.get("max_drawdown_pct", 0.0))
    trades = int(capital.get("trade_count", summary.get("trade_count", 0) or 0))
    defense_capital = defense.get("selected_defense", {}).get("capital", {})
    defense_equity = float(defense_capital.get("final_equity_krw", 0.0))
    defense_mdd = float(defense_capital.get("max_drawdown_pct", 0.0))
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT 투자 리포트 대시보드</title>
  <style>
    body{{margin:0;font-family:Arial,'Malgun Gothic',sans-serif;background:#f7f9fc;color:#172033}}
    header{{background:#0f172a;color:#fff;padding:30px 22px}}main{{max-width:1160px;margin:auto;padding:22px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}}.card{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px}}
    .kpi{{font-size:25px;font-weight:800;margin-top:6px}}.good{{color:#059669}}.bad{{color:#dc2626}}.warn{{color:#d97706}}
    .notice{{border-left:5px solid #d97706;background:#fffbeb;padding:14px 16px;margin:18px 0}}a{{color:#2563eb;font-weight:700;text-decoration:none}}a:hover{{text-decoration:underline}}
    table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e8f0}}th,td{{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}}th{{background:#eef2ff}}
    li{{margin:10px 0}}
  </style>
</head>
<body>
  <header>
    <h1>ASTT 투자 리포트 대시보드</h1>
    <p>모든 PAPER 투자일지, 주간/월간 결과, 리스크 분석과 방어 시스템 피드백을 모아보는 고정 페이지입니다.</p>
  </header>
  <main>
    <section class="notice">
      <strong>안전 고지:</strong> 이 페이지의 모든 결과는 실제 주문이 아닌 모의투자(PAPER)입니다.
      실제 주문은 계속 금지되어 있으며, 실제 호가 깊이와 체결 오차는 별도 forward 검증 전까지 근사치입니다.
    </section>
    <section class="grid">
      <div class="card"><div>투자 시작시점</div><div class="kpi">{start}</div></div>
      <div class="card"><div>검증 종료시점</div><div class="kpi">{end}</div></div>
      <div class="card"><div>기존 최종 계좌 평가금(Equity)</div><div class="kpi good">{final_equity:,.0f} KRW</div></div>
      <div class="card"><div>기존 총수익률(Return)</div><div class="kpi {'good' if ret >= 0 else 'bad'}">{ret:+.2f}%</div></div>
      <div class="card"><div>기존 최대 낙폭(MDD)</div><div class="kpi warn">{mdd:.2f}%</div></div>
      <div class="card"><div>거래 수</div><div class="kpi">{trades}</div></div>
      <div class="card"><div>방어 적용 최종 평가금</div><div class="kpi good">{defense_equity:,.0f} KRW</div></div>
      <div class="card"><div>방어 적용 최대 낙폭</div><div class="kpi warn">{defense_mdd:.2f}%</div></div>
    </section>
    <h2>최신 리포트 바로 보기</h2>
    <ul>
      <li><a href="latest_drawdown_defense_report.html">하락구간 방어 시스템 리포트</a> - 계좌가 꺾였던 구간에서 어떤 대응이 필요했는지 분석</li>
      <li><a href="latest_v62_full_investment_report.html">전체 투자 리포트</a> - 50만 원 시드가 어떻게 변했는지 보는 핵심 보고서</li>
      <li><a href="latest_v62_trade_journal_report.html">거래 일지</a> - 각 거래의 진입 이유, 청산 이유, 손익, 배운 점</li>
      <li><a href="latest_v62_weekly_report.html">주간 리포트</a> - 주별 계좌 변화와 손실/수익 원인</li>
      <li><a href="latest_v62_monthly_report.html">월간 리포트</a> - 월별 수익률, 최대 낙폭, 주요 전략</li>
      <li><a href="latest_v62_risk_report.html">리스크 리포트</a> - 큰 승리 의존도, 손실 연속, 데이터 한계</li>
    </ul>
    <h2>용어 설명</h2>
    <table>
      <tr><th>용어</th><th>쉬운 설명</th></tr>
      <tr><td>계좌 평가금(Equity)</td><td>모의투자를 계속했을 때 현재 계좌가 얼마인지입니다.</td></tr>
      <tr><td>최대 낙폭(MDD)</td><td>가장 많이 벌었던 순간 대비 얼마나 깊게 빠졌는지입니다.</td></tr>
      <tr><td>최근 20거래 자동 감속</td><td>최근 거래 성과가 무너지면 다음 진입 금액을 자동으로 줄이는 방어 장치입니다.</td></tr>
      <tr><td>손익비 계수(Profit Factor)</td><td>총수익을 총손실로 나눈 값입니다. 1보다 크면 수익이 손실보다 컸다는 뜻입니다.</td></tr>
      <tr><td>가격 공백 구간(FVG)</td><td>가격이 빠르게 움직이며 비어 보이는 구간입니다. 되돌림 반응 후보로 봅니다.</td></tr>
      <tr><td>시장 국면(Regime)</td><td>현재 장이 상승장, 횡보장, 알트 순환장 같은 어떤 환경인지 나눈 분류입니다.</td></tr>
    </table>
  </main>
</body>
</html>"""


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
