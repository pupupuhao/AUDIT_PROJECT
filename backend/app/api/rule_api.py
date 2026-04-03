from fastapi import APIRouter, HTTPException

from app.services.rule_service import get_rule_by_id, load_rules, refresh_rules


router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("")
def list_rules(limit: int = 20):
    rules = load_rules()
    return {
        "total": len(rules),
        "items": [rule.model_dump() for rule in rules[:limit]],
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
