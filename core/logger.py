import logging
from colorlog import ColoredFormatter


def setup_logger(level: str = "INFO") -> logging.Logger:
    formatter = ColoredFormatter(
        "%(white)s%(asctime)s%(reset)s "
        "%(log_color)s%(levelname)-7s%(reset)s "
        "%(message_log_color)s%(message)s%(reset)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red",
        },
        secondary_log_colors={
            "message": {
                "DEBUG": "white",
                "INFO": "white",
                "WARNING": "white",
                "ERROR": "red",
                "CRITICAL": "red",
            }
        },
        style="%",
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    logging.getLogger("aiogram.event").setLevel(logging.WARNING)

    return logging.getLogger("bfit_bot")