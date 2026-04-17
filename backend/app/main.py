from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.events import close_orm, init_orm
from app.core.exceptions import exception_handlers
from app.core.middleware import middlewares

from modules.compliance_center.api.law_document_api import router as law_document_router
from modules.compliance_center.api.law_clause_api import router as law_clause_router
from modules.compliance_center.api.rule_api import router as rule_router
from modules.audit_engine.api.audit_engine_api import router as audit_engine_router
from modules.system.api.auth_api import router as auth_router
from modules.system.api.menu_api import router as menu_router
from modules.system.api.role_api import router as role_router
from modules.system.api.user_api import router as user_router



@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_orm()
    try:
        yield
    finally:
        await close_orm()


app = FastAPI(
    title="Audit RAG System",
    description="维修资金合规判定服务",
    version="0.1.0",
    middleware=middlewares,
    exception_handlers=exception_handlers,
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/system")
app.include_router(user_router, prefix="/api/system")
app.include_router(role_router, prefix="/api/system")
app.include_router(menu_router, prefix="/api/system")

app.include_router(law_document_router, prefix="/api/compliance")
app.include_router(law_clause_router, prefix="/api/compliance")
app.include_router(rule_router, prefix="/api/compliance")

app.include_router(audit_engine_router, prefix="/api/audit-engine")


@app.get("/")
def healthcheck():
    return {
        "service": "audit-rag-system",
        "status": "ok",
        "routes": [
            "/api/system/login",
            "/api/system/user",
            "/api/system/role",
            "/api/system/menu",
            "/api/compliance/laws",
            "/api/compliance/law-clauses",
            "/api/compliance/rules",
            "/api/compliance/rules/search",
            "/api/audit-engine/judge",
        ],
    }
