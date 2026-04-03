from fastapi import FastAPI

from app.api.judge_api import router as judge_router
from app.api.rule_api import router as rule_router
from app.api.search_api import router as search_router


app = FastAPI(
    title="Audit RAG System",
    description="维修资金合规判定服务",
    version="0.1.0",
)

app.include_router(rule_router)
app.include_router(search_router)
app.include_router(judge_router)


@app.get("/")
def healthcheck():
    return {
        "service": "audit-rag-system",
        "status": "ok",
        "routes": ["/rules", "/search", "/judge"],
    }
