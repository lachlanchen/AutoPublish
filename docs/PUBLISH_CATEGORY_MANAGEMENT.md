# Publish Category Management

AutoPublish routes videos/music into platform categories using metadata fields
from LazyEdit:

- `publish_category`
- `youtube_playlist` / `playlist_name`
- `shipinhao_collection`

Default routing:

| Content | YouTube | Shipinhao |
| --- | --- | --- |
| personal/self recordings | `SimpleLife` playlist | `简单生活` 合集 |
| LALACHAN/Xiaoyunque story videos | `LALACHAN` playlist | `LALACHAN` 合集 |
| Musia music/art tracks | `Musia` playlist | `Musia` music package |

Environment overrides:

```bash
AUTOPUB_YOUTUBE_PLAYLIST_SIMPLELIFE=SimpleLife
AUTOPUB_YOUTUBE_PLAYLIST_LALACHAN=LALACHAN
AUTOPUB_YOUTUBE_PLAYLIST_MUSIC=Musia
AUTOPUB_SHIPINHAO_COLLECTION_SIMPLELIFE=简单生活
AUTOPUB_SHIPINHAO_COLLECTION_LALACHAN=LALACHAN
AUTOPUB_SHIPINHAO_COLLECTION_MUSIC=Musia
```

## Backfill YouTube

Inventory the logged-in YouTube Studio content page:

```bash
python scripts/manage_y2b_videos.py inventory --scrolls 80 --output /tmp/youtube_inventory.json
```

Dry-run LALACHAN moves:

```bash
python scripts/manage_y2b_videos.py move-lalachan --playlist LALACHAN --scrolls 80 --output /tmp/youtube_move_plan.json
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
python scripts/manage_shipinhao_videos.py move-lalachan --collection LALACHAN --scrolls 80 --output /tmp/shipinhao_lalachan_candidates.json
```

Then verify the account exposes collection editing before doing any manual or
future automated bulk move.
