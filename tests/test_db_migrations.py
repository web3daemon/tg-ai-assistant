import unittest
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from src.db.session import CURRENT_SCHEMA_VERSION, run_migrations


class DatabaseMigrationTests(unittest.TestCase):
    def test_run_migrations_upgrades_legacy_messages_table(self) -> None:
        temp_dir = Path("tests/.tmp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        db_path = temp_dir / "legacy.db"
        if db_path.exists():
            db_path.unlink()

        engine = create_engine(f"sqlite:///{db_path.resolve().as_posix()}", future=True)
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        CREATE TABLE messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            chat_id INTEGER,
                            user_id INTEGER,
                            role VARCHAR(32),
                            content TEXT,
                            created_at DATETIME
                        )
                        """
                    )
                )

            run_migrations(engine)

            inspector = inspect(engine)
            columns = {column["name"] for column in inspector.get_columns("messages")}
            self.assertTrue({"prompt_tokens", "completion_tokens", "total_tokens", "cost"}.issubset(columns))

            with engine.begin() as connection:
                version = connection.execute(
                    text("SELECT value FROM schema_meta WHERE key = 'schema_version'")
                ).scalar_one()
            self.assertEqual(int(version), CURRENT_SCHEMA_VERSION)
        finally:
            engine.dispose()
            if db_path.exists():
                db_path.unlink()


if __name__ == "__main__":
    unittest.main()
