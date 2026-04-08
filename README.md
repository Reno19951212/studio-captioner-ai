# Studio Captioner AI

本地部署的 AI 影片字幕工具，專為工作室團隊設計。支援英文語音辨識、繁體中文翻譯、字幕編輯、以及字幕燒錄輸出。

## 功能一覽

### 核心功能

- **語音辨識 (ASR)** — 使用本地 Whisper 模型（whisper.cpp），支援 Apple Silicon Metal GPU 加速。可選擇 tiny / base / small / medium / large-v2 模型
- **英文轉繁體中文翻譯** — 透過 Ollama 運行本地 LLM（qwen2.5:7b），逐句將英文字幕翻譯為繁體中文
- **完整字幕編輯器** — 影片預覽、雙語字幕列表（英文+繁體中文）、波形時間軸、inline 文字編輯
- **字幕樣式自訂** — 字體、大小、顏色、描邊、背景框、位置等全部可調
- **字幕燒錄輸出** — 將字幕燒錄到影片中，支援 MP4（H.264）及 MXF（DNxHD）格式
- **字幕匯出** — SRT / ASS / VTT 格式

### 準確率提升功能

- **術語表 (Glossary)** — 管理專有名詞對照表（如 Fed → 聯儲局），支援 CSV 匯入匯出。ASR 後自動修正拼寫，翻譯時注入 LLM prompt
- **翻譯記憶 (Translation Memory)** — 儲存已確認的翻譯對照，支援精確匹配及模糊匹配（≥85% 相似度），減少重複翻譯
- **回譯驗證 (Back-Translation)** — 將中文翻譯回譯為英文並與原文比對，計算信心分數，自動標記低信心段落
- **單句重翻** — 喺編輯器中可對個別字幕段落進行即時重新翻譯

### 協作功能

- **多用戶支援** — JWT 認證，每個用戶有獨立嘅任務歷史
- **任務隊列** — FIFO 排隊處理，先到先做
- **即時進度** — 透過 WebSocket 即時推送 ASR / 翻譯進度到前端
- **共享存儲** — 影片存放在共享 NAS/SMB 上，API 只傳路徑，免去大檔案上傳

## 系統架構

```
GPU 伺服器 (Windows/Linux + NVIDIA 或 macOS + Apple Silicon)
┌───────────────────────────────────────────┐
│  FastAPI Backend (:8000)                  │
│  ├─ REST API + WebSocket                  │
│  ├─ 任務隊列 (FIFO)                       │
│  ├─ SQLite 資料庫                          │
│  │                                        │
│  ├─ Core Engine                           │
│  │  ├─ ASR (whisper.cpp / faster-whisper) │
│  │  ├─ 智能斷句 + LLM 優化                │
│  │  ├─ LLM 翻譯 (Ollama)                 │
│  │  └─ 字幕渲染 (FFmpeg)                  │
│  │                                        │
│  ├─ Features                              │
│  │  ├─ 術語表系統                          │
│  │  ├─ 翻譯記憶                            │
│  │  └─ 回譯驗證                            │
│  │                                        │
│  └─ 共享存儲 (SMB)                         │
└───────────────────────────────────────────┘
         ↑ HTTP/WS           ↑ SMB
    團隊成員透過 Tauri 桌面應用連接
```

### 前後端配合方式

| 層 | 技術 | 職責 |
|---|---|---|
| **前端** | Tauri v2 + React 18 + TypeScript | 桌面應用殼、頁面路由、即時 UI 更新 |
| **通訊** | REST API + WebSocket | 任務管理用 REST，進度推送用 WebSocket |
| **後端** | FastAPI + SQLAlchemy + SQLite | API 路由、認證、任務隊列、資料庫 |
| **核心引擎** | Python (whisper.cpp + Ollama + FFmpeg) | ASR、翻譯、字幕渲染、影片合成 |

**資料流程：**

```
用戶提交影片路徑 (前端 New Task)
  → REST POST /api/tasks (前端 → 後端)
  → FIFO 隊列排隊
  → ASR 語音辨識 (whisper.cpp + GPU)
    → WebSocket 即時推送進度 (後端 → 前端)
  → LLM 翻譯 (Ollama qwen2.5:7b)
    → WebSocket 即時推送 "翻譯中 3/22"
  → 狀態變更為 "ready_for_review"
  → 用戶開啟字幕編輯器 (前端 Editor)
    → REST GET /api/tasks/{id}/subtitles (載入字幕)
    → HTTP Range 影片串流 (預覽播放)
  → 用戶校對、編輯、調整
    → REST PUT /api/tasks/{id}/subtitles (儲存)
  → 燒錄字幕到影片
    → REST POST /api/tasks/{id}/synthesize (MP4/MXF)
```

## 項目結構

```
studio-captioner-ai/
├── backend/
│   ├── app/                          # FastAPI 應用層
│   │   ├── main.py                   # 應用入口 + 隊列 worker
│   │   ├── config.py                 # 伺服器設定（環境變數）
│   │   ├── database.py               # SQLite 非同步資料庫
│   │   ├── dependencies.py           # JWT 認證 + 資料庫注入
│   │   ├── api/                      # REST API 路由
│   │   │   ├── auth.py               #   註冊 / 登入
│   │   │   ├── tasks.py              #   任務 CRUD + 隊列狀態
│   │   │   ├── subtitles.py          #   字幕讀取 / 儲存 / 匯出 / 燒錄
│   │   │   ├── preview.py            #   影片串流 / 波形 / 縮圖
│   │   │   └── settings.py           #   伺服器設定 / 模型列表 / 路徑驗證
│   │   ├── ws/                       # WebSocket
│   │   │   └── handlers.py           #   任務進度 + 隊列狀態推送
│   │   ├── services/                 # 業務邏輯
│   │   │   ├── pipeline.py           #   處理管線（ASR → 翻譯 → 完成）
│   │   │   ├── task_queue.py         #   FIFO 任務隊列
│   │   │   ├── auth.py               #   密碼雜湊 + JWT
│   │   │   └── path_resolver.py      #   SMB 路徑映射
│   │   ├── models/                   # SQLAlchemy 資料模型
│   │   └── schemas/                  # Pydantic 請求/回應 schema
│   │
│   ├── core/                         # 核心引擎（從 VideoCaptioner 提取）
│   │   ├── asr/                      #   語音辨識（whisper.cpp / faster-whisper）
│   │   ├── translate/                #   LLM 翻譯
│   │   ├── split/                    #   智能斷句
│   │   ├── optimize/                 #   LLM 字幕優化
│   │   ├── subtitle/                 #   字幕渲染（ASS / 圓角背景）
│   │   ├── llm/                      #   LLM 客戶端（OpenAI 相容）
│   │   ├── prompts/                  #   Prompt 模板
│   │   └── utils/                    #   工具函數（FFmpeg、快取、日誌）
│   │
│   ├── features/                     # 新功能模組
│   │   ├── glossary/                 #   術語表（CRUD、修正、注入、CSV）
│   │   ├── translation_memory/       #   翻譯記憶（儲存、模糊匹配）
│   │   └── back_translation/         #   回譯驗證（比對、信心分數）
│   │
│   ├── resource/                     # 靜態資源
│   │   ├── fonts/                    #   打包字體
│   │   └── subtitle_style/           #   字幕樣式預設 JSON
│   │
│   ├── tests/                        # 測試（73 個測試）
│   │   ├── test_api/                 #   API 端點測試
│   │   ├── test_core/                #   核心模組匯入測試
│   │   └── test_features/            #   功能模組測試
│   │
│   └── run.py                        # 伺服器啟動入口
│
├── frontend/
│   ├── src-tauri/                    # Tauri v2（Rust 桌面殼）
│   ├── src/
│   │   ├── pages/                    # 頁面
│   │   │   ├── Login.tsx             #   登入 / 註冊
│   │   │   ├── Dashboard.tsx         #   儀表板（隊列狀態、即時進度）
│   │   │   ├── NewTask.tsx           #   提交新任務（Whisper 模型選擇）
│   │   │   ├── Editor.tsx            #   字幕編輯器（三欄佈局）
│   │   │   ├── Glossary.tsx          #   術語表管理
│   │   │   ├── History.tsx           #   任務歷史
│   │   │   └── Settings.tsx          #   伺服器設定
│   │   ├── components/
│   │   │   ├── editor/               #   編輯器組件
│   │   │   │   ├── VideoPlayer.tsx   #     影片播放 + 字幕疊加
│   │   │   │   ├── SubtitleList.tsx  #     雙語字幕列表 + inline 編輯
│   │   │   │   ├── Waveform.tsx      #     波形時間軸 + 可拖拉區間
│   │   │   │   ├── StylePanel.tsx    #     字幕樣式自訂面板
│   │   │   │   └── EditorToolbar.tsx #     儲存 / 匯出 / 燒錄按鈕
│   │   │   ├── queue/                #   隊列組件
│   │   │   └── common/               #   通用組件（Layout、Sidebar、Toast）
│   │   ├── store/                    # Zustand 狀態管理
│   │   ├── hooks/                    # React Hooks（WebSocket、鍵盤）
│   │   ├── services/                 # API 客戶端 + WebSocket 客戶端
│   │   └── types/                    # TypeScript 類型定義
│   └── index.html
│
└── docs/
    └── superpowers/
        ├── specs/                    # 設計規格書
        └── plans/                    # 實施計劃（Phase 1-4）
```

