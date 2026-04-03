from typing import List, Optional

from pydantic import BaseModel, Field


class AuditRequest(BaseModel):
    application_text: str = Field(default="", description="维修资金申请描述或原始文本")
    raw_text: str = Field(default="", description="OCR/抽取得到的原始文本")

    project_name: Optional[str] = Field(default=None, description="项目名称")
    applicant: Optional[str] = Field(default=None, description="申请单位或申请主体")
    use_case: Optional[str] = Field(default=None, description="维修类型/用途分类")
    amount: Optional[float] = Field(default=None, description="申请金额")
    data_source: Optional[str] = Field(default=None, description="数据来源")
    knowledge_base_name: Optional[str] = Field(default=None, description="所选知识库名称")

    voting_start_date: Optional[str] = Field(default=None, description="表决开始日期")
    voting_end_date: Optional[str] = Field(default=None, description="表决结束日期")
    publicity_start_date: Optional[str] = Field(default=None, description="公示开始日期")
    publicity_end_date: Optional[str] = Field(default=None, description="公示结束日期")

    total_households: Optional[int] = Field(default=None, description="总业主户数")
    participating_households: Optional[int] = Field(default=None, description="参与表决户数")
    agreed_households: Optional[int] = Field(default=None, description="同意户数")
    agree_ratio: Optional[float] = Field(default=None, description="同意比例")
    publicity_locations: List[str] = Field(default_factory=list, description="公示位置")

    docs: List[str] = Field(default_factory=list, description="已提供材料")
    extracted_fields: dict = Field(default_factory=dict, description="AI抽取出的补充字段")
    top_k: int = Field(default=5, ge=1, le=20, description="召回规则数量")


class SearchRequest(BaseModel):
    query: str = Field(..., description="检索文本")
    top_k: int = Field(default=5, ge=1, le=20)
