"""Enter captions through browser input and verify the editor committed them."""

import re
import time
import unicodedata

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


class InstagramCaptionError(RuntimeError):
    """Caption validation failed; retain the existing upload or post."""


def normalized_caption(text):
    return unicodedata.normalize("NFC", str(text or "")).replace("\r\n", "\n").strip()


def rendered_caption_matches(actual, expected):
    # Rendered hashtag links and paragraph layout can change whitespace only.
    clean = lambda text: re.sub(r"\s+", " ", normalized_caption(text))
    return bool(clean(expected)) and clean(actual) == clean(expected)


def editor_snapshot(driver, editor):
    return driver.execute_script(r"""
        const el = arguments[0];
        const dialog = el.closest('[role="dialog"]');
        const matches = [...(dialog?.innerText || '').matchAll(/([\d,]+)\s*\/\s*2,?200\b/g)];
        const counter = matches.length ? Number(matches.at(-1)[1].replaceAll(',', '')) : null;
        return {text: el.tagName === 'TEXTAREA' ? el.value : el.innerText,
                lexical: el.hasAttribute('data-lexical-editor'), counter};
    """, editor)


def editor_has_caption(snapshot, expected):
    if not snapshot or normalized_caption(snapshot.get("text")) != normalized_caption(expected):
        return False
    if snapshot.get("lexical"):
        # A DOM-only insertion can leave Lexical's state/counter at zero.
        units = len(expected.encode("utf-16-le")) // 2
        counter = snapshot.get("counter")
        if counter is None:
            # Some Instagram variants omit the counter while the editor still
            # exposes a committed Lexical value.
            return True
        # Instagram's counter can differ by a small amount from the browser's
        # UTF-16 length after normalizing line breaks, punctuation, or emoji.
        # Require a non-zero committed counter, but do not reject text that is
        # visibly identical solely because of that representation difference.
        return counter > 0 and abs(counter - units) <= max(4, expected.count("\n") + 2)
    return True


def verify_editor_caption(driver, find_editor, expected, timeout=10):
    consecutive = 0

    def committed(_):
        nonlocal consecutive
        editor = find_editor(driver)
        valid = bool(editor) and editor_has_caption(editor_snapshot(driver, editor), expected)
        consecutive = consecutive + 1 if valid else 0
        return consecutive >= 2

    try:
        WebDriverWait(driver, timeout, poll_frequency=0.5).until(committed)
    except Exception as exc:
        raise InstagramCaptionError("Instagram caption did not persist in the editor; not sharing.") from exc


def _clear_lexical_editor(driver, find_editor, timeout=5):
    """Clear the active Lexical editor and verify that its state is empty."""
    editor = WebDriverWait(driver, timeout).until(find_editor)
    editor.click()
    editor.send_keys(Keys.CONTROL, "a")
    editor.send_keys(Keys.BACKSPACE)

    def is_empty(_):
        current = find_editor(driver)
        return bool(current) and normalized_caption(editor_snapshot(driver, current).get("text")) == ""

    try:
        WebDriverWait(driver, timeout, poll_frequency=0.25).until(is_empty)
    except Exception as exc:
        raise InstagramCaptionError(
            "Instagram caption editor could not be cleared safely; not sharing."
        ) from exc


def enter_verified_caption(driver, find_editor, caption):
    if not normalized_caption(caption):
        raise InstagramCaptionError("Publication metadata produced an empty Instagram caption.")
    try:
        last_error = None
        for attempt in range(2):
            editor = WebDriverWait(driver, 20).until(find_editor)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", editor)
            if editor.tag_name.lower() == "textarea":
                editor.click()
                editor.send_keys(Keys.CONTROL, "a")
                editor.send_keys(Keys.BACKSPACE)
            else:
                _clear_lexical_editor(driver, find_editor)

            editor = WebDriverWait(driver, 10).until(find_editor)
            # Long WebDriver key streams can be coalesced or partially ignored
            # by Lexical. Smaller paced chunks preserve the site's input events
            # and make the committed DOM/state match reliable for multilingual
            # captions, including after a failed upload left stale text.
            for start in range(0, len(caption), 180):
                editor.send_keys(caption[start:start + 180])
                time.sleep(0.08)
            editor.send_keys(Keys.TAB)
            try:
                verify_editor_caption(driver, find_editor, caption)
                return
            except InstagramCaptionError as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.75)
        if last_error:
            raise last_error
    except InstagramCaptionError:
        raise
    except Exception as exc:
        raise InstagramCaptionError("Caption input failed; keep the current upload for recovery.") from exc
