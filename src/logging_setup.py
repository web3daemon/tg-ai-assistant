import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.app_meta import APP_NAME, APP_VERSION
from src.config import settings


def configure_logging() -> None:
    log_path = settings.log_file_path
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | pid=%(process)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.info(
        "Logging configured | app=%s version=%s level=%s cwd=%s",
        APP_NAME,
        APP_VERSION,
        settings.log_level.upper(),
        os.getcwd(),
    )
