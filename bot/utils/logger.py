import sys
from loguru import logger
from bot.config import settings
from datetime import date

logger.remove()

logger.add(sink=sys.stdout, format="<white>{time:YYYY-MM-DD HH:mm:ss}</white>"
                                   " | <level>{level}</level>"
                                   " | <white><b>{message}</b></white>",
           filter=lambda record: record["level"].name != "TRACE")

if settings.DEBUG_LOGGING:
    logger.add(f"logs/err_tracebacks_{date.today()}.txt",
               format="{time:DD.MM.YYYY HH:mm:ss} - {level} - {message}",
               level="TRACE",
               backtrace=True,
               diagnose=True,
               filter=lambda record: record["level"].name == "TRACE")

logger = logger.opt(colors=True)


def log_error(text):
    if settings.DEBUG_LOGGING:
        logger.opt(exception=True, colors=True).trace(text)
    return logger.error(text)
