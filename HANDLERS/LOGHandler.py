import logging
# https://habr.com/ru/companies/wunderfund/articles/683880/
import datetime

import config


def generateFileLogName():
    now = datetime.datetime.now()
    return "log_" + now.strftime('%Y%m%d-%H%M%S')


def init():
    initLogFiles()
    file_name = getLastLogFileName()
    if file_name is not None:
        config.CURRENT_LOG_FILE = file_name.split(".")[0]

#
#
#

def setLogger(file_log_name):
    # https://stackoverflow.com/questions/7484454/removing-handlers-from-pythons-logging-loggers
    LOGGER.handlers.clear()
    while LOGGER.hasHandlers():
        LOGGER.removeHandler(LOGGER.handlers[0])

    # настройка обработчика и форматировщика для logger2
    handler = logging.FileHandler(f'{config.PATH_LOGS_DIR}/{file_log_name}.log', mode='a+')
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    # добавление форматировщика к обработчику
    handler.setFormatter(formatter)
    # добавление обработчика к логгеру
    LOGGER.addHandler(handler)


def setLoggerProgress(file_progress_name):
    # https://stackoverflow.com/questions/7484454/removing-handlers-from-pythons-logging-loggers
    LOGGER_PROGRESS.handlers.clear()
    while LOGGER_PROGRESS.hasHandlers():
        LOGGER_PROGRESS.removeHandler(LOGGER_PROGRESS.handlers[0])

    # настройка обработчика и форматировщика для logger2
    handler2 = logging.FileHandler(f'{config.PATH_LOGS_DIR}/{file_progress_name}.log', mode='a+')
    formatter2 = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    # добавление форматировщика к обработчику
    handler2.setFormatter(formatter2)
    # добавление обработчика к логгеру
    LOGGER_PROGRESS.addHandler(handler2)


def setHandlers():
    setLogger(config.CURRENT_LOG_FILE)
    setLoggerProgress(config.FILE_PROGRESS)


def createNewLogger():
    new_file_log = generateFileLogName()
    createFileLog(new_file_log)
    config.CURRENT_LOG_FILE = new_file_log
    setLogger(new_file_log)

#
#
#

def getLogs():
    return getFileLogText(config.CURRENT_LOG_FILE)


def logError(text):
    LOGGER.error(text)


def logWarning(text):
    LOGGER.warning(text)


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
    removeFileLogAcrossCurrent(config.CURRENT_LOG_FILE)


def removeLogsAcrossLast15():
    removeFileLogsAcrossLast15()


def logProgress(text):
    LOGGER_PROGRESS.info(text)


def getProgress():
    return getFileLogText(config.FILE_PROGRESS)


def cleanProgress():
    cleanFileLog(config.FILE_PROGRESS)
    cleanFileLog(config.DEFAULT_FILE_LOG)

#
#
#

import os
from os import listdir
from pathlib import Path

PATH_JSONS_DIR = config.PATH_JSONS_DIR
PATH_LINKS_DIR = config.PATH_LINKS_DIR
PATH_LOGS_DIR = config.PATH_LOGS_DIR
PATH_REQUEST_FILE = config.PATH_REQUEST_FILE

def initLogFiles():
    Path(f'{config.PATH_LOGS_DIR}/').mkdir(parents=True, exist_ok=True)
    open(f'{config.PATH_LOGS_DIR}/{config.DEFAULT_FILE_LOG}.log', 'w').close()
    open(f'{config.PATH_LOGS_DIR}/{config.FILE_PROGRESS}.log', 'w').close()
    open(f'{config.PATH_LOGS_DIR}/{config.FILE_OUTPUT}.txt', 'w').close()

def createFileLog(file_log):
    with open(f'{PATH_LOGS_DIR}/{file_log}.log', 'a+') as f:
        pass

def appendToFileLog(file_log, text):
    with open(f'{PATH_LOGS_DIR}/{file_log}.log', 'a+') as f:
        f.write(text + "\n")

def getLastLogFileName():
    log_files = []
    for file_name in listdir(PATH_LOGS_DIR):
        if "log_" in file_name:
            log_files.append(file_name)
    if len(log_files) < 1:
        return None
    else:
        return log_files[len(log_files) - 1]

def cleanFileLog(file_log):
    open(f'{PATH_LOGS_DIR}/{file_log}.log', 'w').close()

def getFileLogText(file_log):
    lines = []
    with open(f'{PATH_LOGS_DIR}/{file_log}.log') as file:
        for line in file:
            lines.append(line)
    return lines


def removeFileLogsAcrossLast15():
    max_count = 45
    count_log_files = 0
    for file_name in listdir(PATH_LOGS_DIR):
        if "log_" in file_name:
            count_log_files += 1
    if count_log_files < max_count:
        return
    count_log_files -= 15

    arrayErrors = []
    for file_name in listdir(PATH_LOGS_DIR):
        if count_log_files <= 0:
            return
        try:
            if os.access(f'{PATH_LOGS_DIR}/{file_name}', os.R_OK and os.X_OK):
                os.remove(f'{PATH_LOGS_DIR}/{file_name}')
                count_log_files -= 1
        except PermissionError:
            arrayErrors.append(f"ERROR! removeFileLogsAcrossLast15(): {file_name} while deleting log-file!")
            pass

    # return {"output": "" if len(arrayErrors) > 0 else Warning.CLEAN_LINKS_AND_JSONS, 'warnings': arrayErrors}



def removeFileLogAcrossCurrent(current_file_log_name):
    arrayErrors = []
    for file_name in listdir(PATH_LOGS_DIR):
        if "log_" in file_name and not (current_file_log_name in file_name):
            try:
                if os.access(f'{PATH_LOGS_DIR}/{file_name}', os.R_OK and os.X_OK):
                    os.remove(f'{PATH_LOGS_DIR}/{file_name}')
            except PermissionError:
                arrayErrors.append(f"ERROR! removeFileLogAcrossCurrent(): {file_name} while deleting log-file!")
                pass
    # return {"output": "" if len(arrayErrors) > 0 else Warning.CLEAN_LINKS_AND_JSONS, 'warnings': arrayErrors}

#
#
#

init()

LOGGER = logging.getLogger("LOGGER")
LOGGER.setLevel(logging.DEBUG)
LOGGER_PROGRESS = logging.getLogger("PROGRESS")
LOGGER_PROGRESS.setLevel(logging.DEBUG)

setHandlers()