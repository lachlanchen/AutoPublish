# Shipinhao Mirror Management

Date: 2026-06-29

This is a management workflow, not a publication workflow. It attaches to the
logged-in Shipinhao browser on the Raspberry Pi and mirrors existing platform
rows so AutoPublish can reason about posts after they have already been
published.

The implementation lives in:

- `scripts/manage_shipinhao_videos.py`
- `scripts/shipinhao_mirror_manager.py`

## Goals

- Inventory existing Shipinhao rows without publishing anything.
- Match Shipinhao rows back to LazyEdit publish metadata by title text and
  publish time.
- Preserve row image/cover URLs, links, publish metadata fingerprints, local
  cover hashes, ZIP fingerprints, and LazyEdit publish job history in a local
  SQLite mirror database.
- Build safe plans for maintenance tasks such as missing-description repair.
- Keep post-management code separate from upload/publish code.

## Browser Session

Use the normal logged-in Shipinhao Chromium session:

```bash
ssh lachlan@lazyingart
cd ~/Projects/autopub
/home/lachlan/venvs/autopub/bin/python scripts/shipinhao_mirror_manager.py mirror \
  --scrolls 5 \
  --output /tmp/shipinhao_mirror.json
```

The script attaches to port `5006` by default. If the tab is already on the
right page and you do not want navigation, pass `--url ""`.

Inventory rows now include visible text, links, row attributes, and cover/image
URLs discovered from `img`, `video[poster]`, and CSS background images. This
lets future management tools compare row state with local LazyEdit cover files
instead of relying only on row text.

## LazyEdit Metadata Index

Build the metadata index from LazyEdit `DATA`:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
python AutoPublish/scripts/shipinhao_mirror_manager.py export-metadata \
  --metadata-root DATA \
  --days 45 \
  --output /tmp/lazyedit_shipinhao_metadata_index.json
```

The exported record includes the metadata path, folder name, title,
description, tags, cover path, cover SHA-256, metadata SHA-256, ZIP head hash,
publish category, local video path, and file mtime. The current matching logic
uses text evidence first, then publish-time proximity. Cover/image evidence is
stored in the mirror database for future stronger comparisons and manual
audits.

## LazyEdit Publish History

When run on the LazyEdit host, export local publish jobs from Postgres:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
python AutoPublish/scripts/shipinhao_mirror_manager.py export-publish-history \
  --limit 500 \
  --output /tmp/lazyedit_shipinhao_publish_history.json
```

By default this filters to jobs whose platform flags include `shipinhao`.
Use `--all-platforms` only for broad audits.

## Persistent Mirror Database

The stronger management workflow keeps a SQLite mirror DB independent from
publication. It can be rebuilt at any time from a platform mirror, LazyEdit
metadata index, and optional publish history:

```bash
python AutoPublish/scripts/shipinhao_mirror_manager.py sync-db \
  --db /tmp/shipinhao_management.sqlite \
  --mirror /tmp/shipinhao_mirror.json \
  --metadata-index /tmp/lazyedit_shipinhao_metadata_index.json \
  --publish-history /tmp/lazyedit_shipinhao_publish_history.json \
  --output-plan /tmp/shipinhao_description_plan.json
```

Inspect the summary and planned repairs:

```bash
python AutoPublish/scripts/shipinhao_mirror_manager.py db-report \
  --db /tmp/shipinhao_management.sqlite \
  --limit 20
```

The DB tables are:

- `shipinhao_rows`: mirrored platform rows with stable row keys, links, image
  URLs, visible descriptions, category guesses, and first/last seen times.
- `lazyedit_metadata`: local publish metadata, description text, cover hashes,
  ZIP hashes, and routing fields.
- `lazyedit_publish_jobs`: LazyEdit publish queue/history rows, remote job ids,
  ZIP paths, status, errors, and timestamps.
- `shipinhao_matches`: current row-to-metadata match plans.
- `shipinhao_apply_attempts`: every dry-run or real apply attempt and its
  result.

## Description Repair Planning

Generate a plan from a Shipinhao mirror and LazyEdit metadata:

```bash
python AutoPublish/scripts/shipinhao_mirror_manager.py plan-descriptions \
  --mirror /tmp/shipinhao_mirror.json \
  --metadata-index /tmp/lazyedit_shipinhao_metadata_index.json \
  --include-ok \
  --output /tmp/shipinhao_description_plan.json
```

By default this only plans updates for rows whose visible description is very
short or date-only. It does not overwrite a meaningful existing description
unless `--repair-mismatched` is supplied.

Always inspect planned updates first:

```bash
jq '[.[] | select(.action=="update-description") | {
  query,
  metadata_title,
  row_published_at,
  metadata_mtime,
  match_score,
  new_length
}]' /tmp/shipinhao_description_plan.json
```

Dry-run apply:

```bash
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/shipinhao_mirror_manager.py apply-descriptions \
  --plan /tmp/shipinhao_description_plan.json \
  --db /tmp/shipinhao_management.sqlite \
  --output /tmp/shipinhao_description_apply_dryrun.json'
```

Real apply requires `--apply`:

```bash
ssh lachlan@lazyingart 'cd ~/Projects/autopub && /home/lachlan/venvs/autopub/bin/python scripts/shipinhao_mirror_manager.py apply-descriptions \
  --plan /tmp/shipinhao_description_plan.json \
  --db /tmp/shipinhao_management.sqlite \
  --apply \
  --limit 1 \
  --output /tmp/shipinhao_description_apply_limit1.json'
```

## Current Shipinhao Limitation

On 2026-06-29, old rows whose descriptions were completely missing could be
matched back to LazyEdit metadata, but they could not be restored through the
desktop Shipinhao UI.

Observed behavior:

- The list row action is `修改描述和封面`.
- The reliable click target is the icon area inside `.edit-cover-item`, not
  the visible label text.
- The action opens `/platform/post/coverEdit`.
- Shipinhao shows a guide dialog requiring `我知道了`.
- The description edit panel says selected text can be modified, with a
  20-character limit.
- For missing-description rows, `.edit-desc-content.edit-select-area` is empty,
  and no visible editor/input is exposed.

Therefore the tool reports:

```text
unsupported-description-repair
Shipinhao coverEdit only supports modifying selected existing text, limited to
20 characters; blank/missing descriptions cannot be restored through the
visible UI.
```

No description changes should be assumed unless a post-apply mirror confirms
the visible row text changed.

The mirror DB records these unsupported attempts in `shipinhao_apply_attempts`
so future tooling can see that a row was identified correctly but blocked by
the platform UI.

## 2026-06-29 Test Result

The first-page mirror found six date-only rows that matched LazyEdit metadata
by publish time:

- `2026年06月23日 11:18` -> `紀念日單軌列車與泰迪熊`
- `2026年06月22日 21:57` -> `地板下的金色秘密`
- `2026年06月21日 16:24` -> `橄欖油當洗髮水？結局笑翻`
- `2026年06月21日 16:21` -> `橄欖油當洗髮水？結局笑翻`
- `2026年06月21日 16:06` -> `日語朗讀測試：史記·孔子世家`
- `2026年06月21日 15:44` -> `輕盈前髮修剪技巧分享`

The one-row real apply test on `2026年06月23日 11:18` returned the unsupported
state above. No rows were modified.

## Design Notes

- The mirror tool must stay independent from `pub_shipinhao.py` upload logic.
- Read-only commands are the default.
- Mutating commands require `--apply`, and should be tested with `--limit 1`.
- Matching by time alone is only allowed for short/date-only rows; normal rows
  need text evidence.
- Do not bulk-apply a generated plan without checking the JSON.
