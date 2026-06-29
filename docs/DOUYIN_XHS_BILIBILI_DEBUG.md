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

On the Raspberry Pi, Chromium must be started with software rendering flags.
AutoPublish uses:

```bash
AUTOPUBLISH_CHROMIUM_FLAGS="--disable-gpu --use-gl=swiftshader --enable-unsafe-swiftshader --disable-dev-shm-usage --password-store=basic"
```

The same flags are used by `scripts/debug_platform_logins.py`. Keep this close
to the manual `start_chromium_*` aliases. The `--password-store=basic` flag is
important on the Pi: after reboot or undervoltage events, the desktop keyring
can be locked and Chromium can hang at `Loading...` before creating a usable
page target. This flag keeps cookies in the Chromium profile while avoiding the
keyring modal.

The `--enable-unsafe-swiftshader` flag is also intentional on Chromium 143+.
Without it, Bilibili logs WebGL fallback failures from its uploader/cover
scripts. The Pi is a trusted local publishing box, so this lower-security
software WebGL opt-in is acceptable for these isolated creator profiles.

Do not use DevTools `/json/new` as a generic blank-tab repair: on the Pi it can
create extra empty windows and make creator SPAs harder to recover. Navigation
retries should stay inside the existing tab/profile so the login session
remains shared.

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

## Current Creator URLs

Use the current routes instead of the older XHS `/creator/home` and
`/creator/post` URLs:

- XiaoHongShu home: `https://creator.xiaohongshu.com/new/home?source=official`
- XiaoHongShu publish: `https://creator.xiaohongshu.com/publish/publish?source=official`
- Douyin home: `https://creator.douyin.com/creator-micro/home`
- Douyin upload: `https://creator.douyin.com/creator-micro/content/upload`
- Bilibili upload: `https://member.bilibili.com/platform/upload/video/frame`

For XiaoHongShu/RedNote regional changes, override without code edits:

```bash
XHS_CREATOR_BASE_URL=https://creator.xiaohongshu.com
XHS_HOME_URL=https://creator.xiaohongshu.com/new/home?source=official
XHS_PUBLISH_URL=https://creator.xiaohongshu.com/publish/publish?source=official
```

These sites are heavy SPAs and can leave Selenium waiting in `driver.get()`.
Platform login and publish code now uses `utils.safe_get()` as a non-invasive
bounded navigation helper. It reuses the current browser tab/profile, avoids
creating new DevTools targets, avoids JavaScript `window.stop()` against a
frozen renderer, and returns control to platform-specific selectors if the page
load does not settle quickly. If a creator page looks blank, prefer restarting
that platform's Chromium profile with the normal alias-style command instead of
opening extra DevTools tabs.

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

The Bilibili final submit step now confirms real completion instead of
swallowing click/captcha exceptions. It clicks `立即投稿`, solves GeeTest when
present, watches for publish success/failure markers or URL changes, and writes
an HTML snapshot if the submit button or confirmation state is missing.

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

## 2026-06-29 MV Publish Notes

Target video:

```text
aya_chan_hikari_ame_full_mv_song_locked_portrait_fg30_bottom40_2026-06-29.mp4
```

LazyEdit package that reached AutoPublish:

```text
aya_chan_hikari_ame_lalamv_publish_20260629_session_17.zip
```

This session-17 package was later found to contain the wrong rendered video for
the user's intended publish. The correct retry package was:

```text
aya_chan_hikari_ame_portrait_fg30_bottom40_dy_bl_xhs_20260629.zip
```

It packaged the existing portrait bg-fill MP4 with burned subtitles and the
configured LazyEdit logo:

```text
aya_chan_hikari_ame_full_mv_song_locked_portrait_fg30_bottom40_2026-06-29_portrait_subtitles_logo.mp4
```

Observed issues and fixes:

- LazyEdit upload collision: do not upload a file that is already inside
  LazyEdit `DATA/` using the same filename. The upload-stream endpoint writes
  to `DATA/<stem>/<filename>` and can truncate the source if source and target
  are the same inode/path. Use `--video-id` for existing videos, or pass a
  safe non-colliding `--filename`.
- XiaoHongShu publish button changed: after entering hashtags, a suggestion
  popover can cover the final button. Press Escape/blur the editor after
  filling the description. The final red publish control can render inside a
  custom `xhs-publish-btn` element, so `pub_xhs.py` now falls back to clicking
  that custom element by host offset if normal button selectors fail.
- Bilibili optional SMS overlay: upload completion can show an SMS
  verification dialog for upload-completion notifications. This is optional;
  close `.base-verify-close` or the notification dialog and click `继续上传`
  if the upload pauses.
- Bilibili retry contract: old `pub_bilibili.py`, `pub_douyin.py`, and
  `pub_xhs.py` printed "Maximum retry attempts reached" but returned `None`,
  which the app treated as success. The publishers now return `True` on
  success and raise on retry exhaustion.
- Bilibili cover cropper: the Pi has ffmpeg at `/usr/bin/ffmpeg`, not
  `/usr/local/bin/ffmpeg`. `utils.crop_and_resize_cover_image()` now uses
  `FFMPEG_BIN` or `shutil.which("ffmpeg")`. The Bilibili cover dialog is
  best-effort; if it times out, continue with Bilibili's default generated
  cover instead of restarting the whole upload.
- Bilibili upload rows: retrying on the same SPA page accumulates many pending
  upload rows. Do not use a generic `//*[contains(text(),"上传完成")]` check;
  it can match an old row and start filling the form while the current file is
  still `上传中` or `等待上传`. `pub_bilibili.py` now resets the page, uploads
  through a short `/tmp/autopub_bilibili_uploads/bilibili_upload_*.mp4` copy,
  and checks the status row for that exact file.
- Bilibili rate limit: repeated retries can make
  `https://member.bilibili.com/preupload` return HTTP `406` with code `601`
  and message `您上传视频过快，请您稍作休息后再继续`. When this appears, stop
  retrying and wait. Further retries extend the cooldown. The publisher now
  probes the logged-in browser-side preupload response when the UI is stuck at
  `0.0MB/0.0MB` and raises a fatal rate-limit error instead of looping.
- Douyin draft reuse: if a failed attempt leaves a valid unpublished Douyin
  draft, continue that draft instead of uploading again. Douyin's SPA can hang
  Selenium on synchronous `element.click()` and native `send_keys()` against
  React-controlled fields, so `pub_douyin.py` now uses asynchronous JavaScript
  clicks and JavaScript field replacement. It also avoids the separate topic
  widget; hashtags remain in the description.
- Bilibili SMS gate: on 2026-06-29 the upload page showed
  `请完成短信验证` and stayed at `0.0MB/0.0MB`. This is not GeeTest/click captcha
  and cannot be solved by Tuling. The publisher now reports this as SMS
  verification required instead of hiding it behind the upload-rate message.
- Platform-only retry: when XHS/Douyin/Bilibili are being added to an already
  processed LazyEdit run, reuse the existing ZIP if it contains the desired MP4.
  Only rebuild the ZIP when the existing package points to the wrong rendered
  output.

Operational rule: after a Bilibili code-601 cooldown, leave the `autopub`
service idle and retry only after a cooldown probe no longer returns code
`601`. Do not keep uploading or refreshing the same file during the cooldown.
