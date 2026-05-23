from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

from replay_lab.paths import ROOT_DIR, REPLAY_STORE_DIR
from replay_lab.research.forward_micro_validation import validate_forward_micro_sessions
from replay_lab.research.micro_cost_survival_test import run_micro_cost_survival_test
from replay_lab.research.micro_data_quality_audit import audit_micro_data_quality
from replay_lab.research.micro_entry_exit_effectiveness import validate_micro_entry_exit_effectiveness


@dataclass(frozen=True)
class ForwardMicroHTMLReportBuilder:
    store_dir: Path = REPLAY_STORE_DIR
    docs_root: Path = ROOT_DIR / "docs" / "reports"

    @property
    def out_dir(self) -> Path:
        return self.store_dir / "reports" / "forward_micro"

    def build(self, sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "live_micro") -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.docs_root.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "audit": audit_micro_data_quality(sessions_dir),
            "validation": validate_forward_micro_sessions(sessions_dir),
            "cost_survival": run_micro_cost_survival_test(sessions_dir),
            "entry_exit_effectiveness": validate_micro_entry_exit_effectiveness(sessions_dir),
        }
        payload["live_readiness"] = _readiness(payload)
        html = self._html(payload)
        md = self._markdown(payload)
        (self.out_dir / "forward_micro_report.html").write_text(html, encoding="utf-8")
        (self.out_dir / "forward_micro_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        (self.out_dir / "forward_micro_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_forward_micro_report.html").write_text(html, encoding="utf-8")
        (self.docs_root / "latest_forward_micro_report.md").write_text(md, encoding="utf-8")
        (self.docs_root / "latest_forward_micro_summary.json").write_text(json.dumps(_summary(payload), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return self.out_dir / "forward_micro_report.html"

    def _markdown(self, payload: dict) -> str:
        summary = _summary(payload)
        return f"""# ASTT V5.5.1 Forward Micro Report

이 리포트는 실제 주문이 아니라 PAPER forward 검증입니다.
실전 전환 판단은 데이터 품질과 0.05% 비용 생존 여부를 기준으로 합니다.

- 실전 판정: {summary['live_readiness']}
- 수집 세션 수: {summary['session_count']}
- 총 기록 시간: {summary['total_recording_minutes']}
- GOOD/PARTIAL 거래 수: {summary['good_partial_entry_count']}
- realistic_1 PF: {summary['realistic_1_pf']:.4f}
- 0.05% 비용 생존 여부: {summary['realistic_1_survives']}

PF가 높아도 데이터 품질이 낮으면 믿을 수 없습니다.
초단타는 작은 비용에도 결과가 뒤집힐 수 있습니다.
0.05% 비용 조건에서 살아남지 못하면 실전 금지입니다.
UNAVAILABLE 거래는 실전성 평가에서 제외합니다.

## 데이터 품질 현황
{json.dumps(payload.get('audit', {}).get('quality_distribution', {}), ensure_ascii=False)}

## GOOD/PARTIAL 데이터만 본 성과
entry_count={summary['good_partial_entry_count']}, realistic_1_pf={summary['realistic_1_pf']:.4f}, expectancy={summary['realistic_1_expectancy']:.4f}%

## 초봉 진입/청산 효과
아직 GOOD/PARTIAL 거래가 30건 미만이므로 개선 여부를 확정하지 않습니다.
"""

    def _html(self, payload: dict) -> str:
        s = _summary(payload)
        cards = [
            ("실전 판정", s["live_readiness"]),
            ("수집 세션", s["session_count"]),
            ("총 기록 시간", f"{s['total_recording_minutes']:.1f}분"),
            ("GOOD/PARTIAL 거래", s["good_partial_entry_count"]),
            ("UNAVAILABLE", s["unavailable_count"]),
            ("realistic_1 PF", f"{s['realistic_1_pf']:.3f}"),
            ("realistic_1 기대값", f"{s['realistic_1_expectancy']:.4f}%"),
            ("0.05% 비용 생존", s["realistic_1_survives"]),
        ]
        card_html = "".join(f"<div class='card'><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>" for k, v in cards)
        gp = payload.get("validation", {}).get("results", {}).get("GOOD_PLUS_PARTIAL", {})
        cost_rows = "".join(f"<tr><td>{escape(str(r.get('scenario')))}</td><td>{float(r.get('profit_factor', 0)):.3f}</td><td>{float(r.get('expectancy_pct', 0)):.4f}%</td><td>{float(r.get('pnl_krw', 0)):.0f}원</td><td>{escape(str(r.get('survives')))}</td></tr>" for r in payload.get("cost_survival", {}).get("results", []))
        effect_rows = "".join(f"<tr><td>{escape(str(r.get('model')))}</td><td>{r.get('entry_count', 0)}</td><td>{r.get('cancel_count', 0)}</td><td>{r.get('avoided_loss_count', 0)}</td><td>{r.get('missed_win_count', 0)}</td><td>{float(r.get('profit_factor_realistic_1', 0)):.3f}</td><td>{float(r.get('expectancy_realistic_1', 0)):.4f}%</td></tr>" for r in payload.get("entry_exit_effectiveness", {}).get("results", []))
        return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ASTT V5.5.1 Forward Micro</title><style>body{{margin:0;background:#0f172a;color:#e5e7eb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}}main{{max-width:1120px;margin:auto;padding:28px 18px}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}.card,section{{background:#111c33;border:1px solid #24324d;border-radius:8px;padding:16px}}.card span{{display:block;color:#9ca3af;font-size:13px}}.card strong{{display:block;font-size:22px;margin-top:6px}}section{{margin-top:14px}}p{{color:#cbd5e1;line-height:1.65}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{border-bottom:1px solid #263653;padding:8px;text-align:left}}@media(max-width:820px){{.grid{{grid-template-columns:1fr 1fr}}}}</style></head><body><main><h1>ASTT V5.5.1 Live Micro Data & Forward Paper</h1><p>이 리포트는 실제 주문이 아니라 PAPER forward 검증입니다. 실전 전환 판단은 데이터 품질과 0.05% 비용 생존 여부를 기준으로 합니다.</p><div class="grid">{card_html}</div><section><h2>한눈에 보는 결론</h2><p><b>{escape(str(s['live_readiness']))}</b>. GOOD/PARTIAL 거래가 30건 미만이면 PF가 높아도 실전 근거가 아닙니다.</p></section><section><h2>지금은 왜 실전 금지인가</h2><p>PF가 높아도 데이터 품질이 낮으면 믿을 수 없습니다. 초단타는 작은 비용에도 결과가 뒤집힐 수 있습니다. 0.05% 비용 조건에서 살아남지 못하면 실전 금지입니다. UNAVAILABLE 거래는 실전성 평가에서 제외합니다.</p></section><section><h2>데이터 품질 현황</h2><p>{escape(json.dumps(payload['audit'].get('quality_distribution', {}), ensure_ascii=False))}</p></section><section><h2>수집된 실시간 데이터 요약</h2><p>세션 {s['session_count']}개, 총 기록 시간 {s['total_recording_minutes']:.1f}분, replay 가능 세션 {payload['audit'].get('replayable_session_count', 0)}개입니다.</p></section><section><h2>GOOD/PARTIAL 데이터만 본 성과</h2><p>entry={gp.get('entry_count', 0)}, realistic_1 PF={gp.get('profit_factor_realistic_1', 0):.3f}, expectancy={gp.get('expectancy_realistic_1', 0):.4f}%</p></section><section><h2>비용 미반영 vs 현실 비용 반영 성과 / 0.05% 비용 생존 테스트</h2><table><thead><tr><th>시나리오</th><th>PF</th><th>기대값</th><th>PnL</th><th>생존</th></tr></thead><tbody>{cost_rows}</tbody></table></section><section><h2>초봉 진입 확인 효과 / 초봉 조기청산 효과</h2><table><thead><tr><th>모델</th><th>진입</th><th>취소</th><th>막은 손실</th><th>놓친 승리</th><th>PF realistic_1</th><th>기대값</th></tr></thead><tbody>{effect_rows}</tbody></table></section><section><h2>대표 성공 거래 / 대표 실패 거래</h2><p>현재 표본은 2건뿐이라 대표 패턴을 확정하지 않습니다. 2주 데이터 축적 후 이 섹션을 실제 거래 사례로 채웁니다.</p></section><section><h2>실전 전환 판단</h2><p>{escape(str(s['live_readiness']))}. 이번 단계에서는 MICRO_LIVE_READY를 출력하지 않습니다.</p></section><section><h2>다음 액션</h2><p>2주 동안 누적 20시간 이상 recording을 쌓고, GOOD/PARTIAL 거래 30건 이상에서 realistic_1 PF와 기대값을 다시 확인해야 합니다.</p></section></main></body></html>"""


def _summary(payload: dict) -> dict:
    audit = payload.get("audit", {})
    gp = payload.get("validation", {}).get("results", {}).get("GOOD_PLUS_PARTIAL", {})
    quality = audit.get("quality_distribution", {})
    return {"schema_version": "1.0", "generated_at": payload.get("generated_at"), "live_readiness": payload.get("live_readiness", "LIVE_NOT_ALLOWED"), "session_count": audit.get("session_count", 0), "total_recording_minutes": audit.get("total_recording_minutes", 0.0), "good_partial_entry_count": gp.get("entry_count", 0), "unavailable_count": quality.get("UNAVAILABLE", 0), "realistic_1_pf": gp.get("profit_factor_realistic_1", 0.0), "realistic_1_expectancy": gp.get("expectancy_realistic_1", 0.0), "realistic_1_survives": payload.get("cost_survival", {}).get("realistic_1_survives", False)}


def _readiness(payload: dict) -> str:
    summary = _summary({**payload, "live_readiness": "LIVE_NOT_ALLOWED"})
    if summary["good_partial_entry_count"] >= 30 and summary["realistic_1_pf"] >= 1.1 and summary["realistic_1_expectancy"] > 0:
        return "PAPER_MORE_REQUIRED"
    return "LIVE_NOT_ALLOWED"
