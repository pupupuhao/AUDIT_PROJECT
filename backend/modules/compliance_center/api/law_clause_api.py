from typing import List

from fastapi import APIRouter, Depends

from app.core.middleware import LogRoute
from app.core.security import check_permissions
from modules.compliance_center.schemas import law_clause as LawClauseSchema
from modules.compliance_center.services.law_clause import service as LawClauseService
from modules.system.schemas import common as BaseSchema
from modules.system.schemas.common import QueryData


router = APIRouter(prefix="/law-clauses", tags=["法规条款管理"], route_class=LogRoute)

Response = BaseSchema.Response
ListAll = BaseSchema.ListAll

law_clause_list_schema = ListAll[List[LawClauseSchema.LawClauseRead]]


@router.get("", summary="法规条款列表")
async def law_clause_list(
    query: QueryData = Depends(), _: dict = Depends(check_permissions)
) -> Response[law_clause_list_schema]:
    return await LawClauseService.get_items(query.offset, query.limit)


@router.post("/query", summary="法规条款查询")
async def law_clause_query(
    query: LawClauseSchema.LawClauseQuery, _: dict = Depends(check_permissions)
) -> Response[law_clause_list_schema]:
    return await LawClauseService.query_items(query)


@router.post("", summary="法规条款新增")
async def law_clause_create(
    data: LawClauseSchema.LawClauseIn, _: dict = Depends(check_permissions)
) -> Response[LawClauseSchema.LawClauseRead]:
    return await LawClauseService.create_item(data)


@router.put("/{pk}", summary="法规条款更新")
async def law_clause_update(
    pk: int, data: LawClauseSchema.LawClauseIn, _: dict = Depends(check_permissions)
) -> Response:
    return await LawClauseService.update_item(pk, data)


@router.delete("/{pk}", summary="法规条款删除")
async def law_clause_delete(pk: int, _: dict = Depends(check_permissions)) -> Response:
    return await LawClauseService.delete_item(pk)
