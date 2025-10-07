"""Data models for the gcs-file-observer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_OBSERVER_VERSION = "1.0.0"


class StorageObjectData(BaseModel):
    """Model representing the Cloud Storage finalize event payload."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    bucket: str
    name: str
    size: int | None = None
    content_type: str | None = Field(None, alias="contentType")
    md5_hash: str | None = Field(None, alias="md5Hash")
    crc32c: str | None = None
    time_created: datetime | None = Field(None, alias="timeCreated")
    updated: datetime | None = None
    storage_class: str | None = Field(None, alias="storageClass")
    generation: int | None = None
    metageneration: int | None = None
    source_etag: str | None = Field(None, alias="etag")

    @field_validator("size", mode="before")
    @classmethod
    def _parse_size(cls, value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(value)

    @field_validator("generation", "metageneration", mode="before")
    @classmethod
    def _parse_int(cls, value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(value)


class FileMetadata(BaseModel):
    """Metadata persisted for observed objects."""

    model_config = ConfigDict(populate_by_name=True, ser_json_timedelta="iso8601")

    source_bucket: str
    object_name: str
    size: int | None = None
    content_type: str | None = None
    md5: str | None = None
    crc32c: str | None = None
    time_created: datetime | None = None
    updated: datetime | None = None
    storage_class: str | None = None
    generation: int | None = None
    metageneration: int | None = None
    detected_format: str | None = None
    source_etag: str | None = None
    exists: bool = True
    observer_version: str = Field(default=_OBSERVER_VERSION)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    @field_validator("object_name")
    @classmethod
    def _validate_object_name(cls, value: str) -> str:
        if not value:
            raise ValueError("object_name must not be empty")
        return value


__all__ = ["FileMetadata", "StorageObjectData"]