## 快速開始

### 環境需求

- Python 3.10+
- Node.js 18+
- FFmpeg
- whisper.cpp（`brew install whisper-cpp`）
- Ollama + qwen2.5:7b 模型（翻譯用）

### 安裝與啟動

```bash
# 1. Clone
git clone https://github.com/Reno19951212/studio-captioner-ai.git
cd studio-captioner-ai

# 2. 下載 Whisper 模型（放到 backend/AppData/models/）
mkdir -p backend/AppData/models
curl -L "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v2.bin" \
  -o backend/AppData/models/ggml-large-v2.bin

# 3. 安裝 Ollama 並下載翻譯模型
# macOS: https://ollama.com/download
ollama pull qwen2.5:7b

# 4. 啟動後端
cd backend
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic-settings pyjwt python-multipart openai
python run.py
# → http://localhost:8000

# 5. 啟動前端（另一個終端）
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 使用流程

1. 開啟前端（瀏覽器或 Tauri 桌面應用）
2. 註冊帳號並登入
3. **New Task** → 輸入影片路徑，選擇 Whisper 模型 → 提交
4. **Dashboard** → 觀察即時處理進度（ASR → 翻譯）
5. 處理完成後 → 點擊任務進入 **Editor**
6. 校對字幕 → 調整樣式 → **Export SRT** 或 **Burn to Video**

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/auth/register` | 註冊用戶 |
| POST | `/api/auth/login` | 登入（返回 JWT） |
| POST | `/api/tasks` | 提交新任務 |
| GET | `/api/tasks` | 列出用戶任務 |
| GET | `/api/tasks/{id}` | 任務詳情 |
| DELETE | `/api/tasks/{id}` | 取消排隊中的任務 |
| GET | `/api/queue` | 隊列狀態 |
| GET | `/api/tasks/{id}/subtitles` | 讀取字幕（雙語 JSON） |
| PUT | `/api/tasks/{id}/subtitles` | 儲存編輯後的字幕 |
| POST | `/api/tasks/{id}/export` | 匯出字幕（SRT/ASS/VTT） |
| POST | `/api/tasks/{id}/synthesize` | 燒錄字幕到影片（MP4/MXF） |
| POST | `/api/tasks/{id}/translate-segment` | 單句重翻 |
| GET | `/api/preview/{id}/video` | 影片串流（HTTP Range） |
| GET | `/api/preview/{id}/waveform` | 波形數據 |
| GET/PUT | `/api/settings` | 伺服器設定 |
| GET | `/api/settings/models` | 可用模型列表 |
| GET | `/api/settings/validate-path` | 驗證檔案路徑 |
| CRUD | `/api/glossaries` | 術語表管理 |
| WS | `/ws/tasks/{id}` | 單一任務進度推送 |
| WS | `/ws/queue` | 全局隊列狀態推送 |

## 技術棧

### 後端

| 組件 | 技術 |
|------|------|
| API 框架 | FastAPI |
| 資料庫 | SQLite + SQLAlchemy (async) |
| 認證 | JWT (PyJWT) |
| 任務隊列 | asyncio.Queue (FIFO) |
| 語音辨識 | whisper.cpp / faster-whisper |
| LLM 翻譯 | Ollama (qwen2.5:7b) |
| 影片處理 | FFmpeg |
| 快取 | diskcache |

### 前端

| 組件 | 技術 |
|------|------|
| 桌面殼 | Tauri v2 (Rust) |
| UI 框架 | React 18 + TypeScript |
| 樣式 | Tailwind CSS |
| 狀態管理 | Zustand |
| 波形圖 | wavesurfer.js |
| 建置工具 | Vite |

## 鍵盤快捷鍵（字幕編輯器）

| 快捷鍵 | 功能 |
|--------|------|
| `j` / `↓` | 下一段字幕 |
| `k` / `↑` | 上一段字幕 |
| `Space` | 播放 / 暫停影片 |
| `⌘S` / `Ctrl+S` | 儲存字幕 |
| `Enter` | 跳到下一段（編輯中） |
| `Shift+Enter` | 換行（編輯中） |
| `Esc` | 取消選擇 |

## 授權

MIT License
