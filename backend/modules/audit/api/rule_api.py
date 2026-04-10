from fastapi import APIRouter, HTTPException

from modules.audit.services.rule_service import (
    get_rule_by_id,
    load_rules,
    refresh_rules,
)


router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("")
def list_rules(
    limit: int = 20,
    offset: int = 1,
    keyword: str = "",
    category: str = "",
):
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

    start = max(offset - 1, 0) * limit
    end = start + limit
    categories = sorted({rule.category for rule in load_rules()})
    return {
        "total": len(rules),
        "items": [rule.model_dump() for rule in rules[start:end]],
        "categories": categories,
    }


@router.get("/refresh")
def reload_rules():
    rules = refresh_rules()
    return {"total": len(rules), "message": "规则缓存已刷新"}


@router.get("/{rule_id}")
def get_rule(rule_id: str):
    rule = get_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    return rule.model_dump()
