[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish

> 🌍 **在此工作區於 2026 年 2 月 28 日驗證的在地化狀態：**
> `i18n/` 目前包含 `README.ar.md` 與 `README.es.md`；`README.zh-CN.md` 與 `README.ja.md` 保留作為後續目標檔案。

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#先決條件)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#系統總覽)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#執行-tornado-服務-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#平台專屬注意事項)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#執行-tornado-服務-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-前端-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Arabic%20%7C%20Spanish-0EA5E9)](#目錄)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#授權)

這是一套將短影音內容分發到多個中國與國際創作者平台的自動化工具組。專案結合了 Tornado 服務、Selenium 自動化機器人與本地檔案監看流程，讓你把影片放進資料夾後，就能陸續上傳到小紅書、抖音、Bilibili、微信視頻號、Instagram，以及選用的 YouTube。

此儲存庫刻意維持低抽象層級：多數設定都在 Python 檔案與 shell 腳本中。本文是操作手冊，涵蓋安裝、執行與擴充點。

> ⚙️ **操作哲學**：本專案偏好明確腳本與直接瀏覽器自動化，而非隱藏式抽象層。
> ✅ **此 README 的正典政策**：先保留技術細節，再提升可讀性與可發現性。

## 從這裡開始

如果你是第一次接觸本專案，建議依序：

1. 閱讀[先決條件](#先決條件)與[安裝](#安裝)。
2. 在[設定](#設定)中配置密鑰與絕對路徑。
3. 在[準備瀏覽器工作階段](#準備瀏覽器工作階段)中準備除錯工作階段。
4. 在[使用方式](#使用方式)中選擇一種執行模式：`autopub.py`（監看）或 `app.py`（API 佇列）。
5. 使用[範例](#範例)中的命令驗證流程。

## 概覽

AutoPublish 目前支援兩種正式執行模式：

1. **CLI 監看模式（`autopub.py`）**：以資料夾為基礎進行匯入與發布。
2. **API 佇列模式（`app.py`）**：透過 HTTP（`/publish`, `/publish/queue`）進行 ZIP 發布。

此工具為偏好透明、腳本優先流程的操作者設計，而非抽象編排平台。

### 執行模式一覽

| 模式 | 入口點 | 輸入 | 適用情境 | 輸出行為 |
| --- | --- | --- | --- | --- |
| CLI 監看 | `autopub.py` | 放入 `videos/` 的檔案 | 本地操作者流程與 cron/service 迴圈 | 偵測到影片後即刻處理並發布到所選平台 |
| API 佇列服務 | `app.py` | 上傳 ZIP 到 `POST /publish` | 與上游系統整合、遠端觸發 | 接收工作、排入佇列，並依 worker 順序執行發布 |

## 快速資訊

| 項目 | 值 |
| --- | --- |
| 主要語言 | Python 3.10+ |
| 主要執行模式 | CLI 監看（`autopub.py`）+ Tornado 佇列服務（`app.py`） |
| 自動化引擎 | Selenium + remote-debug Chromium 工作階段 |
| 輸入格式 | 原始影片（`videos/`）與 ZIP 套件（`/publish`） |
| 目前工作區路徑 | `/home/lachlan/ProjectsLFS/AutoPublish` |
| 理想使用者 | 管理多平台短影音流程的創作者/維運工程師 |

### 營運安全快照

| 主題 | 目前狀態 | 動作 |
| --- | --- | --- |
| 硬編碼路徑 | 多個模組/腳本存在 | 上線前先依主機更新路徑常數 |
| 瀏覽器登入狀態 | 必要 | 每平台保留持久 remote-debug profile |
| 驗證碼處理 | 可選整合 | 需要時設定 2Captcha/Turing 憑證 |
| 授權宣告 | 未偵測到頂層 `LICENSE` | 重新散佈前請與維護者確認使用條款 |

---

## 目錄

- [概覽](#概覽)
- [系統總覽](#系統總覽)
- [功能](#功能)
- [專案結構](#專案結構)
- [儲存庫布局](#儲存庫布局)
- [先決條件](#先決條件)
- [安裝](#安裝)
- [設定](#設定)
- [準備瀏覽器工作階段](#準備瀏覽器工作階段)
- [使用方式](#使用方式)
- [範例](#範例)
- [中繼資料與 ZIP 格式](#中繼資料與-zip-格式)
- [平台專屬注意事項](#平台專屬注意事項)
- [Raspberry Pi / Linux 服務設定](#raspberry-pi--linux-服務設定)
- [舊版 macOS 腳本](#舊版-macos-腳本)
- [疑難排解與維護](#疑難排解與維護)
- [擴充系統](#擴充系統)
- [快速啟動檢查清單](#快速啟動檢查清單)
- [開發備註](#開發備註)
- [路線圖](#路線圖)
- [貢獻](#貢獻)
- [授權](#授權)
- [致謝](#致謝)
- [支援 AutoPublish](#支援-autopublish)

---

## 系統總覽

🎯 **從原始素材到發布貼文的端到端流程**：

流程概覽：

1. **原始影片匯入**：將影片放入 `videos/`。監看器（`autopub.py` 或排程/service）會透過 `videos_db.csv` 與 `processed.csv` 偵測新檔。
2. **素材生成**：`process_video.VideoProcessor` 會把檔案上傳到內容處理伺服器（`upload_url` 與 `process_url`），回傳 ZIP 套件，包含：
   - 編輯/編碼後影片（`<stem>.mp4`）
   - 封面圖
   - `{stem}_metadata.json`（含在地化標題、描述、標籤等）
3. **發布**：中繼資料驅動 `pub_*.py` 中的 Selenium 發布器。每個發布器會透過 remote debugging port 與持久化 user-data 目錄，附加到已啟動的 Chromium/Chrome。
4. **Web 控制平面（可選）**：`app.py` 提供 `/publish`，接收預先建好的 ZIP，解壓後將發布工作排入相同發布器。它也能刷新瀏覽器工作階段並觸發登入輔助（`login_*.py`）。
5. **支援模組**：`load_env.py` 從 `~/.bashrc` 載入密鑰，`utils.py` 提供輔助（視窗聚焦、QR 處理、郵件工具函式），`solve_captcha_*.py` 在出現驗證碼時整合 Turing/2Captcha。

## 功能

✨ **為務實、腳本優先的自動化而設計**：

- 多平台發布：小紅書、抖音、Bilibili、視頻號（WeChat Channels）、Instagram、YouTube（可選）。
- 兩種操作模式：CLI 監看管線（`autopub.py`）與 API 佇列服務（`app.py` + `/publish` + `/publish/queue`）。
- 可透過 `ignore_*` 檔快速暫停單一平台。
- 支援 remote-debug 瀏覽器工作階段重用與持久 profile。
- 可選 QR/驗證碼自動化與郵件通知輔助。
- 內建 PWA（`pwa/`）上傳 UI 不需前端建置流程。
- 提供 Linux/Raspberry Pi 服務化腳本（`scripts/`）。

### 功能矩陣

| 能力 | CLI（`autopub.py`） | API（`app.py`） |
| --- | --- | --- |
| 輸入來源 | 本地 `videos/` 監看 | `POST /publish` 上傳 ZIP |
| 佇列 | 內建檔案式進度 | 明確的記憶體內工作佇列 |
| 平台旗標 | CLI 參數（`--pub-*`）+ `ignore_*` | Query 參數（`publish_*`）+ `ignore_*` |
| 最適合 | 單機操作者流程 | 外部系統整合與遠端觸發 |

---

## 專案結構

高層級來源/執行布局：

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

注意：`transcription_data/` 會在處理/發布流程執行後於執行階段出現。

## 儲存庫布局

🗂️ **核心模組與用途**：

| 路徑 | 用途 |
| --- | --- |
| `app.py` | Tornado 服務，提供 `/publish` 與 `/publish/queue`，內含發布佇列與 worker 執行緒。 |
| `autopub.py` | CLI 監看器：掃描 `videos/`，處理新檔並平行呼叫發布器。 |
| `process_video.py` | 上傳影片到處理後端並保存回傳 ZIP 套件。 |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | 各平台 Selenium 自動化模組。 |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | 工作階段檢查與 QR 登入流程。 |
| `utils.py` | 共用自動化工具（視窗聚焦、QR/郵件輔助、診斷工具）。 |
| `load_env.py` | 從 shell 設定檔（`~/.bashrc`）載入環境變數並遮蔽敏感日誌。 |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | SMTP/SendGrid 輔助與測試腳本。 |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | 驗證碼解題服務整合。 |
| `scripts/` | 服務設定與維運腳本（Raspberry Pi/Linux + 舊版自動化）。 |
| `pwa/` | 用於 ZIP 預覽與提交發布的靜態 PWA。 |
| `setup_raspberrypi.md` | Raspberry Pi 佈署逐步指南。 |
| `.env.example` | 環境變數範本（憑證、路徑、驗證碼 key）。 |
| `.github/FUNDING.yml` | 贊助/募資設定。 |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | 執行期產物與日誌（多數已被 gitignore）。 |

---

## 先決條件

🧰 **首次執行前請先安裝以下項目**。

### 作業系統與工具

- Linux 桌面/伺服器並具備 X session（範例腳本常見 `DISPLAY=:1`）。
- Chromium/Chrome 與相容的 ChromeDriver。
- GUI/媒體工具：`xdotool`、`ffmpeg`、`zip`、`unzip`。
- Python 3.10+（venv 或 Conda）。

### Python 相依套件

最小執行集：

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

與儲存庫一致：

```bash
python -m pip install -r requirements.txt
```

輕量服務安裝（設定腳本預設使用）：

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` 包含：
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### 可選：建立 sudo 使用者

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## 安裝

🚀 **從乾淨機器開始設定**：

1. 複製儲存庫：

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. 建立並啟用環境（`venv` 範例）：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. 準備環境變數：

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. 為需要 shell 設定檔值的腳本載入變數：

```bash
source ~/.bashrc
python load_env.py
```

注意：`load_env.py` 以 `~/.bashrc` 為核心設計；若你的環境使用其他 shell profile，請相應調整。

---

## 設定

🔐 **先設定憑證，再確認主機專屬路徑**。

### 環境變數

專案預期從環境變數取得憑證與可選瀏覽器/執行路徑。請從 `.env.example` 開始：

| 變數 | 說明 |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | QR/登入通知用 SMTP 憑證。 |
| `SENDGRID_API_KEY` | 使用 SendGrid API 的郵件流程金鑰。 |
| `APIKEY_2CAPTCHA` | 2Captcha API 金鑰。 |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Turing 驗證碼憑證。 |
| `DOUYIN_LOGIN_PASSWORD` | 抖音二次驗證輔助。 |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Instagram/瀏覽器驅動覆寫設定。 |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | `app.py` 中偏好的全域瀏覽器/驅動/顯示覆寫。 |

### 路徑常數（重要）

📌 **最常見啟動問題**：未解析的硬編碼絕對路徑。

多個模組仍包含硬編碼路徑。請依主機更新：

| 檔案 | 常數 | 意義 |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | API 服務根路徑與後端端點。 |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | CLI 監看根路徑與後端端點。 |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Python/Conda/repo/log 的絕對路徑。 | 舊版/macOS 取向包裝腳本。 |
| `utils.py` | 封面處理輔助中的 FFmpeg 路徑假設。 | 媒體工具路徑相容性。 |

儲存庫重要說明：
- 此工作區目前路徑為 `/home/lachlan/ProjectsLFS/AutoPublish`。
- 某些程式與腳本仍引用 `/home/lachlan/Projects/auto-publish` 或 `/Users/lachlan/...`。
- 正式使用前，請先保留並在本地調整這些路徑。

### 透過 `ignore_*` 進行平台切換

🧩 **快速安全開關**：建立 `ignore_*` 檔即可停用該發布器，不需改碼。

發布旗標同時受 ignore 檔控制。建立空檔案即可停用平台：

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

刪除對應檔案即可重新啟用。

---

## 準備瀏覽器工作階段

🌐 **為了可靠 Selenium 發布，工作階段持久化是必要條件**。

1. 建立專用 profile 資料夾：

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. 以 remote debugging 啟動瀏覽器（小紅書範例）：

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. 每個平台/profile 先手動登入一次。

4. 驗證 Selenium 可附加：

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

安全性提醒：
- `app.py` 目前含有瀏覽器重啟邏輯使用的硬編碼 sudo 密碼佔位（`password = "1"`）。正式部署前請先替換。

---

## 使用方式

▶️ **提供兩種執行模式**：CLI 監看與 API 佇列服務。

### 執行 CLI 管線（`autopub.py`）

1. 將來源影片放入監看資料夾（`videos/` 或你設定的 `autopublish_folder_path`）。
2. 執行：

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

旗標：

| 旗標 | 意義 |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | 限制發布到指定平台。若皆未提供，預設三者全啟用。 |
| `--test` | 傳遞測試模式給發布器（實際行為依平台模組而異）。 |
| `--use-cache` | 若存在則重用 `transcription_data/<video>/<video>.zip`。 |

每支影片的 CLI 流程：
- 透過 `process_video.py` 上傳/處理。
- 解壓 ZIP 到 `transcription_data/<video>/`。
- 透過 `ThreadPoolExecutor` 啟動選定發布器。
- 將追蹤狀態附加到 `videos_db.csv` 與 `processed.csv`。

### 執行 Tornado 服務（`app.py`）

🛰️ **API 模式**適合會產出 ZIP 套件的外部系統。

啟動伺服器：

```bash
python app.py --refresh-time 1800 --port 8081
```

API 端點摘要：

| 端點 | 方法 | 用途 |
| --- | --- | --- |
| `/publish` | `POST` | 上傳 ZIP 位元組並排入發布工作 |
| `/publish/queue` | `GET` | 查看佇列、工作歷史與發布狀態 |

### `POST /publish`

📤 **透過直接上傳 ZIP 位元組**排入發布工作。

- Header: `Content-Type: application/octet-stream`
- 必填 query/form 參數：`filename`（ZIP 檔名）
- 可選布林值：`publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body：原始 ZIP 位元組

範例：

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

程式目前行為：
- 請求會被接受並排入佇列。
- 即時回應會回傳 JSON，包含 `status: queued`、`job_id`、`queue_size`。
- Worker 執行緒會序列化處理佇列中的工作。

### `GET /publish/queue`

📊 **觀察佇列健康度與進行中的工作**。

回傳佇列狀態/歷史 JSON：

```bash
curl "http://localhost:8081/publish/queue"
```

回應欄位包含：
- `status`, `jobs`, `queue_size`, `is_publishing`。

### 瀏覽器刷新執行緒

♻️ 週期性刷新瀏覽器可降低長時間運行下的工作階段老化失敗。

`app.py` 會依 `--refresh-time` 間隔執行背景刷新執行緒，並掛接登入檢查。刷新 sleep 含隨機延遲行為。

### PWA 前端（`pwa/`）

🖥️ 輕量靜態 UI，用於手動上傳 ZIP 與檢視佇列。

本地啟動靜態 UI：

```bash
cd pwa
python -m http.server 5173
```

打開 `http://localhost:5173`，並設定後端 base URL（例如 `http://lazyingart:8081`）。

PWA 功能：
- 拖放 ZIP 預覽。
- 發布目標切換 + 測試模式。
- 提交到 `/publish` 並輪詢 `/publish/queue`。

---

## 範例

🧪 **可直接複製貼上的 smoke test 指令**：

### 範例 0：載入環境並啟動 API 伺服器

```bash
source ~/.bashrc
python load_env.py
python app.py --refresh-time 1800 --port 8081
```

### 範例 A：CLI 發布執行

```bash
python autopub.py --pub-xhs --pub-douyin --use-cache
```

### 範例 B：API 發布執行（單一 ZIP）

```bash
curl -X POST "http://localhost:8081/publish?filename=my_bundle.zip&publish_bilibili=true&test=true" \
  --data-binary @my_bundle.zip \
  -H "Content-Type: application/octet-stream"
```

### 範例 C：檢查佇列狀態

```bash
curl -s "http://localhost:8081/publish/queue"
```

### 範例 D：SMTP 輔助 smoke test

```bash
python smtp.py
python smtp_test_simple.py
```

---

## 中繼資料與 ZIP 格式

📦 **ZIP 合約非常重要**：檔名與 metadata key 必須與發布器預期一致。

預期 ZIP 內容（最小）：

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` 會驅動中文平台發布器；可選 `metadata["english_version"]` 會供 YouTube 發布器使用。

模組常用欄位：
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags`（hashtag 清單）
- `video_filename`, `cover_filename`
- 各平台自訂欄位（依個別 `pub_*.py` 實作）

如果你在外部生成 ZIP，請確保 key 與檔名符合模組預期。

---

## 平台專屬注意事項

🧭 **各發布器的連接埠對照與模組歸屬**。

| 平台 | Port | 模組 | 備註 |
| --- | --- | --- | --- |
| 小紅書 | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | 支援 QR 重新登入流程；標題清洗與 hashtag 使用來自 metadata。 |
| 抖音 | 5004 | `pub_douyin.py`, `login_douyin.py` | 上傳完成檢查與重試流程對平台變動敏感；請密切看日誌。 |
| Bilibili | 5005 | `pub_bilibili.py` | 可透過 `solve_captcha_2captcha.py` 與 `solve_captcha_turing.py` 掛接驗證碼處理。 |
| 視頻號（WeChat Channels） | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | 快速 QR 核准對工作階段刷新穩定性很關鍵。 |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | 在 API 模式以 `publish_instagram=true` 控制；`.env.example` 含對應變數。 |
| YouTube | 9222 | `pub_y2b.py` | 使用 `english_version` metadata 區塊；可用 `ignore_y2b` 停用。 |

---

## Raspberry Pi / Linux 服務設定

🐧 **建議用於長時間常駐主機**。

完整主機開機設定請參考 [`setup_raspberrypi.md`](setup_raspberrypi.md)。

快速管線設定：

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

此流程會編排：
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

以 tmux 手動啟動服務：

```bash
./scripts/start_autopub_tmux.sh
```

驗證服務/連接埠：

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## 舊版 macOS 腳本

🍎 保留舊版包裝腳本以相容歷史本地流程。

儲存庫仍包含舊版偏向 macOS 的包裝腳本：
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

這些腳本包含絕對 `/Users/lachlan/...` 路徑與 Conda 假設。若你依賴該流程可保留，但請依主機更新路徑/venv/工具鏈。

---

## 疑難排解與維護

🛠️ **若流程失敗，先從這裡檢查**。

- **多機路徑漂移**：若錯誤提到 `/Users/lachlan/...` 或 `/home/lachlan/Projects/auto-publish` 缺檔，請把常數對齊目前主機路徑（此工作區為 `/home/lachlan/ProjectsLFS/AutoPublish`）。
- **密鑰衛生**：推送前執行 `~/.local/bin/detect-secrets scan`。若外洩請輪替憑證。
- **處理後端錯誤**：若 `process_video.py` 印出 “Failed to get the uploaded file path,” 請確認上傳回應 JSON 含 `file_path`，且處理端點確實回傳 ZIP 位元組。
- **ChromeDriver 版本不符**：若出現 DevTools 連線錯誤，請對齊 Chrome/Chromium 與 driver 版本（或改用 `webdriver-manager`）。
- **瀏覽器焦點問題**：`bring_to_front` 依賴視窗標題比對（Chromium/Chrome 命名差異可能導致失效）。
- **驗證碼中斷**：設定 2Captcha/Turing 憑證，並在需要處整合 solver 輸出。
- **陳舊 lock 檔**：若排程永遠不啟動，請檢查程序狀態並移除舊的 `autopub.lock`（舊版腳本流程）。
- **建議檢查日誌**：`logs/`、`logs-autopub/`、`~/chromium_dev_session_logs/*.log`，以及 service journal 日誌。

---

## 擴充系統

🧱 **新增平台與提升穩定性的擴充點**。

- **新增平台**：複製一個 `pub_*.py` 模組，更新 selector/流程；若需要 QR 重新驗證就新增 `login_*.py`，再把旗標與佇列處理接到 `app.py`，CLI 佈線接到 `autopub.py`。
- **設定抽象化**：將分散常數遷移到結構化設定（`config.yaml`/`.env` + 型別模型），支援多主機運行。
- **憑證儲存強化**：以更安全機制取代硬編碼或 shell 暴露流程（`sudo -A`、keychain、vault/secret manager）。
- **容器化**：將 Chromium/ChromeDriver + Python runtime + 虛擬顯示封裝成可部署單位，便於雲端/伺服器使用。

---

## 快速啟動檢查清單

✅ **最短路徑完成首次發布**。

1. Clone 此儲存庫並安裝相依（`pip install -r requirements.txt` 或輕量 `requirements.autopub.txt`）。
2. 更新 `app.py`、`autopub.py` 與你會執行的腳本中的硬編碼路徑常數。
3. 在 shell profile 或 `.env` 匯出所需憑證；執行 `python load_env.py` 驗證讀取。
4. 建立 remote-debug 瀏覽器 profile 資料夾，並先啟動每個必要平台工作階段一次。
5. 在各平台 profile 手動登入。
6. 啟動 API 模式（`python app.py --port 8081`）或 CLI 模式（`python autopub.py --use-cache ...`）。
7. 提交一個樣本 ZIP（API 模式）或樣本影片（CLI 模式），並檢查 `logs/`。
8. 每次 push 前執行 secrets 掃描。

---

## 開發備註

🧬 **目前開發基準**（手動格式化 + smoke test）。

- Python 風格沿用既有 4 空白縮排與手動格式化。
- 目前沒有正式自動化測試套件；依賴 smoke test：
  - 透過 `autopub.py` 跑一支樣本影片；
  - 對 `/publish` 提交一個 ZIP 並監看 `/publish/queue`；
  - 手動驗證每個目標平台。
- 新增腳本時，請附一個簡單 `if __name__ == "__main__":` 入口，便於快速 dry-run。
- 盡量隔離平台變更（`pub_*`、`login_*`、`ignore_*` 切換）。
- 執行期產物（`videos/*`、`logs*/*`、`transcription_data/*`、`ignore_*`）預期為本地資料，多數已被 git 忽略。

---

## 路線圖

🗺️ **依目前程式限制整理的優先改進項目**。

規劃/期望改進（根據現有程式結構與備註）：

1. 以集中式設定（`.env`/YAML + 型別模型）取代分散硬編碼路徑。
2. 移除硬編碼 sudo 密碼模式，改為更安全的程序控制機制。
3. 以更強重試與更佳 UI 狀態偵測提升各平台發布穩定性。
4. 擴充平台支援（例如快手或其他創作者平台）。
5. 將執行環境封裝成可重現部署單位（容器 + 虛擬顯示 profile）。
6. 新增 ZIP 合約與佇列執行的自動化整合檢查。

---

## 貢獻

🤝 請保持 PR 聚焦、可重現，並明確說明執行環境假設。

歡迎貢獻。

1. Fork 並建立聚焦分支。
2. Commit 盡量小且使用祈使句（歷史範例：「Wait for YouTube checks before publishing」）。
3. 在 PR 提供手動驗證說明：
   - 環境假設
   - 瀏覽器/工作階段重啟
   - UI 流程變更相關日誌/截圖
4. 不要提交真實密鑰（`.env` 已忽略；僅用 `.env.example` 描述結構）。

若新增發布模組，請一併接好：
- `pub_<platform>.py`
- 可選 `login_<platform>.py`
- `app.py` 的 API 旗標與佇列處理
- `autopub.py` 的 CLI 佈線（需要時）
- `ignore_<platform>` 切換邏輯
- README 更新

---

## 授權

目前此儲存庫快照中沒有 `LICENSE` 檔案。

本草稿的假設：
- 在維護者新增明確授權檔前，使用與再散佈視為未定義。

建議下一步：
- 新增頂層 `LICENSE`（例如 MIT/Apache-2.0/GPL-3.0），並更新本段說明。

> 📝 在加入授權檔之前，請將商用/內部分發假設視為未定，並直接向維護者確認。

---

## 致謝

- 維護者與贊助頁：[@lachlanchen](https://github.com/lachlanchen)
- 資助設定來源：[`.github/FUNDING.yml`](.github/FUNDING.yml)
- 本儲存庫引用的生態服務：Selenium、Tornado、SendGrid、2Captcha、Turing captcha APIs。

---

## 支援 AutoPublish

💖 社群支持可用於基礎設施、穩定性工程與新平台整合。

AutoPublish 屬於更大的開源創作者工具鏈計畫，目標是保持跨平台發布工具可駭、可改、可延伸。捐助可協助：

- 維持 Selenium 節點、處理 API 與雲端 GPU 持續運行。
- 推進新發布器（快手、Instagram Reels 等）與既有機器人穩定性修復。
- 分享更多文件、起始資料集與獨立創作者教學內容。

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
