from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from analysis.v686_runtime_dashboard import build_v686_local_dashboard_summary
from local_dashboard.dashboard_api_schema import api_response
from local_dashboard.dashboard_config import DashboardConfig
from local_dashboard.dashboard_data_service import DashboardDataService
from local_dashboard.dashboard_routes import route_map
from local_dashboard.dashboard_security import is_forbidden_path, security_status


def start_dashboard(host: str = "127.0.0.1", port: int = 8787, reports_dir: str = "docs/reports") -> dict[str, Any]:
    build_v686_local_dashboard_summary(host, port, reports_dir)
    config = DashboardConfig(host=host, port=port, reports_dir=reports_dir)
    service = DashboardDataService(config.reports_dir, config.data_dir)
    routes = route_map(service)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if is_forbidden_path(parsed.path):
                self._json({"ok": False, "error": "live/order endpoint disabled", **security_status()}, 403)
                return
            if parsed.path in routes:
                self._json(api_response(routes[parsed.path]()))
                return
            if parsed.path in {"/", "/index.html"}:
                self._html(_index_html())
                return
            if parsed.path == "/static/dashboard.css":
                self._css(_css())
                return
            if parsed.path == "/static/dashboard.js":
                self._js(_js())
                return
            self._json({"ok": False, "error": "not found"}, 404)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/api/control-tower/review":
                self._json(api_response(service.control_tower() or {"review_generated": False, "fallback_used": True, **security_status()}))
                return
            if parsed.path in {"/api/server/stop-paper", "/api/reports/rebuild"}:
                self._json(api_response({"accepted": False, "reason": "manual CLI operation required", **security_status()}))
                return
            self._json({"ok": False, "error": "POST endpoint disabled", **security_status()}, 403)

        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def _json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _css(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/css; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _js(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"ASTT V6.8.6 local dashboard: http://{host}:{port}")
    server.serve_forever()
    return {"dashboard_ready": True, "host": host, "port": port, "server_running": True}


def _index_html() -> str:
    return (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8") if (Path(__file__).parent / "templates" / "index.html").exists() else _fallback_html()


def _fallback_html() -> str:
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ASTT Control</title><link rel="stylesheet" href="/static/dashboard.css"></head><body><main><h1>ASTT Control Dashboard</h1><div id="app">Loading...</div></main><script src="/static/dashboard.js"></script></body></html>"""


def _css() -> str:
    path = Path(__file__).parent / "static" / "dashboard.css"
    return path.read_text(encoding="utf-8") if path.exists() else "body{font-family:Arial,sans-serif}"


def _js() -> str:
    path = Path(__file__).parent / "static" / "dashboard.js"
    return path.read_text(encoding="utf-8") if path.exists() else "console.log('ASTT dashboard')"
