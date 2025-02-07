import logging
# https://habr.com/ru/companies/wunderfund/articles/683880/

from HANDLERS import FILEHandler

PATH_LOGS_DIR = "LOGS"
FILE_LOG_NAME = "log"


LOGGER = logging.getLogger("LOGGER")
LOGGER.setLevel(logging.DEBUG)

# настройка обработчика и форматировщика для logger2
handler = logging.FileHandler(f'{PATH_LOGS_DIR}/{FILE_LOG_NAME}.log', mode='a+')
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# добавление форматировщика к обработчику
handler.setFormatter(formatter)
# добавление обработчика к логгеру
LOGGER.addHandler(handler)

LOGGER_PROGRESS = logging.getLogger("PROGRESS")
LOGGER_PROGRESS.setLevel(logging.DEBUG)

# настройка обработчика и форматировщика для logger2
handler2 = logging.FileHandler(f'{PATH_LOGS_DIR}/progress.log', mode='a+')
formatter2 = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# добавление форматировщика к обработчику
handler2.setFormatter(formatter2)
# добавление обработчика к логгеру
LOGGER_PROGRESS.addHandler(handler2)

def splitLogs():
    FILEHandler.appendToFileLog("------------", FILE_LOG_NAME)

def getLogs():
    return FILEHandler.getLogText(FILE_LOG_NAME)

def logError(text):
    LOGGER.error(text)

def logText(text):
    LOGGER.info(text)

def logDebug(func_name, signature=None):
    if signature is None or signature == "":
        LOGGER.debug(f">> {func_name}()")
    else:
        LOGGER.debug(f">> {func_name}({signature})")

def logInfo(func_name, runtime, result=None):
    if result is not None and (type(result) is type(str) or type(result) is type(dict)):
        LOGGER.info(f"<< {func_name}(): {runtime:.10f}\n {result}")
    else:
        LOGGER.info(f"<< {func_name}(): {runtime:.10f}")

def logProgress(text):
    LOGGER_PROGRESS.info(text)

def getProgressLog():
    return FILEHandler.getFileProgressText()

def cleanProgress():
    FILEHandler.cleanFileProgress()

