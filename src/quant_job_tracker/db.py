from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from quant_job_tracker.models import Base


def engine_for(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)


def init_db(db_path: Path) -> None:
    engine = engine_for(db_path)
    Base.metadata.create_all(engine)


@contextmanager
def create_session(db_path: Path) -> Iterator[Session]:
    engine = engine_for(db_path)
    with Session(engine) as session:
        yield session
