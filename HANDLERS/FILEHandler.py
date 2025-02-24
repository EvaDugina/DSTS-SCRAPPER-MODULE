import os
from os import listdir
from pathlib import Path
from filelock import FileLock

import config
from HANDLERS.FailureHandler import Warning

import Decorators

PATH_JSONS_DIR = config.PATH_JSONS_DIR
PATH_LINKS_DIR = config.PATH_LINKS_DIR
PATH_LOGS_DIR = config.PATH_LOGS_DIR
PATH_REQUEST_FILE = config.PATH_REQUEST_FILE
OUTPUT_FILE = config.FILE_OUTPUT

LOCK_TIMEOUT = 10

def init():
    Path(f'{PATH_JSONS_DIR}/').mkdir(parents=True, exist_ok=True)
    Path(f'{PATH_LINKS_DIR}/').mkdir(parents=True, exist_ok=True)


def createLINKSDir(catalogue_name):
    Path(f'{PATH_LINKS_DIR}/{catalogue_name}/').mkdir(parents=True, exist_ok=True)
    Path(f'{PATH_LINKS_DIR}/{catalogue_name}/_completed/').mkdir(parents=True, exist_ok=True)


def createJSONSDir(catalogue_name):
    Path(f'{PATH_JSONS_DIR}/{catalogue_name}/').mkdir(parents=True, exist_ok=True)
    Path(f'{PATH_JSONS_DIR}/{catalogue_name}/_completed/').mkdir(parents=True, exist_ok=True)

@Decorators.failures_decorator
def cleanLINKSAndJSONSDir():
    import os, shutil

    arrayErrors = []
    for filename in os.listdir(PATH_JSONS_DIR):
        file_path = os.path.join(PATH_JSONS_DIR, filename)
        try:
            with FileLock(f'{file_path}.lock'):
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        except Exception as e:
            arrayErrors.append('Failed to delete %s. Reason: %s' % (file_path, e))
    for filename in os.listdir(PATH_LINKS_DIR):
        file_path = os.path.join(PATH_LINKS_DIR, filename)
        try:
            with FileLock(f'{file_path}.lock'):
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        except Exception as e:
            arrayErrors.append('Failed to delete %s. Reason: %s' % (file_path, e))

    return {"output": "" if len(arrayErrors) > 0 else Warning.CLEAN_LINKS_AND_JSONS, 'warnings': arrayErrors}


@Decorators.failures_decorator
def removeLINKFiles():
    arrayErrors = []
    for dir_name in listdir(PATH_LINKS_DIR):
        for file_name in listdir(f"{PATH_LINKS_DIR}/{dir_name}"):
            try:
                with FileLock(f'{PATH_LOGS_DIR}/{file_name}.lock'):
                    if os.access(f'{PATH_LOGS_DIR}/{file_name}', os.R_OK and os.X_OK):
                        os.remove(f'{PATH_LOGS_DIR}/{file_name}')
            except PermissionError:
                arrayErrors.append(f"ERROR! removeLINKFiles(): {file_name} while deleting links-file!")
                pass

    return {"output": "" if len(arrayErrors) > 0 else Warning.CLEAN_LINKS_AND_JSONS, 'warnings': arrayErrors}


