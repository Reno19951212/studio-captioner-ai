# Studio Captioner AI — Design Spec

**Date:** 2026-04-08
**Status:** Draft
**Origin:** Fork of VideoCaptioner — stripped to local-only core, new Tauri+React frontend, FastAPI backend

---

## 1. Overview

Studio Captioner AI is an on-premise video captioning tool for small studio/production teams. It provides AI-powered transcription (English), translation (English → Chinese), and subtitle burn-in with a focus on high accuracy (≥97%) through multi-layer verification.

### Core Workflow

```
Video (MXF/MP4) on shared storage
  → ASR (local Whisper GPU)
  → Glossary correction
  → Split + Optimize (local LLM)
  → Translate (local LLM + Glossary + Translation Memory)
  → Back-translation verification + confidence scoring
  → User reviews flagged segments in subtitle editor
  → Burn-in subtitles → Output (MXF/MP4) to shared storage
```

### Key Constraints

- **On-premise only** — no cloud APIs, all models run locally
- **Shared GPU server** — Windows/Linux + NVIDIA GPU, serves the team
- **Shared storage** — server doubles as NAS, files accessed via SMB
- **Queue-based** — FIFO task processing, one at a time
- **Interview/dialogue** — primary video type
- **English input → Chinese subtitle output**

---

## 2. System Architecture

```
GPU Server (Windows/Linux + NVIDIA)
┌─────────────────────────────────────┐
│  FastAPI Backend (:8000)            │
│  ├─ REST API + WebSocket            │
│  ├─ Task Queue (FIFO)               │
│  ├─ SQLite DB (users, tasks, etc.)  │
│  │                                  │
│  ├─ Core Engine (from VideoCaptioner)│
│  │  ├─ ASR (faster-whisper, whisper-cpp)│
│  │  ├─ Split / Optimize / Translate │
│  │  └─ Subtitle Rendering           │
│  │                                  │
│  ├─ New Features                    │
│  │  ├─ Glossary system              │
│  │  ├─ Translation Memory           │
│  │  └─ Back-translation verifier    │
│  │                                  │
│  └─ Shared Storage (SMB)            │
│     ├─ input/   (source videos)     │
│     ├─ output/  (deliverables)      │
│     └─ temp/    (processing)        │
│                                     │
│  [Optional] Tauri App (localhost)   │
└─────────────────────────────────────┘
         ↑ HTTP/WS          ↑ SMB
         │                  │
    Team members via Tauri desktop app
    (macOS / Windows)
```

### Data Flow Principle

- API transmits **file paths only**, never file contents
- Backend reads/writes directly from shared storage
- Frontend reads video for preview via HTTP range streaming from backend
- Path mapping: frontend translates local SMB mount path ↔ server-side path

---

## 3. Repo Structure

Monorepo with backend and frontend in a single repository.

```
studio-captioner-ai/
├── backend/
│   ├── pyproject.toml
│   ├── app/                      # FastAPI application
│   │   ├── main.py               # Entry point
│   │   ├── config.py             # Server configuration
│   │   ├── database.py           # SQLite setup
│   │   ├── api/                  # REST routes
│   │   │   ├── tasks.py          # Task CRUD + queue
│   │   │   ├── users.py          # User management
│   │   │   ├── glossary.py       # Glossary CRUD
│   │   │   ├── subtitles.py      # Subtitle edit/export
│   │   │   ├── styles.py         # Style presets
│   │   │   ├── preview.py        # Video streaming
│   │   │   └── settings.py       # Server settings
│   │   ├── ws/                   # WebSocket handlers
│   │   │   ├── progress.py       # Task progress push
│   │   │   └── queue_status.py   # Queue status push
│   │   ├── services/             # Business logic
│   │   │   ├── task_queue.py     # FIFO queue manager
│   │   │   ├── pipeline.py       # Pipeline orchestrator
│   │   │   ├── path_resolver.py  # SMB path mapping
│   │   │   └── auth.py           # JWT auth
│   │   └── models/               # SQLAlchemy + Pydantic
│   │       ├── task.py
│   │       ├── user.py
│   │       ├── glossary.py
│   │       └── translation_memory.py
│   │
│   ├── core/                     # ← Extracted from VideoCaptioner
│   │   ├── asr/                  # faster_whisper, whisper_cpp only
│   │   ├── split/
│   │   ├── optimize/
│   │   ├── translate/            # LLM translator only
│   │   ├── subtitle/
│   │   ├── llm/
│   │   ├── prompts/
│   │   └── utils/
│   │
│   ├── features/                 # New feature modules
│   │   ├── glossary/
│   │   │   ├── manager.py        # CRUD operations
│   │   │   ├── injector.py       # Inject terms into LLM prompts
│   │   │   └── importer.py       # CSV/Excel import
│   │   ├── translation_memory/
│   │   │   ├── store.py          # TM storage + retrieval
│   │   │   └── matcher.py        # Fuzzy sentence matching
│   │   └── back_translation/
│   │       ├── verifier.py       # Back-translate + compare
│   │       └── confidence.py     # Confidence scoring
│   │
│   ├── resource/                 # ← From VideoCaptioner
│   │   ├── fonts/
│   │   └── subtitle_style/
│   │
│   └── tests/
│       ├── test_core/
│       ├── test_api/
│       ├── test_features/
│       └── test_services/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src-tauri/                # Tauri v2 (Rust)
│   │   ├── Cargo.toml
│   │   ├── tauri.conf.json
│   │   └── src/
│   │       ├── main.rs
│   │       └── commands.rs       # Native file dialogs, etc.
│   │
│   ├── src/                      # React app
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── NewTask.tsx
│   │   │   ├── Editor.tsx
│   │   │   ├── Glossary.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── History.tsx
│   │   ├── components/
│   │   │   ├── editor/
│   │   │   │   ├── Timeline.tsx
│   │   │   │   ├── Waveform.tsx
│   │   │   │   ├── SubtitleList.tsx
│   │   │   │   ├── VideoPlayer.tsx
│   │   │   │   └── StylePanel.tsx
│   │   │   ├── queue/
│   │   │   │   ├── QueueList.tsx
│   │   │   │   └── ProgressBar.tsx
│   │   │   └── common/
│   │   │       ├── Layout.tsx
│   │   │       └── Sidebar.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useTaskQueue.ts
│   │   │   └── useSubtitle.ts
│   │   ├── services/
│   │   │   ├── api.ts            # REST client
│   │   │   └── ws.ts             # WebSocket client
│   │   ├── store/
│   │   │   ├── taskStore.ts
│   │   │   ├── editorStore.ts
│   │   │   └── settingsStore.ts
│   │   └── types/
│   │       ├── task.ts
│   │       ├── subtitle.ts
│   │       └── glossary.ts
│   └── public/
│
├── .gitignore
├── README.md
└── docker-compose.yml            # Optional backend deployment
```

---

## 4. Backend — FastAPI Design

### 4.1 REST API Endpoints

#### Auth (Simple user identification)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create user (name + password) |
| POST | `/api/auth/login` | Login, returns JWT token |

#### Tasks

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tasks` | Submit new task (video path + config + glossary_id) |
| GET | `/api/tasks` | List user's tasks (paginated, filterable) |
| GET | `/api/tasks/{id}` | Task detail (status, result paths) |
| DELETE | `/api/tasks/{id}` | Cancel queued task |
| GET | `/api/queue` | Queue status (count, current task) |

#### Subtitles

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tasks/{id}/subtitles` | Get subtitle data (ASRData JSON) |
| PUT | `/api/tasks/{id}/subtitles` | Save edited subtitles |
| POST | `/api/tasks/{id}/export` | Export subtitle file (SRT/ASS/VTT) |
| POST | `/api/tasks/{id}/synthesize` | Burn subtitles into video (MXF/MP4) |

