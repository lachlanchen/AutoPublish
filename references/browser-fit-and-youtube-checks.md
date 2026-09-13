# Browser Fit And YouTube Check Recovery

## Desktop Fit

Every browser attached through `app.create_new_driver` now uses
`browser_window.fit_browser_window`. It reads the current monitor's available
rectangle, including panel offsets, instead of assuming a 1920x1080 desktop.
This changes only window bounds, not the profile, URL, page zoom, or upload.
Instagram's standalone publisher also uses this helper.

## YouTube Checks

An enabled Next button and an assigned video link indicate navigation/upload
readiness, not completed checks. The publisher now visits Initial check and
waits for the upload's visible progress label. A copyright match is accepted
only when the check details explicitly say it does not affect visibility or
features. Restrictions and unknown results require review.

When the check warning appears after a Publish click, choose Go back and wait
on the same upload. The publisher never chooses Publish anyway. If the warning
persists, preserve the draft for recovery instead of uploading another copy.
A failure after file attachment also preserves the upload without an automatic
full-upload retry.

Completion requires the visible `Video published` share dialog and video URL.
Finding the title in the upload wizard or in a private draft does not count.

## Observed Recovery, 2026-09-13

- The footer completed while an earlier check warning was still open.
- The check page reported a nonrestricting copyright match and no community
  guideline issues.
- The Go back action did not dismiss the stale warning reliably. Escape closed
  the wizard while retaining the upload as a private draft.
- Opening that exact draft from Shorts, reviewing checks, then publishing
  produced a real share receipt. No second video upload was needed.
- Other platform jobs and already published posts were left intact.

## Verification

```bash
python -m pytest tests/test_youtube_check_flow.py tests/test_pub_y2b_metadata.py \
  test_publish_ui_regressions.py test_instagram_caption.py -q
python -m py_compile app.py pub_y2b.py youtube_checks.py browser_window.py
```

Live review should confirm all browser edges fit inside the desktop and retain
private screenshots of the check result and publication receipt. Do not commit
personal media, profile data, session logs, or account screenshots.
