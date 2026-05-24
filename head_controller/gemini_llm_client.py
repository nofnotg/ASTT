from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from head_controller.llm_client_base import HeadControllerLLMClient, LLMResult


class GeminiHeadControllerClient(HeadControllerLLMClient):
    provider = "gemini"

    def __init__(self, api_key: str, model: str | None = None):
        self.api_key = api_key
        self.model = model or os.environ.get("HEAD_CONTROLLER_GEMINI_MODEL", "gemini-1.5-flash")

    def analyze(self, context: dict) -> LLMResult:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?{urllib.parse.urlencode({'key': self.api_key})}"
        payload = {"contents": [{"parts": [{"text": "Return compact JSON Head Controller analysis. No live trading. Context: " + json.dumps(context, ensure_ascii=False)[:6000]}]}]}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return LLMResult(self.provider, True, text)
        except Exception as exc:
            return LLMResult(self.provider, False, "", type(exc).__name__)
