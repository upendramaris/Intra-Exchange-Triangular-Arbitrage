from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from triarb.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(settings.db_url, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
