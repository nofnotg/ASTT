from __future__ import annotations

import webbrowser


def open_dashboard(url: str = "http://127.0.0.1:8787") -> bool:
    return webbrowser.open(url)
