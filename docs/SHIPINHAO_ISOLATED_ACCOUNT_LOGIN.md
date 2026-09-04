# Isolated Shipinhao account login

## Purpose

`scripts/shipinhao_account_login.py` creates or reuses a named Shipinhao
Chromium profile without changing the production profile used by the normal
AutoPublish queue. It is intended for adding another account safely, including
self-contained QR scanning through a separate Waydroid WeChat appliance.

The normal publisher remains unchanged:

- Chromium debug port: `5006`
- profile: `~/chromium_dev_session_5006`
- queue and API behavior: unchanged

The first isolated account used on the Raspberry Pi is:

- profile label: `bolanjie`
- Chromium debug port: `5016`
- profile: `~/chromium_dev_session_shipinhao_bolanjie`
- QR server: `http://127.0.0.1:8765`

The helper rejects all existing platform debug ports and rejects any profile
directory other than the derived named path. This prevents an isolated login
command from accidentally opening or changing the production cookies.

## Decoupled design

The two sides communicate through one loopback HTTP image; neither controls the
other process:

1. AutoPublish opens the isolated browser and publishes the current login QR at
   `GET /qr.png`.
2. `GET /status.json` reports `starting`, `required`, `resolved`, or `error`,
   along with a QR revision and update time.
3. The Waydroid tool fetches `/qr.png`, atomically updates its virtual camera,
   and opens the real WeChat **Scan** UI.
4. Shipinhao completes OAuth in the isolated browser and keeps that browser
   profile for later reuse.

The server binds only to `127.0.0.1`, disables caching, validates the PNG
signature and size, and stops after login. Browser profiles, cookies, QR images,
and account data stay outside Git.

## Run it

Start the producer in one Pi terminal:

```bash
cd ~/Projects/autopub
~/venvs/autopub/bin/python scripts/shipinhao_account_login.py \
  --profile bolanjie \
  --debug-port 5016 \
  --server-port 8765 \
  --login-wait-seconds 1800
```

Then point the independent camera consumer at the loopback endpoint:

```bash
~/.local/bin/waydroid-qr-camera.py \
  --image-url http://127.0.0.1:8765/qr.png \
  --wait-seconds 30 \
  --open-scan
```

Email is disabled for this isolated helper by default. Add `--email` only if a
normal QR email is also wanted. The existing production login still sends its
usual email when required.

## Expected outcomes

- `resolved` means the isolated Chromium session reached an authenticated
  Shipinhao page. If visible, the account name is included in `status.json`.
- A Tencent account-exception screen is not a browser-profile or camera error.
  WeChat may require SMS verification after a correctly decoded self-scan. The
  one-time code must be supplied by the account owner; do not retry it in a
  loop.
- A QR refresh increments `revision`. Run the camera command again if WeChat
  was not already scanning the current image.

## Reuse and publication

Re-run the same command later to verify or refresh the `bolanjie` login. It
reuses port `5016` and the same named profile. It does not make this account the
default publishing destination. Any future publisher integration must select
the named profile explicitly; port `5006` remains the production default.

Before publishing to a new account, detect and record its actual channel name
from the authenticated page. Never infer account identity from the profile
label alone.
