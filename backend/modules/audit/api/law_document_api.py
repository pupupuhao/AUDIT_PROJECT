from fastapi import APIRouter, Depends, HTTPException

from app.core.security import check_permissions
from modules.audit.schemas import law_document as LawDocumentSchema
from modules.audit.services.law_document import service as LawDocumentService
from modules.system.schemas import common as BaseSchema


router = APIRouter(prefix="/laws", tags=["法规文档"])
Response = BaseSchema.Response
ListAll = BaseSchema.ListAll
law_document_list_schema = ListAll[list[LawDocumentSchema.LawDocumentRead]]


@router.get("")
async def list_law_documents(
    limit: int = 20,
    offset: int = 1,
    keyword: str = "",
    _: dict = Depends(check_permissions),
) -> Response[law_document_list_schema]:
    return dict(
        data=await LawDocumentService.list_documents(
            offset=offset,
            limit=limit,
            keyword=keyword,
        )
    )


@router.get("/{law_name}")
async def get_law_document(
    law_name: str,
    _: dict = Depends(check_permissions),
) -> Response[LawDocumentSchema.LawDocumentRead]:
    document = await LawDocumentService.get_document(law_name)
    if document is None:
        raise HTTPException(status_code=404, detail="law document not found")
    return dict(data=document)
