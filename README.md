<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#prerequisites)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#system-overview)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#running-the-tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#platform-specific-notes)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#running-the-tornado-service-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Automation toolkit for distributing short-form video content to multiple Chinese and international creator platforms. The project combines a Tornado-based service, Selenium automation bots, and a local file-watcher workflow so that dropping a video into a folder eventually results in uploads to XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), Instagram, and optionally YouTube.

The repository is intentionally low-level: most configuration lives in Python files and shell scripts. This document is an operational manual that covers setup, runtime, and extension points.

> ⚙️ **Operational philosophy**: this project favors explicit scripts and direct browser automation over hidden abstraction layers.  
> ✅ **Canonical policy for this README**: preserve technical detail, then improve readability and discoverability.

## Quick Snapshot

| What | Value |
| --- | --- |
| Primary language | Python 3.10+ |
| Main runtimes | CLI watcher (`autopub.py`) + Tornado queue service (`app.py`) |
| Automation engine | Selenium + remote-debug Chromium sessions |
| Input formats | Raw videos (`videos/`) and ZIP bundles (`/publish`) |
| Current repo workspace path | `/home/lachlan/ProjectsLFS/AutoPublish` |
| Ideal users | Creators/ops engineers managing multi-platform short video pipelines |

---

## Table of Contents

