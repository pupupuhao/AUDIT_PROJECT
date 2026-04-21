from __future__ import annotations

from pathlib import Path
from typing import Any


def classify_document(file: Any) -> str:
    filename = str(getattr(file, "filename", "") or getattr(file, "name", "") or "")
    text = Path(filename).stem.lower()
    if any(keyword in text for keyword in ("contract", "合同", "施工")):
        return "contract"
    if any(keyword in text for keyword in ("cost", "estimate", "审价", "造价")):
        return "cost_report"
    if any(keyword in text for keyword in ("resolution", "决议", "表决")):
        return "resolution"
    if any(keyword in text for keyword in ("completion", "完工", "竣工")):
        return "completion"
    return "unknown"

