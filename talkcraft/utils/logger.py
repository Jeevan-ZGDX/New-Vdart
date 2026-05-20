import sys
import logging
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "talkcraft",
    level: str = "INFO",
    log_file: Optional[str] = "talkcraft.log",
    fmt: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")

    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if log_file:
            file_handler = logging.FileHandler(Path(log_file))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "talkcraft") -> logging.Logger:
    return logging.getLogger(name)
