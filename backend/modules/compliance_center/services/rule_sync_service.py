import re
from typing import Any

from app.db.pgvector import get_pgvector_store
from modules.compliance_center.models.law_clause import LawClauseModel
from modules.compliance_center.services.rule_service import refresh_rules
from pipelines.rule_builder import enhance_rule


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _extract_label(title: str) -> str:
    standard = re.search(r"第[一二三四五六七八九十百千万零两\d]+条", title or "")
    if standard:
        return standard.group()

    major = re.search(r"^[一二三四五六七八九十百千万零两\d]+[、.]", (title or "").strip())
    if major:
        return major.group()[:-1]

    sub = re.search(r"[（(][一二三四五六七八九十百千万零两\d]+[）)]", (title or "").strip())
    if sub:
        return sub.group()

    return ""


def _split_sub_clauses(text: str) -> list[str]:
    parts = re.split(r"(?=[（(][一二三四五六七八九十百千万零两\d]+[）)])", text or "")
    return [part.strip() for part in parts if part.strip()]


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"[\u4e00-\u9fa5]{2,}", text or "")
    deduped: list[str] = []
    for word in words:
        if word not in deduped:
            deduped.append(word)
    return deduped[:6]


class RuleSyncService:
    @staticmethod
    def _rule_prefix(clause_id: int) -> str:
        return f"LC_{clause_id}_"

    @classmethod
    def _build_chunks(cls, clause: LawClauseModel) -> list[dict[str, Any]]:
        full_title = _normalize_text(clause.full_title or clause.clause_label or "")
        clause_label = _extract_label(full_title) or clause.clause_label or ""
        content = _normalize_text(clause.content)
        sub_parts = _split_sub_clauses(content) or [content]

        chunks: list[dict[str, Any]] = []
        for index, sub in enumerate(sub_parts):
            cleaned = _normalize_text(sub)
            chunks.append(
                {
                    "id": f"{cls._rule_prefix(clause.id)}{index:03d}",
                    "law_name": clause.law_name,
                    "clause_label": clause_label,
                    "full_title": full_title,
                    "content": cleaned,
                    "clean_text": cleaned,
                    "parent_context": content,
                    "keywords": _extract_keywords(cleaned),
                    "sub_clause": _extract_label(cleaned),
                    "index": index,
                    "logic_rules": {
                        "action": "",
                        "target": [],
                        "condition": [],
                        "forbidden": [],
                        "responsibility": "",
                        "threshold": None,
                        "required_docs": [],
                        "is_emergency": False,
                    },
                }
            )

        return chunks

    @classmethod
    def sync_clause(cls, clause: LawClauseModel) -> dict[str, Any]:
        store = get_pgvector_store()
        if not store:
            return {"synced": False, "reason": "pgvector_unavailable"}

        store.delete_rules_by_prefix(cls._rule_prefix(clause.id))

        created = 0
        for chunk in cls._build_chunks(clause):
            enhanced = enhance_rule(chunk)
            store.upsert_rule(enhanced)
            created += 1

        refresh_rules()
        return {"synced": True, "rule_count": created}

    @classmethod
    def delete_clause_rules(cls, clause_id: int) -> dict[str, Any]:
        store = get_pgvector_store()
        if not store:
            return {"synced": False, "reason": "pgvector_unavailable"}

        deleted = store.delete_rules_by_prefix(cls._rule_prefix(clause_id))
        refresh_rules()
        return {"synced": True, "deleted": deleted}


service = RuleSyncService()
