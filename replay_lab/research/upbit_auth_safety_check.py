from __future__ import annotations

from adapters.upbit_private_auth_check import check_upbit_auth_safety


def run_upbit_auth_safety_check(read_check: bool = False) -> dict:
    return check_upbit_auth_safety(read_check=read_check)
