from typing import List

from pydantic import BaseModel, Field


class LawDocumentSectionRead(BaseModel):
    title: str = Field(..., description="条款标题")
    content: str = Field(..., description="条款内容")


class LawDocumentRead(BaseModel):
    id: str = Field(..., description="法规文档ID")
    title: str = Field(..., description="法规名称")
    section_count: int = Field(..., description="条款数量")
    rule_count: int = Field(..., description="关联规则数")
    sections: List[LawDocumentSectionRead] = Field(default_factory=list, description="条款列表")
