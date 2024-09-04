import datetime
import os
import shutil
from os import listdir
from pathlib import Path

from loguru import logger

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



def moveLINKToCompleted(catalogue_name, search_request):
    number = getCountCompleatedLINKSFiles(catalogue_name) + 1
    os.rename(f'{PATH_LINKS_DIR}/{catalogue_name}/{search_request}.txt', f'{PATH_LINKS_DIR}/{catalogue_name}/{number}_{search_request}.txt')
    shutil.move(f'{PATH_LINKS_DIR}/{catalogue_name}/{number}_{search_request}.txt', f'{PATH_LINKS_DIR}/{catalogue_name}/_completed')

def moveJSONToCompleted(catalogue_name, search_request):
    number = getCountCompleatedJSONSFiles(catalogue_name) + 1
    os.rename(f'{PATH_JSONS_DIR}/{catalogue_name}/{search_request}.txt', f'{PATH_JSONS_DIR}/{catalogue_name}/{number}_{search_request}.txt')
    shutil.move(f'{PATH_JSONS_DIR}/{catalogue_name}/{number}_{search_request}.txt', f'{PATH_JSONS_DIR}/{catalogue_name}/_completed')


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





