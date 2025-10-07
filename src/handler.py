"""Cloud Function entrypoint handling Cloud Storage finalize events."""

from __future__ import annotations

import logging
from typing import Any

from cloudevents.http import CloudEvent

from . import storage
from .config import get_settings
from .extractor import detect_format
from .models import FileMetadata, StorageObjectData

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _extract_event_data(cloudevent: CloudEvent | dict[str, Any]) -> dict[str, Any]:
    if isinstance(cloudevent, CloudEvent):
        payload = cloudevent.data
    elif isinstance(cloudevent, dict):
        payload = cloudevent.get("data")
    else:
        raise TypeError("Unsupported CloudEvent payload type")
    if not isinstance(payload, dict):
        raise TypeError("CloudEvent data must be a mapping")
    return payload


def _sanitize_object_name(name: str) -> str:
    return name.replace("/", "__")


def _build_metadata_key(prefix: str, bucket: str, object_name: str) -> str:
    sanitized = _sanitize_object_name(object_name)
    return f"{prefix}{bucket}/{sanitized}.json"


def gcs_file_observer(cloudevent: CloudEvent | dict[str, Any]) -> None:
    """Handle Cloud Storage finalize events."""

    settings = get_settings()
    try:
        payload_dict = _extract_event_data(cloudevent)
        event = StorageObjectData.model_validate(payload_dict)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("event_validation_failed error=%s", exc)
        raise

    if event.bucket == settings.dest_bucket:
        logger.info(
            "skip_self_write source_bucket=%s dest_bucket=%s object=%s",
            event.bucket,
            settings.dest_bucket,
            event.name,
        )
        return

    detected_format = detect_format(event.name, event.content_type, event.size)

    exists = True
    try:
        storage.head_object(event.bucket, event.name)
    except storage.NotFound:
        exists = False
        logger.warning(
            "source_missing bucket=%s object=%s", event.bucket, event.name
        )

    metadata = FileMetadata(
        source_bucket=event.bucket,
        object_name=event.name,
        size=event.size,
        content_type=event.content_type,
        md5=event.md5_hash,
        crc32c=event.crc32c,
        time_created=event.time_created,
        updated=event.updated,
        storage_class=event.storage_class,
        generation=event.generation,
        metageneration=event.metageneration,
        detected_format=detected_format,
        source_etag=event.source_etag,
        exists=exists,
    )

    metadata_key = _build_metadata_key(
        settings.normalized_prefix(), event.bucket, event.name
    )

    storage.put_json(
        settings.dest_bucket,
        metadata_key,
        metadata.model_dump(mode="json"),
    )

    logger.info(
        "metadata_written source_bucket=%s object=%s dest_bucket=%s key=%s exists=%s format=%s",
        event.bucket,
        event.name,
        settings.dest_bucket,
        metadata_key,
        exists,
        detected_format,
    )


__all__ = ["gcs_file_observer"]
