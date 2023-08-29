
def appendJSONToFile(catalogue_name, text):
    fp = open(f'JSONS/{catalogue_name}/{catalogue_name}.txt', 'a')
    fp.write(text + "\n")
    fp.close()

def appendLINKtoFile(catalogue_name, text):
    fp = open(f'LINKS/{catalogue_name}/{catalogue_name}.txt', 'a')
    fp.write(text + "\n")
    fp.close()

def getLINKSfromFile(catalogue_name):
    links = []
    index = 0
    with open(f'LINKS/{catalogue_name}/{catalogue_name}.txt') as file:
        for line in file:
            # print(line)
            links.append(line.rstrip().split(" "))
            index += 1
    return links

def getLINKSfromFileByLines(catalogue_name, start_line, end_line):
    links = []
    index = 0
    with open(f'LINKS/{catalogue_name}/{catalogue_name}.txt') as file:
        for line in file:
            if index >= start_line and index < end_line:
                links.append(line.rstrip().split(" "))
            index += 1
    return links

def getCountLINKSLines(file_path):
    num_lines = 0
    for line in open(f'LINKS/{catalogue_name}/{file_path}'):
        num_lines += 1
    return num_lines


