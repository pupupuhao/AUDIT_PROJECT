from app.core.dbhelper import LawClauseDao
from app.core.service import Service


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
        return dict(data=await self.dao.insert(data.dict()))


service = LawClauseService()
