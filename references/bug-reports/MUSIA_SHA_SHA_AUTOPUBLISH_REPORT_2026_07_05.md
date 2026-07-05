# Musia Sha Sha AutoPublish Report - 2026-07-05

## Scope

This report records observed AutoPublish behavior during the Musia `sha-sha`
publish run. It should not be read as a general failure claim. AutoPublish
successfully published the same direct package to Douyin during this run, and
YouTube progressed after a browser-session restart.

## Package

- Direct ZIP:
  `/home/lachlan/DiskMech/Projects/lazyedit/DATA/sha-sha-musia-lyrics-guitar-4k/publish_direct_4k/sha-sha-musia-lyrics-guitar-4k-direct.zip`
- Internal video:
  `sha-sha-musia-lyrics-guitar-4k-direct_highlighted.mp4`
- Internal metadata:
  `sha-sha-musia-lyrics-guitar-4k-direct_metadata.json`
- Video resolution: `2160x3840`
- Duration: about `76.4s`

## Confirmed Status From Logs

- Douyin: confirmed by AutoPublish log:
  - `Douyin publish submit accepted; browser moved to management page.`
  - `Douyin management verification matched term: '沙沙Musia'`
  - `Successfully published on Douyin.`
- YouTube: after forcing a browser-session restart, the run progressed through:
  - attached video;
  - upload complete;
  - title set;
  - description set;
  - not-made-for-kids selected;
  - tags entered.
- YouTube playlist selection failed after creating `Musia`, but the publisher
  continued without the playlist, which is acceptable for the current run.

## Interrupted Instagram Session Observation

During an Instagram attempt, the automation reached:

```text
Clicking Share...
Waiting for publish confirmation...
```

The process was manually interrupted. A later Instagram attempt reached:

```text
Attempting to set crop to Original...
```

After interruption, the log included:

```text
Instagram publish failed: HTTPConnectionPool(host='localhost', port=51451):
Max retries exceeded ... Failed to establish a new connection: [Errno 111]
Connection refused
```

Suggested fix:

- Treat interrupted Selenium sessions as dirty. Before retrying the same
  platform, close any driver tied to the old chromedriver port and reopen the
  platform browser/session.
- Add a platform-level retry option that restarts only the affected browser
  profile, instead of requiring a full control-plane restart.
- Record whether an Instagram share confirmation was observed before
  interruption, so a retry can avoid duplicate posts or can verify an existing
  pending post first.

## YouTube Browser Session Observation

Before restart, a YouTube-only job stalled after:

```text
Preparing Chromium sessions before publishing...
Reusing existing y2b Chromium session on port 9222.
Original title:  Sha Sha - Musia
```

Manual Selenium attachment to the same `9222` debug endpoint succeeded, so this
was not enough evidence to call the YouTube browser unusable. After restarting
with `AUTOPUBLISH_FORCE_BROWSER_RESTART=1`, the YouTube job advanced.

Suggested fix:

- Add heartbeat/progress logging between `create_new_driver(port=9222)` and
  `Publishing on YouTube...`.
- If no publisher log appears within a bounded timeout after driver creation,
  mark the job as recoverable and restart the target browser session.
- Make `AUTOPUBLISH_FORCE_BROWSER_RESTART=1` a per-job or per-platform option
  exposed through the `/publish` request, so recovery does not require manual
  tmux intervention.

## Shipinhao / Shipinhao Music Note

During an earlier combined attempt, the Shipinhao browser showed repeated login
iframe messages. This report does not claim the Shipinhao publisher is broken;
it records that this run should verify login state before queueing Shipinhao or
Shipinhao Music jobs so they do not block other platform publishes.

## Requested Behavior

- Platform jobs should be safely retryable one platform at a time.
- A failed or interrupted Instagram/Shipinhao session should not poison a later
  YouTube-only publish.
- The queue should expose "published", "in progress", "blocked by login", and
  "interrupted/retry needed" states separately.
