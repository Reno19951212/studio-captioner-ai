import pytest
from features.back_translation.confidence import compute_confidence, flag_low_confidence
from features.back_translation.verifier import compare_texts

class TestCompareTexts:
    def test_identical_texts(self):
        assert compare_texts("The Fed raised rates", "The Fed raised rates") == 1.0

    def test_similar_texts(self):
        assert compare_texts("The Fed raised rates today", "The Fed increased rates today") > 0.7

    def test_different_texts(self):
        assert compare_texts("Hello world", "Completely unrelated text") < 0.5

class TestConfidenceScoring:
    def test_compute_confidence(self):
        segments = [
            {"original": "The Fed raised rates", "back_translated": "The Fed raised rates"},
            {"original": "Markets responded positively", "back_translated": "Something completely different"},
        ]
        scores = compute_confidence(segments)
        assert len(scores) == 2
        assert scores[0] > 0.9
        assert scores[1] < 0.5

    def test_flag_low_confidence(self):
        flagged = flag_low_confidence([0.95, 0.88, 0.45, 0.92, 0.60], threshold=0.90)
        assert flagged == [1, 2, 4]

    def test_flag_all_above_threshold(self):
        assert flag_low_confidence([0.95, 0.98, 0.92], threshold=0.90) == []

    def test_flag_empty(self):
        assert flag_low_confidence([], threshold=0.90) == []
