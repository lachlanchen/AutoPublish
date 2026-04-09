# Shipinhao Publish Workflow

This is the verified workflow for diagnosing and deploying ShiPinHao publish fixes.

## Repos and hosts

- Local editable repo in this workspace: `/home/lachlan/DiskMech/Projects/lazyedit/AutoPublish`
- Live deploy host: `lachlan@lazyingart`
- Live deploy path on host: `~/Projects/autopub`
- Live tmux session on host: `autopub`

## Diagnose the live failure

On `lazyingart`, inspect the running pane:

```bash
tmux capture-pane -pt autopub:0.0 -S -220 | tail -n 220
```

For ShiPinHao, the publish flow should open:

```text
https://channels.weixin.qq.com/platform/post/create
```

The page is considered ready when at least one of these is present:

- `.post-create-wrap`
- `.post-edit-wrap`
- `.post-upload-wrap`
- `.input-editor[contenteditable]`
- the video upload `<input type="file">`

If readiness times out, inspect:

- `logs/selenium-shipinhao.log`
- `logs/shipinhao-publish_ready_timeout.png`

## Local fix and release workflow

From the local submodule checkout:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit/AutoPublish
python -m py_compile pub_shipinhao.py app.py autopub.py
git add pub_shipinhao.py app.py autopub.py scripts/setup_chrome_aliases.sh scripts/setup_chromium_alias_for_pi.sh docs/SHIPINHAO_PUBLISH_WORKFLOW.md
git commit -m "fix shipinhao publish readiness"
git push origin main
```

Then record the new submodule pointer in the parent LazyEdit repo:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
git add AutoPublish
git commit -m "update AutoPublish shipinhao fix"
git push origin main
```

## Deploy to lazyingart

The live host tracks GitHub as `origin`:

```bash
ssh lazyingart
cd ~/Projects/autopub
git pull origin main
```

If the tmux session is already running, restart the relevant browser session or rerun the publish job after pull.
