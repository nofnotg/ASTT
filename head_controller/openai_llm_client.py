from __future__ import annotations

import json
import os
import urllib.request

from head_controller.llm_client_base import HeadControllerLLMClient, LLMResult


class OpenAIHeadControllerClient(HeadControllerLLMClient):
    provider = "openai"

    def __init__(self, api_key: str, model: str | None = None):
        self.api_key = api_key
        self.model = model or os.environ.get("HEAD_CONTROLLER_OPENAI_MODEL", "gpt-4o-mini")

    def analyze(self, context: dict) -> LLMResult:
        payload = {
            "model": self.model,
            "input": "Return a compact JSON Head Controller analysis. No live trading. Context: " + json.dumps(context, ensure_ascii=False)[:6000],
        }
        req = urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(payload).encode("utf-8"), headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data.get("output_text") or json.dumps(data)
            return LLMResult(self.provider, True, text)
        except Exception as exc:
            return LLMResult(self.provider, False, "", type(exc).__name__)
