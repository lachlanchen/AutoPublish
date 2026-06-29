#!/usr/bin/env python3
"""Inventory and manage Shipinhao video rows through the logged-in browser.

This script is intentionally conservative. Inventory/link discovery is read-only.
Deletion requires --apply plus a title confirmation string.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402


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


def connect_driver(port: int, chromedriver: str | None = None):
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    service = Service(executable_path=chromedriver) if chromedriver else Service()
    return webdriver.Chrome(service=service, options=options)


def classify(row: dict) -> str:
    text = f"{row.get('title', '')}\n{row.get('text', '')}".lower()
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage Shipinhao video rows by attached browser session.")
    parser.add_argument("command", choices=["inventory", "link", "delete", "move-lalachan"])
    parser.add_argument("--port", type=int, default=5006)
    parser.add_argument("--chromedriver")
    parser.add_argument("--url", default=DEFAULT_MANAGEMENT_URL, help="Use empty string to keep current tab.")
    parser.add_argument("--scrolls", type=int, default=30)
    parser.add_argument("--pause", type=float, default=1.0)
    parser.add_argument("--output")
    parser.add_argument("--query")
    parser.add_argument("--title-contains", default="")
    parser.add_argument("--collection", default="LALACHAN")
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

    if args.command == "move-lalachan":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        targets = [row for row in rows if row.get("category_guess") == "lalachan"]
        result = {
            "target_collection": args.collection,
            "dry_run": not args.apply,
            "candidates": targets,
            "note": (
                "Shipinhao existing-video collection editing is account/UI dependent. "
                "This command inventories candidates first; use the candidate links or open edit pages before applying manual moves."
            ),
        }
        save_rows([result], args.output)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
