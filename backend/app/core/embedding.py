import hashlib
from typing import List

import requests

from app.core.config import (
    EMBEDDING_PROVIDER,
    EMBEDDING_API_KEY,
    EMBEDDING_API_URL,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
)


def _normalize(vector: List[float]) -> List[float]:
    norm = sum(value * value for value in vector) ** 0.5
    if not norm:
        return vector
    return [value / norm for value in vector]


def _clean_text(text: str) -> str:
    return " ".join((text or "").split())


def _fit_dimension(vector: List[float], dimension: int = EMBEDDING_DIMENSION) -> List[float]:
    clipped = vector[:dimension]
    if len(clipped) < dimension:
        clipped.extend([0.0] * (dimension - len(clipped)))
    return clipped


def _local_embedding(text: str, dimension: int = EMBEDDING_DIMENSION) -> List[float]:
    vector = [0.0] * dimension
    if not text:
        return vector

    for token in _clean_text(text).split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for offset in range(0, len(digest), 4):
            chunk = digest[offset:offset + 4]
            bucket = int.from_bytes(chunk, "big") % dimension
            sign = 1.0 if chunk[0] % 2 == 0 else -1.0
            vector[bucket] += sign

    return _normalize(vector)


def _huggingface_embedding(text: str) -> List[float]:
    response = requests.post(
        f"{EMBEDDING_API_URL.rstrip('/')}/{EMBEDDING_MODEL}",
        json={
            "inputs": text,
            "normalize": True,
            "truncate": True,
        },
        headers={
            "Authorization": f"Bearer {EMBEDDING_API_KEY}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list) and data and isinstance(data[0], list):
        return _fit_dimension(data[0])
    if isinstance(data, list):
        return _fit_dimension(data)
    raise ValueError(f"Unexpected Hugging Face embedding response: {data}")


def _siliconflow_embedding(text: str) -> List[float]:
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text,
        "encoding_format": "float",
        "dimensions": EMBEDDING_DIMENSION,
    }
    headers = {
        "Authorization": f"Bearer {EMBEDDING_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        EMBEDDING_API_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    embedding = data["data"][0]["embedding"]
    return _fit_dimension(embedding)


def embed_text(text: str) -> List[float]:
    cleaned_text = _clean_text(text)
    if not cleaned_text:
        return [0.0] * EMBEDDING_DIMENSION

    try:
        if EMBEDDING_PROVIDER.lower() == "huggingface":
            return _huggingface_embedding(cleaned_text)
        return _siliconflow_embedding(cleaned_text)
    except Exception:
        return _local_embedding(cleaned_text)
