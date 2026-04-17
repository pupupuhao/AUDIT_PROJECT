from fastapi.encoders import jsonable_encoder

from app.core.dbhelper import RoleDao, UserDao, UserRoleDao, has_roles
from app.core.security import get_password_hash
from app.core.service import Service


class UserService(Service):
    ROLE_PRIORITY = ("super_admin", "system_admin", "auditor", "viewer")

    def __init__(self):
        super(UserService, self).__init__(UserDao)

    @staticmethod
    def _validate_role_assignments(roles):
        if not roles:
            return "请至少分配一个角色"

        role_ids = [role.rid for role in roles]
        if len(role_ids) != len(set(role_ids)):
            return "同一用户不能重复分配相同角色"

        invalid_status = [role.status for role in roles if role.status not in (1, 5)]
        if invalid_status:
            return "角色状态仅支持 1（普通）或 5（激活）"

        active_count = sum(1 for role in roles if role.status == 5)
        if active_count > 1:
            return "同一用户最多只能有一个激活角色"

        return None

    async def create_item(self, data):
        """创建用户"""
        # 检查用户是否存在
        if await self.dao.select({"username": data.username}) is not None:
            return dict(code=400, msg="用户名已存在")
        rids = data.roles
        role_error = self._validate_role_assignments(rids)
        if role_error:
            return dict(code=400, msg=role_error)
        del data.roles
        data.password = get_password_hash(data.password)
        # 检查选中的角色是否存在
        for role in rids:
            if await RoleDao.select(dict(id=role.rid, status__not=9)) is None:
                return dict(code=400, msg=f"角色{role.rid}不存在")

        # 创建用户- 用户表写入数据
        user_obj = await UserDao.insert(data.dict())
        # 关联表写入数据
        await UserRoleDao.inserts(
            [dict(rid=role.rid, uid=user_obj.id, status=role.status) for role in rids]
        )
        return dict(data=user_obj)

    async def get_item(self, pk):
        """获取用户信息"""
        user_obj = await self.dao.select({"id": pk})
        if user_obj is None:
            return dict(code=400, msg="用户不存在")
        roles = await has_roles(user_obj.id)
        return dict(data=dict(**jsonable_encoder(user_obj), roles=roles))

    async def update_item(self, pk, data):
        """用户编辑修改"""
        if await self.dao.select({"id": pk}) is None:
            return dict(code=400, msg="用户不存在")

        rids = data.roles
        role_error = self._validate_role_assignments(rids)
        if role_error:
            return dict(code=400, msg=role_error)
        del data.roles
        for role in rids:
            if await RoleDao.select({"id": role.rid, "status__not": 9}) is None:
                return dict(code=400, msg=f"角色{role.rid}不存在")
        # 更新用户
        if data.password != "加密之后的密码":
            data.password = get_password_hash(data.password)
        else:
            del data.password
        await UserDao.update(dict(id=pk), data.dict())

        # todo 1. 先前有的角色，这次更新成没有 2. 先前没有的角色 这次更新成有， 3. 只更新了状态

        roles = await has_roles(pk)

        # 2. 将先有的数据标记 删除
        [
            await UserRoleDao.update(dict(rid=role["id"], uid=pk), dict(status=9))
            for role in roles
        ]

        # 2. 新增次此更新的数据
        await UserRoleDao.inserts(
            [dict(role.dict(), uid=pk, status=role.status) for role in rids]
        )
        return dict()

    @staticmethod
    async def ensure_login_active_role(uid):
        """登录时根据角色优先级自动激活当前角色。"""
        roles = await has_roles(uid)
        if not roles:
            return None

        priority_map = {
            role_name: index for index, role_name in enumerate(UserService.ROLE_PRIORITY)
        }
        active_role = min(
            roles,
            key=lambda role: (priority_map.get(role["name"], len(priority_map)), role["id"]),
        )

        await UserRoleDao.update(dict(uid=uid, status__not=9), dict(status=1))
        await UserRoleDao.update(
            dict(uid=uid, rid=active_role["id"], status__not=9), dict(status=5)
        )
        return active_role

    @staticmethod
    async def change_current_role(uid, rid):
        """用户切换角色"""
        # 1.将用户id 未删除角色状态置为正常 1 （ 除切换角色id ）
        await UserRoleDao.update(
            dict(uid=uid, rid__not=rid, status__not=9), dict(status=1)
        )
        # 2.将用户id 角色id 和当前角色匹配的数据置为选中
        res = await UserRoleDao.update(
            dict(uid=uid, rid=rid, status__not=9), dict(status=5)
        )
        if res == 0:
            return dict(code=400, msg=f"角色不存在{res}")
        return dict()


service = UserService()
