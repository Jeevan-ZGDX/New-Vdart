import logging
import sys
from pathlib import Path


_loggers: dict = {}


def get_logger(name: str) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]
    logger = logging.getLogger(f"talkcraft_coach.{name}")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fmt = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(fmt)
        logger.addHandler(sh)
        log_dir = Path(__file__).resolve().parent.parent
        fh = logging.FileHandler(log_dir / "talkcraft-coach.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    _loggers[name] = logger
    return logger
