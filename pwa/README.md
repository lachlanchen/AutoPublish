# AutoPublish Studio (PWA)

A standalone progressive web app for previewing LazyEdit ZIP bundles and submitting them to the AutoPublish backend.

## Quick start

Serve this folder as static files (no build step required):

```bash
cd /home/lachlan/ProjectsLFS/lazyedit/AutoPublish/pwa
python -m http.server 5173
```

Open `http://localhost:5173` and set the API base URL to the AutoPublish service (for example `http://lazyingart:8081`).

## Features

- Drag-and-drop ZIP preview (cover + metadata JSON).
- Toggle publish targets and test mode.
- Pushes ZIP bundles to `/publish` and watches `/publish/queue`.

## Notes

- The ZIP must include `<stem>_metadata.json` and a cover image referenced by `cover_filename`.
- The backend is unchanged; this UI only consumes the existing REST endpoints.
