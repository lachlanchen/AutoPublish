#!/usr/bin/env python3
"""Inventory and manage Shipinhao video rows through the logged-in browser.

This script is intentionally conservative. Inventory/link discovery is read-only.
Deletion requires --apply plus a title confirmation string.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402

from pub_shipinhao import select_content_frame_collection  # noqa: E402


DEFAULT_MANAGEMENT_URL = "https://channels.weixin.qq.com/platform/post/list"
LALACHAN_KEYWORDS = (
    "lalachan",
    "lala chan",
    "lala xia",
    "啦啦侠",
    "阿芽酱",
    "飒飒君",
    "小云雀",
    "xiaoyunque",
    "seedance",
    "duanpian",
)
MUSIC_KEYWORDS = (
    "musia",
    "musica",
    "慕莎",
    "one sky",
    "three lights",
    "hikari ame",
    "music",
    "song",
    "lyrics",
    "lyric",
    "歌曲",
    "音樂",
    "音乐",
    "歌詞",
    "歌词",
)

INVENTORY_JS = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function absHref(href) {
  if (!href) return '';
  try { return new URL(href, window.location.href).href; } catch (e) { return href; }
}
const selectors = [
  '.ant-table-row',
  '.finder-table-wrap tr',
  '.video-list .item',
  '.post-list .item',
  '[class*="video"][class*="item"]',
  '[class*="post"][class*="item"]',
  'tr',
  '[role="row"]'
];
const rows = [];
for (const selector of selectors) {
  for (const row of Array.from(document.querySelectorAll(selector))) {
    const rowText = norm(row.innerText || row.textContent || '');
    if (!rowText || rowText.length < 4) continue;
    const links = Array.from(row.querySelectorAll('a[href]')).map((a) => absHref(a.getAttribute('href'))).filter(Boolean);
    const titleNode =
      row.querySelector('[class*="title"]') ||
      row.querySelector('[class*="name"]') ||
      row.querySelector('a[href]') ||
      row;
    const title = norm(titleNode.getAttribute && (titleNode.getAttribute('title') || titleNode.getAttribute('aria-label')) || titleNode.innerText || titleNode.textContent || '');
    rows.push({
      title: title || rowText.slice(0, 120),
      links,
      text: rowText.slice(0, 1200)
    });
  }
}
const seen = new Set();
return rows.filter((row) => {
  const key = row.title + '|' + row.text.slice(0, 80);
  if (seen.has(key)) return false;
  seen.add(key);
  return true;
});
"""

DELETE_JS = r"""
const query = (arguments[0] || '').toLowerCase();
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
  el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
const rows = Array.from(document.querySelectorAll('.ant-table-row, tr, [role="row"], .item'));
const row = rows.find((item) => norm(item.innerText || item.textContent || '').toLowerCase().includes(query));
if (!row) return {ok: false, reason: 'row-not-found'};
const buttons = Array.from(row.querySelectorAll('button, a, span, div'));
const target = buttons.find((el) => /删除|delete/i.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')));
if (!target) return {ok: false, reason: 'delete-control-not-found', rowText: norm(row.innerText || row.textContent || '').slice(0, 500)};
click(target);
return {ok: true, rowText: norm(row.innerText || row.textContent || '').slice(0, 500)};
"""

CONFIRM_JS = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
const candidates = Array.from(document.querySelectorAll('button, a, span, div'));
const target = candidates.find((el) => /确定|确认|删除|delete|confirm/i.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')));
if (!target) return false;
click(target);
return true;
"""

OPEN_EDIT_JS = r"""
const query = (arguments[0] || '').toLowerCase();
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));
  el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
