import pytest
from features.glossary.corrector import GlossaryCorrector
from features.glossary.injector import GlossaryInjector
from features.back_translation.confidence import compute_confidence, flag_low_confidence

def test_full_accuracy_pipeline():
    terms = {"Fed": "聯儲局", "Chairman Powell": "鮑威爾主席"}
    corrector = GlossaryCorrector(terms)
    asr_output = "the fed said today that chairman powell will speak"
    corrected = corrector.correct(asr_output)
    assert "Fed" in corrected
    assert "Chairman Powell" in corrected

    injector = GlossaryInjector(terms)
    relevant = injector.filter_relevant(corrected)
    assert "Fed" in relevant
    prompt = injector.inject("Translate the following to Chinese:")
    assert "Fed" in prompt and "聯儲局" in prompt

    segments = [
        {"original": "Fed said today that Chairman Powell will speak",
         "back_translated": "Fed said today that Chairman Powell will speak"},
        {"original": "Markets are uncertain",
         "back_translated": "Something completely different"},
    ]
    scores = compute_confidence(segments)
    flagged = flag_low_confidence(scores, threshold=0.90)
    assert 0 not in flagged
    assert 1 in flagged
