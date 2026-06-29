#!/usr/bin/env python3
"""Inventory and manage YouTube Studio videos through the logged-in browser.

Default behavior is read-only. Use --apply for playlist moves or deletes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver  # noqa: E402
from selenium.common.exceptions import TimeoutException, WebDriverException  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

from pub_y2b import YouTubePublisher  # noqa: E402


DEFAULT_STUDIO_URL = os.environ.get("YOUTUBE_STUDIO_CONTENT_URL", "https://studio.youtube.com")
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
    "啦啦俠",
    "阿芽醬",
    "颯颯君",
    "莎莎君",
    "拉拉夏",
    "莊子機器人",
    "庄子机器人",
)
MUSIC_KEYWORDS = (
    "musia",
    "musica",
    "慕莎",
    "one sky",
    "three lights",
    "hikari ame",
    "lyrics",
    "lyric",
    "歌詞",
    "歌词",
)

INVENTORY_JS = r"""
function text(el) {
  return (el && (el.innerText || el.textContent || '') || '').replace(/\s+/g, ' ').trim();
}
function videoIdFromHref(href) {
  if (!href) return '';
  let match = href.match(/[?&]v=([A-Za-z0-9_-]{6,})/);
  if (match) return match[1];
  match = href.match(/\/video\/([A-Za-z0-9_-]{6,})/);
  if (match) return match[1];
  match = href.match(/youtu\.be\/([A-Za-z0-9_-]{6,})/);
  return match ? match[1] : '';
}
const rowSelectors = [
  'ytcp-video-row',
  'ytcp-entity-page-item',
  'tr',
  'div[role="row"]',
  '#row-container',
  '.row-container'
];
const rows = [];
for (const selector of rowSelectors) {
  for (const row of Array.from(document.querySelectorAll(selector))) {
    const rowText = text(row);
    if (!rowText || rowText.length < 3) continue;
    const anchors = Array.from(row.querySelectorAll('a[href]'));
    let href = '';
    let videoId = '';
    for (const a of anchors) {
      const candidate = a.href || a.getAttribute('href') || '';
      const id = videoIdFromHref(candidate);
      if (id) {
        href = candidate;
        videoId = id;
        break;
      }
    }
    const titleNode =
      row.querySelector('#video-title') ||
      row.querySelector('[id*="video-title"]') ||
      row.querySelector('a[title]') ||
      row.querySelector('[aria-label]');
    const title =
      (titleNode && (titleNode.getAttribute('title') || titleNode.getAttribute('aria-label') || text(titleNode))) ||
      rowText.split(' Visibility ')[0].split(' 可见性 ')[0].trim();
    rows.push({
      video_id: videoId,
      title,
      href,
      text: rowText.slice(0, 1000)
    });
  }
}
const seen = new Set();
return rows.filter((row) => {
  const key = row.video_id || row.title + row.text.slice(0, 80);
  if (seen.has(key)) return false;
  seen.add(key);
  return row.video_id || row.title;
});
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
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(int(os.environ.get("YOUTUBE_STUDIO_PAGE_LOAD_TIMEOUT", "45")))
    return driver


def safe_get(driver, url: str, *, settle_seconds: float = 5.0) -> None:
    if os.environ.get("YOUTUBE_STUDIO_CDP_NAVIGATE", "1") != "0":
        try:
            driver.execute_cdp_cmd("Page.navigate", {"url": url})
            time.sleep(settle_seconds)
            return
        except WebDriverException:
            pass
    try:
        driver.get(url)
    except TimeoutException:
        try:
            driver.execute_script("window.stop();")
        except WebDriverException:
            pass
    except WebDriverException:
        pass
    time.sleep(settle_seconds)


def classify(row: dict) -> str:
    text = f"{row.get('title', '')}\n{row.get('text', '')}".lower()
    if any(keyword in text for keyword in MUSIC_KEYWORDS):
        return "music"
    if any(keyword in text for keyword in LALACHAN_KEYWORDS):
        return "lalachan"
    return "simplelife"


def inventory(driver, *, url: str | None, scrolls: int, pause: float) -> list[dict]:
    if url:
        safe_get(driver, url)
    rows: list[dict] = []
    seen = set()
    for _ in range(max(1, scrolls)):
        for row in driver.execute_script(INVENTORY_JS) or []:
            if not isinstance(row, dict):
                continue
            row["category_guess"] = classify(row)
            key = row.get("video_id") or row.get("title")
            if key and key not in seen:
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


def open_edit_page(driver, video_id: str) -> None:
    safe_get(driver, f"https://studio.youtube.com/video/{video_id}/edit", settle_seconds=3)
    WebDriverWait(driver, 60).until(lambda d: "studio.youtube.com" in d.current_url)
    time.sleep(8)


