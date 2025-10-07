"""Tests for storage helper functions."""

from __future__ import annotations

import json
from typing import cast

import pytest

from src import storage


class _FakeBlob:
    def __init__(self) -> None:
        self.cache_control: str | None = None
        self.content_type: str | None = None
        self.payload: str | None = None

    def upload_from_string(self, payload: str) -> None:
        self.payload = payload

    def reload(self) -> None:  # pragma: no cover - not used in this fake
        return None


class _FakeBucket:
    def __init__(self, blob: _FakeBlob) -> None:
        self._blob = blob
        self.requested_blob: str | None = None

    def blob(self, name: str) -> _FakeBlob:
        self.requested_blob = name
        return self._blob


class _FakeClient:
    def __init__(self, bucket: _FakeBucket) -> None:
        self._bucket = bucket
        self.requested_bucket: str | None = None

    def bucket(self, name: str) -> _FakeBucket:
        self.requested_bucket = name
        return self._bucket


@pytest.fixture(name="fake_client")
def fake_client_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[_FakeClient, _FakeBucket, _FakeBlob]:
    blob = _FakeBlob()
    bucket = _FakeBucket(blob)
    client = _FakeClient(bucket)
    monkeypatch.setattr(storage, "_CLIENT", client)
    monkeypatch.setattr(storage, "_get_client", lambda: client)
    return client, bucket, blob


def test_put_json_uploads_payload(fake_client: tuple[_FakeClient, _FakeBucket, _FakeBlob]) -> None:
    client, bucket, blob = fake_client

    storage.put_json("dest-bucket", "metadata/file.json", {"foo": "bar"})

    assert bucket.requested_blob == "metadata/file.json"
    assert blob.cache_control == "no-cache"
    assert blob.content_type == "application/json"
    assert json.loads(blob.payload or "{}") == {"foo": "bar"}
    assert client.requested_bucket == "dest-bucket"


def test_head_object_propagates_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    not_found = cast(type[Exception], storage.NotFound)

    def fake_reload(bucket: str, name: str) -> None:
        raise not_found("not found")

    monkeypatch.setattr(storage, "_reload_blob", fake_reload)

    with pytest.raises(storage.NotFound):
        storage.head_object("bucket", "object")