def removeLINKFile(catalogue_name, search_request):
    # number = getCountCompleatedLINKSFiles(catalogue_name) + 1
    # os.rename(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt', f'{PATH_LINKS_DIR}/{catalogue_name}/{number}_{search_request}.txt')
    # shutil.move(f'{PATH_LINKS_DIR}/{catalogue_name}/{number}_{search_request}.txt', f'{PATH_LINKS_DIR}/{catalogue_name}/_completed')
    with FileLock(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt.lock'):
        os.remove(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt')


@Decorators.failures_decorator
def removeJSONFiles():
    arrayErrors = []
    for dir_name in listdir(PATH_JSONS_DIR):
        for file_name in listdir(f"{PATH_JSONS_DIR}/{dir_name}"):
            try:
                with FileLock(f'{PATH_LOGS_DIR}/{file_name}.lock'):
                    if os.access(f'{PATH_LOGS_DIR}/{file_name}', os.R_OK and os.X_OK):
                        os.remove(f'{PATH_LOGS_DIR}/{file_name}')
            except PermissionError:
                arrayErrors.append(f"ERROR! removeJSONFiles(): {file_name} while deleting json-file!")
                pass

    return {"output": "" if len(arrayErrors) > 0 else Warning.CLEAN_LINKS_AND_JSONS, 'warnings': arrayErrors}

def removeJSONFile(catalogue_name, search_request):
    # number = getCountCompleatedJSONSFiles(catalogue_name) + 1
    # os.rename(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt', f'{PATH_JSONS_DIR}/{catalogue_name}/{number}_{search_request}.txt')
    # shutil.move(f'{PATH_JSONS_DIR}/{catalogue_name}/{number}_{search_request}.txt', f'{PATH_JSONS_DIR}/{catalogue_name}/_completed')
    with FileLock(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt.lock'):
        os.remove(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt')


#
#
#

def appendToFileOutput(text):
    with FileLock(f'{PATH_LOGS_DIR}/{OUTPUT_FILE}.txt.lock'):
        with open(f'{PATH_LOGS_DIR}/{OUTPUT_FILE}.txt', 'a+') as f:
            f.write(text + "\n")


def cleanFileOutput():
    with FileLock(f'{PATH_LOGS_DIR}/{OUTPUT_FILE}.txt.lock'):
        open(f'{PATH_LOGS_DIR}/{OUTPUT_FILE}.txt', 'w').close()


def getOutputText():
    lines = []
    with FileLock(f'{PATH_LOGS_DIR}/{OUTPUT_FILE}.txt.lock'):
        with open(f'{PATH_LOGS_DIR}/{OUTPUT_FILE}.txt') as file:
            for line in file:
                lines.append(line.strip())
    return lines

#
#
#

@Decorators.log_decorator
def appendJSONToFile(catalogue_name, text, search_request):
    with FileLock(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt.lock'):
        with open(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt', 'a+') as f:
            f.write(text + "\n")


# @Decorators.log_decorator
def appendLINKtoFile(catalogue_name, text, search_request):
    with FileLock(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt.lock'):
        with open(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt', 'a+') as f:
            f.write(text + "\n")


def getLINKSfromFile(catalogue_name, search_request):
    links = []
    index = 0
    with FileLock(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt.lock'):
        with open(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt') as file:
            for line in file:
                links.append(line.rstrip().split(" "))
                index += 1
    return links


def getLINKSfromFileByLines(catalogue_name, search_request, start_line, end_line):
    links = []
    index = 0
    with FileLock(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt.lock'):
        with open(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt') as file:
            for line in file:
                if index >= start_line and index < end_line and line.rstrip() != "":
                    links.append(line.rstrip().split(" "))
                index += 1
    return links


def getJSONSfromFileByLines(catalogue_name, search_request, start_line, end_line):
    links = []
    index = 0
    with FileLock(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt.lock'):
        with open(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt') as file:
            for line in file:
                if index >= start_line and index < end_line:
                    links.append(line.rstrip())
                index += 1
    return links


def getCountLINKSLines(catalogue_name, file_path):
    num_lines = 0
    with FileLock(f'{PATH_LINKS_DIR}/{catalogue_name}/{file_path}.lock'):
        for line in open(f'{PATH_LINKS_DIR}/{catalogue_name}/{file_path}'):
            num_lines += 1
    return num_lines


def getCountJSONSLines(catalogue_name, file_path):
    num_lines = 0
    with FileLock(f'{PATH_JSONS_DIR}/{catalogue_name}/{file_path}.lock'):
        for line in open(f'{PATH_JSONS_DIR}/{catalogue_name}/{file_path}'):
            num_lines += 1
    return num_lines


def getCountCompleatedLINKSFiles(catalogue_name):
    path = f"{PATH_LINKS_DIR}/{catalogue_name}/_completed"
    return len(listdir(path))


def getCountCompleatedJSONSFiles(catalogue_name):
    path = f"{PATH_JSONS_DIR}/{catalogue_name}/_completed"
    return len(listdir(path))


def getCountCompleatedOUTPUTFiles():
    path = f"{PATH_LOGS_DIR}"
    return len(listdir(path)) - 1


def getSearchRequests():
    search_requests = []
    with FileLock(f'{PATH_REQUEST_FILE}.lock'):
        for line in open(f'{PATH_REQUEST_FILE}', 'r'):
            if line.rstrip() == "----" or line.rstrip() == "____":
                break
            search_requests.append(line.rstrip().split(" "))
    return search_requests


def getElementsForParse():
    elements = []
    path = "JSONS"
    for producer_name in listdir(path):
        for file_name in listdir(path + "/" + producer_name):
            if file_name == "_completed":
                continue
            search_request = file_name.split(".")[0]
            if search_request != producer_name:
                elements.append([producer_name, search_request])
    return elements


def deleteSimilarLinesFromJSON(catalogue_name, search_request):
    path = f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}'
    lines_seen = set()  # holds lines already seen

    with FileLock(f'{path}.lock'):
        for line in open(path, "r"):
            if line not in lines_seen:  # not a duplicate
                lines_seen.add(line)
        outfile = open(path, "w")
        for line in lines_seen:
            outfile.write(line)
        outfile.close()
