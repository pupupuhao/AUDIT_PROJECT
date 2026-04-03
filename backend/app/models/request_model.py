from typing import List, Optional

from pydantic import BaseModel, Field


class AuditRequest(BaseModel):
    application_text: str = Field(..., description="维修资金申请描述")
    project_name: Optional[str] = Field(default=None, description="项目名称")
    amount: Optional[float] = Field(default=None, description="申请金额")
    docs: List[str] = Field(default_factory=list, description="已提供材料")
    applicant: Optional[str] = Field(default=None, description="申请主体")
    use_case: Optional[str] = Field(default=None, description="用途分类")
    top_k: int = Field(default=5, ge=1, le=20, description="召回规则数量")


class SearchRequest(BaseModel):
    query: str = Field(..., description="检索文本")
    top_k: int = Field(default=5, ge=1, le=20)
