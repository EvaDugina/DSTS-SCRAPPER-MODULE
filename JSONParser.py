import datetime
import json
import threading

from HANDLERS import WEBHandler as wHandl
from HANDLERS import FILEHandler as fHandl
from HANDLERS import DBHandler as dbHandl
from UTILS import strings
from PROVIDERS import Provider

_search_request = ""
_catalogue_name = ""
_dbHandler = dbHandl.DBWorker('5432')
_number = fHandl.getCountCompleatedOUTPUTFiles() + 1


def parseJSONS(start_line, end_line):
    global _dbHandler, _number

    json_lines = fHandl.getJSONSfromFileByLines(_catalogue_name, _search_request, start_line, end_line)

    for line_json in json_lines:
        line_json = json.loads(line_json)
        article_name = line_json['name']
        catalogue_name = line_json['catalogue_name']
        producer_name = line_json['producer_name']

        cross_ref = line_json['info']['crossReference']

        start_time_parsing_jsons = datetime.datetime.now()
        provider = wHandl.getProviderAndProducerId(catalogue_name, _dbHandler)
        provider.parseCrossReference(article_name, producer_name, cross_ref)
        provider.setInfo(article_name, producer_name, line_json['info'])
        end_time_parsing_jsons = datetime.datetime.now()
        fHandl.appendToFileLog("parseCrossReference() -> completed! ВРЕМЯ: " +
              str(int((end_time_parsing_jsons - start_time_parsing_jsons).total_seconds())) + " сек.")

        fHandl.appendToFileOutput(f'{article_name} ИЗ КАТАЛОГА {catalogue_name} УСПЕШНО ДОБАВЛЕН!', _number)

    fHandl.appendToFileLog("\n")


def parseJSONSbyThreads(catalogue_name, search_request):
    global _catalogue_name, _search_request

    _catalogue_name = catalogue_name
    _search_request = search_request

    count_lines = fHandl.getCountJSONSLines(_catalogue_name, f"{_search_request}.txt")

    # Определяем количество потоков
    count_threads = wHandl.getCountThreads(count_lines)

    # Распределяем ссылки (части файла) по потокам
    parts = []
    count_lines_in_part = count_lines // count_threads
    if count_lines // count_threads > 0:
        for i in range(0, count_threads):
            start_index = i * count_lines_in_part
            end_index = (i + 1) * count_lines_in_part
            parts.append([start_index, end_index])

    # Добавляем поток с нераспределёнными ссылками
    if count_lines % count_threads != 0:
        parts.append([count_lines - (count_lines % count_threads), count_lines])

    # Запускаем потоки

    tasks = []
    for i in range(0, count_threads):
        tasks.append(threading.Thread(target=parseJSONS, args=(parts[i][0], parts[i][1])))
    for i in range(0, count_threads):
        tasks[i].start()
        fHandl.appendToFileLog(f"T{i} START!")
        tasks[i].join()
    if count_lines % count_threads != 0:
        index = len(parts) - 1
        tasks.append(threading.Thread(target=parseJSONS, args=(parts[index][0], parts[index][1])))
        tasks[index].start()
        fHandl.appendToFileLog(f"T{index} START!")
        tasks[index].join()


def doWhileNoSuccess(try_count, type_function, function, driver, article):
    if try_count > 4:
        return "СЛАБОЕ ИНТЕРНЕТ-СОЕДИНЕНИЕ"
    else:
        flag = False
        if type_function == "parseCrossRef":
            if try_count > 0:
                flag = function(driver, article, try_count * 2)
            else:
                flag = function(driver, article, 1)

        elif type_function == "loadArticlePage":
            flag = function(driver, article)

        if flag == "SUCCESS" or flag == strings.INCORRECT_LINK_OR_CHANGED_SITE_STRUCTURE:
            return flag
        else:
            return doWhileNoSuccess(try_count + 1, type_function, function, driver, article)


if __name__=="__main__":

    elements = fHandl.getElementsForParse()

    for elem in elements:
        catalogue_name = elem[0]
        search_request = elem[1]

        fHandl.appendToFileLog("+++++++")
        fHandl.appendToFileLog("CATALOGUE_NAME: " + catalogue_name)
        fHandl.appendToFileLog("SEARCH_REQUEST: " + search_request)
        fHandl.appendToFileLog("parseJSONSbyThreads() -> start!")
        # Парсим JSONS
        start_time_parsing_jsons = datetime.datetime.now()
        parseJSONSbyThreads(catalogue_name, search_request)
        end_time_parsing_jsons = datetime.datetime.now()
        fHandl.appendToFileLog("parseJSONSbyThreads() -> completed! ВРЕМЯ: " +
              str(int((end_time_parsing_jsons - start_time_parsing_jsons).total_seconds())) + " сек.")
        fHandl.appendToFileLog("+++++++")
        fHandl.appendToFileLog("\n")

        fHandl.moveJSONToCompleated(catalogue_name, search_request)
