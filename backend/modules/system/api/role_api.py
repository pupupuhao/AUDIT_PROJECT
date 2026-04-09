from fastapi import APIRouter, Depends
from typing import List

from app.core.middleware import LogRoute
from app.core.security import check_permissions
from modules.system.schemas import common as BaseSchema
from modules.system.schemas import role as RoleSchema
from modules.system.schemas.common import QueryData
from modules.system.services.role import service as RoleService

router = APIRouter(prefix="/role", tags=["角色管理"], route_class=LogRoute)

Response = BaseSchema.Response
ListAll = BaseSchema.ListAll

role_list_schema = ListAll[List[RoleSchema.RoleRead]]


@router.get("", summary="角色列表")
async def role_list(
    query: QueryData = Depends(), _: dict = Depends(check_permissions)
) -> Response[role_list_schema]:
    return await RoleService.get_items(query.offset, query.limit)


@router.post("/query", summary="角色查询")
async def role_query(
    query: RoleSchema.RoleQuery, _: dict = Depends(check_permissions)
) -> Response[role_list_schema]:
    return await RoleService.query_items(query)


@router.post("", summary="角色新增")
async def role_create(
    data: RoleSchema.RoleIn, _: dict = Depends(check_permissions)
) -> Response[RoleSchema.RoleInfo]:
    return await RoleService.create_item(data)


@router.get("/{rid}/menu", summary="查询角色拥有权限")
async def role_has_menu(rid: int, _: dict = Depends(check_permissions)) -> Response:
    return await RoleService.has_tree_menus(rid)


@router.delete("/{pk}", summary="角色删除")
async def role_del(pk: int, _: dict = Depends(check_permissions)) -> Response:
    return await RoleService.delete_item(pk)


@router.put("/{pk}", summary="角色更新")
async def role_put(
    pk: int, data: RoleSchema.RoleIn, _: dict = Depends(check_permissions)
) -> Response:
    """更新角色"""
    return await RoleService.update_item(pk, data)
