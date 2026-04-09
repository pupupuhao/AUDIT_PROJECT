import math
import re
from collections import Counter
from typing import Iterable, List

from app.db.pgvector import get_pgvector_store
from modules.audit.schemas.rule_model import RetrievalResult, RuleModel
from modules.audit.services.rule_service import load_rules


TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fa5]{2,}|[a-zA-Z0-9_]+")


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
