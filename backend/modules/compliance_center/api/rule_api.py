from fastapi import APIRouter, Depends, HTTPException

from app.core.security import check_permissions
from modules.compliance_center.schemas.rule_model import RuleUpsert, SearchRequest
from modules.compliance_center.services.rule_service import (
    delete_rule_in_store,
    get_rule_by_id_from_store,
    list_rules_from_store,
    refresh_rules,
    search_rules,
    upsert_rule_in_store,
)


router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("")
def list_rules(
    limit: int = 20,
    offset: int = 1,
    keyword: str = "",
    category: str = "",
    law_name: str = "",
    _: dict = Depends(check_permissions),
):
    return list_rules_from_store(
        offset=offset,
        limit=limit,
        keyword=keyword,
        category=category,
        law_name=law_name,
    )


@router.get("/refresh")
def reload_rules(_: dict = Depends(check_permissions)):
    rules = refresh_rules()
    return {"total": len(rules), "message": "规则缓存已刷新"}


@router.get("/{rule_id}")
def get_rule(rule_id: str, _: dict = Depends(check_permissions)):
    rule = get_rule_by_id_from_store(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="rule not found")
    return rule


@router.post("/search")
def search_rule_items(request: SearchRequest, _: dict = Depends(check_permissions)):
    results = search_rules(request.query, top_k=request.top_k)
    return {
        "query": request.query,
        "count": len(results),
        "items": [item.model_dump(by_alias=True) for item in results],
    }


@router.post("")
def create_rule(payload: RuleUpsert, _: dict = Depends(check_permissions)):
    if get_rule_by_id_from_store(payload.id):
        raise HTTPException(status_code=400, detail="rule id already exists")

    try:
        return upsert_rule_in_store(payload.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.put("/{rule_id}")
def update_rule(rule_id: str, payload: RuleUpsert, _: dict = Depends(check_permissions)):
    if rule_id != payload.id:
        raise HTTPException(status_code=400, detail="rule id mismatch")

    try:
        return upsert_rule_in_store(payload.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.delete("/{rule_id}")
def delete_rule(rule_id: str, _: dict = Depends(check_permissions)):
    try:
        deleted = delete_rule_in_store(rule_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if not deleted:
        raise HTTPException(status_code=404, detail="rule not found")
    return {"msg": "规则已删除"}
