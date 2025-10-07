"""Tests for data models."""

from datetime import UTC, datetime

import pytest

from src.models import FileMetadata, StorageObjectData


def test_storage_object_data_parses_string_fields() -> None:
    data = StorageObjectData.model_validate(
        {
            "bucket": "source-bucket",
            "name": "path/to/file.txt",
            "size": "42",
            "contentType": "text/plain",
            "timeCreated": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T01:00:00Z",
            "generation": "123",
            "metageneration": "1",
        }
    )

    assert data.size == 42
    assert data.generation == 123
    assert data.metageneration == 1
    assert data.time_created == datetime(2023, 1, 1, tzinfo=UTC)


def test_file_metadata_requires_object_name() -> None:
    with pytest.raises(ValueError):
        FileMetadata(source_bucket="bucket", object_name="")


def test_file_metadata_defaults() -> None:
    metadata = FileMetadata(source_bucket="bucket", object_name="object")
    assert metadata.exists is True
    assert metadata.observer_version == "1.0.0"
    assert metadata.observed_at.tzinfo == UTC
