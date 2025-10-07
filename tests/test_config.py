"""Tests for configuration handling."""

from __future__ import annotations

import pytest

from src import config


def test_normalized_prefix_appends_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEST_BUCKET", "dest")
    monkeypatch.setenv("PROJECT_ID", "pid")
    monkeypatch.setenv("METADATA_PREFIX", "meta")
    config.get_settings.cache_clear()

    settings = config.get_settings()
    assert settings.normalized_prefix() == "meta/"

    config.get_settings.cache_clear()


def test_normalized_prefix_retains_single_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEST_BUCKET", "dest")
    monkeypatch.setenv("PROJECT_ID", "pid")
    monkeypatch.setenv("METADATA_PREFIX", "meta/")
    config.get_settings.cache_clear()

    settings = config.get_settings()
    assert settings.normalized_prefix() == "meta/"

    config.get_settings.cache_clear()
