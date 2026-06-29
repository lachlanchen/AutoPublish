#!/usr/bin/env python3
"""Mirrored Shipinhao post management.

This tool is intentionally separate from publication. It attaches to the
logged-in Shipinhao browser only for management actions, and it can also run
offline to export LazyEdit metadata or build a repair plan.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

DATE_RE = re.compile(r"(20\d{2})年(\d{2})月(\d{2})日\s+(\d{2}):(\d{2})")
PUNCT_RE = re.compile(r"[\s\W_]+", re.UNICODE)
DEFAULT_SHIPINHAO_VIDEO_LIST_URL = "https://channels.weixin.qq.com/platform/post/list"

SET_DESCRIPTION_JS = r"""
const text = arguments[0] || '';
function norm(value) {
  return (value || '').replace(/\s+/g, ' ').trim();
}
function roots() {
  const app = document.querySelector('wujie-app');
  return [document, app && app.shadowRoot].filter(Boolean);
}
function queryAll(selector) {
  return roots().flatMap((root) => Array.from(root.querySelectorAll(selector)));
}
function visibleEnough(el) {
  const rect = el.getBoundingClientRect();
  const style = window.getComputedStyle(el);
  return rect.width > 1 && rect.height > 1 && style.display !== 'none' && style.visibility !== 'hidden';
}
function setInput(input, value) {
  const proto = input instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const descriptor = Object.getOwnPropertyDescriptor(proto, 'value');
  if (descriptor && descriptor.set) {
    descriptor.set.call(input, value);
  } else {
    input.value = value;
  }
  input.dispatchEvent(new Event('input', {bubbles: true}));
  input.dispatchEvent(new Event('change', {bubbles: true}));
}
function setEditable(editor, value) {
  editor.focus();
  editor.innerHTML = '';
  editor.textContent = value;
  editor.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText', data: value}));
  editor.dispatchEvent(new Event('change', {bubbles: true}));
  editor.blur();
}
const candidates = queryAll('.input-editor[contenteditable], [contenteditable][data-placeholder], textarea, [contenteditable]')
  .filter(visibleEnough);
const editor =
  candidates.find((el) => /input-editor/.test(String(el.className || ''))) ||
  candidates.find((el) => /描述|desc|description|添加/.test((el.getAttribute('placeholder') || '') + ' ' + (el.getAttribute('data-placeholder') || '') + ' ' + String(el.className || ''))) ||
  candidates[0];
