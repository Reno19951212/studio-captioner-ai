import pytest
from features.glossary.corrector import GlossaryCorrector
from features.glossary.injector import GlossaryInjector

class TestGlossaryCorrector:
    def test_correct_case_insensitive(self):
        terms = {"Fed": "聯儲局", "APAC": "亞太區", "Chairman Powell": "鮑威爾主席"}
        corrector = GlossaryCorrector(terms)
        text = "the fed announced today that chairman powell"
        result = corrector.correct(text)
        assert "Fed" in result
        assert "Chairman Powell" in result

    def test_correct_preserves_non_matching_text(self):
        terms = {"Fed": "聯儲局"}
        corrector = GlossaryCorrector(terms)
        result = corrector.correct("The economy is growing steadily")
        assert result == "The economy is growing steadily"

    def test_correct_multiple_occurrences(self):
        terms = {"APAC": "亞太區"}
        corrector = GlossaryCorrector(terms)
        result = corrector.correct("apac markets and apac growth")
        assert result.count("APAC") == 2

class TestGlossaryInjector:
    def test_build_glossary_context(self):
        terms = {"Fed": "聯儲局", "APAC": "亞太區"}
        injector = GlossaryInjector(terms)
        context = injector.build_context()
        assert "Fed" in context and "聯儲局" in context

    def test_inject_into_prompt(self):
        terms = {"Fed": "聯儲局"}
        injector = GlossaryInjector(terms)
        result = injector.inject("Translate the following text to Chinese.")
        assert "Fed" in result and "聯儲局" in result
        assert "Translate the following text to Chinese." in result

    def test_inject_empty_glossary(self):
        injector = GlossaryInjector({})
        result = injector.inject("Translate the following.")
        assert result == "Translate the following."

    def test_filter_relevant_terms(self):
        terms = {"Fed": "聯儲局", "APAC": "亞太區", "GDP": "國內生產總值"}
        injector = GlossaryInjector(terms)
        relevant = injector.filter_relevant("The Fed raised rates and GDP grew")
        assert "Fed" in relevant and "GDP" in relevant
        assert "APAC" not in relevant
