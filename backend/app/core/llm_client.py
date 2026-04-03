import requests
import json
import time
from app.core.config import LLM_API_KEY, LLM_API_URL, LLM_MODEL


def call_llm(prompt: str, max_retries: int = 3):

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "你是法规结构化专家，只输出JSON"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(max_retries):
        try:
            res = requests.post(
                LLM_API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )

            if res.status_code != 200:
                print(f"HTTP错误: {res.status_code}, {res.text}")
                time.sleep(1)
                continue

            data = res.json()

            # 防结构异常
            if "choices" not in data:
                print(" 返回格式异常:", data)
                time.sleep(1)
                continue

            content = data["choices"][0]["message"]["content"]

            return content

        except Exception as e:
            print(f" 请求失败（第{attempt+1}次）:", str(e))
            time.sleep(1)

    return "{}"