#### Glossary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/glossaries` | List all glossaries |
| POST | `/api/glossaries` | Create glossary |
| PUT | `/api/glossaries/{id}` | Update glossary |
| DELETE | `/api/glossaries/{id}` | Delete glossary |
| POST | `/api/glossaries/{id}/import` | Import from CSV/Excel |
| GET | `/api/glossaries/{id}/export` | Export to CSV |

#### Preview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/preview/{task_id}/video` | Video streaming (HTTP range) |
| GET | `/api/preview/{task_id}/waveform` | Audio waveform peaks (JSON) |
| GET | `/api/preview/{task_id}/thumbnail` | Video thumbnail |

#### Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/settings` | Get server settings |
| PUT | `/api/settings` | Update settings |
| GET | `/api/settings/models` | List available ASR/LLM models |

### 4.2 WebSocket Channels

**`ws://server:8000/ws/tasks/{id}`** — Single task progress

```json
{
  "stage": "translate",
  "progress": 65,
  "detail": "Batch 3/5",
  "confidence_flags": [12, 45]
}
```

**`ws://server:8000/ws/queue`** — Global queue status

```json
{
  "queue_length": 3,
  "current_task": {
    "id": "abc123",
    "user": "Alice",
    "stage": "optimize",
    "progress": 80
  }
}
```

### 4.3 Task Processing Pipeline

```
POST /api/tasks (video_path, config, glossary_id)
  → FIFO Queue
  → ASR (Whisper on GPU)
  → Glossary post-correction (fix proper nouns)
  → Split + Optimize (LLM)
  → Translate (LLM + Glossary injection + Translation Memory lookup)
  → Back-translation verification + confidence scoring
  → Status: "ready_for_review" (low-confidence segments flagged)
  
User reviews in editor, then:
  POST /api/tasks/{id}/synthesize
  → Burn subtitles → Output to shared storage
```

### 4.4 Database (SQLite)

**Users table:** id, name, password_hash, created_at

**Tasks table:** id, user_id, status (queued/processing/ready_for_review/completed/failed), video_path, output_path, config_json, created_at, completed_at

**Glossaries table:** id, name, created_by, created_at

**Glossary entries table:** id, glossary_id, source_term, target_term

**Translation memory table:** id, source_text, target_text, confirmed_by, created_at, source_hash (for fuzzy matching)

---

## 5. Frontend — Tauri v2 + React

### 5.1 Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop shell | Tauri v2 (Rust) |
| UI framework | React 18 + TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| State management | Zustand |
| Waveform | wavesurfer.js |
| Video player | vidstack or plyr |
| Build | Vite |

### 5.2 Pages

**Dashboard** — Queue status cards (processing/queued/completed/needs review), current task progress bar, queue list, quick links to tasks needing review.

**New Task** — Browse shared storage for video files, select ASR engine and settings, choose glossary, set output format (MXF/MP4), submit to queue.

**Subtitle Editor** (core feature) — Three-panel layout:
- Left: Video player with subtitle overlay preview
- Right: Subtitle list (bilingual EN/ZH), tabbed with Style panel and Glossary panel
- Bottom: Audio waveform timeline with subtitle region markers, drag-to-adjust timing, playhead sync

Key editor features:
- Click subtitle entry → video jumps to that timecode
- Low-confidence segments highlighted in red with ⚠ marker
- Inline text editing for both source and translation
- Drag subtitle boundaries on waveform to adjust timing
- Style panel: font, size, color, outline, shadow, background, position
- Keyboard shortcuts for efficient proofreading (next/prev segment, play segment, confirm)

**Glossary** — List/create/edit glossaries, add/edit/delete terms, CSV/Excel import/export, search and filter.

**History** — Past tasks with status, filterable by user and date, click to reopen in editor.

**Settings** — Server address, shared storage path mapping (local mount ↔ server path), default ASR model, default LLM model, output presets, user profile.

### 5.3 Real-time Sync

