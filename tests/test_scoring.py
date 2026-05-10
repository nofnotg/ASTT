from app.config import get_settings
from decision.debate_engine import decide
from decision.scoring import weighted_score
from personas.base import PersonaResult


def result(name, score, veto=False):
    return PersonaResult(persona_name=name, market="KRW-BTC", score=score, decision="PASS", reasons=[name], veto=veto, veto_reason="blocked" if veto else None)


def test_weighted_score():
    results = [result("Mr.K", 50), result("매기", 90), result("Rezo", 80), result("CostA", 70), result("Iris", 90)]
    assert weighted_score(results) == 81.5


def test_iris_veto_rejects():
    settings = get_settings(TRADING_MODE="PAPER")
    results = [result("Mr.K", 100), result("매기", 100), result("Rezo", 100), result("CostA", 100), result("Iris", 10, veto=True)]
    final = decide("KRW-BTC", results, settings)
    assert final.decision == "REJECT"
    assert final.vetoed is True

