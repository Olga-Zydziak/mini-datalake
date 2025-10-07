"""Utility functions for determining object metadata."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

_EXTENSION_MAPPING = {
    "csv": "csv",
    "json": "json",
    "ndjson": "jsonl",
    "txt": "text",
    "log": "text",
    "parquet": "parquet",
    "avro": "avro",
    "orc": "orc",
    "gz": "gzip",
    "zip": "zip",
    "tar": "tar",
    "xml": "xml",
    "pdf": "pdf",
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "png": "png",
    "gif": "gif",
    "bmp": "bmp",
    "tif": "tiff",
    "tiff": "tiff",
}

_CONTENT_TYPE_MAPPING = {
    "application/json": "json",
    "application/x-ndjson": "jsonl",
    "text/csv": "csv",
    "text/plain": "text",
    "application/pdf": "pdf",
    "application/x-parquet": "parquet",
    "application/octet-stream": "binary",
    "application/zip": "zip",
    "application/gzip": "gzip",
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/gif": "gif",
}


def _iter_suffixes(name: str) -> Iterable[str]:
    path = Path(name)
    for suffix in path.suffixes:
        yield suffix.lstrip(".").lower()


def detect_format(name: str | None, content_type: str | None, size: int | None = None) -> str:
    """Best-effort detection of an object's format."""

    if size == 0:
        return "empty"

    suffixes = list(_iter_suffixes(name or ""))
    for suffix in reversed(suffixes):
        if suffix in _EXTENSION_MAPPING:
            return _EXTENSION_MAPPING[suffix]

    if content_type:
        lowered = content_type.lower()
        if lowered in _CONTENT_TYPE_MAPPING:
            return _CONTENT_TYPE_MAPPING[lowered]
        for candidate, alias in _CONTENT_TYPE_MAPPING.items():
            if candidate in lowered:
                return alias
        if "+json" in lowered:
            return "json"
        if "+xml" in lowered:
            return "xml"

    if suffixes:
        return suffixes[-1]

    if content_type:
        return content_type.lower()

    return "unknown"


__all__ = ["detect_format"]
