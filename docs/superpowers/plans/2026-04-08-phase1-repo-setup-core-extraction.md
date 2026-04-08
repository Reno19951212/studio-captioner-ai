# Phase 1: Repo Setup + Core Extraction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the studio-captioner-ai repo with extracted and cleaned core engine from VideoCaptioner, ready for Phase 2 (FastAPI backend).

**Architecture:** Clone the new empty repo, copy core modules from VideoCaptioner, remove all cloud/CLI/GUI code, update imports and config to use the new package name `studio_captioner_ai`. The result is a clean Python package with only local ASR + LLM translation + subtitle rendering.

**Tech Stack:** Python 3.10+, faster-whisper, whisper.cpp, FFmpeg, diskcache, Pillow

**Source repo:** `/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner`
**Target repo:** `https://github.com/Reno19951212/studio-captioner-ai`

---

### Task 1: Clone Repo + Create Backend Skeleton

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/core/__init__.py`
- Create: `README.md`
- Create: `.gitignore`

- [ ] **Step 1: Clone the new repo**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project"
git clone https://github.com/Reno19951212/studio-captioner-ai.git
cd studio-captioner-ai
```

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p backend/core
mkdir -p backend/app
mkdir -p backend/features
mkdir -p backend/resource
mkdir -p backend/tests/test_core
mkdir -p frontend
```

- [ ] **Step 3: Create .gitignore**

Write to `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
venv/
*.egg

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project
*.log
output/
temp/
.superpowers/

# Node (frontend)
node_modules/
frontend/dist/

# Tauri
frontend/src-tauri/target/
```

- [ ] **Step 4: Create backend/pyproject.toml**

Write to `backend/pyproject.toml`:

```toml
[project]
name = "studio-captioner-ai"
version = "0.1.0"
description = "AI-powered on-premise video captioning tool for studio teams"
readme = "../README.md"
license = { text = "MIT" }
requires-python = ">=3.10,<3.13"
keywords = ["video", "caption", "subtitle", "asr", "llm", "translation"]

dependencies = [
    "requests>=2.32.4",
    "openai>=1.97.1",
    "diskcache>=5.6.3",
    "json-repair>=0.49.0",
    "langdetect>=1.0.9",
    "pydub>=0.25.1",
    "tenacity>=8.2.0",
    "pillow>=12.0.0",
    "fonttools>=4.61.1",
    "platformdirs>=4.0.0",
    "tomli>=2.0.0; python_version < '3.11'",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlalchemy>=2.0.0",
    "pyjwt>=2.9.0",
    "python-multipart>=0.0.18",
]

