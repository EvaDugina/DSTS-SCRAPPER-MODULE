import datetime
import os
import shutil
from os import listdir
from pathlib import Path

from HANDLERS import LOGHandler

PATH_LOGS_DIR = "LOGS"
PATH_JSONS_DIR = "JSONS"
PATH_LINKS_DIR = "LINKS"

PATH_REQUEST_FILE = "SEARCH_REQUESTS.txt"

def createDirectories():
    Path(f'{PATH_LOGS_DIR}').mkdir(parents=True, exist_ok=True)
    Path(f'{PATH_LINKS_DIR}/').mkdir(parents=True, exist_ok=True)
    Path(f'{PATH_JSONS_DIR}/').mkdir(parents=True, exist_ok=True)

def createLINKSDir(catalogue_name):
    Path(f'{PATH_LINKS_DIR}/{catalogue_name}/').mkdir(parents=True, exist_ok=True)
    Path(f'{PATH_LINKS_DIR}/{catalogue_name}/_completed/').mkdir(parents=True, exist_ok=True)

def createJSONSDir(catalogue_name):
    Path(f'{PATH_JSONS_DIR}/{catalogue_name}/').mkdir(parents=True, exist_ok=True)
    Path(f'{PATH_JSONS_DIR}/{catalogue_name}/_completed/').mkdir(parents=True, exist_ok=True)


def cleanLINKSAndJSONSDir():
    import os, shutil
    for filename in os.listdir(PATH_JSONS_DIR):
        file_path = os.path.join(PATH_JSONS_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            LOGHandler.logText('Failed to delete %s. Reason: %s' % (file_path, e))
    for filename in os.listdir(PATH_LINKS_DIR):
        file_path = os.path.join(PATH_LINKS_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            LOGHandler.logText('Failed to delete %s. Reason: %s' % (file_path, e))

def removeLINKFiles():
    for dir_name in listdir(PATH_LINKS_DIR):
        for file_name in listdir(f"{PATH_LINKS_DIR}/{dir_name}"):
            try:
                if os.access(f'{PATH_LOGS_DIR}/{file_name}', os.R_OK and os.X_OK):
                    os.remove(f'{PATH_LOGS_DIR}/{file_name}')
            except PermissionError:
                LOGHandler.logText(f"ERROR! removeLINKFiles(): {file_name} while deleting links-file!")
                pass

def removeLINKFile(catalogue_name, search_request):
    # number = getCountCompleatedLINKSFiles(catalogue_name) + 1
    # os.rename(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt', f'{PATH_LINKS_DIR}/{catalogue_name}/{number}_{search_request}.txt')
    # shutil.move(f'{PATH_LINKS_DIR}/{catalogue_name}/{number}_{search_request}.txt', f'{PATH_LINKS_DIR}/{catalogue_name}/_completed')
    os.remove(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt')

def removeJSONFiles():
    for dir_name in listdir(PATH_JSONS_DIR):
        for file_name in listdir(f"{PATH_JSONS_DIR}/{dir_name}"):
            try:
                if os.access(f'{PATH_LOGS_DIR}/{file_name}', os.R_OK and os.X_OK):
                    os.remove(f'{PATH_LOGS_DIR}/{file_name}')
            except PermissionError:
                LOGHandler.logText(f"ERROR! removeJSONFiles(): {file_name} while deleting json-file!")
                pass

def removeJSONFile(catalogue_name, search_request):
    # number = getCountCompleatedJSONSFiles(catalogue_name) + 1
    # os.rename(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt', f'{PATH_JSONS_DIR}/{catalogue_name}/{number}_{search_request}.txt')
    # shutil.move(f'{PATH_JSONS_DIR}/{catalogue_name}/{number}_{search_request}.txt', f'{PATH_JSONS_DIR}/{catalogue_name}/_completed')
    os.remove(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt')

#
#
#

def appendToFileOutput(text):
    with open(f'{PATH_LOGS_DIR}/output.txt', 'a+') as f:
        f.write(text + "\n")

def cleanFileOutput():
    open(f'{PATH_LOGS_DIR}/output.txt', 'w').close()

def getOutputText():
    lines = []
    with open(f'{PATH_LOGS_DIR}/output.txt') as file:
        for line in file:
            lines.append(line.strip())
    return lines

#
#
#

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
        return log_files[len(log_files)-1]

def cleanFileLog(file_log):
    open(f'{PATH_LOGS_DIR}/{file_log}.log', 'w').close()

def getFileLogText(file_log):
    lines = []
    with open(f'{PATH_LOGS_DIR}/{file_log}.log') as file:
        for line in file:
            lines.append(line.strip())
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
    for file_name in listdir(PATH_LOGS_DIR):
        if count_log_files <= 0:
            return
        try:
            if os.access(f'{PATH_LOGS_DIR}/{file_name}', os.R_OK and os.X_OK):
                os.remove(f'{PATH_LOGS_DIR}/{file_name}')
                count_log_files -= 1
        except PermissionError:
            LOGHandler.logText(f"ERROR! removeFileLogsAcrossLast15(): {file_name} while deleting log-file!")
            pass

def removeFileLogAcrossCurrent(current_file_log_name):
    for file_name in listdir(PATH_LOGS_DIR):
        if "log_" in file_name and not (current_file_log_name in file_name):
            try:
                if os.access(f'{PATH_LOGS_DIR}/{file_name}', os.R_OK and os.X_OK):
                    os.remove(f'{PATH_LOGS_DIR}/{file_name}')
            except PermissionError:
                LOGHandler.logText(f"ERROR! removeFileLogAcrossCurrent(): {file_name} while deleting log-file!")
                pass


#
#
#

def appendJSONToFile(catalogue_name, text, search_request):
    with open(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt', 'a+') as f:
        f.write(text + "\n")

def appendLINKtoFile(catalogue_name, text, search_request):
    with open(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt', 'a+') as f:
        f.write(text + "\n")



def getLINKSfromFile(catalogue_name, search_request):
    links = []
    index = 0
    with open(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt') as file:
        for line in file:
            links.append(line.rstrip().split(" "))
            index += 1
    return links

def getLINKSfromFileByLines(catalogue_name, search_request, start_line, end_line):
    links = []
    index = 0
    with open(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt') as file:
        for line in file:
            if index >= start_line and index < end_line and line.rstrip() != "":
                links.append(line.rstrip().split(" "))
            index += 1
    return links

def getJSONSfromFileByLines(catalogue_name, search_request, start_line, end_line):
    links = []
    index = 0
    with open(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt') as file:
        for line in file:
            if index >= start_line and index < end_line:
                links.append(line.rstrip())
            index += 1
    return links



def getCountLINKSLines(catalogue_name, file_path):
    num_lines = 0
    for line in open(f'{PATH_LINKS_DIR}/{catalogue_name}/{file_path}'):
        num_lines += 1
    return num_lines

def getCountJSONSLines(catalogue_name, file_path):
    num_lines = 0
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
    return len(listdir(path))-1



def getSearchRequests():
    search_requests = []
    for line in open(f'{PATH_REQUEST_FILE}'):
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
    for line in open(path, "r"):
        if line not in lines_seen:  # not a duplicate
            lines_seen.add(line)
    outfile = open(path, "w")
    for line in lines_seen:
        outfile.write(line)
    outfile.close()