def click_save(driver, timeout: int = 20) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        clicked = driver.execute_script(
            r"""
const candidates = Array.from(document.querySelectorAll('ytcp-button, button, tp-yt-paper-button'));
function text(el) { return (el.innerText || el.textContent || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim(); }
const save = candidates.find((el) => /^(Save|保存)$/i.test(text(el)) && !/disabled/.test(String(el.className || '')));
if (!save) return false;
save.click();
return true;
"""
        )
        if clicked:
            time.sleep(3)
            return True
        time.sleep(1)
    return False


def move_to_playlist(driver, video_id: str, playlist: str, *, apply: bool) -> dict:
    if not apply:
        return {"video_id": video_id, "target_playlist": playlist, "dry_run": True}
    open_edit_page(driver, video_id)
    publisher = YouTubePublisher(driver, "", "", {"playlist_name": playlist}, test=False)
    publisher.set_playlist()
    saved = click_save(driver)
    return {"video_id": video_id, "target_playlist": playlist, "saved": saved}


def delete_video(driver, video_id: str, *, title_contains: str, apply: bool) -> dict:
    if not title_contains:
        raise ValueError("--title-contains is required for delete")
    if not apply:
        return {"video_id": video_id, "title_contains": title_contains, "dry_run": True}
    open_edit_page(driver, video_id)
    title_text = driver.execute_script(
        "return (document.body.innerText || document.body.textContent || '').replace(/\\s+/g, ' ').trim();"
    )
    if title_contains.lower() not in title_text.lower():
        raise RuntimeError("title confirmation text was not found on the edit page")
    clicked = driver.execute_script(
        r"""
function text(el) { return (el.innerText || el.textContent || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim(); }
const buttons = Array.from(document.querySelectorAll('ytcp-button, button, tp-yt-paper-button'));
const target = buttons.find((el) => /delete forever|delete|永久删除|删除/i.test(text(el)));
if (!target) return false;
target.click();
return true;
"""
    )
    return {"video_id": video_id, "delete_clicked": bool(clicked)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage YouTube Studio videos by attached browser session.")
    parser.add_argument("command", choices=["inventory", "move-lalachan", "move-music", "move-classified", "move", "link", "delete"])
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--chromedriver")
    parser.add_argument("--url", default=DEFAULT_STUDIO_URL, help="Studio content URL. Use empty string to keep current tab.")
    parser.add_argument("--scrolls", type=int, default=30)
    parser.add_argument("--pause", type=float, default=1.0)
    parser.add_argument("--output")
    parser.add_argument("--playlist")
    parser.add_argument("--lalachan-playlist", default="LALACHAN")
    parser.add_argument("--music-playlist", default="Musia")
    parser.add_argument("--video-id")
    parser.add_argument("--query")
    parser.add_argument("--title-contains", default="")
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

    if args.command == "move-lalachan":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        targets = [row for row in rows if row.get("category_guess") == "lalachan" and row.get("video_id")]
        playlist = args.playlist or args.lalachan_playlist
        results = [move_to_playlist(driver, row["video_id"], playlist, apply=args.apply) for row in targets]
        save_rows(results, args.output)
        return 0

    if args.command == "move-music":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        targets = [row for row in rows if row.get("category_guess") == "music" and row.get("video_id")]
        playlist = args.playlist or args.music_playlist
        results = [move_to_playlist(driver, row["video_id"], playlist, apply=args.apply) for row in targets]
        save_rows(results, args.output)
        return 0

    if args.command == "move-classified":
        rows = inventory(driver, url=url, scrolls=args.scrolls, pause=args.pause)
        results = []
        for row in rows:
            video_id = row.get("video_id")
            if not video_id:
                continue
            category = row.get("category_guess")
            if category == "music":
                results.append(move_to_playlist(driver, video_id, args.music_playlist, apply=args.apply))
            elif category == "lalachan":
                results.append(move_to_playlist(driver, video_id, args.lalachan_playlist, apply=args.apply))
        save_rows(results, args.output)
        return 0

    if args.command == "move":
        if not args.video_id:
            parser.error("--video-id is required for move")
        if not args.playlist:
            parser.error("--playlist is required for move")
        print(json.dumps(move_to_playlist(driver, args.video_id, args.playlist, apply=args.apply), ensure_ascii=False, indent=2))
        return 0

    if args.command == "delete":
        if not args.video_id:
            parser.error("--video-id is required for delete")
        print(json.dumps(delete_video(driver, args.video_id, title_contains=args.title_contains, apply=args.apply), ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
