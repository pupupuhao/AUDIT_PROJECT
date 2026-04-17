from app.core.dbhelper import LawClauseDao
from app.core.service import Service
from modules.compliance_center.services.rule_sync_service import service as RuleSyncService


class LawClauseService(Service):
    def __init__(self):
        super(LawClauseService, self).__init__(LawClauseDao)

    async def create_item(self, data):
        exists = await self.dao.select(
            {
                "law_name": data.law_name,
                "clause_label": data.clause_label,
                "full_title": data.full_title,
                "status__not": 9,
            }
        )
        if exists is not None:
            return dict(code=400, msg="该法规条款已存在")
        clause = await self.dao.insert(data.dict())
        sync_result = RuleSyncService.sync_clause(clause)
        message = "法规条款已新增并同步规则库" if sync_result.get("synced") else "法规条款已新增，但规则库未同步"
        return dict(data=clause, msg=message)

    async def update_item(self, pk, data):
        clause = await self.dao.select({"id": pk, "status__not": 9})
        if clause is None:
            return dict(code=400, msg="法规条款不存在")

        await self.dao.update({"id": pk, "status__not": 9}, data.dict())
        clause = await self.dao.select({"id": pk, "status__not": 9})
        sync_result = RuleSyncService.sync_clause(clause)
        message = "法规条款已更新并同步规则库" if sync_result.get("synced") else "法规条款已更新，但规则库未同步"
        return dict(msg=message)

    async def delete_item(self, pk):
        clause = await self.dao.select({"id": pk, "status__not": 9})
        if clause is None:
            return dict(code=400, msg="法规条款不存在")

        await RuleSyncService.delete_clause_rules(pk)
        await self.dao.update({"id": pk, "status__not": 9}, {"status": 9})
        return dict(msg="法规条款已删除并同步规则库")


service = LawClauseService()
