from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = None
async_session = None


class Base(DeclarativeBase):
    pass


def init_engine():
    global engine, async_session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    if async_session is None:
        init_engine()
    async with async_session() as session:
        yield session
