from __future__ import annotations

from pydantic import BaseModel


class ExperimentConfig(BaseModel):
    experiment_id: str
    name: str
    description: str = ""
    config_version: str = "v0.1"

