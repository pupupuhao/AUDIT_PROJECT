import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.db.pgvector import get_pgvector_store
from pipelines.rule_builder import enhance_rule


INPUT_PATH = BASE_DIR / "data" / "chunks" / "rules_db.json"
OUTPUT_PATH = BASE_DIR / "data" / "rules" / "rules_db_with_llm.json"


def load_chunks():
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_rules(rules):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


def run():
    chunks = load_chunks()
    results = []
    store = get_pgvector_store()

    if store:
        try:
            store.init_schema()
            print("已初始化 pgvector 表结构。")
        except Exception as exc:
            print(f"pgvector 初始化失败，继续仅生成本地规则库: {exc}")
            store = None

    for index, chunk in enumerate(chunks, start=1):
        print(f"[{index}/{len(chunks)}] 正在增强规则: {chunk.get('id', '')}")
        enhanced = enhance_rule(chunk)
        results.append(enhanced)
        if store:
            try:
                store.upsert_rule(enhanced)
            except Exception as exc:
                print(f"规则写入 pgvector 失败 {enhanced.get('id', '')}: {exc}")

    save_rules(results)
    print(f"规则库构建完成，输出文件: {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
