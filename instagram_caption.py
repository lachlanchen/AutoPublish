"""Build bounded multilingual captions without dropping trailing languages."""


def _text(value):
    return value.strip() if isinstance(value, str) else ""


def _block(meta):
    if not isinstance(meta, dict):
        return ""
    description = next((_text(meta.get(key)) for key in (
        "middle_description", "brief_description", "long_description"
    ) if _text(meta.get(key))), "")
    raw_tags = meta.get("tags")
    tags = raw_tags if isinstance(raw_tags, list) else []
    tags = list(dict.fromkeys(_text(tag).lstrip("#") for tag in tags if _text(tag)))
    return "\n\n".join(part for part in (
        _text(meta.get("title")), description, " ".join(f"#{tag}" for tag in tags if tag)
    ) if part)


def build_instagram_caption(metadata, limit=2200):
    """Prefer Japanese, English, Chinese; legacy packages may omit either version."""
    if not isinstance(metadata, dict) or limit <= 0:
        return ""
    blocks = []
    for version in (metadata.get("japanese_version"), metadata.get("english_version"), metadata):
        block = _block(version)
        # Keep the publisher's existing BMP-compatible input policy.
        block = "".join(char for char in block if ord(char) <= 0xFFFF)
        if block and block not in blocks:
            blocks.append(block)
    if not blocks:
        return ""
    available = max(0, limit - 2 * (len(blocks) - 1))
    budgets = [0] * len(blocks)
    pending = list(range(len(blocks)))
    while pending and available:
        share = max(1, available // len(pending))
        for index in pending[:]:
            grant = min(share, len(blocks[index]) - budgets[index], available)
            budgets[index] += grant
            available -= grant
            if budgets[index] == len(blocks[index]):
                pending.remove(index)
            if not available:
                break
    clipped = [block if len(block) <= budget else block[:max(0, budget - 1)].rstrip() + "…"
               for block, budget in zip(blocks, budgets) if budget]
    return "\n\n".join(clipped)[:limit]
