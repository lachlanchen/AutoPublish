[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# AutoPublish

> 🌍 **Estado de localización (verificado en este espacio de trabajo el 28 de febrero de 2026):**
> `i18n/` actualmente incluye `README.ar.md` y `README.es.md`; `README.zh-CN.md` y `README.ja.md` están reservados como objetivos para archivos próximos.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#prerrequisitos)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-43B02A?logo=selenium&logoColor=white)](#descripcion-general-del-sistema)
[![Tornado](https://img.shields.io/badge/API-Tornado-3A7E3A)](#ejecucion-del-servicio-tornado-apppy)
[![Platforms](https://img.shields.io/badge/Platforms-XHS%20%7C%20Douyin%20%7C%20Bilibili%20%7C%20ShiPinHao%20%7C%20Instagram%20%7C%20YouTube-0F766E)](#notas-especificas-por-plataforma)
[![API Queue](https://img.shields.io/badge/Queue-Enabled-2563EB)](#ejecucion-del-servicio-tornado-apppy)
[![PWA](https://img.shields.io/badge/Frontend-PWA-10B981)](#frontend-pwa-pwa)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)
[![i18n](https://img.shields.io/badge/i18n-English%20%7C%20Arabic%20%7C%20Spanish-0EA5E9)](#tabla-de-contenidos)
[![License](https://img.shields.io/badge/License-Not%20Declared-red)](#licencia)

Kit de automatización para distribuir contenido de video corto en múltiples plataformas chinas e internacionales para creadores. El proyecto combina un servicio basado en Tornado, bots de automatización con Selenium y un flujo local de vigilancia de archivos para que, al soltar un video en una carpeta, termine publicándose en XiaoHongShu, Douyin, Bilibili, WeChat Channels (ShiPinHao), Instagram y, opcionalmente, YouTube.

El repositorio es intencionalmente de bajo nivel: la mayor parte de la configuración vive en archivos Python y scripts de shell. Este documento es un manual operativo que cubre configuración, ejecución y puntos de extensión.

> ⚙️ **Filosofía operativa**: este proyecto prioriza scripts explícitos y automatización directa del navegador sobre capas de abstracción ocultas.
> ✅ **Política canónica para este README**: preservar el detalle técnico y luego mejorar legibilidad y descubribilidad.

## Empieza Aquí

Si eres nuevo en este repositorio, usa esta secuencia:

1. Lee [Prerequisites](#prerrequisitos) e [Installation](#instalacion).
2. Configura secretos y rutas absolutas en [Configuration](#configuracion).
3. Prepara sesiones de depuración del navegador en [Preparing Browser Sessions](#preparacion-de-sesiones-del-navegador).
4. Elige un modo de ejecución en [Usage](#uso): `autopub.py` (watcher) o `app.py` (cola API).
5. Valida con los comandos de [Examples](#ejemplos).

## Resumen

AutoPublish actualmente soporta dos modos de ejecución en producción:

1. **Modo watcher de CLI (`autopub.py`)** para ingestión y publicación basadas en carpeta.
2. **Modo cola API (`app.py`)** para publicación basada en ZIP vía HTTP (`/publish`, `/publish/queue`).

Está diseñado para operadores que prefieren flujos transparentes, centrados en scripts, en lugar de plataformas de orquestación abstractas.

### Modos de Ejecución de un Vistazo

| Modo | Punto de entrada | Entrada | Ideal para | Comportamiento de salida |
| --- | --- | --- | --- | --- |
| Watcher CLI | `autopub.py` | Archivos colocados en `videos/` | Flujos locales de operador y bucles cron/servicio | Procesa videos detectados y publica inmediatamente en las plataformas seleccionadas |
| Servicio de cola API | `app.py` | Carga ZIP a `POST /publish` | Integraciones con sistemas upstream y activación remota | Acepta trabajos, los encola y ejecuta publicación en orden de workers |

## Vista Rápida

| Qué | Valor |
| --- | --- |
| Lenguaje principal | Python 3.10+ |
| Runtimes principales | Watcher CLI (`autopub.py`) + servicio de cola Tornado (`app.py`) |
| Motor de automatización | Selenium + sesiones Chromium con depuración remota |
| Formatos de entrada | Videos crudos (`videos/`) y bundles ZIP (`/publish`) |
| Ruta actual del espacio de trabajo del repo | `/home/lachlan/ProjectsLFS/AutoPublish` |
| Usuarios ideales | Creadores/ingenieros de ops que gestionan pipelines multi-plataforma de video corto |

### Vista de Seguridad Operativa

| Tema | Estado actual | Acción |
| --- | --- | --- |
| Rutas hard-codeadas | Presentes en múltiples módulos/scripts | Actualiza constantes de rutas por host antes de ejecución en producción |
| Estado de login del navegador | Requerido | Mantén perfiles persistentes de depuración remota por plataforma |
| Gestión de captcha | Integraciones opcionales disponibles | Configura credenciales de 2Captcha/Turing si hace falta |
| Declaración de licencia | No se detecta archivo `LICENSE` en el nivel raíz | Confirma términos de uso con el mantenedor antes de redistribuir |

---

## Tabla de Contenidos

- [Resumen](#resumen)
- [Descripción General del Sistema](#descripcion-general-del-sistema)
- [Características](#caracteristicas)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Distribución del Repositorio](#distribucion-del-repositorio)
- [Prerrequisitos](#prerrequisitos)
- [Instalación](#instalacion)
- [Configuración](#configuracion)
- [Preparación de Sesiones del Navegador](#preparacion-de-sesiones-del-navegador)
- [Uso](#uso)
- [Ejemplos](#ejemplos)
- [Metadata y Formato ZIP](#metadata-y-formato-zip)
- [Notas Específicas por Plataforma](#notas-especificas-por-plataforma)
- [Configuración de Servicio Raspberry Pi / Linux](#configuracion-de-servicio-raspberry-pi--linux)
- [Scripts Legacy para macOS](#scripts-legacy-para-macos)
- [Solución de Problemas y Mantenimiento](#solucion-de-problemas-y-mantenimiento)
- [Extender el Sistema](#extender-el-sistema)
- [Checklist de Inicio Rápido](#checklist-de-inicio-rapido)
- [Notas de Desarrollo](#notas-de-desarrollo)
- [Hoja de Ruta](#hoja-de-ruta)
- [Contribuir](#contribuir)
- [Licencia](#licencia)
- [Agradecimientos](#agradecimientos)
- [Apoya AutoPublish](#apoya-autopublish)

---

## Descripción General del Sistema

🎯 **Flujo end-to-end** desde media cruda hasta publicaciones.

Flujo de un vistazo:

1. **Ingreso de material bruto**: coloca un video en `videos/`. El watcher (ya sea `autopub.py` o un scheduler/servicio) detecta nuevos archivos usando `videos_db.csv` y `processed.csv`.
2. **Generación de recursos**: `process_video.VideoProcessor` sube el archivo a un servidor de procesamiento de contenido (`upload_url` y `process_url`) que devuelve un paquete ZIP con:
   - el video editado/codificado (`<stem>.mp4`),
   - una imagen de portada,
   - `{stem}_metadata.json` con títulos localizados, descripciones, etiquetas, etc.
3. **Publicación**: la metadata guía a los publicadores Selenium en `pub_*.py`. Cada publicador se adjunta a una instancia Chromium/Chrome ya activa usando puertos de depuración remota y directorios persistentes de datos de usuario.
4. **Plano de control web (opcional)**: `app.py` expone `/publish`, acepta bundles ZIP ya construidos, los descomprime y encola trabajos de publicación para los mismos publicadores. También puede refrescar sesiones del navegador y activar helpers de login (`login_*.py`).
5. **Módulos de soporte**: `load_env.py` hidrata secretos desde `~/.bashrc`, `utils.py` provee helpers (focus de ventana, manejo de QR, utilidades de correo), y `solve_captcha_*.py` integra Turing/2Captcha cuando aparecen captchas.

## Características

✨ **Diseñado para automatización pragmática, centrada en scripts**:

- Publicación multi-plataforma: XiaoHongShu, Douyin, Bilibili, ShiPinHao (WeChat Channels), Instagram, YouTube (opcional).
- Dos modos de operación: pipeline watcher CLI (`autopub.py`) y servicio de cola API (`app.py` + `/publish` + `/publish/queue`).
- Interruptores de deshabilitación temporal por plataforma vía archivos `ignore_*`.
- Reutilización de sesiones de navegador con depuración remota y perfiles persistentes.
- Automatización opcional de QR/captcha y helpers de notificaciones por correo.
- No se requiere build frontend para la UI de subida PWA incluida (`pwa/`).
- Scripts de automatización Linux/Raspberry Pi para configuración de servicios (`scripts/`).

### Matriz de Características

| Capacidad | CLI (`autopub.py`) | API (`app.py`) |
| --- | --- | --- |
| Fuente de entrada | Watcher local en `videos/` | ZIP subido vía `POST /publish` |
| Encolado | Progresión interna basada en archivos | Cola explícita en memoria |
| Flags de plataforma | Args CLI (`--pub-*`) + `ignore_*` | Query args (`publish_*`) + `ignore_*` |
| Mejor encaje | Flujo de operador de un solo host | Sistemas externos y activación remota |

---

## Estructura del Proyecto

Distribución de código/ejecución a alto nivel:

```text
AutoPublish/
├── README.md
├── app.py
├── autopub.py
├── process_video.py
├── load_env.py
├── utils.py
├── pub_*.py                  # publicadores por plataforma
├── login_*.py                # helpers de login/sesión por plataforma
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
├── i18n/                     # READMEs multilingües (actualmente incluye árabe y español)
├── archived/
├── videos/                   # artefactos de entrada en ejecución
├── logs/, logs-autopub/      # logs de ejecución
├── temp/, temp_screenshot/   # artefactos temporales de ejecución
├── videos_db.csv
└── processed.csv
```

Nota: `transcription_data/` se usa en tiempo de ejecución por el flujo de procesamiento/publicación y puede aparecer tras ejecutar.

## Distribución del Repositorio

🗂️ **Módulos clave y qué hacen**:

| Ruta | Propósito |
| --- | --- |
| `app.py` | Servicio Tornado que expone `/publish` y `/publish/queue`, con cola interna de publicación y thread worker. |
| `autopub.py` | Watcher CLI: escanea `videos/`, procesa archivos nuevos e invoca publicadores en paralelo. |
| `process_video.py` | Sube videos al backend de procesamiento y guarda los bundles ZIP devueltos. |
| `pub_xhs.py`, `pub_douyin.py`, `pub_bilibili.py`, `pub_shipinhao.py`, `pub_instagram.py`, `pub_y2b.py` | Módulos de automatización Selenium por plataforma. |
| `login_xiaohongshu.py`, `login_douyin.py`, `login_shipinhao.py`, `login_instagram.py` | Verificaciones de sesión y flujos de login por QR. |
| `utils.py` | Helpers de automatización compartidos (focus de ventana, utilidades QR/mail, helpers de diagnóstico). |
| `load_env.py` | Carga variables de entorno desde el perfil de shell (`~/.bashrc`) y enmascara logs sensibles. |
| `smtp.py`, `smtp_test_simple.py`, `send_email_qreader.py` | Scripts helper y de prueba SMTP/SendGrid. |
| `solve_captcha_2captcha.py`, `solve_captcha_turing.py` | Integraciones de resolvedor captcha. |
| `scripts/` | Scripts de configuración de servicios y operaciones (Raspberry Pi/Linux + automatización legacy). |
| `pwa/` | PWA estática para vista previa de ZIP y envío de publicación. |
| `setup_raspberrypi.md` | Guía paso a paso de aprovisionamiento en Raspberry Pi. |
| `.env.example` | Plantilla de variables de entorno (credenciales, rutas, claves captcha). |
| `.github/FUNDING.yml` | Configuración de patrocinio/financiación. |
| `logs/`, `logs-autopub/`, `temp/`, `temp_screenshot/`, `videos/` | Artefactos y logs de ejecución (muchos están en `.gitignore`). |

---

## Prerrequisitos

🧰 **Instala esto antes de la primera ejecución**.

### Sistema operativo y herramientas

- Linux desktop/server con sesión X (`DISPLAY=:1` es común en los scripts incluidos).
- Chromium/Chrome y ChromeDriver compatible.
- Helpers GUI/media: `xdotool`, `ffmpeg`, `zip`, `unzip`.
- Python 3.10+ (venv o Conda).

### Dependencias de Python

Conjunto mínimo en runtime:

```bash
pip install selenium tornado requests requests-toolbelt sendgrid qreader opencv-python webdriver-manager
```

Paridad con repositorio:

```bash
python -m pip install -r requirements.txt
```

Para instalaciones ligeras del servicio (usadas por los scripts de setup por defecto):

```bash
python -m pip install -r requirements.autopub.txt
```

`requirements.autopub.txt` contiene:
- `selenium`, `webdriver-manager`, `tornado`, `requests`, `requests-toolbelt`, `sendgrid`, `qreader`, `opencv-python`, `numpy`, `pillow`, `twocaptcha`.

### Opcional: crear un usuario sudo

```bash
sudo useradd -m -s /bin/bash -G sudo <USERNAME> && echo "<USERNAME>:<PASSWORD>" | sudo chpasswd
```

---

## Instalación

🚀 **Configuración desde una máquina limpia**:

1. Clona el repositorio:

```bash
git clone https://github.com/lachlanchen/AutoPublish.git
cd AutoPublish
```

2. Crea y activa un entorno (ejemplo con `venv`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

3. Prepara variables de entorno:

```bash
cp .env.example .env
# fill values in .env (do not commit)
```

4. Carga variables para scripts que leen valores del perfil de shell:

```bash
source ~/.bashrc
python load_env.py
```

Nota: `load_env.py` está diseñado en torno a `~/.bashrc`; si tu entorno usa otro perfil de shell, adáptalo.

---

## Configuración

🔐 **Configura credenciales y luego verifica rutas específicas del host**.

### Variables de entorno

El proyecto espera credenciales y rutas opcionales de navegador/runtime desde variables de entorno. Empieza desde `.env.example`:

| Variable | Descripción |
| --- | --- |
| `FROM_EMAIL`, `TO_EMAIL`, `APP_PASSWORD` | Credenciales SMTP para notificaciones de QR/login. |
| `SENDGRID_API_KEY` | Clave SendGrid para flujos de correo que usan APIs de SendGrid. |
| `APIKEY_2CAPTCHA` | Clave API de 2Captcha. |
| `TULING_USERNAME`, `TULING_PASSWORD`, `TULING_ID` | Credenciales captcha de Turing. |
| `DOUYIN_LOGIN_PASSWORD` | Helper para segunda verificación de Douyin. |
| `INSTAGRAM_*`, `CHROME_*`, `CHROMEDRIVER_PATH` | Overrides de driver/navegador para Instagram. |
| `AUTOPUBLISH_BROWSER_BIN`, `AUTOPUBLISH_CHROMEDRIVER`, `AUTOPUBLISH_DISPLAY` | Overrides globales preferidos de navegador/driver/display en `app.py`. |

### Constantes de rutas (importante)

📌 **Problema de arranque más común**: rutas absolutas hard-codeadas sin resolver.

Varios módulos aún contienen rutas hard-codeadas. Actualízalas para tu host:

| Archivo | Constante(s) | Significado |
| --- | --- | --- |
| `app.py` | `logs_folder_root`, `autopublish_folder_root`, `videos_db_path`, `processed_path`, `transcription_root`, `upload_url`, `process_url`. | Raíces del servicio API y endpoints backend. |
| `autopub.py` | `logs_folder_path`, `autopublish_folder_path`, `videos_db_path`, `processed_path`, `transcription_path`, `upload_url`, `process_url`, `chromedriver_path`. | Raíces del watcher CLI y endpoints backend. |
| `scripts/run_autopub.sh`, `scripts/setup_autopub.sh` | Rutas absolutas a Python/Conda/repo/logs. | Wrappers legacy orientados a macOS. |
| `utils.py` | Suposiciones de ruta FFmpeg en helpers de procesamiento de portada. | Compatibilidad de ruta de herramientas multimedia. |

Nota importante del repositorio:
- La ruta actual del repositorio en este espacio de trabajo es `/home/lachlan/ProjectsLFS/AutoPublish`.
- Parte del código y scripts aún referencia `/home/lachlan/Projects/auto-publish` o `/Users/lachlan/...`.
- Conserva y ajusta estas rutas localmente antes del uso en producción.

### Toggles de plataforma vía `ignore_*`

🧩 **Interruptor de seguridad rápido**: crear un archivo `ignore_*` desactiva ese publicador sin editar código.

Los flags de publicación también están condicionados por archivos `ignore`. Crea un archivo vacío para desactivar una plataforma:

```bash
touch ignore_xhs ignore_douyin ignore_bilibili ignore_shipinhao ignore_instagram ignore_y2b
```

Elimina el archivo correspondiente para volver a habilitarla.

---

## Preparación de Sesiones del Navegador

🌐 **La persistencia de sesión es obligatoria** para publicación Selenium fiable.

1. Crea carpetas de perfil dedicadas:

```bash
mkdir -p ~/chromium_dev_session_{5003,5004,5005,5006,5007,9222}
mkdir -p ~/chromium_dev_session_logs
```

2. Lanza sesiones de navegador con depuración remota (ejemplo para XiaoHongShu):

```bash
DISPLAY=:1 chromium-browser \
  --remote-debugging-port=5003 \
  --user-data-dir="$HOME/chromium_dev_session_5003" \
  https://creator.xiaohongshu.com/creator/post \
  > "$HOME/chromium_dev_session_logs/chromium_xhs.log" 2>&1 &
```

3. Inicia sesión manualmente una vez por cada plataforma/perfil.

4. Verifica que Selenium puede adjuntarse:

```python
from selenium import webdriver
opts = webdriver.ChromeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:5003")
driver = webdriver.Chrome(options=opts)
print(driver.title)
driver.quit()
```

Nota de seguridad:
- `app.py` actualmente contiene un placeholder de contraseña sudo hard-codeada (`password = "1"`) usada por la lógica de reinicio del navegador. Reemplázalo antes de un despliegue real.

---

## Uso

▶️ **Hay dos modos de ejecución** disponibles: watcher CLI y servicio de cola API.

### Ejecución del pipeline CLI (`autopub.py`)

1. Coloca videos fuente en el directorio vigilado (`videos/` o tu `autopublish_folder_path` configurado).
2. Ejecuta:

```bash
python autopub.py --use-cache --pub-xhs --pub-douyin --pub-bilibili
```

Flags:

| Flag | Significado |
| --- | --- |
| `--pub-xhs`, `--pub-douyin`, `--pub-bilibili` | Limita la publicación a plataformas seleccionadas. Si no pasas ninguna, las tres quedan habilitadas por defecto. |
| `--test` | Modo test que se pasa a los publicadores (el comportamiento varía por módulo de plataforma). |
| `--use-cache` | Reutiliza `transcription_data/<video>/<video>.zip` existente si está disponible. |

Flujo CLI por video:
- Subir/procesar mediante `process_video.py`.
- Extraer ZIP en `transcription_data/<video>/`.
- Lanzar publicadores seleccionados vía `ThreadPoolExecutor`.
- Añadir estado de seguimiento en `videos_db.csv` y `processed.csv`.

### Ejecución del servicio Tornado (`app.py`)

🛰️ **El modo API** es útil para sistemas externos que generan bundles ZIP.

Iniciar servidor:

```bash
python app.py --refresh-time 1800 --port 8081
```

Resumen de endpoints API:

| Endpoint | Método | Propósito |
| --- | --- | --- |
| `/publish` | `POST` | Subir bytes ZIP y encolar un trabajo de publicación |
| `/publish/queue` | `GET` | Inspeccionar cola, historial de trabajos y estado de publicación |

### `POST /publish`

📤 **Encola un trabajo de publicación** subiendo bytes ZIP directamente.

- Header: `Content-Type: application/octet-stream`
- Arg query/form requerido: `filename` (nombre del ZIP)
- Booleanos opcionales: `publish_xhs`, `publish_douyin`, `publish_bilibili`, `publish_shipinhao`, `publish_instagram`, `publish_y2b`, `test`
- Body: bytes ZIP en crudo

Ejemplo:

```bash
curl -X POST "http://localhost:8081/publish?filename=demo.zip&publish_xhs=true&publish_instagram=true&publish_y2b=true" \
  --data-binary @demo.zip \
  -H "Content-Type: application/octet-stream"
```

Comportamiento actual en el código:
- La solicitud se acepta y se encola.
- La respuesta inmediata devuelve JSON con `status: queued`, `job_id` y `queue_size`.
- Un thread worker procesa serialmente los trabajos en cola.

### `GET /publish/queue`

📊 **Observa la salud de la cola y los trabajos en curso**.

Devuelve JSON de estado/historial de cola:

```bash
curl "http://localhost:8081/publish/queue"
```

Campos de respuesta incluyen:
- `status`, `jobs`, `queue_size`, `is_publishing`.

### Thread de refresco del navegador

♻️ El refresco periódico del navegador reduce fallos por sesiones obsoletas en ventanas de uptime largas.

`app.py` ejecuta un thread de refresco en segundo plano usando el intervalo `--refresh-time` y hooks de verificación de login. La espera de refresco incluye comportamiento de retraso aleatorio.

### Frontend PWA (`pwa/`)

🖥️ UI estática ligera para subidas manuales de ZIP e inspección de cola.

Ejecutar UI estática local:

```bash
cd pwa
python -m http.server 5173
```

Abre `http://localhost:5173` y configura la URL base del backend (por ejemplo `http://lazyingart:8081`).

Capacidades de la PWA:
- Vista previa ZIP por arrastrar/soltar.
- Toggles de objetivos de publicación + modo test.
- Envía a `/publish` y consulta `/publish/queue`.

---

## Ejemplos

🧪 **Comandos de smoke test para copiar/pegar**:

### Ejemplo 0: Cargar entorno e iniciar servidor API

```bash
source ~/.bashrc
python load_env.py
python app.py --refresh-time 1800 --port 8081
```

### Ejemplo A: Ejecución de publicación CLI

```bash
python autopub.py --pub-xhs --pub-douyin --use-cache
```

### Ejemplo B: Ejecución de publicación API (ZIP único)

```bash
curl -X POST "http://localhost:8081/publish?filename=my_bundle.zip&publish_bilibili=true&test=true" \
  --data-binary @my_bundle.zip \
  -H "Content-Type: application/octet-stream"
```

### Ejemplo C: Consultar estado de la cola

```bash
curl -s "http://localhost:8081/publish/queue"
```

### Ejemplo D: Smoke test de helper SMTP

```bash
python smtp.py
python smtp_test_simple.py
```

---

## Metadata y Formato ZIP

📦 **El contrato ZIP importa**: mantén nombres de archivos y claves de metadata alineados con lo que esperan los publicadores.

Contenido esperado del ZIP (mínimo):

```text
<stem>_metadata.json
<video_filename>.mp4
<cover_filename>.jpg
```

`metadata` impulsa los publicadores CN; `metadata["english_version"]` opcional alimenta el publicador de YouTube.

Campos usados comúnmente por los módulos:
- `title`, `brief_description`, `middle_description`, `long_description`
- `tags` (lista de hashtags)
- `video_filename`, `cover_filename`
- campos específicos de plataforma según implementación en `pub_*.py`

Si generas ZIPs externamente, mantén claves y nombres de archivo alineados con las expectativas de los módulos.

---

## Notas Específicas por Plataforma

🧭 **Mapa de puertos + ownership de módulos** para cada publicador.

| Plataforma | Puerto | Módulo(s) | Notas |
| --- | --- | --- | --- |
| XiaoHongShu | 5003 | `pub_xhs.py`, `login_xiaohongshu.py` | Flujo de re-login por QR; sanitización de títulos y uso de hashtags desde metadata. |
| Douyin | 5004 | `pub_douyin.py`, `login_douyin.py` | Checks de finalización de subida y rutas de reintento son frágiles por plataforma; monitoriza logs de cerca. |
| Bilibili | 5005 | `pub_bilibili.py` | Hooks captcha disponibles vía `solve_captcha_2captcha.py` y `solve_captcha_turing.py`. |
| ShiPinHao (WeChat Channels) | 5006 | `pub_shipinhao.py`, `login_shipinhao.py` | Aprobar QR rápido es importante para la fiabilidad del refresco de sesión. |
| Instagram | 5007 | `pub_instagram.py`, `login_instagram.py` | En modo API se controla con `publish_instagram=true`; hay variables de entorno en `.env.example`. |
| YouTube | 9222 | `pub_y2b.py` | Usa bloque metadata `english_version`; desactiva con `ignore_y2b`. |

---

## Configuración de Servicio Raspberry Pi / Linux

🐧 **Recomendado para hosts always-on**.

Para un bootstrap completo del host, sigue [`setup_raspberrypi.md`](setup_raspberrypi.md).

Configuración rápida del pipeline:

```bash
export AUTOPUB_USER=<USERNAME>
export AUTOPUB_REPO=/home/<USERNAME>/Projects/autopub
sudo -E ./scripts/setup_autopub_pipeline.sh
```

Esto orquesta:
- `scripts/setup_envs.sh`
- `scripts/setup_virtual_desktop_service.sh`
- `scripts/download_and_setup_driver.sh`
- `scripts/setup_autopub_service.sh`

Ejecuta el servicio manualmente en tmux:

```bash
./scripts/start_autopub_tmux.sh
```

Validar servicios/puertos:

```bash
systemctl status autopub.service virtual-desktop.service
sudo ss -ltnp | grep 590
```

---

## Scripts Legacy para macOS

🍎 Los wrappers legacy se mantienen por compatibilidad con setups locales antiguos.

El repositorio aún incluye wrappers legacy orientados a macOS:
- `scripts/run_autopub.sh`
- `scripts/setup_autopub.sh`

Estos contienen rutas absolutas `/Users/lachlan/...` y suposiciones de Conda. Consérvalos si dependes de ese flujo, pero actualiza rutas/venv/tooling para tu host.

---

## Solución de Problemas y Mantenimiento

🛠️ **Si algo falla, empieza aquí**.

- **Deriva de rutas entre máquinas**: si los errores mencionan archivos faltantes bajo `/Users/lachlan/...` o `/home/lachlan/Projects/auto-publish`, alinea constantes con la ruta de tu host (`/home/lachlan/ProjectsLFS/AutoPublish` en este workspace).
- **Higiene de secretos**: ejecuta `~/.local/bin/detect-secrets scan` antes de hacer push. Rota cualquier credencial expuesta.
- **Errores del backend de procesamiento**: si `process_video.py` imprime “Failed to get the uploaded file path,” verifica que el JSON de respuesta de subida contiene `file_path` y que el endpoint de procesamiento devuelve bytes ZIP.
- **Desajuste ChromeDriver**: si aparecen errores de conexión DevTools, alinea versiones de Chrome/Chromium y driver (o cambia a `webdriver-manager`).
- **Problemas de focus del navegador**: `bring_to_front` depende de coincidencia del título de ventana (diferencias de nombre Chromium/Chrome pueden romperlo).
- **Interrupciones por captcha**: configura credenciales de 2Captcha/Turing e integra salidas del solver donde sea necesario.
- **Archivos lock obsoletos**: si ejecuciones programadas nunca arrancan, verifica estado de procesos y elimina `autopub.lock` obsoleto (flujo de scripts legacy).
- **Logs a inspeccionar**: `logs/`, `logs-autopub/`, `~/chromium_dev_session_logs/*.log`, además de logs del journal de servicios.

---

## Extender el Sistema

🧱 **Puntos de extensión** para nuevas plataformas y operaciones más seguras.

- **Agregar una nueva plataforma**: copia un módulo `pub_*.py`, actualiza selectores/flujos, agrega `login_*.py` si se requiere reautenticación QR, luego conecta flags y manejo de cola en `app.py` y el wiring CLI en `autopub.py`.
- **Abstracción de configuración**: migra constantes dispersas a configuración estructurada (`config.yaml`/`.env` + modelo tipado) para operación multi-host.
- **Endurecimiento de almacenamiento de credenciales**: reemplaza flujos sensibles hard-codeados o expuestos por shell con gestión segura de secretos (`sudo -A`, keychain, vault/secret manager).
- **Contenerización**: empaqueta Chromium/ChromeDriver + runtime Python + display virtual en una unidad desplegable para uso cloud/server.

---

## Checklist de Inicio Rápido

✅ **Ruta mínima hacia la primera publicación exitosa**.

1. Clona este repositorio e instala dependencias (`pip install -r requirements.txt` o `requirements.autopub.txt` ligero).
2. Actualiza constantes de ruta hard-codeadas en `app.py`, `autopub.py` y cualquier script que vayas a ejecutar.
3. Exporta credenciales requeridas en tu perfil de shell o `.env`; ejecuta `python load_env.py` para validar la carga.
4. Crea carpetas de perfil de navegador con depuración remota y lanza cada sesión de plataforma requerida una vez.
5. Inicia sesión manualmente en cada plataforma objetivo dentro de su perfil.
6. Inicia modo API (`python app.py --port 8081`) o modo CLI (`python autopub.py --use-cache ...`).
7. Envía un ZIP de muestra (modo API) o un archivo de video de muestra (modo CLI) e inspecciona `logs/`.
8. Ejecuta escaneo de secretos antes de cada push.

---

## Notas de Desarrollo

🧬 **Línea base de desarrollo actual** (formato manual + smoke testing).

- El estilo Python sigue indentación de 4 espacios y formato manual existente.
- Actualmente no hay suite formal de tests automatizados; usa smoke tests:
  - procesa un video de muestra vía `autopub.py`;
  - publica un ZIP a `/publish` y monitorea `/publish/queue`;
  - valida manualmente cada plataforma objetivo.
- Incluye un entrypoint pequeño `if __name__ == "__main__":` al agregar scripts nuevos para dry-runs rápidos.
- Mantén cambios de plataforma aislados cuando sea posible (`pub_*`, `login_*`, toggles `ignore_*`).
- Los artefactos runtime (`videos/*`, `logs*/*`, `transcription_data/*`, `ignore_*`) se espera que sean locales y, en su mayoría, están ignorados por git.

---

## Hoja de Ruta

🗺️ **Mejoras prioritarias reflejadas por restricciones actuales del código**.

Mejoras planificadas/deseadas (según estructura actual del código y notas existentes):

1. Reemplazar rutas hard-codeadas dispersas por configuración central (`.env`/YAML + modelos tipados).
2. Eliminar patrones de contraseña sudo hard-codeada y mover control de procesos a mecanismos más seguros.
3. Mejorar fiabilidad de publicación con reintentos más sólidos y mejor detección de estado UI por plataforma.
4. Expandir soporte de plataformas (por ejemplo Kuaishou u otras plataformas de creadores).
5. Empaquetar runtime en unidades de despliegue reproducibles (contenedor + perfil de display virtual).
6. Añadir checks de integración automatizados para contrato ZIP y ejecución de cola.

---

## Contribuir

🤝 Mantén PRs enfocadas, reproducibles y explícitas sobre supuestos de runtime.

Las contribuciones son bienvenidas.

1. Haz fork y crea una rama enfocada.
2. Mantén commits pequeños e imperativos (estilo de ejemplo en historial: “Wait for YouTube checks before publishing”).
3. Incluye notas de verificación manual en PRs:
   - supuestos de entorno,
   - reinicios de navegador/sesión,
   - logs/capturas relevantes para cambios de flujos UI.
4. Nunca hagas commit de secretos reales (`.env` está ignorado; usa `.env.example` solo para la forma).

Si introduces nuevos módulos de publicación, conecta todo lo siguiente:
- `pub_<platform>.py`
- `login_<platform>.py` opcional
- flags API y manejo de cola en `app.py`
- wiring CLI en `autopub.py` (si aplica)
- manejo de toggles `ignore_<platform>`
- actualizaciones de README

---

## Licencia

Actualmente no hay archivo `LICENSE` presente en este snapshot del repositorio.

Supuesto para este borrador:
- Trata uso y redistribución como indefinidos hasta que el mantenedor agregue un archivo de licencia explícito.

Siguiente acción recomendada:
- Agregar un `LICENSE` en la raíz (por ejemplo MIT/Apache-2.0/GPL-3.0) y actualizar esta sección en consecuencia.

> 📝 Hasta que se agregue un archivo de licencia, considera no resueltas las suposiciones de redistribución comercial/interna y confirma directamente con el mantenedor.

---

## Agradecimientos

- Perfil del mantenedor y sponsor: [@lachlanchen](https://github.com/lachlanchen)
- Fuente de configuración de financiación: [`.github/FUNDING.yml`](.github/FUNDING.yml)
- Servicios del ecosistema referenciados en este repo: Selenium, Tornado, SendGrid, APIs de captcha 2Captcha y Turing.

---

## Apoya AutoPublish

💖 El apoyo de la comunidad financia infraestructura, mejoras de fiabilidad e integraciones con nuevas plataformas.

AutoPublish forma parte de un esfuerzo más amplio para mantener abiertas y hackeables las herramientas de creadores multi-plataforma. Las donaciones ayudan a:

- Mantener en línea la granja Selenium, la API de procesamiento y GPUs cloud.
- Lanzar nuevos publicadores (Kuaishou, Instagram Reels, etc.) además de correcciones de fiabilidad para bots existentes.
- Compartir más documentación, datasets iniciales y tutoriales para creadores independientes.

### Donar

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

También disponible vía:
- GitHub Sponsors: <https://github.com/sponsors/lachlanchen>
- Enlaces del proyecto: <https://lazying.art>, <https://chat.lazying.art>, <https://onlyideas.art>
