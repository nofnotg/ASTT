from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def read_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}


def write_investor_html(title: str, payload: dict[str, Any], output_path: str | Path, rows: list[dict] | None = None) -> dict[str, str]:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    capital = payload.get("capital", payload)
    chart_rows = payload.get("equity_curve", [])
    weekly = payload.get("weekly_rows", payload.get("weekly", {}).get("weekly_rows", []))
    table = rows if rows is not None else weekly
    path.write_text(_html(title, capital, chart_rows, table, payload), encoding="utf-8")
    return {"html": str(path)}


def _html(title: str, capital: dict, curve: list[dict], rows: list[dict], payload: dict) -> str:
    labels = [str(row.get("time", "")) for row in curve]
    equity = [round(float(row.get("equity", 0)), 2) for row in curve]
    drawdown = [round(float(row.get("drawdown_pct", 0)), 2) for row in curve]
    cards = [
        ("Final Equity", f"{capital.get('final_equity_krw', payload.get('final_equity_krw', 0)):,.0f} KRW"),
        ("Return", f"{capital.get('total_return_pct', payload.get('total_return_pct', 0)):.2f}%"),
        ("MDD", f"{capital.get('max_drawdown_pct', payload.get('max_drawdown_pct', 0)):.2f}%"),
        ("Trades", str(capital.get("trade_count", payload.get("trade_count", 0)))),
    ]
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{{margin:0;font-family:Arial,sans-serif;background:#f8fafc;color:#172033}}header{{background:#0f172a;color:white;padding:28px}}
main{{max-width:1180px;margin:auto;padding:20px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}
.card{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:16px}}.kpi{{font-size:24px;font-weight:700}}
.good{{color:#047857}}.bad{{color:#b91c1c}}.warn{{background:#fffbeb;border-left:4px solid #f59e0b;padding:14px;margin:14px 0}}
table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:10px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:14px}}
th{{background:#eef2ff}}details{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin:12px 0}}
canvas{{background:white;border:1px solid #e5e7eb;border-radius:8px;padding:10px;max-height:320px}}
</style></head><body><header><h1>{html.escape(title)}</h1><p>실제 주문 없이 PAPER 기준으로 50만 원 계좌 흐름을 복기한 투자자용 리포트입니다.</p></header>
<main><section class="grid">{''.join(f'<div class="card"><div>{html.escape(k)}</div><div class="kpi">{html.escape(v)}</div></div>' for k,v in cards)}</section>
<div class="warn"><strong>안전 고지:</strong> LIVE 주문은 금지 상태입니다. OHLCV-only 결과라 실제 spread/depth forward 검증 전에는 실전 전환할 수 없습니다.</div>
<h2>Equity Curve</h2><canvas id="eq"></canvas><h2>Drawdown</h2><canvas id="dd"></canvas>
<h2>주요 표</h2>{_table(rows)}
<details><summary>원본 구조화 JSON 보기</summary><pre>{html.escape(json.dumps(payload, ensure_ascii=False, indent=2, default=str))}</pre></details>
</main><script>
const labels={json.dumps(labels, ensure_ascii=False)};const equity={json.dumps(equity)};const dd={json.dumps(drawdown)};
new Chart(document.getElementById('eq'),{{type:'line',data:{{labels,datasets:[{{label:'Equity KRW',data:equity,borderColor:'#16a34a',backgroundColor:'rgba(22,163,74,.12)',tension:.25}}]}}}});
new Chart(document.getElementById('dd'),{{type:'bar',data:{{labels,datasets:[{{label:'Drawdown %',data:dd,backgroundColor:'#ef4444'}}]}}}});
</script></body></html>"""


def _table(rows: list[dict]) -> str:
    if not rows:
        return "<p>No rows.</p>"
    if not isinstance(rows[0], dict):
        rows = [{"item": row} for row in rows]
    keys = list(rows[0].keys())[:10]
    head = "".join(f"<th>{html.escape(str(key))}</th>" for key in keys)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key in keys) + "</tr>" for row in rows[:80])
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
