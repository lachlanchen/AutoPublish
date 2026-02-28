[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish

> 🌍 **Статус локализации (проверено в этом workspace 28 февраля 2026):**
> `i18n/` сейчас содержит `README.ar.md` и `README.es.md`; `README.zh-CN.md` и `README.ja.md` зарезервированы для следующих файлов.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#prerequisites)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#system-overview)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#running-the-tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#platform-specific-notes)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#running-the-tornado-service-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Arabic%20%7C%20Spanish-0EA5E9)](#table-of-contents)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#license)

Набор инструментов автоматизации для публикации коротких видео на нескольких китайских и международных платформах для авторов. Проект сочетает сервис на Tornado, Selenium-ботов и локальный workflow с наблюдением за папкой, чтобы добавление видео в каталог в итоге приводило к загрузке на XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), Instagram и, при необходимости, YouTube.

Репозиторий намеренно остаётся низкоуровневым: большая часть конфигурации находится в Python-файлах и shell-скриптах. Этот документ — операционное руководство по настройке, запуску и точкам расширения.

> ⚙️ **Операционная философия**: проект делает ставку на явные скрипты и прямую автоматизацию браузера вместо скрытых слоёв абстракции.
> ✅ **Каноническая политика для этого README**: сохранять технические детали и повышать читаемость/находимость.

## Начните здесь

Если вы впервые в этом репозитории, используйте такую последовательность:

