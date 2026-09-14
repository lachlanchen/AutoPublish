# Douyin visible upload state

A real upload initially reached the editor but subsequently displayed
`上传失败，重新上传`. The publisher had already logged upload completion. It
attempted submission, detected the failure, and reopened the unpublished draft.
The resumed editor later showed a playable video and the separate visible
`重新上传` control.

The old upload loop queried several XPath expressions sequentially with
`visible=False`. Hidden uploader controls could qualify, and a contains-match
for `重新上传` could also match the failure message. A failure check and a
completion check could observe different moments in the upload transition.

`douyin_submit.upload_outcome()` now classifies a single visible `body.innerText`
snapshot. Upload failure wins over completion, active uploading wins over a
replace control, and only exact standalone completion/control lines mean ready.
Empty pages and ordinary upload instructions remain pending. Both the initial
draft decision and the upload wait use this classifier. The existing stale
failure grace period and bounded retry behavior remain in place.

This fixes the readiness decision; it does not claim to prevent network upload
failures. Submission receipts and management verification still determine the
publication result. A later accepted submit must not be reuploaded merely
because management indexing is delayed.

Tests: `PYTHONPATH=. python -m pytest tests/test_douyin_upload_status.py -q`.
Regression cases include the full failed/reupload string, stale ready controls,
upload progress, background preflight checks, instructions and unavailable pages.

Deploy after the active publish queue finishes, since imported module changes
may trigger the server's automatic reload. Keep browsers and authentication
profiles intact.
