[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish

> 🌍 **Lokalisierungsstatus (in diesem Workspace am 28. Februar 2026 geprüft):**
> `i18n/` enthält aktuell `README.ar.md`, `README.es.md` und `README.de.md`; weitere Sprachdateien sind als nächste Ziele vorgesehen.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#voraussetzungen)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#systemueberblick)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#betrieb-des-tornado-services-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#plattformspezifische-hinweise)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#betrieb-des-tornado-services-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Arabic%20%7C%20Spanish-0EA5E9)](#inhaltsverzeichnis)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#lizenz)

Automatisierungs-Toolkit zur Verteilung von Short-Form-Video-Content auf mehrere chinesische und internationale Creator-Plattformen. Das Projekt kombiniert einen Tornado-basierten Service, Selenium-Automation-Bots und einen lokalen File-Watcher-Workflow, sodass das Ablegen eines Videos in einem Ordner schließlich zu Uploads auf XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), Instagram und optional YouTube führt.

Das Repository ist bewusst low-level gehalten: Die meiste Konfiguration liegt in Python-Dateien und Shell-Skripten. Dieses Dokument ist ein operatives Handbuch für Setup, Betrieb und Erweiterungspunkte.

> ⚙️ **Betriebsphilosophie**: Dieses Projekt bevorzugt explizite Skripte und direkte Browser-Automatisierung statt versteckter Abstraktionsschichten.
> ✅ **Kanonische Richtlinie für diese README**: Technische Details beibehalten und danach Lesbarkeit sowie Auffindbarkeit verbessern.

## Hier starten

Wenn du neu in diesem Repository bist, nutze diese Reihenfolge:

