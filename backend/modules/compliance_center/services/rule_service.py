import json
import math
import re
from csv import DictReader
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List

from app.core.embedding import embed_text
from app.db.pgvector import get_pgvector_store
from modules.compliance_center.schemas.rule_model import RetrievalResult, RuleModel


BASE_DIR = Path(__file__).resolve().parents[3]
RULE_PATHS = [
    BASE_DIR / "data" / "rules" / "rules_db_new_pure_with_logic.json",
    # BASE_DIR / "data" / "rules" / "rules_db_with_llm.json",
    BASE_DIR / "data" / "chunks" / "rules_db_with_category.json",
    # BASE_DIR / "data" / "chunks" / "rules_db.json",
]
LOCAL_VECTOR_PATH = BASE_DIR / "data" / "rules" / "rules_db_new_pure_vector.csv"
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fa5]{2,}|[a-zA-Z0-9_]+")


def _resolve_rule_file() -> Path:
    for path in RULE_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError("未找到规则库文件，请先执行规则构建脚本")


def _normalize_rule(raw: dict) -> dict:
    logic = raw.get("logic_rules") or {}
    content = raw.get("content") or raw.get("display_text") or raw.get("clean_text") or ""
    clean_text = raw.get("clean_text") or raw.get("embedding_text") or content
    return {
        "id": raw.get("id", ""),
        "doc_id": raw.get("doc_id", ""),
        "parent_id": raw.get("parent_id"),
        "law_name": raw.get("law_name", ""),
        "node_level": raw.get("node_level"),
        "node_type": raw.get("node_type", ""),
        "clause_label": raw.get("clause_label", ""),
        "item_label": raw.get("item_label", ""),
        "subitem_label": raw.get("subitem_label", ""),
        "sub_clause": raw.get("sub_clause", ""),
        "full_title": raw.get("full_title", ""),
        "title_text": raw.get("title_text", ""),
        "content": content,
        "clean_text": clean_text,
        "embedding_text": raw.get("embedding_text", clean_text),
        "parent_context": raw.get("parent_context", ""),
        "path": raw.get("path") or [],
        "index": raw.get("index"),
        "logic_rules": logic,
        "category": raw.get("category", ""),
    }


@lru_cache(maxsize=1)
def load_rules() -> List[RuleModel]:
    rule_file = _resolve_rule_file()
    with rule_file.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return [RuleModel(**_normalize_rule(item)) for item in payload]


def refresh_rules() -> List[RuleModel]:
    load_rules.cache_clear()
    load_local_vector_rules.cache_clear()
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


def _parse_json_text(raw: str, default):
    text = (raw or "").strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def _parse_embedding(raw: str) -> List[float]:
    text = (raw or "").strip()
    if not text:
        return []
    try:
        return [float(item) for item in text.strip("[]").split(",") if item.strip()]
    except ValueError:
        return []


def _normalize_local_vector_rule(raw: dict) -> dict:
    logic_rules = _parse_json_text(raw.get("logic_rules", ""), {})
    if logic_rules and not logic_rules.get("required_fields"):
        logic_rules["required_fields"] = _parse_json_text(raw.get("required_fields", ""), [])
    return {
        "id": raw.get("rule_id", ""),
        "doc_id": raw.get("doc_id", ""),
        "parent_id": raw.get("parent_id") or None,
        "law_name": raw.get("law_name", ""),
        "node_level": int(raw.get("node_level", 0) or 0),
        "node_type": raw.get("node_type", ""),
        "clause_label": raw.get("clause_label", ""),
        "item_label": raw.get("item_label", ""),
        "subitem_label": raw.get("subitem_label", ""),
        "sub_clause": raw.get("sub_clause", ""),
        "full_title": raw.get("full_title", ""),
        "title_text": raw.get("title_text", ""),
        "content": raw.get("content", ""),
        "clean_text": raw.get("clean_text", ""),
        "embedding_text": raw.get("embedding_text", ""),
        "parent_context": raw.get("parent_context", ""),
        "path": _parse_json_text(raw.get("path", ""), []),
        "index": None,
        "logic_rules": logic_rules,
        "category": raw.get("category", ""),
        "_embedding": _parse_embedding(raw.get("embedding", "")),
    }


@lru_cache(maxsize=1)
def load_local_vector_rules() -> List[dict]:
    if not LOCAL_VECTOR_PATH.exists():
        return []
    with LOCAL_VECTOR_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = DictReader(file)
        return [_normalize_local_vector_rule(row) for row in reader]


def _vector_score(query_vector: List[float], rule_vector: List[float]) -> float:
    if not query_vector or not rule_vector:
        return 0.0
    length = min(len(query_vector), len(rule_vector))
    if length == 0:
        return 0.0
    return round(sum(query_vector[idx] * rule_vector[idx] for idx in range(length)), 4)


def _filter_local_vector_rules(
    keyword: str = "",
    category: str = "",
    law_name: str = "",
) -> List[dict]:
    rules = load_local_vector_rules()
    if keyword:
        needle = keyword.lower()
        rules = [
            rule
            for rule in rules
            if needle in rule["law_name"].lower()
            or needle in rule["content"].lower()
            or needle in rule["full_title"].lower()
            or needle in rule["id"].lower()
            or needle in rule["clause_label"].lower()
        ]
    if category:
        rules = [rule for rule in rules if rule["category"] == category]
    if law_name:
        rules = [rule for rule in rules if rule["law_name"] == law_name]
    return rules


