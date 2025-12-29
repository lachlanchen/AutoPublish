<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish

Automation toolkit for distributing short-form video content to multiple Chinese and international creator platforms. The project combines a Tornado-based service, Selenium automation bots, and a local file-watcher workflow so that dropping a video into a folder eventually results in uploads to XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), and optionally YouTube.

The repository is intentionally low-level: most configuration lives in Python files and shell scripts. This document walks through every moving part so you can adapt it to your machines safely.

---

## 1. System Overview

Workflow at a glance:

1. **Raw footage intake**: Place a video inside `videos/`. The watcher (either `autopub.py` or a LaunchAgent/cron job) notices new files using `videos_db.csv` and `processed.csv`.
2. **Asset generation**: `process_video.VideoProcessor` uploads the file to a content-processing server (`upload_url` and `process_url`) which returns a ZIP package containing:
   - The edited/encoded video (`<stem>.mp4`),
   - A cover image,
   - `{stem}_metadata.json` with localized titles, descriptions, tags, etc.
3. **Publishing**: Metadata drives the Selenium publishers in `pub_*.py`. Each publisher attaches to an already-running Chromium instance (remote debugging ports 5003–9222) using persistent user-data directories so you stay logged in.
4. **Web control plane (optional)**: `app.py` exposes `/publish`, accepts pre-built ZIP bundles, unpacks them, and calls the same publishers. It also keeps browser sessions alive by relaunching Chromium and triggering login helpers (`login_*.py`).
5. **Support modules**: `load_env.py` hydrates secrets from `~/.bashrc`, `utils.py` provides SendGrid-powered QR code emails and xdotool helpers, and `solve_captcha_*.py` scripts integrate with Turing/2Captcha when captchas appear.

---

## 2. Repository Layout

| Path | Purpose |
| --- | --- |
| `app.py` | Tornado service exposing `/publish`, orchestrates Selenium sessions, refreshes browsers, and routes to platform publishers. |
| `autopub.py` | CLI watcher: scans `videos/`, processes new files, and invokes publishers in parallel. Ideal for cron/LaunchAgent runs. |
| `process_video.py` | Handles upload to the media-processing backend and downloads the resulting ZIP bundle. Also performs FFmpeg preprocessing for streaming endpoints. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_y2b.py` | Selenium automation per platform. Each depends on a companion `login_*.py` module for QR-code based re-login flows. |
| `login_*.py` | Detects when a platform session has expired, requests a new QR code, screenshots it, and emails it through SendGrid. |
| `load_env.py` | Sources `~/.bashrc`, loads secrets into `os.environ`, and masks sensitive values in logs. |
| `run_autopub.sh`, `setup_autopub.sh` | Wrapper + macOS LaunchAgent generator for running `autopub.py` on a schedule with locking and logging. |
| `ignore_*` files | Drop an empty file named `ignore_xhs`, `ignore_douyin`, etc. to temporarily disable a platform without changing code. |
| `logs/`, `logs-autopub/`, `chromium_dev_session_logs/` | Execution and browser logs—inspect them whenever a run fails. |

---

## 3. Prerequisites

### 3.1 Operating System & Packages

* Linux desktop/server with an X session (remote debugging windows appear on `DISPLAY=:1` in the current scripts).
* Chromium/Chrome with matching ChromeDriver (`chromium-browser`, `chromedriver`).
* GUI automation helpers: `xdotool`, `ffmpeg`, `zip`, `unzip`.
* Python 3.10+ (Miniconda works well). The repo ships a huge `requirements.txt`; if you only need the publishing pipeline, the key packages are:

  ```bash
  pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
  ```

  For parity with the original environment run:

  ```bash
  pip install -r requirements.txt
  ```

### 3.2 External Accounts & APIs

| Variable | Description |
| --- | --- |
| `SENDGRID_API_KEY`, `FROM_EMAIL`, `TO_EMAIL` | SendGrid credentials used by QR-code mailers in `utils.SendMail`. |
| `APIKEY_2CAPTCHA` | API key for 2Captcha (remove the hard-coded fallback in `solve_captcha_2captcha.py` before pushing code publicly). |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Credentials for the Turing captcha solver used inside `solve_captcha_turing.py`. |
| Platform logins | Manually log into XiaoHongShu, Douyin, Bilibili, etc. once per Chromium profile; the automation reuses those sessions. |

Add these to `~/.bashrc` (or the shell profile you actually use) so `load_env.py` can import them:

```bash
export SENDGRID_API_KEY="..."
export FROM_EMAIL="notifications@example.com"
export TO_EMAIL="me@example.com"
export APIKEY_2CAPTCHA="..."
export TULING_USERNAME="..."
# ...
```

Run `source ~/.bashrc` and `python load_env.py` to verify they are discoverable.

---

## 4. Configure Local Paths

Many modules hard-code directories under `/home/lachlan/Projects/auto-publish`. Update the following constants before running on a different host:

| File | Constant(s) | Meaning |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`, `chromedriver_path`. | Base folders for assets, log files, transcription output, and processing endpoints. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | Same as above for the CLI workflow. |
| `run_autopub.sh` / `setup_autopub.sh` | Absolute paths to Conda, repo, lockfiles, and log destinations. |
| `utils.py` | `crop_and_resize_cover_image` points to `/usr/local/bin/ffmpeg`. Change if FFmpeg lives elsewhere. |

