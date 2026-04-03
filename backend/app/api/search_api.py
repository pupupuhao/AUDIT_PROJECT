from fastapi import APIRouter

from app.models.request_model import SearchRequest
from app.services.retrieval_service import search_rules


router = APIRouter(prefix="/search", tags=["search"])


@router.post("")
def search(request: SearchRequest):
    results = search_rules(request.query, top_k=request.top_k)
    return {
        "query": request.query,
        "count": len(results),
        "items": [item.model_dump(by_alias=True) for item in results],
    }
