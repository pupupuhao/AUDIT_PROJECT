from typing import List

from pydantic import BaseModel, Field

from modules.system.schemas.common import QueryData, ReadBase


class RoleMenuIn(BaseModel):
    """角色 -分配菜单id"""

    rid: int = Field(description="角色ID")
    menus: List[int] = Field(description="菜单ID 列表")


class RoleMenuRead(RoleMenuIn, ReadBase):
    pass


class RoleBasic(BaseModel):
    name: str = Field(None, description="角色名称")
    remark: str = Field(None, description="备注信息")


class RoleIn(RoleBasic):
    menus: List[int] = Field(..., description="菜单id列表")


class RoleRead(RoleBasic, ReadBase):
    user_count: int = Field(default=0, description="已分配用户数")
    users: List[str] = Field(default_factory=list, description="已分配用户名列表")


class RoleInfo(RoleRead):
    pass


class RoleQuery(QueryData):
    """查询模型"""

    name: str = Field("", description="角色名")
