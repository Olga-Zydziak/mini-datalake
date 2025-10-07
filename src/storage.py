"""Google Cloud Storage helpers with retry logic."""

from __future__ import annotations

import json
from typing import Any

from google.api_core import exceptions as core_exceptions
from google.cloud import storage  # type: ignore[attr-defined]
from google.cloud.exceptions import NotFound
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

_CLIENT: storage.Client | None = None

_TRANSIENT_ERRORS = (
    core_exceptions.ServiceUnavailable,
    core_exceptions.TooManyRequests,
    core_exceptions.DeadlineExceeded,
)


def _get_client() -> storage.Client:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = storage.Client()
    return _CLIENT


@retry(
    retry=retry_if_exception_type(_TRANSIENT_ERRORS),
    wait=wait_random_exponential(multiplier=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _reload_blob(bucket_name: str, blob_name: str) -> storage.Blob:
    client = _get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.reload()
    return blob


@retry(
    retry=retry_if_exception_type(_TRANSIENT_ERRORS),
    wait=wait_random_exponential(multiplier=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _upload_json(bucket_name: str, blob_name: str, payload: str) -> None:
    client = _get_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.cache_control = "no-cache"
    blob.content_type = "application/json"
    blob.upload_from_string(payload)


def head_object(bucket_name: str, blob_name: str) -> storage.Blob:
    """Retrieve metadata for an object without downloading its contents."""

    try:
        return _reload_blob(bucket_name, blob_name)
    except NotFound as exc:
        raise exc


def put_json(bucket_name: str, blob_name: str, data: dict[str, Any]) -> None:
    """Upload JSON metadata to Cloud Storage."""

    payload = json.dumps(data, separators=(",", ":"), sort_keys=True)
    _upload_json(bucket_name, blob_name, payload)


__all__ = ["NotFound", "head_object", "put_json"]
