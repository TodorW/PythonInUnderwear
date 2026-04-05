"""
Database integration for PIU using SQLAlchemy async.

Requires: pip install sqlalchemy aiosqlite  (for SQLite)
          pip install sqlalchemy asyncpg     (for PostgreSQL)
          pip install sqlalchemy aiomysql    (for MySQL)

Usage::

    from piu.database import Database, Model
    from sqlalchemy import String, Integer
    from sqlalchemy.orm import Mapped, mapped_column

    db = Database("sqlite+aiosqlite:///app.db")

    class User(Model):
        __tablename__ = "users"
        id:   Mapped[int]  = mapped_column(Integer, primary_key=True)
        name: Mapped[str]  = mapped_column(String(100))

    # In app startup:
    await db.create_tables()

    # In a route:
    @app.get("/users")
    async def get_users(request):
        async with db.session() as s:
            users = await s.execute(select(User))
            return Response.json([{"id": u.id, "name": u.name} for u in users.scalars()])
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator


def _require_sqlalchemy():
    try:
        import sqlalchemy
        return sqlalchemy
    except ImportError:
        raise RuntimeError(
            "Database support requires SQLAlchemy.\n"
            "Install it with: pip install sqlalchemy aiosqlite"
        )


class Database:
    def __init__(self, url: str, echo: bool = False, pool_size: int = 5):
        sa = _require_sqlalchemy()
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

        self._url = url
        self._engine = create_async_engine(url, echo=echo, pool_size=pool_size
                                           if "sqlite" not in url else None)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator:
        async with self._session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    async def create_tables(self):
        sa = _require_sqlalchemy()
        async with self._engine.begin() as conn:
            await conn.run_sync(Model.metadata.create_all)

    async def drop_tables(self):
        sa = _require_sqlalchemy()
        async with self._engine.begin() as conn:
            await conn.run_sync(Model.metadata.drop_all)

    async def close(self):
        await self._engine.dispose()

    def __repr__(self):
        return f"<Database {self._url}>"


def _get_base():
    try:
        from sqlalchemy.orm import DeclarativeBase
        class Model(DeclarativeBase):
            pass
        return Model
    except ImportError:
        raise RuntimeError("SQLAlchemy is required. Run: pip install sqlalchemy")


try:
    Model = _get_base()
except RuntimeError:
    Model = None