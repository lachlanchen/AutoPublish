[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish

> 🌍 **Trạng thái bản địa hóa (xác minh trong workspace này vào ngày February 28, 2026):**
> `i18n/` hiện có `README.ar.md` và `README.es.md`; `README.zh-CN.md` và `README.ja.md` là các mục tiêu dự phòng cho những tệp sắp tới.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#prerequisites)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#system-overview)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#running-the-tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#platform-specific-notes)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#running-the-tornado-service-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Arabic%20%7C%20Spanish-0EA5E9)](#table-of-contents)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#license)

Bộ công cụ tự động hóa để phân phối nội dung video ngắn lên nhiều nền tảng sáng tạo của Trung Quốc và quốc tế. Dự án kết hợp service Tornado, bot Selenium, và workflow theo dõi thư mục cục bộ để khi thả video vào thư mục, hệ thống sẽ lần lượt tải lên XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), Instagram và tùy chọn YouTube.

Kho mã này có chủ đích ở mức low-level: phần lớn cấu hình nằm trong file Python và script shell. Tài liệu này là sổ tay vận hành bao phủ setup, runtime, và các điểm mở rộng.

> ⚙️ **Triết lý vận hành**: dự án ưu tiên script tường minh và tự động hóa trình duyệt trực tiếp thay vì các lớp trừu tượng ẩn.
> ✅ **Chính sách chuẩn cho README này**: giữ nguyên chi tiết kỹ thuật, sau đó cải thiện khả năng đọc và khả năng tra cứu.

## Start Here

Nếu bạn mới dùng repo này, hãy đi theo thứ tự sau:

