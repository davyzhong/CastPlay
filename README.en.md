> ⚠️ 本翻译最后更新于 2026-09-21，主 README 于 2026-09-23 有多项修复未同步至此；最新内容以 [主文档](./README.md) 为准。

---
name: CastPlay All-in-One
description: Single-container digital signage management — FastAPI backend + React admin + Android player, no Redis/Celery/PostgreSQL required. Tuned for fleets under 50 screens.
license: MIT
homepage: https://github.com/davyzhong/CastPlay
platforms:
  - Linux / macOS / Windows (server)
  - Web (admin + player)
  - Android 8.0+ (player client)
language: Python 3.10+ / TypeScript (React) / Kotlin (Android)
model: gpt-4 / claude-sonnet / gemini-2.5
intent: code-generation / question-answering / agent-tool
capabilities:
  - install
  - quickstart
  - deploy
  - api-reference
  - docker
  - troubleshoot
tags:
  - digital-signage
  - fastapi
  - react
  - typescript
  - android
  - kotlin
  - websocket
  - ppt-to-video
  - docker
  - small-fleet
  - self-hosted
  - kiosk
---

<div align="center">

# 🖥️ CastPlay All-in-One

**Single-container digital signage that boots in 10 seconds — manage screens, upload media, push playlists from one web console.**

