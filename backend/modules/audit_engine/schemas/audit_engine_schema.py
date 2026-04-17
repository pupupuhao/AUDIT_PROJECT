from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditRequest(BaseModel):
    project_name: Optional[str] = Field(default=None, description="工程名称；优先使用 sources 中的主表字段")
    sources: Dict[str, Any] = Field(
        default_factory=dict,
        description="统一输入来源，按表或来源分组，如 t_workspace/ws_project/blueprint_draft/hou_notion_sum/project_contract/ocr/text",
    )


class BasisDocument(BaseModel):
    display_name: Optional[str] = None
    source_type: Optional[str] = None
    title: Optional[str] = None
    issuer: Optional[str] = None
    document_no: Optional[str] = None
    article: Optional[str] = None
    section: Optional[str] = None


class FieldMappingRecord(BaseModel):
    standard_field: str
    value: Any = None
    source: str
    source_field: Optional[str] = None
    mapping_rule: str
    field_comment: str


class FieldMappingLayerResult(BaseModel):
    standard_fields: Dict[str, Any] = Field(default_factory=dict)
    field_mappings: List[FieldMappingRecord] = Field(default_factory=list)
    unmapped_sources: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class MappedObject(BaseModel):
    id: int
    full_path: str
    match_score: float
    match_method: str


class AuditSubResult(BaseModel):
    applicable: bool
    result: Optional[str] = None
    display_result: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    missing_items: List[str] = Field(default_factory=list)
    basis_documents: List[BasisDocument] = Field(default_factory=list)
    audit_path: List[str] = Field(default_factory=list)
    used_standard_fields: List[str] = Field(default_factory=list)


class AuditSubAudits(BaseModel):
    entity_audit: AuditSubResult
    trace_audit: AuditSubResult
    process_audit: AuditSubResult
    amount_info: AuditSubResult


class SummaryConclusion(BaseModel):
    type: str
    entity_pass: bool = False
    conflict_detected: bool = False
    gap_categories: List[str] = Field(default_factory=list)
    primary_message: str = ""
    display_summary: str = ""


class AuditResponse(BaseModel):
    project_name: str
    mapped_objects: List[MappedObject] = Field(default_factory=list)
    matched_object_ids: List[int] = Field(default_factory=list)
    normalized_tags: List[str] = Field(default_factory=list)
    overall_result: str
    display_result: str
    reason_codes: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    basis_documents: List[BasisDocument] = Field(default_factory=list)
    missing_items: List[str] = Field(default_factory=list)
    audit_path: List[str] = Field(default_factory=list)
    manual_review_required: bool
    sub_audits: AuditSubAudits
    field_mapping_layer: FieldMappingLayerResult
    summary_conclusion: SummaryConclusion
    display_summary: str
