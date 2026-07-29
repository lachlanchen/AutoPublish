# Publish Attention API

AutoPublish exposes operator actions, such as a platform login QR code, as
job-scoped attention events. Consumers should use this contract instead of
reading terminal logs, listing `/tmp`, or guessing which screenshot belongs to
the active job.

## Queue Contract

`GET /publish/queue` may include:

```json
{
  "id": "job-123",
  "status": "running",
  "attention": {
    "platform": "shipinhao",
    "kind": "login_qr",
    "status": "required",
    "message": "Shipinhao login is required. Scan the current QR code.",
    "revision": 2,
    "media_type": "image/png",
    "artifact_url": "/publish/jobs/job-123/attention/2"
  }
}
```

The event belongs to one exact publish job. `revision` increases only when the
QR content changes. Repeated screenshots of the same QR do not create another
revision.

Fetch the current artifact with:

```text
GET /publish/jobs/JOB_ID/attention/REVISION
```

The response is `image/png` with `Cache-Control: no-store`. An old revision, a
resolved event, or a mismatched job returns `404`.

After login succeeds, the queue event becomes:

```json
{
  "kind": "login_qr",
  "status": "resolved",
  "revision": 2
}
```

The artifact endpoint is no longer available after resolution.

## Ownership

- The platform login class detects login and creates or refreshes the QR.
- AutoPublish owns event identity, revisioning, storage, and artifact serving.
- LazyEdit proxies this internal API and never exposes remote file paths.
- Chat transports fetch the LazyEdit proxy URL, deduplicate by revision, and
  deliver the PNG to the exact originating chat.
- Email remains an independent fallback.

The attention callback is optional. A standalone publisher continues to work
without an API host or chat transport.

## Safety

- Artifacts are bounded to 5 MB and must have a PNG signature.
- Files are copied into an AutoPublish-owned temporary directory.
- Public queue payloads never expose filesystem paths or content hashes.
- Consumers must match the exact job ID and revision.
- Attention delivery never submits, retries, or duplicates a publish job.
