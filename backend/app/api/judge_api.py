from fastapi import APIRouter

from app.models.request_model import AuditRequest
from app.services.judge_service import judge_application


router = APIRouter(prefix="/judge", tags=["judge"])


@router.post("")
def judge(request: AuditRequest):
    result = judge_application(request)
    return result.model_dump(by_alias=True)
