from tortoise import Tortoise

from app.core.config import POSTGRES_DB, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER


def _build_tortoise_db_url() -> str:
    return (
        f"postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )


async def init_orm():
    """初始化orm"""
    await Tortoise.init(
        db_url=_build_tortoise_db_url(),
        modules={"models": ["modules.system.models", "modules.audit.models"]},
    )
    await Tortoise.generate_schemas()


async def close_orm():
    """关闭orm"""
    await Tortoise.close_connections()
