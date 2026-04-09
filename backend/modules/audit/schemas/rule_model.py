from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogicRule(BaseModel):
    action: str = ""
    target: List[str] = Field(default_factory=list)
    condition: List[str] = Field(default_factory=list)
    forbidden: List[str] = Field(default_factory=list)
    required_docs: List[str] = Field(default_factory=list)
    responsibility: Any = ""


class RuleModel(BaseModel):
    id: str
    law_name: str = ""
    clause_label: str = ""
    full_title: str = ""
    content: str = ""
    clean_text: str = ""
    parent_context: str = ""
    keywords: List[str] = Field(default_factory=list)
    sub_clause: str = ""
    index: Optional[int] = None
    logic_rules: LogicRule = Field(default_factory=LogicRule)
    category: str = "使用范围合规审计"


class RetrievalResult(BaseModel):
    rule: RuleModel
    score: float
    match_reasons: List[str] = Field(default_factory=list)


class JudgeResult(BaseModel):
    compliant: bool = Field(..., alias="合规")
    reason: str = Field(..., alias="原因")
    basis: List[str] = Field(default_factory=list, alias="依据")
    matched_rules: List[RetrievalResult] = Field(default_factory=list, alias="命中规则")
    risk_level: str = Field(default="medium", alias="风险等级")
    summary: Dict[str, Any] = Field(default_factory=dict, alias="结构化摘要")

    model_config = {"populate_by_name": True}
