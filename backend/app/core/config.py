import os

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

POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "postgres"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "123456"
