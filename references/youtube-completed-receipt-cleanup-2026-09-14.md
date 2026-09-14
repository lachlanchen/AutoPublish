# YouTube completed receipt and draft recovery

## Failure

A completed upload can leave both its `ytcp-video-share-dialog` confirmation
and an underlying `ytcp-uploads-dialog` visible according to `checkVisibility`.
The draft guard then compares the previous title against the next job and stops
with `Another YouTube draft is open`. The shared browser session is healthy;
this is a completed receipt, not an unfinished upload.

## Publisher behavior

`YouTubePublisher._close_completed_publication()` runs before draft inspection.
It requires a visible success confirmation containing `Video published` or
`视频已发布` and a YouTube watch/Shorts URL. It clicks only that confirmation's
visible `Close`/`关闭` button, then waits for both the confirmation and the
underlying wizard to disappear. A missing button or closing timeout preserves
the browser state and blocks a new upload. Unknown dialogs are not dismissed.

Exact-title drafts continue through the existing resume path without attaching
the file again. Different unfinished drafts remain protected. This change does
not grant permission to republish a video or disable publication-history checks.

After successful current-title receipt verification, the publisher also tries
to close the completed confirmation. Cleanup failure at that point is logged;
it cannot turn a verified publication into a failed job or start a retry. The
next job will retry cleanup before inspecting any draft.

## Verification and operations

Run `PYTHONPATH=. python -m pytest tests/test_youtube_check_flow.py
tests/test_pub_y2b_metadata.py -q` using the project's Python environment.
The tests cover a completed overlay, unrelated and matching drafts, missing
close controls, delayed closing, verified-success cleanup failure, receipt
validation and embedded JavaScript syntax.

Deploy the committed AutoPublish version to the publishing host while its queue
is idle. Leave Chromium and authenticated profiles running. If a combined job
fails on one platform, inspect its individual results and retry only the missing
platform after the recovery is in place.
