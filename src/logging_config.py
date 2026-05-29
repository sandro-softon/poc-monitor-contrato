import logging
import sys
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from src.config import Config


def _cleanup_old_logs(log_dir: Path, retention_days: int) -> None:
    cutoff = time.time() - (retention_days * 24 * 60 * 60)

    for log_file in log_dir.glob("monitor.log*"):
        if log_file.name == "monitor.log" or not log_file.is_file():
            continue

        try:
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
        except OSError:
            continue


def setup_logging(debug: bool = False) -> None:
    log_dir = Path(Config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    _cleanup_old_logs(log_dir, Config.LOG_RETENTION_DAYS)

    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = TimedRotatingFileHandler(
        log_dir / "monitor.log",
        when="midnight",
        interval=1,
        backupCount=Config.LOG_RETENTION_DAYS,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