1. Прочитайте [Prerequisites](#prerequisites) и [Installation](#installation).
2. Настройте секреты и абсолютные пути в [Configuration](#configuration).
3. Подготовьте сессии браузера в [Preparing Browser Sessions](#preparing-browser-sessions).
4. Выберите один режим запуска из [Usage](#usage): `autopub.py` (watcher) или `app.py` (API queue).
5. Проверьте работу командами из [Examples](#examples).

## Обзор

Сейчас AutoPublish поддерживает два рабочих режима исполнения:

1. **Режим CLI watcher (`autopub.py`)** для приёма файлов из папки и публикации.
2. **Режим API queue (`app.py`)** для публикации ZIP через HTTP (`/publish`, `/publish/queue`).

Проект ориентирован на операторов, которым важен прозрачный script-first workflow вместо абстрактных платформ оркестрации.

### Кратко о режимах запуска

| Режим | Точка входа | Вход | Лучшее применение | Поведение на выходе |
| --- | --- | --- | --- | --- |
| CLI watcher | `autopub.py` | Файлы, помещённые в `videos/` | Локальные operator workflow и циклы cron/service | Обрабатывает найденные видео и сразу публикует на выбранные платформы |
| API queue service | `app.py` | Загрузка ZIP в `POST /publish` | Интеграции с upstream-системами и удалённый триггер | Принимает задания, ставит их в очередь и выполняет публикацию в порядке worker |

## Быстрый снимок

| Что | Значение |
| --- | --- |
| Основной язык | Python 3.10+ |
| Основные runtime | CLI watcher (`autopub.py`) + Tornado queue service (`app.py`) |
| Движок автоматизации | Selenium + remote-debug Chromium sessions |
| Форматы входа | Raw video (`videos/`) и ZIP-бандлы (`/publish`) |
| Текущий путь репозитория в workspace | `/home/lachlan/ProjectsLFS/AutoPublish` |
| Идеальные пользователи | Creator/ops-инженеры, управляющие multi-platform short video pipelines |

### Снимок по операционной безопасности

| Тема | Текущее состояние | Действие |
| --- | --- | --- |
| Жёстко заданные пути | Есть в нескольких модулях/скриптах | Обновите константы путей под хост перед production-запуском |
| Состояние логина в браузере | Обязательно | Храните постоянные remote-debug профили по платформам |
| Работа с captcha | Доступны опциональные интеграции | Настройте 2Captcha/Turing credentials при необходимости |
| Декларация лицензии | Не обнаружен top-level файл `LICENSE` | Уточните условия использования у maintainer перед распространением |

---

## Содержание

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

## Обзор системы

🎯 **Сквозной поток** от исходных медиа до опубликованных постов:

Workflow в целом:

1. **Приём сырого видео**: Поместите видео в `videos/`. Watcher (либо `autopub.py`, либо scheduler/service) замечает новые файлы с помощью `videos_db.csv` и `processed.csv`.
2. **Генерация ассетов**: `process_video.VideoProcessor` загружает файл на сервер обработки контента (`upload_url` и `process_url`), который возвращает ZIP-пакет с:
   - отредактированным/перекодированным видео (`<stem>.mp4`),
   - обложкой,
   - `{stem}_metadata.json` с локализованными заголовками, описаниями, тегами и т.д.
3. **Публикация**: Метаданные управляют Selenium-паблишерами в `pub_*.py`. Каждый паблишер подключается к уже запущенному Chromium/Chrome через порты remote debugging и постоянные user-data директории.
4. **Web control plane (опционально)**: `app.py` открывает `/publish`, принимает заранее собранные ZIP-бандлы, распаковывает их и ставит задания публикации в очередь к тем же паблишерам. Также может обновлять browser sessions и запускать login helpers (`login_*.py`).
5. **Вспомогательные модули**: `load_env.py` подтягивает секреты из `~/.bashrc`, `utils.py` содержит helpers (фокус окна, QR handling, mail utility helpers), а `solve_captcha_*.py` интегрируется с Turing/2Captcha при появлении captcha.

## Возможности

✨ **Сделано для прагматичной script-first автоматизации**:

- Публикация на несколько платформ: XiaoHongShu, Douyin, Bilibili, ShiPinHao (WeChat Channels), Instagram, YouTube (опционально).
- Два режима работы: CLI watcher pipeline (`autopub.py`) и API queue service (`app.py` + `/publish` + `/publish/queue`).
- Временное отключение платформ через `ignore_*` файлы.
- Повторное использование browser-session через remote debugging с постоянными профилями.
- Опциональная автоматизация QR/captcha и email-notification helpers.
- Для включённого PWA (`pwa/`) uploader UI не требуется сборка frontend.
- Скрипты Linux/Raspberry Pi для настройки сервисов (`scripts/`).

### Матрица возможностей

| Capability | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Источник входа | Локальный watcher `videos/` | Загруженный ZIP через `POST /publish` |
| Очередь | Внутреннее продвижение на основе файлов | Явная in-memory очередь заданий |
| Флаги платформ | CLI args (`--pub-*`) + `ignore_*` | Query args (`publish_*`) + `ignore_*` |
| Лучший сценарий | Workflow оператора на одном хосте | Внешние системы и удалённый триггер |

---

## Структура проекта

Высокоуровневая структура исходников/runtime:

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

Примечание: `transcription_data/` используется во время выполнения процессом обработки/публикации и может появиться после запуска.

## Layout репозитория

🗂️ **Ключевые модули и их назначение**:

| Path | Назначение |
| --- | --- |
| `app.py` | Tornado-сервис с `/publish` и `/publish/queue`, с внутренней очередью публикаций и worker thread. |
| `autopub.py` | CLI watcher: сканирует `videos/`, обрабатывает новые файлы и параллельно вызывает паблишеры. |
| `process_video.py` | Загружает видео в backend обработки и сохраняет возвращённые ZIP-бандлы. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | Selenium automation модули по платформам. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | Проверки сессии и QR-login flow. |
| `utils.py` | Общие automation helpers (фокус окна, QR/mail utility helpers, diagnostics helpers). |
| `load_env.py` | Загружает env vars из shell profile (`~/.bashrc`) и маскирует чувствительные логи. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | SMTP/SendGrid helper и test scripts. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Интеграции с captcha-солверами. |
| `scripts/` | Скрипты настройки сервисов и операций (Raspberry Pi/Linux + legacy automation). |
| `pwa/` | Статический PWA для предпросмотра ZIP и отправки на публикацию. |
| `setup_raspberrypi.md` | Пошаговое руководство по развёртыванию Raspberry Pi. |
| `.env.example` | Шаблон переменных окружения (credentials, paths, captcha keys). |
| `.github/FUNDING.yml` | Конфигурация sponsor/funding. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | Runtime-артефакты и логи (многие gitignored). |

---

## Prerequisites

🧰 **Установите это перед первым запуском**.

### Операционная система и инструменты

- Linux desktop/server с X session (`DISPLAY=:1` часто используется в предоставленных скриптах).
- Chromium/Chrome и соответствующий ChromeDriver.
- GUI/media helpers: `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv или Conda).

### Python зависимости

Минимальный runtime-набор:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

Паритет с репозиторием:

```bash
python -m pip install -r requirements.txt
```

Для облегчённой установки сервиса (по умолчанию используется setup-скриптами):

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` содержит:
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Опционально: создать sudo-пользователя

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## Installation

🚀 **Настройка на чистой машине**:

1. Клонируйте репозиторий:

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. Создайте и активируйте окружение (пример с `venv`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. Подготовьте переменные окружения:

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. Загрузите переменные для скриптов, которые читают значения shell profile:

```bash
source ~/.bashrc
python load_env.py
```

Примечание: `load_env.py` ориентирован на `~/.bashrc`; если у вас используется другой профиль shell, адаптируйте его соответствующим образом.

---

## Configuration

🔐 **Сначала задайте credentials, затем проверьте host-specific пути**.

### Переменные окружения

Проект ожидает credentials и опциональные пути браузера/runtime через переменные окружения. Начните с `.env.example`:

| Variable | Description |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | SMTP credentials для QR/login уведомлений. |
| `SENDGRID_API_KEY` | Ключ SendGrid для email flow, использующих SendGrid API. |
| `APIKEY_2CAPTCHA` | API key для 2Captcha. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Credentials Turing captcha. |
| `DOUYIN_LOGIN_PASSWORD` | Помощник для второй проверки Douyin. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Instagram/browser driver overrides. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | Предпочитаемые глобальные browser/driver/display overrides в `app.py`. |

### Константы путей (важно)

📌 **Самая частая проблема при старте**: неразрешённые жёстко заданные абсолютные пути.

В нескольких модулях всё ещё есть hard-coded пути. Обновите их под ваш хост:

| File | Constant(s) | Meaning |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | Корни API-сервиса и backend endpoints. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | Корни CLI watcher и backend endpoints. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Абсолютные пути к Python/Conda/repo/log location. | Legacy/macOS-ориентированные обёртки. |
| `utils.py` | Предположения о пути FFmpeg в helper-функциях обработки обложки. | Совместимость путей медиа-инструментов. |

Важное замечание по репозиторию:
- Текущий путь репозитория в этом workspace: `/home/lachlan/ProjectsLFS/AutoPublish`.
- Часть кода и скриптов всё ещё ссылается на `/home/lachlan/Projects/auto-publish` или `/Users/lachlan/...`.
- Сохраните и скорректируйте эти пути локально перед использованием в production.

### Platform toggles через `ignore_*`

🧩 **Быстрый safety switch**: создание `ignore_*` файла отключает соответствующий publisher без правок кода.

Флаги публикации также ограничиваются ignore-файлами. Создайте пустой файл, чтобы отключить платформу:

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

Удалите соответствующий файл, чтобы включить обратно.

---

## Preparing Browser Sessions

🌐 **Постоянство сессий обязательно** для надёжной Selenium-публикации.

1. Создайте выделенные директории профилей:

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. Запустите browser sessions с remote debugging (пример для XiaoHongShu):

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. Один раз выполните ручной вход для каждой платформы/профиля.

4. Проверьте, что Selenium может подключиться:

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Замечание по безопасности:
- `app.py` сейчас содержит hard-coded placeholder sudo-пароля (`password = "1"`), используемый логикой перезапуска браузера. Замените его перед реальным deployment.

---

## Usage

▶️ **Доступны два runtime-режима**: CLI watcher и API queue service.

### Запуск CLI pipeline (`autopub.py`)

1. Поместите исходные видео в директорию наблюдения (`videos/` или ваш настроенный `autopublish_folder_path`).
2. Выполните:

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Флаги:

| Flag | Meaning |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Ограничить публикацию выбранными платформами. Если ни один не указан, по умолчанию включены все три. |
| `--test` | Тестовый режим, передаваемый в паблишеры (поведение зависит от модуля платформы). |
| `--use-cache` | Использовать существующий `transcription_data/<video>/<video>.zip`, если доступен. |

CLI flow для каждого видео:
- Upload/process через `process_video.py`.
- Извлечение ZIP в `transcription_data/<video>/`.
- Запуск выбранных паблишеров через `ThreadPoolExecutor`.
- Добавление tracking state в `videos_db.csv` и `processed.csv`.

### Запуск Tornado service (`app.py`)

🛰️ **API-режим** удобен для внешних систем, которые создают ZIP-бандлы.

Запуск сервера:

```bash
python app.py --refresh-time 1800 --port 8081
```

Кратко по endpoint API:

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/publish` | `POST` | Загрузить ZIP bytes и поставить задание публикации в очередь |
| `/publish/queue` | `GET` | Просмотреть очередь, историю заданий и состояние публикации |

### `POST /publish`

📤 **Поставьте задачу публикации в очередь**, напрямую загрузив ZIP bytes.

- Заголовок: `Content-Type: application/octet-stream`
- Обязательный query/form arg: `filename` (имя ZIP-файла)
- Опциональные boolean: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: raw ZIP bytes

Пример:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

Текущее поведение в коде:
- Запрос принимается и ставится в очередь.
- Немедленный ответ возвращает JSON, включающий `status: queued`, `job_id` и `queue_size`.
- Worker thread последовательно обрабатывает задания из очереди.

### `GET /publish/queue`

📊 **Наблюдайте за состоянием очереди и текущими задачами**.

Возвращает JSON со статусом/историей очереди:

```bash
curl "http://localhost:8081/publish/queue"
```

Поля ответа включают:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Поток обновления браузера

♻️ Периодическое обновление браузера снижает ошибки устаревших сессий при длительном uptime.

`app.py` запускает фоновый поток обновления с интервалом `--refresh-time` и хуками проверок логина. Sleep во время refresh включает рандомизированную задержку.

### PWA frontend (`pwa/`)

🖥️ Лёгкий статический UI для ручной загрузки ZIP и проверки очереди.

Запуск статического UI локально:

```bash
cd pwa
python -m http.server 5173
```

Откройте `http://localhost:5173` и задайте backend base URL (например, `http://lazyingart:8081`).

Возможности PWA:
- Drag/drop предпросмотр ZIP.
- Переключатели целевых платформ + test mode.
- Отправка на `/publish` и опрос `/publish/queue`.

---

## Examples

🧪 **Команды smoke-test для copy/paste**:

### Example 0: Загрузка окружения и запуск API-сервера

```bash
source ~/.bashrc
python load_env.py
python app.py --refresh-time 1800 --port 8081
```

### Example A: Запуск CLI-публикации

```bash
python autopub.py --pub-xhs --pub-douyin --use-cache
```

### Example B: API-публикация (один ZIP)

```bash
curl -X POST "http://localhost:8081/publish?filename=my_bundle.zip&publish_bilibili=true&test=true" \
  --data-binary @my_bundle.zip \
  -H "Content-Type: application/octet-stream"
```

### Example C: Проверка статуса очереди

```bash
curl -s "http://localhost:8081/publish/queue"
```

### Example D: Smoke test SMTP helper

```bash
python smtp.py
python smtp_test_simple.py
```

---

## Metadata & ZIP Format

📦 **Контракт ZIP важен**: держите имена файлов и ключи метаданных согласованными с ожиданиями паблишеров.

Ожидаемое содержимое ZIP (минимум):

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` управляет CN-паблишерами; опциональный `metadata["english_version"]` используется паблишером YouTube.

Поля, часто используемые модулями:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (список hashtags)
- `video_filename`, `cover_filename`
- platform-specific поля согласно реализации в соответствующих `pub_*.py`

Если вы генерируете ZIP извне, держите ключи и имена файлов в соответствии с ожиданиями модулей.

---

## Platform-Specific Notes

🧭 **Карта портов + ответственность модулей** по каждому publisher.

| Platform | Port | Module(s) | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | QR re-login flow; санитаризация заголовка и использование hashtags из metadata. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Проверки завершения загрузки и retry paths платформенно хрупкие; внимательно мониторьте логи. |
| Bilibili | 5005 | `pub_bilibili.py` | Доступны captcha hooks через `solve_captcha_2captcha.py` и `solve_captcha_turing.py`. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Быстрое подтверждение QR важно для надёжности обновления сессии. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | Управляется в API-режиме через `publish_instagram=true`; env vars доступны в `.env.example`. |
| YouTube | 9222 | `pub_y2b.py` | Использует блок metadata `english_version`; отключается через `ignore_y2b`. |

---

## Raspberry Pi / Linux Service Setup

🐧 **Рекомендуется для always-on хостов**.

Для полного bootstrap хоста используйте [`setup_raspberrypi.md`](setup_raspberrypi.md).

Быстрая настройка pipeline:

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

Это оркестрирует:
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

Ручной запуск сервиса в tmux:

```bash
./scripts/start_autopub_tmux.sh
```

Проверка сервисов/портов:

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## Legacy macOS Scripts

🍎 Legacy-обёртки остаются для совместимости со старыми локальными setup.

Репозиторий всё ещё содержит legacy macOS-ориентированные обёртки:
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

Они содержат абсолютные пути `/Users/lachlan/...` и предположения о Conda. Сохраняйте их, если используете этот workflow, но обновите paths/venv/tooling под ваш хост.

---

## Troubleshooting & Maintenance

🛠️ **Если что-то сломалось, начинайте отсюда**.

- **Path drift между машинами**: если ошибки указывают на отсутствующие файлы в `/Users/lachlan/...` или `/home/lachlan/Projects/auto-publish`, выровняйте константы с путём вашего хоста (`/home/lachlan/ProjectsLFS/AutoPublish` в этом workspace).
- **Гигиена секретов**: запускайте `~/.local/bin/detect-secrets scan` перед push. Ротируйте любые утёкшие credentials.
- **Ошибки backend обработки**: если `process_video.py` печатает “Failed to get the uploaded file path,” проверьте, что upload response JSON содержит `file_path`, а endpoint обработки возвращает ZIP bytes.
- **Несовпадение ChromeDriver**: при ошибках DevTools connection выровняйте версии Chrome/Chromium и драйвера (или переключитесь на `webdriver-manager`).
- **Проблемы с фокусом окна браузера**: `bring_to_front` зависит от совпадения заголовка окна (различия в именовании Chromium/Chrome могут ломать это).
- **Прерывания captcha**: настройте credentials для 2Captcha/Turing и интегрируйте вывод solvers при необходимости.
- **Устаревшие lock-файлы**: если запуски по расписанию никогда не стартуют, проверьте состояние процесса и удалите stale `autopub.lock` (legacy script flow).
- **Логи для проверки**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log`, а также service journal logs.

---

## Extending the System

🧱 **Точки расширения** для новых платформ и более безопасной эксплуатации.

- **Добавление новой платформы**: скопируйте модуль `pub_*.py`, обновите selectors/flows, добавьте `login_*.py`, если нужна QR re-auth, затем подключите флаги и обработку очереди в `app.py`, а также CLI wiring в `autopub.py`.
- **Абстракция конфигурации**: перенесите разрозненные константы в структурированный config (`config.yaml`/`.env` + typed model) для multi-host эксплуатации.
- **Усиление хранения credentials**: замените hard-coded или shell-exposed чувствительные потоки на безопасное secret management (`sudo -A`, keychain, vault/secret manager).
- **Контейнеризация**: упакуйте Chromium/ChromeDriver + Python runtime + virtual display в единый deployable unit для cloud/server использования.

---

## Quick Start Checklist

✅ **Минимальный путь к первой успешной публикации**.

1. Клонируйте этот репозиторий и установите зависимости (`pip install -r requirements.txt` или облегчённый `requirements.autopub.txt`).
2. Обновите hard-coded path-константы в `app.py`, `autopub.py` и любом скрипте, который будете запускать.
3. Экспортируйте обязательные credentials в профиль shell или `.env`; запустите `python load_env.py`, чтобы проверить загрузку.
4. Создайте директории browser profile для remote-debug и запустите каждую нужную платформенную сессию хотя бы один раз.
5. Вручную войдите на каждой целевой платформе в её профиле.
6. Запустите либо API-режим (`python app.py --port 8081`), либо CLI-режим (`python autopub.py --use-cache ...`).
7. Отправьте один тестовый ZIP (API-режим) или один тестовый видеофайл (CLI-режим) и проверьте `logs/`.
8. Перед каждым push запускайте сканирование секретов.

---

## Development Notes

🧬 **Текущая база разработки** (ручное форматирование + smoke testing).

- Стиль Python следует существующему 4-space indentation и ручному форматированию.
- Формального автоматизированного тестового набора пока нет; используйте smoke tests:
  - обработайте один тестовый видеофайл через `autopub.py`;
  - отправьте один ZIP в `/publish` и отслеживайте `/publish/queue`;
  - вручную проверьте каждую целевую платформу.
- При добавлении новых скриптов включайте небольшой entrypoint `if __name__ == "__main__":` для быстрых dry-run.
- По возможности изолируйте платформенные изменения (`pub_*`, `login_*`, `ignore_*` toggles).
- Runtime-артефакты (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) ожидаемо локальные и в основном игнорируются git.

---

## Roadmap

🗺️ **Приоритетные улучшения, отражённые текущими ограничениями кода**.

Планируемые/желаемые улучшения (на основе текущей структуры кода и существующих заметок):

1. Заменить разрозненные hard-coded paths на централизованный config (`.env`/YAML + typed models).
2. Удалить hard-coded паттерны sudo-пароля и перевести управление процессами на более безопасные механизмы.
3. Повысить надёжность публикации за счёт более сильных retry и лучшего определения UI-state по платформам.
4. Расширить поддержку платформ (например, Kuaishou и другие creator-платформы).
5. Упаковать runtime в воспроизводимые deployable units (container + virtual display profile).
6. Добавить автоматизированные интеграционные проверки ZIP-контракта и исполнения очереди.

---

## Contributing

🤝 Делайте PR сфокусированными, воспроизводимыми и явно указывайте runtime assumptions.

Вклады приветствуются.

1. Сделайте fork и создайте сфокусированную ветку.
2. Держите коммиты небольшими и в imperative style (пример в истории: “Wait for YouTube checks before publishing”).
3. Добавляйте в PR заметки о ручной проверке:
   - предположения по окружению,
   - перезапуски браузера/сессий,
   - релевантные логи/скриншоты для изменений UI flow.
4. Никогда не коммитьте реальные секреты (`.env` игнорируется; `.env.example` только для формы).

Если добавляете новые publisher-модули, подключите всё перечисленное:
- `pub_<platform>.py`
- опционально `login_<platform>.py`
- API flags и queue handling в `app.py`
- CLI wiring в `autopub.py` (если требуется)
- обработку toggle `ignore_<platform>`
- обновления README

---

## License

Файл `LICENSE` сейчас отсутствует в этом снимке репозитория.

Предположение для этого черновика:
- Считайте условия использования и распространения неопределёнными, пока maintainer не добавит явный файл лицензии.

Рекомендуемое следующее действие:
- Добавить top-level `LICENSE` (например MIT/Apache-2.0/GPL-3.0) и обновить этот раздел.

> 📝 Пока файл лицензии не добавлен, считайте предположения о коммерческом/внутреннем распространении нерешёнными и уточняйте напрямую у maintainer.

---

## Acknowledgements

- Профиль maintainer и sponsor: [@lachlanchen](https://github.com/lachlanchen)
- Источник конфигурации финансирования: [`.github/FUNDING.yml`](.github/FUNDING.yml)
- Сервисы экосистемы, упоминаемые в этом репозитории: Selenium, Tornado, SendGrid, 2Captcha, Turing captcha APIs.

---

## Support AutoPublish

💖 Поддержка сообщества финансирует инфраструктуру, работу над надёжностью и интеграции новых платформ.

AutoPublish является частью более широкой инициативы по сохранению открытости и hackable-подхода в кроссплатформенных инструментах для авторов. Донаты помогают:

- Поддерживать онлайн Selenium farm, processing API и cloud GPU.
- Выпускать новых паблишеров (Kuaishou, Instagram Reels и т.д.) и улучшения надёжности существующих ботов.
- Делиться большим объёмом документации, стартовыми датасетами и туториалами для независимых авторов.

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

Также доступно через:
- GitHub Sponsors: <https://github.com/sponsors/lachlanchen>
- Project links: <https://lazying.art>, <https://chat.lazying.art>, <https://onlyideas.art>