const rows = Array.from(document.querySelectorAll('.ant-table-row, tr, [role="row"], .item, [class*="video"][class*="item"], [class*="post"][class*="item"]'));
const row = rows.find((item) => norm(item.innerText || item.textContent || '').toLowerCase().includes(query));
if (!row) return {ok: false, reason: 'row-not-found'};
const rowText = norm(row.innerText || row.textContent || '').slice(0, 800);
const controls = Array.from(row.querySelectorAll('button, a, span, div'));
const target = controls.find((el) => /编辑|編輯|修改|管理|edit/i.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')));
if (target) {
  click(target);
  return {ok: true, action: 'clicked-edit', rowText};
}
const link = Array.from(row.querySelectorAll('a[href]')).find((a) => /edit|post|detail|video/.test(String(a.getAttribute('href') || '')));
if (link) {
  click(link);
  return {ok: true, action: 'clicked-link', href: link.href || link.getAttribute('href'), rowText};
}
click(row);
return {ok: true, action: 'clicked-row', rowText};
"""

SAVE_EDIT_JS = r"""
function norm(text) {
  return (text || '').replace(/\s+/g, ' ').trim();
}
function disabled(el) {
  const cls = String(el.className || '');
  return !!el.disabled || el.getAttribute('disabled') !== null || /\bdisabled\b/.test(cls);
}
function click(el) {
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  if (typeof el.click === 'function') el.click();
  el.dispatchEvent(new MouseEvent('click', {bubbles: true}));
  return true;
}
const buttons = Array.from(document.querySelectorAll('button, a, span, div'));
const target = buttons.find((el) => /^(保存|保存修改|完成|确定|確認|提交|更新|发表|發表)$/.test(norm(el.innerText || el.textContent || el.getAttribute('aria-label') || '')) && !disabled(el));
if (!target) return {ok: false, reason: 'save-control-not-found'};
click(target);
return {ok: true, text: norm(target.innerText || target.textContent || target.getAttribute('aria-label') || '')};
"""


def resolve_chromedriver(chromedriver: str | None = None) -> str | None:
    if chromedriver:
        return chromedriver
    for key in ("AUTOPUBLISH_CHROMEDRIVER", "CHROMEDRIVER_PATH"):
        value = os.environ.get(key)
        if value and Path(value).exists():
            return value
    for candidate in (
        "/usr/lib/chromium-browser/chromedriver",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/snap/bin/chromium.chromedriver",
    ):
        if Path(candidate).exists():
            return candidate
    return shutil.which("chromedriver")


def connect_driver(port: int, chromedriver: str | None = None):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    driver_path = resolve_chromedriver(chromedriver)
    service = Service(executable_path=driver_path) if driver_path else Service()
    return webdriver.Chrome(service=service, options=options)


def classify(row: dict) -> str:
    text = f"{row.get('title', '')}\n{row.get('text', '')}".lower()
    if any(keyword in text for keyword in MUSIC_KEYWORDS):
        return "music"
    if any(keyword in text for keyword in LALACHAN_KEYWORDS):
        return "lalachan"
    return "simplelife"


def inventory(driver, *, url: str | None, scrolls: int, pause: float) -> list[dict]:
    if url:
        driver.get(url)
        time.sleep(5)
    rows: list[dict] = []
    seen = set()
    for _ in range(max(1, scrolls)):
        current_rows = driver.execute_script(INVENTORY_JS) or []
        for row in current_rows:
            if not isinstance(row, dict):
                continue
            row["category_guess"] = classify(row)
            key = row.get("title") + "|" + str(row.get("links") or "")
            if key not in seen:
                seen.add(key)
                rows.append(row)
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(pause)
    return rows


def save_rows(rows: list[dict], output: str | None) -> None:
    payload = json.dumps(rows, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


def delete_row(driver, query: str, *, title_contains: str, apply: bool) -> dict:
    if not query:
        raise ValueError("--query is required for delete")
    if not title_contains:
        raise ValueError("--title-contains is required for delete")
    if not apply:
        return {"query": query, "title_contains": title_contains, "dry_run": True}
    state = driver.execute_script(DELETE_JS, query)
    text = json.dumps(state, ensure_ascii=False).lower()
    if title_contains.lower() not in text:
        raise RuntimeError("title confirmation text was not found in the matched row")
    time.sleep(1)
    confirmed = driver.execute_script(CONFIRM_JS)
    return {"query": query, "delete_clicked": state, "confirm_clicked": bool(confirmed)}


def move_row_to_collection(driver, query: str, collection: str, *, apply: bool, pause: float = 2.0) -> dict:
    if not query:
        raise ValueError("query is required")
    if not collection:
        raise ValueError("collection is required")
    if not apply:
        return {"query": query, "target_collection": collection, "dry_run": True}

    before_url = driver.current_url
    open_state = driver.execute_script(OPEN_EDIT_JS, query)
    if not isinstance(open_state, dict) or not open_state.get("ok"):
        return {"query": query, "target_collection": collection, "ok": False, "stage": "open-edit", "state": open_state}
    time.sleep(max(2.0, pause))

    collection_state = None
    last_error = None
    for _ in range(20):
        try:
            collection_state = select_content_frame_collection(driver, collection, duration=3)
            break
        except Exception as exc:
            last_error = str(exc)
            time.sleep(1)
    if collection_state is None:
        return {
            "query": query,
            "target_collection": collection,
            "ok": False,
            "stage": "select-collection",
            "open_state": open_state,
            "error": last_error,
            "url": driver.current_url,
        }

    save_state = None
    for _ in range(20):
        save_state = driver.execute_script(SAVE_EDIT_JS)
        if isinstance(save_state, dict) and save_state.get("ok"):
            break
        time.sleep(1)
    time.sleep(max(2.0, pause))
    return {
        "query": query,
        "target_collection": collection,
        "ok": bool(isinstance(save_state, dict) and save_state.get("ok")),
        "open_state": open_state,
        "collection_state": collection_state,
        "save_state": save_state,
        "before_url": before_url,
        "after_url": driver.current_url,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage Shipinhao video rows by attached browser session.")
    parser.add_argument("command", choices=["inventory", "link", "delete", "move", "move-lalachan", "move-music", "move-classified"])
    parser.add_argument("--port", type=int, default=5006)
    parser.add_argument("--chromedriver")
    parser.add_argument("--url", default=DEFAULT_MANAGEMENT_URL, help="Use empty string to keep current tab.")
    parser.add_argument("--scrolls", type=int, default=30)
    parser.add_argument("--pause", type=float, default=1.0)
    parser.add_argument("--output")
    parser.add_argument("--query")
    parser.add_argument("--title-contains", default="")
    parser.add_argument("--collection")
    parser.add_argument("--lalachan-collection", default="啦啦侠")
    parser.add_argument("--music-collection", default="Musia")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    driver = connect_driver(args.port, args.chromedriver)
    url = args.url if args.url else None

    if args.command == "inventory":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        save_rows(rows, args.output)
        return 0

    if args.command == "link":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        query = (args.query or "").lower()
        matches = [row for row in rows if query in json.dumps(row, ensure_ascii=False).lower()]
        save_rows(matches, args.output)
        return 0

    if args.command == "delete":
        print(json.dumps(delete_row(driver, args.query or "", title_contains=args.title_contains, apply=args.apply), ensure_ascii=False, indent=2))
        return 0

    if args.command == "move":
        print(json.dumps(
            move_row_to_collection(
                driver,
                args.query or "",
                args.collection or args.lalachan_collection,
                apply=args.apply,
                pause=args.pause,
            ),
            ensure_ascii=False,
            indent=2,
        ))
        return 0

    if args.command == "move-lalachan":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        targets = [row for row in rows if row.get("category_guess") == "lalachan"]
        collection = args.collection or args.lalachan_collection
        results = [
            move_row_to_collection(driver, row.get("title") or row.get("text", "")[:80], collection, apply=args.apply, pause=args.pause)
            for row in targets
        ]
        save_rows(results or [{"target_collection": collection, "dry_run": not args.apply, "candidates": []}], args.output)
        return 0

    if args.command == "move-music":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        targets = [row for row in rows if row.get("category_guess") == "music"]
        collection = args.collection or args.music_collection
        results = [
            move_row_to_collection(driver, row.get("title") or row.get("text", "")[:80], collection, apply=args.apply, pause=args.pause)
            for row in targets
        ]
        save_rows(results or [{"target_collection": collection, "dry_run": not args.apply, "candidates": []}], args.output)
        return 0

    if args.command == "move-classified":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        results = []
        for row in rows:
            category = row.get("category_guess")
            if category == "music":
                results.append(move_row_to_collection(driver, row.get("title") or row.get("text", "")[:80], args.music_collection, apply=args.apply, pause=args.pause))
            elif category == "lalachan":
                results.append(move_row_to_collection(driver, row.get("title") or row.get("text", "")[:80], args.lalachan_collection, apply=args.apply, pause=args.pause))
        save_rows(results, args.output)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
