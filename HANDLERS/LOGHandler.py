
# https://github.com/Delgan/loguru?tab=readme-ov-file#modern-string-formatting-using-braces-style
from loguru import logger


def debug_only(record):
    return record["level"].name == "DEBUG"

def info_only(record):
    return record["level"].name == "INFO"

def success_only(record):
    return record["level"].name == "SUCCESS"

def error_only(record):
    return record["level"].name == "ERROR"


def init():
    # logger.add("LOGS/log.log", format="{time:YYYY-MM-DD HH:mm:ss:SS} | {level} | {file}:{line} | {message}",
    #            rotation="1 week", filter=debug_only)
    logger.add("LOGS/log.log", format="{time:YYYY-MM-DD HH:mm:ss:SS} | {level}\t| {message}",
               rotation="2 days", filter=debug_only)
    logger.add("LOGS/log.log", format="{time:YYYY-MM-DD HH:mm:ss:SS} | {level}\t| {message}",
               rotation="2 days", filter=info_only)
    logger.add("LOGS/log.log", format="{level} | {message}",
               rotation="2 days", filter=error_only)
    logger.add("LOGS/log.log", format="{level} | {message}",
               rotation="2 days", filter=success_only)

