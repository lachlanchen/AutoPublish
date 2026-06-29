# Douyin, XiaoHongShu, and Bilibili Publish Debugging

Date: 2026-06-29

## Goal

Douyin, XiaoHongShu, and Bilibili used to work through dedicated Chromium
profiles on the Raspberry Pi. If a platform logs out or the site changes, the
publisher should stop before uploading, send a QR-login email like Shipinhao,
and leave enough HTML/screenshot evidence for selector fixes.

## Browser Profiles

AutoPublish uses one Chromium remote-debugging profile per platform:

- XiaoHongShu: port `5003`, profile `~/chromium_dev_session_5003`
- Douyin: port `5004`, profile `~/chromium_dev_session_5004`
- Bilibili: port `5005`, profile `~/chromium_dev_session_5005`

The Python app starts or reuses these sessions. It does not force-restart by
default, so successful logins survive the next publish. Only set
`AUTOPUBLISH_FORCE_BROWSER_RESTART=1` when a browser session is truly wedged.

## Login-Only Debug

Use the login-only tool before a real publish:

```bash
ssh lachlan@lazyingart
cd ~/Projects/autopub
/home/lachlan/venvs/autopub/bin/python scripts/debug_platform_logins.py --platforms xhs,douyin,bilibili
```

To shorten or lengthen the QR waiting window:

```bash
AUTOPUBLISH_LOGIN_WAIT_SECONDS=1800 \
/home/lachlan/venvs/autopub/bin/python scripts/debug_platform_logins.py --platforms bilibili
```

If login is needed, the script sends an email with a watch-friendly inline QR
image plus the full screenshot attachment. Scan it from the phone. The script
waits until the platform becomes logged in or until the timeout expires.

## Publish Behavior

- `login_douyin.py` and `login_xiaohongshu.py` now raise a clear error if login
  was not completed, instead of returning silently and allowing a broken upload.
- `login_bilibili.py` provides the same QR-email login gate for Bilibili.
- `pub_bilibili.py` calls `BilibiliLogin(...).check_and_act()` before upload.
- `app.py` includes Bilibili in the periodic browser login refresh for port
  `5005`.

## Bilibili Captcha

Bilibili upload can still trigger GeeTest/click captcha after clicking
`立即投稿`. The existing solver remains in `pub_bilibili.py`:

- API endpoint: `http://www.fdyscloud.com.cn/tuling/predict`
- Environment variables:
  - `TULING_USERNAME`
  - `TULING_PASSWORD`
  - `TULING_ID`

The solver screenshots the GeeTest panel, sends the image to Tuling, applies
the returned click coordinates, and presses the captcha confirm button.

Important fix from this update: `take_screenshot()` now uses `self.driver` and
the actual captcha image element when calculating the vertical coordinate
offset. The old code referenced undefined variables during that calculation,
which could make captcha clicks less accurate.

## Evidence On Failure

Failed platform publishes call `log_html_snapshot()` and write snapshots under
`logs/` or `logs-autopub/` depending on the caller. Use these snapshots to
update selectors when a site changes.

Recommended first checks:

```bash
ssh lachlan@lazyingart
cd ~/Projects/autopub
tail -n 120 logs-autopub/*.log
find logs logs-autopub -iname '*douyin*' -o -iname '*xiaohongshu*' -o -iname '*bilibili*'
```

## Real Publish Test

After login-only checks pass, trigger a real LazyEdit/AutoPublish publish with
only one of the affected platforms selected. Avoid testing all three at once
until each platform has passed individually.
