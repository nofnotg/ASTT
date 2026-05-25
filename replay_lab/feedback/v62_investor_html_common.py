from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


TITLE_MAP = {
    "V6.2 Full Investment Report": "V6.2 전체 투자 리포트",
    "V6.2 Trade Journal": "V6.2 거래 일지",
    "V6.2 Weekly Report": "V6.2 주간 리포트",
    "V6.2 Monthly Report": "V6.2 월간 리포트",
    "V6.2 Strategy Router Report": "V6.2 전략 라우터 리포트",
    "V6.2 Risk Report": "V6.2 리스크 리포트",
}

TERM_MAP = {
    "Final Equity": "최종 계좌 평가금(Equity)",
    "Return": "총수익률(Return)",
    "MDD": "최대 낙폭(MDD)",
    "Trades": "거래 수",
    "Equity Curve": "계좌 평가금 곡선(Equity Curve)",
    "Drawdown": "낙폭 곡선(Drawdown)",
    "Equity KRW": "계좌 평가금 KRW(Equity)",
    "Drawdown %": "낙폭 %(Drawdown)",
}


def read_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}


def write_investor_html(title: str, payload: dict[str, Any], output_path: str | Path, rows: list[dict] | None = None) -> dict[str, str]:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    capital = payload.get("capital", payload)
    curve = payload.get("equity_curve", [])
    weekly = payload.get("weekly_rows", payload.get("weekly", {}).get("weekly_rows", []))
    table = rows if rows is not None else weekly
    path.write_text(_html(_ko_title(title), capital, curve, table, payload), encoding="utf-8")
    return {"html": str(path)}


def _html(title: str, capital: dict[str, Any], curve: list[dict], rows: list[dict], payload: dict[str, Any]) -> str:
    labels = [str(row.get("time", row.get("week", row.get("month", "")))) for row in curve]
    equity = [round(float(row.get("equity", row.get("end_equity", 0))), 2) for row in curve]
    drawdown = [round(float(row.get("drawdown_pct", 0)), 2) for row in curve]
    cards = [
        ("최종 계좌 평가금(Equity)", f"{capital.get('final_equity_krw', payload.get('final_equity_krw', 0)):,.0f} KRW"),
        ("총수익률(Return)", f"{capital.get('total_return_pct', payload.get('total_return_pct', 0)):.2f}%"),
        ("최대 낙폭(MDD)", f"{capital.get('max_drawdown_pct', payload.get('max_drawdown_pct', 0)):.2f}%"),
        ("거래 수", str(capital.get("trade_count", payload.get("trade_count", 0)))),
    ]
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{{margin:0;font-family:Arial,'Malgun Gothic',sans-serif;background:#f8fafc;color:#172033}}header{{background:#0f172a;color:white;padding:28px}}
main{{max-width:1180px;margin:auto;padding:20px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
.card{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:16px}}.kpi{{font-size:24px;font-weight:700}}
.good{{color:#047857}}.bad{{color:#b91c1c}}.warn{{background:#fffbeb;border-left:4px solid #f59e0b;padding:14px;margin:14px 0}}
table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:10px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:14px}}
th{{background:#eef2ff}}details{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin:12px 0}}
canvas{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:10px;max-height:320px}}.explain{{background:#eff6ff;border-left:4px solid #2563eb;padding:14px;margin:14px 0}}
</style></head><body><header><h1>{html.escape(title)}</h1><p>실제 주문 없이, 50만 원 시드로 투자했다고 가정한 PAPER 검증 리포트입니다.</p></header>
<main><section class="grid">{''.join(f'<div class="card"><div>{html.escape(k)}</div><div class="kpi">{html.escape(v)}</div></div>' for k,v in cards)}</section>
<div class="warn"><strong>안전 고지:</strong> LIVE 주문은 금지 상태입니다. 이 결과는 OHLCV 캔들 기반 모의투자이며, 실제 spread/depth/체결 오차는 forward paper에서 추가 검증해야 합니다.</div>
<div class="explain"><strong>읽는 법:</strong> 계좌 평가금(Equity)은 모의 계좌 잔고, 최대 낙폭(MDD)은 고점 대비 가장 깊은 하락, 손익비 계수(Profit Factor)는 총수익/총손실, 가격 공백 구간(FVG)은 빠른 가격 이동 뒤 비어 보이는 구간을 뜻합니다.</div>
<h2>계좌 평가금 곡선(Equity Curve)</h2><canvas id="eq"></canvas><h2>낙폭 곡선(Drawdown)</h2><canvas id="dd"></canvas>
<h2>주요 표</h2>{_table(rows)}
<details><summary>검증 메타데이터 보기</summary><pre>{html.escape(json.dumps(_metadata(payload), ensure_ascii=False, indent=2, default=str))}</pre></details>
</main><script>
const labels={json.dumps(labels, ensure_ascii=False)};const equity={json.dumps(equity)};const dd={json.dumps(drawdown)};
new Chart(document.getElementById('eq'),{{type:'line',data:{{labels,datasets:[{{label:'계좌 평가금 KRW(Equity)',data:equity,borderColor:'#16a34a',backgroundColor:'rgba(22,163,74,.12)',tension:.25}}]}}}});
new Chart(document.getElementById('dd'),{{type:'bar',data:{{labels,datasets:[{{label:'낙폭 %(Drawdown)',data:dd,backgroundColor:'#ef4444'}}]}}}});
</script></body></html>"""


def _table(rows: list[dict]) -> str:
    if not rows:
        return "<p>표시할 행이 없습니다.</p>"
    if not isinstance(rows[0], dict):
        rows = [{"item": row} for row in rows]
    keys = list(rows[0].keys())[:10]
    head = "".join(f"<th>{html.escape(_label(str(key)))}</th>" for key in keys)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key in keys) + "</tr>" for row in rows[:120])
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _metadata(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": payload.get("schema_version"),
        "mode": payload.get("mode"),
        "investment_start_time": payload.get("investment_start_time"),
        "investment_end_time": payload.get("investment_end_time"),
        "real_order_enabled": payload.get("real_order_enabled"),
        "live_order_allowed": payload.get("live_order_allowed"),
        "auto_apply_allowed": payload.get("auto_apply_allowed"),
        "plain_language_summary": payload.get("plain_language_summary", {}),
    }


def _ko_title(title: str) -> str:
    return TITLE_MAP.get(title, title)


def _label(value: str) -> str:
    labels = {
        "trade_id": "거래 ID",
        "date": "날짜",
        "market": "종목",
        "plan": "운영 플랜",
        "strategy": "전략",
        "setup_type": "셋업",
        "regime": "시장 국면(Regime)",
        "entry_time": "진입 시각",
        "exit_time": "청산 시각",
        "pnl_krw": "손익 KRW",
        "return_pct": "수익률 %",
        "equity_before": "진입 전 평가금",
        "equity_after": "청산 후 평가금",
        "week": "주",
        "month": "월",
        "start_equity": "시작 평가금",
        "end_equity": "종료 평가금",
        "trade_count": "거래 수",
        "win_rate": "승률",
        "profit_factor": "손익비 계수(Profit Factor)",
        "max_drawdown_pct": "최대 낙폭(MDD)",
    }
    return labels.get(value, value)
