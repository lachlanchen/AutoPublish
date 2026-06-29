#!/usr/bin/env python3
"""Mirrored Shipinhao post management.

This tool is intentionally separate from publication. It attaches to the
logged-in Shipinhao browser only for management actions, and it can also run
offline to export LazyEdit metadata or build a repair plan.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
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


def sha256_text(value: Any) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def sha256_file(path: str | Path | None, *, max_bytes: int | None = None) -> str | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None
    digest = hashlib.sha256()
    remaining = max_bytes
    with file_path.open("rb") as handle:
        while True:
            if remaining is None:
                chunk = handle.read(1024 * 1024)
            elif remaining <= 0:
                break
            else:
                chunk = handle.read(min(1024 * 1024, remaining))
                remaining -= len(chunk)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def json_loads(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


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


def row_key(row: dict[str, Any]) -> str:
    published_at = row.get("published_at") or parse_shipinhao_time(
        "\n".join(str(row.get(key) or "") for key in ("title", "text"))
    )
    payload = {
        "published_at": published_at,
        "title": normalize_text(row.get("title"))[:240],
        "text_head": normalize_text(row.get("text"))[:240],
        "links": row.get("links") or [],
        "images": row.get("images") or [],
    }
    return sha256_text(json_dumps(payload))[:24]


def find_publish_sibling(metadata_path: Path, suffix: str) -> str | None:
    candidate = metadata_path.with_name(metadata_path.name.removesuffix("_metadata.json") + suffix)
    if candidate.exists():
        return str(candidate)
    return None


def find_local_video_path(metadata_path: Path, metadata: dict[str, Any]) -> str | None:
    filename = metadata.get("video_filename")
    if filename:
        for root in (metadata_path.parent, metadata_path.parent.parent, metadata_path.parents[1] if len(metadata_path.parents) > 1 else metadata_path.parent):
            candidate = root / str(filename)
            if candidate.exists():
                return str(candidate)
    return None


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
    cover_path = find_publish_sibling(path, "_cover.jpg")
    zip_path = find_publish_sibling(path, ".zip")
    video_path = find_local_video_path(path, metadata)
    return {
        "metadata_path": str(path),
        "metadata_sha256": sha256_file(path),
        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="minutes"),
        "folder": path.parents[1].name if path.parent.name == "publish" else path.parent.name,
        "title": normalize_text(metadata.get("title")),
        "description": description,
        "description_sha256": sha256_text(description),
        "cover": metadata.get("cover"),
        "cover_path": cover_path,
        "cover_sha256": sha256_file(cover_path),
        "zip_path": zip_path,
        "zip_sha256_head": sha256_file(zip_path, max_bytes=1024 * 1024),
        "video_path": video_path,
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
                    "row_key": row.get("row_key") or row_key(row),
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
            "row_key": row.get("row_key") or row_key(row),
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


def export_publish_history(*, limit: int = 500, only_shipinhao: bool = True) -> list[dict[str, Any]]:
    """Export LazyEdit publish job history when the local Postgres DB is reachable."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except Exception as exc:
        raise RuntimeError("psycopg2 is required to export LazyEdit publish history") from exc

    db_url = os.getenv("LAZYEDIT_DATABASE_URL") or os.getenv("DATABASE_URL") or "dbname=lazyedit_db"
    query = """
        SELECT
            j.id,
            j.video_id,
            j.status,
            j.platforms,
            j.test_mode,
            j.config,
            j.detail,
            j.zip_path,
            j.metadata_path,
            j.cover_path,
            j.video_path,
            j.remote_job_id,
            j.remote_filename,
            j.remote_status,
            j.error,
            j.created_at,
            j.updated_at,
            j.started_at,
            j.finished_at,
            j.publication_session_id,
            v.title AS video_title,
            v.file_path AS video_file_path
        FROM publish_jobs j
        LEFT JOIN videos v ON v.id = j.video_id
        ORDER BY j.created_at DESC, j.id DESC
        LIMIT %s
    """
    rows: list[dict[str, Any]] = []
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (limit,))
            for raw in cur.fetchall():
                row = dict(raw)
                for key in ("created_at", "updated_at", "started_at", "finished_at"):
                    value = row.get(key)
                    if value is not None:
                        row[key] = value.isoformat(timespec="seconds")
                platforms = row.get("platforms") or {}
                if isinstance(platforms, str):
                    platforms = json_loads(platforms, {})
                row["platforms"] = platforms if isinstance(platforms, dict) else {}
                if only_shipinhao and not row["platforms"].get("shipinhao"):
                    continue
                config = row.get("config") or {}
                if isinstance(config, str):
                    config = json_loads(config, {})
                row["config"] = config if isinstance(config, dict) else {}
                rows.append(row)
    return rows


