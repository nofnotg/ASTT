from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def build_v64_html_report(
    title: str,
    summary_path: str,
    output_path: str,
    subtitle: str,
) -> dict[str, str]:
    payload = _read(Path(summary_path))
    scenarios = _scenario_rows(payload)
    checks = payload.get("checks", [])
    body = _scenario_table(scenarios) if scenarios else _generic_table(payload)
    if checks:
        body += "<h2>정답지 사용 여부 감사</h2>" + _checks_table(checks)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_html(title, subtitle, body), encoding="utf-8")
    return {"html": str(path)}


def _html(title: str, subtitle: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body{{margin:0;font-family:Arial,'Malgun Gothic',sans-serif;background:#f8fafc;color:#172033}}
    header{{background:#0f172a;color:#fff;padding:28px}}main{{max-width:1180px;margin:auto;padding:20px}}
    .notice{{background:#fffbeb;border-left:5px solid #f59e0b;padding:14px;margin:14px 0}}
    table{{width:100%;border-collapse:collapse;background:white;border:1px solid #e5e7eb;margin:14px 0}}
    th,td{{padding:10px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:14px}}th{{background:#eef2ff}}
    .good{{color:#047857;font-weight:700}}.bad{{color:#b91c1c;font-weight:700}}
  </style>
</head>
<body>
  <header><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></header>
  <main>
    <section class="notice"><strong>안전 고지:</strong> 이 리포트는 PAPER 모의투자 재검증입니다. 실제 주문, 주문 테스트, 취소, 출금은 사용하지 않았고 live_order_enabled=false입니다.</section>
    <h2>한눈에 보는 결론</h2>
    <p>핵심은 방어 판단이 거래 이후 결과를 훔쳐보지 않았는지, 즉 정답지를 보고 만든 사후 최적화가 아닌지와, 방어를 켠 상태에서 수익률 확대가 가능한지를 나눠서 보는 것입니다.</p>
    {body}
    <h2>실전 금지 사유</h2>
    <p>아직 OHLCV 기반 재검증이며 실제 호가 깊이, 스프레드, 체결 지연 overlay가 forward paper에서 충분히 검증되지 않았습니다. 따라서 LIVE_READY는 금지이며 기본 판정은 LIVE_NOT_ALLOWED입니다.</p>
  </main>
</body>
</html>"""


def _scenario_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "scenarios" in payload and payload["scenarios"]:
        rows = payload["scenarios"]
        if rows and "capital" in rows[0]:
            return rows
        if rows and "final_equity_krw" in rows[0]:
            return [{"scenario": row.get("scenario"), "capital": row, "decision": row.get("decision")} for row in rows]
    return []


def _scenario_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        capital = row.get("capital", {})
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('scenario')))}</td>"
            f"<td>{_money(capital.get('final_equity_krw'))}</td>"
            f"<td>{_pct(capital.get('total_return_pct', capital.get('return_pct')))}</td>"
            f"<td>{_pct(capital.get('max_drawdown_pct', capital.get('mdd_pct')))}</td>"
            f"<td>{_num(capital.get('profit_factor'))}</td>"
            f"<td>{capital.get('trade_count', capital.get('trades', 0))}</td>"
            f"<td>{_num(capital.get('return_to_mdd_ratio'))}</td>"
            f"<td>{html.escape(str(row.get('decision', '')))}</td>"
            "</tr>"
        )
    return "<h2>시나리오 비교</h2><table><thead><tr><th>시나리오</th><th>최종 평가금</th><th>수익률</th><th>최대 낙폭(MDD)</th><th>PF</th><th>거래 수</th><th>Return/MDD</th><th>판정</th></tr></thead><tbody>" + "".join(body) + "</tbody></table>"


def _checks_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        f"<tr><td>{html.escape(str(row.get('check')))}</td><td class=\"{'good' if row.get('status') == 'PASS' else 'bad'}\">{html.escape(str(row.get('status')))}</td><td>{html.escape(str(row.get('notes', row.get('checked', ''))))}</td></tr>"
        for row in rows
    )
    return "<table><thead><tr><th>검사</th><th>상태</th><th>메모</th></tr></thead><tbody>" + body + "</tbody></table>"


def _generic_table(payload: dict[str, Any]) -> str:
    rows = []
    for key, value in payload.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            rows.append(f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>")
    return "<table><tbody>" + "".join(rows) + "</tbody></table>"


def _money(value: Any) -> str:
    return f"{float(value or 0):,.0f}원"


def _pct(value: Any) -> str:
    return f"{float(value or 0):+.2f}%"


def _num(value: Any) -> str:
    return f"{float(value or 0):.2f}"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
