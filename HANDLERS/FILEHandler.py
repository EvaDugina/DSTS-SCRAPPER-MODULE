from os import listdir


def appendJSONToFile(catalogue_name, text, search_request):
    fp = open(f'JSONS/{catalogue_name}/{search_request}.txt', 'a')
    fp.write(text + "\n")
    fp.close()

def appendLINKtoFile(catalogue_name, text, search_request):
    fp = open(f'LINKS/{catalogue_name}/{search_request}.txt', 'a')
    fp.write(text + "\n")
    fp.close()

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
    for line in open(f'LINKS/{catalogue_name}/{file_path}'):
        num_lines += 1
    return num_lines

def getSearchRequests():
    search_requests = []
    for line in open(f'SEARCH_REQUESTS.txt'):
        if line == "____":
            break
        search_requests.append(line.rstrip().split(" "))
    return search_requests

def getElementsForParse():
    elements = []
    path = "JSONS"
    for producer_name in listdir(path):
        for file_name in listdir(path + "/" + producer_name):
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




