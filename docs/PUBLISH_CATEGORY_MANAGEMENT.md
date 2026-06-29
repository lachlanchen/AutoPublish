# Publish Category Management

AutoPublish routes videos/music into platform categories using metadata fields
from LazyEdit:

- `publish_category`
- `youtube_playlist` / `playlist_name`
- `shipinhao_collection`

Default routing:

| Content | YouTube | Shipinhao | Instagram |
| --- | --- | --- | --- |
| personal/self recordings | `SimpleLife` playlist | `简单生活` 合集 | no per-post category |
| LALACHAN/Xiaoyunque story videos | `LALACHAN` playlist | `啦啦侠` 合集 | no per-post category |
| Musia music/art tracks | `Musia` playlist | `Musia` music package | no per-post category |

Environment overrides:

```bash
AUTOPUB_YOUTUBE_PLAYLIST_SIMPLELIFE=SimpleLife
AUTOPUB_YOUTUBE_PLAYLIST_LALACHAN=LALACHAN
AUTOPUB_YOUTUBE_PLAYLIST_MUSIC=Musia
AUTOPUB_SHIPINHAO_COLLECTION_SIMPLELIFE=简单生活
AUTOPUB_SHIPINHAO_COLLECTION_LALACHAN=啦啦侠
AUTOPUB_SHIPINHAO_COLLECTION_MUSIC=Musia
```

LazyEdit metadata generation now asks the model to choose
`publish_category` as `simplelife`, `lalachan`, or `music`. The router still
falls back to source-path and keyword inference, but the metadata value is the
preferred forward signal.

## Instagram Category Status

As of 2026-06-29, Instagram does not expose a stable per-post category,
playlist, folder, or collection field in the desktop web upload flow used by
`pub_instagram.py`. Meta's publishing surface supports ordinary post/Reel
fields such as media, caption, cover/thumb offset, location, collaborators,
product/user tags, and feed sharing; the "category" label documented by
Instagram is account/profile-level professional information, not a per-post
routing target.

AutoPublish therefore keeps using the shared `publish_category` metadata for
YouTube and Shipinhao, but Instagram only receives the normal caption/tags.
`pub_instagram.py` logs the inferred category for traceability and explicitly
continues without selecting any Instagram category UI. There is no Instagram
backfill/apply script because there is no platform category to move posts into.

## Backfill YouTube

Inventory the logged-in YouTube Studio content page:

```bash
python scripts/manage_y2b_videos.py inventory --scrolls 80 --output /tmp/youtube_inventory.json
```

If the account needs a specific Studio content URL, set it explicitly:

```bash
YOUTUBE_STUDIO_CONTENT_URL="https://studio.youtube.com/..." \
python scripts/manage_y2b_videos.py inventory --scrolls 80 --output /tmp/youtube_inventory.json
```

If the correct content page is already open in the browser, keep the current
tab instead of navigating:

```bash
python scripts/manage_y2b_videos.py inventory --url "" --scrolls 80 --output /tmp/youtube_inventory.json
```

The manager uses a page-load timeout and Chrome DevTools navigation fallback
because YouTube Studio can keep network requests open indefinitely.

Dry-run LALACHAN moves:

```bash
python scripts/manage_y2b_videos.py move-lalachan --playlist LALACHAN --scrolls 80 --output /tmp/youtube_move_plan.json
```

Dry-run Musia moves:

```bash
python scripts/manage_y2b_videos.py move-music --playlist Musia --scrolls 80 --output /tmp/youtube_music_move_plan.json
```

Dry-run both categories from the same inventory:

```bash
python scripts/manage_y2b_videos.py move-classified --lalachan-playlist LALACHAN --music-playlist Musia --scrolls 80 --output /tmp/youtube_classified_move_plan.json
```

Apply only after reviewing the plan:

```bash
python scripts/manage_y2b_videos.py move-lalachan --playlist LALACHAN --scrolls 80 --apply
```

Get links:

```bash
python scripts/manage_y2b_videos.py link --query "title fragment" --scrolls 80
```

Delete one video, with a second title confirmation:

```bash
python scripts/manage_y2b_videos.py delete --video-id VIDEO_ID --title-contains "visible title fragment" --apply
```

## Backfill Shipinhao

Inventory the logged-in Shipinhao content page:

```bash
python scripts/manage_shipinhao_videos.py inventory --scrolls 80 --output /tmp/shipinhao_inventory.json
```

If the route changes, open the correct management page manually in the browser
on port 5006 and keep the current tab:

```bash
python scripts/manage_shipinhao_videos.py inventory --url "" --scrolls 80
```

Find links:

```bash
python scripts/manage_shipinhao_videos.py link --query "title fragment" --scrolls 80
```

Delete one row, with a second title confirmation:

```bash
python scripts/manage_shipinhao_videos.py delete --query "title fragment" --title-contains "title fragment" --apply
```

Existing-post Shipinhao collection editing is not as stable as upload-time
collection selection. Use the candidate report first:

```bash
python scripts/manage_shipinhao_videos.py ensure-collection --collection Musia --apply
python scripts/manage_shipinhao_videos.py ensure-collection --collection 啦啦侠 --apply
python scripts/manage_shipinhao_videos.py move-lalachan --lalachan-collection 啦啦侠 --scrolls 80 --output /tmp/shipinhao_lalachan_candidates.json
python scripts/manage_shipinhao_videos.py move-music --music-collection Musia --scrolls 80 --output /tmp/shipinhao_music_candidates.json
python scripts/manage_shipinhao_videos.py move-classified --lalachan-collection 啦啦侠 --music-collection Musia --scrolls 80 --output /tmp/shipinhao_classified_candidates.json
```

`ensure-collection` creates the missing collection name if the account does not
already show it. Then verify the account exposes collection editing before
doing any automated bulk move. Prefer small recent-page batches or exact
title-fragment moves:

```bash
python scripts/manage_shipinhao_videos.py move --query "visible title fragment" --collection 啦啦侠 --apply
```

## Shipinhao Mirror Management

For stronger existing-post control that is independent from publication, use:

```bash
python scripts/shipinhao_mirror_manager.py mirror --scrolls 5 --output /tmp/shipinhao_mirror.json
python scripts/shipinhao_mirror_manager.py export-metadata --metadata-root /home/lachlan/DiskMech/Projects/lazyedit/DATA --days 45 --output /tmp/lazyedit_shipinhao_metadata_index.json
python scripts/shipinhao_mirror_manager.py plan-descriptions --mirror /tmp/shipinhao_mirror.json --metadata-index /tmp/lazyedit_shipinhao_metadata_index.json --include-ok --output /tmp/shipinhao_description_plan.json
```

See `docs/SHIPINHAO_MIRROR_MANAGEMENT.md` for the full workflow and the
2026-06-29 finding: old rows with completely missing descriptions can be
matched to LazyEdit metadata, but Shipinhao's current `coverEdit` page only
supports modifying selected existing text with a 20-character limit. Blank
descriptions cannot be restored through the visible desktop UI; the tool now
reports that state cleanly instead of timing out.
