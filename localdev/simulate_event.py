"""Simulate invocation of the Cloud Function locally."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.config import get_settings
from src.handler import gcs_file_observer

_SAMPLE_PATH = Path(__file__).resolve().parents[1] / "sample_event" / "gcs.storage.object.v1.json"


def load_sample_event() -> dict:
    with _SAMPLE_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    os.environ.setdefault("DEST_BUCKET", "destination-bucket")
    os.environ.setdefault("PROJECT_ID", "test-project")
    os.environ.setdefault("METADATA_PREFIX", "metadata/")

    # Ensure settings cache reflects local defaults.
    get_settings.cache_clear()  # type: ignore[attr-defined]

    event = load_sample_event()
    gcs_file_observer(event)


if __name__ == "__main__":
    main()
