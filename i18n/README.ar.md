[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish


> 🌍 **حالة الترجمة (تم التحقق داخل مساحة العمل هذه في February 28, 2026):**
> يتضمن `i18n/` حاليًا الملفين `README.ar.md` و`README.es.md`؛ أما `README.zh-CN.md` و`README.ja.md` فهما أهداف محجوزة لملفات قادمة.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#prerequisites)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#system-overview)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#running-the-tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#platform-specific-notes)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#running-the-tornado-service-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Arabic%20%7C%20Spanish-0EA5E9)](#table-of-contents)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#license)

حزمة أتمتة لتوزيع محتوى الفيديو القصير على عدة منصات صينية وعالمية للمبدعين. يجمع المشروع بين خدمة مبنية على Tornado، وروبوتات Selenium للأتمتة، وسير عمل محلي لمراقبة الملفات بحيث يؤدي وضع فيديو داخل مجلد في النهاية إلى الرفع إلى XiaoHongShu وDouyin وBilibili وWeChat Channels (ShiPinHao) وInstagram ومع YouTube بشكل اختياري.

المستودع منخفض المستوى عن قصد: معظم الإعدادات موجودة في ملفات Python وسكربتات shell. هذا المستند هو دليل تشغيل يغطي الإعداد ووقت التشغيل ونقاط التوسعة.

> ⚙️ **فلسفة التشغيل**: هذا المشروع يفضّل السكربتات الواضحة وأتمتة المتصفح المباشرة على طبقات التجريد المخفية.
> ✅ **السياسة المعتمدة لهذا README**: الحفاظ على التفاصيل التقنية أولًا ثم تحسين سهولة القراءة والعثور على المعلومات.

## Start Here

إذا كنت جديدًا على هذا المستودع، استخدم التسلسل التالي:

1. اقرأ [Prerequisites](#prerequisites) و[Installation](#installation).
2. اضبط الأسرار والمسارات المطلقة في [Configuration](#configuration).
3. جهّز جلسات تصحيح المتصفح في [Preparing Browser Sessions](#preparing-browser-sessions).
4. اختر وضع تشغيل من [Usage](#usage): `autopub.py` (وضع المراقبة) أو `app.py` (طابور API).
5. تحقّق عبر أوامر [Examples](#examples).

## Overview

يدعم AutoPublish حاليًا وضعين تشغيليين للإنتاج:

1. **وضع CLI watcher (`autopub.py`)** للاستيعاب والنشر اعتمادًا على المجلد.
2. **وضع API queue (`app.py`)** للنشر المعتمد على ZIP عبر HTTP (`/publish`, `/publish/queue`).

تم تصميمه للمشغلين الذين يفضّلون سير عمل شفافًا قائمًا على السكربتات بدل منصات التنسيق المجردة.

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

🎯 **تدفق كامل** من الوسائط الخام إلى المنشورات المنشورة:

نظرة سريعة على سير العمل:

1. **استقبال اللقطات الخام**: ضع فيديو داخل `videos/`. يكتشف المراقب (إما `autopub.py` أو مجدول/خدمة) الملفات الجديدة باستخدام `videos_db.csv` و`processed.csv`.
2. **توليد الأصول**: يرفع `process_video.VideoProcessor` الملف إلى خادم معالجة المحتوى (`upload_url` و`process_url`) الذي يعيد حزمة ZIP تحتوي على:
   - الفيديو المحرر/المشفّر (`<stem>.mp4`)،
   - صورة الغلاف،
   - `{stem}_metadata.json` بعناوين وأوصاف ووسوم مترجمة، إلخ.
3. **النشر**: تقود البيانات الوصفية وحدات النشر Selenium في `pub_*.py`. كل ناشر يتصل بنسخة Chromium/Chrome قيد التشغيل مسبقًا عبر منافذ remote debugging ومجلدات user-data الدائمة.
4. **لوحة تحكم ويب (اختياري)**: يوفّر `app.py` المسار `/publish` ويقبل حِزم ZIP الجاهزة، ويفكها، ويضع مهام النشر في طابور لنفس وحدات النشر. ويمكنه أيضًا تحديث جلسات المتصفح وتشغيل مساعدات تسجيل الدخول (`login_*.py`).
5. **وحدات الدعم**: يقوم `load_env.py` بتحميل الأسرار من `~/.bashrc`، ويوفّر `utils.py` مساعدات مشتركة (تركيز النوافذ، التعامل مع QR، مساعدات البريد)، ويتكامل `solve_captcha_*.py` مع Turing/2Captcha عند ظهور captcha.

## Features

✨ **مصمم لأتمتة عملية وعملية قائمة على السكربتات**:

- نشر متعدد المنصات: XiaoHongShu وDouyin وBilibili وShiPinHao (WeChat Channels) وInstagram وYouTube (اختياري).
- وضعا تشغيل: مسار CLI watcher (`autopub.py`) وخدمة API queue (`app.py` + `/publish` + `/publish/queue`).
- مفاتيح تعطيل مؤقتة لكل منصة عبر ملفات `ignore_*`.
- إعادة استخدام جلسات المتصفح عبر remote debugging مع ملفات تعريف دائمة.
- مساعدات اختيارية لأتمتة QR/captcha وإشعارات البريد الإلكتروني.
- لا حاجة لبناء frontend لاستخدام واجهة الرفع المضمنة PWA (`pwa/`).
- سكربتات أتمتة Linux/Raspberry Pi لإعداد الخدمات (`scripts/`).

### Feature Matrix

| Capability | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Input source | Local `videos/` watcher | Uploaded ZIP via `POST /publish` |
| Queueing | Internal file-based progression | Explicit in-memory job queue |
| Platform flags | CLI args (`--pub-*`) + `ignore_*` | Query args (`publish_*`) + `ignore_*` |
| Best fit | Single-host operator workflow | External systems and remote triggering |

---

## Project Structure

تخطيط عالي المستوى للمصدر/وقت التشغيل:

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

ملاحظة: يتم استخدام `transcription_data/` أثناء وقت التشغيل بواسطة تدفق المعالجة/النشر وقد يظهر بعد التنفيذ.

## Repository Layout

🗂️ **الوحدات الأساسية وما الذي تفعله**:

| Path | Purpose |
| --- | --- |
| `app.py` | خدمة Tornado تعرض `/publish` و`/publish/queue` مع طابور نشر داخلي وخيط عامل. |
| `autopub.py` | مراقب CLI: يفحص `videos/`، يعالج الملفات الجديدة، ويستدعي وحدات النشر بالتوازي. |
| `process_video.py` | يرفع الفيديوهات إلى backend المعالجة ويحفظ حِزم ZIP المُعادة. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | وحدات أتمتة Selenium لكل منصة. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | فحوصات الجلسة وتدفقات تسجيل الدخول عبر QR. |
| `utils.py` | مساعدات أتمتة مشتركة (تركيز النافذة، أدوات QR/mail، أدوات تشخيص). |
| `load_env.py` | يحمّل متغيرات البيئة من ملف shell (`~/.bashrc`) ويخفي القيم الحساسة في السجلات. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | مساعد SMTP/SendGrid وسكربتات اختبار. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | تكاملات حل captcha. |
| `scripts/` | سكربتات إعداد الخدمات والتشغيل (Raspberry Pi/Linux + أتمتة قديمة). |
| `pwa/` | PWA ثابتة لمعاينة ZIP وإرسال طلبات النشر. |
| `setup_raspberrypi.md` | دليل خطوة بخطوة لتجهيز Raspberry Pi. |
| `.env.example` | قالب متغيرات البيئة (بيانات اعتماد، مسارات، مفاتيح captcha). |
| `.github/FUNDING.yml` | إعدادات الرعاية/التمويل. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | نواتج وقت التشغيل والسجلات (الكثير منها متجاهل في git). |

---

## Prerequisites

🧰 **قم بتثبيت هذه المتطلبات قبل أول تشغيل**.

### Operating system and tools

- Linux desktop/server مع جلسة X (`DISPLAY=:1` شائع في السكربتات المرفقة).
- Chromium/Chrome مع ChromeDriver المتوافق.
- مساعدات GUI/وسائط: `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv أو Conda).

### Python dependencies

الحد الأدنى للتشغيل:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

مطابقة المستودع:

```bash
python -m pip install -r requirements.txt
```

للتثبيتات الخفيفة للخدمة (تستخدمها سكربتات الإعداد افتراضيًا):

```bash
python -m pip install -r requirements.autopub.txt
```

يحتوي `requirements.autopub.txt` على:
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Optional: create a sudo user

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## Installation

🚀 **الإعداد من جهاز نظيف**:

1. استنسخ المستودع:

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. أنشئ وفعّل البيئة (مثال باستخدام `venv`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. جهّز متغيرات البيئة:

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. حمّل المتغيرات للسكربتات التي تقرأ قيم ملف shell:

```bash
source ~/.bashrc
python load_env.py
```

ملاحظة: تم تصميم `load_env.py` حول `~/.bashrc`؛ إذا كانت بيئتك تستخدم ملف shell مختلفًا فقم بالتعديل وفق ذلك.

---

## Configuration

🔐 **اضبط بيانات الاعتماد أولًا، ثم تحقق من المسارات الخاصة بالمضيف**.

### Environment variables

يتوقع المشروع بيانات الاعتماد ومسارات اختيارية للمتصفح/التشغيل من متغيرات البيئة. ابدأ من `.env.example`:

| Variable | Description |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | بيانات اعتماد SMTP لإشعارات QR/تسجيل الدخول. |
| `SENDGRID_API_KEY` | مفتاح SendGrid لتدفقات البريد التي تستخدم واجهات SendGrid. |
| `APIKEY_2CAPTCHA` | مفتاح API لخدمة 2Captcha. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | بيانات اعتماد Turing captcha. |
| `DOUYIN_LOGIN_PASSWORD` | مساعد التحقق الثانوي في Douyin. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | تجاوزات Instagram/مشغل المتصفح. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | تجاوزات عالمية مفضلة للمتصفح/الدرايفر/العرض في `app.py`. |

### Path constants (important)

📌 **أكثر مشكلة شائعة عند الإقلاع**: مسارات مطلقة hard-coded غير محلولة.

لا تزال عدة وحدات تحتوي على مسارات hard-coded. حدّثها وفق جهازك:

| File | Constant(s) | Meaning |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | جذور خدمة API ونقاط backend الطرفية. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | جذور CLI watcher ونقاط backend الطرفية. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | مسارات مطلقة إلى Python/Conda/repo/log. | أغلفة قديمة موجهة لـ macOS. |
| `utils.py` | افتراضات مسار FFmpeg في مساعدات معالجة الغلاف. | توافق مسارات أدوات الوسائط. |

ملاحظة مهمة للمستودع:
- مسار المستودع الحالي في مساحة العمل هذه هو `/home/lachlan/ProjectsLFS/AutoPublish`.
- لا يزال بعض الكود والسكربتات يشير إلى `/home/lachlan/Projects/auto-publish` أو `/Users/lachlan/...`.
- احتفظ بهذه المسارات وعدّلها محليًا قبل الاستخدام الإنتاجي.

### Platform toggles via `ignore_*`

🧩 **مفتاح أمان سريع**: إنشاء ملف `ignore_*` يعطّل ذلك الناشر بدون تعديل الكود.

أعلام النشر مرتبطة أيضًا بملفات ignore. أنشئ ملفًا فارغًا لتعطيل منصة:

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

احذف الملف المقابل لإعادة التفعيل.

---

## Preparing Browser Sessions

🌐 **استمرارية الجلسة إلزامية** لنشر Selenium بشكل موثوق.

1. أنشئ مجلدات profiles مخصصة:

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. شغّل جلسات المتصفح مع remote debugging (مثال XiaoHongShu):

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. سجّل الدخول يدويًا مرة واحدة لكل منصة/ملف تعريف.

4. تحقّق أن Selenium يستطيع الاتصال:

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

ملاحظة أمنية:
- يحتوي `app.py` حاليًا على قيمة sudo password تجريبية hard-coded (`password = "1"`) مستخدمة ضمن منطق إعادة تشغيل المتصفح. استبدلها قبل أي نشر فعلي.

---

## Usage

▶️ **يتوفر وضعا تشغيل**: CLI watcher وخدمة API queue.

### Running the CLI pipeline (`autopub.py`)

1. ضع فيديوهات المصدر في مجلد المراقبة (`videos/` أو `autopublish_folder_path` المضبوط لديك).
2. شغّل:

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

الأعلام:

| Flag | Meaning |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | تقييد النشر للمنصات المحددة. إذا لم تمرّر أيًا منها، يتم تفعيل الثلاثة افتراضيًا. |
| `--test` | وضع اختبار يُمرر إلى وحدات النشر (السلوك يختلف حسب وحدة المنصة). |
| `--use-cache` | إعادة استخدام `transcription_data/<video>/<video>.zip` الموجود إن توفّر. |

تدفق CLI لكل فيديو:
- رفع/معالجة عبر `process_video.py`.
- فك ZIP إلى `transcription_data/<video>/`.
- تشغيل الناشرين المحددين عبر `ThreadPoolExecutor`.
- إلحاق حالة التتبع داخل `videos_db.csv` و`processed.csv`.

### Running the Tornado service (`app.py`)

🛰️ **وضع API** مفيد للأنظمة الخارجية التي تنتج حِزم ZIP.

بدء الخادم:

```bash
python app.py --refresh-time 1800 --port 8081
```

ملخص endpoints:

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/publish` | `POST` | رفع بايتات ZIP ووضع مهمة نشر في الطابور |
| `/publish/queue` | `GET` | فحص الطابور، وسجل المهام، وحالة النشر |

### `POST /publish`

📤 **ضع مهمة نشر في الطابور** عبر رفع بايتات ZIP مباشرة.

- Header: `Content-Type: application/octet-stream`
- وسيط query/form مطلوب: `filename` (اسم ملف ZIP)
- قيم منطقية اختيارية: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: بايتات ZIP خام

مثال:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

السلوك الحالي في الكود:
- يتم قبول الطلب ووضعه في الطابور.
- الاستجابة الفورية تُرجع JSON يتضمن `status: queued` و`job_id` و`queue_size`.
- خيط عامل يعالج المهام المتراصة تسلسليًا.

### `GET /publish/queue`

📊 **راقب صحة الطابور والمهام قيد التنفيذ**.

يرجع JSON لحالة/سجل الطابور:

```bash
curl "http://localhost:8081/publish/queue"
```

حقول الاستجابة تشمل:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Browser refresh thread

♻️ التحديث الدوري للمتصفح يقلل فشل الجلسات القديمة خلال فترات التشغيل الطويلة.

يشغّل `app.py` خيط تحديث بالخلفية باستخدام فترة `--refresh-time` ويربطها بفحوصات تسجيل الدخول. يتضمن نوم التحديث سلوك تأخير عشوائي.

### PWA frontend (`pwa/`)

🖥️ واجهة ثابتة خفيفة للرفع اليدوي لملفات ZIP وفحص الطابور.

شغّل الواجهة محليًا:

```bash
cd pwa
python -m http.server 5173
```

افتح `http://localhost:5173` واضبط عنوان backend الأساسي (مثلًا `http://lazyingart:8081`).

قدرات PWA:
- معاينة ZIP بالسحب والإفلات.
- مفاتيح تفعيل أهداف النشر + وضع اختبار.
- الإرسال إلى `/publish` والاستطلاع لـ `/publish/queue`.

---

## Examples

🧪 **أوامر smoke test جاهزة للنسخ/اللصق**:

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

📦 **عقد ZIP مهم**: أبقِ أسماء الملفات ومفاتيح metadata متوافقة مع توقعات وحدات النشر.

المحتويات الدنيا المتوقعة داخل ZIP:

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

يقود `metadata` ناشري CN؛ والاختياري `metadata["english_version"]` يغذّي ناشر YouTube.

حقول تستخدمها الوحدات غالبًا:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (قائمة hashtags)
- `video_filename`, `cover_filename`
- حقول خاصة بالمنصة كما هو مطبق داخل ملفات `pub_*.py`

إذا كنت تولد ملفات ZIP خارجيًا، حافظ على توافق المفاتيح وأسماء الملفات مع توقعات الوحدات.

---

## Platform-Specific Notes

🧭 **خريطة المنافذ + الوحدات المسؤولة** لكل ناشر.

| Platform | Port | Module(s) | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | تدفق إعادة تسجيل الدخول عبر QR؛ تنظيف العنوان واستخدام hashtags من metadata. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | فحوص اكتمال الرفع ومسارات إعادة المحاولة هشة حسب المنصة؛ راقب السجلات بعناية. |
| Bilibili | 5005 | `pub_bilibili.py` | تتوفر نقاط ربط captcha عبر `solve_captcha_2captcha.py` و`solve_captcha_turing.py`. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | موافقة QR السريعة مهمة لموثوقية تحديث الجلسة. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | يتم التحكم به في وضع API عبر `publish_instagram=true`؛ متغيرات البيئة متاحة في `.env.example`. |
| YouTube | 9222 | `pub_y2b.py` | يستخدم كتلة metadata `english_version`؛ عطّله عبر `ignore_y2b`. |

---

## Raspberry Pi / Linux Service Setup

🐧 **موصى به للمضيفات العاملة دائمًا**.

لإعداد مضيف كامل، اتبع [`setup_raspberrypi.md`](setup_raspberrypi.md).

إعداد سريع للمسار:

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

يقوم هذا بتنسيق:
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

شغّل الخدمة يدويًا عبر tmux:

```bash
./scripts/start_autopub_tmux.sh
```

تحقق من الخدمات/المنافذ:

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## Legacy macOS Scripts

🍎 ما زالت الأغلفة القديمة موجودة للتوافق مع إعدادات محلية أقدم.

لا يزال المستودع يتضمن أغلفة قديمة موجهة لـ macOS:
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

تحتوي هذه الملفات على مسارات مطلقة `/Users/lachlan/...` وافتراضات Conda. احتفظ بها إذا كنت تعتمد هذا المسار، لكن حدّث المسارات/venv/الأدوات وفق جهازك.

---

## Troubleshooting & Maintenance

🛠️ **إذا حدث فشل، ابدأ من هنا أولًا**.

- **انحراف المسارات بين الأجهزة**: إذا ظهرت أخطاء عن ملفات مفقودة تحت `/Users/lachlan/...` أو `/home/lachlan/Projects/auto-publish` فقم بمواءمة الثوابت مع مسار جهازك (`/home/lachlan/ProjectsLFS/AutoPublish` في مساحة العمل هذه).
- **نظافة الأسرار**: شغّل `~/.local/bin/detect-secrets scan` قبل كل push. قم بتدوير أي بيانات اعتماد مسرّبة.
- **أخطاء backend المعالجة**: إذا طبع `process_video.py` الرسالة “Failed to get the uploaded file path,” فتحقق من أن JSON استجابة الرفع يحتوي `file_path` وأن endpoint المعالجة يعيد بايتات ZIP.
- **عدم توافق ChromeDriver**: إذا ظهرت أخطاء اتصال DevTools فطابق إصدارات Chrome/Chromium مع الدرايفر (أو بدّل إلى `webdriver-manager`).
- **مشكلات تركيز المتصفح**: تعتمد `bring_to_front` على مطابقة عنوان النافذة (اختلافات تسمية Chromium/Chrome قد تكسرها).
- **انقطاعات captcha**: اضبط بيانات اعتماد 2Captcha/Turing وادمج مخرجات solver حيث يلزم.
- **ملفات lock قديمة**: إذا لم تبدأ التشغيلات المجدولة، تحقق من حالة العمليات واحذف `autopub.lock` القديم (تدفق السكربتات القديمة).
- **سجلات للفحص**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log` إضافة إلى سجلات service journal.

---

## Extending the System

🧱 **نقاط التوسعة** للمنصات الجديدة وعمليات أكثر أمانًا.

- **إضافة منصة جديدة**: انسخ وحدة `pub_*.py`، وحدّث selectors/flows، وأضف `login_*.py` إذا كانت إعادة المصادقة عبر QR مطلوبة، ثم اربط الأعلام ومعالجة الطابور في `app.py` وربط CLI في `autopub.py`.
- **تجريد الإعدادات**: انقل الثوابت المتناثرة إلى إعدادات منظمة (`config.yaml`/`.env` + نموذج typed) لتشغيل متعدد المضيفات.
- **تقوية تخزين بيانات الاعتماد**: استبدل التدفقات الحساسة hard-coded أو المعروضة عبر shell بإدارة أسرار آمنة (`sudo -A`, keychain, vault/secret manager).
- **الحاويات**: حزّم Chromium/ChromeDriver + بيئة Python + شاشة افتراضية في وحدة نشر واحدة قابلة للنشر على السحابة/الخوادم.

---

## Quick Start Checklist

✅ **أقصر مسار لأول نشر ناجح**.

1. استنسخ هذا المستودع وثبّت الاعتماديات (`pip install -r requirements.txt` أو الخفيف `requirements.autopub.txt`).
2. حدّث ثوابت المسارات hard-coded في `app.py` و`autopub.py` وأي سكربت ستشغّله.
3. صدّر بيانات الاعتماد المطلوبة في ملف shell profile أو `.env`؛ وشغّل `python load_env.py` للتحقق من التحميل.
4. أنشئ مجلدات browser profile عبر remote-debug وشغّل كل جلسة منصة مطلوبة مرة واحدة.
5. سجّل الدخول يدويًا على كل منصة مستهدفة داخل ملف التعريف الخاص بها.
6. شغّل إما وضع API (`python app.py --port 8081`) أو وضع CLI (`python autopub.py --use-cache ...`).
7. أرسل ZIP تجريبيًا واحدًا (وضع API) أو ملف فيديو تجريبيًا واحدًا (وضع CLI) وافحص `logs/`.
8. شغّل فحص الأسرار قبل كل push.

---

## Development Notes

🧬 **الخط الأساسي الحالي للتطوير** (تنسيق يدوي + اختبارات smoke).

- نمط Python يتبع تنسيق 4 مسافات الحالي والتنسيق اليدوي.
- لا توجد حاليًا مجموعة اختبارات آلية رسمية؛ اعتمد على smoke tests:
  - معالجة فيديو تجريبي عبر `autopub.py`؛
  - إرسال ZIP واحد إلى `/publish` ومراقبة `/publish/queue`؛
  - التحقق يدويًا من كل منصة مستهدفة.
- أضف نقطة دخول صغيرة `if __name__ == "__main__":` عند إنشاء سكربتات جديدة لتجارب dry-run السريعة.
- افصل تغييرات المنصات قدر الإمكان (`pub_*`, `login_*`, مفاتيح `ignore_*`).
- نواتج وقت التشغيل (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) متوقعة محليًا ومعظمها متجاهل في git.

---

## Roadmap

🗺️ **تحسينات ذات أولوية تعكس قيود الكود الحالي**.

التحسينات المخطط/المرغوب بها (استنادًا إلى بنية الكود الحالية والملاحظات الموجودة):

1. استبدال المسارات hard-coded المتناثرة بإعداد مركزي (`.env`/YAML + نماذج typed).
2. إزالة أنماط كلمات مرور sudo hard-coded ونقل التحكم بالعمليات إلى آليات أكثر أمانًا.
3. تحسين موثوقية النشر عبر إعادة محاولات أقوى واكتشاف أفضل لحالة واجهة المستخدم لكل منصة.
4. توسيع دعم المنصات (مثل Kuaishou أو منصات مبدعين أخرى).
5. تغليف وقت التشغيل في وحدات نشر قابلة لإعادة الإنتاج (container + virtual display profile).
6. إضافة فحوص تكامل آلية لعقد ZIP وتنفيذ الطابور.

---

## Contributing

🤝 اجعل طلبات PR مركزة، قابلة لإعادة التنفيذ، وواضحة في افتراضات وقت التشغيل.

المساهمات مرحب بها.

1. Fork للمستودع وأنشئ فرعًا مركزًا.
2. اجعل الـ commits صغيرة وبصيغة فعل أمر (نمط مثال في السجل: “Wait for YouTube checks before publishing”).
3. أدرج ملاحظات تحقق يدوي في PR:
   - افتراضات البيئة،
   - إعادة تشغيل المتصفح/الجلسة،
   - سجلات/لقطات شاشة ذات صلة لتغييرات تدفقات الواجهة.
4. لا تقم أبدًا بعمل commit لأسرار حقيقية (`.env` متجاهل؛ استخدم `.env.example` للبنية فقط).

عند إدخال وحدات ناشر جديدة، اربط كل ما يلي:
- `pub_<platform>.py`
- `login_<platform>.py` الاختياري
- أعلام API ومعالجة الطابور في `app.py`
- ربط CLI في `autopub.py` (إذا لزم)
- معالجة مفاتيح `ignore_<platform>`
- تحديثات README

---

## License

لا يوجد حاليًا ملف `LICENSE` في هذا snapshot من المستودع.

افتراض هذا المسودة:
- اعتبر الاستخدام وإعادة التوزيع غير محددين حتى يضيف المشرف ملف ترخيص صريحًا.

الإجراء التالي الموصى به:
- أضف `LICENSE` على مستوى الجذر (مثل MIT/Apache-2.0/GPL-3.0) وحدّث هذا القسم وفقًا لذلك.

> 📝 إلى أن تتم إضافة ملف ترخيص، اعتبر افتراضات إعادة التوزيع التجاري/الداخلي غير محسومة وأكّدها مباشرة مع المشرف.

---

## Acknowledgements

- ملف المشرف والراعي: [@lachlanchen](https://github.com/lachlanchen)
- مصدر إعدادات التمويل: [`.github/FUNDING.yml`](.github/FUNDING.yml)
- خدمات النظام البيئي المشار إليها في هذا المستودع: Selenium, Tornado, SendGrid, 2Captcha, Turing captcha APIs.

---

## Support AutoPublish

💖 دعم المجتمع يمول البنية التحتية وأعمال الموثوقية وتكاملات المنصات الجديدة.

يقع AutoPublish ضمن جهد أوسع لإبقاء أدوات المبدعين متعددة المنصات مفتوحة وقابلة للتعديل. تساعد التبرعات على:

- إبقاء Selenium farm وواجهة برمجة المعالجة ومعالجات GPU السحابية قيد التشغيل.
- شحن ناشرين جدد (Kuaishou وInstagram Reels وغيرها) إضافة إلى إصلاحات موثوقية للبوتات الحالية.
- مشاركة المزيد من الوثائق ومجموعات البيانات التمهيدية والدروس للمبدعين المستقلين.

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
