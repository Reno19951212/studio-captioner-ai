"""Fuzzy text matching for Translation Memory."""
from difflib import SequenceMatcher

def fuzzy_match(text_a: str, text_b: str) -> float:
    return SequenceMatcher(None, text_a.strip().lower(), text_b.strip().lower()).ratio()
