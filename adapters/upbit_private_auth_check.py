from __future__ import annotations

import os

from adapters.upbit_auth import UpbitAuth
from app.config import get_settings


def check_upbit_auth_safety(read_check: bool = False) -> dict:
    settings = get_settings()
    access = settings.upbit_access_key or os.getenv("UPBIT_ACCESS_KEY", "")
    secret = settings.upbit_secret_key or os.getenv("UPBIT_SECRET_KEY", "")
    allowed_ip = settings.upbit_allowed_ip or os.getenv("UPBIT_ALLOWED_IP", "")
    result = {
        "access_key_loaded": bool(access),
        "secret_key_loaded": bool(secret),
        "allowed_ip_loaded": bool(allowed_ip),
        "access_key_masked": _mask(access),
        "jwt_build_ok": False,
        "private_read_check": "SKIPPED",
        "orders_or_test_called": False,
        "withdraw_called": False,
        "warnings": [],
    }
    if access and secret:
        try:
            UpbitAuth(settings).make_headers()
            result["jwt_build_ok"] = True
        except Exception as exc:
            result["warnings"].append(f"jwt_build_failed:{type(exc).__name__}")
    if read_check:
        result["private_read_check"] = "SKIPPED"
        result["warnings"].append("read_check_not_implemented_to_avoid_private_side_effects")
    return result


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}****{value[-4:]}"
