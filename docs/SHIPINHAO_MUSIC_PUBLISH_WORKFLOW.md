# Shipinhao Music Publish Workflow

This is the working note for the WeChat Channels / Shipinhao music uploader in
AutoPublish. Keep it separate from the normal video `pub_shipinhao.py` flow:
music uses a different route, different validation, and a different final
button.

## What This Publishes

The page is a single-song publish flow, not an album-only publish flow.

Important distinction:

- Final action: `发表音乐`
- Core object: one song/audio track
- Required surrounding metadata: album-style fields, including `专辑名称`,
  `专辑封面`, and `专辑简介`

So the automation should treat each ZIP package as one music publish, while
also filling the album fields for the song.

## Live Hosts And Repos

- Local AutoPublish submodule:
  `/home/lachlan/DiskMech/Projects/lazyedit/AutoPublish`
- Live AutoPublish host:
  `lachlan@lazyingart`
- Live AutoPublish path:
  `~/Projects/autopub`
- Live AutoPublish tmux session:
  `autopub`
- Live API:
  `http://lazyingart:8081/publish`
- Shipinhao browser debug port:
  `5006`

Deploy after local changes:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit/AutoPublish
python -m py_compile pub_shipinhao_music.py app.py autopub.py
git add pub_shipinhao_music.py docs/SHIPINHAO_MUSIC_PUBLISH_WORKFLOW.md
git commit -m "document shipinhao music publish workflow"
git push origin main

ssh lachlan@lazyingart
cd ~/Projects/autopub
git pull origin main
```

## Route

Use the direct create route first:

```text
https://channels.weixin.qq.com/platform/post/createMusic
```

It may redirect to:

```text
https://channels.weixin.qq.com/micro/content/post/createMusic
```

Do not use the normal video route for music:

```text
https://channels.weixin.qq.com/platform/post/create
```

The normal video route opens `发表动态` and will never expose the music form.

## Page Readiness

The music form is ready when the page has any of:

- audio file input accepting `audio/x-wav`, `audio/mpeg`, or `audio/flac`
- `歌曲名称`
- `歌词内容`
- `歌曲版本`
- `歌曲曲风`
- `专辑名称`
- `发表音乐`

Debug from the Pi:

```bash
ssh lachlan@lazyingart 'tmux capture-pane -pt autopub:0 -S -180 | tail -n 180'
curl -fsS http://lazyingart:8081/publish/queue | jq '.jobs[:8]'
```

Useful snapshots are saved under:

```text
~/Projects/autopub/logs/
```

For local inspection after copying:

```text
temp/shipinhao-music-debug/
```

## Required Fields Observed

The current music form requires or strongly expects:

- audio file
- `歌曲名称`
- `歌曲版本`
- `歌词内容`
- `歌曲曲风`
- language field labeled `语言` on the current page
- album cover
- `专辑名称`
- `专辑简介`
- agreement checkbox
- final `发表音乐` button enabled

Recommended values:

- `歌曲版本`: `完整版`
- `歌曲曲风`: use a Shipinhao-supported Chinese option. For Musia songs, use
  `流行` unless there is a clear better match.
- Mixed-language songs: use `中文` unless the song is clearly Japanese or
  English dominant.
- Japanese songs: use `日文` or `日语`, whichever appears in the dropdown.
- Artist / author / producer fields: `Musia 慕莎` is safe when no separate
  performer is provided.

## Audio Requirements

Shipinhao rejected an MP3 with this error:

```text
请上传码率不低于256kbps的音频, 当前为: 187.7kbps
```

For reliable upload, prefer WAV from Musia instead of MP3. MP3 is only safe if
it is definitely 256 kbps or higher.

Check audio before packaging:

```bash
ffprobe -hide_banner -select_streams a:0 \
  -show_entries stream=codec_name,sample_rate,channels,bit_rate \
  -of default=nk=1:nw=1 /path/to/audio.wav
