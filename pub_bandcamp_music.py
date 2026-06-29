"""Bandcamp music publisher.

Bandcamp release setup includes account/payment controls that should remain
human-owned. This publisher prepares/fills a logged-in Bandcamp browser session
from a LazyEdit music package and saves a draft by default. Set
``BANDCAMP_PUBLISH_PUBLIC=1`` only when the account/release settings are ready
and the caller explicitly wants a public publish click.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import time
import traceback

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from utils import log_html_snapshot


BANDCAMP_HOME_URL = "https://bandcamp.com"
BANDCAMP_LOGIN_URL = "https://bandcamp.com/login"


def _is_lossless_audio(path: str | os.PathLike[str]) -> bool:
    return Path(path).suffix.lower() in {".wav", ".aif", ".aiff", ".flac"}


def _first_text(*values) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _metadata_value(metadata: dict, key: str, default=""):
    value = metadata.get(key, default)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return value


def _execute(driver, script, *args):
    return driver.execute_script(script, *args)


PAGE_STATE_SCRIPT = """
const norm = (s) => String(s || '').replace(/\\s+/g, ' ').trim();
const isVisible = (el) => {
  const style = window.getComputedStyle(el);
  const rect = el.getBoundingClientRect();
  return style && style.visibility !== 'hidden' && style.display !== 'none'
    && rect.width > 0 && rect.height > 0;
};
const bodyText = norm(document.body ? document.body.innerText : '');
const fileInputs = Array.from(document.querySelectorAll('input[type="file"]')).map((input) => ({
  accept: input.getAttribute('accept') || '',
  multiple: !!input.multiple,
  visible: isVisible(input),
}));
const buttons = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"]'))
  .filter(isVisible)
  .map((el) => norm(el.innerText || el.value || el.getAttribute('aria-label') || el.title))
  .filter(Boolean)
  .slice(0, 80);
return {
  url: location.href,
  title: document.title,
  bodyText: bodyText.slice(0, 4000),
  fileInputs,
  buttons,
  loggedOut: /log in|sign up|password|email/i.test(bodyText) && /bandcamp/i.test(bodyText),
};
"""


CLICK_TEXT_SCRIPT = """
const texts = Array.isArray(arguments[0]) ? arguments[0] : [arguments[0]];
const exact = !!arguments[1];
const norm = (s) => String(s || '').replace(/\\s+/g, ' ').trim();
const isVisible = (el) => {
  const style = window.getComputedStyle(el);
  const rect = el.getBoundingClientRect();
  return style && style.visibility !== 'hidden' && style.display !== 'none'
    && rect.width > 0 && rect.height > 0;
};
const candidates = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"], label, span, div'))
  .filter(isVisible);
for (const wanted of texts) {
  const targetText = norm(wanted).toLowerCase();
  if (!targetText) continue;
  for (const el of candidates) {
    const text = norm(el.innerText || el.value || el.getAttribute('aria-label') || el.title).toLowerCase();
    if (!text) continue;
    const ok = exact ? text === targetText : text.includes(targetText);
    if (!ok) continue;
    const target = el.closest('button, a, label, input[type="button"], input[type="submit"]') || el;
    target.scrollIntoView({block: 'center'});
    target.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window}));
    if (typeof target.click === 'function') target.click();
    target.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window}));
    target.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
    return {ok: true, clicked: norm(el.innerText || el.value || el.getAttribute('aria-label') || el.title)};
  }
}
return {ok: false, buttons: candidates.map((el) => norm(el.innerText || el.value || el.getAttribute('aria-label') || el.title)).filter(Boolean).slice(0, 80)};
"""


SET_FIELD_SCRIPT = """
const labels = Array.isArray(arguments[0]) ? arguments[0] : [arguments[0]];
const hints = Array.isArray(arguments[1]) ? arguments[1] : [arguments[1]];
const value = arguments[2] == null ? '' : String(arguments[2]);
const norm = (s) => String(s || '').replace(/\\s+/g, ' ').trim();
const isVisible = (el) => {
  const style = window.getComputedStyle(el);
  const rect = el.getBoundingClientRect();
  return style && style.visibility !== 'hidden' && style.display !== 'none'
    && rect.width > 0 && rect.height > 0;
};
function setValue(el) {
  el.scrollIntoView({block: 'center'});
  el.focus();
  if (el.isContentEditable) {
    el.innerText = value;
    el.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText', data: value}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    return {ok: true, tag: el.tagName, value: el.innerText};
  }
  const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
  if (setter) setter.call(el, value);
  else el.value = value;
  el.dispatchEvent(new Event('input', {bubbles: true}));
  el.dispatchEvent(new Event('change', {bubbles: true}));
  el.blur();
  return {ok: true, tag: el.tagName, value: el.value};
}
const fields = Array.from(document.querySelectorAll('input:not([type="file"]):not([type="hidden"]), textarea, [contenteditable="true"]'))
  .filter(isVisible);
