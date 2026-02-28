[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)



[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# AutoPublish

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#prerequisites)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#system-overview)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#running-the-tornado-service-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#platform-specific-notes)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#running-the-tornado-service-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#pwa-frontend-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-ar%20%7C%20de%20%7C%20es%20%7C%20fr%20%7C%20ja%20%7C%20ko%20%7C%20ru%20%7C%20vi%20%7C%20zh--Hans%20%7C%20zh--Hant-0EA5E9)](#table-of-contents)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#license)

Boîte à outils d’automatisation pour distribuer des vidéos courtes sur plusieurs plateformes de créateurs chinoises et internationales. Le projet combine un service basé sur Tornado, des bots d’automatisation Selenium et un workflow local de surveillance de dossiers, de sorte que déposer une vidéo dans un dossier aboutit, à terme, à des publications sur XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), Instagram, et éventuellement YouTube.

Le dépôt est volontairement bas niveau : la majeure partie de la configuration vit dans des fichiers Python et des scripts shell. Ce document sert de manuel d’exploitation couvrant l’installation, l’exécution et les points d’extension.

> ⚙️ **Philosophie d’exploitation** : ce projet privilégie des scripts explicites et l’automatisation directe du navigateur plutôt que des couches d’abstraction cachées.
> ✅ **Politique canonique pour ce README** : préserver le niveau de détail technique, puis améliorer la lisibilité et la découvrabilité.
> 🌍 **État de la localisation (vérifié dans cet espace de travail le 28 février 2026)** : `i18n/` inclut actuellement les variantes arabe, allemande, espagnole, française, japonaise, coréenne, russe, vietnamienne, chinoise simplifiée et chinoise traditionnelle.

### Navigation rapide

