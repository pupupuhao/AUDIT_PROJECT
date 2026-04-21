from __future__ import annotations

from typing import Any, Dict, List

from modules.audit_engine.core.field_runtime import FieldCandidate


def extract_fields_from_pdf(file: Any, doc_type: str) -> Dict[str, List[FieldCandidate]]:
    # PDF/OCR/LLM extraction is intentionally an extension point in this round.
    # Extractors must return FieldCandidate lists and must not produce audit conclusions.
    return {}

