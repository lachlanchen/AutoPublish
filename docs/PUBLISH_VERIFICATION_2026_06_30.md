# Publish Verification Notes - 2026-06-30

## Problem

Browser publishers used to treat a publish-button click as success. That was too weak for Douyin and Shipinhao:

- Douyin can show an unpublished-draft prompt and reuse a stale draft instead of the requested video.
- Douyin can accept a submit click but the post may not appear in the creator management list.
- Shipinhao can finish the editor flow while the final post is still not visible yet.
- LazyEdit and AutoPublish then reported `done`, which made the operator manually check every platform.

## Current Behavior

AutoPublish now verifies successful publishes by opening the platform management page after submit and searching for metadata terms from the uploaded package.

Relevant code:

- `publish_verification.py`
- `pub_douyin.py`
- `pub_shipinhao.py`

The verifier collects text from `document.body`, shadow DOM, and scrollable list containers. This matters because Douyin's creator list can render inside scroll containers, and `document.innerText` can be empty even when the page is visibly loaded.

## Douyin Rules

Default behavior is conservative:

- `AUTOPUB_DOUYIN_REUSE_DRAFT` defaults to off.
- If Douyin shows `你还有上次未发布的视频`, AutoPublish opens that draft only to reach the editor, then replaces the media with the requested file.
- After clicking publish, AutoPublish opens `https://creator.douyin.com/creator-micro/content/manage`.
- The job succeeds only if the management page contains the title or description terms.
- If verification fails after submit, AutoPublish does not retry another upload. This avoids accidental duplicate publishes.

Optional env vars:

- `AUTOPUB_VERIFY_PUBLISH=0` disables management-page verification. Use only for emergency manual operation.
- `AUTOPUB_DOUYIN_REUSE_DRAFT=1` allows stale draft reuse. Use only when you have confirmed the draft is the exact requested video.
- `AUTOPUB_DOUYIN_VERIFY_TIMEOUT=240` controls Douyin verification timeout in seconds.

## Shipinhao Rules

After clicking `发表`, AutoPublish opens:

`https://channels.weixin.qq.com/platform/post/list`

The job succeeds only if the management page contains title or description terms from the package.

Optional env vars:

- `AUTOPUB_SHIPINHAO_VERIFY_TIMEOUT=300`
- `AUTOPUB_VERIFY_PUBLISH=0`

## Operational Lessons

- A platform log line like `Video published successfully!` is not enough unless it follows a management-page verification match.
- If a management-page verification fails, treat the platform as not confirmed even if the submit button was clicked.
- Do not repeatedly retry after a post-submit verification failure. First inspect the management page and the draft list to avoid duplicates.
- For LazyEdit repeat-publish jobs, reuse the existing ZIP only when the ZIP already contains the intended rendered video, logo/subtitle settings, and metadata.
- For Musia screen recordings, publish as `musia`, no LazyEdit subtitles, and top-right LazyEdit logo unless the user overrides it.

## Deployment

After changing AutoPublish from the LazyEdit submodule, deploy to Raspberry Pi:

```bash
git -C AutoPublish push origin main
ssh lachlan@lazyingart
cd ~/Projects/autopub
git pull origin main
/home/lachlan/venvs/autopub/bin/python -m py_compile publish_verification.py pub_douyin.py pub_shipinhao.py
tmux new-session -d -s autopub "cd ~/Projects/autopub && source /home/lachlan/venvs/autopub/bin/activate && python app.py"
curl -fsS http://127.0.0.1:8081/publish/queue
```
