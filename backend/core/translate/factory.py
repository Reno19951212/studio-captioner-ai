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
