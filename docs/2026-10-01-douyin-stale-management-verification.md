# Douyin stale management verification

An accepted publication can return to the creator management SPA while it still
shows the cached pre-upload list. `safe_get` skips a same-route navigation, so
repeating verification previously saw the same stale list until timeout.

Observed with food video IMG_8951 / LazyEdit 600: publish receipt was accepted;
management still showed 2789 older works. One reload of the existing management
page exposed the new title and verification succeeded. No second submission
was made. Earlier Bunko-watch publication had the same symptom.

`publish_verification.py` now refreshes Douyin's management page on subsequent
verification passes. The first pass remains unchanged. This affects only the
readback stage, not upload, title entry or the publish click. A refresh failure
is logged and normal bounded verification continues. Tests cover stale-list
recovery and the no-refresh fast path when the post is already visible.

Deploy only after the active publish queue is finished: this server watches
Python files for autoreload. Do not pull changes halfway through a multi-platform
job, because restarting its in-memory worker can lose the remaining targets.
