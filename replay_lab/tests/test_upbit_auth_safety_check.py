from replay_lab.research.upbit_auth_safety_check import run_upbit_auth_safety_check


def test_upbit_auth_safety_check_masks_and_never_orders(monkeypatch):
    monkeypatch.setenv("UPBIT_ACCESS_KEY", "abcd1234wxyz")
    monkeypatch.setenv("UPBIT_SECRET_KEY", "secret1234")
    monkeypatch.setenv("UPBIT_ALLOWED_IP", "112.157.222.152")

    result = run_upbit_auth_safety_check()

    assert result["access_key_loaded"] is True
    assert result["secret_key_loaded"] is True
    assert result["allowed_ip_loaded"] is True
    assert result["access_key_masked"] == "abcd****wxyz"
    assert result["orders_or_test_called"] is False
    assert result["withdraw_called"] is False
