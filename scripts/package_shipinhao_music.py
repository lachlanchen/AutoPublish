#!/usr/bin/env python3
"""Package a pure Shipinhao music upload ZIP for AutoPublish.

The output is accepted by AutoPublish with:

    /publish?publish_shipinhao_music=true&filename=<zipname>

It is intentionally repo-agnostic so Musia, LALACHAN, or a Codex handoff can
call it with explicit audio/lyrics/artwork paths.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zipfile


DEFAULT_AUTOPUBLISH_URL = "http://lazyingart:8081/publish"


def read_text(path: Path | None) -> str:
    if not path:
        return ""
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def format_lrc_timestamp(seconds: object) -> str | None:
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return None
    if value < 0:
        value = 0.0
    minutes = int(value // 60)
    remainder = value - minutes * 60
    return f"{minutes:02d}:{remainder:05.2f}"


def strip_lrc_timestamps(text: str) -> str:
    import re

    output: list[str] = []
    for line in (text or "").splitlines():
        stripped = re.sub(r"^\s*(?:\[[0-9]{1,3}:[0-9]{2}(?:\.[0-9]{1,3})?\])+\s*", "", line).strip()
        if stripped:
            output.append(stripped)
    return "\n".join(output)


def lyrics_from_json(path: Path | None, *, lyrics_format: str = "auto") -> str:
    if not path:
        return ""
    if lyrics_format not in {"auto", "plain", "lrc"}:
        raise ValueError("lyrics_format must be auto, plain, or lrc")
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines = payload.get("lines") if isinstance(payload, dict) else None
    if not isinstance(lines, list):
        return ""
    use_lrc = lyrics_format == "lrc" or (
        lyrics_format == "auto"
        and any(isinstance(line, dict) and line.get("start") is not None for line in lines)
    )
    output: list[str] = []
    for line in lines:
        if not isinstance(line, dict):
            continue
        text = str(line.get("singableText") or line.get("text") or "").strip()
        if not text:
            continue
        if use_lrc:
            timestamp = format_lrc_timestamp(line.get("start"))
            if timestamp:
                output.append(f"[{timestamp}]{text}")
                continue
        output.append(text)
    return "\n".join(output)


def safe_arcname(path: Path) -> str:
    return path.name.replace("/", "_").replace("\\", "_")


def build_metadata(args: argparse.Namespace, *, audio_name: str, cover_names: list[str], lyrics: str) -> dict:
    title = args.title or args.song_title or Path(audio_name).stem
    story = args.story or args.description or ""
    metadata = {
        "music_filename": audio_name,
        "audio_filename": audio_name,
        "cover_filename": cover_names[0] if cover_names else None,
        "background_image_filenames": cover_names,
        "title": title,
        "song_title": args.song_title or title,
        "lyrics": lyrics,
        "song_lyrics": lyrics,
        "lrc_lyrics": lyrics if lyrics.lstrip().startswith("[") else "",
        "timed_lyrics": lyrics if lyrics.lstrip().startswith("[") else "",
        "plain_lyrics": strip_lrc_timestamps(lyrics),
        "readable_lyrics": strip_lrc_timestamps(lyrics),
        "music_story": story,
        "brief_description": args.description or story,
        "middle_description": story or args.description or "",
        "long_description": args.description or story,
        "author": args.author,
        "artist": args.artist or args.author,
        "language": args.language,
        "genre": args.genre,
        "declare_original": bool(args.declare_original),
    }
    if args.metadata_json:
        override = json.loads(Path(args.metadata_json).read_text(encoding="utf-8"))
        if isinstance(override, dict):
            metadata.update({k: v for k, v in override.items() if v is not None})
    return metadata


def post_zip(zip_path: Path, url: str, *, test: bool) -> dict:
    params = {
        "filename": zip_path.name,
        "publish_shipinhao_music": "true",
        "test": "true" if test else "false",
    }
    endpoint = f"{url}?{urlencode(params)}"
    request = Request(
        endpoint,
        data=zip_path.read_bytes(),
        method="POST",
        headers={"Content-Type": "application/octet-stream"},
    )
    with urlopen(request, timeout=120) as response:
        raw = response.read().decode("utf-8", errors="replace")
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"raw": raw}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package a Shipinhao music upload ZIP.")
    parser.add_argument("--audio", required=True, help="MP3/WAV audio file.")
    parser.add_argument("--cover", action="append", default=[], help="Artwork/background image. Can be passed multiple times.")
    parser.add_argument("--lyrics-file", help="Plain text lyrics file.")
    parser.add_argument("--lyrics-json", help="Musia lyric JSON with a lines[] array.")
    parser.add_argument(
        "--lyrics-format",
        choices=("auto", "plain", "lrc"),
        default="auto",
        help="How to convert --lyrics-json. auto/lrc emits timed LRC when line starts are present.",
    )
    parser.add_argument("--metadata-json", help="Optional JSON metadata override.")
    parser.add_argument("--title", help="Song title.")
    parser.add_argument("--song-title", help="Explicit Shipinhao song title.")
    parser.add_argument("--author", default="Musia 慕莎", help="Author/artist display name.")
    parser.add_argument("--artist", help="Artist name; defaults to --author.")
    parser.add_argument("--language", default="中文", help="Shipinhao song language label.")
    parser.add_argument("--genre", default="", help="Optional Shipinhao song genre.")
    parser.add_argument("--story", default="", help="Short 音乐人说 text.")
    parser.add_argument("--description", default="", help="Description/metadata text.")
    parser.add_argument("--declare-original", action="store_true", help="Request original declaration if the UI supports it.")
    parser.add_argument("--output", help="Output zip path.")
    parser.add_argument("--post", action="store_true", help="Post the ZIP to AutoPublish after packaging.")
    parser.add_argument("--autopublish-url", default=DEFAULT_AUTOPUBLISH_URL)
    parser.add_argument("--test", action="store_true", help="Pass test=true to AutoPublish.")
    args = parser.parse_args(argv)

    audio_path = Path(args.audio).expanduser().resolve()
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)
    cover_paths = [Path(path).expanduser().resolve() for path in args.cover]
    missing_covers = [path for path in cover_paths if not path.exists()]
    if missing_covers:
        raise FileNotFoundError(missing_covers[0])

    lyrics = read_text(Path(args.lyrics_file).expanduser().resolve() if args.lyrics_file else None)
    if not lyrics:
        lyrics = lyrics_from_json(
            Path(args.lyrics_json).expanduser().resolve() if args.lyrics_json else None,
            lyrics_format=args.lyrics_format,
        )
    if not lyrics:
        print("WARNING: no lyrics provided; the Shipinhao lyrics field may stay empty.", file=sys.stderr)

    output_path = Path(args.output).expanduser().resolve() if args.output else Path.cwd() / f"{audio_path.stem}_shipinhao_music.zip"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stem = output_path.stem

    audio_name = safe_arcname(audio_path)
    cover_names = [safe_arcname(path) for path in cover_paths]
    metadata = build_metadata(args, audio_name=audio_name, cover_names=cover_names, lyrics=lyrics)
    metadata_name = f"{stem}_metadata.json"

    metadata_path = output_path.parent / metadata_name
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    with zipfile.ZipFile(output_path, "w") as zipf:
        zipf.write(audio_path, arcname=audio_name)
        for cover_path, cover_name in zip(cover_paths, cover_names):
            zipf.write(cover_path, arcname=cover_name)
        zipf.write(metadata_path, arcname=metadata_name)

    print(json.dumps({
        "zip_path": str(output_path),
        "metadata_path": str(metadata_path),
        "audio": str(audio_path),
        "covers": [str(path) for path in cover_paths],
        "lyrics_lines": len([line for line in lyrics.splitlines() if line.strip()]),
        "metadata": metadata,
    }, ensure_ascii=False, indent=2))

    if args.post:
        response = post_zip(output_path, args.autopublish_url, test=args.test)
        print(json.dumps({"autopublish_response": response}, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
