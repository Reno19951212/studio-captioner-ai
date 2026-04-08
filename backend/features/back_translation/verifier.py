"""Back-translation text comparison."""
from difflib import SequenceMatcher

def compare_texts(original: str, back_translated: str) -> float:
    return SequenceMatcher(None, original.strip().lower(), back_translated.strip().lower()).ratio()