def init_db(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS shipinhao_rows (
            row_key TEXT PRIMARY KEY,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            mirrored_at TEXT,
            published_at TEXT,
            title TEXT,
            visible_description TEXT,
            text TEXT,
            links_json TEXT NOT NULL DEFAULT '[]',
            images_json TEXT NOT NULL DEFAULT '[]',
            attrs_json TEXT NOT NULL DEFAULT '{}',
            category_guess TEXT,
            row_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_shipinhao_rows_published_at ON shipinhao_rows (published_at);
        CREATE INDEX IF NOT EXISTS idx_shipinhao_rows_category ON shipinhao_rows (category_guess);

        CREATE TABLE IF NOT EXISTS lazyedit_metadata (
            metadata_path TEXT PRIMARY KEY,
            metadata_sha256 TEXT,
            mtime TEXT,
            folder TEXT,
            title TEXT,
            description TEXT,
            description_sha256 TEXT,
            cover_path TEXT,
            cover_sha256 TEXT,
            zip_path TEXT,
            zip_sha256_head TEXT,
            video_path TEXT,
            video_filename TEXT,
            publish_category TEXT,
            shipinhao_collection TEXT,
            tags_json TEXT NOT NULL DEFAULT '[]',
            record_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_lazyedit_metadata_mtime ON lazyedit_metadata (mtime);
        CREATE INDEX IF NOT EXISTS idx_lazyedit_metadata_category ON lazyedit_metadata (publish_category);

        CREATE TABLE IF NOT EXISTS lazyedit_publish_jobs (
            job_id INTEGER PRIMARY KEY,
            video_id INTEGER,
            status TEXT,
            platforms_json TEXT NOT NULL DEFAULT '{}',
            config_json TEXT NOT NULL DEFAULT '{}',
            detail TEXT,
            zip_path TEXT,
            metadata_path TEXT,
            cover_path TEXT,
            video_path TEXT,
            remote_job_id TEXT,
            remote_filename TEXT,
            remote_status TEXT,
            error TEXT,
            created_at TEXT,
            updated_at TEXT,
            started_at TEXT,
            finished_at TEXT,
            publication_session_id INTEGER,
            video_title TEXT,
            video_file_path TEXT,
            job_json TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_lazyedit_publish_jobs_created ON lazyedit_publish_jobs (created_at);
        CREATE INDEX IF NOT EXISTS idx_lazyedit_publish_jobs_metadata ON lazyedit_publish_jobs (metadata_path);

        CREATE TABLE IF NOT EXISTS shipinhao_matches (
            row_key TEXT NOT NULL,
            metadata_path TEXT NOT NULL,
            score INTEGER NOT NULL,
            action TEXT,
            reason TEXT,
            plan_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (row_key, metadata_path)
        );
        CREATE INDEX IF NOT EXISTS idx_shipinhao_matches_action ON shipinhao_matches (action);

        CREATE TABLE IF NOT EXISTS shipinhao_apply_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            row_key TEXT,
            metadata_path TEXT,
            action TEXT NOT NULL,
            ok INTEGER NOT NULL DEFAULT 0,
            stage TEXT,
            reason TEXT,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    return conn


def upsert_mirror_rows(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> int:
    count = 0
    now = now_iso()
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = row.get("row_key") or row_key(row)
        row["row_key"] = key
        published_at = row.get("published_at") or parse_shipinhao_time(
            "\n".join(str(row.get(part) or "") for part in ("title", "text"))
        )
        conn.execute(
            """
            INSERT INTO shipinhao_rows (
                row_key, first_seen_at, last_seen_at, mirrored_at, published_at,
                title, visible_description, text, links_json, images_json,
                attrs_json, category_guess, row_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(row_key) DO UPDATE SET
                last_seen_at=excluded.last_seen_at,
                mirrored_at=excluded.mirrored_at,
                published_at=excluded.published_at,
                title=excluded.title,
                visible_description=excluded.visible_description,
                text=excluded.text,
                links_json=excluded.links_json,
                images_json=excluded.images_json,
                attrs_json=excluded.attrs_json,
                category_guess=excluded.category_guess,
                row_json=excluded.row_json
            """,
            (
                key,
                now,
                now,
                row.get("mirrored_at") or now,
                published_at,
                normalize_text(row.get("title")),
                visible_description(row),
                normalize_text(row.get("text")),
                json_dumps(row.get("links") or []),
                json_dumps(row.get("images") or []),
                json_dumps(row.get("attrs") or {}),
                row.get("category_guess"),
                json_dumps(row),
            ),
        )
        count += 1
    conn.commit()
    return count


def upsert_metadata_records(conn: sqlite3.Connection, records: list[dict[str, Any]]) -> int:
    count = 0
    now = now_iso()
    for record in records:
        if not isinstance(record, dict) or not record.get("metadata_path"):
            continue
        conn.execute(
            """
            INSERT INTO lazyedit_metadata (
                metadata_path, metadata_sha256, mtime, folder, title,
                description, description_sha256, cover_path, cover_sha256,
                zip_path, zip_sha256_head, video_path, video_filename,
                publish_category, shipinhao_collection, tags_json, record_json,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(metadata_path) DO UPDATE SET
                metadata_sha256=excluded.metadata_sha256,
                mtime=excluded.mtime,
                folder=excluded.folder,
                title=excluded.title,
                description=excluded.description,
                description_sha256=excluded.description_sha256,
                cover_path=excluded.cover_path,
                cover_sha256=excluded.cover_sha256,
                zip_path=excluded.zip_path,
                zip_sha256_head=excluded.zip_sha256_head,
                video_path=excluded.video_path,
                video_filename=excluded.video_filename,
                publish_category=excluded.publish_category,
                shipinhao_collection=excluded.shipinhao_collection,
                tags_json=excluded.tags_json,
                record_json=excluded.record_json,
                updated_at=excluded.updated_at
            """,
            (
                record.get("metadata_path"),
                record.get("metadata_sha256"),
                record.get("mtime"),
                record.get("folder"),
                record.get("title"),
                record.get("description"),
                record.get("description_sha256"),
                record.get("cover_path"),
                record.get("cover_sha256"),
                record.get("zip_path"),
                record.get("zip_sha256_head"),
                record.get("video_path"),
                record.get("video_filename"),
                record.get("publish_category"),
                record.get("shipinhao_collection"),
                json_dumps(record.get("tags") or []),
                json_dumps(record),
                now,
            ),
        )
        count += 1
    conn.commit()
    return count


def upsert_publish_history(conn: sqlite3.Connection, jobs: list[dict[str, Any]]) -> int:
    count = 0
    now = now_iso()
    for job in jobs:
        if not isinstance(job, dict) or job.get("id") is None:
            continue
        conn.execute(
            """
            INSERT INTO lazyedit_publish_jobs (
                job_id, video_id, status, platforms_json, config_json, detail,
                zip_path, metadata_path, cover_path, video_path, remote_job_id,
                remote_filename, remote_status, error, created_at, updated_at,
                started_at, finished_at, publication_session_id, video_title,
                video_file_path, job_json, imported_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                video_id=excluded.video_id,
                status=excluded.status,
                platforms_json=excluded.platforms_json,
                config_json=excluded.config_json,
                detail=excluded.detail,
                zip_path=excluded.zip_path,
                metadata_path=excluded.metadata_path,
                cover_path=excluded.cover_path,
                video_path=excluded.video_path,
                remote_job_id=excluded.remote_job_id,
                remote_filename=excluded.remote_filename,
                remote_status=excluded.remote_status,
                error=excluded.error,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                started_at=excluded.started_at,
                finished_at=excluded.finished_at,
                publication_session_id=excluded.publication_session_id,
                video_title=excluded.video_title,
                video_file_path=excluded.video_file_path,
                job_json=excluded.job_json,
                imported_at=excluded.imported_at
            """,
            (
                job.get("id"),
                job.get("video_id"),
                job.get("status"),
                json_dumps(job.get("platforms") or {}),
                json_dumps(job.get("config") or {}),
                job.get("detail"),
                job.get("zip_path"),
                job.get("metadata_path"),
                job.get("cover_path"),
                job.get("video_path"),
                job.get("remote_job_id"),
                job.get("remote_filename"),
                job.get("remote_status"),
                job.get("error"),
                job.get("created_at"),
                job.get("updated_at"),
                job.get("started_at"),
                job.get("finished_at"),
                job.get("publication_session_id"),
                job.get("video_title"),
                job.get("video_file_path"),
                json_dumps(job),
                now,
            ),
        )
        count += 1
    conn.commit()
    return count


def plan_rows_from_db(conn: sqlite3.Connection, *, repair_mismatched: bool = False) -> list[dict[str, Any]]:
    rows = [json_loads(row["row_json"], {}) for row in conn.execute("SELECT row_json FROM shipinhao_rows")]
    records = [json_loads(row["record_json"], {}) for row in conn.execute("SELECT record_json FROM lazyedit_metadata")]
    return build_description_plan(rows, records, repair_mismatched=repair_mismatched, include_ok=True)


def save_plan_matches(conn: sqlite3.Connection, plan: list[dict[str, Any]]) -> int:
    conn.execute("DELETE FROM shipinhao_matches")
    now = now_iso()
    count = 0
    for item in plan:
        metadata_path = item.get("metadata_path")
        row = item.get("row") if isinstance(item.get("row"), dict) else {}
        key = row.get("row_key") or row_key(row)
        if not metadata_path or not key:
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO shipinhao_matches (
                row_key, metadata_path, score, action, reason, plan_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                metadata_path,
                int(item.get("match_score") or 0),
                item.get("action"),
                item.get("reason"),
                json_dumps(item),
                now,
            ),
        )
        count += 1
    conn.commit()
    return count


def db_report(path: str | Path, *, limit: int = 20) -> dict[str, Any]:
    conn = init_db(path)
    try:
        summary = {
            "rows": conn.execute("SELECT COUNT(*) FROM shipinhao_rows").fetchone()[0],
            "metadata_records": conn.execute("SELECT COUNT(*) FROM lazyedit_metadata").fetchone()[0],
            "publish_jobs": conn.execute("SELECT COUNT(*) FROM lazyedit_publish_jobs").fetchone()[0],
            "matches": conn.execute("SELECT COUNT(*) FROM shipinhao_matches").fetchone()[0],
            "planned_updates": conn.execute("SELECT COUNT(*) FROM shipinhao_matches WHERE action='update-description'").fetchone()[0],
        }
        missing = []
        for row in conn.execute(
            """
            SELECT r.row_key, r.published_at, r.visible_description, r.title,
                   m.score, m.reason, m.metadata_path, m.plan_json
            FROM shipinhao_matches m
            JOIN shipinhao_rows r ON r.row_key = m.row_key
            WHERE m.action = 'update-description'
            ORDER BY r.published_at DESC
            LIMIT ?
            """,
            (limit,),
        ):
            plan = json_loads(row["plan_json"], {})
            missing.append({
                "row_key": row["row_key"],
                "published_at": row["published_at"],
                "current_description": row["visible_description"],
                "metadata_title": plan.get("metadata_title"),
                "metadata_path": row["metadata_path"],
                "score": row["score"],
                "reason": row["reason"],
                "new_length": plan.get("new_length"),
            })
        return {"summary": summary, "planned_updates": missing}
    finally:
        conn.close()


def record_apply_attempt(
    conn: sqlite3.Connection | None,
    *,
    item: dict[str, Any],
    result: dict[str, Any],
    action: str = "update-description",
) -> None:
    if conn is None:
        return
    row = item.get("row") if isinstance(item.get("row"), dict) else {}
    key = item.get("row_key") or row.get("row_key") or row_key(row)
    conn.execute(
        """
        INSERT INTO shipinhao_apply_attempts (
            row_key, metadata_path, action, ok, stage, reason, result_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            key,
            item.get("metadata_path"),
            action,
            1 if result.get("ok") else 0,
            result.get("stage"),
            result.get("reason") or result.get("error"),
            json_dumps(result),
            now_iso(),
        ),
    )
    conn.commit()


def run_mirror(args: argparse.Namespace) -> int:
    from manage_shipinhao_videos import connect_driver, inventory

    driver = connect_driver(args.port, args.chromedriver)
    rows = inventory(driver, url=args.url if args.url else None, scrolls=args.scrolls, pause=args.pause)
    now = datetime.now().isoformat(timespec="seconds")
    for idx, row in enumerate(rows, start=1):
        text = "\n".join(str(row.get(key) or "") for key in ("title", "text"))
        row["mirror_index"] = idx
        row["row_key"] = row_key(row)
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
    record_conn = init_db(args.db) if args.db else None
    if args.url:
        driver.get(args.url)
        time.sleep(5)
    results = []
    for item in targets:
        query = normalize_text(item.get("query"))
        description = normalize_text(item.get("new_description"))
        if not query or not description:
            result = {"ok": False, "reason": "missing-query-or-description", "item": item}
            results.append(result)
            record_apply_attempt(record_conn, item=item, result=result)
            continue
        if not args.apply:
            result = {"ok": True, "dry_run": True, "query": query, "new_length": len(description)}
            results.append(result)
            record_apply_attempt(record_conn, item=item, result=result)
            continue
        open_state = open_edit_row(driver, query, pause=args.pause)
        if not isinstance(open_state, dict) or not open_state.get("ok"):
            result = {"ok": False, "stage": "open-edit", "query": query, "state": open_state}
            results.append(result)
            record_apply_attempt(record_conn, item=item, result=result)
            continue
        dialog_state = open_state.get("dialog_state") if isinstance(open_state.get("dialog_state"), dict) else {}
        if dialog_state.get("isCoverEdit") and not dialog_state.get("hasEditor"):
            result = {
                "ok": False,
                "stage": "unsupported-description-repair",
                "query": query,
                "reason": "Shipinhao coverEdit only supports modifying selected existing text, limited to 20 characters; blank/missing descriptions cannot be restored through the visible UI.",
                "current_description_text": dialog_state.get("descriptionText", ""),
                "new_length": len(description),
                "metadata_path": item.get("metadata_path"),
            }
            results.append(result)
            record_apply_attempt(record_conn, item=item, result=result)
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
            result = {"ok": False, "stage": "fill-description", "query": query, "error": str(exc)}
            results.append(result)
            record_apply_attempt(record_conn, item=item, result=result)
            continue
        save_state = None
        for _ in range(20):
            save_state = driver.execute_script(SAVE_EDIT_JS)
            if isinstance(save_state, dict) and save_state.get("ok"):
                break
            time.sleep(1)
        result = {
            "ok": bool(isinstance(save_state, dict) and save_state.get("ok")),
            "query": query,
            "filled_length": len(value or ""),
            "save_state": save_state,
            "metadata_path": item.get("metadata_path"),
        }
        results.append(result)
        record_apply_attempt(record_conn, item=item, result=result)
        time.sleep(max(args.pause, 2.0))
    if record_conn is not None:
        record_conn.close()
    write_json(args.output, results)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mirror and manage Shipinhao videos without coupling to publication.")
    sub = parser.add_subparsers(dest="command", required=True)

    meta = sub.add_parser("export-metadata", help="Export LazyEdit publish metadata into a portable index.")
    meta.add_argument("--metadata-root", default=os.environ.get("LAZYEDIT_DATA_ROOT", "/home/lachlan/DiskMech/Projects/lazyedit/DATA"))
    meta.add_argument("--days", type=int, default=90)
    meta.add_argument("--output")

    history = sub.add_parser("export-publish-history", help="Export LazyEdit publish job history from the local Postgres DB.")
    history.add_argument("--limit", type=int, default=500)
    history.add_argument("--all-platforms", action="store_true", help="Do not filter to Shipinhao jobs.")
    history.add_argument("--output")

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
    apply.add_argument("--db", help="Optional mirror SQLite DB for recording apply attempts.")
    apply.add_argument("--output")

    sync = sub.add_parser("sync-db", help="Sync mirror rows, LazyEdit metadata, and optional publish history into a SQLite management DB.")
    sync.add_argument("--db", required=True)
    sync.add_argument("--mirror")
    sync.add_argument("--metadata-index")
    sync.add_argument("--publish-history")
    sync.add_argument("--repair-mismatched", action="store_true")
    sync.add_argument("--output-plan", help="Optional JSON path for the generated description plan.")

    report = sub.add_parser("db-report", help="Summarize the mirrored management DB.")
    report.add_argument("--db", required=True)
    report.add_argument("--limit", type=int, default=20)
    report.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "export-metadata":
        write_json(args.output, export_metadata(args.metadata_root, days=args.days))
        return 0
    if args.command == "export-publish-history":
        write_json(
            args.output,
            export_publish_history(limit=args.limit, only_shipinhao=not args.all_platforms),
        )
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
    if args.command == "sync-db":
        conn = init_db(args.db)
        try:
            result: dict[str, Any] = {"db": str(Path(args.db).expanduser())}
            if args.mirror:
                rows = read_json(args.mirror)
                if not isinstance(rows, list):
                    raise ValueError("--mirror must be a JSON list")
                result["rows"] = upsert_mirror_rows(conn, rows)
            if args.metadata_index:
                records = read_json(args.metadata_index)
                if not isinstance(records, list):
                    raise ValueError("--metadata-index must be a JSON list")
                result["metadata_records"] = upsert_metadata_records(conn, records)
            if args.publish_history:
                jobs = read_json(args.publish_history)
                if not isinstance(jobs, list):
                    raise ValueError("--publish-history must be a JSON list")
                result["publish_jobs"] = upsert_publish_history(conn, jobs)
            plan = plan_rows_from_db(conn, repair_mismatched=args.repair_mismatched)
            result["matches"] = save_plan_matches(conn, plan)
            result["planned_updates"] = sum(1 for item in plan if item.get("action") == "update-description")
            if args.output_plan:
                write_json(args.output_plan, plan)
            write_json(None, result)
        finally:
            conn.close()
        return 0
    if args.command == "db-report":
        write_json(args.output, db_report(args.db, limit=args.limit))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
