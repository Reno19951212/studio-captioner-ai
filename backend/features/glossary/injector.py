"""Inject glossary terms into LLM translation prompts."""
from typing import Dict

class GlossaryInjector:
    def __init__(self, terms: Dict[str, str]):
        self.terms = terms

    def build_context(self) -> str:
        if not self.terms:
            return ""
        lines = [f"- {src} → {tgt}" for src, tgt in self.terms.items()]
        return "Glossary (use these exact translations for the following terms):\n" + "\n".join(lines)

    def inject(self, prompt: str) -> str:
        context = self.build_context()
        if not context:
            return prompt
        return f"{context}\n\n{prompt}"

    def filter_relevant(self, text: str) -> Dict[str, str]:
        relevant = {}
        text_lower = text.lower()
        for src, tgt in self.terms.items():
            if src.lower() in text_lower:
                relevant[src] = tgt
        return relevant
