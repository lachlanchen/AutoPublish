"""Post-publish verification helpers for browser-driven publishers."""

from __future__ import annotations

import os
import re
import time
from typing import Iterable

from utils import safe_get


COLLECT_TEXT_SCRIPT = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function collectShadowText(root, depth, out) {
  if (!root || depth > 8 || !root.querySelectorAll) return out;
  for (const el of root.querySelectorAll('*')) {
    if (!el.shadowRoot) continue;
    const text = norm(el.shadowRoot.innerText || el.shadowRoot.textContent || '');
    if (text) out.push(text);
    collectShadowText(el.shadowRoot, depth + 1, out);
  }
  return out;
}
const out = [];
const bodyText = norm(document.body ? document.body.innerText : '');
if (bodyText) out.push(bodyText);
const rootText = norm(document.documentElement ? document.documentElement.innerText : '');
if (rootText && rootText !== bodyText) out.push(rootText);
collectShadowText(document, 0, out);
return Array.from(new Set(out.filter(Boolean))).join('\n');
"""


SCROLL_PAGE_SCRIPT = r"""
const delta = Math.max(500, Math.floor(window.innerHeight * 0.85));
const seen = new Set();
function add(el, out) {
  if (!el || seen.has(el)) return;
  seen.add(el);
  const scrollHeight = el.scrollHeight || 0;
  const clientHeight = el.clientHeight || 0;
  if (scrollHeight > clientHeight + 80) {
    out.push(el);
  }
}
const candidates = [];
add(document.scrollingElement, candidates);
add(document.documentElement, candidates);
add(document.body, candidates);
for (const el of document.querySelectorAll('*')) {
  const style = window.getComputedStyle(el);
  const overflowY = style ? style.overflowY : '';
  if (
    (overflowY === 'auto' || overflowY === 'scroll' || overflowY === 'overlay')
    || (el.scrollHeight > el.clientHeight + 160)
  ) {
    add(el, candidates);
  }
}
candidates
  .sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))
  .slice(0, 12)
  .forEach(el => { el.scrollTop = Math.min(el.scrollTop + delta, el.scrollHeight); });
window.scrollBy(0, delta);
return candidates.length;
"""


TRADITIONAL_TO_SIMPLIFIED_HINTS = str.maketrans(
    {
        "顧": "顾",
        "護": "护",
        "癒": "愈",
        "療": "疗",
        "藝": "艺",
        "樂": "乐",
        "學": "学",
        "聲": "声",
        "錄": "录",
        "視": "视",
        "頻": "频",
        "關": "关",
        "懷": "怀",
        "氣": "气",
        "與": "与",
        "從": "从",
        "網": "网",
        "頁": "页",
        "現": "现",
        "畫": "画",
        "適": "适",
        "聽": "听",
        "眾": "众",
        "歡": "欢",
        "應": "应",
        "勵": "励",
        "繼": "继",
        "續": "续",
        "實": "实",
    }
)


def normalized_text(value: object) -> str:
    text = str(value or "")
    return re.sub(r"\s+", " ", text).strip().lower()


def text_variants(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    variants = {text, text.translate(TRADITIONAL_TO_SIMPLIFIED_HINTS)}
    compact = re.sub(r"\s+", "", text)
    if compact:
        variants.add(compact)
        variants.add(compact.translate(TRADITIONAL_TO_SIMPLIFIED_HINTS))
    return [item for item in variants if item]


def metadata_verification_terms(metadata: dict, *, include_english: bool = True) -> list[str]:
    terms: list[str] = []

    def add(value: object) -> None:
        for variant in text_variants(value):
            if len(variant) >= 4 and variant not in terms:
                terms.append(variant)

    add(metadata.get("title"))
    if include_english and isinstance(metadata.get("english_version"), dict):
        add(metadata["english_version"].get("title"))

    for key in ("brief_description", "middle_description", "long_description"):
        value = str(metadata.get(key) or "").strip()
        if value:
            add(value[:80])
            for sentence in re.split(r"[。.!?\n]", value):
                sentence = sentence.strip()
                if len(sentence) >= 12:
                    add(sentence[:60])
                    break

    return terms


def any_term_matches(page_text: str, terms: Iterable[str]) -> tuple[bool, str | None]:
    normalized_page = normalized_text(page_text)
    compact_page = normalized_page.replace(" ", "")
    for term in terms:
        normalized_term = normalized_text(term)
        if not normalized_term:
            continue
        if normalized_term in normalized_page or normalized_term.replace(" ", "") in compact_page:
            return True, term
    return False, None


def collect_page_text(driver) -> str:
    try:
        return driver.execute_script(COLLECT_TEXT_SCRIPT) or ""
    except Exception:
        try:
            return driver.execute_script("return document.body ? document.body.innerText : '';") or ""
        except Exception:
            return ""


def scroll_management_page(driver) -> int:
    try:
        return int(driver.execute_script(SCROLL_PAGE_SCRIPT) or 0)
    except Exception:
        try:
            driver.execute_script("window.scrollBy(0, Math.floor(window.innerHeight * 0.85));")
        except Exception:
            pass
        return 0


def click_management_tab(driver, xpath: str, platform_name: str) -> bool:
    try:
        elements = driver.find_elements("xpath", xpath)
    except Exception:
        return False
    for element in elements:
        try:
            if not element.is_displayed():
                continue
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", element)
            print(f"{platform_name} verification clicked management tab: {xpath}")
            time.sleep(3)
            return True
        except Exception:
            continue
    return False


def verify_publish_in_management(
    driver,
    management_url: str,
    metadata: dict,
    *,
    platform_name: str,
    timeout: int | None = None,
    scrolls_per_pass: int = 3,
    include_english: bool = True,
    tab_xpaths: Iterable[str] | None = None,
) -> bool:
    """Verify that a newly published item appears in the platform management UI.

    Browser upload pages can report success after only a button click. This
    helper makes success mean that the post is visible in the creator/content
    management page with title or description text from the metadata.
    """
    if os.environ.get("AUTOPUB_VERIFY_PUBLISH", "1").strip().lower() in {"0", "false", "no", "off"}:
        print(f"{platform_name} post-publish verification disabled by AUTOPUB_VERIFY_PUBLISH.")
        return True

    if timeout is None:
        timeout = int(os.environ.get("AUTOPUB_VERIFY_TIMEOUT", "240"))

    terms = metadata_verification_terms(metadata, include_english=include_english)
    if not terms:
        raise RuntimeError(f"{platform_name} verification has no usable metadata terms.")

    print(f"Verifying {platform_name} publish in management page: {management_url}")
    print(f"{platform_name} verification terms: {terms[:5]}")

    deadline = time.time() + timeout
    last_excerpt = ""
    tab_xpaths = list(tab_xpaths or [])
    while time.time() < deadline:
        safe_get(driver, management_url, timeout=45, label=f"{platform_name} management page")
        time.sleep(5)
        for tab_xpath in [None, *tab_xpaths]:
            if tab_xpath:
                click_management_tab(driver, tab_xpath, platform_name)
            for scroll_index in range(max(1, scrolls_per_pass)):
                page_text = collect_page_text(driver)
                matched, term = any_term_matches(page_text, terms)
                if matched:
                    print(f"{platform_name} management verification matched term: {term!r}")
                    return True
                if page_text:
                    last_excerpt = page_text[:1000]
                scroll_management_page(driver)
                time.sleep(2)
        time.sleep(8)

    raise RuntimeError(
        f"{platform_name} publish verification failed: post not found in management page. "
        f"Last text excerpt: {last_excerpt!r}"
    )
