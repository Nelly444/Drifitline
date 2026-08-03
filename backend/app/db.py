from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


_LIBPQ_ONLY_QUERY_KEYS = {"sslmode", "channel_binding"}


def _async_engine_url_and_connect_args(database_url: str) -> tuple[str, dict]:
    parts = urlsplit(database_url)
    query_pairs = parse_qsl(parts.query)
    wants_ssl = any(key == "sslmode" for key, _ in query_pairs)
    remaining_pairs = [(key, value) for key, value in query_pairs if key not in _LIBPQ_ONLY_QUERY_KEYS]
    clean_url = urlunsplit(parts._replace(query=urlencode(remaining_pairs)))
    connect_args = {"ssl": "require"} if wants_ssl else {}
    return clean_url, connect_args


_engine_url, _connect_args = _async_engine_url_and_connect_args(settings.DATABASE_URL)
engine = create_async_engine(_engine_url, connect_args=_connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session
