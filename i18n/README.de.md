[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)



[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

<div align="center">

# AutoPublish

<p align="center">
  <strong>Skriptbasierte, browsergesteuerte Veröffentlichung von Kurzvideos auf mehreren Plattformen.</strong><br/>
  <sub>Ein kanonisches Betriebs-Handbuch für Einrichtung, Laufzeit, Warteschlangenmodus und Plattform-Automatisierungsabläufe.</sub>
</p>

</div>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#voraussetzungen)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#systemueberblick)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#plattform-spezifische-anweisungen)
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

| Ziel | Link |
| --- | --- |
| Erstanwendung | [Hier starten](#start-here) |
| Mit lokalem Watcher ausführen | [CLI-Pipeline starten (`autopub.py`)](#running-the-cli-pipeline-autopubpy) |
| Über HTTP-Warteschlange starten | [Tornado-Service starten (`app.py`)](#running-the-tornado-service-apppy) |
| Als Service bereitstellen | [Raspberry-Pi-/Linux-Service-Setup](#raspberry-pi--linux-service-setup) |
| Projekt unterstützen | [Support](#support-autopublish) |

Dieses Automation-Toolkit verteilt Kurzvideos auf mehreren chinesischen und internationalen Plattformen für Creator. Das Projekt kombiniert einen Tornado-basierten Dienst, Selenium-Automatisierungs-Bots und einen lokalen File-Watcher-Workflow, sodass das Ablegen eines Videos in einem Ordner schließlich Uploads zu XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), Instagram und optional YouTube auslöst.

Das Repository ist bewusst niedrigschichtig aufgebaut: Die Hauptkonfiguration liegt in Python-Dateien und Shell-Skripten. Dieses Dokument ist ein operatives Handbuch zu Einrichtung, Laufzeit, Warteschlange und Erweiterungspunkten.

> ⚙️ **Betriebsphilosophie**: Dieses Projekt bevorzugt explizite Skripte und direkte Browser-Automatisierung statt versteckter Abstraktionsschichten.
> ✅ **Kanonische Regel für dieses README**: technische Details erhalten, danach Lesbarkeit und Auffindbarkeit verbessern.
> 🌍 **Lokalisierungsstatus (verifiziert in diesem Workspace am 28. Februar 2026)**: `i18n/` enthält Arabisch, Deutsch, Spanisch, Französisch, Japanisch, Koreanisch, Vietnamesisch, vereinfachtes Chinesisch und traditionelles Chinesisch.

### Schnellnavigation

| Ich möchte... | Gehe zu |
| --- | --- |
| Meine erste Veröffentlichung starten | [Schnellstart-Checkliste](#quick-start-checklist) |
| Laufzeitmodi vergleichen | [Laufzeitmodi auf einen Blick](#runtime-modes-at-a-glance) |
| Zugangsdaten und Pfade konfigurieren | [Konfiguration](#configuration) |
| API-Modus starten und Queue-Jobs auslösen | [Tornado-Service starten (`app.py`)](#running-the-tornado-service-apppy) |
| Mit Copy/Paste prüfen | [Beispiele](#examples) |
| Auf Raspberry Pi/Linux einrichten | [Raspberry-Pi-/Linux-Service-Setup](#raspberry-pi--linux-service-setup) |

<a id="start-here"></a>
## Erste Schritte

Wenn du neu in diesem Repository bist, nutze diese Reihenfolge:

1. Lies [Voraussetzungen](#prerequisites) und [Installation](#installation).
2. Konfiguriere Secrets und absolute Pfade in [Konfiguration](#configuration).
3. Bereite Browser-Debug-Sessions in [Browser-Sitzungen vorbereiten](#preparing-browser-sessions) vor.
4. Wähle einen Runtime-Modus unter [Nutzung](#usage): `autopub.py` (Watcher) oder `app.py` (API-Queue).
5. Überprüfe die Ergebnisse mit den Befehlen aus [Beispiele](#examples).

<a id="overview"></a>
## Überblick

AutoPublish unterstützt aktuell zwei produktive Betriebsmodi:

1. **CLI-Watcher-Modus (`autopub.py`)** für ordnerbasiertes Einlesen und Veröffentlichen.
2. **API-Queue-Modus (`app.py`)** für ZIP-basiertes Veröffentlichen über HTTP (`/publish`, `/publish/queue`).

Das Projekt ist für Betreiber:innen gedacht, die transparente, skriptzentrierte Workflows gegenüber abstrakten Orchestrierungsplattformen bevorzugen.

### <a id="runtime-modes-at-a-glance"></a>Laufzeitmodi auf einen Blick

| Modus | Einstiegspunkt | Eingabe | Geeignet für | Ausgabeverhalten |
| --- | --- | --- | --- | --- |
| CLI-Watcher | `autopub.py` | Dateien in `videos/` | Lokale Operator-Workflows und Cron-/Service-Schleifen | Erkanntes Material wird sofort an die gewählten Plattformen übertragen |
| API-Queue-Service | `app.py` | ZIP-Upload auf `POST /publish` | Integrationen mit vorgelagerten Systemen und Remote-Auslösern | Nimmt Jobs entgegen, enqueuet sie und verarbeitet sie in Worker-Reihenfolge |

### <a id="platform-coverage-snapshot"></a>Plattformabdeckung auf einen Blick

| Plattform | Publisher-Modul | Login-Helfer | Kontrollport | CLI-Modus | API-Modus |
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

| Thema | Aktueller Stand | Aktion |
| --- | --- | --- |
| Hardcodierte Pfade | In mehreren Modulen/Skripten vorhanden | Pfadkonstanten pro Host vor dem Produktionseinsatz anpassen |
| Browser-Login-Zustand | Erforderlich | Persistente Remote-Debug-Profile pro Plattform beibehalten |
| Captcha-Handling | Optionale Integrationen verfügbar | Bei Bedarf 2Captcha-/Turing-Anmeldedaten konfigurieren |
| Lizenzangabe | Keine `LICENSE` im Repository-Root erkannt | Nutzungsbedingungen vor Weitergabe mit dem Maintainer klären |

### <a id="compatibility--assumptions"></a>Kompatibilität & Annahmen

| Punkt | Annahme in diesem Repository |
| --- | --- |
| Python | 3.10+ |
| Laufzeitumgebung | Linux-Desktop/Server mit GUI-Verfügbarkeit für Chromium |
| Browser-Steuerung | Remote-Debugging-Sessions mit persistenten Profilverzeichnissen |
| Primärer API-Port | `8081` (`app.py --port`) |
| Verarbeitungs-Backend | `upload_url` + `process_url` müssen erreichbar sein und gültigen ZIP-Output liefern |
| Für diesen Entwurf verwendeter Workspace | `/home/lachlan/ProjectsLFS/AutoPublish` |

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
- [Raspberry-Pi / Linux Service Setup](#raspberry-pi--linux-service-setup)
- [Legacy macOS-Skripte](#legacy-macos-scripts)
- [Fehlersuche & Wartung](#troubleshooting--maintenance)
- [FAQ](#faq)
- [System erweitern](#extending-the-system)
- [Schnellstart-Checkliste](#quick-start-checklist)
- [Entwicklungshinweise](#development-notes)
- [Roadmap](#roadmap)
- [Mitwirken](#contributing)
- [Sicherheits- & Ops-Checkliste](#security--ops-checklist)
- [Lizenz](#license)
- [Danksagung](#acknowledgements)
- [❤️ Support](#support-autopublish)

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

1. **Eingabe von Rohmaterial**: Lege ein Video in `videos/`. Der Watcher (`autopub.py` oder Scheduler/Service) erkennt neue Dateien über `videos_db.csv` und `processed.csv`.
2. **Asset-Generierung**: `process_video.VideoProcessor` lädt die Datei auf einen Content-Processing-Server hoch (`upload_url` und `process_url`), der ein ZIP-Paket zurückliefert, das Folgendes enthält:
   - das bearbeitete/encodierte Video (`<stem>.mp4`),
   - ein Coverbild,
   - `{stem}_metadata.json` mit lokalisierten Titeln, Beschreibungen, Tags etc.
3. **Veröffentlichung**: Metadaten steuern die Selenium-Publisher in `pub_*.py`. Jeder Publisher verbindet sich mit einer bereits laufenden Chromium/Chrome-Instanz über Remote-Debugging-Ports und persistente Benutzerprofil-Ordner.
4. **Web-Steuerebene (optional)**: `app.py` stellt `/publish` bereit, nimmt vorgefertigte ZIP-Bundles entgegen, entpackt sie und legt Veröffentlichungsjobs für dieselben Publisher in die Queue. Es kann außerdem Browser-Sessions erneuern und Login-Helfer (`login_*.py`) auslösen.
5. **Support-Module**: `load_env.py` lädt Secrets aus `~/.bashrc`, `utils.py` stellt Hilfsfunktionen bereit (Fensterfokus, QR-Verarbeitung, Mail-Utilities) und `solve_captcha_*.py` integriert Turing/2Captcha, falls Captchas auftauchen.

<a id="features"></a>
## Funktionen

✨ **Ausgelegt für pragmatische, skriptzentrierte Automatisierung**:

- Multi-Plattform-Publishing: XiaoHongShu, Douyin, Bilibili, ShiPinHao (WeChat Channels), Instagram, YouTube (optional).
- Zwei Betriebsmodi: CLI-Watcher-Pipeline (`autopub.py`) und API-Queue-Service (`app.py` + `/publish` + `/publish/queue`).
- Plattformen können per `ignore_*`-Dateien vorübergehend deaktiviert werden.
- Wiederverwendung von Browser-Sessions per Remote-Debugging mit persistenten Profilen.
- Optionale QR-/Captcha-Automatisierung und E-Mail-Benachrichtigungs-Utilities.
- Kein Frontend-Build erforderlich für die enthaltene PWA (`pwa/`) für Uploads.
- Linux-/Raspberry-Pi-Automatisierungsskripte für Service-Einrichtung (`scripts/`).

### <a id="feature-matrix"></a>Funktionsmatrix

| Fähigkeit | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Eingabequelle | Lokaler `videos/`-Watcher | Hochgeladenes ZIP via `POST /publish` |
| Queueing | Interner dateibasierter Fortschritt | Explizite In-Memory-Job-Queue |
| Plattform-Flags | CLI-Argumente (`--pub-*`) + `ignore_*` | Query-Parameter (`publish_*`) + `ignore_*` |
| Beste Eignung | Einzelner Host / Operator-Workflow | Externe Systeme und Remote-Auslösung |

---

<a id="project-structure"></a>
## Projektstruktur

Hohe Übersicht über Source-/Runtime-Layout:

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
├── videos/                   # Runtime-Eingabeartefakte
├── logs/, logs-autopub/      # Runtime-Logs
├── temp/, temp_screenshot/   # temporäre Runtime-Artefakte
├── videos_db.csv
└── processed.csv
```

<a id="repository-layout"></a>
## Repository-Layout

Note: `transcription_data/` wird während der Laufzeit von Verarbeitungs-/Veröffentlichungsfluss genutzt und kann erst nach Ausführung erscheinen.

| Pfad | Zweck |
| --- | --- |
| `app.py` | Tornado-Service mit `/publish` und `/publish/queue`, inkl. interner Publish-Queue und Worker-Thread. |
| `autopub.py` | CLI-Watcher: scannt `videos/`, verarbeitet neue Dateien und ruft Publisher parallel auf. |
| `process_video.py` | Lädt Videos an das Processing-Backend hoch und speichert zurückgegebene ZIP-Bundles. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | Selenium-Automatisierungsmodule pro Plattform. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | Session-Prüfungen und QR-Login-Flows. |
| `utils.py` | Gemeinsame Hilfsfunktionen (Fensterfokus, QR/Mail-Utilities, Diagnose-Helfer). |
| `load_env.py` | Lädt Umgebungsvariablen aus dem Shell-Profil (`~/.bashrc`) und maskiert sensible Logs. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | SMTP/SendGrid-Helfer und Testskripte. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Captcha-Solver-Integrationen. |
| `scripts/` | Service-Setup und Betriebs-Skripte (Raspberry Pi/Linux + Legacy-Automation). |
| `pwa/` | Statische PWA für ZIP-Vorschau und Publish-Submit. |
| `setup_raspberrypi.md` | Schritt-für-Schritt-Anleitung für Raspberry-Pi-Provisioning. |
| `.env.example` | Vorlage für Umgebungsvariablen (Credentials, Pfade, Captcha-Keys). |
| `.github/FUNDING.yml` | Sponsor-/Funding-Konfiguration. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | Runtime-Artefakte und Logs (meist in `.gitignore`). |

---

<a id="prerequisites"></a>
## Voraussetzungen

🧰 **Installiere diese Komponenten vor dem ersten Lauf**.

### Betriebssystem und Tools

- Linux-Desktop/Server mit einer X-Session (`DISPLAY=:1` ist in den bereitgestellten Skripten üblich).
- Chromium/Chrome und passender ChromeDriver.
- GUI-/Media-Helfer: `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv oder Conda).

### Python-Abhängigkeiten

Minimaler Runtime-Satz:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

Repository-Install:

```bash
python -m pip install -r requirements.txt
```

Für leichte Service-Installationen (standardmäßig von Setup-Skripten verwendet):

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` enthält:
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Optional: Sudo-Benutzer anlegen

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

<a id="installation"></a>
## Installation

🚀 **Einrichtung von einem sauberen Rechner**:

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
# Werte in .env eintragen (nicht committen)
```

4. Variablen für Skripte laden, die Shell-Profile lesen:

```bash
source ~/.bashrc
python load_env.py
```

Hinweis: `load_env.py` ist auf `~/.bashrc` ausgelegt; bei anderem Shell-Profil entsprechend anpassen.

---

<a id="configuration"></a>
## Konfiguration

🔐 **Erst Credentials setzen, dann hostspezifische Pfade prüfen**.

### Umgebungsvariablen

Das Projekt erwartet Credentials und optionale Browser-/Laufzeitpfade aus Umgebungsvariablen. Starte mit `.env.example`:

| Variable | Beschreibung |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | SMTP-Credentials für QR-/Login-Benachrichtigungen. |
| `SENDGRID_API_KEY` | SendGrid-Key für Email-Flows, die SendGrid-APIs verwenden. |
| `APIKEY_2CAPTCHA` | 2Captcha-API-Key. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Turing-Captcha-Credentials. |
| `DOUYIN_LOGIN_PASSWORD` | Zweitverifikation-Helfer für Douyin. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Instagram-/Browser-Driver-Overrides. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | Bevorzugte globale Browser/Driver/Display-Overrides in `app.py`. |

### Pfadkonstanten (wichtig)

📌 **Häufigstes Startproblem**: nicht aufgelöste hartcodierte absolute Pfade.

Mehrere Module enthalten noch hartcodierte Pfade. Passe sie für deinen Host an:

| Datei | Konstanten | Bedeutung |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | API-Service-Wurzeln und Backend-Endpunkte. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | CLI-Watcher-Wurzeln und Backend-Endpunkte. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Absolute Pfade zu Python/Conda/Repo/Logs. | Legacy/macOS-orientierte Wrapper. |
| `utils.py` | FFmpeg-Pfadannahmen in den Cover-Verarbeitungs-Helfern. | Kompatibilität der Medienwerkzeug-Pfade. |

Wichtiger Repository-Hinweis:
- Der aktuelle Repository-Pfad in diesem Workspace ist `/home/lachlan/ProjectsLFS/AutoPublish`.
- Teile des Codes und Skripte referenzieren noch `/home/lachlan/Projects/auto-publish` oder `/Users/lachlan/...`.
- Halte diese Pfade lokal konsistent vor Produktionseinsatz.

### Plattform-Schalter mit `ignore_*`

🧩 **Schneller Sicherheits-Schalter**: Das Anlegen einer `ignore_*`-Datei deaktiviert den jeweiligen Publisher ohne Codeänderung.

Publishing-Flags sind ebenfalls über Ignore-Dateien gesteuert. Lege leere Dateien an, um eine Plattform zu deaktivieren:

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

Lösche die entsprechende Datei wieder, um erneut zu aktivieren.

### <a id="configuration-verification-checklist"></a>Konfigurations-Checkliste

Führe diese schnelle Validierung nach dem Setzen von `.env` und Pfadkonstanten aus:

```bash
python -c "import os;print('AUTOPUBLISH_BROWSER_BIN=', os.getenv('AUTOPUBLISH_BROWSER_BIN'));print('AUTOPUBLISH_CHROMEDRIVER=', os.getenv('AUTOPUBLISH_CHROMEDRIVER'));print('DISPLAY=', os.getenv('DISPLAY') or os.getenv('AUTOPUBLISH_DISPLAY'))"
python -c "from load_env import load_env_from_bashrc; load_env_from_bashrc(); print('Environment load OK')"
python -c "import os; p=os.getenv('AUTOPUBLISH_CHROMEDRIVER') or os.getenv('CHROMEDRIVER_PATH') or '/usr/bin/chromedriver'; print(p, 'exists=', os.path.exists(p))"
```

Wenn Werte fehlen, aktualisiere `.env`, `~/.bashrc` oder die Skript-Konstanten vor dem Start der Publisher.

---

<a id="preparing-browser-sessions"></a>
## Browser-Sitzungen vorbereiten

🌐 **Session-Persistenz ist Pflicht** für zuverlässige Selenium-Veröffentlichung.

1. Lege dedizierte Profilordner an:

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. Starte Browser-Sessions mit Remote-Debugging (Beispiel für XiaoHongShu):

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. Melde dich einmal manuell für jede Plattform/Profil an.

4. Prüfe, ob Selenium sich verbinden kann:

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Sicherheitshinweis:
- `app.py` enthält aktuell einen hartcodierten Sudo-Passwort-Platzhalter (`password = "1"`) in der Browser-Neustartlogik. Ersetze diesen vor echtem Deployment.

---

<a id="usage"></a>
## Nutzung

▶️ **Zwei Betriebsmodi sind verfügbar**: CLI-Watcher und API-Queue-Service.

### Running the CLI pipeline (`autopub.py`)

1. Lege Quellvideos in das Watch-Verzeichnis (`videos/` oder `autopublish_folder_path` in deiner Konfiguration).
2. Starte:

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Flags:

| Flag | Bedeutung |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Beschränkt Veröffentlichung auf ausgewählte Plattformen. Wenn keines angegeben ist, sind standardmäßig diese drei aktiv. |
| `--test` | Testmodus, wird an Publisher übergeben (Verhalten je Plattformmodul unterschiedlich). |
| `--use-cache` | Wiederverwendung vorhandener `transcription_data/<video>/<video>.zip`, falls vorhanden. |

CLI-Fluss pro Video:
- Upload/Verarbeitung über `process_video.py`.
- ZIP nach `transcription_data/<video>/` entpacken.
- Starten der gewählten Publisher über `ThreadPoolExecutor`.
- Tracking-Status in `videos_db.csv` und `processed.csv` anhängen.

### Running the Tornado service (`app.py`)

🛰️ **Der API-Modus** ist nützlich für externe Systeme, die ZIP-Bundles erzeugen.

Server starten:

```bash
python app.py --refresh-time 1800 --port 8081
```

API-Endpunkte:

| Endpoint | Methode | Zweck |
| --- | --- | --- |
| `/publish` | `POST` | ZIP bytes hochladen und einen Publish-Job enqueuen |
| `/publish/queue` | `GET` | Queue, Job-Verlauf und Publish-Status einsehen |

### `POST /publish`

📤 **Einen Publish-Job enqueuen**, indem du ZIP-Bytes direkt hochlädst.

- Header: `Content-Type: application/octet-stream`
- Erforderliches Query-/Form-Argument: `filename` (ZIP-Dateiname)
- Optionale Booleans: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: rohe ZIP-Bytes

Beispiel:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

Aktuelles Verhalten laut Code:
- Anfrage wird angenommen und in die Queue gelegt.
- Die Sofortantwort liefert JSON mit `status: queued`, `job_id` und `queue_size`.
- Worker-Thread verarbeitet Jobs seriell.

### `GET /publish/queue`

📊 **Queue-Gesundheit und in-flight Jobs beobachten**.

Liefert Status-/Historien-JSON:

```bash
curl "http://localhost:8081/publish/queue"
```

Rückgabefelder enthalten:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Browser-Refresh-Thread

♻️ Periodisches Erneuern des Browsers reduziert Session-Fehler über lange Laufzeiten.

`app.py` startet einen Hintergrund-Refresh-Thread mit dem Intervall `--refresh-time` und nutzt Prüfungen im Login. Der Refresh-Sleep enthält zufällige Verzögerung.

### PWA-Frontend (`pwa/`)

🖥️ Schlanke statische UI für manuelle ZIP-Uploads und Queue-Ansicht.

PWA lokal starten:

```bash
cd pwa
python -m http.server 5173
```

Öffne `http://localhost:5173` und setze die Backend-Basis-URL (z. B. `http://lazyingart:8081`).

PWA-Fähigkeiten:
- Drag-and-drop ZIP-Vorschau.
- Zielplattform-Umschalter + Testmodus.
- Sendet an `/publish` und pollt `/publish/queue`.

### Command Palette

🧷 **Am häufigsten verwendete Befehle an einem Ort**.

| Aufgabe | Befehl |
| --- | --- |
| Alle Abhängigkeiten installieren | `python -m pip install -r requirements.txt` |
| Leichte Laufzeitabhängigkeiten installieren | `python -m pip install -r requirements.autopub.txt` |
| Shell-basierte Env-Variablen laden | `source ~/.bashrc && python load_env.py` |
| API-Queue-Server starten | `python app.py --refresh-time 1800 --port 8081` |
| CLI-Watcher-Pipeline starten | `python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili` |
| ZIP in Queue einreichen | `curl -X POST "http://localhost:8081/publish?filename=demo.zip" --data-binary @demo.zip -H "Content-Type: application/octet-stream"` |
| Queue-Status prüfen | `curl -s "http://localhost:8081/publish/queue"` |
| Lokale PWA bereitstellen | `cd pwa && python -m http.server 5173` |

---

<a id="examples"></a>
## Beispiele

🧪 **Copy/Paste Smoke-Test-Befehle**:

### Beispiel 0: Umgebung laden und API-Server starten

```bash
source ~/.bashrc
python load_env.py
python app.py --refresh-time 1800 --port 8081
```

### Beispiel A: CLI-Publish-Lauf

```bash
python autopub.py --pub-xhs --pub-douyin --use-cache
```

### Beispiel B: API-Publish-Lauf (ein einzelnes ZIP)

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

📦 **Das ZIP-Format ist entscheidend**: Dateinamen und Metadaten-Keys müssen zu den Publisher-Erwartungen passen.

Erwartete ZIP-Inhalte (Minimum):

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` steuert CN-Publisher; optional `metadata["english_version"]` wird vom YouTube-Publisher genutzt.

Felder, die typischerweise von Modulen verwendet werden:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (Liste von Hashtags)
- `video_filename`, `cover_filename`
- plattformspezifische Felder wie in den jeweiligen `pub_*.py` implementiert

Wenn du ZIPs extern erzeugst, halte Keys und Dateinamen mit den Modulerwartungen konsistent.

<a id="data--artifact-lifecycle"></a>
## Daten- und Artefakt-Lebenszyklus

Die Pipeline erstellt lokale Artefakte, die Operatoren gezielt behalten, rotieren oder bereinigen sollten:

| Artefakt | Ort | Erzeugt von | Warum wichtig |
| --- | --- | --- | --- |
| Eingabevideos | `videos/` | Manuelles Ablegen oder Upstream-Sync | Quell-Medien für den CLI-Watcher-Modus |
| Processing-ZIP-Output | `transcription_data/<stem>/<stem>.zip` | `process_video.py` | Wiederverwendbare Payload für `--use-cache` |
| Extrahierte Publish-Assets | `transcription_data/<stem>/...` | ZIP-Extraktion in `autopub.py` / `app.py` | Publisher-bereite Dateien und Metadaten |
| Publish-Logs | `logs/`, `logs-autopub/` | CLI/API-Runtime | Fehleranalyse und Audit-Trail |
| Browser-Logs | `~/chromium_dev_session_logs/*.log` (oder Chrome-Präfix) | Browser-Startskripte | Session-/Port-/Startup-Probleme diagnostizieren |
| Tracking-CSVs | `videos_db.csv`, `processed.csv` | CLI-Watcher | Verarbeitet doppelte Dateien |

Empfehlung zur Bereinigung:
- Ergänze einen regelmäßigen Cleanup-/Archiv-Job für alte `transcription_data/`, `temp/` und alte Logs, um Speicherdruck zu vermeiden.

<a id="platform-specific-notes"></a>
## Plattform-spezifische Hinweise

🧭 **Port-Matrix + Modulverantwortung** pro Publisher.

| Plattform | Port | Modul(e) | Hinweise |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | QR-Re-Login-Fluss; Titel-Normalisierung und Hashtag-Nutzung aus Metadaten. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Upload-Abschlussprüfungen und Retry-Pfade sind plattformsensitiv; Logs eng überwachen. |
| Bilibili | 5005 | `pub_bilibili.py` | Captcha-Hooks über `solve_captcha_2captcha.py` und `solve_captcha_turing.py` verfügbar. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Schnelle QR-Freigabe ist wichtig für verlässliche Session-Erneuerung. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | Steuerung im API-Modus mit `publish_instagram=true`; Env-Variablen in `.env.example`. |
| YouTube | 9222 | `pub_y2b.py` | Nutzt `english_version`-Metadatenblock; Deaktivierung über `ignore_y2b`. |

<a id="raspberry-pi--linux-service-setup"></a>
## Raspberry Pi / Linux Service Setup

🐧 **Empfohlen für 24/7-Hosts**.

Für einen kompletten Host-Bootstrap folge [`setup_raspberrypi.md`](setup_raspberrypi.md).

Schneller Setup-Flow:

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

Starte den Service manuell in tmux:

```bash
./scripts/start_autopub_tmux.sh
```

Dienste/Ports prüfen:

```bash
systemctl status autopub.service autopub-vnc.service
sudo ss -ltnp | grep 590
```

Kompatibilitätshinweis:
- Einige ältere Dokumente/Skripte referenzieren noch `virtual-desktop.service`; aktuelle Setup-Skripte installieren `autopub-vnc.service`.

<a id="legacy-macos-scripts"></a>
## Legacy macOS-Skripte

🍎 Legacy-Wrapper bleiben zur Kompatibilität mit älteren lokalen Setups erhalten.

Das Repository enthält weiterhin macOS-orientierte Legacy-Wrapper:
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

Diese enthalten absolute `/Users/lachlan/...`-Pfade und Conda-Annahmen. Behalte sie, wenn du diesen Workflow nutzt, aber passe Pfade/venv/Tools für deinen Host an.

<a id="troubleshooting--maintenance"></a>
## Fehlerbehebung & Wartung

🛠️ **Wenn etwas schiefgeht, beginne hier**.

- **Pfadabweichungen zwischen Hosts**: Wenn Fehler auf fehlende Dateien unter `/Users/lachlan/...` oder `/home/lachlan/Projects/auto-publish` verweisen, passe Konstanten auf deinen Hostpfad an (`/home/lachlan/ProjectsLFS/AutoPublish` in diesem Workspace).
- **Secrets-Hygiene**: `~/.local/bin/detect-secrets scan` vor dem Push ausführen. Leakefaktoren Credentials rotieren.
- **Fehler im Processing-Backend**: Wenn `process_video.py` „Failed to get the uploaded file path“ meldet, prüfe, ob die Upload-Antwort JSON das Feld `file_path` enthält und der Processing-Endpunkt ZIP-Bytes liefert.
- **ChromeDriver-Mismatch**: Bei DevTools-Verbindungsfehlern auf passende Chrome/Chromium- und Treiber-Versionen (oder `webdriver-manager`) achten.
- **Browser-Fokus-Probleme**: `bring_to_front` basiert auf Fenstertitel-Übereinstimmung (Namensunterschiede von Chromium/Chrome können das brechen).
- **Captcha-Unterbrechungen**: Konfiguriere 2Captcha/Turing und integriere Solver-Ausgaben bei Bedarf.
- **Veraltete Lock-Dateien**: Wenn geplante Läufe nie starten, prüfe den Prozesszustand und entferne altes `autopub.lock` (Legacy-Skriptpfad).
- **Zu prüfende Logs**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log` plus Service-Journal-Logs.

<a id="faq"></a>
## FAQ

**F: Kann ich API-Modus und CLI-Watcher-Modus gleichzeitig betreiben?**  
A: Ja, ist aber nicht empfohlen, solange Inputs und Browser-Sessions nicht strikt getrennt sind. Beide Modi können dieselben Publisher, Dateien und Ports konkurrenz nutzen.

**F: Warum liefert `/publish` `queued`, aber noch nichts ist veröffentlicht?**  
A: `app.py` enqueuet zuerst und ein Hintergrund-Worker verarbeitet Jobs seriell. Prüfe `/publish/queue`, `is_publishing` und Service-Logs.

**F: Benötige ich `load_env.py`, wenn ich bereits `.env` nutze?**  
A: `start_autopub_tmux.sh` liest `.env` falls vorhanden, während einige direkte Läufe auf Shell-Environment angewiesen sind. `.env` und Shell-Exports konsistent zu halten vermeidet Überraschungen.

**F: Was ist das minimale ZIP-Format für API-Uploads?**  
A: Ein gültiges ZIP mit `{stem}_metadata.json` sowie Video- und Cover-Dateiname, die zu den Metadaten-Keys (`video_filename`, `cover_filename`) passen.

**F: Wird der Headless-Modus unterstützt?**  
A: Einige Module exponieren Headless-bezogene Variablen, aber der dokumentierte Hauptbetrieb ist GUI-gestützt mit persistenten Profilen.

<a id="extending-the-system"></a>
## Das System erweitern

🧱 **Erweiterungspunkte** für neue Plattformen und sicherere Abläufe.

- **Neue Plattform hinzufügen**: Kopiere ein `pub_*.py`-Modul, passe Selektoren/Flows an, ergänze `login_*.py` bei Bedarf für QR-Neu-Authentifizierung und verdrahte Flags/Queue-Verarbeitung in `app.py` sowie CLI-Anbindung in `autopub.py`.
- **Konfigurationsabstraktion**: Migriere verstreute Konstanten zu strukturierter Konfiguration (`config.yaml`/`.env` + typisiertes Modell) für Multi-Host-Betrieb.
- **Schutz der Zugangsdaten**: Ersetze hartcodierte oder shell-exponierte sensible Pfade durch sichere Geheimnisverwaltung (`sudo -A`, Keychain, Vault/Secret Manager).
- **Containerisierung**: Packe Chromium/ChromeDriver + Python-Runtime + virtuellen Display in eine deploybare Einheit für Cloud/Server.

<a id="quick-start-checklist"></a>
## Schnellstart-Checkliste

✅ **Minimaler Weg zum ersten erfolgreichen Publish**.

1. Repository klonen und Abhängigkeiten installieren (`pip install -r requirements.txt` oder `requirements.autopub.txt` für minimalen Satz).
2. Harte Pfadkonstanten in `app.py`, `autopub.py` und allen ausgeführten Skripten anpassen.
3. Erforderliche Credentials im Shell-Profil oder `.env` exportieren; `python load_env.py` zur Ladeprüfung ausführen.
4. Profile für Remote-Debug-Browser anlegen und jede benötigte Plattform-Session einmal starten.
5. Dich auf jeder Zielplattform manuell anmelden.
6. Entweder API-Modus (`python app.py --port 8081`) oder CLI-Modus (`python autopub.py --use-cache ...`) starten.
7. Eine Beispiel-ZIP (API-Modus) oder eine Beispielvideodatei (CLI-Modus) einreichen und `logs/` prüfen.
8. Secrets-Scan vor jedem Push ausführen.

<a id="development-notes"></a>
## Entwicklungshinweise

🧬 **Aktueller Entwicklungsstand** (manuelle Formatierung + Smoke-Tests).

- Python-Style folgt bestehender 4-Space-Einrückung und manueller Formatierung.
- Derzeit keine formelle automatisierte Test-Suite; rely auf Smoke-Tests:
  - Prozessiere ein Beispielvideo über `autopub.py`.
  - Sende ein ZIP an `/publish` und beobachte `/publish/queue`.
  - Validiere jeden Zielkanal manuell.
- Ergänze einen kleinen `if __name__ == "__main__":`-Einstiegspunkt, wenn neue Skripte hinzugefügt werden, für schnelle Trockenläufe.
- Halte Plattformänderungen so weit wie möglich isoliert (`pub_*`, `login_*`, `ignore_*`-Schalter).
- Runtime-Artefakte (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) sind lokal zu halten und oft in `.gitignore`.

<a id="roadmap"></a>
## Roadmap

🗺️ **Prioritäre Verbesserungen im aktuellen Code-Umfeld**.

Geplante/wünschenswerte Verbesserungen (basierend auf aktueller Code-Struktur und vorhandenen Notizen):

1. Zersplitterte hartcodierte Pfade durch zentrale Konfiguration ersetzen (`.env`/YAML + typisierte Modelle).
2. Harte Sudo-Passwort-Muster entfernen und Prozesssteuerung auf sicherere Mechanismen umstellen.
3. Veröffentlichungsstabilität mit robusteren Retries und besserer UI-Zustands-Erkennung pro Plattform verbessern.
4. Plattformunterstützung erweitern (z. B. Kuaishou oder weitere Creator-Plattformen).
5. Runtime in reproduzierbare Deployment-Einheiten packen (Container + virtueller Display-Profile).
6. Automatisierte Integrationsprüfungen für ZIP-Vertrag und Queue-Ausführung ergänzen.

<a id="contributing"></a>
## Mitwirken

🤝 Halte PRs fokussiert, reproduzierbar und explizit bezüglich Laufzeitannahmen.

Beiträge sind willkommen.

1. Forke das Repo und lege einen fokussierten Branch an.
2. Halte Commits klein und im Imperativ (Beispielstil aus Historie: „Wait for YouTube checks before publishing“).
3. Füge manuelle Verifikationshinweise in PRs hinzu:
   - Laufzeitannahmen,
   - Browser-/Session-Neustarts,
   - relevante Logs/Screenshots für Änderungen im UI-Flow.
4. Niemals echte Secrets committen (`.env` wird ignoriert; nutze `.env.example` nur als Formvorgabe).

Wenn du neue Publisher-Module einführst, verdrahte mindestens:
- `pub_<platform>.py`
- optional `login_<platform>.py`
- API-Flags und Queue-Behandlung in `app.py`
- CLI-Anbindung in `autopub.py` (falls nötig)
- `ignore_<platform>`-Toggle-Handling
- README-Updates

<a id="security--ops-checklist"></a>
## Sicherheits- & Ops-Checkliste

Vor jedem produktionsnahen Lauf:

1. Sicherstellen, dass `.env` lokal existiert und nicht in git getrackt ist.
2. Bereinigte oder historisch geleakte Credentials rotieren/entfernen.
3. Platzhalter für sensible Werte im Code ersetzen (z. B. Sudo-Passwort-Platzhalter in `app.py`).
4. Vor Batch-Läufen Absicht der `ignore_*`-Schalter prüfen.
5. Browser-Profile pro Plattform isoliert halten und Accounts mit geringstmöglichen Rechten nutzen.
6. Sicherstellen, dass Logs vor dem Teilen von Issue-Reports keine Secrets enthalten.
7. `detect-secrets` (oder Äquivalent) vor Push ausführen.

<a id="support-autopublish"></a>
## Lizenz

In diesem Repository-Snapshot liegt derzeit keine `LICENSE`-Datei vor.

Annahmen für diesen Entwurf:
- Die Nutzung und Weiterverbreitung bleiben bis zum Hinzufügen einer expliziten Lizenzdatei durch den Maintainer offen.

Empfohlene nächste Aktion:
- Ergänze eine `LICENSE` im Repository-Root (zum Beispiel MIT/Apache-2.0/GPL-3.0) und aktualisiere diesen Abschnitt entsprechend.

> 📝 Solange keine Lizenzdatei vorhanden ist, gelten kommerzielle/interne Weiterverbreitungsszenarien als unbestimmt und sollten direkt mit dem Maintainer geklärt werden.

---

<a id="acknowledgements"></a>
## Danksagung

- Maintainer- und Sponsorprofil: [@lachlanchen](https://github.com/lachlanchen)
- Herkunft der Finanzierungs-Konfiguration: [`.github/FUNDING.yml`](.github/FUNDING.yml)
- In diesem Repo genutzte Ökosystem-Dienste: Selenium, Tornado, SendGrid, 2Captcha, Turing-Captcha-APIs.


## ❤️ Support

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://camo.githubusercontent.com/24a4914f0b42c6f435f9e101621f1e52535b02c225764b2f6cc99416926004b7/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f446f6e6174652d4c617a79696e674172742d3045413545393f7374796c653d666f722d7468652d6261646765266c6f676f3d6b6f2d6669266c6f676f436f6c6f723d7768697465)](https://chat.lazying.art/donate) | [![PayPal](https://camo.githubusercontent.com/d0f57e8b016517a4b06961b24d0ca87d62fdba16e18bbdb6aba28e978dc0ea21/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f50617950616c2d526f6e677a686f754368656e2d3030343537433f7374796c653d666f722d7468652d6261646765266c6f676f3d70617970616c266c6f676f436f6c6f723d7768697465)](https://paypal.me/RongzhouChen) | [![Stripe](https://camo.githubusercontent.com/1152dfe04b6943afe3a8d2953676749603fb9f95e24088c92c97a01a897b4942/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f5374726970652d446f6e6174652d3633354246463f7374796c653d666f722d7468652d6261646765266c6f676f3d737472697065266c6f676f436f6c6f723d7768697465)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |
