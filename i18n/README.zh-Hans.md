[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish

> 🌍 **本地化状态（于 2026 年 2 月 28 日在当前工作区核验）：**
> `i18n/` 目前已包含 `README.ar.md`、`README.es.md` 与 `README.zh-Hans.md`；其余语言文件请按当前仓库实际情况继续补齐。

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#prerequisites)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#system-overview)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#running-the-tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#platform-specific-notes)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#running-the-tornado-service-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Arabic%20%7C%20Spanish-0EA5E9)](#table-of-contents)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#license)

这是一个面向短视频内容分发的自动化工具包，可将内容发布到多个中国及国际创作者平台。项目将基于 Tornado 的服务、Selenium 自动化机器人与本地文件监听工作流结合起来：只要把视频放进文件夹，系统最终就会上传到小红书、抖音、Bilibili、微信视频号（ShiPinHao）、Instagram，以及可选的 YouTube。

该仓库有意保持“低抽象”风格：大部分配置位于 Python 文件和 shell 脚本中。本文档是运维手册，覆盖安装、运行和扩展点。

> ⚙️ **运维理念**：相比隐藏式抽象层，本项目更偏向显式脚本和直接浏览器自动化。
> ✅ **本 README 的规范原则**：保留技术细节，并持续提升可读性与可发现性。

<a id="start-here"></a>
## Start Here

如果你是第一次接触本仓库，建议按此顺序进行：

1. 先读 [Prerequisites](#prerequisites) 和 [Installation](#installation)。
2. 在 [Configuration](#configuration) 中配置密钥与绝对路径。
3. 在 [Preparing Browser Sessions](#preparing-browser-sessions) 中准备浏览器调试会话。
4. 在 [Usage](#usage) 里选择运行模式：`autopub.py`（监听模式）或 `app.py`（API 队列模式）。
5. 使用 [Examples](#examples) 的命令做验证。

<a id="overview"></a>
## Overview

AutoPublish 当前支持两种生产运行模式：

1. **CLI 监听模式（`autopub.py`）**：面向基于文件夹的采集与发布。
2. **API 队列模式（`app.py`）**：通过 HTTP（`/publish`, `/publish/queue`）处理 ZIP 发布。

适合偏好透明、脚本优先工作流，而非抽象编排平台的运维人员。

### Runtime Modes at a Glance

| 模式 | 入口 | 输入 | 适用场景 | 输出行为 |
| --- | --- | --- | --- | --- |
| CLI 监听 | `autopub.py` | 放入 `videos/` 的文件 | 本地运维工作流、cron/service 循环 | 检测到视频后立即发布到所选平台 |
| API 队列服务 | `app.py` | 上传到 `POST /publish` 的 ZIP | 对接上游系统、远程触发 | 接收任务并入队，按 worker 顺序执行发布 |

## Quick Snapshot

| 项目 | 值 |
| --- | --- |
| 主要语言 | Python 3.10+ |
| 主要运行时 | CLI 监听器（`autopub.py`）+ Tornado 队列服务（`app.py`） |
| 自动化引擎 | Selenium + 远程调试 Chromium 会话 |
| 输入格式 | 原始视频（`videos/`）和 ZIP 包（`/publish`） |
| 当前仓库工作区路径 | `/home/lachlan/ProjectsLFS/AutoPublish` |
| 目标用户 | 维护多平台短视频流水线的创作者/运维工程师 |

### Operational Safety Snapshot

| 主题 | 当前状态 | 建议操作 |
| --- | --- | --- |
| 硬编码路径 | 多个模块/脚本中存在 | 生产前按主机更新路径常量 |
| 浏览器登录状态 | 必需 | 每个平台保留持久化远程调试 profile |
| 验证码处理 | 提供可选集成 | 需要时配置 2Captcha/Turing 凭据 |
| 许可证声明 | 未检测到顶层 `LICENSE` 文件 | 再分发前与维护者确认使用条款 |

---

<a id="table-of-contents"></a>
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

<a id="system-overview"></a>
## System Overview

🎯 从原始素材到发布帖文的**端到端流程**：

流程速览：

1. **原始素材接入**：把视频放入 `videos/`。监听器（`autopub.py` 或调度器/service）会借助 `videos_db.csv` 与 `processed.csv` 发现新文件。
2. **资源生成**：`process_video.VideoProcessor` 将文件上传到内容处理服务（`upload_url` 与 `process_url`），服务返回一个 ZIP 包，包含：
   - 处理后/编码后的视频（`<stem>.mp4`），
   - 封面图，
   - `{stem}_metadata.json`（含本地化标题、描述、标签等）。
3. **发布**：元数据驱动 `pub_*.py` 中的 Selenium 发布器。每个发布器通过远程调试端口和持久化用户目录连接到已运行的 Chromium/Chrome 实例。
4. **Web 控制面（可选）**：`app.py` 暴露 `/publish`，接收已构建好的 ZIP，解包后将发布任务排入同一套发布器。它还可刷新浏览器会话并触发登录辅助（`login_*.py`）。
5. **支撑模块**：`load_env.py` 从 `~/.bashrc` 注入密钥，`utils.py` 提供公共工具（窗口聚焦、二维码处理、邮件辅助），`solve_captcha_*.py` 在出现验证码时对接 Turing/2Captcha。

<a id="features"></a>
## Features

✨ **为务实、脚本优先的自动化而设计**：

- 多平台发布：小红书、抖音、Bilibili、视频号（ShiPinHao）、Instagram、YouTube（可选）。
- 两种运行模式：CLI 监听流水线（`autopub.py`）与 API 队列服务（`app.py` + `/publish` + `/publish/queue`）。
- 通过 `ignore_*` 文件按平台临时停用。
- 基于远程调试的浏览器会话复用，支持持久化 profile。
- 可选二维码/验证码自动化与邮件通知辅助。
- 内置 PWA（`pwa/`）上传 UI，无需前端构建。
- 面向 Linux/Raspberry Pi 的服务部署脚本（`scripts/`）。

### Feature Matrix

| 能力 | CLI（`autopub.py`） | API（`app.py`） |
| --- | --- | --- |
| 输入来源 | 本地 `videos/` 监听 | 通过 `POST /publish` 上传 ZIP |
| 队列机制 | 基于文件的内部推进 | 显式内存任务队列 |
| 平台开关 | CLI 参数（`--pub-*`）+ `ignore_*` | 查询参数（`publish_*`）+ `ignore_*` |
| 最佳适配 | 单机运维流程 | 外部系统集成与远程触发 |

---

<a id="project-structure"></a>
## Project Structure

高层源码/运行时布局：

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

注意：`transcription_data/` 在处理/发布流程运行时会被使用，执行后可能出现该目录。

<a id="repository-layout"></a>
## Repository Layout

🗂️ **关键模块及其作用**：

| 路径 | 用途 |
| --- | --- |
| `app.py` | Tornado 服务：暴露 `/publish` 与 `/publish/queue`，包含内部发布队列与 worker 线程。 |
| `autopub.py` | CLI 监听器：扫描 `videos/`，处理新文件，并并行触发发布器。 |
| `process_video.py` | 将视频上传到处理后端并保存返回的 ZIP 包。 |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | 各平台 Selenium 自动化模块。 |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | 会话检测与二维码登录流程。 |
| `utils.py` | 公共自动化工具（窗口聚焦、二维码/邮件辅助、诊断辅助）。 |
| `load_env.py` | 从 shell profile（`~/.bashrc`）加载环境变量并遮蔽敏感日志。 |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | SMTP/SendGrid 辅助与测试脚本。 |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | 验证码求解集成。 |
| `scripts/` | 服务部署与运维脚本（Raspberry Pi/Linux + 旧版自动化）。 |
| `pwa/` | 用于 ZIP 预览与发布提交的静态 PWA。 |
| `setup_raspberrypi.md` | Raspberry Pi 配置分步指南。 |
| `.env.example` | 环境变量模板（凭据、路径、验证码 key）。 |
| `.github/FUNDING.yml` | 赞助/资助配置。 |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | 运行期产物与日志（多数被 gitignore）。 |

---

<a id="prerequisites"></a>
## Prerequisites

🧰 **首次运行前请先安装以下依赖**。

### Operating system and tools

- 带 X 会话的 Linux 桌面/服务器（示例脚本中常用 `DISPLAY=:1`）。
- Chromium/Chrome 及匹配版本的 ChromeDriver。
- GUI/媒体辅助工具：`xdotool`、`ffmpeg`、`zip`、`unzip`。
- Python 3.10+（venv 或 Conda）。

### Python dependencies

最小运行依赖：

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

与仓库一致：

```bash
python -m pip install -r requirements.txt
```

轻量服务安装（默认被安装脚本使用）：

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` 包含：
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`。

### Optional: create a sudo user

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

<a id="installation"></a>
## Installation

🚀 **在全新机器上的安装流程**：

1. 克隆仓库：

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. 创建并激活环境（以 `venv` 为例）：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. 准备环境变量：

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. 加载给脚本使用的 shell profile 变量：

```bash
source ~/.bashrc
python load_env.py
```

注意：`load_env.py` 默认围绕 `~/.bashrc` 设计；如果你使用其他 shell profile，请按需调整。

---

<a id="configuration"></a>
## Configuration

🔐 **先配置凭据，再核对主机相关路径**。

### Environment variables

项目会从环境变量中读取凭据和可选浏览器/运行时路径。请从 `.env.example` 开始：

| 变量 | 说明 |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | 用于二维码/登录通知的 SMTP 凭据。 |
| `SENDGRID_API_KEY` | 走 SendGrid API 的邮件流程所用 key。 |
| `APIKEY_2CAPTCHA` | 2Captcha API key。 |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Turing 验证码凭据。 |
| `DOUYIN_LOGIN_PASSWORD` | 抖音二次验证辅助。 |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Instagram/浏览器驱动覆盖项。 |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | `app.py` 中优先使用的全局浏览器/驱动/显示覆盖项。 |

### Path constants (important)

📌 **最常见启动问题**：硬编码绝对路径未更新。

多个模块仍含硬编码路径，请按你的主机环境更新：

| 文件 | 常量 | 含义 |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | API 服务根路径与后端端点。 |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | CLI 监听器根路径与后端端点。 |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Python/Conda/仓库/日志位置的绝对路径。 | 旧版/macOS 风格包装脚本。 |
| `utils.py` | 封面处理辅助中的 FFmpeg 路径假设。 | 媒体工具路径兼容性。 |

仓库重要说明：
- 当前工作区仓库路径为 `/home/lachlan/ProjectsLFS/AutoPublish`。
- 仍有部分代码与脚本引用 `/home/lachlan/Projects/auto-publish` 或 `/Users/lachlan/...`。
- 投产前请在本地保留并改正确认这些路径。

### Platform toggles via `ignore_*`

🧩 **快速安全开关**：创建 `ignore_*` 文件即可禁用对应发布器，无需改代码。

发布标志同时受 ignore 文件控制。创建空文件可禁用平台：

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

删除对应文件即可重新启用。

---

<a id="preparing-browser-sessions"></a>
## Preparing Browser Sessions

🌐 **会话持久化是 Selenium 稳定发布的前提**。

1. 创建独立 profile 目录：

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. 以远程调试方式启动浏览器会话（以小红书为例）：

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. 每个平台/profile 至少手动登录一次。

4. 验证 Selenium 可连接：

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

安全说明：
- `app.py` 当前包含硬编码 sudo 密码占位（`password = "1"`），用于浏览器重启逻辑。生产部署前务必替换。

---

<a id="usage"></a>
## Usage

▶️ **支持两种运行模式**：CLI 监听器与 API 队列服务。

### Running the CLI pipeline (`autopub.py`)

1. 将源视频放入监听目录（`videos/` 或你配置的 `autopublish_folder_path`）。
2. 执行：

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

参数说明：

| 参数 | 含义 |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | 仅发布到所选平台。若都不传，则默认启用这三者。 |
| `--test` | 向发布器传入测试模式（具体行为依平台模块而异）。 |
| `--use-cache` | 若存在则复用 `transcription_data/<video>/<video>.zip`。 |

每个视频的 CLI 流程：
- 通过 `process_video.py` 上传/处理。
- 解压 ZIP 到 `transcription_data/<video>/`。
- 通过 `ThreadPoolExecutor` 启动所选发布器。
- 将追踪状态追加到 `videos_db.csv` 与 `processed.csv`。

### Running the Tornado service (`app.py`)

🛰️ **API 模式**适合由外部系统生产 ZIP 并触发发布。

启动服务：

```bash
python app.py --refresh-time 1800 --port 8081
```

API 端点总览：

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/publish` | `POST` | 上传 ZIP 字节并入队发布任务 |
| `/publish/queue` | `GET` | 查看队列、任务历史和发布状态 |

### `POST /publish`

📤 **通过直接上传 ZIP 字节来排队发布任务**。

- Header: `Content-Type: application/octet-stream`
- 必填 query/form 参数：`filename`（ZIP 文件名）
- 可选布尔参数：`publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body：原始 ZIP 字节

示例：

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

当前代码行为：
- 请求会被接收并入队。
- 立即返回 JSON，含 `status: queued`、`job_id`、`queue_size`。
- worker 线程按串行方式处理队列任务。

### `GET /publish/queue`

📊 **观察队列健康状态与在途任务**。

返回队列状态/历史 JSON：

```bash
curl "http://localhost:8081/publish/queue"
```

响应字段包括：
- `status`, `jobs`, `queue_size`, `is_publishing`。

### Browser refresh thread

♻️ 定期刷新浏览器可降低长时间运行中的会话老化失败。

`app.py` 会按 `--refresh-time` 间隔运行后台刷新线程，并挂接登录检查。刷新 sleep 含随机延迟行为。

### PWA frontend (`pwa/`)

🖥️ 用于手动上传 ZIP 与查看队列的轻量静态 UI。

本地运行静态 UI：

```bash
cd pwa
python -m http.server 5173
```

打开 `http://localhost:5173` 并设置后端 base URL（例如 `http://lazyingart:8081`）。

PWA 能力：
- 拖拽 ZIP 预览。
- 发布目标开关 + 测试模式。
- 提交到 `/publish` 并轮询 `/publish/queue`。

---

<a id="examples"></a>
## Examples

🧪 **可直接复制粘贴的冒烟测试命令**：

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

<a id="metadata--zip-format"></a>
## Metadata & ZIP Format

📦 **ZIP 协议很关键**：文件名与 metadata key 必须与发布器预期一致。

ZIP 期望内容（最小）：

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` 用于中文平台发布；可选的 `metadata["english_version"]` 用于 YouTube 发布器。

模块常用字段：
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags`（hashtag 列表）
- `video_filename`, `cover_filename`
- 各平台专用字段（以各 `pub_*.py` 实现为准）

如果你在外部生成 ZIP，请保持 key 和文件名与模块预期严格一致。

---

<a id="platform-specific-notes"></a>
## Platform-Specific Notes

🧭 **每个平台的端口映射与模块归属**。

| Platform | Port | Module(s) | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | 二维码重登流程；标题清洗与 hashtag 使用来自 metadata。 |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | 上传完成检测与重试路径对平台 UI 较敏感；请密切监控日志。 |
| Bilibili | 5005 | `pub_bilibili.py` | 可通过 `solve_captcha_2captcha.py` 与 `solve_captcha_turing.py` 接入验证码钩子。 |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | 快速二维码确认对会话刷新稳定性很重要。 |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | 在 API 模式下通过 `publish_instagram=true` 控制；`.env.example` 提供相关环境变量。 |
| YouTube | 9222 | `pub_y2b.py` | 使用 `english_version` 元数据块；可通过 `ignore_y2b` 禁用。 |

---

<a id="raspberry-pi--linux-service-setup"></a>
## Raspberry Pi / Linux Service Setup

🐧 **适合长期常驻运行主机**。

完整主机引导请参考 [`setup_raspberrypi.md`](setup_raspberrypi.md)。

快速流水线安装：

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

该脚本会编排：
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

在 tmux 中手动运行服务：

```bash
./scripts/start_autopub_tmux.sh
```

验证服务/端口：

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

<a id="legacy-macos-scripts"></a>
## Legacy macOS Scripts

🍎 为兼容旧本地工作流，仍保留历史包装脚本。

仓库目前仍包含以下偏 macOS 的旧脚本：
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

这些脚本包含绝对路径 `/Users/lachlan/...` 以及 Conda 假设。如果你依赖该工作流可继续使用，但请按当前主机更新路径/venv/工具链。

---

<a id="troubleshooting--maintenance"></a>
## Troubleshooting & Maintenance

🛠️ **出现故障时，先从这里排查**。

- **跨机器路径漂移**：若报错指向 `/Users/lachlan/...` 或 `/home/lachlan/Projects/auto-publish`，请将常量统一到当前主机路径（本工作区为 `/home/lachlan/ProjectsLFS/AutoPublish`）。
- **密钥卫生**：推送前运行 `~/.local/bin/detect-secrets scan`。若发生泄露请轮换凭据。
- **处理后端错误**：若 `process_video.py` 输出 “Failed to get the uploaded file path,” 请确认上传响应 JSON 含 `file_path`，且处理端点返回 ZIP 字节。
- **ChromeDriver 版本不匹配**：出现 DevTools 连接错误时，请对齐 Chrome/Chromium 与 driver 版本（或切换到 `webdriver-manager`）。
- **浏览器焦点问题**：`bring_to_front` 依赖窗口标题匹配（Chromium/Chrome 命名差异可能导致失败）。
- **验证码中断**：请配置 2Captcha/Turing 凭据，并在需要处接入 solver 输出。
- **陈旧锁文件**：若定时任务始终不启动，请检查进程状态并移除旧的 `autopub.lock`（旧脚本流）。
- **建议检查日志**：`logs/`、`logs-autopub/`、`~/chromium_dev_session_logs/*.log`，以及 service journal 日志。

---

<a id="extending-the-system"></a>
## Extending the System

🧱 **新增平台与提升安全性的扩展点**。

- **新增平台**：复制一个 `pub_*.py` 模块并更新选择器/流程；若需要二维码重认证则新增 `login_*.py`；再在 `app.py` 接入 flags 与队列处理，在 `autopub.py` 接入 CLI 逻辑。
- **配置抽象**：将分散常量迁移到结构化配置（`config.yaml`/`.env` + typed model），便于多主机运行。
- **凭据存储加固**：将硬编码或 shell 暴露的敏感流程替换为更安全的 secret 管理（`sudo -A`、keychain、vault/secret manager）。
- **容器化**：将 Chromium/ChromeDriver + Python 运行时 + 虚拟显示打包为可部署单元，适用于云端/服务器。

---

<a id="quick-start-checklist"></a>
## Quick Start Checklist

✅ **最短路径完成首次发布**。

1. 克隆仓库并安装依赖（`pip install -r requirements.txt` 或轻量 `requirements.autopub.txt`）。
2. 更新 `app.py`、`autopub.py` 以及你将运行脚本中的硬编码路径常量。
3. 在 shell profile 或 `.env` 导出所需凭据；运行 `python load_env.py` 验证加载。
4. 创建远程调试浏览器 profile 目录，并为每个平台至少启动一次会话。
5. 在每个目标平台 profile 中手动登录。
6. 启动 API 模式（`python app.py --port 8081`）或 CLI 模式（`python autopub.py --use-cache ...`）。
7. 提交一个示例 ZIP（API 模式）或示例视频（CLI 模式），并检查 `logs/`。
8. 每次 push 前执行 secrets 扫描。

---

<a id="development-notes"></a>
## Development Notes

🧬 **当前开发基线**（手工格式化 + 冒烟测试）。

- Python 风格遵循现有 4 空格缩进与手工格式。
- 目前无正式自动化测试套件；请依赖冒烟测试：
  - 用 `autopub.py` 处理一个示例视频；
  - 向 `/publish` 提交一个 ZIP 并监控 `/publish/queue`；
  - 在每个目标平台手动核验。
- 新增脚本时请提供简短 `if __name__ == "__main__":` 入口，便于快速 dry-run。
- 平台变更尽量隔离（`pub_*`、`login_*`、`ignore_*` 开关）。
- 运行期产物（`videos/*`、`logs*/*`、`transcription_data/*`、`ignore_*`）预期为本地产生，多数已被 git 忽略。

---

<a id="roadmap"></a>
## Roadmap

🗺️ **基于当前代码约束的优先改进方向**。

计划/期望改进（依据当前代码结构与已有说明）：

1. 用集中配置（`.env`/YAML + typed model）替换分散硬编码路径。
2. 移除硬编码 sudo 密码模式，改用更安全的进程控制机制。
3. 通过更强重试与更稳 UI 状态检测提升各平台发布可靠性。
4. 扩展平台支持（例如快手或其他创作者平台）。
5. 将运行时打包成可复现部署单元（容器 + 虚拟显示 profile）。
6. 为 ZIP 协议与队列执行增加自动化集成检查。

---

<a id="contributing"></a>
## Contributing

🤝 请保持 PR 聚焦、可复现，并明确运行时假设。

欢迎贡献。

1. Fork 并创建聚焦分支。
2. 保持提交小而明确，标题使用祈使语（历史示例：“Wait for YouTube checks before publishing”）。
3. 在 PR 中附上手动验证说明：
   - 环境假设，
   - 浏览器/会话重启情况，
   - UI 流程变更相关日志/截图。
4. 不要提交真实密钥（`.env` 已忽略，仅用 `.env.example` 描述结构）。

若引入新发布器模块，请同时接入以下项：
- `pub_<platform>.py`
- 可选 `login_<platform>.py`
- `app.py` 的 API flags 与队列处理
- `autopub.py` 的 CLI 接线（若需要）
- `ignore_<platform>` 开关处理
- README 更新

---

<a id="license"></a>
## License

当前仓库快照中尚无 `LICENSE` 文件。

本草案的假设：
- 在维护者添加明确许可证前，使用与再分发权限均视为未定义。

建议下一步：
- 在仓库顶层新增 `LICENSE`（例如 MIT/Apache-2.0/GPL-3.0），并同步更新本节。

> 📝 在许可证文件落地前，请将商业/内部再分发假设视为未决，并直接向维护者确认。

---

<a id="acknowledgements"></a>
## Acknowledgements

- 维护者与赞助主页：[@lachlanchen](https://github.com/lachlanchen)
- 资金配置来源：[`.github/FUNDING.yml`](.github/FUNDING.yml)
- 本仓库引用的生态服务：Selenium、Tornado、SendGrid、2Captcha、Turing captcha APIs。

---

<a id="support-autopublish"></a>
## Support AutoPublish

💖 社区支持将用于基础设施、可靠性改进和新平台集成。

AutoPublish 是更大范围创作者工具开源实践的一部分，目标是让跨平台发布工具链保持开放且可改造。捐赠将帮助：

- 持续运行 Selenium 集群、处理 API 与云 GPU。
- 交付新发布器（快手、Instagram Reels 等）并持续修复现有 bot 稳定性。
- 输出更多文档、入门数据集与独立创作者教程。

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
