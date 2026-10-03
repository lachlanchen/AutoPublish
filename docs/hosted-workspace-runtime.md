# AutoPublish in a private LazyEdit Docker workspace

The parent LazyEdit repository contains `hosted/` and `deploy/hosted/`: an
invite-only account gateway, per-user runtime, build recipes and operator
provisioner. This repository keeps the platform publishing logic. No Pi is
required for the Docker deployment; the existing Pi installation is unaffected.

`container_runtime.py` runs the existing publisher queue and exposes a small
loopback-only `/platform-login` operation. It accepts only the six fixed
platform names and refuses a new browser opening while publication is active.
The parent Studio adapter authenticates HTTP and noVNC/WebSocket requests.
**Never expose port 8081, VNC or CDP directly to the Internet.**

Configuration:

- `AUTOPUBLISH_DATA_ROOT`: replaces the historical owner-specific data root.
  Default remains unchanged for existing installs.
- `HOME`: private persistent workspace home; existing profile-resolution logic
  uses it for each platform's browser profile. Do not share HOME across users.
- `AUTOPUBLISH_ACCOUNT_NEUTRAL=1`: skip the historical owner's name hints and
  rely on account-neutral creator/editor login checks. Explicit name overrides
  still work. Shipinhao already uses generic account detection.
- `AUTOPUBLISH_QUEUE_JOURNAL`: opt-in atomic queue snapshot. Queued jobs resume;
  interrupted running jobs become failed pending manual history verification.
  Never automatically replay a possibly submitted social post.
- `AUTOPUBLISH_LOCAL_PACKAGE_ROOT`: opt-in shared-volume delivery. A loopback
  caller may reference an existing ZIP under this root rather than upload a
  second copy. Canonical path checks reject escapes/symlinks outside the root;
  a SHA-256 binds the queued job to the prepared archive. Changing it while
  queued fails closed. This supports both video and music packages.
- `AUTOPUBLISH_BIND=127.0.0.1`, `AUTOPUBLISH_AUTORELOAD=0`: optional settings for
  the normal `app.py` entry point. The container adapter always binds loopback
  and does not use development autoreload.

The hosted login screen and the publisher open the same profile directories and
CDP ports. Profile volumes survive image replacement. Long QR login waits are
unchanged. QR email is optional and must use that workspace owner's recipient;
none of the existing owner's .env/cookies are copied into an image.

Each workspace has its own queue and browser. The parent deployment caps memory,
CPU and total admitted users. Use one publisher worker per workspace. Drain
active jobs before upgrading. If a restart happens after a submit click, check
the actual platform listing before retrying only missing destinations.

With local package delivery, extraction uses
`transcription_data/scratch/<job-id>`. Only that disposable directory is removed
after success/failure or startup recovery of an interrupted job. Source media,
the canonical ZIP, queue journal and publication evidence are retained. The
ordinary remote ZIP-upload protocol and its storage retention are unchanged.

Validation (no real posts or emails):

```bash
python -m pytest -q tests/test_queue_journal.py tests/test_hosted_account_detection.py tests/test_local_package.py
```

Queue persistence is deliberately opt-in, so merely pulling this change on an
existing host does not migrate its runtime or restart its publisher.