- [System Overview](#system-overview)
- [Features](#features)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Preparing Browser Sessions](#preparing-browser-sessions)
- [Usage](#usage)
- [Examples](#examples)
- [Metadata & ZIP Format](#metadata--zip-format)
- [Platform-Specific Notes](#platform-specific-notes)
- [Raspberry Pi / Linux Service Setup](#raspberry-pi--linux-service-setup)
- [Legacy macOS Scripts](#legacy-macos-scripts)
- [Troubleshooting & Maintenance](#troubleshooting--maintenance)
- [Extending the System](#extending-the-system)
- [Quick Start Checklist](#quick-start-checklist)
- [Development Notes](#development-notes)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Support AutoPublish](#support-autopublish)

---

## System Overview

🎯 **End-to-end flow** from raw media to published posts:

Workflow at a glance:

1. **Raw footage intake**: Place a video inside `videos/`. The watcher (either `autopub.py` or a scheduler/service) notices new files using `videos_db.csv` and `processed.csv`.
2. **Asset generation**: `process_video.VideoProcessor` uploads the file to a content-processing server (`upload_url` and `process_url`) which returns a ZIP package containing:
   - the edited/encoded video (`<stem>.mp4`),
   - a cover image,
   - `{stem}_metadata.json` with localized titles, descriptions, tags, etc.
3. **Publishing**: Metadata drives the Selenium publishers in `pub_*.py`. Each publisher attaches to an already-running Chromium/Chrome instance using remote debugging ports and persistent user-data directories.
4. **Web control plane (optional)**: `app.py` exposes `/publish`, accepts pre-built ZIP bundles, unpacks them, and queues publish jobs to the same publishers. It can also refresh browser sessions and trigger login helpers (`login_*.py`).
5. **Support modules**: `load_env.py` hydrates secrets from `~/.bashrc`, `utils.py` provides helpers (window focus, QR handling, mail utility helpers), and `solve_captcha_*.py` integrates with Turing/2Captcha when captchas appear.

## Features

✨ **Designed for pragmatic, script-first automation**:

- Multi-platform publishing: XiaoHongShu, Douyin, Bilibili, ShiPinHao (WeChat Channels), Instagram, YouTube (optional).
- Two operating modes:
  - CLI watcher pipeline (`autopub.py`).
  - API queue service (`app.py` + `/publish` + `/publish/queue`).
- Per-platform temporary disable switches via `ignore_*` files.
- Remote-debugging browser-session reuse with persistent profiles.
- Optional QR/captcha automation and email notification helpers.
- No frontend build requirement for the included PWA (`pwa/`) uploader UI.
- Linux/Raspberry Pi automation scripts for service setup (`scripts/`).

---

## Repository Layout

🗂️ **Key modules and what they do**:

| Path | Purpose |
| --- | --- |
| `app.py` | Tornado service exposing `/publish` and `/publish/queue`, with internal publish queue and worker thread. |
| `autopub.py` | CLI watcher: scans `videos/`, processes new files, and invokes publishers in parallel. |
| `process_video.py` | Uploads videos to processing backend and stores returned ZIP bundles. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | Selenium automation modules per platform. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | Session checks and QR login flows. |
| `utils.py` | Shared automation helpers (window focus, QR/mail helper utilities, diagnostics helpers). |
| `load_env.py` | Loads env vars from shell profile (`~/.bashrc`) and masks sensitive logs. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | SMTP/SendGrid helper and test scripts. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Captcha solver integrations. |
| `scripts/` | Service setup and operations scripts (Raspberry Pi/Linux + legacy automation). |
| `pwa/` | Static PWA for ZIP preview and publish submission. |
| `setup_raspberrypi.md` | Step-by-step Raspberry Pi provisioning guide. |
| `.env.example` | Environment variable template (credentials, paths, captcha keys). |
| `.github/FUNDING.yml` | Sponsor/funding configuration. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | Runtime artifacts and logs (many are gitignored). |

---

## Prerequisites

🧰 **Install these before first run**.

### Operating system and tools

- Linux desktop/server with an X session (`DISPLAY=:1` is common in provided scripts).
- Chromium/Chrome and matching ChromeDriver.
- GUI/media helpers: `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv or Conda).

### Python dependencies

Minimal runtime set:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

Repository parity:

```bash
python -m pip install -r requirements.txt
```

For lightweight service installs (used by setup scripts by default):

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` contains:
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Optional: create a sudo user

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## Installation

🚀 **Setup from a clean machine**:

1. Clone the repository:

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. Create and activate an environment (example with `venv`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. Prepare environment variables:

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. Load variables for scripts that read shell profile values:

```bash
source ~/.bashrc
python load_env.py
```

Note: `load_env.py` is designed around `~/.bashrc`; if your environment uses a different shell profile, adapt accordingly.

---

## Configuration

🔐 **Set credentials, then verify host-specific paths**.

### Environment variables

The project expects credentials and optional browser/runtime paths from environment variables. Start from `.env.example`:

| Variable | Description |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | SMTP credentials for QR/login notifications. |
| `SENDGRID_API_KEY` | SendGrid key for email flows that use SendGrid APIs. |
| `APIKEY_2CAPTCHA` | 2Captcha API key. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Turing captcha credentials. |
| `DOUYIN_LOGIN_PASSWORD` | Douyin second verification helper. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Instagram/browser driver overrides. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | Preferred global browser/driver/display overrides in `app.py`. |

### Path constants (important)

📌 **Most common startup issue**: unresolved hard-coded absolute paths.

Several modules still contain hard-coded paths. Update these for your host:

| File | Constant(s) | Meaning |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | API service roots and backend endpoints. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | CLI watcher roots and backend endpoints. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Absolute paths to Python/Conda/repo/log locations. | Legacy/macOS-oriented wrappers. |
| `utils.py` | FFmpeg path assumptions in cover processing helpers. | Media tooling path compatibility. |

Important repository note:
- Current repository path in this workspace is `/home/lachlan/ProjectsLFS/AutoPublish`.
- Some code and scripts still reference `/home/lachlan/Projects/auto-publish` or `/Users/lachlan/...`.
- Preserve and adjust these paths locally before production usage.

### Platform toggles via `ignore_*`

🧩 **Fast safety switch**: touching an `ignore_*` file disables that publisher without code edits.

Publishing flags are also gated by ignore files. Create an empty file to disable a platform:

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

Remove the corresponding file to re-enable.

---

## Preparing Browser Sessions

🌐 **Session persistence is mandatory** for reliable Selenium publishing.

1. Create dedicated profile folders:

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. Launch browser sessions with remote debugging (example for XiaoHongShu):

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. Log in manually once for each platform/profile.

4. Verify Selenium can attach:

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Security note:
- `app.py` currently contains a hard-coded sudo password placeholder (`password = "1"`) used by browser restart logic. Replace this before real deployment.

---

## Usage

▶️ **Two runtime modes** are available: CLI watcher and API queue service.

### Running the CLI pipeline (`autopub.py`)

1. Put source videos in the watch directory (`videos/` or your configured `autopublish_folder_path`).
2. Run:

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Flags:

| Flag | Meaning |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Restrict publishing to selected platforms. If none are passed, all three default to enabled. |
| `--test` | Test mode passed into publishers (behavior varies by platform module). |
| `--use-cache` | Reuse existing `transcription_data/<video>/<video>.zip` if available. |

CLI flow per video:
- Upload/process through `process_video.py`.
- Extract ZIP to `transcription_data/<video>/`.
- Launch selected publishers via `ThreadPoolExecutor`.
- Append tracking state into `videos_db.csv` and `processed.csv`.

### Running the Tornado service (`app.py`)

🛰️ **API mode** is useful for external systems that produce ZIP bundles.

Start server:

```bash
python app.py --refresh-time 1800 --port 8081
```

### `POST /publish`

📤 **Queue a publish job** by uploading ZIP bytes directly.

- Header: `Content-Type: application/octet-stream`
- Required query/form arg: `filename` (ZIP filename)
- Optional booleans: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: raw ZIP bytes

Example:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

Current behavior in code:
- Request is accepted and queued.
- Immediate response returns JSON including `status: queued`, `job_id`, and `queue_size`.
- Worker thread serially processes queued jobs.

### `GET /publish/queue`

📊 **Observe queue health and in-flight jobs**.

Returns queue status/history JSON:

```bash
curl "http://localhost:8081/publish/queue"
```

Response fields include:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Browser refresh thread

♻️ Periodic browser refresh reduces stale-session failures over long uptime windows.

`app.py` runs a background refresh thread using `--refresh-time` interval and hooks in login checks. Refresh sleep includes randomized delay behavior.

### PWA frontend (`pwa/`)

🖥️ Lightweight static UI for manual ZIP uploads and queue inspection.

Run static UI locally:

```bash
cd pwa
python -m http.server 5173
```

Open `http://localhost:5173` and set backend base URL (for example `http://lazyingart:8081`).

PWA capabilities:
- Drag/drop ZIP preview.
- Publish-target toggles + test mode.
- Submits to `/publish` and polls `/publish/queue`.

---

## Examples

🧪 **Copy/paste smoke-test commands**:

### Example A: CLI publish run

```bash
python autopub.py --pub-xhs --pub-douyin --use-cache
```

### Example B: API publish run (single ZIP)

```bash
curl -X POST "http://localhost:8081/publish?filename=my_bundle.zip&publish_bilibili=true&test=true" \
  --data-binary @my_bundle.zip \
  -H "Content-Type: application/octet-stream"
```

### Example C: Check queue status

```bash
curl -s "http://localhost:8081/publish/queue"
```

### Example D: SMTP helper smoke test

```bash
python smtp.py
python smtp_test_simple.py
```

---

## Metadata & ZIP Format

📦 **ZIP contract matters**: keep filenames and metadata keys aligned with publisher expectations.

Expected ZIP contents (minimum):

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` drives CN publishers; optional `metadata["english_version"]` feeds YouTube publisher.

Fields commonly used by modules:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (list of hashtags)
- `video_filename`, `cover_filename`
- platform-specific fields as implemented in individual `pub_*.py` files

If you generate ZIPs externally, keep keys and filenames aligned with module expectations.

---

## Platform-Specific Notes

🧭 **Port map + module ownership** for each publisher.

| Platform | Port | Module(s) | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | QR re-login flow; title sanitization and hashtag usage from metadata. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Upload completion checks and retry paths are platform-fragile; monitor logs closely. |
| Bilibili | 5005 | `pub_bilibili.py` | Captcha hooks available via `solve_captcha_2captcha.py` and `solve_captcha_turing.py`. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Fast QR approval is important for session refresh reliability. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | Controlled in API mode with `publish_instagram=true`; env vars available in `.env.example`. |
| YouTube | 9222 | `pub_y2b.py` | Uses `english_version` metadata block; disable with `ignore_y2b`. |

---

## Raspberry Pi / Linux Service Setup

🐧 **Recommended for always-on hosts**.

For a full host bootstrap, follow [`setup_raspberrypi.md`](setup_raspberrypi.md).

Quick pipeline setup:

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

This orchestrates:
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

Run service manually in tmux:

```bash
./scripts/start_autopub_tmux.sh
```

Validate services/ports:

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## Legacy macOS Scripts

🍎 Legacy wrappers remain for compatibility with older local setups.

The repository still includes legacy macOS-oriented wrappers:
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

These contain absolute `/Users/lachlan/...` paths and Conda assumptions. Keep them if you rely on that workflow, but update paths/venv/tooling for your host.

---

## Troubleshooting & Maintenance

🛠️ **If something fails, start here first**.

- **Secrets hygiene**: run `~/.local/bin/detect-secrets scan` before push. Rotate any leaked credentials.
- **Processing backend errors**: if `process_video.py` prints “Failed to get the uploaded file path,” verify upload response JSON contains `file_path` and processing endpoint returns ZIP bytes.
- **ChromeDriver mismatch**: if DevTools connection errors appear, align Chrome/Chromium and driver versions (or switch to `webdriver-manager`).
- **Browser focus issues**: `bring_to_front` relies on window title matching (Chromium/Chrome naming differences can break this).
- **Captcha interrupts**: configure 2Captcha/Turing credentials and integrate solver outputs where needed.
- **Stale lock files**: if scheduled runs never start, verify process state and remove stale `autopub.lock` (legacy script flow).
- **Logs to inspect**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log`, plus service journal logs.

---

## Extending the System

🧱 **Extension points** for new platforms and safer operations.

- **Adding a new platform**: copy a `pub_*.py` module, update selectors/flows, add `login_*.py` if QR re-auth is needed, then wire flags and queue handling in `app.py` and CLI wiring in `autopub.py`.
- **Config abstraction**: migrate scattered constants to structured config (`config.yaml`/`.env` + typed model) for multi-host operation.
- **Credential storage hardening**: replace hard-coded or shell-exposed sensitive flows with secure secret management (`sudo -A`, keychain, vault/secret manager).
- **Containerization**: package Chromium/ChromeDriver + Python runtime + virtual display into one deployable unit for cloud/server use.

---

## Quick Start Checklist

✅ **Minimal path to first successful publish**.

1. Clone this repository and install dependencies (`pip install -r requirements.txt` or lightweight `requirements.autopub.txt`).
2. Update hard-coded path constants in `app.py`, `autopub.py`, and any script you will run.
3. Export required credentials in your shell profile or `.env`; run `python load_env.py` to validate loading.
4. Create remote-debug browser profile folders and launch each required platform session once.
5. Manually sign in on each target platform in its profile.
6. Start either API mode (`python app.py --port 8081`) or CLI mode (`python autopub.py --use-cache ...`).
7. Submit one sample ZIP (API mode) or one sample video file (CLI mode) and inspect `logs/`.
8. Run secrets scanning before every push.

---

## Development Notes

🧬 **Current development baseline** (manual formatting + smoke testing).

- Python style follows existing 4-space indentation and manual formatting.
- No formal automated test suite currently; rely on smoke tests:
  - process one sample video through `autopub.py`;
  - post one ZIP to `/publish` and monitor `/publish/queue`;
  - validate each target platform manually.
- Include a small `if __name__ == "__main__":` entrypoint when adding new scripts for quick dry-runs.
- Keep platform changes isolated where possible (`pub_*`, `login_*`, `ignore_*` toggles).
- Runtime artifacts (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) are expected to be local and are mostly ignored by git.

---

## Roadmap

🗺️ **Priority improvements reflected by current code constraints**.

Planned/desired improvements (based on current code structure and existing notes):

1. Replace scattered hard-coded paths with central config (`.env`/YAML + typed models).
2. Remove hard-coded sudo password patterns and move process control to safer mechanisms.
3. Improve publish reliability with stronger retries and better UI-state detection per platform.
4. Expand platform support (for example Kuaishou or other creators platforms).
5. Package runtime into reproducible deployment units (container + virtual display profile).
6. Add automated integration checks for ZIP contract and queue execution.

---

## Contributing

🤝 Keep PRs focused, reproducible, and explicit about runtime assumptions.

Contributions are welcome.

1. Fork and create a focused branch.
2. Keep commits small and imperative (example style in history: “Wait for YouTube checks before publishing”).
3. Include manual verification notes in PRs:
   - environment assumptions,
   - browser/session restarts,
   - relevant logs/screenshots for UI flow changes.
4. Never commit real secrets (`.env` is ignored; use `.env.example` for shape only).

If introducing new publisher modules, wire all of the following:
- `pub_<platform>.py`
- optional `login_<platform>.py`
- API flags and queue handling in `app.py`
- CLI wiring in `autopub.py` (if needed)
- `ignore_<platform>` toggle handling
- README updates

---

## License

No `LICENSE` file is currently present in this repository snapshot.

Assumption for this draft:
- Treat usage and redistribution as undefined until the maintainer adds an explicit license file.

Recommended next action:
- Add a top-level `LICENSE` (for example MIT/Apache-2.0/GPL-3.0) and update this section accordingly.

> 📝 Until a license file is added, treat commercial/internal redistribution assumptions as unresolved and confirm directly with the maintainer.

---

## Support AutoPublish

💖 Community support funds infra, reliability work, and new platform integrations.

AutoPublish sits inside a broader effort to keep cross-platform creator tooling open and hackable. Donations help:

- Keep the Selenium farm, processing API, and cloud GPUs online.
- Ship new publishers (Kuaishou, Instagram Reels, etc.) plus reliability fixes for existing bots.
- Share more documentation, starter datasets, and tutorials for independent creators.

### Donate

<div align="center">
<table style="margin:0 auto; text-align:center; border-collapse:collapse;">
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://chat.lazying.art/donate">https://chat.lazying.art/donate</a>
    </td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://chat.lazying.art/donate"><img src="figs/donate_button.svg" alt="Donate" height="44"></a>
    </td>
  </tr>
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://paypal.me/RongzhouChen">
        <img src="https://img.shields.io/badge/PayPal-Donate-003087?logo=paypal&logoColor=white" alt="Donate with PayPal">
      </a>
    </td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400">
        <img src="https://img.shields.io/badge/Stripe-Donate-635bff?logo=stripe&logoColor=white" alt="Donate with Stripe">
      </a>
    </td>
  </tr>
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><strong>WeChat</strong></td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><strong>Alipay</strong></td>
  </tr>
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><img alt="WeChat QR" src="figs/donate_wechat.png" width="240"/></td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><img alt="Alipay QR" src="figs/donate_alipay.png" width="240"/></td>
  </tr>
</table>
</div>

**支援 / Donate**

- ご支援はクリエイター自動化の研究・開発・運用コストをまかなう大きな力になります。
- 你的支持将用于服务器与研发，帮助作者持续开放改进跨平台发布工具链。
- Your support keeps the pipelines alive so more independent studios can publish everywhere with less busywork.

Also available via:
- GitHub Sponsors: <https://github.com/sponsors/lachlanchen>
- Project links: <https://lazying.art>, <https://chat.lazying.art>, <https://onlyideas.art>
