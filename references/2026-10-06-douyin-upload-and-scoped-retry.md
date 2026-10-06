# Douyin upload recovery and independent platform results

## Observed incident

The Musia `aya-canada-beyond-the-maples-ja-portrait-4k` publication first
failed during Douyin upload. The visible editor reported upload failure; an
earlier snapshot showed 2%, 0.7/41.9 MB and 12.8 KB/s. This is evidence of a
failed/slow upload, not proof of a particular network or platform root cause.
One subsequent attempt also waited for a draft button after the SPA entered
the editor. No final Douyin publication was confirmed in that batch.

Shipinhao, Instagram and YouTube were then published in a separate scoped job.
Its YouTube receipt was `https://youtube.com/shorts/_kFST2FpDU0` and Instagram
receipt was `https://www.instagram.com/lazyingart/reel/DeJjmI8ORwP/`.
Do not replay these targets when recovering Douyin.

A Douyin-only retry incorrectly POSTed form fields without ZIP bytes and
without `reuse_existing=true`. The old handler saved the 433-byte multipart
body over the existing archive, then failed with `File is not a zip file`.
This was a malformed retry plus missing server validation, not a Douyin outage.

## Changes

- Inspect the draft route and visible continue control together, with a bounded
  wait and click-once behavior. Capture evidence if the editor does not open.
- Log upload percentage, transferred bytes, visible speed and remaining time.
  Save UI evidence at upload failure; do not silently infer publication.
- Complete remaining independent publish calls after one target fails. Record
  `platform_results` in the queue response and optional durable queue journal.
  The overall job still fails when any selected target fails. Constructor/login
  setup errors remain batch-level errors; this is not an automatic retry engine.
- Validate incoming ZIP structure/CRC before replacing a file. Reject empty or
  multipart bodies with HTTP 400 and retain the existing archive. Explicit reuse
  also validates the existing ZIP. Compare hashes, not only sizes. Block changed
  package bytes while that path belongs to a queued/running job (HTTP 409).
- Retain the accepted archive SHA-256 in each new job and reject later mutation.
- Check CRCs of extracted members, not only their sizes, before reusing them.
  Same-length corrected metadata must not leave a stale extracted title behind.

## Retry contract

Send the original reviewed ZIP as raw bytes, with options in the URL query:

```bash
curl --fail-with-body -X POST \
  -H 'Content-Type: application/zip' \
  --data-binary @reviewed-song.zip \
  "$AUTOPUBLISH_API/publish?filename=reviewed-song.zip&publish_douyin=true"
```

For a valid package already on the publisher, use a body-less request with
`reuse_existing=true`. Never use a multipart form as an archive. Restart only
the affected browser if its state is stale. Before a retry after an uncertain
final submit, inspect management/history to prevent duplicate posts.

## Validation

Focused tests cover upload-state parsing, SPA draft races, independent target
results, malformed/empty retry bodies, corrupt ZIP reuse, same-size changed
content and active-job package protection. Run:

```bash
python -m unittest discover -s tests -p 'test_douyin*.py' -v
python -m unittest discover -s tests -p 'test_publish*.py' -v
```

The full suite also has two pre-existing failures in
`test_instagram_caption_persistence.py` (missing counter expectation and native input
replacement expectation). These are outside the changed publisher path;
Instagram's real publication and saved-caption check succeeded in this run.
Full pytest result after the package/handler/diagnostics tests: **81 passed, 2 failed**;
excluding that unchanged Instagram test module: **69 passed**.

Deploy only with the shared queue idle. Save old receipts before restarting a
non-journaled worker. Do not interrupt another project's publication. Code
validation and queue acceptance are not proof of a successful Douyin post;
record the platform management confirmation separately.

For a recurring upload failure, observe the existing browser without touching
its navigation or replaying network requests:

```bash
python scripts/diagnose_douyin_upload.py --port 5004 --seconds 600
```

This read-only CDP probe records upload hosts, timing, HTTP status, network
errors and selected JSON status/error fields. It omits signed URLs, request
bodies, headers, cookies and upload IDs. A canceled request during the publisher's
navigation is not automatically the cause of a preceding upload failure.

## Live recovery result

Corrected raw-ZIP job `job-1791282667698-1` ran only Douyin. Its first upload
failed at 96%; the bounded retry recovered the editor, finished uploading and
received an HTTP 200 JSON `code: 2000, message: Success` from upload storage.
The final publish receipt and management-title match completed at 18:39:52
Asia/Hong_Kong on 2026-10-06. A separate read-only management check showed the
02:26 song row, creation time 18:39 and **审核中**. Submission succeeded; public
visibility still depends on Douyin moderation. Queue `done` is not a claim that
platform moderation has completed.

No Instagram, Shipinhao or YouTube publication was repeated during recovery.
The precise cause of the intermittent upload transport failure remains unknown;
the fixes improve retry reliability and diagnostics, not a guaranteed network cure.