def _text_blob(rule: RuleModel) -> str:
    logic = rule.logic_rules
    parts: List[str] = [
        rule.law_name,
        rule.clause_label,
        rule.item_label,
        rule.subitem_label,
        rule.full_title,
        rule.title_text,
        rule.content,
        rule.clean_text,
        rule.embedding_text,
        rule.parent_context,
        rule.category,
        logic.rule_nature,
        logic.audit_stage,
        logic.audit_dimension,
        logic.judgement_mode,
        " ".join(logic.required_fields),
        " ".join(logic.required_documents),
        " ".join(logic.risk_points),
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
    field_hits = _keyword_overlap(query_token_set, rule.logic_rules.required_fields)
    doc_hits = _keyword_overlap(query_token_set, rule.logic_rules.required_documents)
    risk_hits = _keyword_overlap(query_token_set, rule.logic_rules.risk_points)

    exact_bonus = 0.0
    if rule.full_title and rule.full_title in query:
        exact_bonus += 0.25
    if any(item and item in query for item in rule.logic_rules.required_fields):
        exact_bonus += 0.2
    if any(item and item in query for item in rule.logic_rules.required_documents):
        exact_bonus += 0.15

    score = cosine + exact_bonus + 0.1 * len(field_hits) + 0.08 * len(doc_hits) + 0.08 * len(risk_hits)

    reasons: List[str] = []
    if field_hits:
        reasons.append(f"命中字段要求: {', '.join(field_hits)}")
    if doc_hits:
        reasons.append(f"命中资料要求: {', '.join(doc_hits)}")
    if risk_hits:
        reasons.append(f"命中风险点: {', '.join(risk_hits)}")
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
            db_results = store.search_new_pure_rules(query, top_k=top_k)
            if db_results:
                return [
                    RetrievalResult(
                        rule=RuleModel(**_normalize_rule(item)),
                        score=round(item.get("score", 0), 4),
                        match_reasons=["rule_db_new_pure_vector 语义召回"],
                    )
                    for item in db_results
                ]
        except Exception:
            pass

    local_vector_rules = load_local_vector_rules()
    if local_vector_rules:
        query_vector = embed_text(query)
        scored_results = sorted(
            (
                RetrievalResult(
                    rule=RuleModel(**_normalize_rule(item)),
                    score=_vector_score(query_vector, item.get("_embedding", [])),
                    match_reasons=["rules_db_new_pure_vector.csv 本地兜底召回"],
                )
                for item in local_vector_rules
            ),
            key=lambda item: item.score,
            reverse=True,
        )
        filtered = [item for item in scored_results[:top_k] if item.score > 0]
        if filtered:
            return filtered

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
            return store.list_new_pure_rules(
                offset=offset,
                limit=limit,
                keyword=keyword,
                category=category,
                law_name=law_name,
            )
        except Exception:
            pass

    local_vector_rules = _filter_local_vector_rules(keyword=keyword, category=category, law_name=law_name)
    if local_vector_rules:
        start = max(offset - 1, 0) * limit
        end = start + limit
        latest_updated_at = None
        try:
            latest_updated_at = LOCAL_VECTOR_PATH.stat().st_mtime
        except OSError:
            latest_updated_at = None
        return {
            "total": len(local_vector_rules),
            "items": [{k: v for k, v in rule.items() if k != "_embedding"} for rule in local_vector_rules[start:end]],
            "categories": sorted({rule["category"] for rule in load_local_vector_rules() if rule["category"]}),
            "law_count": len({rule["law_name"] for rule in local_vector_rules if rule["law_name"]}),
            "latest_updated_at": None if latest_updated_at is None else datetime.fromtimestamp(latest_updated_at).isoformat(),
        }

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
        "categories": sorted({rule.category for rule in load_rules() if rule.category}),
        "law_count": len({rule.law_name for rule in rules if rule.law_name}),
        "latest_updated_at": None,
    }


def count_rules_by_law_names(law_names: list[str]) -> dict[str, int]:
    store = get_pgvector_store()
    if store:
        try:
            return store.count_new_pure_rules_by_law_names(law_names)
        except Exception:
            pass

    local_vector_rules = load_local_vector_rules()
    if local_vector_rules:
        rule_counter: dict[str, int] = {}
        targets = {name for name in law_names if name}
        for rule in local_vector_rules:
            if rule["law_name"] in targets:
                rule_counter[rule["law_name"]] = rule_counter.get(rule["law_name"], 0) + 1
        if rule_counter:
            return rule_counter

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
            rule = store.get_new_pure_rule(rule_id)
            if rule:
                return rule
        except Exception:
            pass

    for rule in load_local_vector_rules():
        if rule["id"] == rule_id:
            return {k: v for k, v in rule.items() if k != "_embedding"}

    rule = get_rule_by_id(rule_id)
    return rule.model_dump() if rule else None


def upsert_rule_in_store(payload: dict) -> dict:
    store = get_pgvector_store()
    if not store:
        raise RuntimeError("pgvector 未启用，无法维护新规则库")

    normalized = _normalize_rule(payload)
    normalized["id"] = payload.get("id", normalized["id"])
    store.upsert_new_pure_rule(normalized)
    refresh_rules()
    return get_rule_by_id_from_store(normalized["id"]) or RuleModel(**normalized).model_dump()


def delete_rule_in_store(rule_id: str) -> bool:
    store = get_pgvector_store()
    if not store:
        raise RuntimeError("pgvector 未启用，无法维护新规则库")

    deleted = store.delete_new_pure_rule(rule_id)
    refresh_rules()
    return deleted > 0