- WebSocket connection established on app launch
- Queue status updates push to Dashboard automatically
- Task progress push updates progress bars in real-time
- Subtitle editor saves trigger PUT request; optimistic UI updates

---

## 6. New Features

### 6.1 Glossary System

**Purpose:** Maintain terminology consistency across ASR correction, translation, and optimization.

**Data model:**
```
Glossary
  ├── id, name, description
  └── entries[]
      ├── source_term (English): "Fed", "APAC", "Chairman Powell"
      └── target_term (Chinese): "聯儲局", "亞太區", "鮑威爾主席"
```

**Integration points:**
1. **Post-ASR correction** — After ASR completes, scan output for source terms and fix spelling/casing
2. **Translation prompt injection** — Inject relevant glossary entries into the LLM translation prompt as context
3. **Optimization verification** — Cross-check that glossary terms are correctly used in final output

**Management:** CRUD via API, CSV/Excel import/export, per-task glossary selection.

### 6.2 Translation Memory (TM)

**Purpose:** Store confirmed translation pairs for reuse, reducing repeated translation of identical/similar sentences.

**How it works:**
1. When user confirms a subtitle (in editor or after review), the EN→ZH pair is stored
2. Before translating a new segment, the system searches TM for similar source sentences
3. If a match is found (fuzzy threshold configurable, default ≥85% similarity), the stored translation is suggested or auto-applied
4. TM matches bypass LLM translation, saving time and ensuring consistency

**Matching:** Source text hashing for exact match + fuzzy string similarity (e.g., Levenshtein ratio) for near matches.

**Storage:** SQLite table with source_text, target_text, source_hash, confirmed_by, created_at.

### 6.3 Back-Translation Verification

**Purpose:** Automatically verify translation quality by translating the Chinese output back to English and comparing with the original.

**Pipeline:**
1. For each translated segment: translate ZH → EN using the same local LLM
2. Compare back-translated English with original English source
3. Compute similarity score (semantic similarity via LLM or string-based metrics)
4. Segments below threshold (configurable, default <90% similarity) are flagged as low-confidence

**Output:** Each subtitle segment gets a confidence score. Low-confidence segments are visually flagged in the editor (red highlight, ⚠ icon), directing the user's attention to the segments most likely to need correction.

**Re-processing:** Low-confidence segments can be automatically re-translated with adjusted prompts (e.g., including more context, stricter glossary enforcement) before flagging for human review.

---

## 7. Accuracy Strategy (Target ≥97%)

Multi-layer approach to maximize automated accuracy:

```
Layer 1: ASR (~96% for English interviews)
  └─ Whisper large-v3 on GPU
  └─ VAD preprocessing (Silero)
  └─ Glossary post-correction → ~97% ASR accuracy

Layer 2: Translation
  └─ Glossary injection into prompts
  └─ Translation Memory lookup (exact/fuzzy)
  └─ Context-aware translation (surrounding segments included)
  └─ → ~93-95% translation accuracy

Layer 3: Verification
  └─ Multi-round LLM optimization (up to 3 iterations)
  └─ Back-translation verification
  └─ Auto re-translate low-confidence segments
  └─ → ~96-97% accuracy

Layer 4: Smart Flagging
  └─ Remaining low-confidence segments highlighted
  └─ User reviews only flagged items (not every line)
  └─ Confirmed pairs saved to Translation Memory
```

---

## 8. Output Formats

### Video Output

**MP4:**
- Codec: H.264 (default) or H.265
- Quality presets: ultra (CRF 18), high (CRF 23), medium (CRF 28)
- Audio: AAC pass-through

**MXF — DNxHD/DNxHR (primary):**
- DNxHR LB — low bitrate, preview use
- DNxHR SQ — standard quality
- DNxHR HQ — high quality
- DNxHR HQX — 10-bit high quality
- Audio: PCM pass-through

**MXF — XDCAM HD422 (secondary):**
- MPEG-2 422P@HL, 50 Mbps
- Up to 1080i/1080p
- Audio: PCM pass-through

