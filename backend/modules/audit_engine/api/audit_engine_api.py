from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.security import check_permissions
from modules.audit_engine.schemas.audit_engine_schema import AuditRequest, AuditResponse
from modules.audit_engine.services.audit_pipeline_service import run_audit_pipeline
from modules.audit_engine.services.single_project_analysis_service import analyze_single_project_file
from modules.audit_engine.services.standard_field_payload_builder import build_standard_field_payload_from_flat_fields
from modules.audit_engine.services.uploaded_file_parser import judge_uploaded_files, parse_uploaded_files


router = APIRouter(tags=["audit-engine"])


@router.post("/judge", response_model=AuditResponse)
def audit_engine_judge(req: AuditRequest, _: dict = Depends(check_permissions)):
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    if not payload.get("standard_fields") and payload.get("flat_fields"):
        payload = build_standard_field_payload_from_flat_fields(payload)
    return run_audit_pipeline(payload)


@router.post("/files/parse")
async def audit_engine_parse_files(files: List[UploadFile] = File(...)):
    return await parse_uploaded_files(files)


@router.post("/files/analyze-single")
async def audit_engine_analyze_single_file(files: List[UploadFile] = File(...)):
    return await analyze_single_project_file(files)


@router.post("/files/judge")
async def audit_engine_judge_files(
    files: List[UploadFile] = File(...),
    file_index: Optional[int] = Query(default=None),
    row_index: Optional[int] = Query(default=None),
):
    return await judge_uploaded_files(files, file_index=file_index, row_index=row_index)
