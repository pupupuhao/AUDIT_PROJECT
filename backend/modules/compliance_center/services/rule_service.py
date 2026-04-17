import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List

from app.db.pgvector import get_pgvector_store
from modules.compliance_center.schemas.rule_model import RetrievalResult, RuleModel


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
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fa5]{2,}|[a-zA-Z0-9_]+")


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
            "required_docs": logic.get("required_docs") or raw.get("required_docs") or [],
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


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return TOKEN_PATTERN.findall(text.lower())


def _text_blob(rule: RuleModel) -> str:
    logic = rule.logic_rules
    parts: List[str] = [
        rule.law_name,
        rule.clause_label,
        rule.full_title,
        rule.content,
        rule.clean_text,
        rule.parent_context,
        rule.category,
        " ".join(rule.keywords),
        " ".join(logic.target),
        " ".join(logic.condition),
        " ".join(logic.forbidden),
        str(logic.responsibility),
        logic.action,
    ]
    return " ".join(part for part in parts if part)


def _keyword_overlap(query_tokens: set[str], candidates: Iterable[str]) -> List[str]:
    hits = []
    for item in candidates:
        item = item.strip()
        if not item:
            continue
        item_tokens = set(tokenize(item))
        if item_tokens and item_tokens & query_tokens:
            hits.append(item)
    return hits[:4]


def _score_rule(query: str, query_tokens: List[str], rule: RuleModel) -> RetrievalResult:
    blob = _text_blob(rule)
    rule_tokens = tokenize(blob)
    query_counter = Counter(query_tokens)
    rule_counter = Counter(rule_tokens)

    dot = sum(query_counter[token] * rule_counter[token] for token in query_counter)
    q_norm = math.sqrt(sum(value * value for value in query_counter.values()))
    r_norm = math.sqrt(sum(value * value for value in rule_counter.values()))
    cosine = dot / (q_norm * r_norm) if q_norm and r_norm else 0.0

    query_token_set = set(query_tokens)
    keyword_hits = _keyword_overlap(query_token_set, rule.keywords)
    target_hits = _keyword_overlap(query_token_set, rule.logic_rules.target)
    forbidden_hits = _keyword_overlap(query_token_set, rule.logic_rules.forbidden)
    condition_hits = _keyword_overlap(query_token_set, rule.logic_rules.condition)

    exact_bonus = 0.0
    if any(keyword and keyword in query for keyword in rule.keywords):
        exact_bonus += 0.25
    if any(item and item in query for item in rule.logic_rules.forbidden):
        exact_bonus += 0.3
    if any(item and item in query for item in rule.logic_rules.target):
        exact_bonus += 0.2

    score = cosine + exact_bonus + 0.08 * len(keyword_hits) + 0.1 * len(target_hits) + 0.12 * len(forbidden_hits)

    reasons: List[str] = []
    if keyword_hits:
        reasons.append(f"命中关键词: {', '.join(keyword_hits)}")
    if target_hits:
        reasons.append(f"命中适用对象: {', '.join(target_hits)}")
    if forbidden_hits:
        reasons.append(f"命中禁止事项: {', '.join(forbidden_hits)}")
    if condition_hits:
        reasons.append(f"命中触发条件: {', '.join(condition_hits)}")
    if not reasons and score > 0:
        reasons.append("文本语义相近")

    return RetrievalResult(rule=rule, score=round(score, 4), match_reasons=reasons)


def search_rules(query: str, top_k: int = 5) -> List[RetrievalResult]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    store = get_pgvector_store()
    if store:
        try:
            db_results = store.search_rules(query, top_k=top_k)
            if db_results:
                return [
                    RetrievalResult(
                        rule=RuleModel(
                            id=item.get("id", ""),
                            law_name=item.get("law_name", ""),
                            clause_label=item.get("clause_label", ""),
                            full_title=item.get("full_title", ""),
                            content=item.get("content", ""),
                            clean_text=item.get("content", ""),
                            parent_context=item.get("content", ""),
                            keywords=item.get("keywords", []),
                            logic_rules=item.get("logic_rules", {}),
                            category=item.get("category", "使用范围合规审计"),
                        ),
                        score=round(item.get("score", 0), 4),
                        match_reasons=["pgvector 语义召回"],
                    )
                    for item in db_results
                ]
        except Exception:
            pass

    scored = [_score_rule(query, query_tokens, rule) for rule in load_rules()]
    scored.sort(key=lambda item: item.score, reverse=True)
    return [item for item in scored[:top_k] if item.score > 0]


def list_rules_from_store(
    offset: int = 1,
    limit: int = 20,
    keyword: str = "",
    category: str = "",
    law_name: str = "",
) -> dict:
    store = get_pgvector_store()
    if store:
        try:
            return store.list_rules(
                offset=offset,
                limit=limit,
                keyword=keyword,
                category=category,
                law_name=law_name,
            )
        except Exception:
            pass

    rules = load_rules()
    if keyword:
        needle = keyword.lower()
        rules = [
            rule
            for rule in rules
            if needle in rule.law_name.lower()
            or needle in rule.content.lower()
            or needle in rule.full_title.lower()
            or needle in rule.id.lower()
        ]
    if category:
        rules = [rule for rule in rules if rule.category == category]
    if law_name:
        rules = [rule for rule in rules if rule.law_name == law_name]

    start = max(offset - 1, 0) * limit
    end = start + limit
    return {
        "total": len(rules),
        "items": [rule.model_dump() for rule in rules[start:end]],
        "categories": sorted({rule.category for rule in load_rules()}),
        "law_count": len({rule.law_name for rule in rules if rule.law_name}),
        "latest_updated_at": None,
    }


def count_rules_by_law_names(law_names: list[str]) -> dict[str, int]:
    store = get_pgvector_store()
    if store:
        try:
            return store.count_rules_by_law_names(law_names)
        except Exception:
            pass

    rule_counter: dict[str, int] = {}
    targets = {name for name in law_names if name}
    for rule in load_rules():
        if rule.law_name in targets:
            rule_counter[rule.law_name] = rule_counter.get(rule.law_name, 0) + 1
    return rule_counter


def get_rule_by_id_from_store(rule_id: str) -> dict | None:
    store = get_pgvector_store()
    if store:
        try:
            rule = store.get_rule(rule_id)
            if rule:
                return rule
        except Exception:
            pass

    rule = get_rule_by_id(rule_id)
    return rule.model_dump() if rule else None


def upsert_rule_in_store(payload: dict) -> dict:
    store = get_pgvector_store()
    if not store:
        raise RuntimeError("pgvector 未启用，无法维护规则库")

    normalized = _normalize_rule(payload)
    normalized["id"] = payload.get("id", normalized["id"])
    normalized["logic_rules"]["required_docs"] = (
        payload.get("logic_rules", {}).get("required_docs")
        or normalized["logic_rules"].get("required_docs")
        or []
    )
    store.upsert_rule(normalized)
    refresh_rules()
    return get_rule_by_id_from_store(normalized["id"]) or RuleModel(**normalized).model_dump()


def delete_rule_in_store(rule_id: str) -> bool:
    store = get_pgvector_store()
    if not store:
        raise RuntimeError("pgvector 未启用，无法维护规则库")

    deleted = store.delete_rule(rule_id)
    refresh_rules()
    return deleted > 0


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