### Subtitle Output

- SRT (SubRip)
- ASS (Advanced SubStation Alpha)
- VTT (WebVTT)

### Subtitle Styling

Fully customizable:
- Font family, size, weight
- Color (primary + outline + shadow)
- Outline thickness, shadow offset
- Background box (on/off, color, opacity, border radius for rounded mode)
- Position (top/middle/bottom, left/center/right)
- Two render modes: ASS (traditional) and Rounded (modern box background)

---

## 9. Codebase Migration — Keep / Modify / Remove

### Remove (~70+ files)

| Path | Reason |
|------|--------|
| `videocaptioner/cli/` (12 files) | Replaced by Tauri frontend |
| `videocaptioner/ui/` (45+ files) | Replaced by Tauri+React frontend |
| `videocaptioner/core/tts/` (7 files) | TTS not needed; all cloud services |
| `core/asr/bcut.py` | Bilibili cloud ASR |
| `core/asr/jianying.py` | ByteDance cloud ASR |
| `core/asr/whisper_api.py` | OpenAI cloud Whisper API |
| `core/translate/bing_translator.py` | Bing cloud translation |
| `core/translate/google_translator.py` | Google cloud translation |
| `core/translate/deeplx_translator.py` | DeepLX external translation service |
| `docs/`, `README.md` | Original project docs/branding |
| `tests/test_cli/`, `test_thread/`, `test_tts/` | Tests for removed modules |
| Tests for cloud ASR/translators | Tests for removed engines |

### Modify (8 files)

| File | Changes |
|------|---------|
| `core/asr/transcribe.py` | Remove bijian/jianying/whisper_api references |
| `core/asr/__init__.py` | Remove cloud engine imports |
| `core/translate/factory.py` | Remove Bing/Google factory methods |
| `core/translate/types.py` | Remove Bing/Google language mappings |
| `core/entities.py` | Remove cloud enums from TranscribeModelEnum, TranslatorServiceEnum |
| `pyproject.toml` | Remove yt-dlp, PyQt5; update project name/metadata |
| `videocaptioner/__main__.py` | Change to launch FastAPI server |
| `videocaptioner/config.py` | Update project name, paths, version |

### Keep (~40+ files)

All core processing modules:
- `core/asr/` — asr_data.py, base.py, faster_whisper.py, whisper_cpp.py, chunked_asr.py, chunk_merger.py, status.py
- `core/split/` — all files
- `core/optimize/` — all files
- `core/translate/` — base.py, llm_translator.py
- `core/subtitle/` — all files (ass_renderer, rounded_renderer, style_manager, etc.)
- `core/llm/` — all files (client, context, check_llm, request_logger)
- `core/prompts/` — all prompt templates
- `core/utils/` — all files (cache, logger, video_utils, text_utils, etc.)
- `resource/` — fonts, subtitle_style presets

### New Modules

| Module | Purpose |
|--------|---------|
| `app/` | FastAPI application layer (API, WS, services, models) |
| `features/glossary/` | Glossary management + prompt injection |
| `features/translation_memory/` | TM storage + fuzzy matching |
| `features/back_translation/` | Back-translation verification + confidence scoring |
| `frontend/` | Tauri v2 + React application |

---

## 10. Technology Summary

### Backend

| Component | Technology |
|-----------|-----------|
| API framework | FastAPI |
| Database | SQLite + SQLAlchemy |
| Auth | JWT (simple) |
| Task queue | In-process FIFO (asyncio.Queue) |
| ASR | faster-whisper / whisper.cpp (local, CUDA) |
| LLM | Ollama (local, future) / OpenAI-compatible API |
| Video processing | FFmpeg |
| Caching | diskcache |

### Frontend

| Component | Technology |
|-----------|-----------|
| Desktop shell | Tauri v2 (Rust) |
| UI framework | React 18 + TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| State management | Zustand |
| Waveform | wavesurfer.js |
| Video player | vidstack or plyr |
| Build tool | Vite |
