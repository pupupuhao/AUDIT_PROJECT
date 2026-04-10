import json
import re
from functools import lru_cache
from pathlib import Path
from typing import List

from modules.audit.schemas.rule_model import RuleModel


BASE_DIR = Path(__file__).resolve().parents[3]
RAW_LAW_PATH = BASE_DIR / "data" / "raw" / "law_policy.md"
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


def _parse_law_documents(markdown: str) -> list[dict]:
    documents: list[dict] = []
    current_doc: dict | None = None
    current_section: dict | None = None

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("## "):
            if current_section and current_doc is not None:
                current_doc["sections"].append(current_section)
            if current_doc is not None:
                documents.append(current_doc)

            title = line[3:].strip()
            current_doc = {
                "id": f"LAW_{len(documents) + 1:03d}",
                "title": title,
                "doc_type": _infer_law_type(title),
                "sections": [],
                "content": "",
            }
            current_section = None
            continue

        if line.startswith("### "):
            if current_doc is None:
                continue
            if current_section is not None:
                current_doc["sections"].append(current_section)

            heading = line[4:].strip()
            current_section = {
                "title": heading,
                "content": "",
            }
            continue

        if current_doc is None:
            continue

        if current_section is None:
            current_section = {
                "title": "正文",
                "content": line,
            }
        else:
            current_section["content"] = (
                f"{current_section['content']}\n{line}".strip()
                if current_section["content"]
                else line
            )

    if current_section and current_doc is not None:
        current_doc["sections"].append(current_section)
    if current_doc is not None:
        documents.append(current_doc)

    for doc in documents:
        doc["section_count"] = len(doc["sections"])
        doc["content"] = "\n\n".join(
            [f"{section['title']}\n{section['content']}".strip() for section in doc["sections"]]
        )
        doc["rule_count"] = 0

    return documents


def _infer_law_type(title: str) -> str:
    mapping = {
        "管理办法": "管理办法",
        "通知": "通知",
        "意见": "意见",
        "规定": "规定",
        "民法典": "法律",
        "工作意见": "工作意见",
    }
    for key, value in mapping.items():
        if key in title:
            return value
    return "法规文件"


@lru_cache(maxsize=1)
def load_law_documents() -> list[dict]:
    if not RAW_LAW_PATH.exists():
        return []

    documents = _parse_law_documents(RAW_LAW_PATH.read_text(encoding="utf-8"))
    rule_counter: dict[str, int] = {}
    for rule in load_rules():
        rule_counter[rule.law_name] = rule_counter.get(rule.law_name, 0) + 1

    for doc in documents:
        normalized_title = re.sub(r"\s+", "", doc["title"])
        for law_name, count in rule_counter.items():
            if normalized_title and normalized_title in re.sub(r"\s+", "", law_name):
                doc["rule_count"] = count
                break

    return documents


def refresh_law_documents() -> list[dict]:
    load_law_documents.cache_clear()
    return load_law_documents()