if (!editor) {
  return {ok: false, reason: 'description-editor-not-found'};
}
if (editor.tagName === 'TEXTAREA' || editor.tagName === 'INPUT') {
  setInput(editor, text);
} else {
  setEditable(editor, text);
}
return {
  ok: true,
  tag: editor.tagName,
  className: String(editor.className || ''),
  placeholder: editor.getAttribute('placeholder') || editor.getAttribute('data-placeholder') || '',
  value: norm(editor.innerText || editor.textContent || editor.value || '')
};
"""


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path | None, payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def compact_text(value: Any) -> str:
    return PUNCT_RE.sub("", str(value or "").lower())


def parse_shipinhao_time(text: str) -> str | None:
    match = DATE_RE.search(text or "")
    if not match:
        return None
    year, month, day, hour, minute = map(int, match.groups())
    return datetime(year, month, day, hour, minute).isoformat(timespec="minutes")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def remove_non_bmp(text: str) -> str:
    return "".join(ch for ch in (text or "") if ord(ch) <= 0xFFFF)


def build_shipinhao_description(metadata: dict[str, Any]) -> str:
    body = (
        metadata.get("long_description")
        or metadata.get("middle_description")
        or metadata.get("brief_description")
        or metadata.get("title")
        or ""
    )
    tags = metadata.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    tag_text = " ".join(
        "#" + str(tag).strip().lstrip("#")
        for tag in tags
        if str(tag).strip()
    )
    return remove_non_bmp(normalize_text(f"{body} {tag_text}"))


def visible_description(row: dict[str, Any]) -> str:
    title = normalize_text(row.get("title"))
    if title:
        return title
    text = normalize_text(row.get("text"))
    match = DATE_RE.search(text)
    if match:
        return normalize_text(text[: match.start()])
    return text


def load_metadata_record(path: Path) -> dict[str, Any] | None:
    try:
        metadata = read_json(path)
    except Exception:
        return None
    if not isinstance(metadata, dict):
        return None
    stat = path.stat()
    description = build_shipinhao_description(metadata)
    return {
        "metadata_path": str(path),
        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="minutes"),
        "folder": path.parents[1].name if path.parent.name == "publish" else path.parent.name,
        "title": normalize_text(metadata.get("title")),
        "description": description,
        "cover": metadata.get("cover"),
        "video_filename": metadata.get("video_filename"),
        "publish_category": metadata.get("publish_category"),
        "shipinhao_collection": metadata.get("shipinhao_collection"),
        "tags": metadata.get("tags") if isinstance(metadata.get("tags"), list) else [],
    }


def export_metadata(metadata_root: str | Path, *, days: int | None = None) -> list[dict[str, Any]]:
    root = Path(metadata_root).expanduser().resolve()
    cutoff = None
    if days is not None:
        cutoff = time.time() - max(days, 0) * 86400
    records: list[dict[str, Any]] = []
    for path in root.glob("**/publish/*_metadata.json"):
        if cutoff and path.stat().st_mtime < cutoff:
            continue
        record = load_metadata_record(path)
        if record and record.get("description"):
            records.append(record)
    records.sort(key=lambda item: item.get("mtime") or "")
    return records


def text_score(row_text: str, record: dict[str, Any]) -> int:
    row_compact = compact_text(row_text)
    title = compact_text(record.get("title"))
    desc = compact_text(record.get("description"))
    score = 0
    if title and title in row_compact:
        score += 80
    if desc:
        sample_lengths = (80, 40, 24, 16)
        for length in sample_lengths:
            sample = desc[:length]
            if len(sample) >= min(length, 16) and sample in row_compact:
                score += 70
                break
    for tag in record.get("tags") or []:
        tag_compact = compact_text(tag)
        if tag_compact and tag_compact in row_compact:
            score += 4
    folder = compact_text(record.get("folder"))
    if folder and folder in row_compact:
        score += 20
    return score


def time_score(row_time: str | None, record_time: str | None) -> int:
    row_dt = parse_iso(row_time)
    meta_dt = parse_iso(record_time)
    if not row_dt or not meta_dt:
        return 0
    diff_minutes = abs((row_dt - meta_dt).total_seconds()) / 60
    if diff_minutes <= 3:
        return 85
    if diff_minutes <= 7:
        return 75
    if diff_minutes <= 12:
        return 65
    if diff_minutes <= 20:
        return 50
    if diff_minutes <= 90:
        return 35
    if diff_minutes <= 240:
        return 15
    if diff_minutes <= 1440:
        return 5
    return 0


def choose_match(row: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any] | None:
    row_text = "\n".join(
        part
        for part in (
            normalize_text(row.get("title")),
            normalize_text(row.get("text")),
        )
        if part
    )
    row_time = row.get("published_at") or parse_shipinhao_time(row_text)
    best: dict[str, Any] | None = None
    for record in records:
        score = text_score(row_text, record) + time_score(row_time, record.get("mtime"))
        if score <= 0:
            continue
        candidate = {
            "score": score,
            "row_published_at": row_time,
            **record,
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    return best


def common_prefix_hit(expected: str, current: str, min_chars: int = 24) -> bool:
    expected_c = compact_text(expected)
    current_c = compact_text(current)
    if not expected_c or not current_c:
        return False
    for size in (80, 48, 32, min_chars):
        sample = expected_c[:size]
        if len(sample) >= min(size, min_chars) and sample in current_c:
            return True
    return False


def build_description_plan(
    mirror_rows: list[dict[str, Any]],
    records: list[dict[str, Any]],
    *,
    score_threshold: int = 60,
    min_current_chars: int = 60,
    repair_mismatched: bool = False,
    include_ok: bool = False,
) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for index, row in enumerate(mirror_rows, start=1):
        current = visible_description(row)
        current_compact_len = len(compact_text(current))
        match = choose_match(row, records)
        row_time = row.get("published_at") or parse_shipinhao_time("\n".join(
            str(row.get(key) or "") for key in ("title", "text")
        ))
        effective_threshold = score_threshold
        if current_compact_len < min_current_chars and row_time:
            # Date-only rows cannot text-match because Shipinhao lost the
            # description. A tight publish-time match is enough for a repair
            # plan, but only for too-short rows.
            effective_threshold = min(effective_threshold, 50)
        if not match or match["score"] < effective_threshold:
            if include_ok:
                plan.append({
                    "index": index,
                    "action": "skip",
                    "reason": "no-confident-match",
                    "current_description": current,
                    "row_published_at": row_time,
                    "row": row,
                    "match": match,
                })
            continue
        expected = match.get("description") or ""
        has_enough_description = current_compact_len >= min_current_chars
        already_ok = has_enough_description and common_prefix_hit(expected, current)
        should_update = (not has_enough_description) or (repair_mismatched and not already_ok)
        action = "update-description" if should_update else "skip"
        if already_ok:
            reason = "already-has-description"
        elif has_enough_description:
            reason = "mismatched-but-not-overwriting"
        else:
            reason = "missing-or-too-short-description"
        plan.append({
            "index": index,
            "action": action,
            "reason": reason,
            "query": current[:80],
            "current_description": current,
            "new_description": expected,
            "current_length": len(current),
            "new_length": len(expected),
            "row_published_at": match.get("row_published_at"),
            "match_score": match.get("score"),
            "metadata_path": match.get("metadata_path"),
            "metadata_title": match.get("title"),
            "metadata_mtime": match.get("mtime"),
            "row": row,
        })
    return plan


def run_mirror(args: argparse.Namespace) -> int:
    from manage_shipinhao_videos import connect_driver, inventory

    driver = connect_driver(args.port, args.chromedriver)
    rows = inventory(driver, url=args.url if args.url else None, scrolls=args.scrolls, pause=args.pause)
    now = datetime.now().isoformat(timespec="seconds")
    for idx, row in enumerate(rows, start=1):
        text = "\n".join(str(row.get(key) or "") for key in ("title", "text"))
        row["mirror_index"] = idx
        row["published_at"] = parse_shipinhao_time(text)
        row["mirrored_at"] = now
    write_json(args.output, rows)
    return 0


def apply_description_plan(args: argparse.Namespace) -> int:
    from manage_shipinhao_videos import SAVE_EDIT_JS, connect_driver, open_edit_row
    from pub_shipinhao import ensure_content_frame_editable_value

    plan = read_json(args.plan)
    if not isinstance(plan, list):
        raise ValueError("plan must be a JSON list")
    targets = [item for item in plan if item.get("action") == "update-description"]
    if args.limit:
        targets = targets[: args.limit]
    driver = connect_driver(args.port, args.chromedriver)
    if args.url:
        driver.get(args.url)
        time.sleep(5)
    results = []
    for item in targets:
        query = normalize_text(item.get("query"))
        description = normalize_text(item.get("new_description"))
        if not query or not description:
            results.append({"ok": False, "reason": "missing-query-or-description", "item": item})
            continue
        if not args.apply:
            results.append({"ok": True, "dry_run": True, "query": query, "new_length": len(description)})
            continue
        open_state = open_edit_row(driver, query, pause=args.pause)
        if not isinstance(open_state, dict) or not open_state.get("ok"):
            results.append({"ok": False, "stage": "open-edit", "query": query, "state": open_state})
            continue
        dialog_state = open_state.get("dialog_state") if isinstance(open_state.get("dialog_state"), dict) else {}
        if dialog_state.get("isCoverEdit") and not dialog_state.get("hasEditor"):
            results.append({
                "ok": False,
                "stage": "unsupported-description-repair",
                "query": query,
                "reason": "Shipinhao coverEdit only supports modifying selected existing text, limited to 20 characters; blank/missing descriptions cannot be restored through the visible UI.",
                "current_description_text": dialog_state.get("descriptionText", ""),
                "new_length": len(description),
                "metadata_path": item.get("metadata_path"),
            })
            try:
                driver.back()
                time.sleep(max(args.pause, 2.0))
            except Exception:
                pass
            continue
        time.sleep(max(args.pause, 1.0))
        try:
            try:
                value = ensure_content_frame_editable_value(
                    driver,
                    ".input-editor[contenteditable]",
                    description,
                    duration=12,
                )
            except Exception:
                set_state = driver.execute_script(SET_DESCRIPTION_JS, description)
                if not isinstance(set_state, dict) or not set_state.get("ok"):
                    raise RuntimeError(f"description editor not filled: {set_state}")
                value = set_state.get("value") or ""
                expected = normalize_text(description)
                if expected not in normalize_text(value) and normalize_text(value) != expected:
                    raise RuntimeError(f"description verify failed: {set_state}")
        except Exception as exc:
            results.append({"ok": False, "stage": "fill-description", "query": query, "error": str(exc)})
            continue
        save_state = None
        for _ in range(20):
            save_state = driver.execute_script(SAVE_EDIT_JS)
            if isinstance(save_state, dict) and save_state.get("ok"):
                break
            time.sleep(1)
        results.append({
            "ok": bool(isinstance(save_state, dict) and save_state.get("ok")),
            "query": query,
            "filled_length": len(value or ""),
            "save_state": save_state,
            "metadata_path": item.get("metadata_path"),
        })
        time.sleep(max(args.pause, 2.0))
    write_json(args.output, results)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mirror and manage Shipinhao videos without coupling to publication.")
    sub = parser.add_subparsers(dest="command", required=True)

    meta = sub.add_parser("export-metadata", help="Export LazyEdit publish metadata into a portable index.")
    meta.add_argument("--metadata-root", default=os.environ.get("LAZYEDIT_DATA_ROOT", "/home/lachlan/DiskMech/Projects/lazyedit/DATA"))
    meta.add_argument("--days", type=int, default=90)
    meta.add_argument("--output")

    mirror = sub.add_parser("mirror", help="Mirror the logged-in Shipinhao video list.")
    mirror.add_argument("--port", type=int, default=5006)
    mirror.add_argument("--chromedriver")
    mirror.add_argument("--url", default="https://channels.weixin.qq.com/platform/post/list")
    mirror.add_argument("--scrolls", type=int, default=30)
    mirror.add_argument("--pause", type=float, default=1.0)
    mirror.add_argument("--output", default="logs/shipinhao-video-mirror.json")

    plan = sub.add_parser("plan-descriptions", help="Match mirror rows to metadata and build a safe repair plan.")
    plan.add_argument("--mirror", required=True)
    plan.add_argument("--metadata-index", required=True)
    plan.add_argument("--score-threshold", type=int, default=60)
    plan.add_argument("--min-current-chars", type=int, default=60)
    plan.add_argument("--repair-mismatched", action="store_true")
    plan.add_argument("--include-ok", action="store_true")
    plan.add_argument("--output")

    apply = sub.add_parser("apply-descriptions", help="Apply a description repair plan through Shipinhao UI.")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--port", type=int, default=5006)
    apply.add_argument("--chromedriver")
    apply.add_argument("--url", default=DEFAULT_SHIPINHAO_VIDEO_LIST_URL, help="Use empty string to keep the current page.")
    apply.add_argument("--pause", type=float, default=2.0)
    apply.add_argument("--limit", type=int, default=0)
    apply.add_argument("--apply", action="store_true")
    apply.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "export-metadata":
        write_json(args.output, export_metadata(args.metadata_root, days=args.days))
        return 0
    if args.command == "mirror":
        return run_mirror(args)
    if args.command == "plan-descriptions":
        mirror_rows = read_json(args.mirror)
        records = read_json(args.metadata_index)
        if not isinstance(mirror_rows, list) or not isinstance(records, list):
            raise ValueError("mirror and metadata index must both be JSON lists")
        write_json(
            args.output,
            build_description_plan(
                mirror_rows,
                records,
                score_threshold=args.score_threshold,
                min_current_chars=args.min_current_chars,
                repair_mismatched=args.repair_mismatched,
                include_ok=args.include_ok,
            ),
        )
        return 0
    if args.command == "apply-descriptions":
        return apply_description_plan(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
