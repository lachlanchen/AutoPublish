[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)



<div align="center">

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# AutoPublish

<p align="center">
  <strong>Skriptzentrierte, browsergesteuerte Veröffentlichung von Kurzvideos auf mehreren Plattformen.</strong><br/>
  <sub>Ein kanonisches Betriebs-Handbuch für Einrichtung, Runtime, Warteschlangenmodus und Plattform-Automatisierungsabläufe.</sub>
</p>

</div>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#voraussetzungen)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#systemueberblick)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#plattform-spezifische-hinweise)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#tornado-service-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-ar%20%7C%20de%20%7C%20es%20%7C%20fr%20%7C%20ja%20%7C%20ko%20%7C%20ru%20%7C%20vi%20%7C%20zh--Hans%20%7C%20zh--Hant-0EA5E9)](#inhaltsverzeichnis)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#lizenz)
[![Ops](https://img.shields.io/badge/Ops-Path%20Checks%20Required-orange)](#konfiguration)
[![Security](https://img.shields.io/badge/Security-Env%20Secrets%20Required-critical)](#sicherheits--ops-checkliste)
[![Service](https://img.shields.io/badge/Linux-Service%20Scripts%20Included-1D4ED8)](#raspberry-pi--linux-service-setup)

[![Workflow](https://img.shields.io/badge/Workflow-CLI%20%2F%20Queue-2563EB)](#nutzung)
[![Browser Engine](https://img.shields.io/badge/Browser-Chromium%20Remote%20Debug-4F46E5)](#browser-sitzungen-vorbereiten)
[![Input Formats](https://img.shields.io/badge/Inputs-videos%20%26%20ZIP-0891B2)](#metadaten--zip-format)

| Sprungziel | Link |
| --- | --- |
| Erstanwendung | [Erste Schritte](#start-here)
| Lauf mit lokalem Watcher | [CLI-Pipeline starten (`autopub.py`)](#running-the-cli-pipeline-autopubpy) |
| Lauf über HTTP-Warteschlange | [Tornado-Service starten (`app.py`)](#running-the-tornado-service-apppy) |
| Als Service bereitstellen | [Raspberry Pi / Linux Service Setup](#raspberry-pi--linux-service-setup) |
| Projekt unterstützen | [Support](#support-autopublish) |

Automatisierungs-Toolkit für die Verteilung von Kurzvideos auf mehrere chinesische und internationale Plattformen. Das Projekt kombiniert einen Tornado-basierten Service, Selenium-Automatisierungs-Bots und einen lokalen File-Watcher-Workflow, sodass das Ablegen eines Videos in einem Ordner schließlich zu Uploads auf XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), Instagram und optional YouTube führt.

Das Repository ist bewusst low-level ausgelegt: Die Hauptkonfiguration liegt in Python-Dateien und Shell-Skripten. Dieses Dokument ist ein operatives Handbuch für Setup, Runtime, und Erweiterungspunkte.

> ⚙️ **Betriebsphilosophie**: Dieses Projekt bevorzugt explizite Skripte und direkte Browser-Automatisierung statt versteckter Abstraktionsschichten.
> ✅ **Kanonische Policy für dieses README**: technische Details bewahren, dann Lesbarkeit und Auffindbarkeit verbessern.
> 🌍 **Lokalisierungsstatus (verifiziert im Workspace am 28. Februar 2026)**: `i18n/` umfasst aktuell Arabisch, Deutsch, Spanisch, Französisch, Japanisch, Koreanisch, Vietnamesisch, vereinfachtes Chinesisch und traditionelles Chinesisch.

### Schnellnavigation

| Ich möchte... | Gehe zu |
| --- | --- |
| Meine erste Veröffentlichung starten | [Quick-Start-Checkliste](#quick-start-checklist) |
| Laufzeitmodi vergleichen | [Laufzeitmodi auf einen Blick](#runtime-modes-at-a-glance) |
| Zugangsdaten und Pfade konfigurieren | [Konfiguration](#configuration) |
| API-Modus starten und Jobs in die Queue geben | [Tornado-Service starten (`app.py`)](#running-the-tornado-service-apppy) |
| Mit Copy/Paste-Befehlen validieren | [Beispiele](#examples) |
| Auf Raspberry Pi/Linux einrichten | [Raspberry Pi / Linux Service Setup](#raspberry-pi--linux-service-setup) |

<a id="start-here"></a>
## Erste Schritte

Wenn du neu in diesem Repository bist, nutze diese Reihenfolge:

1. Lies [Voraussetzungen](#prerequisites) und [Installation](#installation).
2. Konfiguriere Geheimnisse und absolute Pfade in [Konfiguration](#configuration).
3. Bereite Browser-Debug-Sessions in [Browser-Sitzungen vorbereiten](#preparing-browser-sessions) vor.
4. Wähle einen Runtime-Modus unter [Nutzung](#usage): `autopub.py` (Watcher) oder `app.py` (API-Queue).
5. Validiere mit den Befehlen aus [Beispiele](#examples).

<a id="overview"></a>
## Überblick

AutoPublish unterstützt derzeit zwei produktive Runtime-Modi:

1. **CLI-Watcher-Modus (`autopub.py`)** für ordnerbasiertes Einlesen und Veröffentlichen.
2. **API-Queue-Modus (`app.py`)** für ZIP-basiertes Veröffentlichen über HTTP (`/publish`, `/publish/queue`).

Es ist für Betreiber:innen gedacht, die transparente, skriptzentrierte Workflows gegenüber abstrakten Orchestrierungsplattformen bevorzugen.

### <a id="runtime-modes-at-a-glance"></a>Laufzeitmodi auf einen Blick

| Modus | Einstiegspunkt | Eingabe | Am besten geeignet für | Ausgabeverhalten |
| --- | --- | --- | --- | --- |
| CLI-Watcher | `autopub.py` | In `videos/` abgelegte Dateien | Lokale Operator-Workflows und Cron-/Service-Loops | Verarbeitet erkannte Videos und veröffentlicht sofort auf den ausgewählten Plattformen |
| API-Queue-Service | `app.py` | ZIP-Upload zu `POST /publish` | Integration mit vorgelagerten Systemen und Remote-Auslösung | Nimmt Jobs an, stellt sie in die Queue und verarbeitet sie in Worker-Reihenfolge |

### <a id="platform-coverage-snapshot"></a>Plattformabdeckung auf einen Blick

| Plattform | Publisher-Modul | Login-Helfer | Steuerport | CLI-Modus | API-Modus |
| --- | --- | --- | --- | --- | --- |
| XiaoHongShu | `pub_xhs.py` | `login_xiaohongshu.py` | `5003` | ✅ | ✅ |
| Douyin | `pub_douyin.py` | `login_douyin.py` | `5004` | ✅ | ✅ |
| Bilibili | `pub_bilibili.py` | N/A | `5005` | ✅ | ✅ |
| ShiPinHao (WeChat Channels) | `pub_shipinhao.py` | `login_shipinhao.py` | `5006` | Optional | ✅ |
| Instagram | `pub_instagram.py` | `login_instagram.py` | `5007` | Optional | ✅ |
| YouTube | `pub_y2b.py` | N/A | `9222` | Optional | ✅ |

<a id="quick-snapshot"></a>
## Kurzer Überblick

| Was | Wert | Farbleitsignal |
| --- | --- | --- |
| Primäre Sprache | Python 3.10+ | ![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white) |
| Haupt-Runtimes | CLI-Watcher (`autopub.py`) + Tornado-Queue-Service (`app.py`) | ![Modes](https://img.shields.io/badge/Modes-CLI%20%2B%20API-2563EB) |
| Automations-Engine | Selenium + Remote-Debug-Chromium-Sessions | ![Engine](https://img.shields.io/badge/Engine-Selenium-43B02A?logo=selenium&logoColor=white) |
| Eingabeformate | Rohvideos (`videos/`) und ZIP-Bundles (`/publish`) | ![Inputs](https://img.shields.io/badge/Inputs-videos%20%26%20ZIP-6B7280) |
| Aktueller Repo-Pfad | `/home/lachlan/ProjectsLFS/AutoPublish` | ![Workspace](https://img.shields.io/badge/Path-Verified-10B981) |
| Zielgruppe | Creator-/Ops-Engineers für Multi-Platform-Short-Video-Pipelines | ![Audience](https://img.shields.io/badge/Users-Operators-0F766E) |

### <a id="operational-safety-snapshot"></a>Sicherheits-Snapshot

| Thema | Aktueller Zustand | Aktion |
| --- | --- | --- |
| Hartkodierte Pfade | In mehreren Modulen/Skripten vorhanden | Pfadkonstanten je Host vor dem Produktionsbetrieb anpassen |
| Browser-Loginzustand | Erforderlich | Persistente Remote-Debug-Profile pro Plattform beibehalten |
| Captcha-Handling | Optionale Integrationen verfügbar | Bei Bedarf 2Captcha/Turing-Zugangsdaten konfigurieren |
| Lizenzangabe | Keine `LICENSE`-Datei im Repository-Root gefunden | Nutzungsbedingungen vor Weitergabe mit dem Maintainer klären |

### <a id="compatibility--assumptions"></a>Kompatibilität & Annahmen

| Punkt | Aktuelle Annahme in diesem Repo |
| --- | --- |
| Python | 3.10+ |
| Runtime-Umgebung | Linux Desktop/Server mit GUI-Verfügbarkeit für Chromium |
| Browser-Steuerungsmodus | Remote-Debugging-Sessions mit persistenten Profilverzeichnissen |
| Primärer API-Port | `8081` (`app.py --port`) |
| Verarbeitungs-Backend | `upload_url` + `process_url` müssen erreichbar sein und gültigen ZIP-Output liefern |
| In diesem Entwurf verwendeter Workspace | `/home/lachlan/ProjectsLFS/AutoPublish` |

---

<a id="table-of-contents"></a>
## Inhaltsverzeichnis

- [Erste Schritte](#start-here)
- [Überblick](#overview)
- [Laufzeitmodi auf einen Blick](#runtime-modes-at-a-glance)
- [Plattformabdeckung auf einen Blick](#platform-coverage-snapshot)
- [Kurzer Überblick](#quick-snapshot)
- [Sicherheits-Snapshot](#operational-safety-snapshot)
- [Kompatibilität & Annahmen](#compatibility--assumptions)
- [Systemübersicht](#system-overview)
- [Funktionen](#features)
- [Projektstruktur](#project-structure)
- [Repository-Layout](#repository-layout)
- [Voraussetzungen](#prerequisites)
- [Installation](#installation)
- [Konfiguration](#configuration)
- [Konfigurations-Checkliste](#configuration-verification-checklist)
- [Browser-Sitzungen vorbereiten](#preparing-browser-sessions)
- [Nutzung](#usage)
- [Beispiele](#examples)
- [Metadaten & ZIP-Format](#metadata--zip-format)
- [Daten- und Artefakt-Lebenszyklus](#data--artifact-lifecycle)
- [Plattform-spezifische Hinweise](#platform-specific-notes)
- [Raspberry Pi / Linux Service Setup](#raspberry-pi--linux-service-setup)
- [Legacy macOS Skripte](#legacy-macos-scripts)
- [Fehlerbehebung & Wartung](#troubleshooting--maintenance)
- [FAQ](#faq)
- [Das System erweitern](#extending-the-system)
- [Quick-Start-Checkliste](#quick-start-checklist)
- [Entwicklungsnotizen](#development-notes)
- [Roadmap](#roadmap)
- [Mitwirken](#contributing)
- [Sicherheits- & Ops-Checkliste](#security--ops-checklist)
- [Lizenz](#license)
- [Danksagung](#acknowledgements)
- [Support](#support-autopublish)

---

<a id="system-overview"></a>
## Systemübersicht

🎯 **End-to-End-Flow** von Rohmedien bis zu veröffentlichten Beiträgen:

```mermaid
flowchart LR
    A[Video in videos/] --> B[autopub.py watcher]
    B --> C[process_video.py]
    C --> D[ZIP + metadata in transcription_data/]
    D --> E[pub_*.py Selenium publishers]
    F[POST /publish ZIP] --> G[app.py queue worker]
    G --> E
    E --> H[Plattformen: XHS, Douyin, Bilibili, ShiPinHao, Instagram, YouTube]
```

Ablauf im Überblick:

1. **Rohes Material aufnehmen**: Lege ein Video in `videos/` ab. Der Watcher (`autopub.py` oder Scheduler/Service) erkennt neue Dateien über `videos_db.csv` und `processed.csv`.
2. **Asset-Generierung**: `process_video.VideoProcessor` lädt die Datei auf einen Content-Processing-Server hoch (`upload_url` und `process_url`), der ein ZIP-Paket liefert mit:
   - dem bearbeiteten/encodierten Video (`<stem>.mp4`),
   - einem Coverbild,
   - `{stem}_metadata.json` mit lokalisierter Titel-, Beschreibungs- und Tag-Information.
3. **Veröffentlichung**: Metadaten werden von den Selenium-Publishern in `pub_*.py` verwendet. Jeder Publisher verbindet sich mit einer bereits laufenden Chromium/Chrome-Instanz über Remote-Debugging-Ports und persistente User-Data-Verzeichnisse.
4. **Web-Steuerebene (optional)**: `app.py` stellt `/publish` bereit, nimmt vorgefertigte ZIP-Bundles entgegen, entpackt sie und stellt Publish-Jobs für dieselben Publisher in die Queue. Es kann außerdem Browser-Sessions aktualisieren und Login-Helfer auslösen (`login_*.py`).
5. **Unterstützungs-Module**: `load_env.py` lädt Secrets aus `~/.bashrc`, `utils.py` stellt Helferfunktionen bereit (Fensterfokus, QR-Handling, Mail-Helpers) und `solve_captcha_*.py` integriert Turing/2Captcha, wenn Captchas auftreten.

<a id="features"></a>
## Funktionen

✨ **Ausgelegt für pragmatische, skriptzentrische Automatisierung**:

- Multi-Plattform-Publishing: XiaoHongShu, Douyin, Bilibili, ShiPinHao (WeChat Channels), Instagram, YouTube (optional).
- Zwei Betriebsmodi: CLI-Watcher-Pipeline (`autopub.py`) und API-Queue-Service (`app.py` + `/publish` + `/publish/queue`).
- Plattformspezifische temporäre Deaktivierung über `ignore_*`-Dateien.
- Wiederverwendung von Browser-Sessions per Remote-Debugging mit persistenten Profilen.
- Optionale QR-/Captcha-Automatisierung und E-Mail-Benachrichtigungs-Helfer.
- Kein Frontend-Build erforderlich für die mitgelieferte PWA-Datei-Upload-Oberfläche (`pwa/`).
- Linux/Raspberry-Pi-Automatisierungsskripte für Service-Setup (`scripts/`).

### <a id="features"></a>Funktionsmatrix

| Fähigkeit | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Eingabequelle | Lokaler `videos/`-Watcher | Hochgeladenes ZIP via `POST /publish` |
| Warteschlange | Interner dateibasierter Fortschritt | Explizit in-memory Job-Queue |
| Plattform-Flags | CLI-Argumente (`--pub-*`) + `ignore_*` | Query-Parameter (`publish_*`) + `ignore_*` |
| Beste Passung | Einzelner Host/Operator-Workflow | Externe Systeme und Remote-Aktivierung |

---

<a id="project-structure"></a>
## Projektstruktur

Grober Überblick über Source-/Runtime-Layout:

```text
AutoPublish/
├── README.md
├── app.py
├── autopub.py
├── process_video.py
├── load_env.py
├── utils.py
├── pub_*.py                  # Plattform-Publisher
├── login_*.py                # Plattform-Login-/Session-Helfer
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
├── videos/                   # Runtime-Eingabe-Artefakte
├── logs/, logs-autopub/      # Runtime-Logs
├── temp/, temp_screenshot/   # Runtime-Temp-Artefakte
├── videos_db.csv
└── processed.csv
```

Hinweis: `transcription_data/` wird im Verarbeitungs-/Publishing-Flow zur Laufzeit genutzt und kann nach Ausführung entstehen.

<a id="repository-layout"></a>
## Repository-Layout

🗂️ **Zentrale Module und deren Aufgabe**:

| Pfad | Zweck |
| --- | --- |
| `app.py` | Tornado-Service mit Endpunkten `/publish` und `/publish/queue`, interner Publish-Queue und Worker-Thread. |
| `autopub.py` | CLI-Watcher: scannt `videos/`, verarbeitet neue Dateien und startet Publisher parallel. |
| `process_video.py` | Lädt Videos in das Verarbeitungs-Backend hoch und speichert zurückgelieferte ZIP-Bundles. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | Selenium-Automatisierungsmodul je Plattform. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | Session-Checks und QR-Login-Flows. |
| `utils.py` | Gemeinsame Automatisierungshilfen (Fensterfokus, QR-/Mail-Helfer, Diagnosefunktionen). |
| `load_env.py` | Lädt Umgebungsvariablen aus Shell-Profil (`~/.bashrc`) und maskiert sensible Logs. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | SMTP/SendGrid-Helfer und Testskripte. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Integrationen für Captcha-Löser. |
| `scripts/` | Service-Setup und Betriebs-Skripte (Raspberry Pi/Linux + Legacy-Automation). |
| `pwa/` | Statisches PWA-Frontend für ZIP-Vorschau und Publish-Einreichung. |
| `setup_raspberrypi.md` | Schritt-für-Schritt-Anleitung zur Raspberry-Pi-Bereitstellung. |
| `.env.example` | Umgebungs-Variablenvorlage (Credentials, Pfade, Captcha-Keys). |
| `.github/FUNDING.yml` | Sponsor-/Funding-Konfiguration. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | Runtime-Artefakte und Logs (meist gitignoriert). |

---

<a id="prerequisites"></a>
## Voraussetzungen

🧰 **Vor dem ersten Lauf installieren**.

### Betriebssystem und Werkzeuge

- Linux Desktop/Server mit X-Session (`DISPLAY=:1` ist in bereitgestellten Skripten üblich).
- Chromium/Chrome und passender ChromeDriver.
- GUI-/Medienwerkzeuge: `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv oder Conda).

### Python-Abhängigkeiten

Minimaler Runtime-Satz:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

Vollständiger Repo-Satz:

```bash
python -m pip install -r requirements.txt
```

Für schlanke Service-Installationen (Standard in Setup-Skripten):

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` enthält:
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Optional: sudo-User anlegen

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

<a id="installation"></a>
## Installation

🚀 **Einrichtung auf einer sauberen Maschine**:

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
# Werte in .env ausfüllen (nicht committen)
```

4. Variablen für Skripte laden, die Shell-Profile lesen:

```bash
source ~/.bashrc
python load_env.py
```

Hinweis: `load_env.py` ist auf `~/.bashrc` ausgerichtet. Wenn dein Shell-Profil anders ist, passe es entsprechend an.

---

<a id="configuration"></a>
## Konfiguration

🔐 **Credentials setzen, dann host-spezifische Pfade prüfen**.

### Umgebungsvariablen

Das Projekt erwartet Credentials und optionale Browser-/Runtime-Pfade aus Umgebungsvariablen. Starte mit `.env.example`:

| Variable | Beschreibung |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | SMTP-Zugangsdaten für QR/Login-Benachrichtigungen. |
| `SENDGRID_API_KEY` | SendGrid-Key für E-Mail-Flows, die SendGrid-APIs nutzen. |
| `APIKEY_2CAPTCHA` | 2Captcha-API-Key. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Turing-Captcha-Zugangsdaten. |
| `DOUYIN_LOGIN_PASSWORD` | Zweit-Authentifizierungshelfer für Douyin. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Overrides für Instagram/Browser-Treiber. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | Bevorzugte globale Browser/Driver/Display-Overrides in `app.py`. |

### Pfadkonstanten (wichtig)

📌 **Häufigster Startfehler**: nicht aufgelöste hartkodierte absolute Pfade.

Mehrere Module enthalten noch hartkodierte Pfade. Passe diese für deinen Host an:

| Datei | Konstante(n) | Bedeutung |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | API-Service-Roots und Backend-Endpunkte. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | CLI-Watcher-Roots und Backend-Endpunkte. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Absolute Pfade zu Python/Conda/Repo/Logs. | Legacy/macOS-orientierte Wrapper. |
| `utils.py` | FFmpeg-Pfadannahmen in Cover-Verarbeitungs-Helfern. | Medien-Tooling-Pfad-Kompatibilität. |

Wichtiger Repository-Hinweis:
- Aktueller Repository-Pfad in diesem Workspace ist `/home/lachlan/ProjectsLFS/AutoPublish`.
- Einige Dateien und Skripte referenzieren noch `/home/lachlan/Projects/auto-publish` oder `/Users/lachlan/...`.
- Bewahre solche Pfade lokal und passe sie vor produktivem Einsatz an.

### Plattform-Toggles über `ignore_*`

🧩 **Schneller Sicherheits-Schalter**: Das Anlegen einer `ignore_*`-Datei deaktiviert den Publisher ohne Codeänderung.

Publishing-Flags werden ebenfalls über Ignore-Dateien gesteuert. Lege leere Dateien an, um eine Plattform zu deaktivieren:

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

Entferne die entsprechende Datei wieder, um zu reaktivieren.

### Checkliste zur Konfigurationsprüfung

Führe diese schnelle Validierung nach `.env` und Pfadkonstanten durch:

```bash
python -c "import os;print('AUTOPUBLISH_BROWSER_BIN=', os.getenv('AUTOPUBLISH_BROWSER_BIN'));print('AUTOPUBLISH_CHROMEDRIVER=', os.getenv('AUTOPUBLISH_CHROMEDRIVER'));print('DISPLAY=', os.getenv('DISPLAY') or os.getenv('AUTOPUBLISH_DISPLAY'))"
python -c "from load_env import load_env_from_bashrc; load_env_from_bashrc(); print('Environment load OK')"
python -c "import os; p=os.getenv('AUTOPUBLISH_CHROMEDRIVER') or os.getenv('CHROMEDRIVER_PATH') or '/usr/bin/chromedriver'; print(p, 'exists=', os.path.exists(p))"
```

Fehlt ein Wert, aktualisiere `.env`, `~/.bashrc` oder skriptseitige Konstanten vor dem Start der Publisher.

---

<a id="preparing-browser-sessions"></a>
## Browser-Sitzungen vorbereiten

🌐 **Sitzungspersistenz ist Pflicht** für verlässliche Selenium-Publikationen.

1. Eigene Profilordner anlegen:

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. Browser-Sessions mit Remote-Debugging starten (Beispiel für XiaoHongShu):

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. Für jede Plattform/jedes Profil einmal manuell einloggen.

4. Prüfe, dass Selenium sich anhängen kann:

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Sicherheitshinweis:
- `app.py` enthält aktuell ein hartkodiertes `sudo`-Passwort-Platzhalterfeld (`password = "1"`) in der Browser-Neustartlogik. Ersetze es vor echtem Betrieb.

---

<a id="usage"></a>
## Nutzung

▶️ **Zwei Runtime-Modi** sind verfügbar: CLI-Watcher und API-Queue-Service.

<a id="running-the-cli-pipeline-autopubpy"></a>
### CLI-Pipeline ausführen (`autopub.py`)

1. Lege Quelldateien ins Watch-Verzeichnis (`videos/` oder dein konfiguriertes `autopublish_folder_path`).
2. Starte:

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Flags:

| Flag | Bedeutung |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Beschränkt Veröffentlichung auf ausgewählte Plattformen. Wenn keiner angegeben ist, sind alle drei standardmäßig aktiv. |
| `--test` | Testmodus, der an Publisher übergeben wird (Verhalten plattformabhängig). |
| `--use-cache` | Wiederverwendung vorhandener `transcription_data/<video>/<video>.zip` wenn vorhanden. |

CLI-Ablauf pro Video:
- Upload/Verarbeitung über `process_video.py`.
- Entpacken des ZIP nach `transcription_data/<video>/`.
- Start der gewählten Publisher via `ThreadPoolExecutor`.
- Aktualisierung von `videos_db.csv` und `processed.csv`.

<a id="running-the-tornado-service-apppy"></a>
### Tornado-Service ausführen (`app.py`)

🛰️ **API-Modus** ist nützlich für externe Systeme, die ZIP-Bundles erzeugen.

Server starten:

```bash
python app.py --refresh-time 1800 --port 8081
```

API-Endpunkt-Übersicht:

| Endpunkt | Methode | Zweck |
| --- | --- | --- |
| `/publish` | `POST` | ZIP-Daten hochladen und einen Publish-Job in die Queue stellen |
| `/publish/queue` | `GET` | Queue, Job-Historie und Publish-Status einsehen |

### `POST /publish`

📤 **Einen Publish-Job in die Queue stellen** durch direkten ZIP-Upload.

- Header: `Content-Type: application/octet-stream`
- Erforderlich: Query-/Form-Parameter `filename` (ZIP-Dateiname)
- Optionale Booleans: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: rohe ZIP-Daten

Beispiel:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

Aktuelles Verhalten im Code:
- Die Anfrage wird angenommen und in die Queue gestellt.
- Die Sofortantwort liefert JSON mit `status: queued`, `job_id` und `queue_size`.
- Der Worker verarbeitet Jobs seriell.

### `GET /publish/queue`

📊 **Queue-Gesundheit und In-Flight-Jobs beobachten**.

Die Queue-Status-/History-Antwort liefert JSON:

```bash
curl "http://localhost:8081/publish/queue"
```

Antwortfelder sind u. a.:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Browser-Refresh-Thread

♻️ Regelmäßiges Browser-Refreshing reduziert Sessionfehler bei hoher Laufzeit.

`app.py` führt einen Hintergrund-Refresh-Thread mit `--refresh-time`-Intervall aus und nutzt Login-Checks. Das Refresh-Sleep enthält zufällige Verzögerungen.

### PWA-Frontend (`pwa/`)

🖥️ Leichtgewichtige statische Oberfläche für manuelle ZIP-Uploads und Queue-Übersicht.

Lokales UI starten:

```bash
cd pwa
python -m http.server 5173
```

Öffne `http://localhost:5173` und setze die Backend-Basis-URL (z. B. `http://lazyingart:8081`).

PWA-Funktionen:
- Drag/drop ZIP-Vorschau.
- Publish-Ziele-Umschaltung + Testmodus.
- Sendet an `/publish` und pollt `/publish/queue`.

### Command Palette

🧷 **Die meistgenutzten Befehle gesammelt an einem Ort**.

| Aufgabe | Befehl |
| --- | --- |
| Volle Abhängigkeiten installieren | `python -m pip install -r requirements.txt` |
| Leichte Laufzeit-Abhängigkeiten installieren | `python -m pip install -r requirements.autopub.txt` |
| Shell-basierte Env-Vars laden | `source ~/.bashrc && python load_env.py` |
| API-Queue-Server starten | `python app.py --refresh-time 1800 --port 8081` |
| CLI-Watcher-Pipeline starten | `python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili` |
| ZIP in die Queue einreichen | `curl -X POST "http://localhost:8081/publish?filename=demo.zip" --data-binary @demo.zip -H "Content-Type: application/octet-stream"` |
| Queue-Status prüfen | `curl -s "http://localhost:8081/publish/queue"` |
| Lokales PWA bereitstellen | `cd pwa && python -m http.server 5173` |

---

<a id="examples"></a>
## Beispiele

🧪 **Copy/Paste-Smoke-Test-Befehle**:

### Beispiel 0: Environment laden und API-Server starten

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

### Beispiel C: Queue-Status prüfen

```bash
curl -s "http://localhost:8081/publish/queue"
```

### Beispiel D: SMTP-Helfer Smoke-Test

```bash
python smtp.py
python smtp_test_simple.py
```

---

<a id="metadata--zip-format"></a>
## Metadaten & ZIP-Format

📦 **ZIP-Vertrag ist wichtig**: Dateinamen und Metadaten-Schlüssel müssen zu Publisher-Erwartungen passen.

Erwartete ZIP-Inhalte (Minimum):

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` treibt die CN-Publisher; optional `metadata["english_version"]` wird vom YouTube-Publisher genutzt.

Felder, die typischerweise in Modulen verwendet werden:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (Hashtag-Liste)
- `video_filename`, `cover_filename`
- Plattform-spezifische Felder entsprechend den `pub_*.py`-Modulen

Wenn du ZIPs extern erzeugst, halte Schlüssel und Dateinamen an den Modul-Erwartungen.

<a id="data--artifact-lifecycle"></a>
## Daten- und Artefakt-Lebenszyklus

Die Pipeline erzeugt lokale Artefakte, die Operatoren bewusst aufbewahren, rotieren oder bereinigen sollten:

| Artefakt | Ort | Erzeugt von | Warum relevant |
| --- | --- | --- | --- |
| Eingangsvideos | `videos/` | Manueller Drop oder Upstream-Sync | Quellmedien für CLI-Watcher-Modus |
| Verarbeitungs-ZIP-Ausgabe | `transcription_data/<stem>/<stem>.zip` | `process_video.py` | Wiederverwendbare Payload für `--use-cache` |
| Extrahierte Publish-Assets | `transcription_data/<stem>/...` | ZIP-Extraktion in `autopub.py` / `app.py` | Publisher-bereite Dateien und Metadaten |
| Publish-Logs | `logs/`, `logs-autopub/` | CLI/API-Runtime | Fehleranalyse und Audit-Trail |
| Browser-Logs | `~/chromium_dev_session_logs/*.log` (oder Chrome-Prefix) | Browser-Startskripte | Diagnose von Session/Port/Startup-Problemen |
| Tracking-CSVs | `videos_db.csv`, `processed.csv` | CLI-Watcher | Verhindert Doppelverarbeitung |

Empfehlung zur Bereinigung:
- Plane einen periodischen Cleanup/Archivierungsjob für alte `transcription_data/`, `temp/` und alte Logs, um Festplattenengpässe zu vermeiden.

<a id="platform-specific-notes"></a>
## Plattform-spezifische Hinweise

🧭 **Port-Matrix + Modulverantwortung** je Publisher.

| Plattform | Port | Modul(e) | Hinweise |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | QR-Re-Login-Flow; Titel-Sanitizing und Hashtag-Verwendung aus Metadaten. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Upload-Abschlussprüfungen und Retry-Pfade sind plattform-sensitiv; Logs engmaschig beobachten. |
| Bilibili | 5005 | `pub_bilibili.py` | Captcha-Hooks vorhanden über `solve_captcha_2captcha.py` und `solve_captcha_turing.py`. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Schnelle QR-Genehmigung ist wichtig für zuverlässige Session-Erneuerung. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | Im API-Modus mit `publish_instagram=true` gesteuert; Env-Variablen in `.env.example`. |
| YouTube | 9222 | `pub_y2b.py` | Nutzt Metadatenblock `english_version`; mit `ignore_y2b` deaktivierbar. |

<a id="raspberry-pi--linux-service-setup"></a>
## Raspberry Pi / Linux Service Setup

🐧 **Empfohlen für dauerhaft laufende Hosts**.

Für vollständiges Host-Bootstrapping folge [`setup_raspberrypi.md`](setup_raspberrypi.md).

Schnell-Setup:

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

Dabei werden orchestriert:
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

Service manuell in tmux starten:

```bash
./scripts/start_autopub_tmux.sh
```

Services/Ports prüfen:

```bash
systemctl status autopub.service autopub-vnc.service
sudo ss -ltnp | grep 590
```

Kompatibilitäts-Hinweis:
- Ältere Doku/Skripte referenzieren noch `virtual-desktop.service`; aktuelle Setup-Skripte installieren `autopub-vnc.service`.

<a id="legacy-macos-scripts"></a>
## Legacy-macOS-Skripte

🍎 Ältere Wrapper bleiben für Kompatibilität mit älteren lokalen Setups.

Das Repository enthält weiterhin macOS-orientierte Legacy-Wrapper:
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

Diese enthalten absolute `/Users/lachlan/...`-Pfade und Conda-Annahmen. Behalte sie bei, wenn du diesen Workflow nutzt, passe aber Pfade/venv/Tooling für deinen Host an.

<a id="troubleshooting--maintenance"></a>
## Fehlerbehebung & Wartung

🛠️ **Wenn etwas fehlschlägt, zuerst hier anfangen**.

- **Pfadangleichheit über Hosts**: Wenn Fehler fehlende Dateien unter `/Users/lachlan/...` oder `/home/lachlan/Projects/auto-publish` melden, richte Konstanten auf deinen Host-Pfad aus (`/home/lachlan/ProjectsLFS/AutoPublish` in diesem Workspace).
- **Secrets-Hygiene**: Führe `~/.local/bin/detect-secrets scan` vor dem Push aus. Drehe ggf. bekannte Credentials.
- **Verarbeitungs-Backend-Fehler**: Wenn `process_video.py` „Failed to get the uploaded file path“ zeigt, prüfe, ob die Upload-Response-JSON `file_path` enthält und der Verarbeitungs-Endpunkt ZIP-Daten zurückgibt.
- **ChromeDriver-Mismatch**: Bei DevTools-Verbindungsfehlern Chrome/Chromium und Treiberversionen angleichen (oder auf `webdriver-manager` wechseln).
- **Browser-Fokus-Probleme**: `bring_to_front` hängt vom Fenstertitel ab (Unterschiede in Chromium/Chrome-Namen können brechen).
- **Captcha-Unterbrechungen**: 2Captcha/Turing konfigurieren und Solver-Ausgaben dort integrieren, wo nötig.
- **Veraltete Sperrdateien**: Wenn geplante Läufe nie starten, Prozessstatus prüfen und `autopub.lock` entfernen (legacy Skriptfluss).
- **Zu prüfende Logs**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log` sowie Service-Journal-Logs.

<a id="faq"></a>
## FAQ

**F: Kann ich API-Modus und CLI-Watcher parallel betreiben?**  
A: Das ist möglich, aber nur empfehlenswert, wenn Eingaben und Browser-Sessions sauber isoliert sind. Beide Modi können um dieselben Publisher, Dateien und Ports konkurrieren.

**F: Warum gibt `/publish` `queued` zurück, aber es ist noch nichts veröffentlicht?**  
A: `app.py` stellt Jobs zuerst in die Queue, anschließend verarbeitet ein Hintergrundworker sie seriell. Prüfe `/publish/queue`, `is_publishing` und Service-Logs.

**F: Benötige ich `load_env.py`, wenn ich bereits `.env` nutze?**  
A: `start_autopub_tmux.sh` liest `.env`, wenn vorhanden; einige direkte Läufe verlassen sich auf Shell-Environment. `.env` und Shell-Exports konsistent zu halten vermeidet Überraschungen.

**F: Wie ist das minimale ZIP-Format für API-Uploads?**  
A: Ein gültiges ZIP mit `{stem}_metadata.json`, dazu Video- und Cover-Dateinamen, die zu den Metadaten-Schlüsseln passen (`video_filename`, `cover_filename`).

**F: Wird ein Headless-Modus unterstützt?**  
A: Einige Module haben headless-bezogene Variablen, aber der primäre dokumentierte Betriebsmodus dieses Repos ist GUI-basierte Browser-Sessions mit persistenten Profilen.

<a id="extending-the-system"></a>
## Das System erweitern

🧱 **Erweiterungspunkte** für neue Plattformen und stabileren Betrieb.

- **Neue Plattform hinzufügen**: kopiere ein `pub_*.py`-Modul, passe Selektoren/Flows an, ergänze bei Bedarf `login_*.py` für QR-Re-Auth und verdrahte Flags plus Queue-Handling in `app.py` und CLI-Anbindung in `autopub.py`.
- **Konfigurationsabstraktion**: migriere verstreute Konstanten in strukturierte Konfiguration (`config.yaml`/`.env` + getypte Modelle) für Multi-Host-Betrieb.
- **Credential-Sicherheit verbessern**: ersetze harte oder shell-offene sensitive Flows durch sicheres Secret-Management (`sudo -A`, Keychain, Vault/Secret-Manager).
- **Containerisierung**: Chromium/ChromeDriver + Python-Runtime + virtuellen Display in eine ausrollbare Einheit für Cloud/Server-Umgebungen packen.

<a id="quick-start-checklist"></a>
## Quick-Start-Checkliste

✅ **Minimaler Pfad zu erstem erfolgreichen Publish**.

1. Repository klonen und Abhängigkeiten installieren (`pip install -r requirements.txt` oder schlankes `requirements.autopub.txt`).
2. Hartkodierte Pfadkonstanten in `app.py`, `autopub.py` und in allen auszuführenden Skripten anpassen.
3. Benötigte Credentials in Shell-Profil oder `.env` exportieren; `python load_env.py` zur Validierung ausführen.
4. Remote-Debug-Browserprofilordner anlegen und jede benötigte Plattform-Session einmal starten.
5. Manuell auf jeder Zielplattform im jeweiligen Profil anmelden.
6. Entweder API-Modus (`python app.py --port 8081`) oder CLI-Modus (`python autopub.py --use-cache ...`) starten.
7. Ein Beispiel-ZIP (API-Modus) oder eine Beispielvideodatei (CLI-Modus) einreichen und `logs/` prüfen.
8. Vor jedem Push einen Secrets-Scan ausführen.

<a id="development-notes"></a>
## Entwicklungsnotizen

🧬 **Aktuelle Entwicklungsgrundlage** (manuelles Format + Smoke-Testing).

- Python-Stil folgt bestehender 4-Space-Einrückung und manueller Formatierung.
- Es gibt aktuell keine formale automatisierte Testsuite; stütze dich auf Smoke-Tests:
  - verarbeite ein Beispielvideo durch `autopub.py`;
  - sende ein ZIP an `/publish` und beobachte `/publish/queue`;
  - validiere jede Zielplattform manuell.
- Füge einen kleinen `if __name__ == "__main__":`-Entrypoint hinzu, wenn neue Skripte ergänzt werden, für schnelle Dry-Runs.
- Halte Plattformänderungen isoliert, wo möglich (`pub_*`, `login_*`, `ignore_*`-Schalter).
- Runtime-Artefakte (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) sind lokal zu erwarten und meist gitignored.

<a id="roadmap"></a>
## Roadmap

🗺️ **Priorisierte Verbesserungen entsprechend aktuellen Code-Constraints**.

Geplante/erwünschte Verbesserungen (auf Basis aktueller Code-Struktur und bestehender Notizen):

1. Verstreute hartkodierte Pfade durch zentrale Konfiguration ersetzen (`.env`/YAML + getypte Modelle).
2. Hartkodierte `sudo`-Passwortmuster entfernen und Prozesssteuerung auf sicherere Mechanismen umstellen.
3. Veröffentlichungssicherheit durch robustere Retries und bessere UI-State-Detection pro Plattform verbessern.
4. Plattformabdeckung erweitern (z. B. Kuaishou oder weitere Creator-Plattformen).
5. Runtime in reproduzierbaren Deploy-Einheiten verpacken (Container + virtuelles Display-Profile).
6. Automatisierte Integrationsprüfungen für ZIP-Vertrag und Queue-Ausführung ergänzen.

<a id="contributing"></a>
## Mitwirken

🤝 Halte PRs fokussiert, reproduzierbar und explizit bzgl. Laufzeitannahmen.

Beiträge sind willkommen.

1. Forken und fokussierten Branch erstellen.
2. Kleine und imperative Commits (Beispielstil aus Historie: "Wait for YouTube checks before publishing").
3. Manuelle Verifikationsnotizen in PRs aufnehmen:
   - Umgebungsannahmen,
   - Browser-/Session-Neustarts,
   - relevante Logs/Screenshots für UI-Flow-Änderungen.
4. Nie echte Secrets committen (`.env` ist ignored; nutze `.env.example` nur als Schema).

Wenn neue Publisher-Module eingeführt werden, müssen alle Punkte verdrahtet werden:
- `pub_<platform>.py`
- optional `login_<platform>.py`
- API-Flags und Queue-Handling in `app.py`
- CLI-Anbindung in `autopub.py` (falls nötig)
- `ignore_<platform>`-Toggle-Handling
- README-Updates

<a id="security--ops-checklist"></a>
## Sicherheits- & Ops-Checkliste

Vor jedem produktionsnahen Lauf:

1. Sicherstellen, dass `.env` lokal existiert und nicht getrackt wird.
2. Credentials, die jemals committed wurden, rotieren/entfernen.
3. Platzhalterwerte für sensible Pfade im Code ersetzen (z. B. hartkodiertes sudo-Passwort in `app.py`).
4. Prüfen, ob `ignore_*`-Schalter vor Batch-Runs beabsichtigt sind.
5. Browser-Profile je Plattform isolieren und minimal-privilegierte Accounts verwenden.
6. Prüfen, dass Logs vor Teilen in Issue-Reports keine Secrets enthalten.
7. Vor Push `detect-secrets` (oder Äquivalent) ausführen.

<a id="support-autopublish"></a>
## Lizenz

In diesem Repository-Snapshot liegt derzeit keine `LICENSE`-Datei vor.

Annahme für diesen Entwurf:
- Nutze und verteile das Projekt nur nach Klärung, da die kommerziellen/internen Nutzungsannahmen bis zur expliziten Lizenzdatei offen sind.

Empfohlene nächste Aktion:
- Füge eine Top-Level-`LICENSE` hinzu (z. B. MIT/Apache-2.0/GPL-3.0) und passe diesen Abschnitt entsprechend an.

> 📝 Solange keine Lizenzdatei hinzugefügt wurde, gelten Annahmen zu kommerzieller/innerbetrieblicher Weitergabe als ungeklärt; bitte direkt mit dem Maintainer abstimmen.

---

<a id="acknowledgements"></a>
## Danksagung

- Maintainer- und Sponsorprofil: [@lachlanchen](https://github.com/lachlanchen)
- Funding-Konfigurationsquelle: [`.github/FUNDING.yml`](.github/FUNDING.yml)
- Ökosystemdienste, die in diesem Repo genutzt werden: Selenium, Tornado, SendGrid, 2Captcha, Turing captcha APIs.


## ❤️ Support

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://camo.githubusercontent.com/24a4914f0b42c6f435f9e101621f1e52535b02c225764b2f6cc99416926004b7/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f446f6e6174652d4c617a79696e674172742d3045413545393f7374796c653d666f722d7468652d6261646765266c6f676f3d6b6f2d6669266c6f676f436f6c6f723d7768697465)](https://chat.lazying.art/donate) | [![PayPal](https://camo.githubusercontent.com/d0f57e8b016517a4b06961b24d0ca87d62fdba16e18bbdb6aba28e978dc0ea21/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f50617950616c2d526f6e677a686f754368656e2d3030343537433f7374796c653d666f722d7468652d6261646765266c6f676f3d70617970616c266c6f676f436f6c6f723d7768697465)](https://paypal.me/RongzhouChen) | [![Stripe](https://camo.githubusercontent.com/1152dfe04b6943afe3a8d2953676749603fb9f95e24088c92c97a01a897b4942/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f5374726970652d446f6e6174652d3633354246463f7374796c653d666f722d7468652d6261646765266c6f676f3d737472697065266c6f676f436f6c6f723d7768697465)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |
