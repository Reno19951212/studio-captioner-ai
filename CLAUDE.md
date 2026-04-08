# CLAUDE.md — Studio Captioner AI

## 項目概述

Studio Captioner AI 是一個本地部署的 AI 影片字幕工具，專為小型工作室/製作團隊設計。從 [VideoCaptioner](https://github.com/WEIFENG2333/VideoCaptioner) 核心引擎提取，重新建構為 FastAPI 後端 + Tauri v2 React 前端的架構。

## 開發環境

- **後端：** `cd backend && python run.py`（port 8000）
- **前端：** `cd frontend && npm run dev`（port 5173）
- **測試：** `cd backend && python3 -m pytest tests/ -v`（73 個測試）
- **前端建置：** `cd frontend && npm run build`

## 項目結構

```
backend/
  app/          → FastAPI 應用層（API、WebSocket、服務、模型）
  core/         → 核心引擎（ASR、翻譯、字幕渲染）— 從 VideoCaptioner 提取
  features/     → 新功能（術語表、翻譯記憶、回譯驗證）
  tests/        → pytest 測試

frontend/
  src-tauri/    → Tauri v2 Rust 桌面殼
  src/          → React 18 + TypeScript 應用
    pages/      → 頁面組件（Dashboard、Editor、NewTask 等）
    components/ → UI 組件（editor/、queue/、common/）
    store/      → Zustand 狀態管理
    services/   → API + WebSocket 客戶端
```

## 關鍵架構決策

- **Monorepo** — backend/ + frontend/ 在同一個 repo
- **core/ 獨立** — 從 VideoCaptioner 提取的核心引擎保持獨立，app/ 是 API wrapper
- **features/ 分離** — 新功能模組獨立，不污染 core
- **SQLite** — 輕量資料庫，on-premise 部署不需要額外裝 DB server
- **WebSocket** — 任務進度即時推送，Dashboard 30 秒 polling 兜底
- **共享存儲** — API 只傳路徑不傳檔案，後端直接讀取共享 NAS

## 外部依賴

- **whisper.cpp** — 語音辨識（`brew install whisper-cpp`）
  - 模型放在 `backend/AppData/models/`（被 .gitignore 排除）
- **Ollama** — 本地 LLM（翻譯用 qwen2.5:7b）
  - API base: `http://localhost:11434/v1`
- **FFmpeg** — 音頻提取 + 字幕燒錄

## 編碼慣例

- **後端：** Python 3.10+, ruff lint, pyright type check, async/await
- **前端：** TypeScript strict, Tailwind CSS, Zustand stores, React hooks
- **測試：** pytest-asyncio, `@pytest_asyncio.fixture` for async fixtures
- **提交：** conventional commits (feat/fix/chore/docs)

## 常見操作

```bash
# 運行所有測試
cd backend && python3 -m pytest tests/ -v

# 前端建置檢查
cd frontend && npm run build

# 重啟後端（重新載入代碼）
lsof -ti :8000 | xargs kill -9; cd backend && python run.py

# 下載新的 Whisper 模型
curl -L "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v2.bin" \
  -o backend/AppData/models/ggml-large-v2.bin
```

## 需要注意

- `backend/AppData/` 被 .gitignore 排除（包含 whisper 模型、cache DB）
- `backend/studio_captioner.db` 是 SQLite 運行時資料庫，不入 git
- 前端 `<video src>` 和 `<img src>` 不能設 HTTP header，preview API 支援 `?token=` query param 認證
- `ProtectedRoute` 同時檢查 Zustand store 和 localStorage 以支援頁面刷新
