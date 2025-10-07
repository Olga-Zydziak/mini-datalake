"""Cloud Functions entrypoint module."""

from __future__ import annotations

from cloudevents.http import CloudEvent

from src.handler import gcs_file_observer as _handler_entrypoint


def gcs_file_observer(event: CloudEvent) -> None:
    """Adapter to expose the handler for Cloud Functions 2nd gen."""

    _handler_entrypoint(event)
