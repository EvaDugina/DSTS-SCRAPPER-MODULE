import logging
# https://habr.com/ru/companies/wunderfund/articles/683880/
import datetime

# НЕ МОЖЕТ БЫТЬ ДЕКОРАТОРОВ, ТК ДЕКОРАТОРЫ ИСПОЛЬЗУЮТ ЕГО!!
from HANDLERS import FILEHandler

PATH_LOGS_DIR = "LOGS"
DEFAULT_FILE_LOG = "default"
FILE_PROGRESS = "progress"


def generateFileLogName():
    now = datetime.datetime.now()
    return "log_" + now.strftime('%Y%m%d-%H%M%S')


def getCurrentLogFile():
    global DEFAULT_FILE_LOG
    file_name = FILEHandler.getLastLogFileName()
    if file_name is None:
        return DEFAULT_FILE_LOG
    else:
        return file_name.split(".")[0]


FILE_LOG = getCurrentLogFile()

LOGGER = logging.getLogger("LOGGER")
LOGGER.setLevel(logging.DEBUG)
LOGGER_PROGRESS = logging.getLogger("PROGRESS")
LOGGER_PROGRESS.setLevel(logging.DEBUG)


def initLogger(file_log):
    global LOGGER

    # https://stackoverflow.com/questions/7484454/removing-handlers-from-pythons-logging-loggers
    LOGGER.handlers.clear()
    while LOGGER.hasHandlers():
        LOGGER.removeHandler(LOGGER.handlers[0])

    FILEHandler.createFileLog(file_log)

    # настройка обработчика и форматировщика для logger2
    handler = logging.FileHandler(f'{PATH_LOGS_DIR}/{file_log}.log', mode='a+')
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    # добавление форматировщика к обработчику
    handler.setFormatter(formatter)
    # добавление обработчика к логгеру
    LOGGER.addHandler(handler)


def initLoggerProgress(file_progress):
    global LOGGER_PROGRESS

    FILEHandler.createFileLog(file_progress)

    # настройка обработчика и форматировщика для logger2
    handler2 = logging.FileHandler(f'{PATH_LOGS_DIR}/{file_progress}.log', mode='a+')
    formatter2 = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    # добавление форматировщика к обработчику
    handler2.setFormatter(formatter2)
    # добавление обработчика к логгеру
    LOGGER_PROGRESS.addHandler(handler2)


initLogger(FILE_LOG)
initLoggerProgress(FILE_PROGRESS)


def splitLogs():
    global FILE_LOG
    FILE_LOG = generateFileLogName()
    initLogger(FILE_LOG)
    FILEHandler.removeFileLogsAcrossLast15()
    FILEHandler.removeLINKFiles()
    FILEHandler.removeJSONFiles()


def getLogs():
    global FILE_LOG
    return FILEHandler.getFileLogText(FILE_LOG)


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


def cleanLogs():
    FILEHandler.removeFileLogAcrossCurrent(FILE_LOG)


def logProgress(text):
    LOGGER_PROGRESS.info(text)


def getProgress():
    global FILE_PROGRESS
    return FILEHandler.getFileLogText(FILE_PROGRESS)


def cleanProgress():
    global FILE_PROGRESS, DEFAULT_FILE_LOG
    FILEHandler.cleanFileLog(FILE_PROGRESS)
    FILEHandler.cleanFileLog(DEFAULT_FILE_LOG)
