"""Publication routing helpers for AutoPublish."""

from __future__ import annotations

import os
import re
from typing import Any


CATEGORY_SIMPLELIFE = "simplelife"
CATEGORY_LALACHAN = "lalachan"
CATEGORY_MUSIC = "music"

_ALIASES = {
    "simple": CATEGORY_SIMPLELIFE,
    "simplelife": CATEGORY_SIMPLELIFE,
    "simple life": CATEGORY_SIMPLELIFE,
    "简单生活": CATEGORY_SIMPLELIFE,
    "lalachan": CATEGORY_LALACHAN,
    "lala": CATEGORY_LALACHAN,
    "lala chan": CATEGORY_LALACHAN,
    "lala-chan": CATEGORY_LALACHAN,
    "啦啦侠": CATEGORY_LALACHAN,
    "music": CATEGORY_MUSIC,
    "musica": CATEGORY_MUSIC,
    "musia": CATEGORY_MUSIC,
    "慕莎": CATEGORY_MUSIC,
    "音乐": CATEGORY_MUSIC,
    "歌曲": CATEGORY_MUSIC,
}


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def normalize_publish_category(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lowered = re.sub(r"[-_]+", " ", text.lower())
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return _ALIASES.get(text) or _ALIASES.get(lowered)


def category_names(category: str) -> dict[str, str]:
    normalized = normalize_publish_category(category) or CATEGORY_SIMPLELIFE
    if normalized == CATEGORY_LALACHAN:
        return {
            "youtube_playlist": _env("AUTOPUB_YOUTUBE_PLAYLIST_LALACHAN", "LALACHAN"),
            "shipinhao_collection": _env("AUTOPUB_SHIPINHAO_COLLECTION_LALACHAN", "啦啦侠"),
        }
    if normalized == CATEGORY_MUSIC:
        return {
            "youtube_playlist": _env("AUTOPUB_YOUTUBE_PLAYLIST_MUSIC", "Musia"),
            "shipinhao_collection": _env("AUTOPUB_SHIPINHAO_COLLECTION_MUSIC", "Musia"),
        }
    return {
        "youtube_playlist": _env("AUTOPUB_YOUTUBE_PLAYLIST_SIMPLELIFE", "SimpleLife"),
        "shipinhao_collection": _env("AUTOPUB_SHIPINHAO_COLLECTION_SIMPLELIFE", "简单生活"),
    }


def infer_publish_category(metadata: dict | None, *, media_kind: str = "video") -> tuple[str, str]:
    metadata = metadata or {}
    for key in (
        "publish_category",
        "publishCategory",
        "content_category",
        "contentCategory",
        "series",
        "project",
    ):
        category = normalize_publish_category(metadata.get(key))
        if category:
            return category, f"metadata.{key}"

    if normalize_publish_category(media_kind) == CATEGORY_MUSIC:
        return CATEGORY_MUSIC, "media_kind"

    text = "\n".join(
        str(metadata.get(key) or "")
        for key in (
            "source_video_path",
            "source_path",
            "source_repo",
            "prompt_file",
            "title",
            "brief_description",
            "middle_description",
            "long_description",
        )
    ).lower()
    if "/lalachan/" in text or "projectslfs/lalachan" in text:
        return CATEGORY_LALACHAN, "source_path"
    if any(token in text for token in (
        "lalachan",
        "lala xia",
        "lala chan",
        "啦啦侠",
        "啦啦俠",
        "阿芽酱",
        "阿芽醬",
        "飒飒君",
        "颯颯君",
        "莎莎君",
        "拉拉夏",
        "莊子機器人",
        "庄子机器人",
        "小云雀",
        "xiaoyunque",
        "seedance",
        "duanpian",
    )):
        return CATEGORY_LALACHAN, "story_keywords"
    return CATEGORY_SIMPLELIFE, "default"


def resolve_youtube_playlist(metadata: dict | None, *, media_kind: str = "video") -> str:
    metadata = metadata or {}
    explicit = metadata.get("playlist_name") or metadata.get("youtube_playlist")
    if explicit:
        return str(explicit).strip()
    category, _reason = infer_publish_category(metadata, media_kind=media_kind)
    return category_names(category)["youtube_playlist"]


def resolve_shipinhao_collection(metadata: dict | None, *, media_kind: str = "video") -> str:
    metadata = metadata or {}
    explicit = metadata.get("shipinhao_collection") or metadata.get("shipinhao_album")
    if explicit:
        return str(explicit).strip()
    category, _reason = infer_publish_category(metadata, media_kind=media_kind)
    return category_names(category)["shipinhao_collection"]
