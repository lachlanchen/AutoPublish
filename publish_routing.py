"""Publication routing helpers for AutoPublish."""

from __future__ import annotations

import os
import re
from typing import Any


CATEGORY_SIMPLELIFE = "simplelife"
CATEGORY_LAZYINGART = "lazyingart"
CATEGORY_LALACHAN = "lalachan"
CATEGORY_LALAMV = "lalamv"
CATEGORY_MUSIA = "musia"
CATEGORY_MUSIC = CATEGORY_MUSIA

_ALIASES = {
    "simple": CATEGORY_SIMPLELIFE,
    "simplelife": CATEGORY_SIMPLELIFE,
    "simple life": CATEGORY_SIMPLELIFE,
    "简单生活": CATEGORY_SIMPLELIFE,
    "lazyingart": CATEGORY_LAZYINGART,
    "lazying art": CATEGORY_LAZYINGART,
    "lazying-art": CATEGORY_LAZYINGART,
    "懒人艺术": CATEGORY_LAZYINGART,
    "懶人藝術": CATEGORY_LAZYINGART,
    "lalachan": CATEGORY_LALACHAN,
    "lala": CATEGORY_LALACHAN,
    "lala chan": CATEGORY_LALACHAN,
    "lala-chan": CATEGORY_LALACHAN,
    "啦啦侠": CATEGORY_LALACHAN,
    "lalamv": CATEGORY_LALAMV,
    "lala mv": CATEGORY_LALAMV,
    "lala-mv": CATEGORY_LALAMV,
    "lala_mv": CATEGORY_LALAMV,
    "啦啦mv": CATEGORY_LALAMV,
    "啦啦MV": CATEGORY_LALAMV,
    "music": CATEGORY_MUSIA,
    "musica": CATEGORY_MUSIA,
    "musia": CATEGORY_MUSIA,
    "慕莎": CATEGORY_MUSIA,
    "音乐": CATEGORY_MUSIA,
    "歌曲": CATEGORY_MUSIA,
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
    if normalized == CATEGORY_LAZYINGART:
        return {
            "youtube_playlist": _env("AUTOPUB_YOUTUBE_PLAYLIST_LAZYINGART", "LazyingArt"),
            "shipinhao_collection": _env("AUTOPUB_SHIPINHAO_COLLECTION_LAZYINGART", "懒人艺术"),
        }
    if normalized == CATEGORY_LALACHAN:
        return {
            "youtube_playlist": _env("AUTOPUB_YOUTUBE_PLAYLIST_LALACHAN", "LALACHAN"),
            "shipinhao_collection": _env("AUTOPUB_SHIPINHAO_COLLECTION_LALACHAN", "啦啦侠"),
        }
    if normalized == CATEGORY_LALAMV:
        return {
            "youtube_playlist": _env("AUTOPUB_YOUTUBE_PLAYLIST_LALAMV", "LalaMV"),
            "shipinhao_collection": _env("AUTOPUB_SHIPINHAO_COLLECTION_LALAMV", "LalaMV"),
        }
    if normalized == CATEGORY_MUSIA:
        return {
            "youtube_playlist": _env("AUTOPUB_YOUTUBE_PLAYLIST_MUSIA", _env("AUTOPUB_YOUTUBE_PLAYLIST_MUSIC", "Musia")),
            "shipinhao_collection": _env("AUTOPUB_SHIPINHAO_COLLECTION_MUSIA", _env("AUTOPUB_SHIPINHAO_COLLECTION_MUSIC", "Musia")),
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

    if normalize_publish_category(media_kind) == CATEGORY_MUSIA:
        return CATEGORY_MUSIA, "media_kind"

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
    if any(token in text for token in (
        "hikari ame",
        "光の雨",
        "光雨",
        "music video",
        "full mv",
        " mv ",
        "musia mv",
        "song locked",
        "song-locked",
        "副歌",
        "高潮",
    )) and any(token in text for token in (
        "lalachan",
        "lala xia",
        "啦啦侠",
        "啦啦俠",
        "阿芽酱",
        "阿芽醬",
        "飒飒君",
        "颯颯君",
        "庄子机器人",
        "莊子機器人",
    )):
        return CATEGORY_LALAMV, "lalamv_keywords"

    if any(token in text for token in (
        "lazyingart",
        "lazying art",
        "懒人艺术",
        "懶人藝術",
        "buy.lazying.art",
        "lazying.art",
    )):
        return CATEGORY_LAZYINGART, "lazyingart_keywords"

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
