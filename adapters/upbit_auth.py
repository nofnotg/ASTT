from __future__ import annotations

import hashlib
import uuid
from urllib.parse import urlencode

import jwt

from app.config import Settings, get_settings


class UpbitAuth:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def make_headers(self, params: dict | None = None) -> dict[str, str]:
        if not self.settings.has_upbit_keys:
            raise RuntimeError("UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY are required for authenticated API calls")
        payload = {
            "access_key": self.settings.upbit_access_key,
            "nonce": str(uuid.uuid4()),
        }
        if params:
            query_string = urlencode(params, doseq=True).encode()
            payload["query_hash"] = hashlib.sha512(query_string).hexdigest()
            payload["query_hash_alg"] = "SHA512"
        token = jwt.encode(payload, self.settings.upbit_secret_key, algorithm="HS512")
        return {"Authorization": f"Bearer {token}"}

