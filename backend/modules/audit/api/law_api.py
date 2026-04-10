from fastapi import APIRouter

from modules.audit.services.rule_service import load_law_documents, refresh_law_documents


router = APIRouter(prefix="/laws", tags=["laws"])


@router.get("")
def list_laws(limit: int = 20, offset: int = 1, keyword: str = ""):
    docs = load_law_documents()
    if keyword:
        docs = [doc for doc in docs if keyword.lower() in doc["title"].lower()]

    start = max(offset - 1, 0) * limit
    end = start + limit
    return {
        "total": len(docs),
        "items": docs[start:end],
    }


@router.get("/refresh")
def reload_laws():
    docs = refresh_law_documents()
    return {"total": len(docs), "message": "法规文件缓存已刷新"}
