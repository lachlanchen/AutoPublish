# Publish Category Management

AutoPublish routes each LazyEdit package through a shared `publish_category`
contract. The category is platform-independent; YouTube receives a playlist,
Shipinhao receives a collection, and Instagram logs the category while using
normal captions/tags because its desktop upload flow has no per-post category.

## Categories

| Category | Use For | YouTube | Shipinhao |
| --- | --- | --- | --- |
| `simplelife` | personal/self recordings, real-world daily videos | `SimpleLife` | `简单生活` |
| `lazyingart` | LazyingArt brand, product, shop, portfolio posts | `LazyingArt` | `懒人艺术` |
| `musia` | pure Musia songs, audio/art-track uploads | `Musia` | `Musia` |
| `lalachan` | LALACHAN story videos that are not primarily MVs | `LALACHAN` | `啦啦侠` |
| `lalamv` | LALACHAN character music videos and song-led MVs | `LalaMV` | `LalaMV` |

`music` is accepted only as a backwards-compatible alias for `musia`.

## Forward Routing

LazyEdit should include these fields in video/music publish ZIP metadata:

- `publish_category`
- `youtube_playlist` or `playlist_name`
- `shipinhao_collection`

The router also accepts environment overrides:

```bash
AUTOPUB_YOUTUBE_PLAYLIST_SIMPLELIFE=SimpleLife
AUTOPUB_YOUTUBE_PLAYLIST_LAZYINGART=LazyingArt
AUTOPUB_YOUTUBE_PLAYLIST_MUSIA=Musia
AUTOPUB_YOUTUBE_PLAYLIST_LALACHAN=LALACHAN
AUTOPUB_YOUTUBE_PLAYLIST_LALAMV=LalaMV

AUTOPUB_SHIPINHAO_COLLECTION_SIMPLELIFE=简单生活
AUTOPUB_SHIPINHAO_COLLECTION_LAZYINGART=懒人艺术
AUTOPUB_SHIPINHAO_COLLECTION_MUSIA=Musia
AUTOPUB_SHIPINHAO_COLLECTION_LALACHAN=啦啦侠
AUTOPUB_SHIPINHAO_COLLECTION_LALAMV=LalaMV
```

For a LALACHAN MV, prefer explicit metadata or CLI overrides:

```bash
python scripts/lazyedit_publish.py \
  --video-id VIDEO_ID \
  --use-current-settings \
  --publish-category lalamv \
  --youtube-playlist LalaMV \
  --shipinhao-collection LalaMV \
  --platforms shipinhao,youtube,instagram \
  --wait
```

YouTube upload-time routing can create the missing playlist from the upload
dialog when YouTube exposes the create control. Shipinhao collection creation is
handled by the management helper below.

## Validate Routing

Run this on the AutoPublish host before a real publish if category behavior is
in doubt:

```bash
/home/lachlan/venvs/autopub/bin/python - <<'PY'
from publish_routing import category_names, infer_publish_category, resolve_shipinhao_collection, resolve_youtube_playlist

expected = {
    "simplelife": ("SimpleLife", "简单生活"),
    "lazyingart": ("LazyingArt", "懒人艺术"),
    "musia": ("Musia", "Musia"),
    "lalachan": ("LALACHAN", "啦啦侠"),
    "lalamv": ("LalaMV", "LalaMV"),
}
for category, names in expected.items():
    actual = category_names(category)
    assert (actual["youtube_playlist"], actual["shipinhao_collection"]) == names, actual

metadata = {"publish_category": "lalamv", "title": "Aya Chan Hikari Ame"}
assert infer_publish_category(metadata)[0] == "lalamv"
assert resolve_youtube_playlist(metadata) == "LalaMV"
assert resolve_shipinhao_collection(metadata) == "LalaMV"
print("category routing ok")
PY
```

## YouTube Backfill

All helpers are dry-run by default. Add `--apply` only after inspecting the JSON
plan.

```bash
python scripts/manage_y2b_videos.py inventory --scrolls 80 --output /tmp/youtube_inventory.json

python scripts/manage_y2b_videos.py move-category \
  --category lalamv \
  --lalamv-playlist LalaMV \
  --scrolls 80 \
  --output /tmp/youtube_lalamv_plan.json

python scripts/manage_y2b_videos.py move-classified \
  --lazyingart-playlist LazyingArt \
  --musia-playlist Musia \
  --lalachan-playlist LALACHAN \
  --lalamv-playlist LalaMV \
  --scrolls 80 \
  --output /tmp/youtube_category_plan.json
```

Move one known video:

```bash
python scripts/manage_y2b_videos.py move \
  --video-id VIDEO_ID \
  --playlist LalaMV \
  --apply
```

`move-classified` skips `simplelife` unless `--include-simplelife` is supplied,
to avoid bulk-moving normal personal videos accidentally.

## Shipinhao Backfill

Create or confirm collections first:

```bash
python scripts/manage_shipinhao_videos.py ensure-collection --collection LalaMV --apply
python scripts/manage_shipinhao_videos.py ensure-collection --collection 啦啦侠 --apply
python scripts/manage_shipinhao_videos.py ensure-collection --collection Musia --apply
```

Dry-run LalaMV moves:

```bash
python scripts/manage_shipinhao_videos.py move-category \
  --category lalamv \
  --lalamv-collection LalaMV \
  --scrolls 80 \
  --output /tmp/shipinhao_lalamv_plan.json
```

Dry-run all non-`simplelife` categories:

```bash
python scripts/manage_shipinhao_videos.py move-classified \
  --lazyingart-collection 懒人艺术 \
  --musia-collection Musia \
  --lalachan-collection 啦啦侠 \
  --lalamv-collection LalaMV \
  --scrolls 80 \
  --output /tmp/shipinhao_category_plan.json
```

Move one known row:

```bash
python scripts/manage_shipinhao_videos.py move \
  --query "visible title fragment" \
  --collection LalaMV \
  --apply
```

Existing-post Shipinhao edits are more UI-dependent than upload-time collection
selection. Prefer exact title fragments and small batches.

## Instagram

Instagram has no comparable playlist/collection/category target in the current
desktop web upload flow. Do not run an Instagram category backfill. Keep using
`publish_category` for metadata traceability and normal Instagram captions/tags.
