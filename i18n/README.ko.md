[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


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
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Arabic%20%7C%20Spanish-0EA5E9)](#table-of-contents)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#license)

짧은 영상 콘텐츠를 중국 및 글로벌 크리에이터 플랫폼 여러 곳에 배포하기 위한 자동화 툴킷입니다. 이 프로젝트는 Tornado 기반 서비스, Selenium 자동화 봇, 로컬 파일 감시 워크플로를 결합해 `videos/` 폴더에 영상을 넣으면 최종적으로 샤오홍슈(XiaoHongShu), 도우인(Douyin), 빌리빌리(Bilibili), 위챗 채널(ShiPinHao), 인스타그램, 그리고 선택적으로 유튜브까지 업로드되도록 설계되어 있습니다.

이 저장소는 의도적으로 저수준(low-level) 구조를 유지합니다. 대부분의 설정은 Python 파일과 셸 스크립트에 직접 존재합니다. 이 문서는 설치, 실행, 확장 지점을 다루는 운영 매뉴얼입니다.

> ⚙️ **운영 철학**: 이 프로젝트는 숨겨진 추상화 레이어보다 명시적 스크립트와 직접적인 브라우저 자동화를 우선합니다.
> ✅ **이 README의 기준 정책**: 기술적 디테일은 보존하고, 가독성과 탐색성은 개선합니다.

## Start Here

이 저장소를 처음 사용하는 경우 아래 순서를 권장합니다.

1. [Prerequisites](#prerequisites)와 [Installation](#installation)을 읽습니다.
2. [Configuration](#configuration)에서 시크릿과 절대 경로를 설정합니다.
3. [Preparing Browser Sessions](#preparing-browser-sessions)에 따라 브라우저 디버그 세션을 준비합니다.
4. [Usage](#usage)에서 런타임 모드를 선택합니다: `autopub.py`(watcher) 또는 `app.py`(API queue).
5. [Examples](#examples)의 명령어로 검증합니다.

## Overview

AutoPublish는 현재 두 가지 프로덕션 런타임 모드를 지원합니다.

1. **CLI watcher 모드 (`autopub.py`)**: 폴더 기반 수집 및 게시.
2. **API queue 모드 (`app.py`)**: HTTP(`POST /publish`, `/publish/queue`) 기반 ZIP 게시.

추상화된 오케스트레이션 플랫폼보다, 투명하고 스크립트 중심인 워크플로를 선호하는 운영자를 위해 설계되었습니다.

### Runtime Modes at a Glance

| Mode | Entry point | Input | Best for | Output behavior |
| --- | --- | --- | --- | --- |
| CLI watcher | `autopub.py` | Files dropped into `videos/` | Local operator workflows and cron/service loops | Processes detected videos and publishes immediately to selected platforms |
| API queue service | `app.py` | ZIP upload to `POST /publish` | Integrations with upstream systems and remote triggering | Accepts jobs, enqueues them, and executes publishing in worker order |

## Quick Snapshot

| What | Value |
| --- | --- |
| Primary language | Python 3.10+ |
| Main runtimes | CLI watcher (`autopub.py`) + Tornado queue service (`app.py`) |
| Automation engine | Selenium + remote-debug Chromium sessions |
| Input formats | Raw videos (`videos/`) and ZIP bundles (`/publish`) |
| Current repo workspace path | `/home/lachlan/ProjectsLFS/AutoPublish` |
| Ideal users | Creators/ops engineers managing multi-platform short video pipelines |

### Operational Safety Snapshot

| Topic | Current state | Action |
| --- | --- | --- |
| Hard-coded paths | Present in multiple modules/scripts | Update path constants per host before production runs |
| Browser login state | Required | Keep persistent remote-debug profiles per platform |
| Captcha handling | Optional integrations available | Configure 2Captcha/Turing credentials if needed |
| License declaration | No top-level `LICENSE` file detected | Confirm usage terms with maintainer before redistribution |

---

## Table of Contents

- [Overview](#overview)
- [System Overview](#system-overview)
- [Features](#features)
- [Project Structure](#project-structure)
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
- [Acknowledgements](#acknowledgements)
- [Support AutoPublish](#support-autopublish)

---

## System Overview

🎯 **원본 미디어에서 게시 완료까지의 전체 흐름**:

전체 워크플로 요약:

1. **원본 영상 수집**: `videos/`에 영상을 넣습니다. watcher(`autopub.py` 또는 스케줄러/서비스)가 `videos_db.csv`, `processed.csv`를 사용해 새 파일을 감지합니다.
2. **에셋 생성**: `process_video.VideoProcessor`가 파일을 콘텐츠 처리 서버(`upload_url`, `process_url`)로 업로드하면, 다음이 포함된 ZIP 패키지를 반환합니다.
   - 편집/인코딩된 영상(`<stem>.mp4`),
   - 커버 이미지,
   - 로컬라이즈된 제목/설명/태그 등이 담긴 `{stem}_metadata.json`.
3. **게시**: 메타데이터를 기반으로 `pub_*.py` Selenium 게시 모듈이 동작합니다. 각 게시기는 원격 디버깅 포트와 영속 user-data 디렉터리를 통해 이미 실행 중인 Chromium/Chrome 인스턴스에 붙습니다.
4. **웹 컨트롤 플레인(선택)**: `app.py`가 `/publish`를 제공하고, 미리 생성된 ZIP 번들을 받아 압축 해제한 뒤 동일 게시 모듈 큐에 작업을 넣습니다. 브라우저 세션 갱신 및 로그인 헬퍼(`login_*.py`) 트리거도 가능합니다.
5. **보조 모듈**: `load_env.py`는 `~/.bashrc`에서 시크릿을 로드하고, `utils.py`는 공용 유틸(윈도우 포커스, QR 처리, 메일 유틸)을 제공합니다. 캡차가 나오면 `solve_captcha_*.py`로 Turing/2Captcha 연동이 가능합니다.

## Features

✨ **실용적인 스크립트 중심 자동화를 위해 설계됨**:

- 멀티 플랫폼 게시: XiaoHongShu, Douyin, Bilibili, ShiPinHao(WeChat Channels), Instagram, YouTube(선택).
- 두 가지 운영 모드: CLI watcher 파이프라인(`autopub.py`)과 API queue 서비스(`app.py` + `/publish` + `/publish/queue`).
- `ignore_*` 파일 기반 플랫폼별 임시 비활성화 스위치.
- 원격 디버깅 브라우저 세션 재사용(영속 프로필).
- 선택적 QR/캡차 자동화 및 이메일 알림 헬퍼.
- 포함된 PWA(`pwa/`) 업로더 UI는 프런트엔드 빌드가 필요 없음.
- Linux/Raspberry Pi 서비스 자동화 스크립트 제공(`scripts/`).

### Feature Matrix

| Capability | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Input source | Local `videos/` watcher | Uploaded ZIP via `POST /publish` |
| Queueing | Internal file-based progression | Explicit in-memory job queue |
| Platform flags | CLI args (`--pub-*`) + `ignore_*` | Query args (`publish_*`) + `ignore_*` |
| Best fit | Single-host operator workflow | External systems and remote triggering |

---

## Project Structure

상위 수준 소스/런타임 구조:

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

참고: `transcription_data/`는 처리/게시 런타임에서 사용되며, 실행 후 생성될 수 있습니다.

## Repository Layout

🗂️ **핵심 모듈과 역할**:

| Path | Purpose |
| --- | --- |
| `app.py` | `/publish`, `/publish/queue`를 제공하는 Tornado 서비스. 내부 게시 큐와 worker thread 포함. |
| `autopub.py` | CLI watcher: `videos/`를 스캔하고 새 파일을 처리한 뒤 게시 모듈을 병렬 호출. |
| `process_video.py` | 영상을 처리 백엔드로 업로드하고 반환된 ZIP 번들을 저장. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | 플랫폼별 Selenium 자동화 모듈. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | 세션 점검 및 QR 로그인 플로우. |
| `utils.py` | 공용 자동화 유틸(윈도우 포커스, QR/메일 헬퍼 유틸, 진단 유틸). |
| `load_env.py` | 셸 프로필(`~/.bashrc`)에서 env var를 불러오고 민감 로그를 마스킹. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | SMTP/SendGrid 헬퍼 및 테스트 스크립트. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | 캡차 해결 연동 모듈. |
| `scripts/` | 서비스 설치/운영 스크립트(Raspberry Pi/Linux + 레거시 자동화). |
| `pwa/` | ZIP 미리보기 및 게시 요청용 정적 PWA. |
| `setup_raspberrypi.md` | Raspberry Pi 프로비저닝 단계별 가이드. |
| `.env.example` | 환경 변수 템플릿(자격 증명, 경로, 캡차 키). |
| `.github/FUNDING.yml` | 스폰서/후원 설정. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | 런타임 아티팩트 및 로그(대부분 gitignore). |

---

## Prerequisites

🧰 **첫 실행 전에 아래 항목을 준비하세요.**

### Operating system and tools

- X 세션이 있는 Linux 데스크톱/서버(`DISPLAY=:1`이 제공 스크립트에서 자주 사용됨).
- Chromium/Chrome 및 버전이 맞는 ChromeDriver.
- GUI/미디어 유틸: `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv 또는 Conda).

### Python dependencies

최소 런타임 패키지:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

저장소 기준 일치 설치:

```bash
python -m pip install -r requirements.txt
```

경량 서비스 설치(기본 setup 스크립트에서 사용):

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` 포함 패키지:
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Optional: create a sudo user

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## Installation

🚀 **클린 머신 기준 설치 절차**:

1. 저장소를 클론합니다.

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. 가상환경을 만들고 활성화합니다(`venv` 예시).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. 환경 변수를 준비합니다.

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. 셸 프로필 값을 읽는 스크립트를 위해 변수를 로드합니다.

```bash
source ~/.bashrc
python load_env.py
```

참고: `load_env.py`는 `~/.bashrc`를 기준으로 작성되어 있습니다. 다른 셸 프로필을 사용한다면 이에 맞게 조정하세요.

---

## Configuration

🔐 **자격 증명을 설정한 뒤, 호스트별 경로를 확인하세요.**

### Environment variables

프로젝트는 환경 변수에서 자격 증명과 선택적 브라우저/런타임 경로를 읽습니다. `.env.example`에서 시작하세요.

| Variable | Description |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | QR/로그인 알림용 SMTP 자격 증명. |
| `SENDGRID_API_KEY` | SendGrid API 기반 메일 플로우용 키. |
| `APIKEY_2CAPTCHA` | 2Captcha API 키. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Turing 캡차 자격 증명. |
| `DOUYIN_LOGIN_PASSWORD` | Douyin 2차 인증 보조 값. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Instagram/브라우저 드라이버 오버라이드. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | `app.py`에서 우선 적용되는 전역 브라우저/드라이버/디스플레이 오버라이드. |

### Path constants (important)

📌 **가장 흔한 시작 실패 원인**: 해결되지 않은 하드코딩 절대 경로.

여러 모듈에 하드코딩 경로가 남아 있습니다. 실행 호스트 기준으로 수정하세요.

| File | Constant(s) | Meaning |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | API 서비스 루트 및 백엔드 엔드포인트. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | CLI watcher 루트 및 백엔드 엔드포인트. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Python/Conda/저장소/로그 절대 경로. | 레거시/macOS 지향 래퍼. |
| `utils.py` | 커버 처리 헬퍼의 FFmpeg 경로 가정. | 미디어 툴 경로 호환성. |

중요 저장소 메모:
- 현재 워크스페이스 저장소 경로는 `/home/lachlan/ProjectsLFS/AutoPublish`입니다.
- 일부 코드/스크립트는 여전히 `/home/lachlan/Projects/auto-publish` 또는 `/Users/lachlan/...`를 참조합니다.
- 프로덕션 사용 전 로컬 환경에 맞게 경로를 반드시 조정하세요.

### Platform toggles via `ignore_*`

🧩 **빠른 안전 스위치**: `ignore_*` 파일을 만들면 코드 수정 없이 해당 게시기를 비활성화할 수 있습니다.

게시 플래그는 ignore 파일에도 의해 게이트됩니다. 플랫폼을 끄려면 빈 파일을 생성하세요.

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

다시 활성화하려면 해당 파일을 삭제하면 됩니다.

---

## Preparing Browser Sessions

🌐 **안정적인 Selenium 게시를 위해 세션 지속성은 필수입니다.**

1. 플랫폼별 프로필 폴더를 만듭니다.

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. 원격 디버깅 옵션으로 브라우저 세션을 실행합니다(XiaoHongShu 예시).

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. 각 플랫폼/프로필별로 한 번 수동 로그인합니다.

4. Selenium attach 동작을 확인합니다.

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

보안 참고:
- `app.py`에는 브라우저 재시작 로직에 쓰이는 하드코딩 sudo 비밀번호 플레이스홀더(`password = "1"`)가 현재 존재합니다. 실제 배포 전 반드시 교체하세요.

---

## Usage

▶️ **런타임 모드는 두 가지**: CLI watcher와 API queue 서비스.

### Running the CLI pipeline (`autopub.py`)

1. 감시 디렉터리(`videos/` 또는 설정된 `autopublish_folder_path`)에 소스 영상을 넣습니다.
2. 아래 명령으로 실행합니다.

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

플래그:

| Flag | Meaning |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | 지정 플랫폼만 게시합니다. 아무것도 주지 않으면 기본으로 세 플랫폼 모두 활성화됩니다. |
| `--test` | 게시 모듈에 test 모드를 전달합니다(동작은 플랫폼별로 다름). |
| `--use-cache` | `transcription_data/<video>/<video>.zip`가 있으면 재사용합니다. |

영상별 CLI 처리 흐름:
- `process_video.py`를 통한 업로드/처리
- ZIP을 `transcription_data/<video>/`로 압축 해제
- `ThreadPoolExecutor`로 선택한 게시 모듈 실행
- `videos_db.csv`, `processed.csv`에 추적 상태 기록

### Running the Tornado service (`app.py`)

🛰️ **API 모드**는 ZIP 번들을 생성하는 외부 시스템 연동에 유용합니다.

서버 시작:

```bash
python app.py --refresh-time 1800 --port 8081
```

API 엔드포인트 요약:

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/publish` | `POST` | ZIP bytes를 업로드해 게시 작업 큐에 추가 |
| `/publish/queue` | `GET` | 큐, 작업 이력, 게시 상태 조회 |

### `POST /publish`

📤 **ZIP bytes 직접 업로드로 게시 작업을 큐잉**합니다.

- Header: `Content-Type: application/octet-stream`
- 필수 query/form arg: `filename`(ZIP 파일명)
- 선택 boolean: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: raw ZIP bytes

예시:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

현재 코드 동작:
- 요청을 수락하고 큐에 넣습니다.
- 즉시 `status: queued`, `job_id`, `queue_size`를 포함한 JSON을 반환합니다.
- worker thread가 큐를 직렬 처리합니다.

### `GET /publish/queue`

📊 **큐 상태와 진행 중 작업을 모니터링**합니다.

큐 상태/이력 JSON 반환:

```bash
curl "http://localhost:8081/publish/queue"
```

응답 필드 예:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Browser refresh thread

♻️ 장시간 실행 시 세션 만료로 인한 실패를 줄이기 위해 주기적 브라우저 리프레시를 수행합니다.

`app.py`는 `--refresh-time` 간격의 백그라운드 refresh thread를 실행하고 로그인 점검 훅과 연동합니다. refresh sleep에는 랜덤 지연 동작이 포함됩니다.

### PWA frontend (`pwa/`)

🖥️ 수동 ZIP 업로드와 큐 확인을 위한 경량 정적 UI입니다.

로컬 실행:

```bash
cd pwa
python -m http.server 5173
```

`http://localhost:5173`를 열고 백엔드 base URL(예: `http://lazyingart:8081`)을 입력하세요.

PWA 기능:
- ZIP drag/drop 미리보기
- 게시 대상 토글 + test mode
- `/publish` 제출 및 `/publish/queue` 폴링

---

## Examples

🧪 **바로 실행 가능한 스모크 테스트 명령어**:

### Example 0: Load environment and start API server

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

📦 **ZIP 계약 형식이 중요합니다**: 파일명과 메타데이터 키를 게시 모듈 기대값과 맞추세요.

기대 ZIP 내용(최소):

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata`는 CN 게시 모듈을 구동하며, 선택적으로 `metadata["english_version"]`는 YouTube 게시 모듈에서 사용됩니다.

모듈에서 자주 사용하는 필드:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags`(해시태그 리스트)
- `video_filename`, `cover_filename`
- `pub_*.py` 개별 구현에 따른 플랫폼 전용 필드

외부에서 ZIP을 생성하는 경우에도, 키와 파일명을 모듈 기대 형식에 맞춰 유지하세요.

---

## Platform-Specific Notes

🧭 플랫폼별 **포트 매핑 + 모듈 소유 관계**.

| Platform | Port | Module(s) | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | QR 재로그인 플로우, 메타데이터 기반 제목 정리 및 해시태그 처리. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | 업로드 완료 체크/재시도 경로가 플랫폼 변경에 취약하므로 로그를 면밀히 확인하세요. |
| Bilibili | 5005 | `pub_bilibili.py` | `solve_captcha_2captcha.py`, `solve_captcha_turing.py` 캡차 훅 사용 가능. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | 세션 리프레시 신뢰성을 위해 빠른 QR 승인 중요. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | API 모드에서 `publish_instagram=true`로 제어, `.env.example`에 env var 제공. |
| YouTube | 9222 | `pub_y2b.py` | `english_version` 메타데이터 블록 사용, `ignore_y2b`로 비활성화 가능. |

---

## Raspberry Pi / Linux Service Setup

🐧 **상시 실행 호스트에 권장되는 방식**.

전체 호스트 부트스트랩은 [`setup_raspberrypi.md`](setup_raspberrypi.md)를 따르세요.

빠른 파이프라인 설정:

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

이 스크립트는 아래를 순서대로 실행합니다.
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

tmux에서 수동 실행:

```bash
./scripts/start_autopub_tmux.sh
```

서비스/포트 검증:

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## Legacy macOS Scripts

🍎 과거 로컬 환경 호환을 위해 레거시 래퍼를 유지하고 있습니다.

저장소에는 다음 macOS 지향 레거시 래퍼가 남아 있습니다.
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

이들 스크립트는 `/Users/lachlan/...` 절대 경로와 Conda 환경을 가정합니다. 해당 워크플로를 계속 쓴다면 유지하되, 호스트 환경에 맞게 경로/venv/도구 체인을 업데이트하세요.

---

## Troubleshooting & Maintenance

🛠️ **문제가 생기면 먼저 여기부터 확인하세요.**

- **머신별 경로 드리프트**: `/Users/lachlan/...` 또는 `/home/lachlan/Projects/auto-publish` 누락 오류가 보이면, 상수 경로를 현재 호스트 경로(이 워크스페이스는 `/home/lachlan/ProjectsLFS/AutoPublish`)로 맞추세요.
- **시크릿 위생**: push 전 `~/.local/bin/detect-secrets scan` 실행. 유출된 자격 증명은 즉시 회전하세요.
- **처리 백엔드 오류**: `process_video.py`에서 “Failed to get the uploaded file path”가 나오면 업로드 응답 JSON에 `file_path`가 있는지, 처리 엔드포인트가 ZIP bytes를 반환하는지 확인하세요.
- **ChromeDriver 불일치**: DevTools 연결 오류가 발생하면 Chrome/Chromium과 driver 버전을 맞추거나 `webdriver-manager`를 사용하세요.
- **브라우저 포커스 문제**: `bring_to_front`는 윈도우 타이틀 매칭에 의존하므로 Chromium/Chrome 명명 차이로 깨질 수 있습니다.
- **캡차 중단**: 2Captcha/Turing 자격 증명을 설정하고 필요한 지점에 solver 출력 연동을 추가하세요.
- **오래된 lock 파일**: 스케줄 실행이 시작되지 않으면 프로세스 상태를 확인하고 오래된 `autopub.lock`을 제거하세요(레거시 스크립트 플로우).
- **확인할 로그**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log`, 그리고 서비스 journal 로그.

---

## Extending the System

🧱 **새 플랫폼 추가와 운영 안정성 강화를 위한 확장 지점**.

- **새 플랫폼 추가**: 기존 `pub_*.py`를 복제해 셀렉터/플로우를 수정하고, QR 재인증이 필요하면 `login_*.py`를 추가한 뒤 `app.py`(flags/queue)와 `autopub.py`(CLI wiring)에 연결합니다.
- **설정 추상화**: 흩어진 상수를 구조화된 설정(`config.yaml`/`.env` + 타입 모델)으로 이관해 멀티 호스트 운영을 단순화합니다.
- **자격 증명 저장 강화**: 하드코딩/셸 노출 민감 경로를 보안 시크릿 관리(`sudo -A`, keychain, vault/secret manager)로 대체합니다.
- **컨테이너화**: Chromium/ChromeDriver + Python 런타임 + 가상 디스플레이를 하나의 배포 단위로 패키징합니다.

---

## Quick Start Checklist

✅ **첫 게시 성공까지의 최소 경로**.

1. 저장소를 클론하고 의존성을 설치합니다(`pip install -r requirements.txt` 또는 경량 `requirements.autopub.txt`).
2. `app.py`, `autopub.py`, 그리고 사용할 스크립트의 하드코딩 경로 상수를 수정합니다.
3. 필수 자격 증명을 셸 프로필 또는 `.env`에 내보내고, `python load_env.py`로 로딩을 검증합니다.
4. 원격 디버깅 브라우저 프로필 폴더를 만들고 각 플랫폼 세션을 최소 1회 실행합니다.
5. 각 대상 플랫폼에 해당 프로필로 수동 로그인합니다.
6. API 모드(`python app.py --port 8081`) 또는 CLI 모드(`python autopub.py --use-cache ...`) 중 하나를 시작합니다.
7. 샘플 ZIP 1개(API 모드) 또는 샘플 영상 1개(CLI 모드)를 투입하고 `logs/`를 확인합니다.
8. 매 push 전에 시크릿 스캔을 실행합니다.

---

## Development Notes

🧬 **현재 개발 기준선**(수동 포맷 + 스모크 테스트).

- Python 스타일은 기존 4칸 들여쓰기와 수동 포맷 규칙을 따릅니다.
- 공식 자동 테스트 스위트는 현재 없습니다. 아래 스모크 테스트를 권장합니다.
  - `autopub.py`로 샘플 영상 1개 처리,
  - `/publish`에 ZIP 1개 POST 후 `/publish/queue` 모니터링,
  - 각 대상 플랫폼 수동 검증.
- 새 스크립트를 추가할 때는 빠른 dry-run을 위해 작은 `if __name__ == "__main__":` 진입점을 포함하세요.
- 플랫폼 변경은 가능한 한 분리하세요(`pub_*`, `login_*`, `ignore_*` 토글).
- 런타임 아티팩트(`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`)는 로컬 전용이며 대부분 git에서 무시됩니다.

---

## Roadmap

🗺️ **현재 코드 제약을 반영한 우선 개선 항목**.

현재 구조/노트를 바탕으로 한 계획:

1. 흩어진 하드코딩 경로를 중앙 설정(`.env`/YAML + 타입 모델)으로 통합.
2. 하드코딩 sudo 비밀번호 패턴 제거 및 더 안전한 프로세스 제어로 전환.
3. 플랫폼별 재시도/상태 감지 강화를 통한 게시 안정성 개선.
4. 플랫폼 지원 확장(예: Kuaishou 등).
5. 재현 가능한 배포 단위(container + virtual display profile) 제공.
6. ZIP 계약 검증 및 큐 실행에 대한 자동 통합 체크 추가.

---

## Contributing

🤝 PR은 작고 재현 가능하게 유지하고, 런타임 가정을 명확히 적어 주세요.

기여를 환영합니다.

1. 포크 후 목적이 분명한 브랜치를 생성합니다.
2. 커밋은 작게, 제목은 명령형으로 작성합니다(히스토리 예: “Wait for YouTube checks before publishing”).
3. PR에 수동 검증 내용을 포함합니다.
   - 환경 가정,
   - 브라우저/세션 재시작 여부,
   - UI 플로우 변경 관련 로그/스크린샷.
4. 실제 시크릿은 절대 커밋하지 마세요(`.env`는 ignore, `.env.example`은 형태 템플릿 전용).

새 게시 모듈을 추가한다면 아래를 모두 연결해야 합니다.
- `pub_<platform>.py`
- optional `login_<platform>.py`
- `app.py`의 API flags 및 queue 처리
- `autopub.py`의 CLI 연결(필요 시)
- `ignore_<platform>` 토글 처리
- README 업데이트

---

## License

현재 이 저장소 스냅샷에는 `LICENSE` 파일이 없습니다.

이 초안의 가정:
- 유지보수자가 명시적 라이선스 파일을 추가하기 전까지 사용/재배포 조건은 미정으로 간주합니다.

권장 다음 조치:
- 최상위에 `LICENSE`(예: MIT/Apache-2.0/GPL-3.0)를 추가하고 이 섹션을 갱신하세요.

> 📝 라이선스 파일이 추가되기 전까지, 상업적/내부 재배포 가정은 미해결 상태로 보고 유지보수자에게 직접 확인하세요.

---

## Acknowledgements

- Maintainer and sponsor profile: [@lachlanchen](https://github.com/lachlanchen)
- Funding configuration source: [`.github/FUNDING.yml`](.github/FUNDING.yml)
- Ecosystem services referenced in this repo: Selenium, Tornado, SendGrid, 2Captcha, Turing captcha APIs.

---

## Support AutoPublish

💖 커뮤니티 지원은 인프라 유지, 안정성 개선, 신규 플랫폼 통합에 사용됩니다.

AutoPublish는 크로스 플랫폼 크리에이터 툴링을 개방적이고 해킹 가능하게 유지하려는 더 큰 노력의 일부입니다. 후원금은 다음에 도움이 됩니다.

- Selenium 팜, 처리 API, 클라우드 GPU를 운영 상태로 유지.
- 신규 게시기(Kuaishou, Instagram Reels 등) 개발 및 기존 봇 안정화.
- 독립 크리에이터를 위한 문서, 스타터 데이터셋, 튜토리얼 확대.

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
