[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish

> 🌍 **État de la localisation (vérifié dans cet espace de travail le 28 février 2026) :**
> `i18n/` contient actuellement `README.ar.md`, `README.es.md` et ce fichier `README.fr.md` ; les autres fichiers listés dans la barre de langues sont des cibles prévues/à synchroniser selon l’avancement.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#prerequisites)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#system-overview)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#running-the-tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#platform-specific-notes)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#running-the-tornado-service-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Arabic%20%7C%20Spanish-0EA5E9)](#table-of-contents)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#license)

Boîte à outils d’automatisation pour distribuer des vidéos courtes sur plusieurs plateformes de créateurs chinoises et internationales. Le projet combine un service Tornado, des bots Selenium, et un workflow local de surveillance de fichiers : déposer une vidéo dans un dossier peut aboutir à une publication sur XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), Instagram, et éventuellement YouTube.

Le dépôt est volontairement bas niveau : la majorité de la configuration vit dans des fichiers Python et des scripts shell. Ce document sert de manuel opérationnel pour l’installation, l’exécution et les points d’extension.

> ⚙️ **Philosophie opérationnelle** : le projet privilégie des scripts explicites et l’automatisation directe du navigateur plutôt que des couches d’abstraction cachées.
> ✅ **Politique canonique pour ce README** : conserver la granularité technique, puis améliorer la lisibilité et la découvrabilité.

## Commencer ici

Si vous découvrez ce dépôt, suivez cet ordre :

