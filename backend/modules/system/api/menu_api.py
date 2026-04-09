from fastapi import APIRouter, Depends

from app.core.middleware import LogRoute
from app.core.security import check_permissions
from modules.system.schemas import common as BaseSchema
from modules.system.schemas import menu as MenuSchema
from modules.system.services.menu import service as MenuService

router = APIRouter(prefix="/menu", tags=["菜单管理"], route_class=LogRoute)

Response = BaseSchema.Response


@router.post("", summary="菜单新增")
async def menu_add(
    data: MenuSchema.MenuIn, _: dict = Depends(check_permissions)
) -> Response[MenuSchema.MenuRead]:
    return await MenuService.create_item(data)


@router.get("", summary="菜单列表")
async def menu_arr(_: dict = Depends(check_permissions)) -> Response:
    return await MenuService.get_items()


@router.delete("/{pk}", summary="菜单删除")
async def menu_del(pk: int, _: dict = Depends(check_permissions)) -> Response:
    return await MenuService.delete_item(pk)


@router.put("/{pk}", summary="菜单更新")
async def menu_put(
    pk: int, data: MenuSchema.MenuIn, _: dict = Depends(check_permissions)
) -> Response:
    """更新菜单"""
    return await MenuService.update_item(pk, data)
