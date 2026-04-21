import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from pipelines.rule_builder import enhance_rule


INPUT_PATH = BASE_DIR / "data" / "chunks" / "rule_db_pure(new).json"
OUTPUT_PATH = BASE_DIR / "data" / "rules" / "rules_db_new_pure_with_logic.json"


def load_rules() -> list[dict]:
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"输入文件格式错误: {INPUT_PATH}")
    return payload


def save_rules(rules: list[dict]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(rules, file, ensure_ascii=False, indent=2)


def run() -> None:
    source_rules = load_rules()
    results: list[dict] = []

    for index, rule in enumerate(source_rules, start=1):
        print(f"[{index}/{len(source_rules)}] 正在增强纯规则: {rule.get('id', '')}")
        results.append(enhance_rule(rule))

    save_rules(results)
    print(f"纯规则逻辑增强完成，输出文件: {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