Tip: centralize these values via environment variables or a `.env` reader if you plan to deploy the project on multiple machines.

---

## 5. Preparing Browser Sessions

1. **Create dedicated profiles** so the automation can restart Chromium without losing state:

   ```bash
   mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,9222}
   mkdir -p ~/chromium_dev_session_logs
   ```

2. **Launch Chromium with remote debugging** (do this for each platform you need). Example for XiaoHongShu:

   ```bash
   DISPLAY=:1 chromium-browser \
     --remote-debugging-port=5003 \
     --user-data-dir="$HOME/chromium_dev_session_5003" \
     https://creator.xiaohongshu.com/creator/post \
     > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
   ```

   `app.py`’s `stop_and_start_chromium_sessions` function automates these launches, but you must ensure the `sudo` password handling is secure (replace the hard-coded `"1"` with a prompt or a password manager).

3. **Log in manually** the first time. The `login_*.py` helpers monitor session status and email you whenever a QR code refresh is needed.

4. **Verify connectivity**: From a Python shell run `webdriver.Chrome(options=...)` with `debuggerAddress` pointing at one of the ports to ensure ChromeDriver can attach.

---

## 6. Running the CLI Pipeline (`autopub.py`)

1. Drop or sync raw videos into `videos/` (or whatever `autopublish_folder_path` points to). Filenames must end in `.mp4`, `.mov`, `.avi`, `.flv`, `.wmv`, or `.mkv`.

2. Execute:

   ```bash
   python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
   ```

   Flags:

   | Flag | Meaning |
   | --- | --- |
   | `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Limit publishing to specific platforms. If none are set, all three default to `True`. |
   | `--test` | Passes `test=True` into publishers so they can perform dry runs (platform implementation dependent). |
   | `--use-cache` | Reuses previously processed ZIP files in `transcription_data/<video>/` if they exist. |

3. The script logs activity to `logs/<timestamp>.txt` and appends filenames to `videos_db.csv` (every file seen) and `processed.csv` (successfully uploaded).

4. Process flow per video:
   - Upload & process via `process_video.py`.
   - Extract ZIP contents into `transcription_data/<video>/`.
   - Launch publishers in parallel via `ThreadPoolExecutor`.
   - Update `processed.csv` only after at least one platform succeeded.

5. To run it on a schedule, use `run_autopub.sh`. It:
   - Sources your shell profile,
   - Activates Conda,
   - Checks/creates `/path/to/autopub.lock`,
   - Logs output to `logs-autopub/autopub_<timestamp>.log`.

   On macOS, run `setup_autopub.sh` to install a LaunchAgent (`~/Library/LaunchAgents/com.lachlan.autopublish.plist`) that triggers whenever files change inside the watch path. On Linux, adapt the same logic to systemd timers or cron.

---

## 7. Running the Tornado Service (`app.py`)

`app.py` consolidates browser management and exposes a REST endpoint that other systems can call once they’ve already generated the ZIP bundle.

```bash
python app.py --refresh-time 1800 --port 8081
```

### 7.1 `/publish` Endpoint

* **Method**: `POST`
* **Headers**: `Content-Type: application/octet-stream`
* **Query/Form parameters**:

  | Param | Default | Description |
  | --- | --- | --- |
  | `filename` | *required* | Expected to end in `.zip`. Determines extraction directory and metadata filename. |
  | `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_y2b` | `false` | Set to `true` to enable that platform for this request. Each flag is also gated by the presence of `ignore_*` files. |
  | `test` | `false` | Passes through to publishers. |

* **Body**: Raw ZIP file with the same structure produced by `process_video.py`.

Example upload:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_y2b=true" \
     --data-binary @demo.zip \
     -H "Content-Type: application/octet-stream"
```

The handler:

1. Optionally restarts Chromium sessions for the requested platforms.
2. Saves the ZIP under `transcription_root/<stem>/`.
3. Extracts metadata, cleans Unicode/emoji via `clean_title` / `clean_bmp`.
4. Brings the corresponding browser window to the foreground (`bring_to_front`) before each publish call to reduce flakiness.
5. Responds with JSON `{"message": "Published the content from demo.zip"}` or an error payload.

### 7.2 Background Browser Refresh

The `refresh_browsers` thread periodically calls:

* `stop_and_start_chromium_sessions` to restart browsers,
* `login_*.check_and_act()` to prompt for QR re-authentication,
* `bring_to_front` to focus windows.

