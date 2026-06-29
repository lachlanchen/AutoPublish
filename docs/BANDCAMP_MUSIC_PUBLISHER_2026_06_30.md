# Bandcamp Music Publisher

Date: 2026-06-30

`pub_bandcamp_music.py` is a guarded Bandcamp publisher for LazyEdit music
packages. It is meant for first-run login/account setup, draft creation, and
eventual controlled public release.

## Important Rules

- Use a real `.wav`, `.aif`, `.aiff`, or `.flac` source for Bandcamp.
- Do not upload an MP3-derived WAV as a public Bandcamp master.
- LazyEdit packages expose this as `bandcamp_audio_filename`.
- First run should be `test=true`; let the user register or log in.
- AutoPublish opens/reuses the Bandcamp browser profile on port `5008`.
- The publisher fills metadata and tries to save a draft by default.
- It only clicks a public publish/release button when:

```bash
export BANDCAMP_PUBLISH_PUBLIC=1
```

Keep that env var unset until payment, price, account, and release settings are
manually verified.

If Bandcamp sends the logged-in account to a specific upload/dashboard page,
set:

```bash
export BANDCAMP_UPLOAD_URL='https://...'
```

## LazyEdit CLI Example

```bash
python scripts/lazyedit_music_package.py \
  --audio song-preview-or-shipinhao.mp3 \
  --bandcamp-audio song-master.wav \
  --title "Song Title" \
  --lyrics-file corrected-lyrics.txt \
  --cover cover-square.png \
  --platforms bandcamp_music \
  --post \
  --test
```

When the Bandcamp account is ready and the form has been verified, rerun
without `--test`. Public publishing still requires `BANDCAMP_PUBLISH_PUBLIC=1`.

