from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


REPORT_LABELS: dict[str, tuple[str, str, str]] = {
    "latest_v64_investor_report.html": (
        "V6.4 투자자 요약",
        "방어 전략이 정답지를 본 결과인지와 다음 forward 후보를 한눈에 보는 요약입니다.",
        "V6.4 핵심",
    ),
    "latest_v64_hindsight_audit_report.html": (
        "V6.4 정답지 사용 여부 감사",
        "거래 전 정보만 사용했는지, 미래 데이터를 훔쳐보지 않았는지 검사합니다.",
        "V6.4 핵심",
    ),
    "latest_v64_scenario_comparison_report.html": (
        "V6.4 시나리오 비교",
        "Baseline, 방어형, 균형형, 공격형, 고위험 연구 모드를 같은 기준으로 비교합니다.",
        "V6.4 핵심",
    ),
    "latest_v64_return_amplification_report.html": (
        "V6.4 수익률 확대 실험",
        "방어를 켠 상태에서 수익률을 더 키울 수 있는 공격형 운용안을 검증합니다.",
        "V6.4 핵심",
    ),
    "latest_v64_causal_defense_report.html": (
        "V6.4 causal 방어 재검증",
        "방어 규칙을 처음 날짜부터 순차 적용했을 때도 효과가 유지되는지 확인합니다.",
        "V6.4 핵심",
    ),
    "latest_v64_policy_blend_analysis_report.html": (
        "V6.4 정책 조합 분석",
        "Rolling Edge, Balanced, Hybrid, Aggressive를 하나의 운용 부품으로 비교해 보완 가능한 지점을 찾습니다.",
        "V6.4 핵심",
    ),
    "latest_head_controller_v64_review_report.html": (
        "V6.4 Head Controller 검토",
        "LLM 기반 복기와 다음 실험 제안을 보되, 자동 적용은 금지합니다.",
        "V6.4 핵심",
    ),
    "latest_drawdown_defense_report.html": (
        "하락구간 방어 시스템 리포트",
        "계좌가 줄어든 구간에서 어떤 감속 대응이 필요했는지 분석합니다.",
        "방어/리스크",
    ),
    "latest_v62_full_investment_report.html": (
        "V6.2 전체 투자 리포트",
        "50만 원 시드가 장기 모의투자에서 어떻게 변했는지 보는 핵심 보고서입니다.",
        "투자 일지",
    ),
    "latest_v62_trade_journal_report.html": (
        "V6.2 거래 일지",
        "각 거래의 진입 이유, 청산 이유, 손익, 배운 점을 확인합니다.",
        "투자 일지",
    ),
    "latest_v62_weekly_report.html": (
        "V6.2 주간 리포트",
        "주별 계좌 변화와 손실/수익 원인을 확인합니다.",
        "투자 일지",
    ),
    "latest_v62_monthly_report.html": (
        "V6.2 월간 리포트",
        "월별 수익률, 최대 낙폭(MDD), 주요 전략을 확인합니다.",
        "투자 일지",
    ),
    "latest_v62_risk_report.html": (
        "V6.2 리스크 리포트",
        "큰 승리 의존도, 손실 연속, 데이터 한계를 확인합니다.",
        "방어/리스크",
    ),
}

V64_PACK = [
    "latest_v64_investor_report.html",
    "latest_v64_hindsight_audit_report.html",
    "latest_v64_scenario_comparison_report.html",
    "latest_v64_return_amplification_report.html",
    "latest_v64_causal_defense_report.html",
    "latest_v64_policy_blend_analysis_report.html",
]


