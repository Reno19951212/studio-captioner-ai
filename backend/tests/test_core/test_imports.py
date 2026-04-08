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
    from core.subtitle.ass_utils import AssStyle
    from core.subtitle.style_manager import SubtitleStyle

    assert AssStyle is not None
    assert SubtitleStyle is not None


def test_import_llm_module():
    from core.llm.client import get_llm_client, call_llm

    assert get_llm_client is not None
    assert call_llm is not None


def test_import_utils():
    from core.utils.logger import setup_logger
    from core.utils.video_utils import video2audio

    assert setup_logger is not None
    assert video2audio is not None