Tune the interval using `--refresh-time` (seconds). The actual sleep length is randomized to mimic human interaction.

---

## 8. Metadata & ZIP Format

The automation expects each ZIP to contain at minimum:

```
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` (Simplified Chinese) drives all CN publishers. Optional `metadata["english_version"]` feeds the YouTube publisher (`pub_y2b`). Fields referenced in code:

* `title`, `brief_description`, `middle_description`, `long_description`
* `tags` (list of hashtags)
* Platform-specific switches you may add (e.g., Douyin location, category).

If you’re generating these ZIPs from another service, ensure the JSON keys match what `pub_*.py` expects.

---

## 9. Platform-Specific Notes

| Platform | Port | Module | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | Uses QR code re-login via SendGrid. Cleans titles to 20 chars, appends hashtags from `metadata["tags"]`. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Tracks upload completion via `"重新上传"` text. Throws `UploadFailedException` to trigger retry logic. |
| Bilibili | 5005 | `pub_bilibili.py`, (login handled inline) | Includes Geetest captcha solving hook (`solve_captcha_2captcha.py` / `solve_captcha_turing.py`). |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Similar flow; ensure the WeChat QR emails reach a device that can approve login quickly. |
| YouTube | 9222 | `pub_y2b.py` | Uses the English metadata block. Disable it by creating `ignore_y2b`. |

For each platform you can temporarily pause automation by touching the corresponding `ignore_*` file in the repo root. Remove the file to re-enable.

---

## 10. Troubleshooting & Maintenance

* **Secrets hygiene**: Run `~/.local/bin/detect-secrets scan` before pushing. Remove literal API keys (e.g., the fallback 2Captcha token) and rotate any credentials that ever lived in git history.
* **Chromedriver mismatches**: If `selenium.common.exceptions.WebDriverException: unknown error: DevToolsActivePort file doesn't exist` occurs, ensure the running Chromium version matches the installed ChromeDriver. `webdriver-manager` can auto-download if you replace the hard-coded path with `ChromeDriverManager().install()`.
* **Browser focus issues**: `bring_to_front` relies on `xdotool search --name Chromium`. If your window titles differ, update the pattern list in each publisher or set custom titles using `--app-name`.
* **Captchas**: Bilibili and other sites may surface Geetest challenges. Configure `solve_captcha_turing.py` or `solve_captcha_2captcha.py` with real credentials and integrate their outputs in the publisher flows.
* **Processing backend**: If `process_video` fails with “Failed to get the uploaded file path,” inspect the API responses from your backend service. The upload endpoint must return JSON containing `file_path`, and the processing endpoint must stream the ZIP in its body.
* **Logs**: Check `logs/<timestamp>.txt`, `logs-autopub/`, and `chromium_dev_session_logs/*.log` for stack traces. Tornado’s console output also prints every Selenium exception.
* **Lock files**: If `autopub.py` never starts, delete the stale `autopub.lock` (path configured inside `run_autopub.sh`) after verifying no real process is running.

---

## 11. Extending the System

* **Adding a new platform**: Copy a `pub_*.py` file, change locators and metadata usage, add a matching `login_*.py` if QR login is required, register it in `app.py` and `autopub.py`, and create an `ignore_<platform>` toggle file.
* **Config abstraction**: Consider introducing `config.yaml` + `pydantic` models to replace scattered path constants. That also makes it easier to run multiple instances (e.g., staging vs. production).
* **Credential storage**: Replace hard-coded sudo passwords with `sudo -A` (askpass helper) or system keychains. Use a secrets manager (1Password CLI, AWS Secrets Manager, etc.) for API keys.
* **Containerization**: Package Chromium, ChromeDriver, and the Python runtime into a single container with a VNC display if you need to deploy on cloud servers.

---

## 12. Quick Start Checklist

1. `git clone` this repository.
2. Create/activate a Python environment; `pip install -r requirements.txt`.
3. Edit path constants in `app.py`, `autopub.py`, and shell scripts to match your filesystem.
4. Export SendGrid/captcha credentials in `~/.bashrc`; run `python load_env.py` to confirm.
5. Create Chromium profile folders and launch each browser with `--remote-debugging-port` once; log into all platforms.
6. Start the Tornado service (`python app.py --port 8081`) **or** schedule `python autopub.py --use-cache`.
7. Drop a sample video into `videos/` and watch the logs for successful uploads.
8. Run `~/.local/bin/detect-secrets scan` before every push to ensure no secrets leak.

With these pieces in place, you can fully automate multi-platform video publishing while keeping manual control over inputs and credentials.

---

## 13. Support AutoPublish

AutoPublish sits inside a broader effort to keep cross-platform creator tooling open and hackable. Donations help:

- Keep the Selenium farm, processing API, and cloud GPUs online.
- Ship new publishers (Kuaishou, Instagram Reels, etc.) plus reliability fixes for the existing bots.
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
