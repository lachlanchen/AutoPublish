[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# AutoPublish

> 🌍 **ローカライズ状況（このワークスペースで 2026年2月28日 に確認）:**
> `i18n/` は多言語 README の配置先です。英語版（`README.md`）を基準に、各翻訳版は運用ドキュメントとして内容の完全性を保つ方針です。

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#prerequisites)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#system-overview)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#running-the-tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#platform-specific-notes)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#running-the-tornado-service-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-ar%20%7C%20de%20%7C%20es%20%7C%20fr%20%7C%20ja%20%7C%20ko%20%7C%20ru%20%7C%20vi%20%7C%20zh--Hans%20%7C%20zh--Hant-0EA5E9)](#table-of-contents)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#license)

短尺動画コンテンツを中国および海外の複数クリエイタープラットフォームへ配信するための自動化ツールキットです。Tornado ベースのサービス、Selenium 自動化ボット、ローカルのファイル監視ワークフローを組み合わせ、`videos/` に動画を置くと最終的に XiaoHongShu、Douyin、Bilibili、WeChat Channels（ShiPinHao）、Instagram、必要に応じて YouTube へ投稿されます。

このリポジトリは意図的に低レベルです。設定の多くは Python ファイルとシェルスクリプトにあります。本ドキュメントはセットアップ、実行、拡張ポイントを扱う運用マニュアルです。

> ⚙️ **運用思想**: 抽象化レイヤーを隠すより、明示的なスクリプトと直接的なブラウザ自動化を優先します。  
> ✅ **README の正本ポリシー**: 技術情報の完全性を維持しつつ、可読性と発見性を高めます。

## Start Here

このリポジトリを初めて触る場合は、次の順で進めてください。

1. [Prerequisites](#prerequisites) と [Installation](#installation) を読む。
2. [Configuration](#configuration) でシークレットと絶対パスを設定する。
3. [Preparing Browser Sessions](#preparing-browser-sessions) でブラウザのデバッグセッションを準備する。
4. [Usage](#usage) から実行モードを選ぶ: `autopub.py`（watcher）または `app.py`（API queue）。
5. [Examples](#examples) のコマンドで動作確認する。

## Overview

AutoPublish は現在、次の 2 つの本番運用モードをサポートしています。

1. フォルダ投入型の **CLI watcher mode (`autopub.py`)**
2. HTTP (`/publish`, `/publish/queue`) 経由で ZIP を受け付ける **API queue mode (`app.py`)**

抽象的なオーケストレーション基盤より、透明性の高いスクリプト主導ワークフローを好む運用者向けに設計されています。

### Runtime Modes at a Glance

| Mode | Entry point | Input | Best for | Output behavior |
| --- | --- | --- | --- | --- |
| CLI watcher | `autopub.py` | `videos/` へ投入されたファイル | ローカル運用者のワークフローや cron/service ループ | 検出した動画を処理し、選択プラットフォームへ即時投稿 |
| API queue service | `app.py` | `POST /publish` への ZIP アップロード | 上流システム連携やリモート起動 | ジョブを受理してキューに積み、ワーカー順に投稿を実行 |

### Platform Coverage Snapshot

| Platform | Publisher module | Login helper | Control port | CLI mode | API mode |
| --- | --- | --- | --- | --- | --- |
| XiaoHongShu | `pub_xhs.py` | `login_xiaohongshu.py` | `5003` | ✅ | ✅ |
| Douyin | `pub_douyin.py` | `login_douyin.py` | `5004` | ✅ | ✅ |
| Bilibili | `pub_bilibili.py` | N/A | `5005` | ✅ | ✅ |
| ShiPinHao (WeChat Channels) | `pub_shipinhao.py` | `login_shipinhao.py` | `5006` | Optional | ✅ |
| Instagram | `pub_instagram.py` | `login_instagram.py` | `5007` | Optional | ✅ |
| YouTube | `pub_y2b.py` | N/A | `9222` | Optional | ✅ |

## Quick Snapshot

| What | Value |
| --- | --- |
| Primary language | Python 3.10+ |
| Main runtimes | CLI watcher (`autopub.py`) + Tornado queue service (`app.py`) |
| Automation engine | Selenium + remote-debug Chromium sessions |
| Input formats | Raw videos (`videos/`) and ZIP bundles (`/publish`) |
| Current repo workspace path | `/home/lachlan/ProjectsLFS/AutoPublish` |
| Ideal users | マルチプラットフォーム短尺動画パイプラインを扱うクリエイター/運用エンジニア |

### Operational Safety Snapshot

| Topic | Current state | Action |
| --- | --- | --- |
| Hard-coded paths | 複数モジュール/スクリプトに存在 | 本番運用前にホストごとにパス定数を更新 |
| Browser login state | 必須 | プラットフォームごとに永続 remote-debug プロファイルを維持 |
| Captcha handling | 任意の連携あり | 必要に応じて 2Captcha/Turing 認証情報を設定 |
| License declaration | ルート `LICENSE` ファイル未検出 | 再配布前にメンテナーへ利用条件を確認 |

### Compatibility & Assumptions

| Item | Current assumption in this repo |
| --- | --- |
| Python | 3.10+ |
| Runtime environment | Chromium を GUI で動かせる Linux desktop/server |
| Browser control mode | 永続プロファイルディレクトリを使う remote debugging sessions |
| Primary API port | `8081`（`app.py --port`） |
| Processing backend | `upload_url` + `process_url` が到達可能で、有効な ZIP を返すこと |
| Workspace used for this draft | `/home/lachlan/ProjectsLFS/AutoPublish` |

---

## Table of Contents

- [Start Here](#start-here)
- [Overview](#overview)
- [Runtime Modes at a Glance](#runtime-modes-at-a-glance)
- [Platform Coverage Snapshot](#platform-coverage-snapshot)
- [Quick Snapshot](#quick-snapshot)
- [Operational Safety Snapshot](#operational-safety-snapshot)
- [Compatibility & Assumptions](#compatibility--assumptions)
- [System Overview](#system-overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Configuration Verification Checklist](#configuration-verification-checklist)
- [Preparing Browser Sessions](#preparing-browser-sessions)
- [Usage](#usage)
- [Examples](#examples)
- [Metadata & ZIP Format](#metadata--zip-format)
- [Data & Artifact Lifecycle](#data--artifact-lifecycle)
- [Platform-Specific Notes](#platform-specific-notes)
- [Raspberry Pi / Linux Service Setup](#raspberry-pi--linux-service-setup)
- [Legacy macOS Scripts](#legacy-macos-scripts)
- [Troubleshooting & Maintenance](#troubleshooting--maintenance)
- [FAQ](#faq)
- [Extending the System](#extending-the-system)
- [Quick Start Checklist](#quick-start-checklist)
- [Development Notes](#development-notes)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security & Ops Checklist](#security--ops-checklist)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Support](#support-autopublish)

---

## System Overview

🎯 **生メディアから公開投稿までのエンドツーエンドフロー**:

全体の流れ:

1. **素材取り込み**: `videos/` に動画を配置します。watcher（`autopub.py` またはスケジューラ/service）が `videos_db.csv` と `processed.csv` を使って新規ファイルを検出します。
2. **アセット生成**: `process_video.VideoProcessor` がファイルをコンテンツ処理サーバー（`upload_url` と `process_url`）へ送信し、以下を含む ZIP パッケージを受け取ります。
   - 編集/エンコード済み動画（`<stem>.mp4`）
   - カバー画像
   - ローカライズ済みタイトル・説明・タグ等を含む `{stem}_metadata.json`
3. **投稿**: メタデータをもとに `pub_*.py` の Selenium パブリッシャーが実行されます。各パブリッシャーは remote debugging port と永続 user-data directory を使い、すでに起動中の Chromium/Chrome セッションへ接続します。
4. **Web コントロールプレーン（任意）**: `app.py` が `/publish` を公開し、事前生成 ZIP を受け付けて展開し、同じパブリッシャーへジョブ投入します。ブラウザセッション更新やログイン補助（`login_*.py`）も起動できます。
5. **補助モジュール**: `load_env.py` は `~/.bashrc` から秘密情報を読み込み、`utils.py` は共通ヘルパー（ウィンドウフォーカス、QR 処理、メール補助）を提供し、`solve_captcha_*.py` は captcha 発生時に Turing/2Captcha と連携します。

## Features

✨ **実運用重視のスクリプトファースト自動化**:

- マルチプラットフォーム投稿: XiaoHongShu、Douyin、Bilibili、ShiPinHao（WeChat Channels）、Instagram、YouTube（任意）。
- 2 つの運用モード:
  - CLI watcher pipeline（`autopub.py`）
  - API queue service（`app.py` + `/publish` + `/publish/queue`）
- `ignore_*` ファイルによるプラットフォーム単位の一時停止スイッチ。
- 永続プロファイルを使った remote-debugging ブラウザセッション再利用。
- 任意の QR/captcha 自動化およびメール通知ヘルパー。
- 同梱 PWA（`pwa/`）アップローダ UI はフロントエンドビルド不要。
- Linux/Raspberry Pi 向けサービスセットアップスクリプト（`scripts/`）。

### Feature Matrix

| Capability | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Input source | ローカル `videos/` watcher | `POST /publish` 経由の ZIP アップロード |
| Queueing | ファイルベースの内部進行 | 明示的なインメモリジョブキュー |
| Platform flags | CLI 引数（`--pub-*`）+ `ignore_*` | クエリ引数（`publish_*`）+ `ignore_*` |
| Best fit | 単一ホストの運用者ワークフロー | 外部システム連携・リモートトリガー |

---

## Project Structure

ソース/実行時レイアウト（上位）:

```text
AutoPublish/
├── README.md
├── app.py
├── autopub.py
├── process_video.py
├── load_env.py
├── utils.py
├── pub_*.py                  # platform publishers
├── login_*.py                # platform login/session helpers
├── solve_captcha_*.py
├── smtp.py
├── smtp_test_simple.py
├── send_email_qreader.py
├── requirements.txt
├── requirements.autopub.txt
├── .env.example
├── setup_raspberrypi.md
├── scripts/
├── pwa/
├── figs/
├── .github/FUNDING.yml
├── i18n/                     # multilingual READMEs (currently includes Arabic and Spanish)
├── archived/
├── videos/                   # runtime input artifacts
├── logs/, logs-autopub/      # runtime logs
├── temp/, temp_screenshot/   # runtime temp artifacts
├── videos_db.csv
└── processed.csv
```

補足: `transcription_data/` は処理/投稿フロー実行時に利用され、実行後に作成される場合があります。

## Repository Layout

🗂️ **主要モジュールと役割**:

| Path | Purpose |
| --- | --- |
| `app.py` | `/publish` と `/publish/queue` を公開する Tornado サービス。内部投稿キューとワーカースレッドを含みます。 |
| `autopub.py` | CLI watcher。`videos/` を走査し、新規ファイルを処理して並列でパブリッシャーを呼び出します。 |
| `process_video.py` | 動画を処理バックエンドへ送信し、返却された ZIP バンドルを保存します。 |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | プラットフォーム別 Selenium 自動化モジュール。 |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | セッション確認と QR ログインフロー。 |
| `utils.py` | 共通自動化ヘルパー（ウィンドウフォーカス、QR/メール補助、診断補助）。 |
| `load_env.py` | シェルプロファイル（`~/.bashrc`）から環境変数を読み込み、機密情報ログをマスクします。 |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | SMTP/SendGrid 補助およびテストスクリプト。 |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Captcha ソルバー連携。 |
| `scripts/` | サービスセットアップと運用スクリプト（Raspberry Pi/Linux + legacy automation）。 |
| `pwa/` | ZIP プレビューと投稿送信用の静的 PWA。 |
| `setup_raspberrypi.md` | Raspberry Pi プロビジョニング手順。 |
| `.env.example` | 環境変数テンプレート（認証情報、パス、captcha キー）。 |
| `.github/FUNDING.yml` | スポンサー/資金設定。 |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | 実行時成果物とログ（多くは gitignore 対象）。 |

---

## Prerequisites

🧰 **初回実行前に以下をインストールしてください。**

### Operating system and tools

- X セッション付き Linux desktop/server（提供スクリプトでは `DISPLAY=:1` が一般的）。
- Chromium/Chrome と対応する ChromeDriver。
- GUI/メディア補助: `xdotool`、`ffmpeg`、`zip`、`unzip`。
- Python 3.10+（venv または Conda）。

### Python dependencies

最小ランタイムセット:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

リポジトリ準拠:

```bash
python -m pip install -r requirements.txt
```

軽量サービスインストール（セットアップスクリプト既定）:

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` には次が含まれます。
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Optional: create a sudo user

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## Installation

🚀 **クリーン環境からのセットアップ**:

1. リポジトリをクローン:

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. 仮想環境を作成して有効化（`venv` 例）:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. 環境変数を準備:

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. シェルプロファイル依存の値を読むスクリプト向けに変数をロード:

```bash
source ~/.bashrc
python load_env.py
```

補足: `load_env.py` は `~/.bashrc` 前提で設計されています。別プロファイルを使う場合は適宜調整してください。

---

## Configuration

🔐 **認証情報を設定し、ホスト固有パスを確認します。**

### Environment variables

本プロジェクトは認証情報や任意のブラウザ/ランタイムパスを環境変数から受け取ります。`.env.example` を起点にしてください。

| Variable | Description |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | QR/ログイン通知向け SMTP 認証情報。 |
| `SENDGRID_API_KEY` | SendGrid API を使うメールフロー向けキー。 |
| `APIKEY_2CAPTCHA` | 2Captcha API キー。 |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Turing captcha 認証情報。 |
| `DOUYIN_LOGIN_PASSWORD` | Douyin 二段階認証補助。 |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Instagram/ブラウザドライバの上書き設定。 |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | `app.py` 側のグローバル browser/driver/display 上書き設定。 |

### Path constants (important)

📌 **最も多い起動失敗要因**: ハードコードされた絶対パスの未調整。

複数モジュールにはまだハードコードされたパスがあります。利用ホスト向けに更新してください。

| File | Constant(s) | Meaning |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | API サービスのルートとバックエンド endpoint。 |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | CLI watcher のルートとバックエンド endpoint。 |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Python/Conda/repo/log の絶対パス。 | legacy/macOS 寄りラッパー。 |
| `utils.py` | カバー処理ヘルパーの FFmpeg パス前提。 | メディアツールパス互換性。 |

リポジトリ重要メモ:
- このワークスペースでの現在のリポジトリパスは `/home/lachlan/ProjectsLFS/AutoPublish` です。
- 一部コードやスクリプトは依然として `/home/lachlan/Projects/auto-publish` や `/Users/lachlan/...` を参照します。
- 本番運用前に必ずローカル環境へ合わせて調整してください。

### Platform toggles via `ignore_*`

🧩 **即時セーフティスイッチ**: `ignore_*` ファイルを作成すると、コード修正なしで該当パブリッシャーを無効化できます。

公開フラグは ignore ファイルでも制御されます。無効化したい場合は空ファイルを作成します。

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

再有効化するには対応ファイルを削除します。

### Configuration Verification Checklist

`.env` とパス定数を設定した後、次の簡易チェックを実行してください。

```bash
python -c "import os;print('AUTOPUBLISH_BROWSER_BIN=', os.getenv('AUTOPUBLISH_BROWSER_BIN'));print('AUTOPUBLISH_CHROMEDRIVER=', os.getenv('AUTOPUBLISH_CHROMEDRIVER'));print('DISPLAY=', os.getenv('DISPLAY') or os.getenv('AUTOPUBLISH_DISPLAY'))"
python -c "from load_env import load_env_from_bashrc; load_env_from_bashrc(); print('Environment load OK')"
python -c "import os; p=os.getenv('AUTOPUBLISH_CHROMEDRIVER') or os.getenv('CHROMEDRIVER_PATH') or '/usr/bin/chromedriver'; print(p, 'exists=', os.path.exists(p))"
```

値が不足している場合は、実行前に `.env`、`~/.bashrc`、またはスクリプト内定数を修正してください。

---

## Preparing Browser Sessions

🌐 **安定した Selenium 投稿にはセッション永続化が必須です。**

1. 専用プロファイルフォルダを作成:

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. remote debugging 付きでブラウザセッションを起動（XiaoHongShu 例）:

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. 各プラットフォーム/プロファイルで初回のみ手動ログイン。

4. Selenium が接続できることを確認:

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Security note:
- `app.py` にはブラウザ再起動ロジックで使われるハードコード sudo パスワードのプレースホルダー（`password = "1"`）が現状含まれます。実運用前に必ず置き換えてください。

---

## Usage

▶️ **実行モードは 2 つ**: CLI watcher と API queue service。

### Running the CLI pipeline (`autopub.py`)

1. 監視ディレクトリ（`videos/` または設定済み `autopublish_folder_path`）へ元動画を配置。
2. 実行:

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Flags:

| Flag | Meaning |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | 投稿先を指定。何も渡さない場合は 3 つすべて有効が既定。 |
| `--test` | パブリッシャーへ test mode を渡します（挙動はプラットフォーム実装ごとに異なる）。 |
| `--use-cache` | `transcription_data/<video>/<video>.zip` があれば再利用。 |

動画ごとの CLI フロー:
- `process_video.py` で upload/process。
- ZIP を `transcription_data/<video>/` へ展開。
- `ThreadPoolExecutor` で選択パブリッシャーを起動。
- `videos_db.csv` と `processed.csv` に追跡状態を追記。

### Running the Tornado service (`app.py`)

🛰️ **API mode** は ZIP を生成する外部システム連携に有効です。

サーバー起動:

```bash
python app.py --refresh-time 1800 --port 8081
```

### `POST /publish`

📤 **ZIP バイト列を直接送信して投稿ジョブをキュー投入**。

- Header: `Content-Type: application/octet-stream`
- 必須 query/form 引数: `filename`（ZIP ファイル名）
- 任意 boolean: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: 生 ZIP bytes

例:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

現行コードでの挙動:
- リクエストは受理され、キューに投入されます。
- 即時レスポンスは `status: queued`、`job_id`、`queue_size` を含む JSON。
- ワーカースレッドがキューを直列処理。

### `GET /publish/queue`

📊 **キュー健全性と実行中ジョブを観測**。

キュー状態/履歴 JSON を返します:

```bash
curl "http://localhost:8081/publish/queue"
```

レスポンス項目例:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Browser refresh thread

♻️ 長時間稼働時の stale session 障害を減らすため、定期ブラウザ更新を行います。

`app.py` は `--refresh-time` 間隔でバックグラウンド更新スレッドを動かし、ログインチェックへ連携します。更新待機にはランダム遅延挙動が含まれます。

### PWA frontend (`pwa/`)

🖥️ ZIP 手動アップロードとキュー確認のための軽量静的 UI。

ローカル起動:

```bash
cd pwa
python -m http.server 5173
```

`http://localhost:5173` を開き、backend base URL（例: `http://lazyingart:8081`）を設定します。

PWA の機能:
- ZIP のドラッグ&ドロッププレビュー。
- 投稿先トグル + test mode。
- `/publish` 送信と `/publish/queue` ポーリング。

---

## Examples

🧪 **そのまま使えるスモークテストコマンド**:

### Example 0: 環境をロードして API サーバー起動

```bash
source ~/.bashrc
python load_env.py
python app.py --refresh-time 1800 --port 8081
```

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

📦 **ZIP 契約は重要**: ファイル名とメタデータキーをパブリッシャー期待値に合わせてください。

想定 ZIP 内容（最小）:

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` は CN 系パブリッシャーで使用されます。任意の `metadata["english_version"]` は YouTube パブリッシャーで使用されます。

モジュールでよく使うフィールド:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags`（ハッシュタグ配列）
- `video_filename`, `cover_filename`
- 各 `pub_*.py` 実装にあるプラットフォーム固有フィールド

外部で ZIP を生成する場合も、キーとファイル名をモジュール側の期待に合わせてください。


## Data & Artifact Lifecycle

パイプラインは、運用者が意図的に保持・ローテーション・クリーンアップすべきローカル成果物を生成します。

| Artifact | Location | Produced by | Why it matters |
| --- | --- | --- | --- |
| Input videos | `videos/` | 手動投入または上流同期 | CLI watcher モードの入力素材 |
| Processing ZIP output | `transcription_data/<stem>/<stem>.zip` | `process_video.py` | `--use-cache` で再利用可能なペイロード |
| Extracted publish assets | `transcription_data/<stem>/...` | `autopub.py` / `app.py` の ZIP 展開 | 投稿可能なファイルとメタデータ |
| Publish logs | `logs/`, `logs-autopub/` | CLI/API 実行時 | 障害切り分けと監査証跡 |
| Browser logs | `~/chromium_dev_session_logs/*.log`（または chrome prefix） | ブラウザ起動スクリプト | セッション/ポート/起動問題の診断 |
| Tracking CSVs | `videos_db.csv`, `processed.csv` | CLI watcher | 重複処理の防止 |

運用上の推奨:
- ディスク逼迫を防ぐため、古い `transcription_data/`、`temp/`、ログを定期アーカイブ/削除してください。

---

## Platform-Specific Notes

🧭 **各パブリッシャーのポート対応とモジュール責務**。

| Platform | Port | Module(s) | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | QR 再ログインフローあり。メタデータのタイトル整形とハッシュタグを使用。 |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | アップロード完了判定と再試行経路は壊れやすいため、ログ監視を推奨。 |
| Bilibili | 5005 | `pub_bilibili.py` | `solve_captcha_2captcha.py` と `solve_captcha_turing.py` で captcha 連携可能。 |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | セッション更新の信頼性のため QR 承認を迅速に行うことが重要。 |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | API mode では `publish_instagram=true` で制御。`.env.example` に環境変数あり。 |
| YouTube | 9222 | `pub_y2b.py` | `english_version` メタデータブロックを使用。`ignore_y2b` で無効化。 |

---

## Raspberry Pi / Linux Service Setup

🐧 **常時稼働ホスト向けの推奨構成**。

ホスト全体のブートストラップは [`setup_raspberrypi.md`](../setup_raspberrypi.md) を参照してください。

クイックセットアップ:

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

この処理で以下を順に実行します。
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

tmux で手動起動:

```bash
./scripts/start_autopub_tmux.sh
```

サービス/ポート確認:

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## Legacy macOS Scripts

🍎 旧ローカル環境との互換性のため legacy ラッパーを残しています。

リポジトリには次の macOS 向け legacy ラッパーが残っています。
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

これらは絶対パス `/Users/lachlan/...` と Conda 前提を含みます。そのワークフローを使う場合は維持し、ホストに合わせてパス/venv/ツール設定を更新してください。

---

## Troubleshooting & Maintenance

🛠️ **障害時はまずここを確認してください。**

- **シークレット衛生**: push 前に `~/.local/bin/detect-secrets scan` を実行し、漏洩した認証情報はローテーションします。
- **処理バックエンドエラー**: `process_video.py` で “Failed to get the uploaded file path,” が出る場合、upload 応答 JSON に `file_path` があるか、process endpoint が ZIP bytes を返すか確認してください。
- **ChromeDriver 不一致**: DevTools 接続エラーが出る場合、Chrome/Chromium と driver のバージョンを揃える（または `webdriver-manager` に切替）必要があります。
- **ブラウザフォーカス不良**: `bring_to_front` はウィンドウタイトル一致に依存するため、Chromium/Chrome の命名差で失敗することがあります。
- **Captcha 中断**: 2Captcha/Turing 認証情報を設定し、必要箇所で solver 出力を統合してください。
- **古いロックファイル**: 定期実行が開始しない場合、プロセス状態を確認し、古い `autopub.lock`（legacy script flow）を削除してください。
- **確認すべきログ**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log`, および service journal logs。


## FAQ

**Q: API mode と CLI watcher mode を同時に実行できますか？**  
A: 可能ですが、入力ディレクトリとブラウザセッションを厳密に分離しない限り推奨しません。両モードが同じ publisher・ファイル・ポートを奪い合う可能性があります。

**Q: `/publish` が queued を返すのに、投稿が始まりません。**  
A: `app.py` はまずジョブをキュー投入し、その後バックグラウンドワーカーが直列処理します。`/publish/queue`、`is_publishing`、サービスログを確認してください。

**Q: `.env` を使っていても `load_env.py` は必要ですか？**  
A: `start_autopub_tmux.sh` は `.env` を読み込みますが、直接実行ではシェル環境依存のケースがあります。`.env` とシェル exports を一致させるのが安全です。

**Q: API アップロードで必要な最小 ZIP 契約は？**  
A: `{stem}_metadata.json` と、メタデータキー（`video_filename`, `cover_filename`）に一致する動画/カバーファイルを含む有効な ZIP です。

**Q: headless mode はサポートされていますか？**  
A: 一部モジュールに headless 関連変数はありますが、このリポジトリの主運用モードは GUI 付き永続ブラウザセッションです。

---

## Extending the System

🧱 **新規プラットフォーム追加と運用強化の拡張ポイント**。

- **新規プラットフォーム追加**: 既存 `pub_*.py` を複製し selector/flow を調整。QR 再認証が必要なら `login_*.py` を追加し、`app.py` の flags/queue 処理と `autopub.py` の CLI 配線へ統合します。
- **設定抽象化**: 分散した定数を構造化設定（`config.yaml`/`.env` + typed model）へ移行し、マルチホスト運用を容易にします。
- **認証情報保護強化**: ハードコードやシェル露出に依存する機密フローを、より安全な secret 管理（`sudo -A`、keychain、vault/secret manager）へ置換します。
- **コンテナ化**: Chromium/ChromeDriver + Python runtime + virtual display を 1 つの配布単位にまとめ、クラウド/サーバー運用を簡素化します。

---

## Quick Start Checklist

✅ **最短で最初の投稿成功まで進む手順**。

1. このリポジトリをクローンし、依存関係をインストール（`pip install -r requirements.txt` または軽量 `requirements.autopub.txt`）。
2. `app.py`、`autopub.py`、使用する各スクリプトのハードコードパス定数を更新。
3. 必須認証情報をシェルプロファイルまたは `.env` に設定し、`python load_env.py` で読み込み確認。
4. remote-debug 用ブラウザプロファイルフォルダを作成し、必要な各プラットフォームセッションを一度起動。
5. 各投稿先プラットフォームで手動サインイン。
6. API mode（`python app.py --port 8081`）または CLI mode（`python autopub.py --use-cache ...`）を起動。
7. サンプル ZIP（API）またはサンプル動画（CLI）を 1 件流し、`logs/` を確認。
8. push 前に必ずシークレットスキャンを実施。

---

## Development Notes

🧬 **現行開発ベースライン**（手動整形 + スモークテスト）。

- Python スタイルは既存の 4 スペースインデントと手動整形に従います。
- 公式の自動テストスイートは現状ありません。次のスモークテストを実施してください。
  - `autopub.py` でサンプル動画 1 本を処理。
  - `/publish` に ZIP 1 件を投稿し `/publish/queue` を監視。
  - 各投稿先プラットフォームで手動検証。
- 新規スクリプト追加時は、短い dry-run 用に `if __name__ == "__main__":` エントリポイントを付けてください。
- プラットフォーム変更は可能な限り局所化（`pub_*`, `login_*`, `ignore_*` toggles）。
- 実行時成果物（`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`）はローカル前提で、多くが git では無視されます。

---

## Roadmap

🗺️ **現行コード制約を踏まえた優先改善項目**。

現状構造と既存メモに基づく改善案:

1. 分散したハードコードパスを集中設定（`.env`/YAML + typed model）へ移行。
2. ハードコード sudo パスワードパターンを除去し、より安全なプロセス制御へ移行。
3. プラットフォームごとの再試行強化と UI 状態検出改善で投稿信頼性を向上。
4. 対応プラットフォーム拡張（例: Kuaishou など）。
5. ランタイムを再現性のある配布単位へパッケージ化（container + virtual display profile）。
6. ZIP 契約とキュー実行の自動統合チェックを追加。

---

## Contributing

🤝 PR は小さく再現可能にし、実行前提を明示してください。

コントリビューション歓迎です。

1. Fork して、焦点を絞ったブランチを作成。
2. コミットは小さく、命令形で統一（履歴例: “Wait for YouTube checks before publishing”）。
3. PR には手動検証メモを含めてください。
   - 環境前提
   - ブラウザ/セッション再起動有無
   - UI フロー変更に関連するログ/スクリーンショット
4. 実シークレットをコミットしない（`.env` は ignore。形は `.env.example` で管理）。

新しい publisher module を追加する場合、以下すべてを配線してください。
- `pub_<platform>.py`
- optional `login_<platform>.py`
- `app.py` の API flags と queue handling
- 必要に応じた `autopub.py` の CLI wiring
- `ignore_<platform>` toggle handling
- README 更新


## Security & Ops Checklist

本番相当の実行前に、以下を確認してください。

1. `.env` がローカルに存在し、git 追跡されていないこと。
2. 過去にコミットされた可能性のある認証情報をローテーション/削除したこと。
3. コード内のプレースホルダー機密値（例: `app.py` の sudo パスワード仮値）を置き換えたこと。
4. バッチ実行前に `ignore_*` スイッチの有効/無効を意図どおり確認したこと。
5. ブラウザプロファイルがプラットフォームごとに分離され、最小権限アカウントを使っていること。
6. 共有前ログにシークレットが含まれていないこと。
7. push 前に `detect-secrets`（同等ツール可）を実行したこと。

---

<a id="support-autopublish"></a>
## ❤️ Support

| Donate | PayPal | Stripe |
|---|---|---|
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=ko-fi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

💖 コミュニティからの支援は、インフラ運用・信頼性向上・新規プラットフォーム統合を支える原資になります。

AutoPublish は、クロスプラットフォーム向けクリエイターツールをオープンで拡張可能に保つ取り組みの一部です。寄付は次を後押しします。

- Selenium farm、処理 API、クラウド GPU の継続運用。
- 新規 publisher（Kuaishou、Instagram Reels など）の実装と既存 bot の安定化。
- 個人クリエイター向けドキュメント、スターターデータセット、チュートリアルの拡充。

### Additional Donation Options

<div align="center">
<table style="margin:0 auto; text-align:center; border-collapse:collapse;">
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://chat.lazying.art/donate">https://chat.lazying.art/donate</a>
    </td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://chat.lazying.art/donate"><img src="../figs/donate_button.svg" alt="Donate" height="44"></a>
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
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><img alt="WeChat QR" src="../figs/donate_wechat.png" width="240"/></td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><img alt="Alipay QR" src="../figs/donate_alipay.png" width="240"/></td>
  </tr>
</table>
</div>

**支援 / Donate**

- ご支援はクリエイター自動化の研究・開発・運用コストを支える大きな力になります。
- 你的支持将用于服务器与研发，帮助作者持续开放改进跨平台发布工具链。
- Your support keeps the pipelines alive so more independent studios can publish everywhere with less busywork.

Also available via:
- GitHub Sponsors: <https://github.com/sponsors/lachlanchen>
- Project links: <https://lazying.art>, <https://chat.lazying.art>, <https://onlyideas.art>

---

## License

このリポジトリスナップショットには現在 `LICENSE` ファイルがありません。

この文書時点の扱い:
- メンテナーが明示的なライセンスファイルを追加するまで、利用・再配布条件は未定義として扱ってください。

推奨アクション:
- ルートに `LICENSE`（例: MIT/Apache-2.0/GPL-3.0）を追加し、このセクションを更新してください。

> 📝 ライセンスファイル追加前は、商用/社内再配布の前提を未確定として扱い、必ずメンテナーへ直接確認してください。

---

## Acknowledgements

- メンテナー兼スポンサー: [@lachlanchen](https://github.com/lachlanchen)
- 資金設定の出典: [`.github/FUNDING.yml`](../.github/FUNDING.yml)
- 本リポジトリで参照しているエコシステムサービス: Selenium, Tornado, SendGrid, 2Captcha, Turing captcha APIs.