1. Lies [Voraussetzungen](#voraussetzungen) und [Installation](#installation).
2. Konfiguriere Secrets und absolute Pfade in [Konfiguration](#konfiguration).
3. Bereite Browser-Debug-Sessions in [Browser-Sessions vorbereiten](#browser-sessions-vorbereiten) vor.
4. Wähle in [Nutzung](#nutzung) einen Betriebsmodus: `autopub.py` (Watcher) oder `app.py` (API Queue).
5. Prüfe alles mit den Befehlen aus [Beispiele](#beispiele).

## Ueberblick

AutoPublish unterstützt derzeit zwei produktive Laufzeitmodi:

1. **CLI-Watcher-Modus (`autopub.py`)** für ordnerbasierte Ingestion und Publishing.
2. **API-Queue-Modus (`app.py`)** für ZIP-basiertes Publishing per HTTP (`/publish`, `/publish/queue`).

Das System ist für Operatoren ausgelegt, die transparente, skriptzentrierte Workflows gegenüber abstrakten Orchestrierungsplattformen bevorzugen.

### Laufzeitmodi auf einen Blick

| Modus | Einstiegspunkt | Eingabe | Am besten fuer | Ausgabeverhalten |
| --- | --- | --- | --- | --- |
| CLI Watcher | `autopub.py` | Dateien in `videos/` | Lokale Operator-Workflows und cron/service-Schleifen | Verarbeitet erkannte Videos und publiziert sofort auf ausgewaehlte Plattformen |
| API Queue Service | `app.py` | ZIP-Upload an `POST /publish` | Integrationen mit Upstream-Systemen und Remote-Triggern | Nimmt Jobs an, reiht sie ein und fuehrt Publishing in Worker-Reihenfolge aus |

## Schneller Snapshot

| Was | Wert |
| --- | --- |
| Primaere Sprache | Python 3.10+ |
| Haupt-Runtimes | CLI Watcher (`autopub.py`) + Tornado Queue Service (`app.py`) |
| Automation Engine | Selenium + Remote-Debug-Chromium-Sessions |
| Eingabeformate | Rohvideos (`videos/`) und ZIP-Bundles (`/publish`) |
| Aktueller Repo-Workspace-Pfad | `/home/lachlan/ProjectsLFS/AutoPublish` |
| Zielnutzer | Creators/Ops-Engineers mit Multi-Plattform-Short-Video-Pipelines |

### Snapshot zur Betriebssicherheit

| Thema | Aktueller Status | Aktion |
| --- | --- | --- |
| Hard-coded Paths | In mehreren Modulen/Skripten vorhanden | Pfadkonstanten pro Host vor Produktionslauf aktualisieren |
| Browser-Login-Status | Erforderlich | Persistente Remote-Debug-Profile pro Plattform beibehalten |
| Captcha-Handling | Optionale Integrationen verfuegbar | 2Captcha-/Turing-Credentials bei Bedarf konfigurieren |
| Lizenzdeklaration | Keine `LICENSE`-Datei auf Top-Level erkannt | Nutzungsbedingungen vor Weitergabe mit Maintainer klaeren |

---

## Inhaltsverzeichnis

- [Ueberblick](#ueberblick)
- [Systemueberblick](#systemueberblick)
- [Funktionen](#funktionen)
- [Projektstruktur](#projektstruktur)
- [Repository-Layout](#repository-layout)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Browser-Sessions vorbereiten](#browser-sessions-vorbereiten)
- [Nutzung](#nutzung)
- [Beispiele](#beispiele)
- [Metadaten & ZIP-Format](#metadaten--zip-format)
- [Plattformspezifische Hinweise](#plattformspezifische-hinweise)
- [Raspberry Pi / Linux Service Setup](#raspberry-pi--linux-service-setup)
- [Legacy-macOS-Skripte](#legacy-macos-skripte)
- [Troubleshooting & Wartung](#troubleshooting--wartung)
- [System erweitern](#system-erweitern)
- [Quick-Start-Checkliste](#quick-start-checkliste)
- [Entwicklungsnotizen](#entwicklungsnotizen)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Lizenz](#lizenz)
- [Danksagungen](#danksagungen)
- [AutoPublish unterstuetzen](#autopublish-unterstuetzen)

---

## Systemueberblick

🎯 **End-to-End-Flow** von Rohmedien bis zu veroeffentlichten Posts:

Workflow auf einen Blick:

1. **Rohmaterial-Ingestion**: Lege ein Video in `videos/` ab. Der Watcher (entweder `autopub.py` oder Scheduler/Service) erkennt neue Dateien ueber `videos_db.csv` und `processed.csv`.
2. **Asset-Generierung**: `process_video.VideoProcessor` laedt die Datei auf einen Content-Processing-Server (`upload_url` und `process_url`) hoch, der ein ZIP-Paket zurueckgibt mit:
   - dem bearbeiteten/encodierten Video (`<stem>.mp4`),
   - einem Cover-Bild,
   - `{stem}_metadata.json` mit lokalisierten Titeln, Beschreibungen, Tags usw.
3. **Publishing**: Metadaten steuern die Selenium-Publisher in `pub_*.py`. Jeder Publisher verbindet sich mit einer bereits laufenden Chromium/Chrome-Instanz ueber Remote-Debugging-Ports und persistente User-Data-Verzeichnisse.
4. **Web-Control-Plane (optional)**: `app.py` stellt `/publish` bereit, akzeptiert vorgebaute ZIP-Bundles, entpackt sie und reiht Publish-Jobs fuer dieselben Publisher ein. Außerdem kann der Service Browser-Sessions refreshen und Login-Helper (`login_*.py`) triggern.
5. **Support-Module**: `load_env.py` hydriert Secrets aus `~/.bashrc`, `utils.py` liefert Helper (Fensterfokus, QR-Handling, Mail-Utilities), und `solve_captcha_*.py` integriert Turing/2Captcha bei Captchas.

## Funktionen

✨ **Entwickelt fuer pragmatische, skriptzentrierte Automatisierung**:

- Multi-Plattform-Publishing: XiaoHongShu, Douyin, Bilibili, ShiPinHao (WeChat Channels), Instagram, YouTube (optional).
- Zwei Betriebsmodi: CLI-Watcher-Pipeline (`autopub.py`) und API-Queue-Service (`app.py` + `/publish` + `/publish/queue`).
- Temporäre Deaktivierung pro Plattform ueber `ignore_*`-Dateien.
- Wiederverwendung von Remote-Debugging-Browser-Sessions mit persistenten Profilen.
- Optionale QR-/Captcha-Automatisierung und E-Mail-Benachrichtigungs-Helper.
- Kein Frontend-Build fuer die enthaltene PWA-Upload-UI (`pwa/`) noetig.
- Linux/Raspberry-Pi-Automatisierungsskripte fuer Service-Setup (`scripts/`).

### Feature-Matrix

| Faehigkeit | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Eingabequelle | Lokaler `videos/`-Watcher | Hochgeladenes ZIP via `POST /publish` |
| Queueing | Interner dateibasierter Fortschritt | Explizite In-Memory-Job-Queue |
| Plattform-Flags | CLI-Args (`--pub-*`) + `ignore_*` | Query-Args (`publish_*`) + `ignore_*` |
| Best Fit | Single-Host-Operator-Workflow | Externe Systeme und Remote-Trigger |

---

## Projektstruktur

High-Level-Source-/Runtime-Layout:

```text
AutoPublish/
├── README.md
├── app.py
├── autopub.py
├── process_video.py
├── load_env.py
├── utils.py
├── pub_*.py                  # Plattform-Publisher
├── login_*.py                # Plattform-Login-/Session-Helper
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
├── i18n/                     # mehrsprachige READMEs
├── archived/
├── videos/                   # Runtime-Eingabeartefakte
├── logs/, logs-autopub/      # Runtime-Logs
├── temp/, temp_screenshot/   # Runtime-Temp-Artefakte
├── videos_db.csv
└── processed.csv
```

Hinweis: `transcription_data/` wird zur Laufzeit vom Processing-/Publishing-Flow verwendet und kann nach der Ausfuehrung erscheinen.

## Repository-Layout

🗂️ **Wichtige Module und ihre Aufgaben**:

| Pfad | Zweck |
| --- | --- |
| `app.py` | Tornado-Service mit `/publish` und `/publish/queue`, inkl. interner Publish-Queue und Worker-Thread. |
| `autopub.py` | CLI-Watcher: scannt `videos/`, verarbeitet neue Dateien und ruft Publisher parallel auf. |
| `process_video.py` | Laedt Videos zum Processing-Backend hoch und speichert die zurueckgegebenen ZIP-Bundles. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | Selenium-Automationsmodule je Plattform. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | Session-Checks und QR-Login-Flows. |
| `utils.py` | Gemeinsame Automation-Helper (Fensterfokus, QR-/Mail-Utilities, Diagnose-Helper). |
| `load_env.py` | Laedt Env-Variablen aus Shell-Profil (`~/.bashrc`) und maskiert sensitive Logs. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | SMTP-/SendGrid-Helper und Testskripte. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Captcha-Solver-Integrationen. |
| `scripts/` | Service-Setup- und Betriebs-Skripte (Raspberry Pi/Linux + Legacy-Automatisierung). |
| `pwa/` | Statische PWA fuer ZIP-Vorschau und Publish-Submission. |
| `setup_raspberrypi.md` | Schritt-fuer-Schritt-Guide fuer Raspberry-Pi-Provisioning. |
| `.env.example` | Template fuer Umgebungsvariablen (Credentials, Pfade, Captcha-Keys). |
| `.github/FUNDING.yml` | Sponsor-/Funding-Konfiguration. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | Runtime-Artefakte und Logs (vieles ist gitignored). |

---

## Voraussetzungen

🧰 **Vor dem ersten Run installieren**.

### Betriebssystem und Tools

- Linux-Desktop/Server mit X-Session (`DISPLAY=:1` ist in den bereitgestellten Skripten haeufig).
- Chromium/Chrome und passender ChromeDriver.
- GUI-/Media-Helper: `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv oder Conda).

### Python-Abhaengigkeiten

Minimales Runtime-Set:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

Repository-Paritaet:

```bash
python -m pip install -r requirements.txt
```

Fuer schlanke Service-Installationen (standardmaeßig von Setup-Skripten genutzt):

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` enthaelt:
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Optional: sudo-Benutzer erstellen

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## Installation

🚀 **Setup auf einer sauberen Maschine**:

1. Repository klonen:

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. Umgebung erstellen und aktivieren (Beispiel mit `venv`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. Umgebungsvariablen vorbereiten:

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. Variablen fuer Skripte laden, die Shell-Profilwerte verwenden:

```bash
source ~/.bashrc
python load_env.py
```

Hinweis: `load_env.py` ist auf `~/.bashrc` ausgelegt; wenn deine Umgebung ein anderes Shell-Profil verwendet, passe das entsprechend an.

---

## Konfiguration

🔐 **Credentials setzen, danach hostspezifische Pfade pruefen**.

### Umgebungsvariablen

Das Projekt erwartet Credentials und optionale Browser-/Runtime-Pfade aus Umgebungsvariablen. Starte mit `.env.example`:

| Variable | Beschreibung |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | SMTP-Credentials fuer QR-/Login-Benachrichtigungen. |
| `SENDGRID_API_KEY` | SendGrid-Key fuer E-Mail-Flows ueber SendGrid-APIs. |
| `APIKEY_2CAPTCHA` | 2Captcha-API-Key. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Turing-Captcha-Credentials. |
| `DOUYIN_LOGIN_PASSWORD` | Douyin-Helper fuer zweite Verifikation. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Instagram-/Browser-Driver-Overrides. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | Bevorzugte globale Browser-/Driver-/Display-Overrides in `app.py`. |

### Pfadkonstanten (wichtig)

📌 **Hauefigstes Startup-Problem**: nicht aufgeloeste hard-coded absolute Pfade.

Mehrere Module enthalten weiterhin hard-coded Pfade. Aktualisiere diese fuer deinen Host:

| Datei | Konstante(n) | Bedeutung |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | API-Service-Roots und Backend-Endpunkte. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | CLI-Watcher-Roots und Backend-Endpunkte. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Absolute Pfade zu Python/Conda/Repo/Log-Orten. | Legacy-/macOS-orientierte Wrapper. |
| `utils.py` | FFmpeg-Pfadannahmen in Cover-Processing-Helpern. | Medien-Tooling-Pfadkompatibilitaet. |

Wichtiger Repository-Hinweis:
- Der aktuelle Repository-Pfad in diesem Workspace ist `/home/lachlan/ProjectsLFS/AutoPublish`.
- Einige Code- und Skriptstellen referenzieren weiterhin `/home/lachlan/Projects/auto-publish` oder `/Users/lachlan/...`.
- Diese Pfade vor Produktionsnutzung lokal beibehalten und korrekt anpassen.

### Plattform-Toggles ueber `ignore_*`

🧩 **Schneller Safety-Switch**: Das Anlegen einer `ignore_*`-Datei deaktiviert den Publisher ohne Code-Aenderung.

Publish-Flags werden auch durch Ignore-Dateien gesteuert. Lege eine leere Datei an, um eine Plattform zu deaktivieren:

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

Zum Reaktivieren die entsprechende Datei entfernen.

---

## Browser-Sessions vorbereiten

🌐 **Session-Persistenz ist Pflicht** fuer zuverlaessiges Selenium-Publishing.

1. Dedizierte Profilordner erstellen:

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. Browser-Sessions mit Remote-Debugging starten (Beispiel fuer XiaoHongShu):

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. Einmalig pro Plattform/Profil manuell einloggen.

4. Pruefen, ob Selenium sich verbinden kann:

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Sicherheitshinweis:
- `app.py` enthaelt aktuell einen hard-coded sudo-Passwort-Placeholder (`password = "1"`) in der Browser-Restart-Logik. Vor echtem Deployment ersetzen.

---

## Nutzung

▶️ **Es gibt zwei Betriebsmodi**: CLI-Watcher und API-Queue-Service.

### CLI-Pipeline ausfuehren (`autopub.py`)

1. Quellvideos in das Watch-Verzeichnis legen (`videos/` oder dein konfigurierter `autopublish_folder_path`).
2. Ausfuehren:

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Flags:

| Flag | Bedeutung |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Publishing auf ausgewaehlte Plattformen beschraenken. Wenn keine gesetzt sind, sind alle drei standardmaeßig aktiv. |
| `--test` | Testmodus, der an Publisher weitergegeben wird (Verhalten je Plattformmodul unterschiedlich). |
| `--use-cache` | Vorhandenes `transcription_data/<video>/<video>.zip` wiederverwenden, falls vorhanden. |

CLI-Flow pro Video:
- Upload/Processing ueber `process_video.py`.
- ZIP nach `transcription_data/<video>/` entpacken.
- Ausgewaehlte Publisher ueber `ThreadPoolExecutor` starten.
- Tracking-Status in `videos_db.csv` und `processed.csv` fortschreiben.

### Betrieb des Tornado-Services (`app.py`)

🛰️ **API-Modus** eignet sich fuer externe Systeme, die ZIP-Bundles erzeugen.

Server starten:

```bash
python app.py --refresh-time 1800 --port 8081
```

API-Endpunkt-Uebersicht:

| Endpunkt | Methode | Zweck |
| --- | --- | --- |
| `/publish` | `POST` | ZIP-Bytes hochladen und Publish-Job einreihen |
| `/publish/queue` | `GET` | Queue, Job-Historie und Publish-Status einsehen |

### `POST /publish`

📤 **Publish-Job einreihen**, indem ZIP-Bytes direkt hochgeladen werden.

- Header: `Content-Type: application/octet-stream`
- Erforderliches Query-/Form-Arg: `filename` (ZIP-Dateiname)
- Optionale Booleans: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: rohe ZIP-Bytes

Beispiel:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

Aktuelles Verhalten im Code:
- Anfrage wird akzeptiert und in die Queue gestellt.
- Sofortantwort gibt JSON mit `status: queued`, `job_id` und `queue_size` zurueck.
- Worker-Thread verarbeitet Jobs seriell.

### `GET /publish/queue`

📊 **Queue-Zustand und aktive Jobs beobachten**.

Liefert Queue-Status-/Historie-JSON:

```bash
curl "http://localhost:8081/publish/queue"
```

Antwortfelder enthalten u. a.:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Browser-Refresh-Thread

♻️ Periodischer Browser-Refresh reduziert stale-session-Fehler bei langen Laufzeiten.

`app.py` startet einen Hintergrund-Refresh-Thread mit dem `--refresh-time`-Intervall und Login-Checks. Der Refresh-Sleep enthaelt randomisierte Verzoegerung.

### PWA-Frontend (`pwa/`)

🖥️ Leichte statische UI fuer manuelle ZIP-Uploads und Queue-Inspektion.

Statische UI lokal starten:

```bash
cd pwa
python -m http.server 5173
```

`http://localhost:5173` oeffnen und Backend-Basis-URL setzen (z. B. `http://lazyingart:8081`).

PWA-Funktionen:
- Drag-and-drop-ZIP-Vorschau.
- Publish-Target-Toggles + Testmodus.
- Sendet an `/publish` und pollt `/publish/queue`.

---

## Beispiele

🧪 **Smoke-Test-Befehle zum Kopieren/Einsetzen**:

### Beispiel 0: Umgebung laden und API-Server starten

```bash
source ~/.bashrc
python load_env.py
python app.py --refresh-time 1800 --port 8081
```

### Beispiel A: CLI-Publish-Run

```bash
python autopub.py --pub-xhs --pub-douyin --use-cache
```

### Beispiel B: API-Publish-Run (ein einzelnes ZIP)

```bash
curl -X POST "http://localhost:8081/publish?filename=my_bundle.zip&publish_bilibili=true&test=true" \
  --data-binary @my_bundle.zip \
  -H "Content-Type: application/octet-stream"
```

### Beispiel C: Queue-Status pruefen

```bash
curl -s "http://localhost:8081/publish/queue"
```

### Beispiel D: SMTP-Helper-Smoketest

```bash
python smtp.py
python smtp_test_simple.py
```

---

## Metadaten & ZIP-Format

📦 **Der ZIP-Vertrag ist entscheidend**: Dateinamen und Metadaten-Keys muessen zu den Erwartungen der Publisher passen.

Erwarteter ZIP-Inhalt (Minimum):

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` steuert CN-Publisher; optional speist `metadata["english_version"]` den YouTube-Publisher.

Von Modulen haeufig genutzte Felder:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (Liste von Hashtags)
- `video_filename`, `cover_filename`
- plattformspezifische Felder, wie in einzelnen `pub_*.py`-Dateien implementiert

Wenn du ZIPs extern erzeugst, halte Keys und Dateinamen konsistent zu den Modulerwartungen.

---

## Plattformspezifische Hinweise

🧭 **Port-Mapping + Modulzuordnung** je Publisher.

| Plattform | Port | Modul(e) | Hinweise |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | QR-Re-Login-Flow; Titel-Sanitisierung und Hashtag-Nutzung aus Metadaten. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Upload-Completion-Checks und Retry-Pfade sind plattformfragil; Logs eng beobachten. |
| Bilibili | 5005 | `pub_bilibili.py` | Captcha-Hooks verfuegbar ueber `solve_captcha_2captcha.py` und `solve_captcha_turing.py`. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Schnelle QR-Freigabe ist wichtig fuer zuverlaessige Session-Refreshes. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | Im API-Modus mit `publish_instagram=true` steuerbar; Env-Variablen in `.env.example` verfuegbar. |
| YouTube | 9222 | `pub_y2b.py` | Verwendet den Metadatenblock `english_version`; deaktivieren mit `ignore_y2b`. |

---

## Raspberry Pi / Linux Service Setup

🐧 **Empfohlen fuer Always-on-Hosts**.

Fuer ein vollstaendiges Host-Bootstrap siehe [`setup_raspberrypi.md`](setup_raspberrypi.md).

Schnelles Pipeline-Setup:

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

Das orchestriert:
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

Service manuell in tmux starten:

```bash
./scripts/start_autopub_tmux.sh
```

Services/Ports validieren:

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## Legacy-macOS-Skripte

🍎 Legacy-Wrapper bleiben zur Kompatibilitaet mit aelteren lokalen Setups erhalten.

Das Repository enthaelt weiterhin legacy macOS-orientierte Wrapper:
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

Diese enthalten absolute `/Users/lachlan/...`-Pfade und Conda-Annahmen. Wenn du diesen Workflow nutzt, behalte sie bei, aber aktualisiere Pfade/venv/Tooling fuer deinen Host.

---

## Troubleshooting & Wartung

🛠️ **Bei Fehlern zuerst hier anfangen**.

- **Path Drift zwischen Maschinen**: Wenn Fehler fehlende Dateien unter `/Users/lachlan/...` oder `/home/lachlan/Projects/auto-publish` melden, Konstanten an deinen Hostpfad anpassen (`/home/lachlan/ProjectsLFS/AutoPublish` in diesem Workspace).
- **Secrets Hygiene**: Vor Push `~/.local/bin/detect-secrets scan` ausfuehren. Geleakte Credentials rotieren.
- **Processing-Backend-Fehler**: Wenn `process_video.py` „Failed to get the uploaded file path“ ausgibt, pruefe, ob die Upload-Antwort `file_path` im JSON enthaelt und der Processing-Endpunkt ZIP-Bytes zurueckgibt.
- **ChromeDriver-Mismatch**: Bei DevTools-Connection-Fehlern Chrome/Chromium- und Driver-Versionen angleichen (oder auf `webdriver-manager` umstellen).
- **Browser-Fokus-Probleme**: `bring_to_front` verlaesst sich auf Window-Title-Matching (Chromium/Chrome-Namensunterschiede koennen brechen).
- **Captcha-Unterbrechungen**: 2Captcha-/Turing-Credentials konfigurieren und Solver-Outputs bei Bedarf integrieren.
- **Veraltete Lock-Dateien**: Wenn geplante Runs nie starten, Prozessstatus pruefen und veraltete `autopub.lock` entfernen (Legacy-Skriptflow).
- **Zu pruefende Logs**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log` sowie Service-Journal-Logs.

---

## System erweitern

🧱 **Erweiterungspunkte** fuer neue Plattformen und sichereren Betrieb.

- **Neue Plattform hinzufuegen**: Ein `pub_*.py`-Modul kopieren, Selektoren/Flows anpassen, bei Bedarf `login_*.py` fuer QR-Reauth ergaenzen und dann Flags/Queue-Handling in `app.py` sowie CLI-Wiring in `autopub.py` anbinden.
- **Konfigurationsabstraktion**: Verstreute Konstanten in strukturierte Konfiguration migrieren (`config.yaml`/`.env` + typisiertes Modell) fuer Multi-Host-Betrieb.
- **Credential-Storage hardening**: Hard-coded oder shell-exponierte Sensitive-Flows durch sicheres Secret-Management ersetzen (`sudo -A`, Keychain, Vault/Secret-Manager).
- **Containerisierung**: Chromium/ChromeDriver + Python-Runtime + virtuelles Display in eine deploybare Einheit packen.

---

## Quick-Start-Checkliste

✅ **Minimaler Pfad zum ersten erfolgreichen Publish**.

1. Repository klonen und Abhaengigkeiten installieren (`pip install -r requirements.txt` oder schlankes `requirements.autopub.txt`).
2. Hard-coded Pfadkonstanten in `app.py`, `autopub.py` und allen verwendeten Skripten aktualisieren.
3. Erforderliche Credentials im Shell-Profil oder in `.env` exportieren; mit `python load_env.py` das Laden pruefen.
4. Remote-Debug-Browserprofilordner erstellen und jede benoetigte Plattform-Session einmal starten.
5. Auf jeder Zielplattform im jeweiligen Profil manuell anmelden.
6. Entweder API-Modus (`python app.py --port 8081`) oder CLI-Modus (`python autopub.py --use-cache ...`) starten.
7. Ein Sample-ZIP (API-Modus) oder eine Sample-Video-Datei (CLI-Modus) einspeisen und `logs/` pruefen.
8. Vor jedem Push Secrets-Scan ausfuehren.

---

## Entwicklungsnotizen

🧬 **Aktueller Entwicklungs-Baseline** (manuelles Formatting + Smoke-Testing).

- Python-Stil folgt der vorhandenen 4-Space-Indentation und manuellen Formatierung.
- Es gibt derzeit keine formale automatisierte Testsuite; stattdessen Smoke-Tests:
  - ein Sample-Video ueber `autopub.py` verarbeiten,
  - ein ZIP zu `/publish` posten und `/publish/queue` beobachten,
  - jede Zielplattform manuell validieren.
- Beim Hinzufuegen neuer Skripte einen kleinen `if __name__ == "__main__":`-Entrypoint fuer schnelle Dry-Runs ergaenzen.
- Plattformaenderungen nach Moeglichkeit isoliert halten (`pub_*`, `login_*`, `ignore_*`-Toggles).
- Runtime-Artefakte (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) sind lokal erwartet und groesstenteils von Git ignoriert.

---

## Roadmap

🗺️ **Priorisierte Verbesserungen anhand aktueller Codegrenzen**.

Geplante/gewuenschte Verbesserungen (basierend auf aktueller Codestruktur und vorhandenen Notizen):

1. Verstreute hard-coded Pfade durch zentrale Konfiguration ersetzen (`.env`/YAML + typisierte Modelle).
2. Hard-coded sudo-Passwortmuster entfernen und Prozesssteuerung auf sicherere Mechanismen umstellen.
3. Publish-Zuverlaessigkeit mit staerkeren Retries und besserer UI-State-Erkennung pro Plattform verbessern.
4. Plattformsupport erweitern (z. B. Kuaishou oder weitere Creator-Plattformen).
5. Runtime in reproduzierbare Deployment-Einheiten verpacken (Container + virtuelles Display-Profil).
6. Automatisierte Integrationschecks fuer ZIP-Vertrag und Queue-Ausfuehrung hinzufuegen.

---

## Contributing

🤝 PRs fokussiert halten, reproduzierbar machen und Runtime-Annahmen klar nennen.

Contributions sind willkommen.

1. Forken und einen fokussierten Branch erstellen.
2. Commits klein und im Imperativ halten (Beispielstil in der Historie: „Wait for YouTube checks before publishing“).
3. Manuelle Verifikationsnotizen in PRs aufnehmen:
   - Umgebungsannahmen,
   - Browser-/Session-Restarts,
   - relevante Logs/Screenshots bei UI-Flow-Aenderungen.
4. Niemals echte Secrets committen (`.env` ist ignoriert; `.env.example` nur fuer Struktur).

Wenn neue Publisher-Module eingefuehrt werden, alle folgenden Punkte verdrahten:
- `pub_<platform>.py`
- optional `login_<platform>.py`
- API-Flags und Queue-Handling in `app.py`
- CLI-Wiring in `autopub.py` (falls benoetigt)
- `ignore_<platform>`-Toggle-Handling
- README-Updates

---

## Lizenz

In diesem Repository-Snapshot ist aktuell keine `LICENSE`-Datei vorhanden.

Annahme fuer diesen Entwurf:
- Nutzung und Weiterverteilung als undefiniert behandeln, bis der Maintainer eine explizite Lizenzdatei hinzufuegt.

Empfohlene naechste Aktion:
- Eine Top-Level-`LICENSE` hinzufuegen (z. B. MIT/Apache-2.0/GPL-3.0) und diesen Abschnitt entsprechend aktualisieren.

> 📝 Solange keine Lizenzdatei existiert, Annahmen zu kommerzieller/interner Weiterverteilung als ungeklaert behandeln und direkt mit dem Maintainer klaeren.

---

## Danksagungen

- Maintainer- und Sponsor-Profil: [@lachlanchen](https://github.com/lachlanchen)
- Funding-Konfigurationsquelle: [`.github/FUNDING.yml`](.github/FUNDING.yml)
- In diesem Repository referenzierte Ecosystem-Services: Selenium, Tornado, SendGrid, 2Captcha, Turing-Captcha-APIs.

---

## AutoPublish unterstuetzen

💖 Community-Support finanziert Infrastruktur, Zuverlaessigkeitsarbeit und neue Plattformintegrationen.

AutoPublish ist Teil einer groesseren Initiative, Creator-Tooling fuer Cross-Platform-Verteilung offen und hackbar zu halten. Spenden helfen dabei:

- Selenium-Farm, Processing-API und Cloud-GPUs online zu halten.
- Neue Publisher (Kuaishou, Instagram Reels usw.) sowie Reliability-Fixes fuer bestehende Bots zu liefern.
- Mehr Dokumentation, Starter-Datasets und Tutorials fuer unabhaengige Creators bereitzustellen.

### Spenden

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
