import datetime
import os
import shutil
from os import listdir
from pathlib import Path


def createLOGSDir():
    Path(f'LOGS/').mkdir(parents=True, exist_ok=True)

def createLINKSDir(catalogue_name):
    Path(f'LINKS/{catalogue_name}/').mkdir(parents=True, exist_ok=True)
    Path(f'LINKS/{catalogue_name}/_completed/').mkdir(parents=True, exist_ok=True)

def createJSONSDir(catalogue_name):
    Path(f'JSONS/{catalogue_name}/').mkdir(parents=True, exist_ok=True)
    Path(f'JSONS/{catalogue_name}/_completed/').mkdir(parents=True, exist_ok=True)



def moveLINKToCompleated(catalogue_name, search_request):
    number = getCountCompleatedLINKSFiles(catalogue_name) + 1
    os.rename(f'LINKS/{catalogue_name}/{search_request}.txt', f'LINKS/{catalogue_name}/{number}_{search_request}.txt')
    shutil.move(f'LINKS/{catalogue_name}/{number}_{search_request}.txt', f'LINKS/{catalogue_name}/_completed')

def moveJSONToCompleated(catalogue_name, search_request):
    number = getCountCompleatedJSONSFiles(catalogue_name) + 1
    os.rename(f'JSONS/{catalogue_name}/{search_request}.txt', f'JSONS/{catalogue_name}/{number}_{search_request}.txt')
    shutil.move(f'JSONS/{catalogue_name}/{number}_{search_request}.txt', f'JSONS/{catalogue_name}/_completed')



def appendToFileOutput(text, number):
    # prefix = datetime.datetime.now().strftime("%d%m%Y%H%M%S")
    with open(f'LOGS/{number}_output.txt', 'a+') as f:
        f.write(text + "\n")

def appendToFileLog(text):
    with open(f'LOGS/log.txt', 'a+') as f:
        f.write(text + "\n")

def appendJSONToFile(catalogue_name, text, search_request):
    with open(f'JSONS/{catalogue_name}/{search_request}.txt', 'a+') as f:
        f.write(text + "\n")

def appendLINKtoFile(catalogue_name, text, search_request):
    with open(f'LINKS/{catalogue_name}/{search_request}.txt', 'a+') as f:
        f.write(text + "\n")



def getLINKSfromFile(catalogue_name, search_request):
    links = []
    index = 0
    with open(f'LINKS/{catalogue_name}/{search_request}.txt') as file:
        for line in file:
            # print(line)
            links.append(line.rstrip().split(" "))
            index += 1
    return links

def getLINKSfromFileByLines(catalogue_name, search_request, start_line, end_line):
    links = []
    index = 0
    with open(f'LINKS/{catalogue_name}/{search_request}.txt') as file:
        for line in file:
            if index >= start_line and index < end_line:
                links.append(line.rstrip().split(" "))
            index += 1
    return links

def getJSONSfromFileByLines(catalogue_name, search_request, start_line, end_line):
    links = []
    index = 0
    with open(f'JSONS/{catalogue_name}/{search_request}.txt') as file:
        for line in file:
            if index >= start_line and index < end_line:
                links.append(line.rstrip())
            index += 1
    return links



def getCountLINKSLines(catalogue_name, file_path):
    num_lines = 0
    for line in open(f'LINKS/{catalogue_name}/{file_path}'):
        num_lines += 1
    return num_lines

def getCountJSONSLines(catalogue_name, file_path):
    num_lines = 0
    for line in open(f'JSONS/{catalogue_name}/{file_path}'):
        num_lines += 1
    return num_lines

def getCountCompleatedLINKSFiles(catalogue_name):
    path = f"LINKS/{catalogue_name}/_completed"
    return len(listdir(path))

def getCountCompleatedJSONSFiles(catalogue_name):
    path = f"JSONS/{catalogue_name}/_completed"
    return len(listdir(path))

def getCountCompleatedOUTPUTFiles():
    path = f"LOGS"
    return len(listdir(path))-1



def getSearchRequests():
    search_requests = []
    for line in open(f'SEARCH_REQUESTS.txt'):
        if line.rstrip() == "____":
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
    path = f'JSONS/{catalogue_name}/{search_request}'
    lines_seen = set()  # holds lines already seen
    for line in open(path, "r"):
        if line not in lines_seen:  # not a duplicate
            lines_seen.add(line)
    outfile = open(path, "w")
    for line in lines_seen:
        outfile.write(line)
    outfile.close()





