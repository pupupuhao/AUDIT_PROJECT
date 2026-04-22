from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from app.core.config import LOCAL_LLM_API_KEY, LOCAL_LLM_BASE_URL, LOCAL_LLM_MODEL


def call_local_llm_json(prompt: str, *, timeout: int = 8) -> Dict[str, Any]:
    """Call LM Studio's OpenAI-compatible chat completions endpoint.

    The audit pipeline must keep running when the local model is unavailable.
    This function therefore returns an availability marker instead of raising
    network or response-shape exceptions.
    """
    url = f"{LOCAL_LLM_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {LOCAL_LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LOCAL_LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你只做字段归类，不做审计判断。必须只输出严格 JSON。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        content: Optional[str] = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )
        return {
            "available": True,
            "model": LOCAL_LLM_MODEL,
            "raw_content": content or "{}",
            "error": None,
        }
    except Exception as exc:
        return {
            "available": False,
            "model": LOCAL_LLM_MODEL,
            "raw_content": "{}",
            "error": str(exc),
        }