`Upload media` → `Build playlist` → `Push to devices` → `Screens reflect changes within 2 s`

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-success)](https://github.com/davyzhong/CastPlay/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)](https://www.python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](Dockerfile)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20SQLAlchemy-009688)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/admin-React%2018%20%2B%20Ant%20Design-61dafb)](https://react.dev)
[![Player](https://img.shields.io/badge/player-Android%20WebView-3DDC84)](android/)
[![Security](https://img.shields.io/badge/security-policy-lightgrey)](SECURITY.md)

**Languages**: [English](./README.md) · [中文](./README.zh.md)

[Quick Start](#-quick-start) · [Install](#-install) · [Architecture](#-architecture) · [API](#-api-surface) · [Android Player](#-android-player) · [Comparison](#-comparison) · [Contributing](#-contributing)

</div>

---

> Run a sign network from one process — admin web, REST + WebSocket API, multi-format media (image / video / PPT), and a kiosk-mode Android client — without standing up Redis, Celery, or PostgreSQL.

---

## ✨ Why CastPlay

- **🚀 Single container, zero external deps** — `docker run castplay` and you have admin + API + WebSocket up. No Redis, no Celery, no separate database server.
- **🖼️ Multi-format media, including PPT** — drop in `.pptx` and CastPlay converts it to a video on the server side (LibreOffice + ffmpeg) while keeping every original slide animation.
- **📡 Live push to every screen** — playlists and schedule changes are dispatched over WebSocket; clients reflect changes within ≈ 2 s without polling.
- **📱 Kiosk-locked Android player** — `MainActivity.kt` is a WebView host with `DevicePolicyManager` kiosk mode, so the device stays on your content.
- **📅 Schedule + timezone aware** — daily on/off windows per device, multiple timezones, automatic fallback to a default playlist.
- **🔍 Tuned for fleets under 50** — SQLite-backed, APScheduler-driven, 3 worker threads. Doesn't sprawl the way a Redis/Celery/PG stack does at this scale.

---

## 🚀 Quick Start

### 30 seconds — try it with Docker

```bash
docker run -d \
  --name castplay \
  -p 8000:8000 \
  -v castplay-data:/app/data \
  ghcr.io/davyzhong/castplay:latest
# Or build locally:
# docker build -t castplay:latest . && docker compose up -d
```

Open <http://localhost:8000/> for the admin console, <http://localhost:8000/player.html> for the web player preview.

### 60 seconds — from source (no Docker)

```bash
# 1. Clone
git clone https://github.com/davyzhong/CastPlay.git
cd CastPlay

# 2. Install system prerequisites (Ubuntu/Debian names)
sudo apt-get update && sudo apt-get install -y libreoffice ffmpeg

# 3. Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py

# 4. Frontend (for local development)
cd frontend && npm install && npm run build && cd ..
# (Pre-built assets are committed; you can skip the build for a quick look.)

# 5. Run
python scripts/run.py
# or: make dev
```

- **Admin console** → <http://localhost:8000/>
- **Player simulator** → <http://localhost:8000/player.html>
- **OpenAPI docs** → <http://localhost:8000/docs>

### Default credentials

The bootstrap seeds an admin on first run:

```
username: admin
password: changeme    # rotate in production via .env
```

> See [`docs/deployment/guide.md`](docs/deployment/guide.md) for the hardening checklist.

---

## 📸 Visual Tour

> ⚠️ Real screenshots are queued as `[TODO]` placeholders. Capture them from your running instance and commit into `docs/screenshots/` — placeholders resolve automatically.

### Admin console

<p align="center">
  <a href="docs/screenshots/dashboard.png"><img src="docs/screenshots/dashboard.png" width="320" alt="CastPlay admin dashboard: fleet status cards (online / offline / total devices), recent uploads, last push timestamps."></a>
  <a href="docs/screenshots/playlists.png"><img src="docs/screenshots/playlists.png" width="320" alt="Playlist editor: media tiles in a drag-and-drop order rail, per-item duration slider, device assignment dropdown."></a>
</p>
<p align="center"><sub><em>[TODO: dashboard.png] · [TODO: playlists.png]</em></sub></p>

### Media library + Android player

<p align="center">
  <a href="docs/screenshots/media.png"><img src="docs/screenshots/media.png" width="320" alt="Media library: grid of uploaded images, videos, and converted PPT thumbnails with status badges."></a>
  <a href="docs/screenshots/android-player.png"><img src="docs/screenshots/android-player.png" width="320" alt="Android player on a 10-inch display showing a fullscreen image followed by a video, with no system chrome."></a>
</p>
<p align="center"><sub><em>[TODO: media.png] · [TODO: android-player.png]</em></sub></p>

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Browser[Admin browser]
        Admin[Admin console<br/>React 18 + Ant Design]
        PlayerWeb[Web player simulator<br/>player.html]
    end
    subgraph Server[CastPlay server — single process]
        API[REST API<br/>FastAPI]
        WS[WebSocket<br/>/ws/{device_id}]
        Sched[Scheduler<br/>APScheduler · 3 workers]
        PptSvc[PPT conversion<br/>LibreOffice + ffmpeg]
        DB[(SQLite<br/>SQLAlchemy ORM)]
        Files[Local FS<br/>uploads / converted / thumbnails]
    end
    subgraph Devices[Player clients]
        Web[Browser-based player]
        Android[Android WebView<br/>Kiosk mode · CacheManager]
    end
    Admin -->|REST + WebSocket| API
    PlayerWeb -->|REST + WebSocket| API
    Web -->|REST + WebSocket| API
    Android -->|REST + WebSocket| API
    Sched --> API
    PptSvc --> Files
    API --> DB
    API --> Files
    WS --> Devices
```

**Push path**: admin → REST `POST /api/playlists/{id}/devices/{deviceId}` → WebSocket fan-out → connected clients receive the diff and rebuild their playlist.

---

## 📦 Features

### 🖼️ Media management

- 🧩 **Multi-format ingest** — JPG/PNG/GIF images, MP4/AVI/MOV videos, and PPT/PPTX decks in one queue.
- 🎞️ **PPT → video pipeline** — LibreOffice converts the deck, Poppler renders each page, ffmpeg stitches the result into an MP4.
- 🔁 **Retry per file** — failed conversions expose a single-click retry button in the admin UI (`POST /api/media/{id}/retry`).
- 🔍 **Content validation** — extension check *and* magic-number check; mismatches are rejected before they hit disk.
- 🖼️ **Thumbnail generation** — Pillow renders previews for images and the first slide of PPT decks.

### 📋 Playlists & devices

- 🎯 **Drag-and-drop reordering** — `@dnd-kit` on the admin side; ordering is persisted via `PUT /api/playlists/{id}/items/reorder`.
- 📡 **Push in ≈ 2 s** — changes fan out over WebSocket; devices never have to poll.
- 🎚️ **Per-item duration** — set how long each tile plays; defaults to 8 s if unset.
- 🎞️ **Web player simulator** — preview an entire playlist in the browser before assigning it (`/player.html`).
- 📅 **Schedule-aware** — daily on/off windows per device, multi-timezone support, automatic fallback to a default playlist.

### 🛡️ Operations

- 🖥️ **Device registration** — MAC-address-keyed registry with `registration_code` for token auth in production.
- 🔐 **JWT auth + bcrypt** — token rotation via `/api/auth/refresh`; rotate `SECRET_KEY` from `.env`.
- 🧹 **Self-cleaning storage** — Android `CacheManager.kt` evicts non-essential files before storage fills up.
- 🚦 **3-worker scheduler** — bounded concurrency for PPT conversions plus schedule evaluation per tick.
- 🔁 **Auto-reconnect** — devices recover from network drops; WebSocket heartbeats keep liveness truthful.

### 📱 Players

- 🌐 **Browser player** — `frontend/player.html` runs the same code the Android WebView ships.
- 🤖 **Android player** — `MainActivity.kt` is a WebView host with `DevicePolicyManager` kiosk mode and `CacheManager.kt` for offline-first media.

---

## 🔧 Install

### 1. System prerequisites

| Tool | Why | Verified version |
|---|---|---|
| Python | 3.10+ | 3.10 / 3.11 / 3.12 |
| Node.js | admin dev mode | 18+ |
| LibreOffice | PPT → PDF | 7+ |
| ffmpeg | media stitching | 4.4+ |
| Docker (optional) | one-shot deploy | 24+ |

### 2. Install paths

#### Docker (recommended)

```bash
docker compose up -d             # uses docker-compose.yml
# or
docker build -t castplay . && docker run -d -p 8000:8000 -v castplay-data:/app/data castplay
```

#### Pip + npm (developer mode)

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/run.py

# Frontend (optional — prebuilt assets ship in repo)
cd frontend && npm install && npm run dev
```

#### Make (developer convenience)

```bash
make install          # pip + npm install
make dev              # backend + frontend in parallel
make test             # pytest
make lint             # black + isort + mypy + pylint
make docker-build     # build container image
make docker-run       # docker compose up
```

### 3. Configuration

CastPlay reads from environment variables (`.env` or container env):

```bash
DATABASE_PATH=/app/data/castplay.db   # SQLite path
SECRET_KEY=...                        # JWT signing secret
DEBUG=false                           # disable verbose logging in prod
NUM_WORKERS=3                         # APScheduler thread pool size
ENVIRONMENT=production                # tighten auth checks when "production"
```

> Full reference: [`docs/deployment/guide.md`](docs/deployment/guide.md) and `.env.example`.

---

## 🌐 API surface

REST routes are mounted under `/api/`. The OpenAPI explorer lives at `/docs` (Swagger UI) and `/redoc`.

| Group | Endpoints (highlights) | Notes |
|---|---|---|
| **Auth** | `POST /auth/token`, `POST /auth/refresh`, `GET /auth/me` | JWT bearer |
| **Devices** | `POST /devices/register`, `GET /devices`, `PUT /devices/{id}/disable`, `* /schedule` | MAC-keyed registration |
| **Media** | `POST /media/upload`, `GET /media`, `DELETE /media/{id}`, `POST /media/{id}/retry` | multipart upload + thumbnails |
| **Playlists** | `POST /playlists`, `* /items`, `PUT /items/reorder`, `POST /playlists/{id}/devices/{deviceId}` | drag-and-drop ordering persisted |
| **Schedules** | `GET/PUT /devices/{id}/schedule` | per-device daily on/off windows |
| **Player** | `GET /playlists/{deviceId}`, `GET /config/{deviceId}`, `POST /status/{deviceId}` | read-side for clients |
| **WebSocket** | `WS /ws/{deviceId}` | playlist diffs + heartbeat |

> Full schema: <http://localhost:8000/docs> after first launch.

---

## 📱 Android Player

The Android player is a thin Kotlin shell around the same web player used in the browser:

- **WebView host** — [`MainActivity.kt`](android/app/src/main/java/com/castplay/player/MainActivity.kt) loads the web player with a runtime-injected `deviceId`.
- **Kiosk mode** — `MyDeviceAdminReceiver.kt` + `DevicePolicyManager` lock the device to the player; `BootReceiver.kt` restarts on power-up.
- **Offline cache** — `CacheManager.kt` downloads the assigned playlist's media ahead of time and verifies MD5, with an exponential-backoff retry budget of 3.
- **JsBridge** — exposes MAC, IP, registration code, download progress, and network status to the WebView.

Build:

```bash
# Default backend URL (edit android/app/build.gradle.kts to override)
./build-android.sh

# Or point at your own server:
./build-android.sh http://192.168.1.100:8000
```

Output: `android/app/build/outputs/apk/debug/app-debug.apk` (~20–30 MB).

> Detailed Android walkthrough: [`docs/android/deployment_guide.md`](docs/android/deployment_guide.md).

---

## 🆚 Comparison

| Metric | CastPlay 2.0 | CastPlay v1 (legacy) | A commercial CMS |
|---|---|---|---|
| External dependencies (Redis/Celery/PG) | **none** | required | required |
| Time to first deploy (clean VM) | **5 min** | 30 min | 30+ min |
| Cold-start time | **≈ 10 s** | ≈ 2 min | ≈ 30 s |
| Python source files | **36** | 79 | n/a |
| LOC vs v1 | **−34 %** | baseline | n/a |
| Fleet sweet spot | **< 50 screens** | small-mid | mid-large |
| License | **MIT** | per-seat | subscription |
| WebSocket push (no polling) | ✅ | ✅ | ✅ |

---

## 🗓️ Roadmap

- [x] **v2.0** — bootstrap architecture; zero external deps; 3-worker scheduler; drag-and-drop playlist ordering; WebSocket push; Android kiosk player.
- [ ] **v2.1** — Optional Postgres + Redis adapter for fleets > 50 (legacy compatibility layer).
- [ ] **v2.2** — Multi-user roles (admin / editor / viewer) and per-device permission scopes.
- [ ] **v2.3** — Tiles for weather, RSS, and live data widgets in playlists.
- [ ] **v2.4** — tvOS player for Apple TV screens.

> See [`docs/reports/PROJECT_REVIEW_REPORT.md`](docs/reports/PROJECT_REVIEW_REPORT.md) for the most recent code review, and [`OPTIMIZATION.md`](OPTIMIZATION.md) for follow-up ideas captured during that review.

---

## 🧪 Testing

```bash
# All tests
make test                            # = pytest tests/ -v

# Grouped runs
make test-unit                       # pytest -m unit
make test-integration                # pytest -m integration
make test-e2e                        # frontend end-to-end
make test-performance                # Locust 100 users / 60 s

# Coverage report
make test-coverage                   # htmlcov/index.html + coverage.xml
```

Continuous integration expectations live in [`docs/testing/`](docs/testing/).

---

## 🤝 Contributing

Pull requests welcome — start by reading [`CLAUDE.md`](CLAUDE.md) for the build / test conventions. High-leverage contributions:

- **Bug reports** — include the OS, CastPlay version, `docker compose ps` output, and a snippet from `logs/`.
- **Translations** — `frontend/src/locales/` ships `zh-CN` + `en-US`; add another locale and ping a maintainer.
- **API patches** — write a test under `tests/integration/` first; the OpenAPI spec at `/docs` will be regenerated from the code.
- **Android player fixes** — bring up an emulator via [`docs/android/emulator_setup.md`](docs/android/emulator_setup.md).

This project follows the spirit of the [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

---

## 🔒 Security

Found a vulnerability? **Do not** open a public issue. See [`SECURITY.md`](SECURITY.md) for the supported-versions table, disclosure window, and the private contact channel.

CastPlay's threat posture:

- **JWT bearer auth** — rotate `SECRET_KEY` from `.env`; tokens are short-lived with a refresh path.
- **`registration_code` token** — production mode (set `ENVIRONMENT=production`) requires the registration code on every WebSocket connect (codes `4001`/`4003`/`4004` reject unauthorized clients).
- **WebSocket origin allowlist** — production mode scopes accepted origins to the configured admin host.
- **Hardened defaults** — `DEBUG=false`, `NUM_WORKERS=3`, no analytics, no third-party CDN.
- **Content validation** — file uploads are extension-checked *and* magic-number-checked before they touch disk.

---

## ⚖️ Legal

This project is provided under the [MIT License](LICENSE). It does not ship any third-party sample media — supply your own.

---

<div align="center">

<sub>📌 CastPlay is maintained by <a href="https://github.com/davyzhong">qiming</a> · <a href="https://github.com/davyzhong/CastPlay/issues">🐛 Report a bug</a> · <a href="https://github.com/davyzhong/CastPlay/discussions">💬 Discuss</a></sub>

</div>
