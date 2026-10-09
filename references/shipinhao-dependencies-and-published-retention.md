# Shipinhao Recovery and Published Staging Retention

## Diagnosed Failures

On 2026-10-09 a valid 2160x3840 recording uploaded and decoded, but the cover
stayed at `生成中`. Browser resource timing showed repeated 30-second timeouts
for Tencent's public `rhino_video.wasm`. The music form also stalled on
`vts.wasm`, leaving its audio upload at zero percent. This was not disk pressure.

The language menu independently had a double-click bug: native `click()` plus
a synthetic click opened then closed the dropdown. Its Japanese option existed.
The selector now clicks once and preserves an open menu across asynchronous
render polls. Live verification selected Japanese and read it back on the next
poll. Do not report missing platform support from a failed selector alone.

## Verified Public Dependency Cache

`browser_asset_cache.py` optionally reads
`~/.cache/autopublish/browser-assets.json` (override with
`AUTOPUBLISH_BROWSER_ASSETS`). A manifest entry contains `url`, `file` and
`sha256`; the file must be beside the manifest, not a symlink. Only the explicit
Tencent public WebAssembly URL families are allowed. Magic bytes and SHA-256
must both match. Fetch the original bytes over verified HTTPS, optionally using
an authorized machine with working access to that CDN. Do not synthesize them,
disable TLS verification, or commit cached binaries.

The cache attaches only during Shipinhao video/music publication, to its existing
dedicated loopback Chrome browser, and supplies the exact vendor bytes. Browser
level Fetch is necessary: worker sessions reject `Fetch.enable`, and page-level
interception misses the worker's downloads. All authenticated
APIs and every other request still use the platform normally. Cover readiness,
form validation and publication verification remain mandatory. The connection
and interception are closed after the publisher exits. Without a manifest the
browser behaves as before.

The live worker appends `_rid` and `_pageUrl` telemetry query parameters. The
cache ignores only those observed keys when matching the pinned static binary;
unknown query keys bypass the cache, and parameter values are not logged.

## Default Cleanup

After a terminal job, `AUTOPUBLISH_CLEAN_PUBLISHED=1` (default) removes confirmed
published **remote staging** media and their uploaded ZIP. Set it to `0` to retain
staging. The queue journal now defaults to `logs/publish-queue.json` under the
runtime data root, preserving job hashes and results across restarts.

- Require the current archive's recorded SHA-256 and a successful result for
  **every requested platform**, including targets from earlier partial batches.
- A successful scoped retry can complete that same immutable archive's batch.
- An acceptance guard blocks cleanup from the beginning of upload validation
  through queue insertion, not merely while a job is already visible as queued.
- Preserve any archive still queued/running, partially failed, ambiguous, in
  test mode, from shared canonical workspace storage, or lacking hash evidence.
- Delete only exact archive-member media whose bytes still match. Keep manual
  files, changed files, metadata, corrected lyrics, subtitles, covers and proofs.
- Never follow symlinks, traverse outside the direct package directory, delete
  browser profiles, or touch original workstation/Nutstore recordings.
- Write a durable checksum/result receipt under
  `transcription_data/.published-receipts/` **before** deletion. A cleanup failure
  does not invalidate publication or trigger another social post.

Review historical candidates without deleting:

```bash
python published_retention.py --journal /runtime/logs/publish-queue.json \
  --root /runtime/transcription_data
```

Use `--apply` only while the publisher is stopped or idle. Unknown older data is
not automatically assumed published. Keep it until its receipts are recovered.
After cleanup, a deliberate republish re-uploads the canonical LazyEdit ZIP;
`reuse_existing=true` alone cannot recover a removed staging archive.

## Tests and Deployment

Run `python -m unittest discover -s tests -p 'test_published_retention.py'` and
the analogous `test_browser_asset_cache.py`. Retention tests cover partial
failures/retries, active jobs, source paths, changed files, unknown evidence,
test/shared packages, symlinks and idempotency.

With Playwright installed, also run `test_shipinhao_music_dropdown.py` and
`test_browser_asset_cache_worker.py`. These exercise asynchronous menu toggling,
selection readback, and an actual dedicated worker fetching a pinned dependency.

Deploy only after the queue is idle. Preserve receipts before an old
non-journaled process restarts. Retry failed platforms only, never all targets.
