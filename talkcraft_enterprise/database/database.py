from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from talkcraft_enterprise.utils.config import config
from talkcraft_enterprise.utils.logger import get_logger
from talkcraft_enterprise.database.models import Base

logger = get_logger("database")

engine = create_engine(
    config.database.url,
    echo=config.database.echo,
    pool_size=config.database.pool_size,
    max_overflow=config.database.max_overflow,
    connect_args={"check_same_thread": False} if "sqlite" in config.database.url else {},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in config.database.url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_sync():
    return SessionLocal()
