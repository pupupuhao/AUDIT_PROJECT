from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogicRule(BaseModel):
    rule_nature: str = ""
    audit_stage: str = ""
    audit_dimension: str = ""
    apply_scope: Dict[str, List[str]] = Field(default_factory=dict)
    judgement_mode: str = ""
    required_fields: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    field_expectations: List[Dict[str, Any]] = Field(default_factory=list)
    risk_points: List[str] = Field(default_factory=list)
    output_hint: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class RuleModel(BaseModel):
    id: str
    doc_id: str = ""
    parent_id: Optional[str] = None
    law_name: str = ""
    node_level: Optional[int] = None
    node_type: str = ""
    clause_label: str = ""
    item_label: str = ""
    subitem_label: str = ""
    full_title: str = ""
    title_text: str = ""
    content: str = ""
    clean_text: str = ""
    embedding_text: str = ""
    parent_context: str = ""
    path: List[str] = Field(default_factory=list)
    sub_clause: str = ""
    index: Optional[int] = None
    logic_rules: LogicRule = Field(default_factory=LogicRule)
    category: str = "使用范围合规审计"


class RuleWrite(LogicRule):
    pass


class RuleUpsert(BaseModel):
    id: str
    doc_id: str = ""
    parent_id: Optional[str] = None
    law_name: str = ""
    node_level: Optional[int] = None
    node_type: str = ""
    clause_label: str = ""
    item_label: str = ""
    subitem_label: str = ""
    full_title: str = ""
    title_text: str = ""
    content: str = ""
    clean_text: str = ""
    embedding_text: str = ""
    parent_context: str = ""
    path: List[str] = Field(default_factory=list)
    sub_clause: str = ""
    index: Optional[int] = None
    category: str = "使用范围合规审计"
    logic_rules: LogicRule = Field(default_factory=LogicRule)


class SearchRequest(BaseModel):
    query: str = Field(..., description="检索文本")
    top_k: int = Field(default=5, ge=1, le=20)


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
