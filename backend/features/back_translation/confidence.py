"""Confidence scoring and low-confidence flagging."""
from typing import Dict, List
from features.back_translation.verifier import compare_texts

def compute_confidence(segments: List[Dict[str, str]]) -> List[float]:
    scores = []
    for seg in segments:
        original = seg.get("original", "")
        back_translated = seg.get("back_translated", "")
        score = compare_texts(original, back_translated)
        scores.append(round(score, 3))
    return scores

def flag_low_confidence(scores: List[float], threshold: float = 0.90) -> List[int]:
    return [i for i, score in enumerate(scores) if score < threshold]
