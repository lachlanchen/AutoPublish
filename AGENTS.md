# Repository Guidelines

## Project Structure & Module Organization
- Root scripts (e.g., `autopub.py`, `app.py`, `process_video.py`) orchestrate ingestion, processing, and publishing of videos.
- Platform-specific automation lives in `pub_*.py` and the matching `login_*.py` modules; shared helpers reside in `utils.py`, `smtp.py`, and `load_env.py`.
- Assets such as processed video metadata/outputs live under `videos/`, `transcription_data/`, and `logs*/`.
- Documentation, funding, and media assets appear under `README.md`, `.github/FUNDING.yml`, and `figs/`.

## Build, Test, and Development Commands
- `python -m pip install -r requirements.txt`: installs Selenium, Tornado, and other dependencies before running automation.
- `python load_env.py`: mirrors `~/.bashrc` secrets into the current environment; run this before any publisher that needs API keys.
- `python autopub.py --pub-xhs --pub-douyin --pub-bilibili`: watches `videos/`, processes new files, and kicks off each publisher (use `--use-cache` to reuse artifacts).
- `python app.py --refresh-time N --port 8081`: starts the Tornado control plane used by webhooks or manual ZIP uploads.
- `python smtp.py` / `python smtp_test_simple.py`: manually exercise the SMTP helpers after populating `.env`.

## Coding Style & Naming Conventions
- Python files use 4-space indentation; keep imports grouped (stdlib, third-party, local).
- Use descriptive names for constants (e.g., `chromedriver_path`, `upload_url`) and avoid magic strings where possible.
- Keep platform toggles in `ignore_*` files; touching the file disables that publisher.
- Formatting is manual (no formatter enforced) but follow existing spacing and docstring patterns; run `python -m compileall` if needed for bytecode sanity.

## Testing Guidelines
- There is no automated test suite; rely on manual smoke tests (upload a sample video via `autopub.py`, verify `logs/` output).
- When adding new scripts, include a simple `if __name__ == "__main__":` block to demonstrate usage and to allow quick dry runs.
- Flagging issues should mention platform-specific behavior (e.g., YouTube check status) and include log snippets or screenshots if applicable.

## Commit & Pull Request Guidelines
- Follow the existing git history: commit titles use imperative verbs (e.g., “Wait for YouTube checks before publishing”, “Sanitize secrets...”).
- Keep each commit focused (separate docs, dependency updates, implementation tweaks).
- Pull requests should summarize what changed, note any manual steps (secrets, browser setup), and mention whether Chromium sessions were restarted; include screenshots/log lines if the change affects UI flows.

## Security & Configuration Tips
- Keep real secrets out of git—copy `.env.example` to `.env` and populate `SENDGRID_API_KEY`, `APP_PASSWORD`, `APIKEY_2CAPTCHA`, etc.; `.env` is ignored.
- Store Chromium user data and remote debugging folders outside the repo (typically `~/chromium_dev_session_*`).
- Rotate API keys if they were ever committed; hard-coded defaults (like the old 2Captcha token) are replaced with environment checks.
