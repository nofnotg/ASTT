from __future__ import annotations

from pathlib import Path

from replay_lab.paths import ROOT_DIR


def load_source_registry(path: Path | None = None) -> dict:
    registry_path = path or ROOT_DIR / "research_external" / "source_registry.yaml"
    text = registry_path.read_text(encoding="utf-8")
    sources = []
    current: dict | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line == "sources:":
            continue
        if line.startswith("- "):
            if current:
                sources.append(current)
            current = {}
            line = line[2:]
        if ":" in line and current is not None:
            key, value = line.split(":", 1)
            value = value.strip()
            if value == "null":
                parsed: str | bool | None = None
            elif value.lower() in {"true", "false"}:
                parsed = value.lower() == "true"
            else:
                parsed = value
            current[key.strip()] = parsed
    if current:
        sources.append(current)
    return {"sources": sources}
