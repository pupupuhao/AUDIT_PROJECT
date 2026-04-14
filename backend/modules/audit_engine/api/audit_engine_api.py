from fastapi import APIRouter

from modules.audit_engine.schemas.audit_engine_schema import AuditRequest, AuditResponse
from modules.audit_engine.services.audit_pipeline_service import run_audit_pipeline


router = APIRouter(prefix="/engine", tags=["audit-engine"])


@router.post("/judge", response_model=AuditResponse)
def audit_engine_judge(req: AuditRequest):
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    return run_audit_pipeline(payload)
