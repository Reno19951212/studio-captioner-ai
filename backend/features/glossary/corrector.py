"""Post-ASR glossary correction — fix spelling and casing of known terms."""
import re
from typing import Dict

class GlossaryCorrector:
    def __init__(self, terms: Dict[str, str]):
        self.terms = terms
        sorted_terms = sorted(terms.keys(), key=len, reverse=True)
        self._patterns = [(re.compile(re.escape(term), re.IGNORECASE), term) for term in sorted_terms]

    def correct(self, text: str) -> str:
        for pattern, canonical in self._patterns:
            text = pattern.sub(canonical, text)
        return text
