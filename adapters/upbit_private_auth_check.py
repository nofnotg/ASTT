from __future__ import annotations

import os

from adapters.upbit_auth import UpbitAuth
from app.config import get_settings


def check_upbit_auth_safety(read_check: bool = False) -> dict:
    settings = get_settings()
    process_access = os.getenv("UPBIT_ACCESS_KEY", "")
    process_secret = os.getenv("UPBIT_SECRET_KEY", "")
    process_allowed_ip = os.getenv("UPBIT_ALLOWED_IP", "")
    access = process_access or settings.upbit_access_key
    secret = process_secret or settings.upbit_secret_key
    allowed_ip = process_allowed_ip or settings.upbit_allowed_ip
    auth_settings = settings.model_copy(update={"upbit_access_key": access, "upbit_secret_key": secret, "upbit_allowed_ip": allowed_ip})
    result = {
        "access_key_loaded": bool(access),
        "secret_key_loaded": bool(secret),
        "allowed_ip_loaded": bool(allowed_ip),
        "access_key_masked": _mask(access),
        "env_source": _source(process_access, settings.upbit_access_key),
        "allowed_ip_source": _source(process_allowed_ip, settings.upbit_allowed_ip),
        "missing_variables": _missing(access, secret, allowed_ip),
        "jwt_build_ok": False,
        "private_read_check": "SKIPPED",
        "orders_or_test_called": False,
        "withdraw_called": False,
        "warnings": [],
    }
    if access and secret:
        try:
            UpbitAuth(auth_settings).make_headers()
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


def _source(process_value: str, settings_value: str) -> str:
    if process_value:
        return "process_env"
    if settings_value:
        return "settings_env_file"
    return "missing"


def _missing(access: str, secret: str, allowed_ip: str) -> list[str]:
    missing = []
    if not access:
        missing.append("UPBIT_ACCESS_KEY")
    if not secret:
        missing.append("UPBIT_SECRET_KEY")
    if not allowed_ip:
        missing.append("UPBIT_ALLOWED_IP")
    return missing