def build_investor_dashboard(reports_dir: str = "docs/reports") -> dict[str, str]:
    root = Path(reports_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary_source = _summary_source(root)
    summary = _read(root / summary_source) if summary_source else {}
    defense = _read(root / "latest_drawdown_defense_summary.json")
    capital = summary.get("capital", {})
    archive = summary.get("archive_coverage", summary.get("coverage", {}))
    reports = _discover_reports(root)
    html_doc = _dashboard_html(summary, capital, archive, defense, reports)
    path = root / "astt_report_dashboard.html"
    path.write_text(html_doc, encoding="utf-8")
    return {
        "html": str(path),
        "source": summary_source or "none",
        "report_count": str(len(reports)),
    }


def _dashboard_html(
    summary: dict[str, Any],
    capital: dict[str, Any],
    archive: dict[str, Any],
    defense: dict[str, Any],
    reports: list[dict[str, str]],
) -> str:
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
  <title>ASTT Report Dashboard</title>
  <style>
    body{{margin:0;font-family:Arial,'Malgun Gothic',sans-serif;background:#f7f9fc;color:#172033;line-height:1.55}}
    header{{background:#0f172a;color:#fff;padding:30px 22px}}main{{max-width:1180px;margin:auto;padding:22px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}
    .card{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px}}
    .card h3{{margin:0 0 8px;font-size:18px}}.card p{{margin:8px 0 0;color:#475569}}
    .kpi{{font-size:25px;font-weight:800;margin-top:6px}}.good{{color:#059669}}.bad{{color:#dc2626}}.warn{{color:#d97706}}
    .notice{{border-left:5px solid #d97706;background:#fffbeb;padding:14px 16px;margin:18px 0;border-radius:8px}}
    .info{{border-left:5px solid #2563eb;background:#eff6ff;padding:14px 16px;margin:18px 0;border-radius:8px}}
    a{{color:#2563eb;font-weight:700;text-decoration:none}}a:hover{{text-decoration:underline}}
    table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden}}
    th,td{{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}}th{{background:#eef2ff}}
    section{{margin:28px 0}}.pill{{display:inline-block;background:#e2e8f0;border-radius:999px;padding:3px 9px;font-size:12px;color:#334155}}
  </style>
</head>
<body>
  <header>
    <h1>ASTT Report Dashboard</h1>
    <p>모든 PAPER 투자일지, 주간/월간 결과, 리스크 분석, 방어 시스템 검증을 모아 보는 고정 대시보드입니다.</p>
  </header>
  <main>
    <section class="notice">
      <strong>안전 고지:</strong> 이 페이지의 모든 결과는 실제 주문이 아닌 모의투자(PAPER)입니다.
      실제 주문, 주문 테스트, 출금, LLM 자동 설정 적용은 계속 금지됩니다.
    </section>
    <section class="grid">
      <div class="card"><div>투자 시작시점</div><div class="kpi">{_esc(start)}</div></div>
      <div class="card"><div>검증 종료시점</div><div class="kpi">{_esc(end)}</div></div>
      <div class="card"><div>기준 최종 계좌 평가금(Equity)</div><div class="kpi good">{final_equity:,.0f} KRW</div></div>
      <div class="card"><div>기준 총수익률(Return)</div><div class="kpi {'good' if ret >= 0 else 'bad'}">{ret:+.2f}%</div></div>
      <div class="card"><div>기준 최대 낙폭(MDD)</div><div class="kpi warn">{mdd:.2f}%</div></div>
      <div class="card"><div>거래 수</div><div class="kpi">{trades}</div></div>
      <div class="card"><div>방어 적용 최종 평가금</div><div class="kpi good">{defense_equity:,.0f} KRW</div></div>
      <div class="card"><div>방어 적용 최대 낙폭</div><div class="kpi warn">{defense_mdd:.2f}%</div></div>
    </section>
    <section class="info">
      <strong>운영 원칙:</strong> 앞으로 새 리포트가 <code>docs/reports/latest_*.html</code> 형식으로 생성되면
      <code>build-investor-dashboard</code> 실행 시 이 대시보드의 전체 리포트 목록에 자동으로 추가됩니다.
    </section>
    <section>
      <h2>V6.4 핵심 리포트 묶음</h2>
      <div class="grid">
        {_report_cards(reports, V64_PACK)}
      </div>
    </section>
    <section>
      <h2>전체 리포트 목록</h2>
      <p>최신 실험과 과거 검증 리포트를 한 곳에서 볼 수 있도록 자동 수집한 목록입니다.</p>
      {_report_table(reports)}
    </section>
    <section>
      <h2>용어 설명</h2>
      <table>
        <tr><th>용어</th><th>쉬운 설명</th></tr>
        <tr><td>계좌 평가금(Equity)</td><td>모의투자를 계속했을 때 현재 계좌가 얼마인지 보여주는 값입니다.</td></tr>
        <tr><td>최대 낙폭(MDD)</td><td>가장 많이 벌었던 시점 대비 계좌가 얼마나 깊게 빠졌는지 보여주는 위험 지표입니다.</td></tr>
        <tr><td>손익비 계수(Profit Factor)</td><td>총수익을 총손실로 나눈 값입니다. 1보다 크면 수익이 손실보다 컸다는 뜻입니다.</td></tr>
        <tr><td>거래당 기대수익(Expectancy)</td><td>거래 1번을 할 때 평균적으로 기대할 수 있는 수익 또는 손실입니다.</td></tr>
        <tr><td>가격 공백 구간(FVG)</td><td>가격이 빠르게 움직이며 비어 보이는 구간입니다. 되돌림 반응 후보로 봅니다.</td></tr>
        <tr><td>유동성 훑기/휩쏘(Liquidity Sweep)</td><td>전고점/전저점을 살짝 건드린 뒤 빠르게 되돌리는 움직임입니다.</td></tr>
        <tr><td>시장 국면(Regime)</td><td>현재 장이 상승장, 횡보장, 알트 순환장, 위험 회피장 중 어디에 가까운지 나눈 분류입니다.</td></tr>
      </table>
    </section>
  </main>
</body>
</html>"""


def _discover_reports(root: Path) -> list[dict[str, str]]:
    reports: list[dict[str, str]] = []
    for path in sorted(root.glob("latest_*.html")):
        title, description, category = REPORT_LABELS.get(path.name, _default_report_meta(path.name))
        reports.append(
            {
                "filename": path.name,
                "title": title,
                "description": description,
                "category": category,
            }
        )
    return sorted(reports, key=lambda item: (item["category"] != "V6.4 핵심", item["category"], item["title"]))


def _report_cards(reports: list[dict[str, str]], filenames: list[str]) -> str:
    by_name = {report["filename"]: report for report in reports}
    cards = []
    for filename in filenames:
        report = by_name.get(filename)
        if not report:
            cards.append(
                f"""<div class="card">
          <h3>{_esc(REPORT_LABELS.get(filename, (filename, "", ""))[0])}</h3>
          <p class="warn">아직 생성되지 않았습니다.</p>
        </div>"""
            )
            continue
        cards.append(
            f"""<div class="card">
          <span class="pill">{_esc(report["category"])}</span>
          <h3><a href="{_esc(report["filename"])}">{_esc(report["title"])}</a></h3>
          <p>{_esc(report["description"])}</p>
        </div>"""
        )
    return "\n".join(cards)


def _report_table(reports: list[dict[str, str]]) -> str:
    rows = "\n".join(
        f"""<tr>
          <td><span class="pill">{_esc(report["category"])}</span></td>
          <td><a href="{_esc(report["filename"])}">{_esc(report["title"])}</a></td>
          <td>{_esc(report["description"])}</td>
          <td><code>{_esc(report["filename"])}</code></td>
        </tr>"""
        for report in reports
    )
    return f"""<table>
        <tr><th>분류</th><th>리포트</th><th>설명</th><th>파일</th></tr>
        {rows}
      </table>"""


def _default_report_meta(filename: str) -> tuple[str, str, str]:
    stem = filename.removeprefix("latest_").removesuffix(".html")
    category = "기타"
    if stem.startswith("v62"):
        category = "V6.2 투자일지"
    elif stem.startswith("v61"):
        category = "V6.1 장기검증"
    elif stem.startswith("v6"):
        category = "V6 전략검증"
    elif "risk" in stem or "defense" in stem:
        category = "방어/리스크"
    elif "head_controller" in stem:
        category = "Head Controller"
    elif "timing" in stem:
        category = "타이밍랩"
    title = stem.replace("_", " ").upper()
    description = "자동 수집된 최신 리포트입니다. 상세 내용은 링크를 열어 확인하세요."
    return title, description, category


def _summary_source(root: Path) -> str:
    for name in ["latest_true_walk_forward_summary.json", "latest_v62_full_investment_summary.json"]:
        if (root / name).exists():
            return name
    return ""


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
