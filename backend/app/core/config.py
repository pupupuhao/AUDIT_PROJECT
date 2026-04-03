import os
from pathlib import Path


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_local_env()

LLM_API_KEY = os.getenv(
    "LLM_API_KEY", "")
LLM_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
LLM_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_API_URL = os.getenv(
    "EMBEDDING_API_URL", "https://router.huggingface.co/hf-inference/models")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
