from __future__ import annotations

from pydantic import BaseModel, Field


class MainImportArtifact(BaseModel):
    artifact_type: str
    schema_version: str = "1.0"
    status: str
    source_experiment_id: str
    base_config_version: str
    target_config_version: str
    patch: dict = Field(default_factory=dict)
    validation: dict = Field(default_factory=dict)

    def assert_importable(self) -> None:
        if self.status != "APPROVED":
            raise ValueError("Only APPROVED replay artifacts can be imported by the main app")
        if self.schema_version != "1.0":
            raise ValueError("Unsupported replay artifact schema_version")