| Je veux... | Aller ici |
| --- | --- |
| Exécuter ma première publication | [Quick Start Checklist](#quick-start-checklist) |
| Comparer les modes d’exécution | [Runtime Modes at a Glance](#runtime-modes-at-a-glance) |
| Configurer identifiants et chemins | [Configuration](#configuration) |
| Lancer le mode API et mettre des jobs en file | [Running the Tornado service (`app.py`)](#running-the-tornado-service-apppy) |
| Valider avec des commandes copier-coller | [Examples](#examples) |
| Installer sur Raspberry Pi/Linux | [Raspberry Pi / Linux Service Setup](#raspberry-pi--linux-service-setup) |

## Commencer ici

Si vous découvrez ce dépôt, suivez cette séquence :

1. Lisez [Prerequisites](#prerequisites) et [Installation](#installation).
2. Configurez les secrets et chemins absolus dans [Configuration](#configuration).
3. Préparez les sessions de débogage navigateur dans [Preparing Browser Sessions](#preparing-browser-sessions).
4. Choisissez un mode d’exécution dans [Usage](#usage) : `autopub.py` (watcher) ou `app.py` (file API).
5. Validez avec les commandes de [Examples](#examples).

## Vue d’ensemble

AutoPublish prend actuellement en charge deux modes d’exécution de production :

1. **Mode watcher CLI (`autopub.py`)** pour une ingestion et une publication basées sur des dossiers.
2. **Mode file API (`app.py`)** pour une publication via HTTP (`/publish`, `/publish/queue`) à partir de ZIP.

Il est conçu pour les opérateurs qui préfèrent des workflows transparents centrés sur des scripts, plutôt que des plateformes d’orchestration abstraites.

### Modes d’exécution en un coup d’œil

| Mode | Point d’entrée | Entrée | Idéal pour | Comportement en sortie |
| --- | --- | --- | --- | --- |
| Watcher CLI | `autopub.py` | Fichiers déposés dans `videos/` | Workflows d’opérateur local et boucles cron/service | Traite les vidéos détectées et publie immédiatement sur les plateformes sélectionnées |
| Service de file API | `app.py` | Upload ZIP vers `POST /publish` | Intégrations avec des systèmes amont et déclenchement distant | Accepte les jobs, les place en file et exécute la publication dans l’ordre des workers |

## Aperçu rapide

| Élément | Valeur |
| --- | --- |
| Langage principal | Python 3.10+ |
| Exécutions principales | Watcher CLI (`autopub.py`) + service de file Tornado (`app.py`) |
| Moteur d’automatisation | Selenium + sessions Chromium en remote-debug |
| Formats d’entrée | Vidéos brutes (`videos/`) et bundles ZIP (`/publish`) |
| Chemin de l’espace de travail actuel | `/home/lachlan/ProjectsLFS/AutoPublish` |
| Utilisateurs visés | Créateurs/ingénieurs ops gérant des pipelines vidéo courts multi-plateformes |

### Instantané sécurité opérationnelle

| Sujet | État actuel | Action |
| --- | --- | --- |
| Chemins codés en dur | Présents dans plusieurs modules/scripts | Mettre à jour les constantes de chemin par machine avant la production |
| État de connexion navigateur | Requis | Conserver des profils remote-debug persistants par plateforme |
| Gestion des captchas | Intégrations optionnelles disponibles | Configurer les identifiants 2Captcha/Turing si nécessaire |
| Déclaration de licence | Aucun fichier `LICENSE` détecté à la racine | Confirmer les conditions d’usage avec le mainteneur avant redistribution |

---

## Table des matières

- [Commencer ici](#commencer-ici)
- [Vue d’ensemble](#vue-densemble)
- [Modes d’exécution en un coup d’œil](#modes-dexécution-en-un-coup-dœil)
- [Aperçu rapide](#aperçu-rapide)
- [Instantané sécurité opérationnelle](#instantané-sécurité-opérationnelle)
- [Aperçu système](#aperçu-système)
- [Fonctionnalités](#fonctionnalités)
- [Structure du projet](#structure-du-projet)
- [Organisation du dépôt](#organisation-du-dépôt)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Préparer les sessions navigateur](#préparer-les-sessions-navigateur)
- [Utilisation](#utilisation)
- [Exemples](#exemples)
- [Format des métadonnées et ZIP](#format-des-métadonnées-et-zip)
- [Notes spécifiques par plateforme](#notes-spécifiques-par-plateforme)
- [Installation du service Raspberry Pi / Linux](#installation-du-service-raspberry-pi--linux)
- [Scripts macOS hérités](#scripts-macos-hérités)
- [Dépannage et maintenance](#dépannage-et-maintenance)
- [Étendre le système](#étendre-le-système)
- [Checklist de démarrage rapide](#checklist-de-démarrage-rapide)
- [Notes de développement](#notes-de-développement)
- [Feuille de route](#feuille-de-route)
- [Contribuer](#contribuer)
- [❤️ Support](#-support)
- [Licence](#licence)
- [Remerciements](#remerciements)

---

## Aperçu système

🎯 **Flux de bout en bout** des médias bruts vers les posts publiés :

Vue d’ensemble du workflow :

1. **Ingestion des rushes** : placez une vidéo dans `videos/`. Le watcher (via `autopub.py` ou un planificateur/service) détecte les nouveaux fichiers à l’aide de `videos_db.csv` et `processed.csv`.
2. **Génération des assets** : `process_video.VideoProcessor` envoie le fichier vers un serveur de traitement de contenu (`upload_url` et `process_url`) qui renvoie un package ZIP contenant :
   - la vidéo éditée/encodée (`<stem>.mp4`),
   - une image de couverture,
   - `{stem}_metadata.json` avec titres localisés, descriptions, tags, etc.
3. **Publication** : les métadonnées pilotent les publishers Selenium dans `pub_*.py`. Chaque publisher se connecte à une instance Chromium/Chrome déjà lancée via des ports de remote debugging et des répertoires de profil persistants.
4. **Plan de contrôle Web (optionnel)** : `app.py` expose `/publish`, accepte des bundles ZIP préconstruits, les extrait et place des jobs de publication en file vers les mêmes publishers. Il peut aussi rafraîchir les sessions navigateur et déclencher les helpers de connexion (`login_*.py`).
5. **Modules de support** : `load_env.py` hydrate les secrets depuis `~/.bashrc`, `utils.py` fournit des helpers (focus fenêtre, gestion QR, helpers mail), et `solve_captcha_*.py` intègre Turing/2Captcha quand des captchas apparaissent.

## Fonctionnalités

✨ **Conçu pour une automatisation pragmatique centrée scripts** :

- Publication multi-plateformes : XiaoHongShu, Douyin, Bilibili, ShiPinHao (WeChat Channels), Instagram, YouTube (optionnel).
- Deux modes de fonctionnement : pipeline watcher CLI (`autopub.py`) et service de file API (`app.py` + `/publish` + `/publish/queue`).
- Interrupteurs de désactivation temporaire par plateforme via les fichiers `ignore_*`.
- Réutilisation de sessions navigateur en remote-debug avec profils persistants.
- Helpers optionnels pour QR/captcha et notifications email.
- Pas de build frontend requis pour l’UI d’upload PWA incluse (`pwa/`).
- Scripts d’automatisation Linux/Raspberry Pi pour l’installation de service (`scripts/`).

### Matrice de fonctionnalités

| Capacité | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Source d’entrée | Watcher local `videos/` | ZIP uploadé via `POST /publish` |
| Mise en file | Progression interne basée fichiers | File de jobs explicite en mémoire |
| Drapeaux de plateforme | Args CLI (`--pub-*`) + `ignore_*` | Args de requête (`publish_*`) + `ignore_*` |
| Cas d’usage idéal | Workflow opérateur mono-hôte | Systèmes externes et déclenchement distant |

---

## Structure du projet

Organisation source/exécution de haut niveau :

```text
AutoPublish/
├── README.md
├── app.py
├── autopub.py
├── process_video.py
├── load_env.py
├── utils.py
├── pub_*.py                  # publishers de plateforme
├── login_*.py                # helpers de connexion/session
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
├── i18n/                     # READMEs multilingues
├── videos/                   # artefacts d’entrée runtime
├── logs/, logs-autopub/      # logs runtime
├── temp/, temp_screenshot/   # artefacts temporaires runtime
├── videos_db.csv
└── processed.csv
```

Note : `transcription_data/` est utilisé à l’exécution par le flux de traitement/publication et peut apparaître après exécution.

## Organisation du dépôt

🗂️ **Modules clés et rôle** :

| Path | Purpose |
| --- | --- |
| `app.py` | Service Tornado exposant `/publish` et `/publish/queue`, avec file de publication interne et thread worker. |
| `autopub.py` | Watcher CLI : scanne `videos/`, traite les nouveaux fichiers et invoque les publishers en parallèle. |
| `process_video.py` | Envoie les vidéos au backend de traitement et stocke les bundles ZIP retournés. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | Modules d’automatisation Selenium par plateforme. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | Vérifications de session et flux de connexion QR. |
| `utils.py` | Helpers d’automatisation partagés (focus fenêtre, utilitaires QR/mail, helpers de diagnostic). |
| `load_env.py` | Charge les variables d’environnement depuis le profil shell (`~/.bashrc`) et masque les logs sensibles. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | Helpers SMTP/SendGrid et scripts de test. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Intégrations de résolution de captcha. |
| `scripts/` | Scripts d’installation et d’exploitation de service (Raspberry Pi/Linux + automatisation héritée). |
| `pwa/` | PWA statique pour prévisualisation ZIP et soumission de publication. |
| `setup_raspberrypi.md` | Guide pas-à-pas de provisioning Raspberry Pi. |
| `.env.example` | Template de variables d’environnement (identifiants, chemins, clés captcha). |
| `.github/FUNDING.yml` | Configuration sponsor/financement. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | Artefacts runtime et logs (beaucoup sont ignorés par git). |

---

## Prérequis

🧰 **Installez ces éléments avant la première exécution**.

### Système d’exploitation et outils

- Linux desktop/server avec session X (`DISPLAY=:1` est courant dans les scripts fournis).
- Chromium/Chrome et ChromeDriver correspondant.
- Outils GUI/média : `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv ou Conda).

### Dépendances Python

Jeu minimal runtime :

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

Parité dépôt :

```bash
python -m pip install -r requirements.txt
```

Pour des installations de service allégées (utilisées par défaut par les scripts d’installation) :

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

1. Clonez le dépôt :

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. Créez et activez un environnement (exemple avec `venv`) :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. Préparez les variables d’environnement :

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. Chargez les variables pour les scripts qui lisent les valeurs du profil shell :

```bash
source ~/.bashrc
python load_env.py
```

Note : `load_env.py` est conçu autour de `~/.bashrc` ; si votre environnement utilise un autre profil shell, adaptez en conséquence.

---

## Configuration

🔐 **Définissez les identifiants, puis vérifiez les chemins spécifiques à l’hôte**.

### Variables d’environnement

Le projet attend des identifiants et des chemins optionnels navigateur/runtime via des variables d’environnement. Commencez à partir de `.env.example` :

| Variable | Description |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | Identifiants SMTP pour les notifications QR/connexion. |
| `SENDGRID_API_KEY` | Clé SendGrid pour les flux email qui utilisent les APIs SendGrid. |
| `APIKEY_2CAPTCHA` | Clé API 2Captcha. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Identifiants captcha Turing. |
| `DOUYIN_LOGIN_PASSWORD` | Helper de seconde vérification Douyin. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Surcharges Instagram/driver navigateur. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | Surcharges globales préférées navigateur/driver/display dans `app.py`. |

### Constantes de chemin (important)

📌 **Problème de démarrage le plus fréquent** : chemins absolus codés en dur non résolus.

Plusieurs modules contiennent encore des chemins codés en dur. Mettez-les à jour pour votre hôte :

| File | Constant(s) | Meaning |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | Racines du service API et endpoints backend. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | Racines du watcher CLI et endpoints backend. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Chemins absolus vers emplacements Python/Conda/dépôt/logs. | Wrappers hérités orientés macOS. |
| `utils.py` | Hypothèses de chemin FFmpeg dans les helpers de traitement des couvertures. | Compatibilité des chemins d’outils média. |

Note importante sur le dépôt :
- Le chemin actuel du dépôt dans cet espace de travail est `/home/lachlan/ProjectsLFS/AutoPublish`.
- Une partie du code et des scripts référence encore `/home/lachlan/Projects/auto-publish` ou `/Users/lachlan/...`.
- Conservez puis ajustez ces chemins en local avant usage en production.

### Bascule plateforme via `ignore_*`

🧩 **Interrupteur de sécurité rapide** : toucher un fichier `ignore_*` désactive ce publisher sans modifier le code.

Les drapeaux de publication sont aussi soumis aux fichiers d’ignore. Créez un fichier vide pour désactiver une plateforme :

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

Supprimez le fichier correspondant pour réactiver.

---

## Préparer les sessions navigateur

🌐 **La persistance de session est obligatoire** pour une publication Selenium fiable.

1. Créez des dossiers de profil dédiés :

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. Lancez les sessions navigateur avec remote debugging (exemple pour XiaoHongShu) :

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. Connectez-vous manuellement une fois par plateforme/profil.

4. Vérifiez que Selenium peut se connecter :

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Note de sécurité :
- `app.py` contient actuellement un placeholder de mot de passe sudo codé en dur (`password = "1"`) utilisé par la logique de redémarrage navigateur. Remplacez-le avant un déploiement réel.

---

## Utilisation

▶️ **Deux modes d’exécution** sont disponibles : watcher CLI et service de file API.

### Exécuter le pipeline CLI (`autopub.py`)

1. Placez les vidéos source dans le dossier surveillé (`videos/` ou votre `autopublish_folder_path` configuré).
2. Exécutez :

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Drapeaux :

| Flag | Meaning |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Restreint la publication aux plateformes sélectionnées. Si aucun n’est passé, les trois sont activées par défaut. |
| `--test` | Mode test transmis aux publishers (comportement variable selon le module de plateforme). |
| `--use-cache` | Réutilise `transcription_data/<video>/<video>.zip` existant si disponible. |

Flux CLI par vidéo :
- Upload/traitement via `process_video.py`.
- Extraction du ZIP vers `transcription_data/<video>/`.
- Lancement des publishers sélectionnés via `ThreadPoolExecutor`.
- Ajout de l’état de suivi dans `videos_db.csv` et `processed.csv`.

### Exécuter le service Tornado (`app.py`)

🛰️ **Le mode API** est utile pour les systèmes externes qui produisent des bundles ZIP.

Démarrer le serveur :

```bash
python app.py --refresh-time 1800 --port 8081
```

Résumé des endpoints API :

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/publish` | `POST` | Upload des octets ZIP et mise en file d’un job de publication |
| `/publish/queue` | `GET` | Inspection de la file, de l’historique des jobs et de l’état de publication |

### `POST /publish`

📤 **Mettre un job de publication en file** en envoyant directement les octets ZIP.

- Header: `Content-Type: application/octet-stream`
- Arg de query/form requis : `filename` (nom du ZIP)
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
- La réponse immédiate renvoie un JSON incluant `status: queued`, `job_id`, et `queue_size`.
- Le thread worker traite les jobs en file de manière sérielle.

### `GET /publish/queue`

📊 **Observer l’état de la file et des jobs en vol**.

Renvoie un JSON de statut/historique de file :

```bash
curl "http://localhost:8081/publish/queue"
```

Les champs de réponse incluent :
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Thread de rafraîchissement navigateur

♻️ Un rafraîchissement périodique du navigateur réduit les échecs de session expirée sur de longues durées d’exécution.

`app.py` exécute un thread de rafraîchissement en arrière-plan avec l’intervalle `--refresh-time` et des hooks de vérification de connexion. Le délai de sleep du refresh inclut un comportement de retard aléatoire.

### Frontend PWA (`pwa/`)

🖥️ UI statique légère pour upload manuel de ZIP et inspection de la file.

Lancer l’UI statique en local :

```bash
cd pwa
python -m http.server 5173
```

Ouvrez `http://localhost:5173` et définissez l’URL de base backend (par exemple `http://lazyingart:8081`).

Capacités PWA :
- Prévisualisation ZIP via glisser-déposer.
- Bascules de cibles de publication + mode test.
- Envoi vers `/publish` et polling de `/publish/queue`.

### Palette de commandes

🧷 **Les commandes les plus utilisées au même endroit**.

| Task | Command |
| --- | --- |
| Installer toutes les dépendances | `python -m pip install -r requirements.txt` |
| Installer les dépendances runtime allégées | `python -m pip install -r requirements.autopub.txt` |
| Charger les variables d’env shell | `source ~/.bashrc && python load_env.py` |
| Démarrer le serveur API de file | `python app.py --refresh-time 1800 --port 8081` |
| Démarrer le pipeline watcher CLI | `python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili` |
| Soumettre un ZIP à la file | `curl -X POST "http://localhost:8081/publish?filename=demo.zip" --data-binary @demo.zip -H "Content-Type: application/octet-stream"` |
| Inspecter l’état de la file | `curl -s "http://localhost:8081/publish/queue"` |
| Servir la PWA locale | `cd pwa && python -m http.server 5173` |

---

## Exemples

🧪 **Commandes de smoke test copier-coller** :

### Exemple 0 : charger l’environnement et démarrer le serveur API

```bash
source ~/.bashrc
python load_env.py
python app.py --refresh-time 1800 --port 8081
```

### Exemple A : exécution de publication CLI

```bash
python autopub.py --pub-xhs --pub-douyin --use-cache
```

### Exemple B : exécution de publication API (ZIP unique)

```bash
curl -X POST "http://localhost:8081/publish?filename=my_bundle.zip&publish_bilibili=true&test=true" \
  --data-binary @my_bundle.zip \
  -H "Content-Type: application/octet-stream"
```

### Exemple C : vérifier l’état de la file

```bash
curl -s "http://localhost:8081/publish/queue"
```

### Exemple D : smoke test des helpers SMTP

```bash
python smtp.py
python smtp_test_simple.py
```

---

## Format des métadonnées et ZIP

📦 **Le contrat ZIP est essentiel** : gardez les noms de fichiers et clés de métadonnées alignés avec les attentes des publishers.

Contenu ZIP attendu (minimum) :

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` pilote les publishers CN ; `metadata["english_version"]` optionnel alimente le publisher YouTube.

Champs couramment utilisés par les modules :
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (liste de hashtags)
- `video_filename`, `cover_filename`
- champs spécifiques plateforme tels qu’implémentés dans les fichiers `pub_*.py`

Si vous générez des ZIPs en externe, gardez les clés et noms de fichiers alignés avec les attentes des modules.

---

## Notes spécifiques par plateforme

🧭 **Carte des ports + modules propriétaires** pour chaque publisher.

| Platform | Port | Module(s) | Notes |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | Flux de reconnexion QR ; assainissement du titre et hashtags depuis les métadonnées. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Les vérifications de fin d’upload et chemins de retry sont fragiles côté plateforme ; surveillez les logs de près. |
| Bilibili | 5005 | `pub_bilibili.py` | Hooks captcha disponibles via `solve_captcha_2captcha.py` et `solve_captcha_turing.py`. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Une validation QR rapide est importante pour la fiabilité du rafraîchissement de session. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | Contrôlé en mode API avec `publish_instagram=true` ; variables d’environnement disponibles dans `.env.example`. |
| YouTube | 9222 | `pub_y2b.py` | Utilise le bloc de métadonnées `english_version` ; désactiver via `ignore_y2b`. |

---

## Installation du service Raspberry Pi / Linux

🐧 **Recommandé pour les hôtes toujours actifs**.

Pour un bootstrap hôte complet, suivez [`setup_raspberrypi.md`](setup_raspberrypi.md).

Installation rapide du pipeline :

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

Exécuter le service manuellement dans tmux :

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

🍎 Des wrappers hérités restent présents pour compatibilité avec d’anciens environnements locaux.

Le dépôt inclut encore des wrappers hérités orientés macOS :
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

Ils contiennent des chemins absolus `/Users/lachlan/...` et des hypothèses Conda. Conservez-les si vous dépendez de ce workflow, mais mettez à jour chemins/venv/outillage pour votre hôte.

---

## Dépannage et maintenance

🛠️ **En cas d’échec, commencez ici**.

- **Dérive des chemins entre machines** : si des erreurs mentionnent des fichiers manquants sous `/Users/lachlan/...` ou `/home/lachlan/Projects/auto-publish`, alignez les constantes sur le chemin de votre hôte (`/home/lachlan/ProjectsLFS/AutoPublish` dans cet espace de travail).
- **Hygiène des secrets** : exécutez `~/.local/bin/detect-secrets scan` avant chaque push. Faites tourner toute clé exposée.
- **Erreurs backend de traitement** : si `process_video.py` affiche “Failed to get the uploaded file path,” vérifiez que le JSON de réponse d’upload contient `file_path` et que l’endpoint de traitement renvoie des octets ZIP.
- **Incompatibilité ChromeDriver** : si des erreurs de connexion DevTools apparaissent, alignez les versions Chrome/Chromium et driver (ou basculez sur `webdriver-manager`).
- **Problèmes de focus navigateur** : `bring_to_front` dépend du matching du titre de fenêtre (les différences de nommage Chromium/Chrome peuvent casser cela).
- **Interruptions captcha** : configurez les identifiants 2Captcha/Turing et intégrez les sorties du solveur si nécessaire.
- **Fichiers de lock obsolètes** : si les runs planifiés ne démarrent jamais, vérifiez l’état des processus et supprimez `autopub.lock` obsolète (flux script hérité).
- **Logs à inspecter** : `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log`, plus les journaux de service.

---

## Étendre le système

🧱 **Points d’extension** pour de nouvelles plateformes et une exploitation plus sûre.

- **Ajouter une nouvelle plateforme** : copiez un module `pub_*.py`, mettez à jour sélecteurs/flows, ajoutez `login_*.py` si une réauth QR est nécessaire, puis branchez les drapeaux et la gestion de file dans `app.py` et le câblage CLI dans `autopub.py`.
- **Abstraction de configuration** : migrez les constantes dispersées vers une config structurée (`config.yaml`/`.env` + modèle typé) pour un fonctionnement multi-hôtes.
- **Renforcement du stockage des identifiants** : remplacez les flux sensibles codés en dur ou exposés shell par une gestion sécurisée des secrets (`sudo -A`, trousseau, vault/secret manager).
- **Conteneurisation** : packagez Chromium/ChromeDriver + runtime Python + affichage virtuel en une unité déployable pour usage cloud/serveur.

---

## Checklist de démarrage rapide

✅ **Chemin minimal vers une première publication réussie**.

1. Clonez ce dépôt et installez les dépendances (`pip install -r requirements.txt` ou `requirements.autopub.txt` allégé).
2. Mettez à jour les constantes de chemins codés en dur dans `app.py`, `autopub.py`, et tout script que vous allez exécuter.
3. Exportez les identifiants requis dans votre profil shell ou `.env` ; exécutez `python load_env.py` pour valider le chargement.
4. Créez les dossiers de profil navigateur remote-debug et lancez une fois chaque session de plateforme requise.
5. Connectez-vous manuellement sur chaque plateforme cible dans son profil.
6. Démarrez soit le mode API (`python app.py --port 8081`), soit le mode CLI (`python autopub.py --use-cache ...`).
7. Soumettez un ZIP d’exemple (mode API) ou un fichier vidéo d’exemple (mode CLI), puis inspectez `logs/`.
8. Lancez un scan de secrets avant chaque push.

---

## Notes de développement

🧬 **Baseline de développement actuelle** (formatage manuel + smoke tests).

- Le style Python suit l’indentation existante à 4 espaces et un formatage manuel.
- Il n’existe pas de suite de tests automatisée formelle ; reposez-vous sur des smoke tests :
  - traiter une vidéo d’exemple via `autopub.py` ;
  - poster un ZIP vers `/publish` et surveiller `/publish/queue` ;
  - valider manuellement chaque plateforme cible.
- Incluez un petit point d’entrée `if __name__ == "__main__":` quand vous ajoutez de nouveaux scripts pour des dry-runs rapides.
- Isolez les changements plateforme autant que possible (`pub_*`, `login_*`, bascules `ignore_*`).
- Les artefacts runtime (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) sont censés rester locaux et sont majoritairement ignorés par git.

---

## Feuille de route

🗺️ **Améliorations prioritaires reflétées par les contraintes actuelles du code**.

Améliorations prévues/souhaitées (d’après la structure actuelle du code et les notes existantes) :

1. Remplacer les chemins codés en dur dispersés par une configuration centrale (`.env`/YAML + modèles typés).
2. Supprimer les motifs de mot de passe sudo codé en dur et déplacer le contrôle des processus vers des mécanismes plus sûrs.
3. Améliorer la fiabilité de publication avec des retries plus robustes et une meilleure détection d’état UI par plateforme.
4. Étendre le support plateforme (par exemple Kuaishou ou d’autres plateformes créateurs).
5. Emballer le runtime en unités de déploiement reproductibles (conteneur + profil d’affichage virtuel).
6. Ajouter des contrôles d’intégration automatisés pour le contrat ZIP et l’exécution de file.

---

## Contribuer

🤝 Gardez les PR ciblées, reproductibles, et explicites sur les hypothèses runtime.

Les contributions sont bienvenues.

1. Forkez et créez une branche ciblée.
2. Gardez des commits petits et impératifs (style d’exemple dans l’historique : “Wait for YouTube checks before publishing”).
3. Incluez des notes de vérification manuelle dans les PR :
   - hypothèses d’environnement,
   - redémarrages navigateur/session,
   - logs/captures pertinents pour les changements de flux UI.
4. Ne committez jamais de vrais secrets (`.env` est ignoré ; utilisez `.env.example` uniquement pour la forme).

Si vous introduisez de nouveaux modules publisher, câblez tous les éléments suivants :
- `pub_<platform>.py`
- `login_<platform>.py` optionnel
- Drapeaux API et gestion de file dans `app.py`
- Câblage CLI dans `autopub.py` (si nécessaire)
- Gestion des bascules `ignore_<platform>`
- Mises à jour du README

---

## ❤️ Support

| Donate | PayPal | Stripe |
|---|---|---|
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=ko-fi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

---

## Licence

Aucun fichier `LICENSE` n’est actuellement présent dans cet instantané du dépôt.

Hypothèse pour ce draft :
- Considérez l’usage et la redistribution comme non définis tant que le mainteneur n’a pas ajouté un fichier de licence explicite.

Prochaine action recommandée :
- Ajouter un `LICENSE` à la racine (par exemple MIT/Apache-2.0/GPL-3.0) et mettre cette section à jour en conséquence.

> 📝 Tant qu’un fichier de licence n’est pas ajouté, considérez les hypothèses de redistribution commerciale/interne comme non résolues et confirmez directement avec le mainteneur.

---

## Remerciements

- Profil mainteneur et sponsor : [@lachlanchen](https://github.com/lachlanchen)
- Source de configuration de financement : [`.github/FUNDING.yml`](.github/FUNDING.yml)
- Services écosystème référencés dans ce dépôt : Selenium, Tornado, SendGrid, APIs captcha 2Captcha et Turing.

---

