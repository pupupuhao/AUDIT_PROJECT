import json
from functools import lru_cache
from pathlib import Path
from typing import List

from app.models.rule_model import RuleModel


BASE_DIR = Path(__file__).resolve().parents[2]
RULE_PATHS = [
    BASE_DIR / "data" / "rules" / "rules_db_with_llm.json",
    BASE_DIR / "data" / "chunks" / "rules_db_with_category.json",
    BASE_DIR / "data" / "chunks" / "rules_db.json",
]
CATEGORY_ALIASES = {
    "使用范围审计": "使用范围合规审计",
}


def _resolve_rule_file() -> Path:
    for path in RULE_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError("未找到规则库文件，请先执行 backend/script/build_rules.py")


def _normalize_rule(raw: dict) -> dict:
    logic = raw.get("logic_rules") or {}
    content = raw.get("content") or raw.get("clean_text") or ""
    category = raw.get("category", "使用范围合规审计")
    return {
        "id": raw.get("id", ""),
        "law_name": raw.get("law_name", ""),
        "clause_label": raw.get("clause_label", ""),
        "full_title": raw.get("full_title", ""),
        "content": content,
        "clean_text": raw.get("clean_text", content),
        "parent_context": raw.get("parent_context", ""),
        "keywords": raw.get("keywords") or [],
        "sub_clause": raw.get("sub_clause", ""),
        "index": raw.get("index"),
        "logic_rules": {
            "action": logic.get("action", ""),
            "target": logic.get("target") or [],
            "condition": logic.get("condition") or [],
            "forbidden": logic.get("forbidden") or [],
            "responsibility": logic.get("responsibility", ""),
        },
        "category": CATEGORY_ALIASES.get(category, category),
    }


@lru_cache(maxsize=1)
def load_rules() -> List[RuleModel]:
    rule_file = _resolve_rule_file()
    with rule_file.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return [RuleModel(**_normalize_rule(item)) for item in payload]


def refresh_rules() -> List[RuleModel]:
    load_rules.cache_clear()
    return load_rules()


def get_rule_by_id(rule_id: str) -> RuleModel | None:
    for rule in load_rules():
        if rule.id == rule_id:
            return rule
    return None
