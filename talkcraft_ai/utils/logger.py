import logging
import sys
from pathlib import Path


_loggers = {}


def setup_logger(name: str = "talkcraft-ai", level: int = logging.INFO) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    try:
        log_dir = Path(__file__).resolve().parent.parent
        file_handler = logging.FileHandler(log_dir / "talkcraft-ai.log", mode="a")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass
    _loggers[name] = logger
    return logger


def get_logger(name: str = "talkcraft-ai") -> logging.Logger:
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)
