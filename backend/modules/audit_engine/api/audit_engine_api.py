from typing import List, Optional

from fastapi import APIRouter, File, Query, UploadFile

from modules.audit_engine.schemas.audit_engine_schema import AuditRequest, AuditResponse
from modules.audit_engine.services.audit_pipeline_service import run_audit_pipeline
from modules.audit_engine.services.uploaded_file_parser import judge_uploaded_files, parse_uploaded_files


router = APIRouter(prefix="/engine", tags=["audit-engine"])


@router.post("/judge", response_model=AuditResponse)
def audit_engine_judge(req: AuditRequest):
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    return run_audit_pipeline(payload)


@router.post("/files/parse")
async def audit_engine_parse_files(files: List[UploadFile] = File(...)):
    return await parse_uploaded_files(files)


@router.post("/files/judge")
async def audit_engine_judge_files(
    files: List[UploadFile] = File(...),
    file_index: Optional[int] = Query(default=None),
    row_index: Optional[int] = Query(default=None),
):
    return await judge_uploaded_files(files, file_index=file_index, row_index=row_index)
