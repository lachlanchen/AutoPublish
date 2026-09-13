# Instagram Caption Persistence

## Failure Observed

A reel was successfully shared but its caption was empty. The previous workflow
confirmed the media-share receipt without reopening the post to validate its
description. A visually filled editor therefore did not prove that Instagram
had saved the metadata.

The current editor is a Lexical contenteditable. Programmatic DOM insertion can
show text without updating its internal state. The old hidden-field fallback
used `execCommand` plus a synthetic event and accepted a short text prefix.
The precise server-side cause of the original loss was not captured; this is
an observed validation gap, not proof that every native typing call fails.

## Current Flow

1. Build one caption with `instagram_caption.build_instagram_caption` using
   Japanese, English, Chinese in that order when available.
2. Select a visible, enabled caption editor and replace text with native
   WebDriver keyboard input. Tab away to let the editor commit and dismiss tag
   suggestions. Hidden-editor DOM injection is no longer a fallback.
3. Confirm the complete text and, for Lexical, the character counter. Require
   two stable readings after blur, and repeat validation immediately before
   Share. Empty metadata or a mismatch blocks submission without restarting
   the upload.
4. After sharing, visit the profile and open the latest post's own permalink.
   Compare the complete saved caption with the expected text. Both modern span
   captions and older heading captions are supported. Whitespace formatting
   changes are tolerated; missing languages and title-only matches are not.
5. A share receipt alone is not final success. A missing saved caption reports
   the candidate URL for edit-in-place recovery, without reuploading the video.

Mark the Share boundary before clicking: if a browser response is lost, the
publisher must not recursively create a duplicate post.

## Existing-Post Recovery

Use the exact post's More Options -> Edit, type the same approved merged caption,
verify its counter after leaving the editor, then Done. Reload the permalink and
read the caption again. Keep the media, reactions, AI label, and other platforms
unchanged. An unavailable location is optional and must not delay this repair.

In the inspected recovery, the 747-character caption persisted after native
typing and a full reload. Japanese, English, Chinese, and the photography
attribution were all present. Private screenshots and the exact post URL stay
in the local delivery record, not the public repository.

## Export A Delivery Copy

```bash
python scripts/export_instagram_caption.py package_metadata.json delivery/instagram-caption-ja-en-zh.txt
```

This exports the publisher's exact text rather than generating another version.
It refuses to overwrite a different existing caption. Put the resulting file
in the user's chosen delivery/sync folder and verify synchronization separately.

## Tests

```bash
python -m unittest discover -s tests -p test_instagram_caption_persistence.py -q
python -m unittest test_instagram_caption test_publish_ui_regressions -q
```

Tests cover a zero/stale Lexical counter, partial text, UTF-16 character counts,
legacy textarea input, hidden editors, empty captions, native replacement,
post-share validation, and non-destructive text export. No test publish is
required.