[project.urls]
Repository = "https://github.com/Reno19951212/studio-captioner-ai"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["core", "app", "features"]

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "basic"
include = ["core", "app", "features"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --strict-markers --tb=short"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
ignore = ["E501"]
```

- [ ] **Step 5: Create backend/core/__init__.py**

Write to `backend/core/__init__.py`:

```python
"""Studio Captioner AI — Core Engine"""
```

- [ ] **Step 6: Create README.md**

Write to `README.md`:

```markdown
# Studio Captioner AI

AI-powered on-premise video captioning tool for studio teams.

- Local ASR (Whisper GPU)
- LLM-powered subtitle optimization and translation
- Subtitle burn-in (MXF / MP4)
- Tauri v2 + React desktop frontend

## Development

See `docs/superpowers/specs/` for design documentation.
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: initialize repo structure with backend skeleton"
```

---

### Task 2: Copy Core ASR Module (Local Engines Only)

**Files:**
- Create: `backend/core/asr/__init__.py`
- Create: `backend/core/asr/asr_data.py` (copy)
- Create: `backend/core/asr/base.py` (copy)
- Create: `backend/core/asr/status.py` (copy)
- Create: `backend/core/asr/faster_whisper.py` (copy)
- Create: `backend/core/asr/whisper_cpp.py` (copy)
- Create: `backend/core/asr/chunked_asr.py` (copy)
- Create: `backend/core/asr/chunk_merger.py` (copy)
- Create: `backend/core/asr/transcribe.py` (copy + modify)

Source: `/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/core/asr/`

- [ ] **Step 1: Copy local ASR files**

```bash
SRC="/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/core/asr"
DST="/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/backend/core/asr"
mkdir -p "$DST"

cp "$SRC/asr_data.py" "$DST/"
cp "$SRC/base.py" "$DST/"
cp "$SRC/status.py" "$DST/"
cp "$SRC/faster_whisper.py" "$DST/"
cp "$SRC/whisper_cpp.py" "$DST/"
cp "$SRC/chunked_asr.py" "$DST/"
cp "$SRC/chunk_merger.py" "$DST/"
cp "$SRC/transcribe.py" "$DST/"
```

Do NOT copy: `bcut.py`, `jianying.py`, `whisper_api.py`

- [ ] **Step 2: Write cleaned `backend/core/asr/__init__.py`**

Write to `backend/core/asr/__init__.py`:

```python
from .chunked_asr import ChunkedASR
from .faster_whisper import FasterWhisperASR
from .status import ASRStatus
from .transcribe import transcribe
from .whisper_cpp import WhisperCppASR

__all__ = [
    "ChunkedASR",
    "FasterWhisperASR",
    "WhisperCppASR",
    "transcribe",
    "ASRStatus",
]
```

- [ ] **Step 3: Clean `backend/core/asr/transcribe.py`**

Replace the entire content of `backend/core/asr/transcribe.py` with:

```python
from core.asr.asr_data import ASRData
from core.asr.chunked_asr import ChunkedASR
from core.asr.faster_whisper import FasterWhisperASR
from core.asr.whisper_cpp import WhisperCppASR
from core.entities import TranscribeConfig, TranscribeModelEnum


def transcribe(audio_path: str, config: TranscribeConfig, callback=None) -> ASRData:
    """Transcribe audio file using specified configuration.

    Args:
        audio_path: Path to audio file
        config: Transcription configuration
        callback: Progress callback function(progress: int, message: str)

    Returns:
        ASRData: Transcription result data
    """

    def _default_callback(x, y):
        pass

    if callback is None:
        callback = _default_callback

    if config.transcribe_model is None:
        raise ValueError("Transcription model not set")

    asr = _create_asr_instance(audio_path, config)
    asr_data = asr.run(callback=callback)

    if not config.need_word_time_stamp:
        asr_data.optimize_timing()

    return asr_data


def _create_asr_instance(audio_path: str, config: TranscribeConfig) -> ChunkedASR:
    """Create appropriate ASR instance based on configuration."""
    model_type = config.transcribe_model

    if model_type == TranscribeModelEnum.WHISPER_CPP:
        return _create_whisper_cpp_asr(audio_path, config)

    elif model_type == TranscribeModelEnum.FASTER_WHISPER:
        return _create_faster_whisper_asr(audio_path, config)

    else:
        raise ValueError(f"Unsupported transcription model: {model_type}")


def _create_whisper_cpp_asr(audio_path: str, config: TranscribeConfig) -> ChunkedASR:
    """Create WhisperCpp ASR instance with chunking support."""
    asr_kwargs = {
        "use_cache": True,
        "need_word_time_stamp": config.need_word_time_stamp,
        "language": config.transcribe_language,
        "whisper_model": config.whisper_model.value if config.whisper_model else None,
    }
    return ChunkedASR(
        asr_class=WhisperCppASR,
        audio_path=audio_path,
        asr_kwargs=asr_kwargs,
        chunk_concurrency=1,
        chunk_length=60 * 20,
    )


def _create_faster_whisper_asr(audio_path: str, config: TranscribeConfig) -> ChunkedASR:
    """Create FasterWhisper ASR instance with chunking support."""
    asr_kwargs = {
        "use_cache": True,
        "need_word_time_stamp": config.need_word_time_stamp,
        "faster_whisper_program": config.faster_whisper_program or "",
        "language": config.transcribe_language,
        "whisper_model": (
            config.faster_whisper_model.value if config.faster_whisper_model else "base"
        ),
        "model_dir": config.faster_whisper_model_dir or "",
        "device": config.faster_whisper_device,
        "vad_filter": config.faster_whisper_vad_filter,
        "vad_threshold": config.faster_whisper_vad_threshold,
        "vad_method": (
            config.faster_whisper_vad_method.value
            if config.faster_whisper_vad_method
            else ""
        ),
        "ff_mdx_kim2": config.faster_whisper_ff_mdx_kim2,
        "one_word": config.faster_whisper_one_word,
        "prompt": config.faster_whisper_prompt,
    }
    return ChunkedASR(
        asr_class=FasterWhisperASR,
        audio_path=audio_path,
        asr_kwargs=asr_kwargs,
        chunk_concurrency=1,
        chunk_length=60 * 20,
    )
```

- [ ] **Step 4: Commit**

```bash
git add backend/core/asr/
git commit -m "feat: add core ASR module (local engines only)"
```

---

### Task 3: Copy Core Processing Modules (Split, Optimize, LLM, Prompts)

**Files:**
- Create: `backend/core/split/` (copy all)
- Create: `backend/core/optimize/` (copy all)
- Create: `backend/core/llm/` (copy all)
- Create: `backend/core/prompts/` (copy all)

Source: `/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/core/`

- [ ] **Step 1: Copy split module**

```bash
SRC="/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/core"
DST="/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/backend/core"

cp -r "$SRC/split" "$DST/"
```

- [ ] **Step 2: Copy optimize module**

```bash
cp -r "$SRC/optimize" "$DST/"
```

- [ ] **Step 3: Copy LLM module**

```bash
cp -r "$SRC/llm" "$DST/"
```

- [ ] **Step 4: Copy prompts module**

```bash
cp -r "$SRC/prompts" "$DST/"
```

- [ ] **Step 5: Commit**

```bash
git add backend/core/split/ backend/core/optimize/ backend/core/llm/ backend/core/prompts/
git commit -m "feat: add core split, optimize, LLM, and prompts modules"
```

---

### Task 4: Copy Translate Module (LLM Only)

**Files:**
- Create: `backend/core/translate/__init__.py` (cleaned)
- Create: `backend/core/translate/base.py` (copy)
- Create: `backend/core/translate/llm_translator.py` (copy)
- Create: `backend/core/translate/factory.py` (cleaned)
- Create: `backend/core/translate/types.py` (cleaned)

Source: `/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/core/translate/`

- [ ] **Step 1: Copy base files**

```bash
SRC="/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/core/translate"
DST="/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/backend/core/translate"
mkdir -p "$DST"

cp "$SRC/base.py" "$DST/"
cp "$SRC/llm_translator.py" "$DST/"
```

Do NOT copy: `bing_translator.py`, `google_translator.py`, `deeplx_translator.py`

- [ ] **Step 2: Write cleaned `backend/core/translate/__init__.py`**

Write to `backend/core/translate/__init__.py`:

```python
"""Translation module — LLM-based translation only"""

from core.entities import SubtitleProcessData
from core.translate.base import BaseTranslator
from core.translate.factory import TranslatorFactory
from core.translate.llm_translator import LLMTranslator
from core.translate.types import TargetLanguage, TranslatorType

__all__ = [
    "BaseTranslator",
    "SubtitleProcessData",
    "TranslatorFactory",
    "TranslatorType",
    "TargetLanguage",
    "LLMTranslator",
]
```

- [ ] **Step 3: Write cleaned `backend/core/translate/factory.py`**

Write to `backend/core/translate/factory.py`:

```python
"""Translator factory — LLM only"""

from typing import Callable, Optional

from core.translate.base import BaseTranslator
from core.translate.llm_translator import LLMTranslator
from core.translate.types import TargetLanguage, TranslatorType
from core.utils.logger import setup_logger

logger = setup_logger("translator_factory")


class TranslatorFactory:
    """Translator factory class"""

    @staticmethod
    def create_translator(
        translator_type: TranslatorType,
        thread_num: int = 5,
        batch_num: int = 10,
        target_language: Optional[TargetLanguage] = None,
        model: str = "gpt-4o-mini",
        custom_prompt: str = "",
        is_reflect: bool = False,
        update_callback: Optional[Callable] = None,
    ) -> BaseTranslator:
        """Create translator instance"""
        try:
            if target_language is None:
                target_language = TargetLanguage.SIMPLIFIED_CHINESE

            if translator_type == TranslatorType.LLM:
                return LLMTranslator(
                    thread_num=thread_num,
                    batch_num=batch_num,
                    target_language=target_language,
                    model=model,
                    custom_prompt=custom_prompt,
                    is_reflect=is_reflect,
                    update_callback=update_callback,
                )
            else:
                raise ValueError(f"Unsupported translator type: {translator_type}")
        except Exception as e:
            logger.error(f"Failed to create translator: {str(e)}")
            raise
```

- [ ] **Step 4: Write cleaned `backend/core/translate/types.py`**

Write to `backend/core/translate/types.py`:

```python
"""Translator type enums"""

from enum import Enum


class TranslatorType(Enum):
    """Translator type"""

    LLM = "llm"


class TargetLanguage(Enum):
    """Target language enum"""

    # Chinese
    SIMPLIFIED_CHINESE = "简体中文"
    TRADITIONAL_CHINESE = "繁体中文"

    # English
    ENGLISH = "英语"
    ENGLISH_US = "英语(美国)"
    ENGLISH_UK = "英语(英国)"

    # Asian languages
    JAPANESE = "日本語"
    KOREAN = "韩语"
    CANTONESE = "粤语"
    THAI = "泰语"
    VIETNAMESE = "越南语"
    INDONESIAN = "印尼语"
    MALAY = "马来语"
    TAGALOG = "菲律宾语"

    # European languages
    FRENCH = "法语"
    GERMAN = "德语"
    SPANISH = "西班牙语"
    SPANISH_LATAM = "西班牙语(拉丁美洲)"
    RUSSIAN = "俄语"
    PORTUGUESE = "葡萄牙语"
    PORTUGUESE_BR = "葡萄牙语(巴西)"
    PORTUGUESE_PT = "葡萄牙语(葡萄牙)"
    ITALIAN = "意大利语"
    DUTCH = "荷兰语"
    POLISH = "波兰语"
    TURKISH = "土耳其语"
    GREEK = "希腊语"
    CZECH = "捷克语"
    SWEDISH = "瑞典语"
    DANISH = "丹麦语"
    FINNISH = "芬兰语"
    NORWEGIAN = "挪威语"
    HUNGARIAN = "匈牙利语"
    ROMANIAN = "罗马尼亚语"
    BULGARIAN = "保加利亚语"
    UKRAINIAN = "乌克兰语"

    # Middle Eastern languages
    ARABIC = "阿拉伯语"
    HEBREW = "希伯来语"
    PERSIAN = "波斯语"
```

- [ ] **Step 5: Commit**

```bash
git add backend/core/translate/
git commit -m "feat: add core translate module (LLM only, removed cloud services)"
```

---

### Task 5: Copy Subtitle, Utils, and Resource Modules

**Files:**
- Create: `backend/core/subtitle/` (copy all)
- Create: `backend/core/utils/` (copy all)
- Create: `backend/resource/fonts/` (copy)
- Create: `backend/resource/subtitle_style/` (copy)

- [ ] **Step 1: Copy subtitle module**

```bash
SRC="/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/core"
DST="/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/backend/core"

cp -r "$SRC/subtitle" "$DST/"
```

- [ ] **Step 2: Copy utils module**

```bash
cp -r "$SRC/utils" "$DST/"
```

- [ ] **Step 3: Copy resource files**

```bash
RSRC="/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/resource"
RDST="/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/backend/resource"

cp -r "$RSRC/fonts" "$RDST/"
cp -r "$RSRC/subtitle_style" "$RDST/"
```

- [ ] **Step 4: Commit**

```bash
git add backend/core/subtitle/ backend/core/utils/ backend/resource/
git commit -m "feat: add subtitle rendering, utils, fonts, and style presets"
```

---

### Task 6: Copy and Clean Entities + Config

**Files:**
- Create: `backend/core/entities.py` (copy + modify)
- Create: `backend/core/constant.py` (copy)
- Create: `backend/core/config.py` (new, based on original)

Source: `/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/core/`

- [ ] **Step 1: Copy entities.py**

```bash
SRC="/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/core"
DST="/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/backend/core"

cp "$SRC/entities.py" "$DST/"
cp "$SRC/constant.py" "$DST/"
```

- [ ] **Step 2: Clean `backend/core/entities.py` — Remove cloud enums**

In `backend/core/entities.py`, replace the `TranscribeModelEnum` class:

Find:
```python
class TranscribeModelEnum(Enum):
    """转录模型"""

    BIJIAN = "B 接口"
    JIANYING = "J 接口"
    WHISPER_API = "Whisper [API] ✨"
    FASTER_WHISPER = "FasterWhisper ✨"
    WHISPER_CPP = "WhisperCpp"
```

Replace with:
```python
class TranscribeModelEnum(Enum):
    """Transcription model"""

    FASTER_WHISPER = "FasterWhisper"
    WHISPER_CPP = "WhisperCpp"
```

- [ ] **Step 3: Clean `backend/core/entities.py` — Remove cloud translator enums**

Find:
```python
class TranslatorServiceEnum(Enum):
    """翻译器服务"""

    OPENAI = "LLM 大模型翻译"
    DEEPLX = "DeepLx 翻译"
    BING = "微软翻译"
    GOOGLE = "谷歌翻译"
```

Replace with:
```python
class TranslatorServiceEnum(Enum):
    """Translator service"""

    LLM = "LLM Translation"
```

- [ ] **Step 4: Clean `backend/core/entities.py` — Remove cloud LLM services**

Find:
```python
class LLMServiceEnum(Enum):
    """LLM服务"""

    OPENAI = "OpenAI 兼容"
    SILICON_CLOUD = "SiliconCloud"
    DEEPSEEK = "DeepSeek"
    OLLAMA = "Ollama"
    LM_STUDIO = "LM Studio"
    GEMINI = "Gemini"
    CHATGLM = "ChatGLM"
```

Replace with:
```python
class LLMServiceEnum(Enum):
    """LLM service"""

    OPENAI_COMPATIBLE = "OpenAI Compatible"
    OLLAMA = "Ollama"
```

- [ ] **Step 5: Copy and create config.py**

```bash
cp "/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/videocaptioner/config.py" \
   "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/backend/core/config.py"
```

In `backend/core/config.py`, update the app name. Find any reference to `"VideoCaptioner"` or `"videocaptioner"` and replace with `"studio-captioner-ai"` / `"Studio Captioner AI"`. Update the platformdirs app name accordingly.

- [ ] **Step 6: Commit**

```bash
git add backend/core/entities.py backend/core/constant.py backend/core/config.py
git commit -m "feat: add entities and config (cleaned cloud references)"
```

---

### Task 7: Fix All Import Paths

All copied files use `videocaptioner.core.*` imports. These must be changed to `core.*` to match the new package structure.

**Files:**
- Modify: All `.py` files in `backend/core/`

- [ ] **Step 1: Bulk replace imports**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai"
find backend/core -name "*.py" -exec sed -i '' 's/from videocaptioner\.core\./from core./g' {} +
find backend/core -name "*.py" -exec sed -i '' 's/import videocaptioner\.core\./import core./g' {} +
find backend/core -name "*.py" -exec sed -i '' 's/from videocaptioner\./from core./g' {} +
```

- [ ] **Step 2: Verify no remaining old imports**

```bash
grep -r "videocaptioner" backend/core/ || echo "Clean — no old imports found"
```

Expected: "Clean — no old imports found"

- [ ] **Step 3: Commit**

```bash
git add backend/core/
git commit -m "refactor: update all imports from videocaptioner.core to core"
```

---

### Task 8: Write Smoke Test

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_core/__init__.py`
- Create: `backend/tests/test_core/test_imports.py`

- [ ] **Step 1: Write import smoke test**

Write to `backend/tests/__init__.py`:

```python
```

Write to `backend/tests/test_core/__init__.py`:

```python
```

Write to `backend/tests/test_core/test_imports.py`:

```python
"""Smoke tests to verify all core modules import correctly."""


def test_import_asr_module():
    from core.asr import FasterWhisperASR, WhisperCppASR, transcribe, ASRStatus

    assert FasterWhisperASR is not None
    assert WhisperCppASR is not None
    assert transcribe is not None
    assert ASRStatus is not None


def test_import_asr_data():
    from core.asr.asr_data import ASRData, ASRDataSeg

    assert ASRData is not None
    assert ASRDataSeg is not None


def test_import_translate_module():
    from core.translate import LLMTranslator, TranslatorFactory, TranslatorType, TargetLanguage

    assert LLMTranslator is not None
    assert TranslatorFactory is not None
    assert TranslatorType is not None
    assert TargetLanguage is not None


def test_translator_type_has_no_cloud_services():
    from core.translate.types import TranslatorType

    member_names = [m.name for m in TranslatorType]
    assert "GOOGLE" not in member_names
    assert "BING" not in member_names
    assert "DEEPLX" not in member_names
    assert "LLM" in member_names


def test_transcribe_model_enum_has_no_cloud_services():
    from core.entities import TranscribeModelEnum

    member_names = [m.name for m in TranscribeModelEnum]
    assert "BIJIAN" not in member_names
    assert "JIANYING" not in member_names
    assert "WHISPER_API" not in member_names
    assert "FASTER_WHISPER" in member_names
    assert "WHISPER_CPP" in member_names


def test_import_split_module():
    from core.split.split import SubtitleSplitter

    assert SubtitleSplitter is not None


def test_import_optimize_module():
    from core.optimize.optimize import SubtitleOptimizer

    assert SubtitleOptimizer is not None


def test_import_subtitle_module():
    from core.subtitle.ass_renderer import AssRenderer
    from core.subtitle.style_manager import StyleManager

    assert AssRenderer is not None
    assert StyleManager is not None


def test_import_llm_module():
    from core.llm.client import LLMClient

    assert LLMClient is not None


def test_import_utils():
    from core.utils.logger import setup_logger
    from core.utils.video_utils import extract_audio

    assert setup_logger is not None
    assert extract_audio is not None
```

- [ ] **Step 2: Run the smoke tests**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/backend"
python -m pytest tests/test_core/test_imports.py -v
```

Expected: All tests PASS. If any fail due to import errors, fix the broken imports in the referenced files.

- [ ] **Step 3: Commit**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai"
git add backend/tests/
git commit -m "test: add import smoke tests for all core modules"
```

---

### Task 9: Copy Design Spec + Push to Remote

**Files:**
- Create: `docs/superpowers/specs/2026-04-08-studio-captioner-design.md` (copy)

- [ ] **Step 1: Copy design spec from original repo**

```bash
mkdir -p "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/docs/superpowers/specs"
cp "/Users/renomacm2/Documents/GitHub Remote Project/VideoCaptioner/docs/superpowers/specs/2026-04-08-studio-captioner-design.md" \
   "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/docs/superpowers/specs/"
```

- [ ] **Step 2: Commit**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai"
git add docs/
git commit -m "docs: add Studio Captioner AI design spec"
```

- [ ] **Step 3: Push to remote**

```bash
git push origin main
```

- [ ] **Step 4: Verify on GitHub**

```bash
gh repo view Reno19951212/studio-captioner-ai --web
```

---

### Task Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Clone repo + create skeleton | pyproject.toml, .gitignore, README |
| 2 | Copy ASR module (local only) | 9 files (no bcut/jianying/whisper_api) |
| 3 | Copy split, optimize, LLM, prompts | 4 directories |
| 4 | Copy translate module (LLM only) | 5 files (no bing/google/deeplx) |
| 5 | Copy subtitle, utils, resources | 3 directories |
| 6 | Copy + clean entities and config | 3 files |
| 7 | Fix all import paths | All .py in core/ |
| 8 | Write + run smoke tests | 1 test file, 11 tests |
| 9 | Copy spec + push to remote | 1 doc file |

**Phase 1 output:** A clean `studio-captioner-ai` repo on GitHub with:
- `backend/core/` — extracted and cleaned core engine (local ASR + LLM translate + subtitle rendering)
- All cloud service code removed
- All imports updated
- Smoke tests passing
- Ready for Phase 2 (FastAPI backend layer)