1. Đọc [Prerequisites](#prerequisites) và [Installation](#installation).
2. Cấu hình secrets và đường dẫn tuyệt đối trong [Configuration](#configuration).
3. Chuẩn bị các browser debug session trong [Preparing Browser Sessions](#preparing-browser-sessions).
4. Chọn một chế độ chạy trong [Usage](#usage): `autopub.py` (watcher) hoặc `app.py` (API queue).
5. Xác thực bằng các lệnh trong [Examples](#examples).

## Overview

AutoPublish hiện hỗ trợ hai chế độ runtime production:

1. **CLI watcher mode (`autopub.py`)** cho ingest và publish theo thư mục.
2. **API queue mode (`app.py`)** cho publish qua HTTP bằng ZIP (`/publish`, `/publish/queue`).

Hệ thống được thiết kế cho operator thích quy trình minh bạch, script-first thay vì nền tảng orchestration trừu tượng.

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

🎯 **Luồng end-to-end** từ media thô đến bài đã đăng:

Tổng quan workflow:

1. **Nhận footage thô**: đặt video vào `videos/`. Watcher (hoặc `autopub.py` hoặc scheduler/service) phát hiện file mới bằng `videos_db.csv` và `processed.csv`.
2. **Sinh asset**: `process_video.VideoProcessor` upload file lên content-processing server (`upload_url` và `process_url`) và nhận lại gói ZIP chứa:
   - video đã biên tập/mã hóa (`<stem>.mp4`),
   - ảnh cover,
   - `{stem}_metadata.json` với tiêu đề, mô tả, tag theo ngôn ngữ, v.v.
3. **Publish**: metadata điều khiển các Selenium publisher trong `pub_*.py`. Mỗi publisher gắn vào phiên Chromium/Chrome đang chạy sẵn bằng remote debugging port và user-data directory bền vững.
4. **Web control plane (tùy chọn)**: `app.py` mở `/publish`, nhận ZIP dựng sẵn, giải nén, và xếp hàng publish đến cùng các publisher. Nó cũng có thể refresh browser session và gọi login helper (`login_*.py`).
5. **Module hỗ trợ**: `load_env.py` nạp secrets từ `~/.bashrc`, `utils.py` cung cấp helper (focus cửa sổ, xử lý QR, helper mail), và `solve_captcha_*.py` tích hợp Turing/2Captcha khi gặp captcha.

## Features

✨ **Thiết kế cho tự động hóa thực dụng, script-first**:

- Publish đa nền tảng: XiaoHongShu, Douyin, Bilibili, ShiPinHao (WeChat Channels), Instagram, YouTube (tùy chọn).
- Hai chế độ vận hành: CLI watcher pipeline (`autopub.py`) và API queue service (`app.py` + `/publish` + `/publish/queue`).
- Công tắc tắt tạm thời theo nền tảng qua file `ignore_*`.
- Tái sử dụng browser-session remote-debugging với profile bền vững.
- Tùy chọn tự động hóa QR/captcha và helper thông báo email.
- Không cần frontend build cho uploader UI PWA đi kèm (`pwa/`).
- Script tự động hóa Linux/Raspberry Pi cho service setup (`scripts/`).

### Feature Matrix

| Capability | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Input source | Local `videos/` watcher | Uploaded ZIP via `POST /publish` |
| Queueing | Internal file-based progression | Explicit in-memory job queue |
| Platform flags | CLI args (`--pub-*`) + `ignore_*` | Query args (`publish_*`) + `ignore_*` |
| Best fit | Single-host operator workflow | External systems and remote triggering |

---

## Project Structure

Bố cục mã nguồn/runtime ở mức cao:

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

Lưu ý: `transcription_data/` được dùng trong luồng xử lý/publish lúc chạy và có thể xuất hiện sau khi thực thi.

## Repository Layout

🗂️ **Các module chính và chức năng**:

| Path | Purpose |
| --- | --- |
| `app.py` | Tornado service mở `/publish` và `/publish/queue`, có publish queue nội bộ và worker thread. |
| `autopub.py` | CLI watcher: quét `videos/`, xử lý file mới, rồi gọi publisher song song. |
| `process_video.py` | Upload video lên backend xử lý và lưu các ZIP bundle trả về. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | Module tự động hóa Selenium theo từng nền tảng. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | Kiểm tra session và luồng login QR. |
| `utils.py` | Helper dùng chung cho automation (focus cửa sổ, QR/mail utilities, helper chẩn đoán). |
| `load_env.py` | Nạp biến môi trường từ shell profile (`~/.bashrc`) và che log nhạy cảm. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | Helper SMTP/SendGrid và script test. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Tích hợp giải captcha. |
| `scripts/` | Script setup service và vận hành (Raspberry Pi/Linux + automation cũ). |
| `pwa/` | PWA tĩnh để preview ZIP và gửi publish. |
| `setup_raspberrypi.md` | Hướng dẫn provisioning Raspberry Pi từng bước. |
| `.env.example` | Mẫu biến môi trường (credentials, paths, captcha keys). |
| `.github/FUNDING.yml` | Cấu hình tài trợ/funding. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | Artifact và log runtime (nhiều mục được gitignore). |

---

## Prerequisites

🧰 **Cài các thành phần này trước lần chạy đầu tiên**.

### Operating system and tools

- Linux desktop/server có phiên X (`DISPLAY=:1` thường được dùng trong script mẫu).
- Chromium/Chrome và ChromeDriver tương thích.
- Công cụ GUI/media: `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv hoặc Conda).

### Python dependencies

Bộ runtime tối thiểu:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

Đồng bộ theo repo:

```bash
python -m pip install -r requirements.txt
```

Với bản cài service nhẹ (mặc định được dùng bởi setup scripts):

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` gồm:
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Optional: create a sudo user

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## Installation

🚀 **Thiết lập từ máy sạch**:

1. Clone repository:

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. Tạo và kích hoạt môi trường (ví dụ với `venv`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. Chuẩn bị biến môi trường:

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. Nạp biến cho các script đọc giá trị từ shell profile:

```bash
source ~/.bashrc
python load_env.py
```

Lưu ý: `load_env.py` được thiết kế xoay quanh `~/.bashrc`; nếu bạn dùng shell profile khác, hãy điều chỉnh tương ứng.

---

## Configuration

🔐 **Đặt credentials, sau đó kiểm tra đường dẫn theo từng host**.

### Environment variables

Dự án cần credentials và (tùy chọn) browser/runtime path từ biến môi trường. Bắt đầu từ `.env.example`:

| Variable | Description |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | Thông tin SMTP cho thông báo QR/login. |
| `SENDGRID_API_KEY` | Khóa SendGrid cho các luồng email dùng API SendGrid. |
| `APIKEY_2CAPTCHA` | Khóa API 2Captcha. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Thông tin captcha Turing. |
| `DOUYIN_LOGIN_PASSWORD` | Helper cho xác minh lớp hai của Douyin. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Ghi đè Instagram/browser driver. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | Ghi đè browser/driver/display toàn cục ưu tiên trong `app.py`. |

### Path constants (important)

📌 **Lỗi khởi động phổ biến nhất**: đường dẫn tuyệt đối hard-code không khớp.

Nhiều module vẫn chứa đường dẫn hard-code. Hãy cập nhật theo host của bạn:

| File | Constant(s) | Meaning |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | Root của API service và endpoint backend. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | Root của CLI watcher và endpoint backend. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Đường dẫn tuyệt đối đến Python/Conda/repo/log. | Wrapper cũ thiên về macOS. |
| `utils.py` | Giả định đường dẫn FFmpeg trong helper xử lý cover. | Tương thích đường dẫn media tooling. |

Ghi chú quan trọng cho repository:
- Đường dẫn repo hiện tại trong workspace này là `/home/lachlan/ProjectsLFS/AutoPublish`.
- Một số code và script vẫn tham chiếu `/home/lachlan/Projects/auto-publish` hoặc `/Users/lachlan/...`.
- Hãy giữ và chỉnh lại các đường dẫn này tại máy cục bộ trước khi chạy production.

### Platform toggles via `ignore_*`

🧩 **Công tắc an toàn nhanh**: tạo file `ignore_*` để tắt publisher mà không sửa code.

Các cờ publish cũng bị chặn bởi ignore file. Tạo file rỗng để tắt một nền tảng:

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

Xóa file tương ứng để bật lại.

---

## Preparing Browser Sessions

🌐 **Bắt buộc dùng session persistence** để publish Selenium ổn định.

1. Tạo thư mục profile riêng:

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. Khởi chạy browser session với remote debugging (ví dụ cho XiaoHongShu):

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. Đăng nhập thủ công một lần cho từng nền tảng/profile.

4. Xác minh Selenium có thể attach:

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Lưu ý bảo mật:
- `app.py` hiện có placeholder mật khẩu sudo hard-code (`password = "1"`) được dùng trong logic restart browser. Hãy thay thế trước khi triển khai thực tế.

---

## Usage

▶️ **Có hai chế độ runtime**: CLI watcher và API queue service.

### Running the CLI pipeline (`autopub.py`)

1. Đặt video nguồn vào thư mục theo dõi (`videos/` hoặc `autopublish_folder_path` mà bạn đã cấu hình).
2. Chạy:

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Flags:

| Flag | Meaning |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Giới hạn publish theo nền tảng chọn. Nếu không truyền cờ nào, mặc định bật cả ba. |
| `--test` | Test mode truyền xuống publisher (hành vi khác nhau theo từng module nền tảng). |
| `--use-cache` | Tái sử dụng `transcription_data/<video>/<video>.zip` nếu có. |

Luồng CLI cho mỗi video:
- Upload/xử lý qua `process_video.py`.
- Giải nén ZIP vào `transcription_data/<video>/`.
- Chạy publisher đã chọn qua `ThreadPoolExecutor`.
- Ghi trạng thái theo dõi vào `videos_db.csv` và `processed.csv`.

### Running the Tornado service (`app.py`)

🛰️ **API mode** phù hợp cho hệ thống bên ngoài tạo ZIP bundle.

Khởi chạy server:

```bash
python app.py --refresh-time 1800 --port 8081
```

Tóm tắt endpoint API:

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/publish` | `POST` | Upload ZIP bytes và xếp hàng một publish job |
| `/publish/queue` | `GET` | Xem queue, lịch sử job, và trạng thái publish |

### `POST /publish`

📤 **Xếp một publish job** bằng cách upload trực tiếp ZIP bytes.

- Header: `Content-Type: application/octet-stream`
- Query/form arg bắt buộc: `filename` (tên file ZIP)
- Boolean tùy chọn: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: raw ZIP bytes

Ví dụ:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

Hành vi hiện tại trong code:
- Request được chấp nhận và đưa vào queue.
- Phản hồi tức thì trả JSON gồm `status: queued`, `job_id`, và `queue_size`.
- Worker thread xử lý tuần tự các job trong queue.

### `GET /publish/queue`

📊 **Theo dõi sức khỏe queue và job đang chạy**.

Trả JSON trạng thái/lịch sử queue:

```bash
curl "http://localhost:8081/publish/queue"
```

Trường phản hồi gồm:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Browser refresh thread

♻️ Luồng refresh trình duyệt định kỳ giúp giảm lỗi session cũ khi chạy uptime dài.

`app.py` chạy một background refresh thread theo chu kỳ `--refresh-time` và có hook login checks. Thời gian sleep refresh có thêm độ trễ ngẫu nhiên.

### PWA frontend (`pwa/`)

🖥️ UI tĩnh nhẹ cho upload ZIP thủ công và theo dõi queue.

Chạy UI tĩnh cục bộ:

```bash
cd pwa
python -m http.server 5173
```

Mở `http://localhost:5173` và đặt backend base URL (ví dụ `http://lazyingart:8081`).

Khả năng của PWA:
- Preview ZIP bằng kéo/thả.
- Bật/tắt đích publish + test mode.
- Gửi lên `/publish` và poll `/publish/queue`.

---

## Examples

🧪 **Các lệnh smoke-test có thể copy/paste**:

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

📦 **Hợp đồng ZIP rất quan trọng**: giữ tên file và khóa metadata khớp kỳ vọng của publisher.

Nội dung ZIP kỳ vọng (tối thiểu):

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` điều khiển các publisher CN; `metadata["english_version"]` (tùy chọn) cấp dữ liệu cho publisher YouTube.

Các trường thường được module dùng:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (danh sách hashtag)
- `video_filename`, `cover_filename`
- các trường riêng theo nền tảng được implement trong từng `pub_*.py`

Nếu bạn tạo ZIP từ hệ thống bên ngoài, hãy giữ keys và filenames đúng như module mong đợi.

---

## Platform-Specific Notes

🧭 **Bản đồ cổng + module phụ trách** cho từng publisher.

| Platform | Port | Module(s) | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | Luồng đăng nhập lại bằng QR; tiêu đề và hashtag lấy từ metadata. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Kiểm tra upload hoàn tất và retry khá mong manh theo nền tảng; cần theo dõi log sát. |
| Bilibili | 5005 | `pub_bilibili.py` | Có hook captcha qua `solve_captcha_2captcha.py` và `solve_captcha_turing.py`. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Duyệt QR nhanh rất quan trọng để refresh session ổn định. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | Điều khiển trong API mode bằng `publish_instagram=true`; env vars có sẵn trong `.env.example`. |
| YouTube | 9222 | `pub_y2b.py` | Dùng khối metadata `english_version`; tắt bằng `ignore_y2b`. |

---

## Raspberry Pi / Linux Service Setup

🐧 **Khuyến nghị cho host chạy liên tục (always-on)**.

Để bootstrap đầy đủ một host, làm theo [`setup_raspberrypi.md`](setup_raspberrypi.md).

Thiết lập pipeline nhanh:

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

Lệnh này điều phối:
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

Chạy service thủ công trong tmux:

```bash
./scripts/start_autopub_tmux.sh
```

Xác thực service/cổng:

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## Legacy macOS Scripts

🍎 Các wrapper cũ vẫn được giữ để tương thích với môi trường local trước đây.

Repository vẫn bao gồm các wrapper cũ thiên về macOS:
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

Các file này chứa đường dẫn tuyệt đối `/Users/lachlan/...` và giả định Conda. Hãy giữ nếu bạn còn dùng workflow đó, nhưng cần cập nhật paths/venv/tooling theo host của bạn.

---

## Troubleshooting & Maintenance

🛠️ **Nếu có lỗi, bắt đầu kiểm tra từ đây**.

- **Path drift giữa các máy**: nếu lỗi báo thiếu file dưới `/Users/lachlan/...` hoặc `/home/lachlan/Projects/auto-publish`, hãy đồng bộ constants theo đường dẫn host của bạn (`/home/lachlan/ProjectsLFS/AutoPublish` trong workspace này).
- **Secrets hygiene**: chạy `~/.local/bin/detect-secrets scan` trước khi push. Rotate mọi credential bị lộ.
- **Lỗi processing backend**: nếu `process_video.py` in “Failed to get the uploaded file path,” hãy xác minh JSON phản hồi upload có `file_path` và endpoint xử lý trả về ZIP bytes.
- **ChromeDriver mismatch**: nếu xuất hiện lỗi kết nối DevTools, hãy đồng bộ phiên bản Chrome/Chromium và driver (hoặc chuyển sang `webdriver-manager`).
- **Vấn đề focus trình duyệt**: `bring_to_front` phụ thuộc vào khớp tiêu đề cửa sổ (khác biệt tên Chromium/Chrome có thể làm hỏng).
- **Captcha làm gián đoạn**: cấu hình credential 2Captcha/Turing và tích hợp output của solver khi cần.
- **Stale lock files**: nếu tác vụ định kỳ không bao giờ chạy, kiểm tra trạng thái process và xóa `autopub.lock` cũ (luồng script legacy).
- **Logs cần xem**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log`, và service journal logs.

---

## Extending the System

🧱 **Điểm mở rộng** để thêm nền tảng mới và vận hành an toàn hơn.

- **Thêm nền tảng mới**: sao chép một module `pub_*.py`, cập nhật selector/flow, thêm `login_*.py` nếu cần QR re-auth, sau đó nối cờ và queue handling trong `app.py` và wiring CLI trong `autopub.py`.
- **Trừu tượng hóa config**: chuyển các hằng số rải rác sang config có cấu trúc (`config.yaml`/`.env` + typed model) để chạy đa host.
- **Tăng cường lưu trữ credential**: thay luồng hard-code hoặc lộ qua shell bằng secret management an toàn (`sudo -A`, keychain, vault/secret manager).
- **Containerization**: đóng gói Chromium/ChromeDriver + Python runtime + virtual display thành một đơn vị triển khai cho cloud/server.

---

## Quick Start Checklist

✅ **Đường ngắn nhất để publish thành công lần đầu**.

1. Clone repository này và cài dependencies (`pip install -r requirements.txt` hoặc bản nhẹ `requirements.autopub.txt`).
2. Cập nhật các path constant hard-code trong `app.py`, `autopub.py`, và mọi script bạn sẽ chạy.
3. Export credential cần thiết trong shell profile hoặc `.env`; chạy `python load_env.py` để xác minh nạp thành công.
4. Tạo thư mục profile browser remote-debug và khởi chạy mỗi session nền tảng cần dùng ít nhất một lần.
5. Đăng nhập thủ công vào từng nền tảng đích trong profile tương ứng.
6. Khởi chạy API mode (`python app.py --port 8081`) hoặc CLI mode (`python autopub.py --use-cache ...`).
7. Gửi một ZIP mẫu (API mode) hoặc một file video mẫu (CLI mode) và kiểm tra `logs/`.
8. Chạy secrets scanning trước mỗi lần push.

---

## Development Notes

🧬 **Mốc phát triển hiện tại** (format thủ công + smoke test).

- Style Python theo chuẩn sẵn có: indent 4 spaces và format thủ công.
- Hiện chưa có bộ test tự động chính thức; hãy dùng smoke test:
  - xử lý một video mẫu qua `autopub.py`;
  - gửi một ZIP lên `/publish` và theo dõi `/publish/queue`;
  - xác nhận thủ công từng nền tảng mục tiêu.
- Khi thêm script mới, thêm entrypoint nhỏ `if __name__ == "__main__":` để dry-run nhanh.
- Cố gắng cô lập thay đổi theo nền tảng (`pub_*`, `login_*`, toggle `ignore_*`).
- Runtime artifacts (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) được kỳ vọng là cục bộ và đa phần bị gitignore.

---

## Roadmap

🗺️ **Các cải tiến ưu tiên phản ánh giới hạn hiện tại của code**.

Các cải tiến dự kiến/mong muốn (dựa trên cấu trúc mã hiện tại và ghi chú sẵn có):

1. Thay các path hard-code rải rác bằng config trung tâm (`.env`/YAML + typed models).
2. Loại bỏ pattern hard-code mật khẩu sudo và chuyển kiểm soát tiến trình sang cơ chế an toàn hơn.
3. Tăng độ tin cậy publish bằng retry mạnh hơn và nhận diện UI-state tốt hơn theo từng nền tảng.
4. Mở rộng hỗ trợ nền tảng (ví dụ Kuaishou hoặc các nền tảng creator khác).
5. Đóng gói runtime thành đơn vị triển khai có thể tái lập (container + virtual display profile).
6. Bổ sung kiểm tra tích hợp tự động cho ZIP contract và queue execution.

---

## Contributing

🤝 Giữ PR tập trung, tái lập được, và nêu rõ giả định runtime.

Mọi đóng góp đều được chào đón.

1. Fork và tạo branch tập trung.
2. Giữ commit nhỏ, dùng câu mệnh lệnh (phong cách ví dụ trong lịch sử: “Wait for YouTube checks before publishing”).
3. Thêm ghi chú xác minh thủ công trong PR:
   - giả định môi trường,
   - thao tác restart browser/session,
   - log/screenshot liên quan cho thay đổi luồng UI.
4. Không commit secrets thật (`.env` bị ignore; chỉ dùng `.env.example` làm khuôn dạng).

Nếu thêm module publisher mới, hãy nối đủ các phần sau:
- `pub_<platform>.py`
- `login_<platform>.py` (tùy chọn)
- API flags và queue handling trong `app.py`
- wiring CLI trong `autopub.py` (nếu cần)
- xử lý toggle `ignore_<platform>`
- cập nhật README

---

## License

Hiện chưa có file `LICENSE` trong snapshot repository này.

Giả định cho bản nháp này:
- Xem quyền sử dụng và phân phối lại là chưa xác định cho tới khi maintainer thêm file license rõ ràng.

Hành động tiếp theo được khuyến nghị:
- Thêm `LICENSE` ở cấp root (ví dụ MIT/Apache-2.0/GPL-3.0) và cập nhật lại mục này.

> 📝 Cho đến khi có file license, hãy coi các giả định về phân phối lại thương mại/nội bộ là chưa rõ và xác nhận trực tiếp với maintainer.

---

## Acknowledgements

- Trang maintainer và sponsor: [@lachlanchen](https://github.com/lachlanchen)
- Nguồn cấu hình funding: [`.github/FUNDING.yml`](.github/FUNDING.yml)
- Dịch vụ hệ sinh thái được nhắc tới trong repo này: Selenium, Tornado, SendGrid, 2Captcha, Turing captcha APIs.

---

## Support AutoPublish

💖 Hỗ trợ từ cộng đồng giúp chi trả hạ tầng, cải thiện độ ổn định, và tích hợp nền tảng mới.

AutoPublish nằm trong nỗ lực rộng hơn nhằm giữ bộ công cụ creator đa nền tảng luôn mở và dễ tùy biến. Quyên góp giúp:

- Duy trì cụm Selenium, processing API, và cloud GPUs hoạt động.
- Phát hành publisher mới (Kuaishou, Instagram Reels, v.v.) cùng các bản vá độ ổn định cho bot hiện có.
- Chia sẻ thêm tài liệu, bộ dữ liệu khởi đầu, và tutorial cho creator độc lập.

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
