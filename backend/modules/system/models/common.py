from tortoise import fields, models


class Table(models.Model):
    """
    抽象模型。
    默认语义：status=1 为有效，status=9 为逻辑删除。
    例外：sys_user_role 额外使用 status=5 表示当前激活角色。
    """

    id = fields.IntField(pk=True, description="主键")
    status = fields.SmallIntField(default=1, description="状态：默认 1 有效、9 删除；用户角色关系表中的 5 表示激活角色")
    created = fields.DatetimeField(auto_now_add=True, description="创建时间", null=True)
    modified = fields.DatetimeField(auto_now=True, description="更新时间", null=True)

    class Meta:
        abstract = True
        ordering = ["-created"]
        indexes = ("status",)
