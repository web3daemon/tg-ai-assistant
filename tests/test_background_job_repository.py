import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base
from src.db.repository import BackgroundJobRepository
from src.db.session import SessionLocal


class BackgroundJobRepositoryTests(unittest.TestCase):
    def test_job_artifacts_round_trip(self) -> None:
        temp_dir = Path("tests/.tmp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        db_path = temp_dir / "job_artifacts.db"
        if db_path.exists():
            db_path.unlink()

        engine = create_engine(f"sqlite:///{db_path.resolve().as_posix()}", future=True)
        original_bind = SessionLocal.kw["bind"]
        SessionLocal.configure(bind=engine)
        try:
            Base.metadata.create_all(bind=engine)
            repository = BackgroundJobRepository()
            job_id = repository.create_job(chat_id=1, user_id=2, job_type="document", payload={"mime_type": "text/plain"})
            repository.add_job_artifact(
                job_id=job_id,
                telegram_file_id="file-1",
                telegram_file_unique_id="unique-1",
                file_name="notes.txt",
                mime_type="text/plain",
                file_size=123,
                source_kind="document",
                caption_text="analyze",
            )

            artifacts = repository.get_job_artifacts(job_id)

            self.assertEqual(len(artifacts), 1)
            self.assertEqual(artifacts[0].telegram_file_id, "file-1")
            self.assertEqual(artifacts[0].file_name, "notes.txt")
            self.assertEqual(artifacts[0].caption_text, "analyze")
        finally:
            SessionLocal.configure(bind=original_bind)
            engine.dispose()
            if db_path.exists():
                db_path.unlink()


if __name__ == "__main__":
    unittest.main()
