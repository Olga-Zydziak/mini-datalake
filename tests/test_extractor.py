"""Tests for extractor utilities."""

from src.extractor import detect_format


def test_detect_format_from_extension() -> None:
    assert detect_format("data/file.json", "application/json") == "json"


def test_detect_format_empty_file() -> None:
    assert detect_format("anything.txt", "text/plain", size=0) == "empty"


def test_detect_format_fallback_to_content_type() -> None:
    assert detect_format("file.bin", "text/csv") == "csv"


def test_detect_format_unknown() -> None:
    assert detect_format("file.unknown", None) == "unknown"


def test_detect_format_multi_suffix() -> None:
    assert detect_format("archive.tar.gz", "application/gzip") == "gzip"


def test_detect_format_partial_content_type_match() -> None:
    assert detect_format("data", "application/vnd.custom+json") == "json"
