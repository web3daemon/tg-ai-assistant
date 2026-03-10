from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect, select, text
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.db.models import Base, SchemaMeta


Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{settings.sqlite_path.as_posix()}",
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

CURRENT_SCHEMA_VERSION = 2


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)

def run_migrations(db_engine: Engine) -> None:
    inspector = inspect(db_engine)
    if "messages" not in inspector.get_table_names():
        return

    Base.metadata.create_all(bind=db_engine, tables=[SchemaMeta.__table__])
    current_version = _get_schema_version(db_engine)

    migrations: list[tuple[int, callable[[Engine], None]]] = [
        (1, _migration_add_usage_columns),
        (2, _migration_backfill_schema_meta),
    ]
    for version, migration in migrations:
        if current_version >= version:
            continue
        migration(db_engine)
        _set_schema_version(db_engine, version)
        current_version = version


def _migration_add_usage_columns(db_engine: Engine) -> None:
    inspector = inspect(db_engine)
    existing_columns = {column["name"] for column in inspector.get_columns("messages")}
    required_columns = {
        "prompt_tokens": "INTEGER",
        "completion_tokens": "INTEGER",
        "total_tokens": "INTEGER",
        "cost": "FLOAT",
    }

    with db_engine.begin() as connection:
        for column_name, column_type in required_columns.items():
            if column_name in existing_columns:
                continue
            connection.execute(text(f"ALTER TABLE messages ADD COLUMN {column_name} {column_type}"))


def _migration_backfill_schema_meta(db_engine: Engine) -> None:
    _set_schema_version(db_engine, CURRENT_SCHEMA_VERSION)


def _get_schema_version(db_engine: Engine) -> int:
    with sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)() as session:
        record = session.get(SchemaMeta, "schema_version")
        if record is None:
            return 0
        return int(record.value)


def _set_schema_version(db_engine: Engine, version: int) -> None:
    Session = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)
    with Session() as session:
        record = session.get(SchemaMeta, "schema_version")
        if record is None:
            record = SchemaMeta(key="schema_version", value=str(version))
            session.add(record)
        else:
            record.value = str(version)
        session.commit()
