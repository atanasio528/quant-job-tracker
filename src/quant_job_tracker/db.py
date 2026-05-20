from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from quant_job_tracker.models import Base


def engine_for(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)

    if engine.url.get_backend_name() == "sqlite":

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def init_db(db_path: Path) -> None:
    engine = engine_for(db_path)
    Base.metadata.create_all(engine)


@contextmanager
def create_session(db_path: Path) -> Iterator[Session]:
    engine = engine_for(db_path)
    with Session(engine) as session:
        yield session
