# ============================
# logger_setup.py
# ============================
import logging
from colorlog import ColoredFormatter
from config.config import LOG_PATH


def setup_logger(name="scraper", log_file=None, level=logging.INFO):
    """logのコンソール及び、ファイル出力"""

    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s] [%(levelname)s]%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # avoid duplicate logs

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
        )
        logger.addHandler(file_handler)

    return logger


if __name__ == "__main__":

    logger = setup_logger("logger_setup", log_file=LOG_PATH)
    logger.info("log_test")
