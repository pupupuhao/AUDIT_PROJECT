from pydantic import BaseModel, Field

from modules.system.schemas.common import QueryData, ReadBase


class LawClauseBasic(BaseModel):
    law_name: str = Field(..., description="法规名称", max_length=255)
    clause_label: str = Field(..., description="条款编号", max_length=100)
    full_title: str = Field("", description="完整标题")
    content: str = Field(..., description="条款内容")


class LawClauseIn(LawClauseBasic):
    pass


class LawClauseRead(LawClauseBasic, ReadBase):
    pass


class LawClauseQuery(QueryData):
    law_name: str = Field("", description="法规名称")
    clause_label: str = Field("", description="条款编号")
    full_title: str = Field("", description="完整标题")
