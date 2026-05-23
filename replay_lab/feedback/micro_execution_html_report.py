from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.replay.micro_execution_replay import latest_micro_execution_experiment


@dataclass(frozen=True)
class MicroExecutionHTMLReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "micro_execution"

    def build(self, start_date: str = "2026-04-01", end_date: str = "2026-05-15") -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = self._payload(start_date, end_date)
        html = self._html(payload)
        md = self._markdown(payload)
        (self.out_dir / "micro_execution_report.html").write_text(html, encoding="utf-8")
        (self.out_dir / "micro_execution_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        (self.out_dir / "micro_execution_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_micro_execution_report.html").write_text(html, encoding="utf-8")
        (self.docs_root / "latest_micro_execution_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_micro_execution_summary.json").write_text(json.dumps(self._summary(payload), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return self.out_dir / "micro_execution_report.html"

    def _payload(self, start_date: str, end_date: str) -> dict:
        exp = latest_micro_execution_experiment(self.store_dir)
        metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8")) if exp and (exp / "metrics.json").exists() else {}
        trades = pd.read_parquet(exp / "micro_trades.parquet") if exp and (exp / "micro_trades.parquet").exists() else pd.DataFrame()
        entry = _read_json(self.out_dir / "micro_entry_timing_validation.json")
        exit_validation = _read_json(self.out_dir / "micro_exit_validation.json")
        latency = _read_json(self.out_dir / "latency_slippage_simulation.json")
        return {
            "schema_version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {"start_date": start_date, "end_date": end_date},
            "metrics": metrics,
            "entry_timing": entry,
            "exit_validation": exit_validation,
            "latency_slippage": latency,
            "trades": trades.head(120).to_dict("records") if not trades.empty else [],
            "live_readiness": metrics.get("live_readiness", "LIVE_NOT_ALLOWED"),
            "plain_language": _plain_language(),
        }

    def _summary(self, payload: dict) -> dict:
        m = payload.get("metrics", {})
        return {
            "schema_version": "1.0",
            "generated_at": payload["generated_at"],
            "period": payload["period"],
            "entry_count": m.get("entry_count", 0),
            "win_rate": m.get("win_rate", 0.0),
            "profit_factor": m.get("profit_factor", 0.0),
            "expectancy_pct": m.get("expectancy_pct", 0.0),
            "avg_hold_seconds": m.get("avg_hold_seconds", 0.0),
            "cancel_count": m.get("cancel_count", 0),
            "micro_failure_exit_count": m.get("micro_failure_exit_count", 0),
            "time_stop_count": m.get("time_stop_count", 0),
            "take_profit_count": m.get("take_profit_count", 0),
            "stop_loss_count": m.get("stop_loss_count", 0),
            "total_pnl_krw": m.get("total_pnl_krw", 0.0),
            "data_quality_summary": m.get("data_quality_summary", {}),
            "live_readiness": payload.get("live_readiness", "LIVE_NOT_ALLOWED"),
        }

    def _markdown(self, payload: dict) -> str:
        m = payload.get("metrics", {})
        return f"""# ASTT V5.5 Micro Execution & Response Report

## 1. 한눈에 보는 결론
- 실전 판정: {payload.get('live_readiness', 'LIVE_NOT_ALLOWED')}
- 총 거래 수: {m.get('entry_count', 0)}
- 승률: {m.get('win_rate', 0) * 100:.2f}%
- Profit Factor: {m.get('profit_factor', 0):.4f}
- 기대값: {m.get('expectancy_pct', 0):.4f}%
- 평균 보유 시간: {m.get('avg_hold_seconds', 0):.1f}초
- 초봉 진입 취소 수: {m.get('cancel_count', 0)}
- 초봉 조기청산 수: {m.get('micro_failure_exit_count', 0)}
- 데이터 품질: {m.get('data_quality_summary', {})}

## 2. 일반 투자자용 설명
Profit Factor는 1보다 크면 번 돈이 잃은 돈보다 많다는 뜻입니다.

초봉 진입 취소는 분봉상 좋아 보였지만 실제 초 단위 힘이 약해서 들어가지 않은 경우입니다.

초봉 조기청산은 들어간 뒤 바로 힘이 죽어 손절 전에 빠져나온 경우입니다.

## 3. 실전 전환 판단
{payload.get('live_readiness', 'LIVE_NOT_ALLOWED')}
"""

    def _html(self, payload: dict) -> str:
        m = payload.get("metrics", {})
        entry_rows = _entry_rows(payload.get("entry_timing", {}).get("results", []))
        exit_rows = _exit_rows(payload.get("exit_validation", {}).get("results", []))
        latency_rows = _latency_rows(payload.get("latency_slippage", {}).get("results", []))
        success_rows = _trade_rows([t for t in payload.get("trades", []) if float(t.get("realized_pnl_pct", 0)) > 0][:3])
        failure_rows = _trade_rows([t for t in payload.get("trades", []) if float(t.get("realized_pnl_pct", 0)) <= 0][:3])
        cards = [
            ("실전 판정", payload.get("live_readiness", "LIVE_NOT_ALLOWED")),
            ("총 거래 수", m.get("entry_count", 0)),
            ("승률", f"{m.get('win_rate', 0) * 100:.2f}%"),
            ("Profit Factor", f"{m.get('profit_factor', 0):.3f}"),
            ("기대값", f"{m.get('expectancy_pct', 0):.3f}%"),
            ("평균 보유", f"{m.get('avg_hold_seconds', 0):.1f}초"),
            ("진입 취소", m.get("cancel_count", 0)),
            ("조기청산", m.get("micro_failure_exit_count", 0)),
            ("데이터 품질", str(m.get("data_quality_summary", {}))),
        ]
        card_html = "".join(f"<div class='card'><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>" for k, v in cards)
        rows = "".join(
            f"<tr><td>{escape(str(t.get('date_kst', '')))}</td><td>{escape(str(t.get('market', '')))}</td><td>{escape(str(t.get('entry_decision', '')))}</td><td>{escape(str(t.get('micro_exit_decision', '')))}</td><td>{float(t.get('realized_pnl_pct', 0)):.3f}%</td><td>{escape(str(t.get('data_quality', '')))}</td></tr>"
            for t in payload.get("trades", [])[:80]
        )
        return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ASTT V5.5 Micro Execution Report</title>
  <style>
    body {{ margin:0; background:#0f172a; color:#e5e7eb; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif; }}
    main {{ max-width:1180px; margin:auto; padding:28px 18px; }}
    .hero {{ padding:20px 0 8px; }}
    .hero p, .explain {{ color:#cbd5e1; line-height:1.65; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    .card, section {{ background:#111c33; border:1px solid #24324d; border-radius:8px; padding:16px; }}
    .card span {{ display:block; color:#9ca3af; font-size:13px; }}
    .card strong {{ display:block; margin-top:6px; font-size:22px; color:#fff; overflow-wrap:anywhere; }}
    section {{ margin-top:14px; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th,td {{ border-bottom:1px solid #263653; padding:8px; text-align:left; }}
    th {{ color:#a5b4fc; }}
    .badge {{ display:inline-block; padding:4px 8px; border-radius:999px; background:#312e81; color:#c7d2fe; }}
    @media(max-width:820px) {{ .grid {{ grid-template-columns:1fr; }} table {{ font-size:12px; }} }}
  </style>
</head>
<body>
<main>
  <div class="hero">
    <span class="badge">PAPER Replay Only</span>
    <h1>ASTT V5.5 Micro Execution & Response</h1>
    <p>미래를 맞히는 시스템이 아니라, 이미 정해진 분봉 셋업이 왔을 때 초봉 반응으로 들어갈지, 기다릴지, 빠질지를 검증한 리포트입니다.</p>
  </div>
  <div class="grid">{card_html}</div>
  <section>
    <h2>한눈에 보는 결론</h2>
    <p class="explain">이번 검증의 실전 판정은 <b>{escape(str(payload.get("live_readiness", "LIVE_NOT_ALLOWED")))}</b>입니다. 초봉 데이터와 호가 데이터가 충분하지 않거나, 초봉 대응이 손익을 개선하지 못하면 실전 전환은 금지합니다.</p>
  </section>
  <section>
    <h2>일반 투자자용 해석</h2>
    <p class="explain"><b>Profit Factor</b>는 1보다 크면 번 돈이 잃은 돈보다 많다는 뜻입니다. <b>초봉 진입 취소</b>는 분봉상 좋아 보였지만 실제 초 단위 힘이 약해서 들어가지 않은 경우입니다. <b>초봉 조기청산</b>은 들어간 뒤 바로 힘이 죽어 손절 전에 빠져나온 경우입니다.</p>
  </section>
  <section>
    <h2>지난 시스템에서 남긴 것 / 제외한 것</h2>
    <p class="explain">V5.5는 Daily + 4H 구조 필터, 15M/5M/1M 셋업, BTC shock 필터, fixed RR, fixed order PAPER 검증만 기본으로 남겼습니다. Zone, runner, full seed, grade allocation은 이번 기본 실행에서 제외하고 보조 리포트용으로만 둡니다.</p>
  </section>
  <section>
    <h2>초봉 데이터 품질</h2>
    <p class="explain">초봉 데이터 품질 요약: <b>{escape(str(m.get("data_quality_summary", {})))}</b>. 초봉 또는 호가가 부족한 구간은 실제 투자처럼 검증됐다고 보지 않고, 실전 판정은 보수적으로 낮춥니다.</p>
  </section>
  <section>
    <h2>분봉 진입 vs 초봉 확인 진입 비교</h2>
    <table><thead><tr><th>모델</th><th>진입</th><th>취소</th><th>승률</th><th>PF</th><th>기대값</th><th>막은 손실</th><th>놓친 수익</th></tr></thead><tbody>{entry_rows}</tbody></table>
  </section>
  <section>
    <h2>기존 청산 vs 초봉 대응 청산 비교</h2>
    <table><thead><tr><th>모델</th><th>진입</th><th>승률</th><th>PF</th><th>평균 이익</th><th>평균 손실</th><th>막아낸 손실</th><th>놓친 수익</th></tr></thead><tbody>{exit_rows}</tbody></table>
  </section>
  <section>
    <h2>지연 / 슬리피지 민감도</h2>
    <p class="explain">초단타는 0.05%의 비용 차이만으로도 결과가 뒤집힐 수 있습니다. 그래서 좋은 백테스트라도 지연과 슬리피지에 약하면 실전 금지입니다.</p>
    <table><thead><tr><th>지연/슬리피지</th><th>PF</th><th>기대값</th><th>손익</th></tr></thead><tbody>{latency_rows}</tbody></table>
  </section>
  <section>
    <h2>초봉 대응이 막아낸 손실 / 놓친 수익</h2>
    <p class="explain">이번 산출물 기준 막아낸 손실은 <b>{payload.get("exit_validation", {}).get("saved_loss_krw", 0):.0f}원</b>, 놓친 수익은 <b>{payload.get("exit_validation", {}).get("early_exit_missed_profit_krw", 0):.0f}원</b>으로 기록됐습니다. 다만 초봉 데이터가 대부분 proxy 또는 unavailable이면 이 수치는 실전 근거가 아니라 진단값입니다.</p>
  </section>
  <section>
    <h2>대표 성공 거래 3개</h2>
    <table><thead><tr><th>날짜</th><th>마켓</th><th>청산</th><th>손익</th><th>보유</th><th>데이터</th></tr></thead><tbody>{success_rows}</tbody></table>
  </section>
  <section>
    <h2>대표 실패 거래 3개</h2>
    <table><thead><tr><th>날짜</th><th>마켓</th><th>청산</th><th>손익</th><th>보유</th><th>데이터</th></tr></thead><tbody>{failure_rows}</tbody></table>
  </section>
  <section>
    <h2>실전 전환 판단</h2>
    <p class="explain"><b>{escape(str(payload.get("live_readiness", "LIVE_NOT_ALLOWED")))}</b>. 초봉 데이터 부족, orderbook 미사용, 슬리피지 민감도 때문에 이번 단계에서 실제 주문 전환은 금지합니다.</p>
  </section>
  <section>
    <h2>다음 과제</h2>
    <p class="explain">1초봉과 WebSocket 체결/호가를 지속 저장해 진짜 micro replay 표본을 늘리고, 0.05~0.10% 비용에서도 양수 기대값을 유지하는지 다시 확인해야 합니다.</p>
  </section>
  <section>
    <h2>거래 요약</h2>
    <table><thead><tr><th>날짜</th><th>마켓</th><th>진입</th><th>청산</th><th>손익</th><th>데이터</th></tr></thead><tbody>{rows}</tbody></table>
  </section>
</main>
</body>
</html>"""


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _plain_language() -> dict:
    return {
        "profit_factor": "1보다 크면 번 돈이 잃은 돈보다 많다는 뜻입니다.",
        "micro_cancel": "분봉은 좋아 보였지만 초 단위 힘이 약해서 들어가지 않은 경우입니다.",
        "micro_failure_exit": "진입 뒤 바로 힘이 죽어 손절 전에 빠져나오는 경우입니다.",
        "data_quality": "초봉 또는 호가 데이터가 부족하면 실전 판정 신뢰도가 낮아집니다.",
    }


def _entry_rows(rows: list[dict]) -> str:
    if not rows:
        return "<tr><td colspan='8'>검증 데이터 없음</td></tr>"
    return "".join(
        f"<tr><td>{escape(str(r.get('model', '')))}</td><td>{r.get('entry_count', 0)}</td><td>{r.get('cancel_count', 0)}</td><td>{float(r.get('win_rate', 0))*100:.2f}%</td><td>{float(r.get('profit_factor', 0)):.3f}</td><td>{float(r.get('expectancy_pct', 0)):.3f}%</td><td>{r.get('avoided_loss_count', 0)}</td><td>{r.get('missed_win_count', 0)}</td></tr>"
        for r in rows
    )


def _exit_rows(rows: list[dict]) -> str:
    if not rows:
        return "<tr><td colspan='8'>검증 데이터 없음</td></tr>"
    return "".join(
        f"<tr><td>{escape(str(r.get('model', '')))}</td><td>{r.get('entry_count', 0)}</td><td>{float(r.get('win_rate', 0))*100:.2f}%</td><td>{float(r.get('profit_factor', 0)):.3f}</td><td>{float(r.get('avg_win_pct', 0)):.3f}%</td><td>{float(r.get('avg_loss_pct', 0)):.3f}%</td><td>{float(r.get('saved_loss_krw', 0)):.0f}원</td><td>{float(r.get('early_exit_missed_profit_krw', 0)):.0f}원</td></tr>"
        for r in rows
    )


def _latency_rows(rows: list[dict]) -> str:
    wanted = {(0, 0.0), (500, 0.05), (1000, 0.1), (2000, 0.15)}
    picked = [r for r in rows if (int(r.get("latency_ms", 0)), float(r.get("slippage_pct", 0))) in wanted]
    if not picked:
        return "<tr><td colspan='4'>검증 데이터 없음</td></tr>"
    return "".join(
        f"<tr><td>{int(r.get('latency_ms', 0))}ms / {float(r.get('slippage_pct', 0)):.2f}%</td><td>{float(r.get('profit_factor', 0)):.3f}</td><td>{float(r.get('expectancy_pct', 0)):.3f}%</td><td>{float(r.get('final_pnl_krw', 0)):.0f}원</td></tr>"
        for r in picked
    )


def _trade_rows(rows: list[dict]) -> str:
    if not rows:
        return "<tr><td colspan='6'>대상 거래 없음</td></tr>"
    return "".join(
        f"<tr><td>{escape(str(t.get('date_kst', '')))}</td><td>{escape(str(t.get('market', '')))}</td><td>{escape(str(t.get('micro_exit_decision', '')))}</td><td>{float(t.get('realized_pnl_pct', 0)):.3f}%</td><td>{float(t.get('hold_seconds', 0)):.0f}초</td><td>{escape(str(t.get('data_quality', '')))}</td></tr>"
        for t in rows
    )