for (const field of fields) {
  const text = norm([
    field.name,
    field.id,
    field.placeholder,
    field.getAttribute('aria-label'),
    field.title,
    field.closest('label')?.innerText,
    field.closest('tr, li, div')?.innerText,
  ].filter(Boolean).join(' ')).toLowerCase();
  if (hints.some((hint) => hint && text.includes(norm(hint).toLowerCase()))) {
    const result = setValue(field);
    result.method = 'hint';
    result.hintText = text.slice(0, 200);
    return result;
  }
}
const textNodes = Array.from(document.querySelectorAll('label, span, div, td, th, p'))
  .filter(isVisible);
for (const labelEl of textNodes) {
  const labelText = norm(labelEl.innerText || labelEl.textContent).toLowerCase();
  if (!labels.some((label) => label && labelText.includes(norm(label).toLowerCase()))) continue;
  let scope = labelEl.closest('tr, li, fieldset, section, form, div') || labelEl.parentElement;
  for (let i = 0; i < 4 && scope; i += 1, scope = scope.parentElement) {
    const field = Array.from(scope.querySelectorAll('input:not([type="file"]):not([type="hidden"]), textarea, [contenteditable="true"]')).find(isVisible);
    if (field) {
      const result = setValue(field);
      result.method = 'label';
      result.label = labelText.slice(0, 200);
      return result;
    }
  }
}
return {ok: false, labels, hints, fields: fields.map((field) => norm([field.name, field.id, field.placeholder, field.getAttribute('aria-label'), field.title].join(' '))).slice(0, 80)};
"""


UPLOAD_FILE_SCRIPT = """
const kind = arguments[0] || 'audio';
const marker = arguments[1] || kind;
const inputs = Array.from(document.querySelectorAll('input[type="file"]'));
function score(input) {
  const accept = String(input.getAttribute('accept') || '').toLowerCase();
  const text = String([input.name, input.id, input.getAttribute('aria-label'), input.closest('label')?.innerText, input.closest('div')?.innerText].filter(Boolean).join(' ')).toLowerCase();
  if (kind === 'audio') {
    if (/audio|wav|flac|aiff|mp3/.test(accept + ' ' + text)) return 0;
  }
  if (kind === 'image') {
    if (/image|jpg|jpeg|png|art|cover|album/.test(accept + ' ' + text)) return 0;
  }
  return 10;
}
inputs.sort((a, b) => score(a) - score(b));
const input = inputs[0];
if (!input) return {ok: false, reason: 'no-file-input'};
input.setAttribute('data-autopub-bandcamp-target', marker);
return {ok: true, marker, accept: input.getAttribute('accept') || '', name: input.name || '', id: input.id || ''};
"""


class BandcampMusicPublisher:
    def __init__(self, driver, audio_path, cover_path, metadata, test=False):
        self.driver = driver
        self.audio_path = str(audio_path) if audio_path else ""
        self.cover_path = str(cover_path) if cover_path else ""
        self.metadata = metadata or {}
        self.test = test

    def _state(self):
        try:
            return _execute(self.driver, PAGE_STATE_SCRIPT)
        except Exception:
            traceback.print_exc()
            return {"url": self.driver.current_url, "bodyText": ""}

    def _wait_for_file_input(self, timeout=30):
        end_time = time.time() + timeout
        last_state = None
        while time.time() < end_time:
            state = self._state()
            last_state = state
            if state.get("fileInputs"):
                return state
            time.sleep(1)
        raise TimeoutException(f"Timed out waiting for Bandcamp upload input. Last state: {last_state}")

    def _click_any(self, texts, exact=False, timeout=8):
        end_time = time.time() + timeout
        last_result = None
        while time.time() < end_time:
            result = _execute(self.driver, CLICK_TEXT_SCRIPT, texts, exact)
            last_result = result
            if result and result.get("ok"):
                return result
            time.sleep(1)
        return last_result or {"ok": False}

    def _set_field(self, labels, hints, value, required=False):
        if not str(value or "").strip():
            return {"ok": False, "reason": "empty"}
        result = _execute(self.driver, SET_FIELD_SCRIPT, labels, hints, value)
        print(f"Bandcamp field set {labels}: {result}")
        if required and not result.get("ok"):
            raise RuntimeError(f"Bandcamp field not found: {labels} / {hints}")
        return result

    def _upload_file(self, path, kind="audio"):
        marker = f"{kind}-{int(time.time() * 1000)}"
        state = _execute(self.driver, UPLOAD_FILE_SCRIPT, kind, marker)
        if not state.get("ok"):
            raise RuntimeError(f"Bandcamp {kind} file input not found: {state}")
        inputs = self.driver.find_elements(By.CSS_SELECTOR, f"input[data-autopub-bandcamp-target='{marker}']")
        if not inputs:
            raise RuntimeError("Bandcamp file input disappeared.")
        target = inputs[0]
        target.send_keys(str(path))
        print(f"Bandcamp {kind} selected: {path}")
        return state

    def _normalized(self):
        title = _first_text(
            self.metadata.get("song_title"),
            self.metadata.get("music_title"),
            self.metadata.get("title"),
            Path(self.audio_path).stem,
        )
        artist = _first_text(self.metadata.get("artist"), self.metadata.get("author"), "Musia")
        description = _first_text(
            self.metadata.get("long_description"),
            self.metadata.get("music_story"),
            self.metadata.get("brief_description"),
        )
        lyrics = _first_text(
            self.metadata.get("plain_lyrics"),
            self.metadata.get("readable_lyrics"),
            self.metadata.get("lyrics"),
            self.metadata.get("song_lyrics"),
        )
        tags = _metadata_value(self.metadata, "tags", "")
        source_url = _first_text(
            self.metadata.get("source_url"),
            self.metadata.get("canonical_url"),
            self.metadata.get("website_url"),
        )
        if source_url and source_url not in description:
            description = (description + "\n\n" + source_url).strip()
        return {
            "title": title,
            "artist": artist,
            "description": description,
            "lyrics": lyrics,
            "tags": tags,
            "genre": _first_text(self.metadata.get("genre")),
            "price": _first_text(self.metadata.get("bandcamp_price"), os.environ.get("BANDCAMP_DEFAULT_PRICE")),
        }

    def publish(self):
        if not self.audio_path or not os.path.exists(self.audio_path):
            raise FileNotFoundError(f"Bandcamp audio not found: {self.audio_path}")
        if not _is_lossless_audio(self.audio_path):
            raise RuntimeError(
                "Bandcamp requires a real WAV/AIFF/FLAC master. "
                f"Refusing to upload non-lossless file: {self.audio_path}"
            )

        driver = self.driver
        upload_url = os.environ.get("BANDCAMP_UPLOAD_URL") or os.environ.get("BANDCAMP_DASHBOARD_URL") or BANDCAMP_HOME_URL
        driver.get(upload_url)
        time.sleep(3)
        state = self._state()
        print(f"Bandcamp initial state: {json.dumps(state, ensure_ascii=False)[:2000]}")

        if "login" in (state.get("url") or "").lower() or state.get("loggedOut"):
            driver.get(BANDCAMP_LOGIN_URL)
            log_html_snapshot(driver, "bandcamp_music", "login_required")
            raise RuntimeError(
                "Bandcamp login/account setup required. Log in on the port-5008 browser, "
                "then rerun. If Bandcamp opens a specific upload URL after account setup, "
                "set BANDCAMP_UPLOAD_URL to that page."
            )

        if not state.get("fileInputs"):
            click_result = self._click_any(
                [
                    "+ add",
                    "add",
                    "add track",
                    "add a track",
                    "add music",
                    "upload",
                    "new track",
                    "new album",
                ],
                exact=False,
                timeout=8,
            )
            print(f"Bandcamp add/upload click result: {click_result}")

        self._wait_for_file_input(timeout=30)
        self._upload_file(self.audio_path, kind="audio")
        time.sleep(5)

        normalized = self._normalized()
        self._set_field(["track title", "title", "name"], ["track title", "title", "name"], normalized["title"], required=False)
        self._set_field(["artist"], ["artist", "artist name"], normalized["artist"], required=False)
        self._set_field(["about", "description", "credits"], ["about", "description", "credits"], normalized["description"], required=False)
        self._set_field(["lyrics"], ["lyrics"], normalized["lyrics"], required=False)
        self._set_field(["tags"], ["tags", "genre"], normalized["tags"] or normalized["genre"], required=False)
        self._set_field(["price"], ["price", "minimum price"], normalized["price"], required=False)

        if self.cover_path and os.path.exists(self.cover_path):
            try:
                self._upload_file(self.cover_path, kind="image")
            except Exception as exc:
                print(f"Bandcamp cover upload skipped: {exc}")

        time.sleep(3)
        log_html_snapshot(driver, "bandcamp_music", "filled")
        print(f"Bandcamp form filled for: {normalized['title']}")

        if self.test:
            print("Bandcamp test mode: not saving or publishing.")
            return True

        allow_public = os.environ.get("BANDCAMP_PUBLISH_PUBLIC", "").strip().lower() in {"1", "true", "yes", "y"}
        if allow_public:
            result = self._click_any(["publish", "release", "make public"], exact=False, timeout=10)
            print(f"Bandcamp public publish click result: {result}")
            if not result.get("ok"):
                raise RuntimeError(f"Bandcamp public publish button not found: {result}")
        else:
            result = self._click_any(["save draft", "save", "draft"], exact=False, timeout=10)
            print(f"Bandcamp save draft click result: {result}")
            if not result.get("ok"):
                print("Bandcamp draft button not found; leaving the filled form open for manual save.")

        time.sleep(5)
        log_html_snapshot(driver, "bandcamp_music", "after_submit")
        return True
