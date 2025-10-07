# gcs-file-observer

## Overview

```
             ┌───────────────────────┐
             │   Source GCS Bucket   │
             │  (Object Finalized)   │
             └──────────┬────────────┘
                        │ CloudEvent
                        ▼
             ┌───────────────────────┐
             │  Cloud Functions Gen2 │
             │  gcs_file_observer    │
             └──────────┬────────────┘
                        │ JSON metadata
                        ▼
             ┌───────────────────────┐
             │ Destination GCS Bucket│
             │  (metadata/...)       │
             └───────────────────────┘
```

The **gcs-file-observer** project listens to Cloud Storage finalize events. When a new object is created, the Cloud Function validates the payload, enriches the metadata, and persists a structured JSON representation into a destination bucket.

## Architecture

* **Language:** Python 3.11 (PEP 8 compliant, fully typed).
* **Trigger:** Eventarc CloudEvent for `google.cloud.storage.object.v1.finalized`.
* **Storage:** Metadata persisted into a separate Google Cloud Storage bucket to avoid recursive triggers.
* **Observability:** Structured logging with contextual metadata.
* **Resilience:** Tenacity-powered retries on transient Google Cloud errors.
* **Validation:** Pydantic models ensure consistent schemas for incoming and outgoing payloads.

## Deployment

Prerequisites:

* Google Cloud project with Cloud Functions 2nd gen enabled.
* Artifact Registry or Cloud Storage staging bucket (managed automatically by `gcloud`).
* The Cloud Function's service account requires the following roles:
  * `roles/storage.objectViewer` on the **source** bucket.
  * `roles/storage.objectAdmin` on the **destination** bucket.
  * `roles/eventarc.eventReceiver` for Eventarc triggers (granted automatically on deploy if using the default service account).

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEST_BUCKET` | Yes | — | Bucket that receives JSON metadata. Must differ from source. |
| `PROJECT_ID` | Yes | — | Google Cloud project ID. |
| `METADATA_PREFIX` | No | `metadata/` | Prefix prepended to output object keys. |

See [`.env.example`](./.env.example) for local development.

### Deployment Command

```bash
gcloud functions deploy gcs-file-observer \
  --gen2 \
  --region=us-central1 \
  --runtime=python311 \
  --entry-point=gcs_file_observer \
  --source=. \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=<SOURCE_BUCKET_NAME>" \
  --set-env-vars=DEST_BUCKET=<DEST_BUCKET_NAME>,PROJECT_ID=<PROJECT_ID>,METADATA_PREFIX=metadata/
```

## IAM & Least Privilege

Configure IAM so that the Cloud Function's runtime service account has:

1. **Source Bucket**: `roles/storage.objectViewer`
2. **Destination Bucket**: `roles/storage.objectAdmin`
3. **Project Level**: `roles/logging.logWriter` (default) and `roles/eventarc.eventReceiver`

These assignments limit the function to only read source objects and write metadata objects.

## Local Development

1. Create and populate a `.env` file from `.env.example`.
2. Install dependencies and run tests:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make all
```

3. Simulate an event locally:

```bash
python -m localdev.simulate_event
```

This will load the sample CloudEvent JSON, invoke the handler, and log the resulting metadata payload.

## Testing & Quality Gates

* `make fmt` — Auto-format using Ruff (where safe).
* `make lint` — Static linting via Ruff.
* `make type` — Type checking with `mypy --strict`.
* `make test` — Run pytest with coverage (threshold enforced in CI).
* `make all` — Runs lint, type, and tests.

Continuous Integration executes the same steps using GitHub Actions on every push.

## Design Rationale

* **Pydantic Models:** Provide strict validation for CloudEvent payloads and ensure outgoing metadata conforms to contract. Validation catches malformed timestamps and missing fields early.
* **Tenacity Retries:** Wrap storage interactions to transparently retry on `ServiceUnavailable`, `TooManyRequests`, and `DeadlineExceeded` errors, improving reliability under transient network issues.
* **Structured Logging:** Emitting key-value logs simplifies observability and integrates with Cloud Logging's advanced filters.
* **Bucket Separation:** The handler short-circuits when the source bucket matches the destination to avoid infinite recursion and cost amplification.
* **Metadata Prefixing:** Output keys follow `<prefix>/<source>/<object>.json` while sanitizing object paths by replacing `/` with `__`, preserving hierarchy but avoiding unintended folder structures.
* **Failure Modes:** If the source object disappears before processing, the function marks `exists=false` while still writing the metadata artifact, providing forensic context without crashing.
* **Extensibility:** `extractor.detect_format` fuses filename extension and MIME type to produce a best-effort classification, defaulting to `empty` for zero-byte files.

## Cost Considerations

* Cloud Functions and Eventarc charges apply per invocation (per object finalize event).
* Google Cloud Storage charges for metadata writes and storage of JSON metadata.
* Retries are limited to three attempts to balance resiliency with cost and avoid runaway execution.

## Security Notes

* Environment variables should be configured through secure deployment pipelines rather than committed code.
* Metadata output does not include object data; only non-sensitive headers are persisted.
* Structured logging avoids logging secrets. Ensure Cloud Logging sinks follow principle of least privilege.