```

## Covers

Shipinhao music uses a square album-cover crop flow. The current page opens a
`专辑封面编辑` overlay after uploading the image, and the overlay must be
confirmed with:

```text
确认
```

Do not wait for or click `完成` in that overlay. The final page button is
`发表音乐`.

Future LazyEdit packages should prefer square cover candidates for Shipinhao
music. Existing packages do not need to be regenerated solely for square cover
if the user says not to regenerate; use the crop confirmation instead.

## Proof Materials / 原创证明

If Shipinhao asks for proof material or exposes the archive upload input
accepting `.zip` or `.rar`, use Musia-generation evidence, not a generic cover
image.

For 原创证明, prefer evidence that shows the song identity and that it belongs to
the Musia/LazyingArt workflow:

- screenshot from the Musia/Fun Lazying Art website page for the song, if it
  clearly shows the song title, player, lyrics, or public context. This is often
  the best "original proof" because it shows the public song identity.
- screenshot from the Musia webapp showing the prompt/message or generation
  session for the song. This is supporting proof for how the original work was
  created.
- song title and local project path
- lyric JSON or Markdown source
- short `README.txt` saying the song is an original Musia/LazyingArt generated
  work by Lachlan Chen / Musia 慕莎

Package these as a zip/rar and upload them only when the proof field is visible
or validation requires it. Do not confuse proof material with the album cover.

Suggested zip layout:

```text
proof/
  README.txt
  musia-webapp-generation-screenshot.png
  fun-lazying-art-song-page-screenshot.png
  lyrics.json
  prompt-or-run-note.md
```

## LazyEdit Package Contract

LazyEdit should create the music ZIP. AutoPublish consumes the ZIP.

Minimum expected contents:

```text
audio file, preferably WAV
metadata.json
lyrics.txt or lyrics.json
manifest.json
covers/
```

Example LazyEdit package command:

```bash
cd /home/lachlan/DiskMech/Projects/lazyedit
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lazyedit

python scripts/lazyedit_music_package.py \
  --audio /home/lachlan/ProjectsLFS/Musia/path/to/song.wav \
  --title "Song Title" \
  --author "Musia 慕莎" \
  --language 中文 \
  --genre 流行 \
  --story "Short music story for 音乐人说." \
  --lyrics-json /home/lachlan/ProjectsLFS/Musia/path/to/lyrics.json \
  --cover /home/lachlan/ProjectsLFS/Musia/path/to/cover.png \
  --cover-video /home/lachlan/ProjectsLFS/Musia/path/to/related-video.mp4 \
  --cover-count 9 \
  --output-slug song-title-music
```

Post the package to AutoPublish as a music task:

```bash
curl -fsS -X POST http://lazyingart:8081/publish \
  -F "file=@/path/to/song-title-music.zip" \
  -F "platforms=shipinhao" \
  -F "publish_shipinhao_music=true"
```

## Automation Caveats

- The final submit button is exactly `发表音乐`.
- A button with class `weui-desktop-btn_disabled` is disabled even if Selenium
  says the DOM button exists.
- The cover-crop overlay has a visible `确认` button that must be clicked.
- Broad DOM clicks can disturb form state. Selection helpers must target the
  label scope and then the visible dropdown option.
- After cover confirmation, re-check core fields (`歌曲名称`, lyrics,
  `专辑名称`, `专辑简介`) before final submission, because bad dropdown clicks
  can clear or focus fields unexpectedly.
- Do not publish the next song until the current song is either confirmed done
  or failed with a captured snapshot.

## Current Musia Defaults

For Musia songs:

- Author/artist: `Musia 慕莎`
- Real-name fallback if required: `陈荣周`
- Genre default on Shipinhao: `流行`
- Mixed-language default: `中文`
- Japanese-dominant default: `日文` / `日语`
- Proof source: Musia webapp screenshot showing the generation prompt/messages,
  or the Musia/Fun Lazying Art website screenshot when it better proves the song
  identity and public context
