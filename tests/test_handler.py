"""Tests for the handler module."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path
from typing import Any, cast

import pytest

from src import config, handler, storage as storage_module

_SAMPLE_EVENT_PATH = (
    Path(__file__).resolve().parents[1]
    / "sample_event"
    / "gcs.storage.object.v1.json"
)

NOT_FOUND_ERROR = cast(type[Exception], storage_module.NotFound)


def _load_event() -> dict[str, Any]:
    with _SAMPLE_EVENT_PATH.open("r", encoding="utf-8") as fh:
        return cast(dict[str, Any], json.load(fh))


@pytest.fixture(autouse=True)
def _configure_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("DEST_BUCKET", "dest-bucket")
    monkeypatch.setenv("PROJECT_ID", "project-id")
    monkeypatch.setenv("METADATA_PREFIX", "metadata/")
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_handler_writes_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    event = _load_event()
    captured: dict[str, Any] = {}

    def fake_head(bucket: str, name: str) -> None:
        assert bucket == "source-bucket"
        assert name == "text/sample.txt"
        return None

    def fake_put(bucket: str, key: str, data: dict[str, Any]) -> None:
        captured["bucket"] = bucket
        captured["key"] = key
        captured["data"] = data

    monkeypatch.setattr("src.handler.storage.head_object", fake_head)
    monkeypatch.setattr("src.handler.storage.put_json", fake_put)

    handler.gcs_file_observer(event)

    assert captured["bucket"] == "dest-bucket"
    assert captured["key"] == "metadata/source-bucket/text__sample.txt.json"
    assert captured["data"]["exists"] is True
    assert captured["data"]["detected_format"] == "text"


def test_handler_marks_missing_object(monkeypatch: pytest.MonkeyPatch) -> None:
    event = _load_event()
    captured: dict[str, Any] = {}

    def fake_head(_: str, __: str) -> None:
        raise NOT_FOUND_ERROR("not found")

    def fake_put(bucket: str, key: str, data: dict[str, Any]) -> None:
        captured["data"] = data

    monkeypatch.setattr("src.handler.storage.head_object", fake_head)
    monkeypatch.setattr("src.handler.storage.put_json", fake_put)

    handler.gcs_file_observer(event)

    assert captured["data"]["exists"] is False


def test_handler_skips_same_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    event = _load_event()

    monkeypatch.setenv("DEST_BUCKET", "source-bucket")
    config.get_settings.cache_clear()

    called = False

    def fake_put(*_: Any, **__: Any) -> None:  # pragma: no cover - should not run
        nonlocal called
        called = True

    monkeypatch.setattr("src.handler.storage.put_json", fake_put)

    handler.gcs_file_observer(event)

    assert called is False


def test_extract_event_data_invalid_type() -> None:
    with pytest.raises(TypeError):
        handler._extract_event_data(cast(Any, "bad"))


def test_extract_event_data_invalid_payload() -> None:
    with pytest.raises(TypeError):
        handler._extract_event_data({"data": "not-a-dict"})