1. Lire [Prérequis](#prerequisites) et [Installation](#installation).
2. Configurer les secrets et chemins absolus dans [Configuration](#configuration).
3. Préparer les sessions de debug navigateur dans [Préparation des sessions navigateur](#preparing-browser-sessions).
4. Choisir un mode d’exécution dans [Utilisation](#usage) : `autopub.py` (watcher) ou `app.py` (file API).
5. Valider avec les commandes de [Exemples](#examples).

## Vue d’ensemble

AutoPublish prend actuellement en charge deux modes d’exécution en production :

1. **Mode watcher CLI (`autopub.py`)** pour l’ingestion par dossier et la publication.
2. **Mode file API (`app.py`)** pour la publication de ZIP via HTTP (`/publish`, `/publish/queue`).

Il est conçu pour les opérateurs qui préfèrent des workflows transparents orientés scripts plutôt que des plateformes d’orchestration abstraites.

### Modes d’exécution en un coup d’œil

| Mode | Point d’entrée | Entrée | Idéal pour | Comportement en sortie |
| --- | --- | --- | --- | --- |
| Watcher CLI | `autopub.py` | Fichiers déposés dans `videos/` | Workflows opérateur locaux et boucles cron/service | Traite les vidéos détectées et publie immédiatement sur les plateformes sélectionnées |
| Service de file API | `app.py` | Upload ZIP vers `POST /publish` | Intégration avec systèmes amont et déclenchement distant | Accepte les jobs, les place en file, puis publie dans l’ordre du worker |

## Résumé rapide

| Élément | Valeur |
| --- | --- |
| Langage principal | Python 3.10+ |
| Runtimes principaux | Watcher CLI (`autopub.py`) + service Tornado en file (`app.py`) |
| Moteur d’automatisation | Selenium + sessions Chromium en remote-debug |
| Formats d’entrée | Vidéos brutes (`videos/`) et bundles ZIP (`/publish`) |
| Chemin courant du dépôt | `/home/lachlan/ProjectsLFS/AutoPublish` |
| Utilisateurs cibles | Créateurs/ingénieurs ops gérant des pipelines vidéo multi-plateformes |

### Instantané sécurité opérationnelle

| Sujet | État actuel | Action |
| --- | --- | --- |
| Chemins codés en dur | Présents dans plusieurs modules/scripts | Mettre à jour les constantes de chemin selon l’hôte avant toute exécution production |
| État de connexion navigateur | Requis | Conserver des profils remote-debug persistants par plateforme |
| Gestion captcha | Intégrations optionnelles disponibles | Configurer les identifiants 2Captcha/Turing si nécessaire |
| Déclaration de licence | Aucun fichier `LICENSE` à la racine détecté | Confirmer les conditions d’utilisation avec le mainteneur avant redistribution |

---

## Table of Contents

- [Vue d’ensemble](#vue-densemble)
- [System Overview](#system-overview)
- [Fonctionnalités](#fonctionnalités)
- [Structure du projet](#structure-du-projet)
- [Organisation du dépôt](#organisation-du-dépôt)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Preparing Browser Sessions](#preparing-browser-sessions)
- [Usage](#usage)
- [Examples](#examples)
- [Métadonnées & format ZIP](#métadonnées--format-zip)
- [Platform-Specific Notes](#platform-specific-notes)
- [Configuration de service Raspberry Pi / Linux](#configuration-de-service-raspberry-pi--linux)
- [Scripts macOS hérités](#scripts-macos-hérités)
- [Dépannage & maintenance](#dépannage--maintenance)
- [Extension du système](#extension-du-système)
- [Checklist de démarrage rapide](#checklist-de-démarrage-rapide)
- [Notes de développement](#notes-de-développement)
- [Feuille de route](#feuille-de-route)
- [Contribuer](#contribuer)
- [License](#license)
- [Remerciements](#remerciements)
- [Soutenir AutoPublish](#soutenir-autopublish)

---

<a id="system-overview"></a>
## System Overview

🎯 **Flux de bout en bout** depuis le média brut jusqu’à la publication :

Vue rapide du workflow :

1. **Ingestion des vidéos brutes** : placez une vidéo dans `videos/`. Le watcher (`autopub.py` ou un scheduler/service) détecte les nouveaux fichiers via `videos_db.csv` et `processed.csv`.
2. **Génération des assets** : `process_video.VideoProcessor` envoie le fichier vers un serveur de traitement (`upload_url` et `process_url`) qui renvoie un ZIP contenant :
   - la vidéo éditée/encodée (`<stem>.mp4`),
   - une image de couverture,
   - `{stem}_metadata.json` avec titres localisés, descriptions, tags, etc.
3. **Publication** : les métadonnées pilotent les publishers Selenium de `pub_*.py`. Chaque publisher s’attache à une instance Chromium/Chrome déjà démarrée via port remote-debug et profil utilisateur persistant.
4. **Plan de contrôle web (optionnel)** : `app.py` expose `/publish`, accepte des ZIP déjà construits, les extrait et met les jobs en file vers les mêmes publishers. Il peut aussi rafraîchir les sessions navigateur et déclencher les helpers de login (`login_*.py`).
5. **Modules de support** : `load_env.py` hydrate les secrets depuis `~/.bashrc`, `utils.py` fournit des helpers (focus fenêtre, QR, utilitaires mail), et `solve_captcha_*.py` intègre Turing/2Captcha quand des captchas apparaissent.

## Fonctionnalités

✨ **Conçu pour une automatisation pragmatique orientée scripts** :

- Publication multi-plateformes : XiaoHongShu, Douyin, Bilibili, ShiPinHao (WeChat Channels), Instagram, YouTube (optionnel).
- Deux modes d’exploitation : pipeline watcher CLI (`autopub.py`) et service API en file (`app.py` + `/publish` + `/publish/queue`).
- Désactivation temporaire par plateforme via les fichiers `ignore_*`.
- Réutilisation des sessions navigateur remote-debug avec profils persistants.
- Automatisation QR/captcha et helpers de notification email en option.
- Aucune build frontend requise pour l’UI uploader PWA incluse (`pwa/`).
- Scripts Linux/Raspberry Pi pour le setup de service (`scripts/`).

### Matrice des fonctionnalités

| Capacité | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Source d’entrée | Watcher local `videos/` | ZIP uploadé via `POST /publish` |
| Mise en file | Progression interne basée fichiers | File de jobs explicite en mémoire |
| Flags plateforme | Arguments CLI (`--pub-*`) + `ignore_*` | Paramètres query (`publish_*`) + `ignore_*` |
| Cas d’usage idéal | Workflow opérateur sur un seul hôte | Systèmes externes et déclenchement distant |

---

## Structure du projet

Organisation haut niveau du code/runtime :

```text
AutoPublish/
├── README.md
├── app.py
├── autopub.py
├── process_video.py
├── load_env.py
├── utils.py
├── pub_*.py                  # publishers plateforme
├── login_*.py                # helpers login/session plateforme
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
├── i18n/                     # READMEs multilingues (inclut actuellement arabe, espagnol et français)
├── archived/
├── videos/                   # artefacts d’entrée runtime
├── logs/, logs-autopub/      # logs runtime
├── temp/, temp_screenshot/   # artefacts temporaires runtime
├── videos_db.csv
└── processed.csv
```

Note : `transcription_data/` est utilisé à l’exécution par le flux traitement/publication et peut apparaître après exécution.

## Organisation du dépôt

🗂️ **Modules clés et rôle de chacun** :

| Chemin | Rôle |
| --- | --- |
| `app.py` | Service Tornado exposant `/publish` et `/publish/queue`, avec file interne de publication et thread worker. |
| `autopub.py` | Watcher CLI : scanne `videos/`, traite les nouveaux fichiers et invoque les publishers en parallèle. |
| `process_video.py` | Upload des vidéos vers le backend de traitement et stockage des ZIP retournés. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | Modules d’automatisation Selenium par plateforme. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | Vérification de session et flux de login QR. |
| `utils.py` | Helpers d’automatisation partagés (focus fenêtre, utilitaires QR/mail, helpers de diagnostic). |
| `load_env.py` | Charge les variables d’environnement depuis le profil shell (`~/.bashrc`) et masque les logs sensibles. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | Helpers SMTP/SendGrid et scripts de test. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Intégrations de résolution captcha. |
| `scripts/` | Scripts d’opérations et setup service (Raspberry Pi/Linux + automation héritée). |
| `pwa/` | PWA statique pour prévisualiser un ZIP et soumettre une publication. |
| `setup_raspberrypi.md` | Guide pas à pas de provisionnement Raspberry Pi. |
| `.env.example` | Modèle de variables d’environnement (identifiants, chemins, clés captcha). |
| `.github/FUNDING.yml` | Configuration sponsor/financement. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | Artefacts runtime et logs (beaucoup sont gitignored). |

---

<a id="prerequisites"></a>
## Prerequisites

🧰 **À installer avant la première exécution.**

### Système d’exploitation et outils

- Linux desktop/serveur avec session X (`DISPLAY=:1` est courant dans les scripts fournis).
- Chromium/Chrome et ChromeDriver compatible.
- Outils GUI/média : `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (`venv` ou Conda).

### Dépendances Python

Jeu minimal runtime :

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

Parité avec le dépôt :

```bash
python -m pip install -r requirements.txt
```

Pour les installations service allégées (utilisées par défaut par les scripts de setup) :

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` contient :
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Optionnel : créer un utilisateur sudo

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## Installation

🚀 **Installation depuis une machine propre** :

1. Cloner le dépôt :

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. Créer et activer un environnement (exemple avec `venv`) :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. Préparer les variables d’environnement :

```bash
cp .env.example .env
# remplir les valeurs dans .env (ne pas commit)
```

4. Charger les variables pour les scripts qui lisent le profil shell :

```bash
source ~/.bashrc
python load_env.py
```

Note : `load_env.py` est conçu autour de `~/.bashrc`; si vous utilisez un autre profil shell, adaptez en conséquence.

---

## Configuration

🔐 **Configurer les identifiants, puis vérifier les chemins spécifiques à l’hôte.**

### Variables d’environnement

Le projet attend des identifiants et, optionnellement, des chemins navigateur/runtime via variables d’environnement. Commencez depuis `.env.example` :

| Variable | Description |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | Identifiants SMTP pour les notifications QR/login. |
| `SENDGRID_API_KEY` | Clé SendGrid pour les flux email utilisant les API SendGrid. |
| `APIKEY_2CAPTCHA` | Clé API 2Captcha. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Identifiants captcha Turing. |
| `DOUYIN_LOGIN_PASSWORD` | Helper de seconde vérification Douyin. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Overrides Instagram/driver navigateur. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | Overrides globaux navigateur/driver/display préférés dans `app.py`. |

### Constantes de chemin (important)

📌 **Problème de démarrage le plus fréquent** : chemins absolus codés en dur non résolus.

Plusieurs modules contiennent encore des chemins codés en dur. Mettez-les à jour pour votre hôte :

| Fichier | Constante(s) | Signification |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | Racines du service API et endpoints backend. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | Racines watcher CLI et endpoints backend. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Chemins absolus vers Python/Conda/dépôt/logs. | Wrappers hérités orientés macOS. |
| `utils.py` | Hypothèses de chemin FFmpeg dans les helpers de couverture. | Compatibilité des chemins outillage média. |

Note importante sur ce dépôt :
- Le chemin actuel du dépôt dans cet espace de travail est `/home/lachlan/ProjectsLFS/AutoPublish`.
- Une partie du code et des scripts référence encore `/home/lachlan/Projects/auto-publish` ou `/Users/lachlan/...`.
- Conservez et ajustez ces chemins localement avant toute utilisation en production.

### Toggles plateforme via `ignore_*`

🧩 **Interrupteur de sécurité rapide** : créer un fichier `ignore_*` désactive un publisher sans modifier le code.

Les flags de publication sont aussi pilotés par ces fichiers. Créez un fichier vide pour désactiver une plateforme :

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

Supprimez le fichier correspondant pour réactiver.

---

<a id="preparing-browser-sessions"></a>
## Preparing Browser Sessions

🌐 **La persistance de session est obligatoire** pour une publication Selenium fiable.

1. Créez des dossiers de profil dédiés :

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. Lancez des sessions navigateur en remote-debug (exemple XiaoHongShu) :

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. Connectez-vous manuellement une fois sur chaque plateforme/profil.

4. Vérifiez que Selenium peut s’attacher :

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Note sécurité :
- `app.py` contient actuellement un placeholder de mot de passe sudo codé en dur (`password = "1"`) utilisé par la logique de redémarrage navigateur. Remplacez-le avant un vrai déploiement.

---

<a id="usage"></a>
## Usage

▶️ **Deux modes d’exécution** sont disponibles : watcher CLI et service API en file.

### Exécuter le pipeline CLI (`autopub.py`)

1. Déposez les vidéos source dans le dossier surveillé (`videos/` ou `autopublish_folder_path` configuré).
2. Exécutez :

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Flags :

| Flag | Signification |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Limite la publication aux plateformes sélectionnées. Si aucun n’est passé, les trois sont activées par défaut. |
| `--test` | Mode test transmis aux publishers (comportement variable selon le module plateforme). |
| `--use-cache` | Réutilise `transcription_data/<video>/<video>.zip` si disponible. |

Flux CLI par vidéo :
- Upload/traitement via `process_video.py`.
- Extraction ZIP vers `transcription_data/<video>/`.
- Lancement des publishers sélectionnés via `ThreadPoolExecutor`.
- Ajout de l’état de suivi dans `videos_db.csv` et `processed.csv`.

<a id="running-the-tornado-service-apppy"></a>
### Exécuter le service Tornado (`app.py`)

🛰️ **Le mode API** est utile pour les systèmes externes qui produisent des bundles ZIP.

Démarrer le serveur :

```bash
python app.py --refresh-time 1800 --port 8081
```

Résumé des endpoints API :

| Endpoint | Méthode | Rôle |
| --- | --- | --- |
| `/publish` | `POST` | Upload des octets ZIP et mise en file d’un job de publication |
| `/publish/queue` | `GET` | Inspection de la file, de l’historique et de l’état de publication |

### `POST /publish`

📤 **Mettre un job en file** en envoyant directement les octets ZIP.

- Header : `Content-Type: application/octet-stream`
- Argument query/form requis : `filename` (nom du ZIP)
- Booléens optionnels : `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body : octets ZIP bruts

Exemple :

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

Comportement actuel dans le code :
- La requête est acceptée et mise en file.
- La réponse immédiate renvoie un JSON avec `status: queued`, `job_id` et `queue_size`.
- Un thread worker traite les jobs en série.

### `GET /publish/queue`

📊 **Observer la santé de la file et les jobs en cours**.

Renvoie un JSON d’état/historique de file :

```bash
curl "http://localhost:8081/publish/queue"
```

Les champs de réponse incluent :
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Thread de rafraîchissement navigateur

♻️ Le rafraîchissement périodique du navigateur réduit les échecs liés aux sessions obsolètes sur de longues durées.

`app.py` exécute un thread de refresh en arrière-plan avec l’intervalle `--refresh-time` et des hooks de vérification de login. Le sommeil du refresh inclut une temporisation aléatoire.

<a id="pwa-frontend-pwa"></a>
### Frontend PWA (`pwa/`)

🖥️ UI statique légère pour upload manuel de ZIP et inspection de la file.

Lancer l’UI statique en local :

```bash
cd pwa
python -m http.server 5173
```

Ouvrir `http://localhost:5173` puis définir l’URL de base backend (par exemple `http://lazyingart:8081`).

Capacités PWA :
- Prévisualisation ZIP en drag/drop.
- Toggles de cibles de publication + mode test.
- Soumission vers `/publish` et polling de `/publish/queue`.

---

<a id="examples"></a>
## Examples

🧪 **Commandes smoke-test prêtes à copier/coller** :

### Exemple 0 : charger l’environnement et démarrer le serveur API

```bash
source ~/.bashrc
python load_env.py
python app.py --refresh-time 1800 --port 8081
```

### Exemple A : exécution CLI de publication

```bash
python autopub.py --pub-xhs --pub-douyin --use-cache
```

### Exemple B : exécution API de publication (ZIP unique)

```bash
curl -X POST "http://localhost:8081/publish?filename=my_bundle.zip&publish_bilibili=true&test=true" \
  --data-binary @my_bundle.zip \
  -H "Content-Type: application/octet-stream"
```

### Exemple C : vérifier l’état de la file

```bash
curl -s "http://localhost:8081/publish/queue"
```

### Exemple D : smoke test helper SMTP

```bash
python smtp.py
python smtp_test_simple.py
```

---

## Métadonnées & format ZIP

📦 **Le contrat ZIP est important** : gardez les noms de fichiers et clés metadata alignés sur les attentes des publishers.

Contenu ZIP attendu (minimum) :

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` pilote les publishers CN ; `metadata["english_version"]` (optionnel) alimente le publisher YouTube.

Champs couramment utilisés par les modules :
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (liste de hashtags)
- `video_filename`, `cover_filename`
- champs spécifiques plateforme tels qu’implémentés dans chaque `pub_*.py`

Si vous générez des ZIP en externe, gardez les clés et les noms de fichiers conformes aux attentes des modules.

---

<a id="platform-specific-notes"></a>
## Platform-Specific Notes

🧭 **Carte des ports + ownership des modules** pour chaque publisher.

| Plateforme | Port | Module(s) | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | Flux de reconnexion QR ; sanitation du titre et usage des hashtags issus des métadonnées. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Les vérifications de fin d’upload et retries sont fragiles selon la plateforme ; surveiller les logs de près. |
| Bilibili | 5005 | `pub_bilibili.py` | Hooks captcha disponibles via `solve_captcha_2captcha.py` et `solve_captcha_turing.py`. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Validation QR rapide importante pour la fiabilité du refresh de session. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | Contrôlé en mode API avec `publish_instagram=true` ; variables d’environnement disponibles dans `.env.example`. |
| YouTube | 9222 | `pub_y2b.py` | Utilise le bloc metadata `english_version` ; désactivation via `ignore_y2b`. |

---

## Configuration de service Raspberry Pi / Linux

🐧 **Recommandé pour les hôtes toujours allumés**.

Pour un bootstrap complet de machine, suivre [`setup_raspberrypi.md`](setup_raspberrypi.md).

Setup pipeline rapide :

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

Cela orchestre :
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

Lancer le service manuellement dans tmux :

```bash
./scripts/start_autopub_tmux.sh
```

Valider services/ports :

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## Scripts macOS hérités

🍎 Des wrappers hérités restent disponibles pour compatibilité avec des setups locaux plus anciens.

Le dépôt contient encore des wrappers orientés macOS :
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

Ils incluent des chemins absolus `/Users/lachlan/...` et des hypothèses Conda. Conservez-les si vous utilisez encore ce workflow, mais mettez à jour chemins/venv/outillage pour votre hôte.

---

## Dépannage & maintenance

🛠️ **En cas d’échec, commencez ici.**

- **Dérive de chemins entre machines** : si des erreurs mentionnent des fichiers absents sous `/Users/lachlan/...` ou `/home/lachlan/Projects/auto-publish`, alignez les constantes sur le chemin de votre hôte (`/home/lachlan/ProjectsLFS/AutoPublish` dans cet espace de travail).
- **Hygiène des secrets** : exécutez `~/.local/bin/detect-secrets scan` avant push. Faites tourner toute clé divulguée.
- **Erreurs backend de traitement** : si `process_video.py` affiche “Failed to get the uploaded file path,” vérifiez que le JSON de réponse upload contient `file_path` et que l’endpoint de traitement renvoie bien des octets ZIP.
- **Incompatibilité ChromeDriver** : en cas d’erreur de connexion DevTools, alignez les versions Chrome/Chromium et driver (ou basculez sur `webdriver-manager`).
- **Problèmes de focus navigateur** : `bring_to_front` dépend de la correspondance du titre de fenêtre (les différences de nommage Chromium/Chrome peuvent casser le comportement).
- **Interruptions captcha** : configurez les identifiants 2Captcha/Turing et intégrez les sorties solver là où nécessaire.
- **Fichiers lock obsolètes** : si les exécutions planifiées ne démarrent jamais, vérifiez l’état des processus et supprimez `autopub.lock` obsolète (flux script hérité).
- **Logs à inspecter** : `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log`, et journaux systemd des services.

---

## Extension du système

🧱 **Points d’extension** pour de nouvelles plateformes et des opérations plus sûres.

- **Ajouter une nouvelle plateforme** : copier un module `pub_*.py`, adapter sélecteurs/flows, ajouter `login_*.py` si un réauth QR est nécessaire, puis câbler les flags et la gestion de file dans `app.py` et le câblage CLI dans `autopub.py`.
- **Abstraction de configuration** : migrer les constantes dispersées vers une config structurée (`config.yaml`/`.env` + modèle typé) pour l’exploitation multi-hôtes.
- **Durcissement du stockage des identifiants** : remplacer les flux sensibles codés en dur ou exposés dans le shell par une gestion secrète plus sûre (`sudo -A`, keychain, vault/secret manager).
- **Conteneurisation** : empaqueter Chromium/ChromeDriver + runtime Python + affichage virtuel dans une unité déployable unique pour usage cloud/serveur.

---

## Checklist de démarrage rapide

✅ **Chemin minimal vers une première publication réussie.**

1. Cloner ce dépôt et installer les dépendances (`pip install -r requirements.txt` ou version allégée `requirements.autopub.txt`).
2. Mettre à jour les constantes de chemin codées en dur dans `app.py`, `autopub.py`, et tout script que vous allez exécuter.
3. Exporter les identifiants requis dans votre profil shell ou `.env` ; exécuter `python load_env.py` pour valider le chargement.
4. Créer les dossiers de profil navigateur remote-debug et lancer chaque session plateforme requise au moins une fois.
5. Se connecter manuellement sur chaque plateforme cible dans son profil.
6. Démarrer soit le mode API (`python app.py --port 8081`), soit le mode CLI (`python autopub.py --use-cache ...`).
7. Soumettre un ZIP exemple (mode API) ou une vidéo exemple (mode CLI), puis inspecter `logs/`.
8. Exécuter un scan de secrets avant chaque push.

---

## Notes de développement

🧬 **Baseline de développement actuelle** (formatage manuel + smoke tests).

- Le style Python suit l’existant : indentation 4 espaces et formatage manuel.
- Pas de suite de tests automatisés formelle actuellement ; s’appuyer sur des smoke tests :
  - traiter une vidéo exemple via `autopub.py` ;
  - poster un ZIP sur `/publish` puis surveiller `/publish/queue` ;
  - valider manuellement chaque plateforme cible.
- Ajouter un petit point d’entrée `if __name__ == "__main__":` lors de l’ajout de nouveaux scripts pour faciliter les dry-runs.
- Isoler autant que possible les changements plateforme (`pub_*`, `login_*`, toggles `ignore_*`).
- Les artefacts runtime (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) sont attendus en local et majoritairement ignorés par git.

---

## Feuille de route

🗺️ **Améliorations prioritaires** reflétées par les contraintes actuelles du code.

Améliorations planifiées/souhaitées (selon la structure actuelle du code et les notes existantes) :

1. Remplacer les chemins codés en dur dispersés par une configuration centrale (`.env`/YAML + modèles typés).
2. Retirer les motifs de mot de passe sudo codé en dur et passer à des mécanismes de contrôle de processus plus sûrs.
3. Améliorer la fiabilité de publication avec des retries plus robustes et une meilleure détection d’état UI par plateforme.
4. Étendre le support plateforme (par exemple Kuaishou ou d’autres plateformes créateurs).
5. Emballer le runtime dans des unités de déploiement reproductibles (conteneur + profil d’affichage virtuel).
6. Ajouter des contrôles d’intégration automatisés pour le contrat ZIP et l’exécution de la file.

---

## Contribuer

🤝 Gardez les PR ciblées, reproductibles et explicites sur les hypothèses runtime.

Les contributions sont bienvenues.

1. Forker puis créer une branche ciblée.
2. Garder des commits petits et impératifs (style historique : “Wait for YouTube checks before publishing”).
3. Inclure des notes de vérification manuelle dans les PR :
   - hypothèses d’environnement,
   - redémarrages navigateur/session,
   - logs/captures d’écran pertinents pour les changements de flux UI.
4. Ne jamais commit de vrais secrets (`.env` est ignoré ; utiliser `.env.example` pour la structure uniquement).

Si vous introduisez de nouveaux modules publisher, câbler l’ensemble suivant :
- `pub_<platform>.py`
- `login_<platform>.py` optionnel
- flags API et gestion de file dans `app.py`
- câblage CLI dans `autopub.py` (si nécessaire)
- gestion du toggle `ignore_<platform>`
- mise à jour du README

---

<a id="license"></a>
## License

Aucun fichier `LICENSE` n’est actuellement présent dans ce snapshot du dépôt.

Hypothèse pour ce brouillon :
- Traiter l’utilisation et la redistribution comme non définies tant que le mainteneur n’ajoute pas une licence explicite.

Action suivante recommandée :
- Ajouter un `LICENSE` à la racine (par exemple MIT/Apache-2.0/GPL-3.0) puis mettre à jour cette section.

> 📝 Tant qu’un fichier de licence n’est pas ajouté, considérez les hypothèses de redistribution commerciale/interne comme non résolues et confirmez directement avec le mainteneur.

---

## Remerciements

- Profil du mainteneur et sponsor : [@lachlanchen](https://github.com/lachlanchen)
- Source de configuration de financement : [`.github/FUNDING.yml`](.github/FUNDING.yml)
- Services de l’écosystème référencés dans ce dépôt : Selenium, Tornado, SendGrid, 2Captcha, APIs captcha Turing.

---

## Soutenir AutoPublish

💖 Le soutien de la communauté finance l’infra, le travail de fiabilité et les nouvelles intégrations plateformes.

AutoPublish s’inscrit dans un effort plus large pour garder les outils créateurs cross-plateformes ouverts et hackables. Les dons aident à :

- Maintenir en ligne la ferme Selenium, l’API de traitement et les GPUs cloud.
- Livrer de nouveaux publishers (Kuaishou, Instagram Reels, etc.) et des correctifs de fiabilité pour les bots existants.
- Partager davantage de documentation, jeux de données de démarrage et tutoriels pour les créateurs indépendants.

### Faire un don

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

Également disponible via :
- GitHub Sponsors: <https://github.com/sponsors/lachlanchen>
- Liens projet : <https://lazying.art>, <https://chat.lazying.art>, <https://onlyideas.art>
